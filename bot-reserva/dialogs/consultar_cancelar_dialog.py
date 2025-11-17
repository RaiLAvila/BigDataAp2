from botbuilder.dialogs import (
    ComponentDialog, WaterfallDialog, WaterfallStepContext, DialogTurnResult
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions
from botbuilder.core import MessageFactory

# Armazenamento simples em memória (global)
RESERVAS_MEMORIA = {}

class ConsultarCancelarDialog(ComponentDialog):
    def __init__(self, dialog_id: str = None):
        super().__init__(dialog_id or ConsultarCancelarDialog.__name__)

        self.add_dialog(TextPrompt("CpfPrompt"))
        self.add_dialog(TextPrompt("AcaoPrompt"))
        self.add_dialog(
            WaterfallDialog(
                "WFConsultarCancelar",
                [
                    self.cpf_step,
                    self.listar_reservas_step,
                    self.cancelar_step,
                ],
            )
        )
        self.initial_dialog_id = "WFConsultarCancelar"

    async def cpf_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        intent = step_context.options.get("intent") if step_context.options else None
        if intent == "ConsultarHotel":
            msg = "Informe seu CPF para consultar hotel."
        elif intent == "ConsultarVoo":
            msg = "Informe seu CPF para consultar voo."
        elif intent == "CancelarHotel":
            msg = "Informe seu CPF para cancelar hotel."
        elif intent == "CancelarVoo":
            msg = "Informe seu CPF para cancelar voo."
        else:
            msg = "Informe seu CPF para consultar ou cancelar reservas:"
        return await step_context.prompt(
            "CpfPrompt",
            PromptOptions(prompt=MessageFactory.text(msg))
        )

    async def listar_reservas_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        cpf = step_context.result
        step_context.values["cpf"] = cpf
        intent = step_context.options.get("intent") if step_context.options else None

        # Filtra reservas conforme a intenção
        reservas = RESERVAS_MEMORIA.get(cpf, [])
        if intent == "ConsultarHotel" or intent == "CancelarHotel":
            reservas_filtradas = [r for r in reservas if r.startswith("Hotel:")]
            tipo = "hotel"
        elif intent == "ConsultarVoo" or intent == "CancelarVoo":
            reservas_filtradas = [r for r in reservas if r.startswith("Voo:")]
            tipo = "voo"
        else:
            reservas_filtradas = reservas
            tipo = "reserva"

        step_context.values["reservas_filtradas"] = reservas_filtradas
        step_context.values["tipo"] = tipo
        step_context.values["intent"] = intent

        if not reservas_filtradas:
            await step_context.context.send_activity(f"Nenhuma {tipo} encontrada para este CPF.")
            return await step_context.end_dialog()

        reservas_texto = "\n".join([f"{i+1}. {r}" for i, r in enumerate(reservas_filtradas)])
        await step_context.context.send_activity(
            MessageFactory.text(f"{tipo.capitalize()}s encontradas:\n{reservas_texto}")
        )

        # Só pergunta sobre cancelamento se for intenção de cancelar
        if intent and intent.startswith("Cancelar"):
            return await step_context.prompt(
                "AcaoPrompt",
                PromptOptions(prompt=MessageFactory.text(
                    f"Se quiser cancelar alguma, informe o número da {tipo}. Caso contrário, digite 'não'."
                ))
            )
        else:
            return await step_context.end_dialog()

    async def cancelar_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        intent = step_context.values.get("intent")
        if not intent or not intent.startswith("Cancelar"):
            return await step_context.end_dialog()

        resposta = step_context.result
        cpf = step_context.values["cpf"]
        reservas_filtradas = step_context.values["reservas_filtradas"]
        tipo = step_context.values["tipo"]
        reservas = RESERVAS_MEMORIA.get(cpf, [])

        if resposta and resposta.lower() != "não":
            try:
                idx = int(resposta) - 1
                if idx < 0 or idx >= len(reservas_filtradas):
                    raise ValueError()
                reserva_cancelada = reservas_filtradas[idx]
                # Remove do total de reservas do CPF
                reservas.remove(reserva_cancelada)
                RESERVAS_MEMORIA[cpf] = reservas
                await step_context.context.send_activity(
                    MessageFactory.text(f"{tipo.capitalize()} cancelado(a): {reserva_cancelada}")
                )
            except Exception:
                await step_context.context.send_activity("Opção inválida. Nenhuma reserva foi cancelada.")
        else:
            await step_context.context.send_activity("Nenhuma reserva foi cancelada.")
        return await step_context.end_dialog()
