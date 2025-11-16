from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import TextPrompt, ConfirmPrompt, PromptOptions
from botbuilder.core import MessageFactory, CardFactory
from botbuilder.schema import HeroCard, CardAction, ActionTypes

from .cancel_and_help_dialog import CancelAndHelpDialog
from flight_booking_details import FlightBookingDetails
from helpers import api_client

class ComprarVooDialog(CancelAndHelpDialog):
    def __init__(self, dialog_id: str = None):
        super(ComprarVooDialog, self).__init__(dialog_id or ComprarVooDialog.__name__)

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.origin_step,
                    self.destination_step,
                    self.departure_date_step,
                    self.show_flights_step,
                    self.cpf_step,
                    self.confirm_step,
                    self.final_step,
                ],
            )
        )

        self.initial_dialog_id = WaterfallDialog.__name__

    async def origin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details: FlightBookingDetails = step_context.options
        if booking_details.origin is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text("De qual cidade você vai sair?")),
            )
        return await step_context.next(booking_details.origin)

    async def destination_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details: FlightBookingDetails = step_context.options
        booking_details.origin = step_context.result
        if booking_details.destination is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text("Para qual cidade você quer ir?")),
            )
        return await step_context.next(booking_details.destination)

    async def departure_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details: FlightBookingDetails = step_context.options
        booking_details.destination = step_context.result
        if booking_details.departure_date is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text("Qual a data da viagem (AAAA-MM-DD)?")),
            )
        return await step_context.next(booking_details.departure_date)

    async def show_flights_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details: FlightBookingDetails = step_context.options
        booking_details.departure_date = step_context.result

        origin_iata = api_client.get_iata_code(booking_details.origin)
        destination_iata = api_client.get_iata_code(booking_details.destination)

        if not origin_iata or not destination_iata:
            await step_context.context.send_activity(MessageFactory.text("Não consegui encontrar uma das cidades. Por favor, tente novamente."))
            return await step_context.end_dialog()

        await step_context.context.send_activity(MessageFactory.text("Buscando voos..."))
        flights = api_client.search_flights(origin_iata, destination_iata, booking_details.departure_date, 1)

        if not flights or not flights.get("data"):
            await step_context.context.send_activity(MessageFactory.text("Não encontrei voos para esta rota e data."))
            return await step_context.end_dialog()

        step_context.values["flights"] = flights["data"]
        
        await step_context.context.send_activity(MessageFactory.text("Encontrei estes voos para você:"))
        
        cards = []
        for i, flight in enumerate(flights["data"][:5]):
            price = flight.get("price", {}).get("total", "N/A")
            card = HeroCard(
                title=f"Voo de {booking_details.origin} para {booking_details.destination}",
                text=f"Preço: R$ {price}",
                buttons=[
                    CardAction(
                        type=ActionTypes.im_back,
                        title=f"Reservar Voo (R$ {price})",
                        value=str(i), # Usando índice como ID
                    )
                ],
            )
            cards.append(CardFactory.hero_card(card))

        reply = MessageFactory.carousel(cards)
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=reply))

    async def cpf_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        selected_flight_index = int(step_context.result)
        flights = step_context.values["flights"]
        selected_flight = flights[selected_flight_index]

        step_context.values["selected_flight"] = selected_flight
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text("Por favor, informe seu CPF.")))

    async def confirm_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        cpf = step_context.result
        step_context.values["cpf"] = cpf
        
        booking_details: FlightBookingDetails = step_context.options
        flight = step_context.values["selected_flight"]
        price = flight.get("price", {}).get("total", "N/A")

        message = (
            f"Por favor, confirme sua reserva:\n"
            f"Origem: {booking_details.origin}\n"
            f"Destino: {booking_details.destination}\n"
            f"Data: {booking_details.departure_date}\n"
            f"Preço: R$ {price}\n"
            f"CPF: {cpf}"
        )
        return await step_context.prompt(ConfirmPrompt.__name__, PromptOptions(prompt=MessageFactory.text(message)))

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result:
            cpf = step_context.values["cpf"]
            flight_data = step_context.values["selected_flight"]

            cliente = api_client.criar_ou_buscar_cliente(cpf)
            if not cliente:
                await step_context.context.send_activity(MessageFactory.text("Houve um problema ao verificar seu cadastro. Tente novamente."))
                return await step_context.end_dialog()

            reserva = api_client.adicionar_reserva_voo(cliente["id"], flight_data)
            if reserva:
                await step_context.context.send_activity(MessageFactory.text(f"Sua reserva de voo foi confirmada! O código da reserva é {reserva.get('id')}."))
            else:
                await step_context.context.send_activity(MessageFactory.text("Não foi possível concluir sua reserva. Tente novamente mais tarde."))
        else:
            await step_context.context.send_activity(MessageFactory.text("Sua reserva foi cancelada."))

        return await step_context.end_dialog()
