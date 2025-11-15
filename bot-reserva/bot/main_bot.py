from botbuilder.core import ActivityHandler, TurnContext, ConversationState, UserState
from botbuilder.schema import ChannelAccount
from botbuilder.dialogs import Dialog

# Dicionário simples para códigos IATA de cidades comuns
CITY_IATA = {
    "rio de janeiro": "RIO",
    "rio": "RIO",
    "são paulo": "SAO",
    "sao paulo": "SAO",
    "sp": "SAO",
    "guarulhos": "GRU",
    "campinas": "VCP",
    "brasilia": "BSB",
    "belo horizonte": "CNF",
    "salvador": "SSA",
    "recife": "REC",
    "fortaleza": "FOR"
}

class TravelBot(ActivityHandler):
    def __init__(self, conversation_state: ConversationState, user_state: UserState, dialog):
        self.conversation_state = conversation_state
        self.user_state = user_state
        self.dialog = dialog
        self.dialog_state_property = self.conversation_state.create_property("DialogState")
        self.user_flow_state = {}

    async def on_turn(self, turn_context: TurnContext):
        text = (turn_context.activity.text or "").strip().lower()
        user_id = turn_context.activity.from_property.id
        state = self.user_flow_state.get(user_id, {"stage": "menu"})

        def normalize_date(date_str):
            return date_str.replace("/", "-").strip()

        def get_city_code(city_name):
            return CITY_IATA.get(city_name.lower(), city_name.upper()[:3])

        # Reinicia conversa se usuário disser saudação
        if text in ["olá", "oi", "bom dia", "boa tarde", "boa noite"]:
            self.user_flow_state[user_id] = {"stage": "menu"}
            await turn_context.send_activity("Bem-vindo ao Bot de Hotel e Voo do André e do Raí.")
            await turn_context.send_activity("O que você deseja fazer? (Ex: reservar hotel, comprar passagem, consultar/cancelar reserva)")
            return

        # MENU: Detecta intenção e inicia fluxo correto
        if state["stage"] == "menu":
            clu_result = getattr(turn_context.activity, "additional_properties", {}).get("clu_result")
            if clu_result:
                intent = clu_result.get("result", {}).get("prediction", {}).get("topIntent")
                if intent and intent != "None":
                    state["intent"] = intent
                    state["stage"] = "collect"
                    state["data"] = {}
                    self.user_flow_state[user_id] = state
                    if intent == "ReservarHotel":
                        await turn_context.send_activity("Ótimo! Para qual cidade você deseja reservar o hotel?")
                        return
                    elif intent == "ComprarVoo":
                        await turn_context.send_activity("Perfeito! Qual a cidade de origem do voo?")
                        return
                    elif intent == "ConsultarHotel":
                        await turn_context.send_activity("Informe o código ou nome da sua reserva de hotel.")
                        return
                    elif intent == "CancelarHotel":
                        await turn_context.send_activity("Informe o código ou nome da reserva de hotel que deseja cancelar.")
                        return
                    elif intent == "ConsultarVoo":
                        await turn_context.send_activity("Informe o código ou nome da sua reserva de voo.")
                        return
                    elif intent == "CancelarVoo":
                        await turn_context.send_activity("Informe o código ou nome da reserva de voo que deseja cancelar.")
                        return
                    else:
                        await turn_context.send_activity("Desculpe, ainda não sei como tratar essa intenção.")
                        self.user_flow_state[user_id] = {"stage": "menu"}
                        await turn_context.send_activity("O que você deseja fazer?")
                        return
                else:
                    await turn_context.send_activity("Desculpe, não entendi sua solicitação. O que você deseja fazer?")
                    return
            else:
                await turn_context.send_activity("O que você deseja fazer? (Ex: reservar hotel, comprar passagem, consultar/cancelar reserva)")
                return

        # FLUXO DE RESERVA DE HOTEL
        if state.get("intent") == "ReservarHotel" and state["stage"] == "collect":
            data = state["data"]
            if "cidade" not in data:
                data["cidade"] = turn_context.activity.text
                await turn_context.send_activity("Qual a data de check-in? (AAAA-MM-DD)")
                return
            if "checkin" not in data:
                data["checkin"] = normalize_date(turn_context.activity.text)
                await turn_context.send_activity("Qual a data de check-out? (AAAA-MM-DD)")
                return
            if "checkout" not in data:
                data["checkout"] = normalize_date(turn_context.activity.text)
                await turn_context.send_activity("Quantos adultos?")
                return
            if "adults" not in data:
                data["adults"] = turn_context.activity.text
                try:
                    city_code = get_city_code(data["cidade"])
                    # DEBUG: Mostra parâmetros usados
                    await turn_context.send_activity(f"[DEBUG] cityCode={city_code}, checkIn={data['checkin']}, checkOut={data['checkout']}")
                    hotels = self.amadeus.search_hotels(
                        city_code=city_code,
                        check_in_date=data["checkin"],
                        check_out_date=data["checkout"]
                    )
                    offers = hotels.get("data", [])
                    if offers:
                        msg = f"Encontrei {len(offers)} hotéis em {data['cidade']} de {data['checkin']} a {data['checkout']}.\n"
                        nomes = [h['hotel']['name'] for h in offers[:3] if 'hotel' in h and 'name' in h['hotel']]
                        msg += "Opções: " + ", ".join(nomes)
                    else:
                        msg = "Não encontrei hotéis para os critérios informados."
                    await turn_context.send_activity(msg)
                except Exception as e:
                    await turn_context.send_activity(f"Erro ao consultar hotéis: {e}")
                self.user_flow_state[user_id] = {"stage": "menu"}
                await turn_context.send_activity("O que você deseja fazer agora?")
                return

        # FLUXO DE COMPRA DE VOO
        if state.get("intent") == "ComprarVoo" and state["stage"] == "collect":
            data = state["data"]
            if "origem" not in data:
                data["origem"] = turn_context.activity.text
                await turn_context.send_activity("Qual a cidade de destino do voo?")
                return
            if "destino" not in data:
                data["destino"] = turn_context.activity.text
                await turn_context.send_activity("Qual a data do voo? (AAAA-MM-DD)")
                return
            if "data_voo" not in data:
                data["data_voo"] = normalize_date(turn_context.activity.text)
                # Busca voos reais no Amadeus
                try:
                    origin_code = get_city_code(data["origem"])
                    dest_code = get_city_code(data["destino"])
                    flights = self.amadeus.search_flights(
                        origin=origin_code,
                        destination=dest_code,
                        departure_date=data["data_voo"]
                    )
                    offers = flights.get("data", [])
                    if offers:
                        msg = f"Encontrei {len(offers)} voos de {data['origem']} para {data['destino']} em {data['data_voo']}.\n"
                        companhias = [f['itineraries'][0]['segments'][0]['carrierCode'] for f in offers[:3] if 'itineraries' in f and f['itineraries']]
                        msg += "Opções de companhias: " + ", ".join(companhias)
                    else:
                        msg = "Não encontrei voos para os critérios informados."
                    await turn_context.send_activity(msg)
                except Exception as e:
                    await turn_context.send_activity(f"Erro ao consultar voos: {e}")
                # Volta ao menu
                self.user_flow_state[user_id] = {"stage": "menu"}
                await turn_context.send_activity("O que você deseja fazer agora?")
                return

        # FLUXOS DE CONSULTA/CANCELAMENTO (simulação)
        if state.get("intent") in ["ConsultarHotel", "CancelarHotel", "ConsultarVoo", "CancelarVoo"] and state["stage"] == "collect":
            await turn_context.send_activity(f"Fluxo de {state['intent']} ainda não implementado. Voltando ao menu.")
            self.user_flow_state[user_id] = {"stage": "menu"}
            await turn_context.send_activity("O que você deseja fazer agora?")
            return

        # Se nada foi tratado, volta ao menu
        await turn_context.send_activity("O que você deseja fazer? (Ex: reservar hotel, comprar passagem, consultar/cancelar reserva)")

        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)