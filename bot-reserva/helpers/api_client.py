import requests
from config import DefaultConfig

CONFIG = DefaultConfig()
API_BASE_URL = CONFIG.API_BASE_URL

def criar_ou_buscar_cliente(cpf: str, nome: str = "", email: str = "", celular: str = ""):
    """
    Chama o endpoint do backend para criar um novo cliente ou buscar um existente pelo CPF.
    """
    url = f"{API_BASE_URL}/clientes"
    payload = {
        "cpf": cpf,
        "nome": nome,
        "email": email,
        "celular": celular
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Lança uma exceção para respostas com erro (4xx ou 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao chamar a API de clientes: {e}")
        return None

# Futuramente, adicionaremos aqui as funções para criar reservas de voo e hotel.
# def adicionar_reserva_voo(cliente_id: str, reserva_data: dict):
#     ...

# def adicionar_reserva_hotel(cliente_id: str, reserva_data: dict):
#     ...
