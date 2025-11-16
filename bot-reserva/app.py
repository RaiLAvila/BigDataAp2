import sys
import traceback
from datetime import datetime

from aiohttp import web
from aiohttp.web import Request, Response, json_response
from botbuilder.core import (
    BotFrameworkAdapterSettings,
    TurnContext,
    BotFrameworkAdapter,
    ConversationState,
    UserState,
    MemoryStorage,
)
from botbuilder.schema import Activity, ActivityTypes

# Alteração: Importando as ferramentas corretas para CLU
from azure.core.credentials import AzureKeyCredential
from azure.ai.language.conversations import ConversationAnalysisClient

from config import DefaultConfig
from dialogs.main_dialog import MainDialog
from bot import DialogBot

CONFIG = DefaultConfig()

# Criar adaptador
SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

# --- Configuração do Reconhecedor CLU ---
# Alteração: Usando a configuração moderna e correta para CLU
clu_credential = AzureKeyCredential(CONFIG.CLU_API_KEY)
clu_client = ConversationAnalysisClient(endpoint=CONFIG.CLU_ENDPOINT, credential=clu_credential)
# Passamos o cliente CLU diretamente para o diálogo principal
clu_recognizer = {
    "client": clu_client,
    "project_name": CONFIG.CLU_PROJECT_NAME,
    "deployment_name": CONFIG.CLU_DEPLOYMENT_NAME,
}


# Criar armazenamento, estado do usuário e estado da conversa
MEMORY = MemoryStorage()
USER_STATE = UserState(MEMORY)
CONVERSATION_STATE = ConversationState(MEMORY)

# Criar diálogo principal e bot
DIALOG = MainDialog(clu_recognizer)
BOT = DialogBot(CONVERSATION_STATE, USER_STATE, DIALOG)


# Interceptador de erros
async def on_error(context: TurnContext, error: Exception):
    print(f"\n [on_turn_error] Ocorreu um erro: {error}", file=sys.stderr)
    traceback.print_exc()

    # Enviar mensagem de erro para o usuário
    await context.send_activity("Desculpe, ocorreu um erro.")
    await context.send_activity("Para recomeçar, digite 'olá'.")
    
    # Limpar o estado da conversa
    await CONVERSATION_STATE.delete(context)

ADAPTER.on_turn_error = on_error

# Função para processar as requisições do adaptador
async def messages(req: Request) -> Response:
    # Transformar o corpo da requisição em um objeto Activity
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    # Processar a atividade através do adaptador
    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    if response:
        return json_response(data=response.body, status=response.status)
    return Response(status=HTTPStatus.OK)

# Configurar rotas web
APP = web.Application(middlewares=[aiohttp_error_middleware])
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        web.run_app(APP, host="localhost", port=CONFIG.PORT)
    except Exception as error:
        raise error