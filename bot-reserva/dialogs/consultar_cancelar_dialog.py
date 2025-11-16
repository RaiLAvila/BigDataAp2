from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import TextPrompt, ChoicePrompt, ConfirmPrompt, PromptOptions, Choice
from botbuilder.core import MessageFactory

from .cancel_and_help_dialog import CancelAndHelpDialog
from helpers import api_client

class ConsultarCancelarDialog(CancelAndHelpDialog):
    def __init__(self, dialog_id: str = None):
        super(ConsultarCancelarDialog, self).__init__(dialog_id or ConsultarCancelarDialog.__name__)

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(ChoicePrompt(ChoicePrompt.__name__))
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.cpf_step,
                    self.show_reservations_step,
                    self.action_step,
                    self.confirm_cancel_step,
                    self.final_step,
                ],
            )
        )

        self.initial_dialog_id = WaterfallDialog.__name__
        self.intent = None

    async def cpf_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.intent = step_context.options.get("intent")
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Por favor, informe seu CPF para consulta.")),
        )

    async def show_reservations_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        cpf = step_context.result
        step_context.values["cpf"] = cpf
        
        await step_context.context.send_activity(MessageFactory.text("Buscando suas reservas..."))
        
        voos = api_client.consultar_reservas_voo(cpf) or []
        hoteis = api_client.consultar_reservas_hotel(cpf) or []
        
        reservas = voos + hoteis
        step_context.values["reservas"] = reservas

        if not reservas:
            await step_context.context.send_activity(MessageFactory.text("Não encontrei nenhuma reserva no seu CPF."))
            return await step_context.end_dialog()

        if self.intent == "ConsultarReservas":
            await step_context.context.send_activity(MessageFactory.text("Aqui estão suas reservas:"))
            for r in reservas:
                tipo = "Voo" if "itineraries" in r else "Hotel"
                msg = f"Reserva de {tipo} - ID: {r.get('id')}"
                await step_context.context.send_activity(MessageFactory.text(msg))
            return await step_context.end_dialog()

        # Para cancelamento
        choices = []
        for r in reservas:
            tipo = "Voo" if "itineraries" in r else "Hotel"
            label = f"Reserva de {tipo} - ID: {r.get('id')}"
            choices.append(Choice(value=f"{tipo.lower()}_{r.get('id')}", title=label))
        
        choices.append(Choice(value="nenhuma", title="Nenhuma, obrigado"))
        
        return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Qual reserva você gostaria de cancelar?"),
                choices=choices,
            ),
        )

    async def action_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        choice = step_context.result.value
        if choice == "nenhuma":
            await step_context.context.send_activity(MessageFactory.text("Ok, nenhuma reserva foi cancelada."))
            return await step_context.end_dialog()
        
        step_context.values["reserva_para_cancelar"] = choice
        return await step_context.next(True) # Pula para o próximo passo

    async def confirm_cancel_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Você tem certeza que deseja cancelar esta reserva?")),
        )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result:
            reserva_id_str = step_context.values["reserva_para_cancelar"]
            tipo, reserva_id = reserva_id_str.split("_")

            success = False
            if tipo == "voo":
                success = api_client.cancelar_reserva_voo(reserva_id)
            elif tipo == "hotel":
                success = api_client.cancelar_reserva_hotel(reserva_id)

            if success:
                await step_context.context.send_activity(MessageFactory.text("Sua reserva foi cancelada com sucesso."))
            else:
                await step_context.context.send_activity(MessageFactory.text("Houve um erro ao cancelar sua reserva."))
        else:
            await step_context.context.send_activity(MessageFactory.text("A reserva não foi cancelada."))
        
        return await step_context.end_dialog()
