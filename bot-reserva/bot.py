from botbuilder.core import ActivityHandler, TurnContext, ConversationState, UserState
from botbuilder.dialogs import Dialog, DialogSet, DialogTurnStatus

class DialogBot(ActivityHandler):
    def __init__(self, conversation_state: ConversationState, user_state: UserState, dialog: Dialog):
        self.conversation_state = conversation_state
        self.user_state = user_state
        self.dialog = dialog
        self.dialog_state = self.conversation_state.create_property("DialogState")

    async def on_message_activity(self, turn_context: TurnContext):
        dialog_set = DialogSet(self.dialog_state)
        dialog_set.add(self.dialog)

        dialog_context = await dialog_set.create_context(turn_context)
        results = await dialog_context.continue_dialog()

        if results.status == DialogTurnStatus.Empty:
            await dialog_context.begin_dialog(self.dialog.id)

        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)
