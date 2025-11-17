from azure.core.credentials import AzureKeyCredential
from azure.ai.language.conversations import ConversationAnalysisClient
from config import DefaultConfig

# Carrega a configuração
CONFIG = DefaultConfig()

def analyze_text_with_clu(text: str):
    """
    Analisa o texto do usuário usando o serviço de Conversational Language Understanding (CLU).
    """
    # Cria o cliente de análise de conversação com o endpoint e a chave da API corretos
    client = ConversationAnalysisClient(
        CONFIG.CLU_ENDPOINT, AzureKeyCredential(CONFIG.CLU_API_KEY)
    )

    # Monta a requisição para o CLU
    with client:
        result = client.analyze_conversation(
            task={
                "kind": "Conversation",
                "analysisInput": {
                    "conversationItem": {
                        "id": "1",
                        "participantId": "1",
                        "text": text,
                    },
                    "isLoggingEnabled": False,
                },
                "parameters": {
                    "projectName": CONFIG.CLU_PROJECT_NAME,
                    "deploymentName": CONFIG.CLU_DEPLOYMENT_NAME,
                    "verbose": True,
                },
            }
        )
    
    # Retorna o resultado da análise
    return result
