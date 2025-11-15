from botbuilder.core import MessageFactory, UserState
from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    ComponentDialog,
    DialogTurnStatus,
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions, NumberPrompt, ChoicePrompt
from amadeus_client import amadeus  # Importa a instância do cliente
from botbuilder.schema import CardAction, ActionTypes, HeroCard, InputHints
from amadeus.client.errors import ResponseError

class MainDialog(ComponentDialog):
    def __init__(self, user_state: UserState):
        super(MainDialog, self).__init__(MainDialog.__name__)
        self.user_state = user_state

        self.add_dialog(
            WaterfallDialog(
                "MainWaterfall",
                [
                    self.initial_step,
                    self.intent_router_step,
                    # Passos para voos
                    self.flight_origin_step,
                    self.flight_destination_step,
                    self.flight_date_step,
                    self.flight_adults_step,
                    self.flight_search_step,
                    # Passos para hotéis
                    self.hotel_city_step,
                    self.hotel_checkin_step,
                    self.hotel_checkout_step,
                    self.hotel_adults_step,
                    self.hotel_search_step,
                ],
            )
        )
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(NumberPrompt(NumberPrompt.__name__))
        self.initial_dialog_id = "MainWaterfall"

    async def initial_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Olá! O que você deseja fazer? (Ex: comprar passagem, reservar hotel)")),
        )

    async def intent_router_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        clu_result = step_context.context.turn_state.get("clu_result")
        intent = clu_result["result"]["prediction"]["topIntent"] if clu_result else None
        
        step_context.values["intent"] = intent

        if intent == "ComprarVoo":
            return await self.flight_origin_step(step_context)
        if intent == "ReservarHotel":
            return await self.hotel_city_step(step_context)
        
        await step_context.context.send_activity("Não entendi o que você quer. Por favor, tente 'comprar passagem' ou 'reservar hotel'.")
        return await step_context.end_dialog()

    # --- FLUXO DE VOO ---
    async def flight_origin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text("Qual a cidade de origem do voo?")))
    
    async def flight_destination_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["origin"] = step_context.result
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text("Qual a cidade de destino?")))

    async def flight_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["destination"] = step_context.result
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text("Qual a data do voo? (AAAA-MM-DD)")))

    async def flight_adults_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["date"] = step_context.result
        return await step_context.prompt(NumberPrompt.__name__, PromptOptions(prompt=MessageFactory.text("Quantos adultos?")))

    async def flight_search_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["adults"] = step_context.result
        try:
            origin_iata = await self._get_iata_code(step_context.values["origin"], "AIRPORT")
            destination_iata = await self._get_iata_code(step_context.values["destination"], "AIRPORT")
            if not origin_iata or not destination_iata:
                await step_context.context.send_activity("Não encontrei uma das cidades. Tente novamente.")
                return await step_context.end_dialog()

            # CORREÇÃO: Usar 'amadeus' diretamente, não 'self.amadeus'
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin_iata,
                destinationLocationCode=destination_iata,
                departureDate=step_context.values["date"],
                adults=step_context.values["adults"],
                max=3,
            )
            if not response.data:
                await step_context.context.send_activity("Nenhum voo encontrado para esta rota/data (lembre-se que o ambiente de teste é limitado).")
            else:
                await step_context.context.send_activity("Encontrei estes voos:")
                # (Lógica para mostrar cards de voos pode ser adicionada aqui)
                await step_context.context.send_activity(f"Primeira oferta: {response.data[0]['price']['total']} {response.data[0]['price']['currency']}")

        except ResponseError as e:
            await step_context.context.send_activity(f"Erro ao buscar voos: {e}")
        return await step_context.end_dialog()

    # --- FLUXO DE HOTEL ---
    async def hotel_city_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text("Para qual cidade você quer reservar o hotel?")))

    async def hotel_checkin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["city"] = step_context.result
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text("Data de check-in? (AAAA-MM-DD)")))

    async def hotel_checkout_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["checkin_date"] = step_context.result
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text("Data de check-out? (AAAA-MM-DD)")))

    async def hotel_adults_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["checkout_date"] = step_context.result
        return await step_context.prompt(NumberPrompt.__name__, PromptOptions(prompt=MessageFactory.text("Quantos adultos?")))

    async def hotel_search_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["adults"] = step_context.result
        try:
            city_code = await self._get_iata_code(step_context.values["city"], "CITY")
            if not city_code:
                await step_context.context.send_activity("Não encontrei esta cidade. Tente novamente.")
                return await step_context.end_dialog()

            # CORREÇÃO: Usar 'amadeus' diretamente
            hotels_response = amadeus.reference_data.locations.hotels.by_city.get(cityCode=city_code)
            if not hotels_response.data:
                await step_context.context.send_activity("Nenhum hotel encontrado nesta cidade (lembre-se que o ambiente de teste é limitado).")
                return await step_context.end_dialog()

            hotel_ids = [hotel['hotelId'] for hotel in hotels_response.data[:3]]
            # CORREÇÃO: Usar 'amadeus' diretamente
            offers_response = amadeus.shopping.hotel_offers_by_hotel.get(
                hotelId=','.join(hotel_ids),
                checkInDate=step_context.values["checkin_date"],
                checkOutDate=step_context.values["checkout_date"],
                adults=step_context.values["adults"]
            )
            if not offers_response.data:
                await step_context.context.send_activity("Nenhuma oferta de hotel encontrada para estas datas.")
            else:
                await step_context.context.send_activity("Encontrei estas ofertas de hotéis:")
                # (Lógica para mostrar cards de hotéis pode ser adicionada aqui)
                await step_context.context.send_activity(f"Primeira oferta: {offers_response.data[0]['offers'][0]['price']['total']} {offers_response.data[0]['offers'][0]['price']['currency']}")

        except ResponseError as e:
            await step_context.context.send_activity(f"Erro ao buscar hotéis: {e}")
        return await step_context.end_dialog()

    # --- FUNÇÃO AUXILIAR ---
    async def _get_iata_code(self, city_name: str, sub_type: str) -> str:
        try:
            # CORREÇÃO: Usar 'amadeus' diretamente
            response = amadeus.reference_data.locations.get(keyword=city_name, subType=sub_type)
            if response.data:
                return response.data[0]['iataCode']
        except ResponseError as e:
            print(f"Erro ao buscar IATA para '{city_name}': {e}")
        return None