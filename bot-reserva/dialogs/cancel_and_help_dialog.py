from botbuilder.dialogs import ComponentDialog, DialogContext, DialogTurnResult, DialogTurnStatus
from botbuilder.core import MessageFactory, TurnContext

class CancelAndHelpDialog(ComponentDialog):
    async def on_begin_dialog(self, inner_dc: DialogContext, options) -> DialogTurnResult:
        result = await self.interrupt(inner_dc)
        if result:
            return result
        return await super(CancelAndHelpDialog, self).on_begin_dialog(inner_dc, options)

    async def on_continue_dialog(self, inner_dc: DialogContext) -> DialogTurnResult:
        result = await self.interrupt(inner_dc)
        if result:
            return result
        return await super(CancelAndHelpDialog, self).on_continue_dialog(inner_dc)

    async def interrupt(self, inner_dc: DialogContext) -> DialogTurnResult:
        if inner_dc.context.activity.type == "message":
            text = inner_dc.context.activity.text.lower()

            if text in ("ajuda", "?"):
                await inner_dc.context.send_activity(MessageFactory.text("Mostrando ajuda..."))
                return DialogTurnResult(DialogTurnStatus.Waiting)

            if text in ("cancelar", "sair"):
                await inner_dc.context.send_activity(
                    MessageFactory.text("Cancelando...")
                )
                return await inner_dc.cancel_all_dialogs()
        return None
