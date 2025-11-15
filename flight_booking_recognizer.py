from botbuilder.ai.luis import LuisApplication, LuisPredictionOptions, LuisRecognizer
from botbuilder.core import TurnContext
from botbuilder.dialogs import Recognizer, RecognizerResult
from .configuration import DefaultConfig


class FlightBookingRecognizer(Recognizer):
    def __init__(self, configuration: DefaultConfig):
        self._recognizer = None
        luis_is_configured = (
            configuration.LUIS_APP_ID
            and configuration.LUIS_API_KEY
            and configuration.LUIS_API_HOST_NAME
        )
        if luis_is_configured:
            luis_application = LuisApplication(
                configuration.LUIS_APP_ID,
                configuration.LUIS_API_KEY,
                "https://" + configuration.LUIS_API_HOST_NAME,
            )

            options = LuisPredictionOptions()
            options.include_all_intents = True
            options.include_instance_data = True

            self._recognizer = LuisRecognizer(
                luis_application, prediction_options=options
            )

    @property
    def is_configured(self) -> bool:
        return self._recognizer is not None

    async def recognize(self, turn_context: TurnContext) -> RecognizerResult:
        return await self._recognizer.recognize(turn_context)