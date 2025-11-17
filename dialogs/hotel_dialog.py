from botbuilder.core import MessageFactory, UserState
from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    ComponentDialog,
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions, NumberPrompt
from amadeus_client import amadeus
from botbuilder.schema import CardAction, ActionTypes, HeroCard, InputHints
from amadeus.client.errors import ResponseError

class HotelDialog(ComponentDialog):
    def __init__(self, user_state: UserState):
        super(HotelDialog, self).__init__(HotelDialog.__name__)
        self.user_state = user_state

        self.add_dialog(
            WaterfallDialog(
                "HotelWaterfall",
                [
                    self.city_step,
                    self.checkin_date_step,
                    self.checkout_date_step,
                    self.adults_step,
                    self.search_step,
                ],
            )
        )
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(NumberPrompt(NumberPrompt.__name__))
        self.initial_dialog_id = "HotelWaterfall"

    async def city_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Ótimo! Para qual cidade você deseja reservar o hotel?")
            ),
        )

    async def checkin_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["city"] = step_context.result
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Qual a data de check-in? (AAAA-MM-DD)")
            ),
        )

    async def checkout_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["checkin_date"] = step_context.result
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Qual a data de check-out? (AAAA-MM-DD)")
            ),
        )

    async def adults_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["checkout_date"] = step_context.result
        return await step_context.prompt(
            NumberPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Quantos adultos?")),
        )

    async def search_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["adults"] = step_context.result
        
        city_name = step_context.values["city"]
        check_in = step_context.values["checkin_date"]
        check_out = step_context.values["checkout_date"]
        adults = step_context.values["adults"]

        try:
            # Etapa 1: Converter nome da cidade em cityCode
            city_code = await self.get_city_code(city_name)
            if not city_code:
                await step_context.context.send_activity(f"Não consegui encontrar a cidade '{city_name}'. Por favor, tente novamente.")
                return await step_context.end_dialog()

            await step_context.context.send_activity(f"[DEBUG] Buscando hotéis em {city_code}...")

            # Etapa 2: Buscar IDs de hotéis na cidade
            hotels_response = amadeus.reference_data.locations.hotels.by_city.get(cityCode=city_code)
            if not hotels_response.data:
                await step_context.context.send_activity("Nenhum hotel encontrado para esta cidade. O ambiente de teste da Amadeus tem dados limitados (tente 'Paris').")
                return await step_context.end_dialog()

            hotel_ids = [hotel['hotelId'] for hotel in hotels_response.data[:5]]

            # Etapa 3: Buscar ofertas para esses hotéis
            offers_response = amadeus.shopping.hotel_offers_by_hotel.get(
                hotelId=','.join(hotel_ids),
                checkInDate=check_in,
                checkOutDate=check_out,
                adults=adults
            )

            if not offers_response.data:
                await step_context.context.send_activity("Nenhuma oferta de hotel encontrada para as datas selecionadas. Verifique as datas e tente novamente.")
                return await step_context.end_dialog()

            await step_context.context.send_activity("Encontrei as seguintes ofertas de hotéis:")
            
            cards = []
            for offer in offers_response.data[:3]:
                hotel = offer.get('hotel', {})
                offer_details = offer.get('offers', [{}])[0]
                price = offer_details.get('price', {})
                
                card = HeroCard(
                    title=hotel.get('name', 'Nome não disponível'),
                    subtitle=f"Total: {price.get('total')} {price.get('currency')}",
                    text=f"Check-in: {offer_details.get('checkInDate')}, Check-out: {offer_details.get('checkOutDate')}",
                    buttons=[
                        CardAction(
                            type=ActionTypes.open_url,
                            title="Reservar Agora",
                            value="https://www.amadeus.com",
                        )
                    ],
                )
                cards.append(card)

            await step_context.context.send_activity(
                MessageFactory.carousel(cards, input_hint=InputHints.accepting_input)
            )

        except ResponseError as e:
            await step_context.context.send_activity(f"Erro ao consultar hotéis: {e.description.get('detail', str(e))}")
        except Exception as e:
            await step_context.context.send_activity(f"Ocorreu um erro inesperado: {e}")

        return await step_context.end_dialog()

    async def get_city_code(self, city_name: str) -> str:
        """Converte o nome de uma cidade para um código IATA de cidade."""
        try:
            response = amadeus.reference_data.locations.get(
                keyword=city_name, subType='CITY'
            )
            if response.data:
                return response.data[0]['iataCode']
        except ResponseError as e:
            print(f"Erro ao buscar cityCode para '{city_name}': {e}")
        return None
