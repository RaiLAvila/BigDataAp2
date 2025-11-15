# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.dialogs import (
    ComponentDialog,
    DialogContext,
    DialogSet,
    DialogTurnResult,
    DialogTurnStatus,
    WaterfallDialog,
    WaterfallStepContext,
)
from botbuilder.core import MessageFactory, TurnContext
from botbuilder.schema import InputHints

from config import DefaultConfig
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.luis_helper import LuisHelper, Intent

from .booking_dialog import BookingDialog
from .consultar_voo_dialog import ConsultarVooDialog
from .cancelar_voo_dialog import CancelarVooDialog
from .reservar_hotel_dialog import ReservarHotelDialog
from .consultar_hotel_dialog import ConsultarHotelDialog
from .cancelar_hotel_dialog import CancelarHotelDialog


class MainDialog(ComponentDialog):
    def __init__(
        self,
        luis_recognizer: FlightBookingRecognizer,
        booking_dialog: BookingDialog,
        consultar_voo_dialog: ConsultarVooDialog,
        cancelar_voo_dialog: CancelarVooDialog,
        reservar_hotel_dialog: ReservarHotelDialog,
        consultar_hotel_dialog: ConsultarHotelDialog,
        cancelar_hotel_dialog: CancelarHotelDialog,
        configuration: DefaultConfig,
    ):
        super(MainDialog, self).__init__(MainDialog.__name__)

        self._luis_recognizer = luis_recognizer
        self._config = configuration

        self.add_dialog(WaterfallDialog(self.__class__.__name__, [self.intro_step, self.act_step, self.final_step]))
        self.add_dialog(booking_dialog)
        self.add_dialog(consultar_voo_dialog)
        self.add_dialog(cancelar_voo_dialog)
        self.add_dialog(reservar_hotel_dialog)
        self.add_dialog(consultar_hotel_dialog)
        self.add_dialog(cancelar_hotel_dialog)

        self.initial_dialog_id = self.__class__.__name__

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self._luis_recognizer.is_configured:
            await step_context.context.send_activity(
                MessageFactory.text(
                    "NOTE: LUIS is not configured. To enable all capabilities, add 'LuisAppId', 'LuisAPIKey' and "
                    "'LuisAPIHostName' to the appsettings.json file.",
                    input_hint=InputHints.ignoring_input,
                )
            )
            return await step_context.next(None)

        message_text = (
            str(step_context.options)
            if step_context.options
            else "Olá! Como posso te ajudar hoje? (ex: comprar uma passagem, reservar um hotel)"
        )
        prompt_message = MessageFactory.text(
            message_text, message_text, InputHints.expecting_input
        )
        return await step_context.prompt(
            "TextPrompt", prompt=prompt_message
        )

    async def act_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self._luis_recognizer.is_configured:
            return await step_context.begin_dialog(BookingDialog.__name__)

        intent, luis_result = await LuisHelper.execute_luis_query(
            self._luis_recognizer, step_context.context
        )

        if intent == self._config.LUIS_INTENT_COMPRAR and luis_result:
            return await step_context.begin_dialog(BookingDialog.__name__, luis_result)

        if intent == self._config.LUIS_INTENT_CONSULTAR_VOO:
            return await step_context.begin_dialog(ConsultarVooDialog.__name__)

        if intent == self._config.LUIS_INTENT_CANCELAR_VOO:
            return await step_context.begin_dialog(CancelarVooDialog.__name__)

        if intent == self._config.LUIS_INTENT_RESERVAR_HOTEL:
            return await step_context.begin_dialog(ReservarHotelDialog.__name__)

        if intent == self._config.LUIS_INTENT_CONSULTAR_HOTEL:
            return await step_context.begin_dialog(ConsultarHotelDialog.__name__)

        if intent == self._config.LUIS_INTENT_CANCELAR_HOTEL:
            return await step_context.begin_dialog(CancelarHotelDialog.__name__)

        else:
            didnt_understand_text = (
                "Desculpe, não entendi o que você quis dizer. Tente algo como 'comprar uma passagem de São Paulo para o Rio de Janeiro'."
            )
            didnt_understand_message = MessageFactory.text(
                didnt_understand_text, didnt_understand_text, InputHints.ignoring_input
            )
            await step_context.context.send_activity(didnt_understand_message)

        return await step_context.next(None)


    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result is not None:
            result = step_context.result
            msg_txt = "Sua reserva está confirmada. Obrigado por escolher nossos serviços!"
            message = MessageFactory.text(msg_txt, msg_txt, InputHints.ignoring_input)
            await step_context.context.send_activity(message)

        prompt_message = "Posso te ajudar com mais alguma coisa?"
        return await step_context.replace_dialog(self.id, prompt_message)

    async def on_continue_dialog(self, inner_dc: DialogContext) -> DialogTurnResult:
        result = await self.interrupt(inner_dc)
        if result is not None:
            return result

        return await super(MainDialog, self).on_continue_dialog(inner_dc)
