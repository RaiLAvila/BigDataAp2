from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult, ComponentDialog
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions
from botbuilder.core import MessageFactory
from botbuilder.schema import InputHints

class ReservarHotelDialog(ComponentDialog):
    def __init__(self, dialog_id: str = None):
        super(ReservarHotelDialog, self).__init__(dialog_id or ReservarHotelDialog.__name__)

        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.cidade_step,
                    self.final_step,
                ],
            )
        )
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.initial_dialog_id = WaterfallDialog.__name__

    async def cidade_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        prompt_text = "Em qual cidade você gostaria de reservar um hotel?"
        prompt_message = MessageFactory.text(prompt_text, prompt_text, InputHints.expecting_input)
        return await step_context.prompt(
            TextPrompt.__name__, PromptOptions(prompt=prompt_message)
        )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        cidade = step_context.result
        # TODO: Adicionar lógica para buscar e reservar hotel
        msg_text = f"Buscando hotéis em {cidade}... (funcionalidade em desenvolvimento)."
        await step_context.context.send_activity(MessageFactory.text(msg_text))
        return await step_context.end_dialog()
