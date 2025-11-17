from botbuilder.dialogs import ComponentDialog, DialogSet, DialogTurnStatus, WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.core import MessageFactory, TurnContext
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions

from .comprar_voo_dialog import ComprarVooDialog
from .reservar_hotel_dialog import ReservarHotelDialog
from .consultar_cancelar_dialog import ConsultarCancelarDialog
from flight_booking_details import FlightBookingDetails
from hotel_booking_details import HotelBookingDetails
from helpers.luis_helper import LuisHelper, Intent

class MainDialog(ComponentDialog):
    def __init__(self, luis_recognizer):
        super(MainDialog, self).__init__(MainDialog.__name__)

        self._luis_recognizer = luis_recognizer

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(ComprarVooDialog(ComprarVooDialog.__name__))
        self.add_dialog(ReservarHotelDialog(ReservarHotelDialog.__name__))
        self.add_dialog(ConsultarCancelarDialog(ConsultarCancelarDialog.__name__))
        self.add_dialog(
            WaterfallDialog(
                "WFDialog", [self.intro_step, self.act_step, self.final_step]
            )
        )

        self.initial_dialog_id = "WFDialog"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self._luis_recognizer or not self._luis_recognizer.get("client"):
            await step_context.context.send_activity(
                MessageFactory.text("O serviço de reconhecimento de linguagem (CLU) não está configurado.")
            )
            return await step_context.next(None)
        
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Olá! Como posso te ajudar hoje? (ex: quero comprar uma passagem, reservar um hotel, etc.)")
            ),
        )

    async def act_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        luis_result = await LuisHelper.execute_luis_query(self._luis_recognizer, step_context.context)
        intent = luis_result.top_intent

        if intent == Intent.COMPRAR_VOO.value:
            # Extrai entidades do CLU
            flight_details = FlightBookingDetails(
                origin=luis_result.origin,
                destination=luis_result.destination,
                departure_date=luis_result.departure_date
            )
            return await step_context.begin_dialog(ComprarVooDialog.__name__, flight_details)

        if intent == Intent.RESERVAR_HOTEL.value:
            # Extrai entidades do CLU
            hotel_details = HotelBookingDetails(
                destination=luis_result.destination,
                checkin_date=luis_result.checkin_date
            )
            return await step_context.begin_dialog(ReservarHotelDialog.__name__, hotel_details)

        if intent in [
            Intent.CONSULTAR_HOTEL.value,
            Intent.CONSULTAR_VOO.value,
            Intent.CANCELAR_HOTEL.value,
            Intent.CANCELAR_VOO.value,
        ]:
            return await step_context.begin_dialog(ConsultarCancelarDialog.__name__, {"intent": intent})

        else:
            await step_context.context.send_activity(MessageFactory.text("Desculpe, não entendi. Por favor, tente reformular."))
            return await step_context.next(None)

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Posso ajudar em algo mais?"))
        return await step_context.replace_dialog(self.id)