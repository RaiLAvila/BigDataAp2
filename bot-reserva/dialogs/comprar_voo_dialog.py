from botbuilder.dialogs import (
    ComponentDialog, WaterfallDialog, WaterfallStepContext, DialogTurnResult
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions
from botbuilder.core import MessageFactory
from dialogs.consultar_cancelar_dialog import RESERVAS_MEMORIA

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
        # Se já veio origem do CLU, use, senão pergunte
        origem = getattr(step_context.options, "origin", None) if step_context.options else None
        if origem:
            step_context.values["origem"] = origem
            return await step_context.next(origem)
        return await step_context.prompt(
            "OrigemPrompt",
            PromptOptions(prompt=MessageFactory.text("De qual cidade você vai partir?"))
        )

    async def destino_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["origem"] = step_context.result
        destino = getattr(step_context.options, "destination", None) if step_context.options else None
        if destino:
            step_context.values["destino"] = destino
            return await step_context.next(destino)
        return await step_context.prompt(
            "DestinoPrompt",
            PromptOptions(prompt=MessageFactory.text("Para qual cidade você quer ir?"))
        )

    async def data_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["destino"] = step_context.result
        data = getattr(step_context.options, "departure_date", None) if step_context.options else None
        if data:
            step_context.values["data"] = data
            return await step_context.next(data)
        return await step_context.prompt(
            "DataPrompt",
            PromptOptions(prompt=MessageFactory.text("Qual a data do voo? (ex: 25/12/2026)"))
        )

    async def cpf_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["data"] = step_context.result
        return await step_context.prompt(
            "CpfPrompt",
            PromptOptions(prompt=MessageFactory.text("Informe seu CPF para associar a reserva:"))
        )

    async def opcoes_voo_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["cpf"] = step_context.result
        # Aqui futuramente será feita a chamada à API Amadeus
        opcoes = [
            "Voo 1: 10h - Companhia X - R$500",
            "Voo 2: 15h - Companhia Y - R$550",
            "Voo 3: 20h - Companhia Z - R$600"
        ]
        step_context.values["opcoes"] = opcoes
        opcoes_texto = "\n".join([f"{i+1}. {op}" for i, op in enumerate(opcoes)])
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
        reserva = f"Voo: {voo_escolhido} ({step_context.values['origem']} -> {step_context.values['destino']} em {step_context.values['data']})"
        RESERVAS_MEMORIA.setdefault(cpf, []).append(reserva)

        await step_context.context.send_activity(
            MessageFactory.text(
                f"Reserva realizada!\n{voo_escolhido}\nCPF: {cpf}\n"
                "Guarde seu CPF para consultar ou cancelar a reserva depois."
            )
        )
        return await step_context.end_dialog()
