from botbuilder.dialogs import (
    ComponentDialog, WaterfallDialog, WaterfallStepContext, DialogTurnResult
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions
from botbuilder.core import MessageFactory
from dialogs.consultar_cancelar_dialog import RESERVAS_MEMORIA
from amadeus_helper import buscar_voos

class ComprarVooDialog(ComponentDialog):
    def __init__(self, dialog_id: str = None):
        super().__init__(dialog_id or ComprarVooDialog.__name__)

        self.add_dialog(TextPrompt("OrigemPrompt"))
        self.add_dialog(TextPrompt("DestinoPrompt"))
        self.add_dialog(TextPrompt("DataPrompt"))
        self.add_dialog(TextPrompt("CpfPrompt"))
        self.add_dialog(
            WaterfallDialog(
                "WFComprarVoo",
                [
                    self.origem_step,
                    self.destino_step,
                    self.data_step,
                    self.cpf_step,
                    self.opcoes_voo_step,
                    self.confirmacao_step,
                ],
            )
        )
        self.initial_dialog_id = "WFComprarVoo"

    async def origem_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        origem = getattr(step_context.options, "origin", None) if step_context.options else None
        if origem:
            step_context.values["origem"] = origem
            return await step_context.next(origem)
        return await step_context.prompt(
            "OrigemPrompt",
            PromptOptions(prompt=MessageFactory.text("Qual a origem? (Exemplo: PAR para Paris)"))
        )

    async def destino_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["origem"] = step_context.result
        destino = getattr(step_context.options, "destination", None) if step_context.options else None
        if destino:
            step_context.values["destino"] = destino
            return await step_context.next(destino)
        return await step_context.prompt(
            "DestinoPrompt",
            PromptOptions(prompt=MessageFactory.text("Qual o destino? (Exemplo: MAD para Madrid)"))
        )

    async def data_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["destino"] = step_context.result
        data = getattr(step_context.options, "departure_date", None) if step_context.options else None
        if data:
            step_context.values["data"] = data
            return await step_context.next(data)
        return await step_context.prompt(
            "DataPrompt",
            PromptOptions(prompt=MessageFactory.text("Qual a data do voo? (Exemplo: 2025-11-20)"))
        )

    async def cpf_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["data"] = step_context.result
        return await step_context.prompt(
            "CpfPrompt",
            PromptOptions(prompt=MessageFactory.text("Informe seu CPF para associar a reserva:"))
        )

    async def opcoes_voo_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["cpf"] = step_context.result
        origem = step_context.values["origem"]
        destino = step_context.values["destino"]
        data = step_context.values["data"]
        opcoes = buscar_voos(origem, destino, data)
        if not opcoes:
            await step_context.context.send_activity("Nenhuma opção de voo encontrada para os dados informados.")
            return await step_context.end_dialog()
        step_context.values["opcoes"] = opcoes
        opcoes_texto = "\n".join(opcoes)
        return await step_context.prompt(
            "DataPrompt",
            PromptOptions(prompt=MessageFactory.text(f"Escolha uma opção de voo:\n{opcoes_texto}\nDigite o número da opção:"))
        )

    async def confirmacao_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        escolha = step_context.result
        opcoes = step_context.values["opcoes"]
        try:
            idx = int(escolha) - 1
            if idx < 0 or idx >= len(opcoes):
                raise ValueError()
            voo_escolhido = opcoes[idx]
        except Exception:
            await step_context.context.send_activity("Opção inválida. Reserva não realizada.")
            return await step_context.end_dialog()

        cpf = step_context.values['cpf']
        reserva = f"Voo: {voo_escolhido} (CPF: {cpf})"
        RESERVAS_MEMORIA.setdefault(cpf, []).append(reserva)

        await step_context.context.send_activity(
            MessageFactory.text(
                f"Reserva realizada!\n{voo_escolhido}\nCPF: {cpf}\n"
                "Guarde seu CPF para consultar ou cancelar a reserva depois."
            )
        )
        return await step_context.end_dialog()
