from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import TextPrompt, ConfirmPrompt, PromptOptions
from botbuilder.core import MessageFactory, CardFactory
from botbuilder.schema import HeroCard, CardAction, ActionTypes

from .cancel_and_help_dialog import CancelAndHelpDialog
from hotel_booking_details import HotelBookingDetails
from helpers import api_client

class ReservarHotelDialog(CancelAndHelpDialog):
    def __init__(self, dialog_id: str = None):
        super(ReservarHotelDialog, self).__init__(dialog_id or ReservarHotelDialog.__name__)

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.destination_step,
                    self.checkin_date_step,
                    self.checkout_date_step,
                    self.show_hotels_step,
                    self.cpf_step,
                    self.confirm_step,
                    self.final_step,
                ],
            )
        )

        self.initial_dialog_id = WaterfallDialog.__name__

    async def destination_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details = step_context.options
        if booking_details.destination is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text("Para qual cidade você gostaria de reservar um hotel?")),
            )
        return await step_context.next(booking_details.destination)

    async def checkin_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details: HotelBookingDetails = step_context.options
        booking_details.destination = step_context.result
        if booking_details.checkin_date is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text("Qual a data de check-in (AAAA-MM-DD)?")),
            )
        return await step_context.next(booking_details.checkin_date)

    async def checkout_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details: HotelBookingDetails = step_context.options
        booking_details.checkin_date = step_context.result
        if booking_details.checkout_date is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text("Qual a data de check-out (AAAA-MM-DD)?")),
            )
        return await step_context.next(booking_details.checkout_date)

    async def show_hotels_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details: HotelBookingDetails = step_context.options
        booking_details.checkout_date = step_context.result
        
        city_code = api_client.get_iata_code(booking_details.destination)
        if not city_code:
            await step_context.context.send_activity(MessageFactory.text(f"Não consegui encontrar o código para a cidade '{booking_details.destination}'. Por favor, tente novamente."))
            return await step_context.end_dialog()

        await step_context.context.send_activity(MessageFactory.text("Buscando hotéis..."))
        hotels = api_client.search_hotels(city_code)

        if not hotels or not hotels.get("data"):
            await step_context.context.send_activity(MessageFactory.text("Não encontrei hotéis para esta cidade."))
            return await step_context.end_dialog()

        step_context.values["hotels"] = hotels["data"]
        
        await step_context.context.send_activity(MessageFactory.text("Encontrei estes hotéis para você:"))
        
        cards = []
        for hotel in hotels["data"][:5]: # Limita a 5 hotéis
            card = HeroCard(
                title=hotel.get("name"),
                text=f"Endereço: {hotel.get('address', {}).get('lines', ['N/A'])[0]}",
                buttons=[
                    CardAction(
                        type=ActionTypes.im_back,
                        title=f"Reservar {hotel.get('name')}",
                        value=hotel.get("hotelId"),
                    )
                ],
            )
            cards.append(CardFactory.hero_card(card))

        reply = MessageFactory.carousel(cards)
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=reply))

    async def cpf_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        selected_hotel_id = step_context.result
        hotels = step_context.values["hotels"]
        selected_hotel = next((h for h in hotels if h["hotelId"] == selected_hotel_id), None)

        if not selected_hotel:
            await step_context.context.send_activity(MessageFactory.text("Seleção de hotel inválida. Por favor, tente novamente."))
            return await step_context.end_dialog()

        step_context.values["selected_hotel"] = selected_hotel
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text("Por favor, informe seu CPF.")))

    async def confirm_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        cpf = step_context.result
        step_context.values["cpf"] = cpf
        
        booking_details: HotelBookingDetails = step_context.options
        hotel = step_context.values["selected_hotel"]

        message = (
            f"Por favor, confirme sua reserva:\n"
            f"Hotel: {hotel['name']}\n"
            f"Cidade: {booking_details.destination}\n"
            f"Check-in: {booking_details.checkin_date}\n"
            f"Check-out: {booking_details.checkout_date}\n"
            f"CPF: {cpf}"
        )
        return await step_context.prompt(ConfirmPrompt.__name__, PromptOptions(prompt=MessageFactory.text(message)))

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result:
            cpf = step_context.values["cpf"]
            booking_details: HotelBookingDetails = step_context.options
            hotel = step_context.values["selected_hotel"]

            cliente = api_client.criar_ou_buscar_cliente(cpf)
            if not cliente:
                await step_context.context.send_activity(MessageFactory.text("Houve um problema ao verificar seu cadastro. Tente novamente."))
                return await step_context.end_dialog()

            reserva_data = {
                "hotelId": hotel["hotelId"],
                "checkInDate": booking_details.checkin_date,
                "checkOutDate": booking_details.checkout_date,
            }

            reserva = api_client.adicionar_reserva_hotel(cliente["id"], reserva_data)
            if reserva:
                await step_context.context.send_activity(MessageFactory.text(f"Sua reserva no hotel {hotel['name']} foi confirmada! O código da reserva é {reserva.get('id')}."))
            else:
                await step_context.context.send_activity(MessageFactory.text("Não foi possível concluir sua reserva. Tente novamente mais tarde."))
        else:
            await step_context.context.send_activity(MessageFactory.text("Sua reserva foi cancelada."))

        return await step_context.end_dialog()
