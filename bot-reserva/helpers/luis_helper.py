from enum import Enum
from botbuilder.core import TurnContext
from typing import Dict

class Intent(Enum):
    COMPRAR_VOO = "ComprarVoo"
    RESERVAR_HOTEL = "ReservarHotel"
    CONSULTAR_HOTEL = "ConsultarHotel"
    CONSULTAR_VOO = "ConsultarVoo"
    CANCELAR_HOTEL = "CancelarHotel"
    CANCELAR_VOO = "CancelarVoo"
    NONE_INTENT = "None"

class LuisResult:
    def __init__(self, top_intent: str = None, entities: Dict = None):
        self.top_intent = top_intent or Intent.NONE_INTENT.value
        self.entities = entities or {}
        
        # Extrai as entidades mais comuns para fácil acesso
        self.origin = self._get_first_entity_value("origem")
        self.destination = self._get_first_entity_value("destino")
        self.departure_date = self._get_first_entity_value("data_partida")
        self.checkin_date = self._get_first_entity_value("data_checkin")

    def _get_first_entity_value(self, entity_name: str):
        """ Pega o primeiro valor de uma entidade, já que o CLU pode retornar múltiplos. """
        if entity_name in self.entities and self.entities[entity_name]:
            return self.entities[entity_name][0].get("text")
        return None

class LuisHelper:
    @staticmethod
    async def execute_luis_query(
        clu_recognizer: dict, turn_context: TurnContext
    ) -> LuisResult:
        
        try:
            clu_client = clu_recognizer["client"]
            result = clu_client.analyze_conversation(
                task={
                    "kind": "Conversation",
                    "analysisInput": {
                        "conversationItem": {
                            "participantId": turn_context.activity.from_property.id,
                            "id": turn_context.activity.id,
                            "text": turn_context.activity.text,
                        },
                        "isLoggingEnabled": False,
                    },
                    "parameters": {
                        "projectName": clu_recognizer["project_name"],
                        "deploymentName": clu_recognizer["deployment_name"],
                        "verbose": True,
                    },
                }
            )
            
            if not result or not result.get("result"):
                return LuisResult()

            prediction = result["result"]["prediction"]
            top_intent = prediction.get("topIntent")
            
            entities_result = {}
            for entity in prediction.get("entities", []):
                category = entity.get("category")
                if category not in entities_result:
                    entities_result[category] = []
                entities_result[category].append(entity)

            return LuisResult(top_intent, entities_result)

        except Exception as e:
            print(f"Erro ao chamar o CLU: {e}")
            return LuisResult()
