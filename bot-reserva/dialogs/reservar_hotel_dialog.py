from botbuilder.dialogs import (
    ComponentDialog, WaterfallDialog, WaterfallStepContext, DialogTurnResult
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions
from botbuilder.core import MessageFactory
from dialogs.consultar_cancelar_dialog import RESERVAS_MEMORIA

class ReservarHotelDialog(ComponentDialog):
    def __init__(self, dialog_id: str = None):
        super().__init__(dialog_id or ReservarHotelDialog.__name__)

        self.add_dialog(TextPrompt("CidadePrompt"))
        self.add_dialog(TextPrompt("CheckinPrompt"))
        self.add_dialog(TextPrompt("CheckoutPrompt"))
        self.add_dialog(TextPrompt("CpfPrompt"))
        self.add_dialog(
            WaterfallDialog(
                "WFReservarHotel",
                [
                    self.cidade_step,
                    self.checkin_step,
                    self.checkout_step,
                    self.cpf_step,
                    self.opcoes_hotel_step,
                    self.confirmacao_step,
                ],
            )
        )
        self.initial_dialog_id = "WFReservarHotel"

    async def cidade_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        cidade = getattr(step_context.options, "destination", None) if step_context.options else None
        if cidade:
            step_context.values["cidade"] = cidade
            return await step_context.next(cidade)
        return await step_context.prompt(
            "CidadePrompt",
            PromptOptions(prompt=MessageFactory.text("Para qual cidade você deseja reservar o hotel?"))
        )

    async def checkin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["cidade"] = step_context.result
        checkin = getattr(step_context.options, "checkin_date", None) if step_context.options else None
        if checkin:
            step_context.values["checkin"] = checkin
            return await step_context.next(checkin)
        return await step_context.prompt(
            "CheckinPrompt",
            PromptOptions(prompt=MessageFactory.text("Qual a data de entrada? (ex: 25/12/2026)"))
        )

    async def checkout_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["checkin"] = step_context.result
        return await step_context.prompt(
            "CheckoutPrompt",
            PromptOptions(prompt=MessageFactory.text("Qual a data de saída? (ex: 30/12/2026)"))
        )

    async def cpf_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["checkout"] = step_context.result
        return await step_context.prompt(
            "CpfPrompt",
            PromptOptions(prompt=MessageFactory.text("Informe seu CPF para associar a reserva:"))
        )

    async def opcoes_hotel_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["cpf"] = step_context.result
        # Aqui futuramente será feita a chamada à API Amadeus
        opcoes = [
            "Hotel A - 4 estrelas - R$400/noite",
            "Hotel B - 3 estrelas - R$300/noite",
            "Hotel C - 5 estrelas - R$600/noite"
        ]
        step_context.values["opcoes"] = opcoes
        opcoes_texto = "\n".join([f"{i+1}. {op}" for i, op in enumerate(opcoes)])
        return await step_context.prompt(
            "CheckinPrompt",
            PromptOptions(prompt=MessageFactory.text(f"Escolha uma opção de hotel:\n{opcoes_texto}\nDigite o número da opção:"))
        )

    async def confirmacao_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        escolha = step_context.result
        opcoes = step_context.values["opcoes"]
        try:
            idx = int(escolha) - 1
            if idx < 0 or idx >= len(opcoes):
                raise ValueError()
            hotel_escolhido = opcoes[idx]
        except Exception:
            await step_context.context.send_activity("Opção inválida. Reserva não realizada.")
            return await step_context.end_dialog()

        cpf = step_context.values['cpf']
        reserva = f"Hotel: {hotel_escolhido} ({step_context.values['cidade']} de {step_context.values['checkin']} a {step_context.values['checkout']})"
        RESERVAS_MEMORIA.setdefault(cpf, []).append(reserva)

        await step_context.context.send_activity(
            MessageFactory.text(
                f"Reserva realizada!\n{hotel_escolhido}\nCPF: {cpf}\n"
                "Guarde seu CPF para consultar ou cancelar a reserva depois."
            )
        )
        return await step_context.end_dialog()
