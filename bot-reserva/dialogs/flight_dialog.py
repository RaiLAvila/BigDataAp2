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

class FlightDialog(ComponentDialog):
    def __init__(self, user_state: UserState):
        super(FlightDialog, self).__init__(FlightDialog.__name__)
        self.user_state = user_state

        self.add_dialog(
            WaterfallDialog(
                "FlightWaterfall",
                [
                    self.origin_step,
                    self.destination_step,
                    self.date_step,
                    self.adults_step,
                    self.search_step,
                ],
            )
        )
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(NumberPrompt(NumberPrompt.__name__))
        self.initial_dialog_id = "FlightWaterfall"

    async def origin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Perfeito! Qual a cidade de origem do voo?")
            ),
        )

    async def destination_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["origin"] = step_context.result
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Qual a cidade de destino do voo?")
            ),
        )

    async def date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["destination"] = step_context.result
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Qual a data do voo? (AAAA-MM-DD)")),
        )

    async def adults_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["date"] = step_context.result
        return await step_context.prompt(
            NumberPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Quantos adultos?")),
        )

    async def search_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["adults"] = step_context.result
        
        origin_city_name = step_context.values["origin"]
        destination_city_name = step_context.values["destination"]
        departure_date = step_context.values["date"]
        adults = step_context.values["adults"]

        try:
            # Etapa 1: Converter nomes de cidades em códigos IATA de aeroporto
            origin_iata = await self.get_iata_code(origin_city_name)
            destination_iata = await self.get_iata_code(destination_city_name)

            if not origin_iata or not destination_iata:
                await step_context.context.send_activity("Não consegui encontrar o código do aeroporto para uma das cidades. Por favor, tente novamente com um nome de cidade diferente.")
                return await step_context.end_dialog()

            await step_context.context.send_activity(f"[DEBUG] Buscando voos de {origin_iata} para {destination_iata}")

            # Etapa 2: Buscar voos com os códigos IATA
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin_iata,
                destinationLocationCode=destination_iata,
                departureDate=departure_date,
                adults=adults,
                max=3,
            )
            
            if not response.data:
                await step_context.context.send_activity("Nenhuma oferta de voo encontrada para esta rota e data. O ambiente de teste da Amadeus tem dados limitados (tente Madrid para Atenas).")
                return await step_context.end_dialog()

            await step_context.context.send_activity("Encontrei as seguintes ofertas de voos:")
            
            cards = []
            for offer in response.data:
                price = offer.get('price', {})
                itinerary = offer.get('itineraries', [{}])[0]
                segment = itinerary.get('segments', [{}])[0]
                
                card = HeroCard(
                    title=f"Voo de {segment['departure']['iataCode']} para {segment['arrival']['iataCode']}",
                    subtitle=f"Preço Total: {price.get('total')} {price.get('currency')}",
                    text=f"Duração: {itinerary.get('duration', 'N/A').replace('PT', '')}",
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
            await step_context.context.send_activity(f"Erro ao consultar voos: {e.description.get('detail', str(e))}")
        except Exception as e:
            await step_context.context.send_activity(f"Ocorreu um erro inesperado: {e}")

        return await step_context.end_dialog()

    async def get_iata_code(self, city_name: str) -> str:
        """Converte o nome de uma cidade para um código IATA de aeroporto."""
        try:
            response = amadeus.reference_data.locations.get(
                keyword=city_name, subType='AIRPORT'
            )
            # Retorna o código IATA do primeiro resultado
            if response.data:
                return response.data[0]['iataCode']
        except ResponseError as e:
            print(f"Erro ao buscar IATA para '{city_name}': {e}")
        return None
