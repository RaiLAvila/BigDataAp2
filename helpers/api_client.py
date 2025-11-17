import requests
import json
from config import DefaultConfig

CONFIG = DefaultConfig()
API_BASE_URL = CONFIG.API_BASE_URL

def get_iata_code(city_name: str):
    """
    Busca o código IATA para uma cidade usando a API Java.
    """
    url = f"{API_BASE_URL}/locations/cities"
    params = {"keyword": city_name}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        api_data = response.json()
        if api_data and api_data.get("data"):
            # Assumindo que a API retorna uma lista e pegamos o primeiro resultado
            return api_data["data"][0]["iataCode"]
        return None
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar código IATA para '{city_name}': {e}")
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Erro ao processar a resposta da API para '{city_name}': {e}")
        return None


def search_flights(origin_iata: str, destination_iata: str, date: str, adults: int):
    """
    Busca voos usando a API Java.
    """
    url = f"{API_BASE_URL}/flights/search"
    params = {
        "origin": origin_iata,
        "destination": destination_iata,
        "departureDate": date,
        "adults": str(adults),
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return json.loads(response.text)  # A resposta já é um JSON
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar voos: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Erro ao processar a resposta de voos: {e}")
        return None


def search_hotels(city_code: str):
    """
    Busca hotéis em uma cidade usando a API Java.
    """
    url = f"{API_BASE_URL}/hotels/searchHotelsByCityCode"
    params = {"cityCode": city_code}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return json.loads(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar hotéis: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Erro ao processar a resposta de hotéis: {e}")
        return None


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

def adicionar_reserva_voo(cliente_id: str, reserva_data: dict):
    """
    Chama o endpoint do backend para criar uma nova reserva de voo.
    """
    url = f"{API_BASE_URL}/clientes/{cliente_id}/reservas/voo"
    try:
        response = requests.post(url, json=reserva_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao criar reserva de voo: {e}")
        return None

def adicionar_reserva_hotel(cliente_id: str, reserva_data: dict):
    """
    Chama o endpoint do backend para criar uma nova reserva de hotel.
    """
    url = f"{API_BASE_URL}/clientes/{cliente_id}/reservas/hotel"
    try:
        response = requests.post(url, json=reserva_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao criar reserva de hotel: {e}")
        return None

def consultar_reservas_voo(cpf: str):
    """
    Consulta as reservas de voo de um cliente pelo CPF.
    """
    url = f"{API_BASE_URL}/reservas/voo"
    params = {"cpf": cpf}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao consultar reservas de voo: {e}")
        return None

def consultar_reservas_hotel(cpf: str):
    """
    Consulta as reservas de hotel de um cliente pelo CPF.
    """
    url = f"{API_BASE_URL}/reservas/hotel"
    params = {"cpf": cpf}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao consultar reservas de hotel: {e}")
        return None

def cancelar_reserva_voo(reserva_id: str):
    """
    Cancela uma reserva de voo específica.
    """
    url = f"{API_BASE_URL}/reservas/voo/{reserva_id}"
    try:
        response = requests.delete(url)
        response.raise_for_status()
        return response.status_code == 204  # Sucesso sem conteúdo
    except requests.exceptions.RequestException as e:
        print(f"Erro ao cancelar reserva de voo: {e}")
        return False

def cancelar_reserva_hotel(reserva_id: str):
    """
    Cancela uma reserva de hotel específica.
    """
    url = f"{API_BASE_URL}/reservas/hotel/{reserva_id}"
    try:
        response = requests.delete(url)
        response.raise_for_status()
        return response.status_code == 204  # Sucesso sem conteúdo
    except requests.exceptions.RequestException as e:
        print(f"Erro ao cancelar reserva de hotel: {e}")
        return False
