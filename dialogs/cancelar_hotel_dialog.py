from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult, ComponentDialog
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions, ConfirmPrompt
from botbuilder.core import MessageFactory
from botbuilder.schema import InputHints

class CancelarHotelDialog(ComponentDialog):
    def __init__(self, dialog_id: str = None):
        super(CancelarHotelDialog, self).__init__(dialog_id or CancelarHotelDialog.__name__)

        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.codigo_reserva_step,
                    self.confirm_step,
                    self.final_step,
                ],
            )
        )
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.initial_dialog_id = WaterfallDialog.__name__

    async def codigo_reserva_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        prompt_text = "Por favor, informe o código da reserva de hotel que deseja cancelar."
        prompt_message = MessageFactory.text(prompt_text, prompt_text, InputHints.expecting_input)
        return await step_context.prompt(
            TextPrompt.__name__, PromptOptions(prompt=prompt_message)
        )

    async def confirm_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["codigo_reserva"] = step_context.result
        prompt_text = f"Você confirma o cancelamento da reserva {step_context.result}?"
        return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt_text)),
        )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result:
            codigo_reserva = step_context.values["codigo_reserva"]
            # TODO: Adicionar lógica para cancelar a reserva de hotel
            msg_text = f"Cancelando reserva de hotel {codigo_reserva}... (funcionalidade em desenvolvimento)."
            await step_context.context.send_activity(MessageFactory.text(msg_text))
        else:
            await step_context.context.send_activity(MessageFactory.text("O cancelamento não foi realizado."))
        return await step_context.end_dialog()
