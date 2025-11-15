import os

class DefaultConfig:
    """Bot Configuration"""

    # ...existing code...
    LUIS_APP_ID = os.environ.get("LuisAppId", "d2e15483-b863-445c-9112-6da4188829e9")
    LUIS_API_KEY = os.environ.get("LuisAPIKey", "c434c036339944aaa8c755d3793eff40")
    LUIS_API_HOST_NAME = os.environ.get("LuisAPIHostName", "brazilsouth.api.cognitive.microsoft.com")
    LUIS_INTENT_COMPRAR = os.environ.get("LuisIntentComprar", "Comprar")
    LUIS_INTENT_CONSULTAR_VOO = os.environ.get("LuisIntentConsultarVoo", "Consultar_Voo")
    LUIS_INTENT_CANCELAR_VOO = os.environ.get("LuisIntentCancelarVoo", "Cancelar_Voo")
    LUIS_INTENT_RESERVAR_HOTEL = os.environ.get("LuisIntentReservarHotel", "Reservar_Hotel")
    LUIS_INTENT_CONSULTAR_HOTEL = os.environ.get("LuisIntentConsultarHotel", "Consultar_Hotel")
    LUIS_INTENT_CANCELAR_HOTEL = os.environ.get("LuisIntentCancelarHotel", "Cancelar_Hotel")