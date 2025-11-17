import requests
from config import DefaultConfig
from amadeus import Client, ResponseError

# URL base do ambiente de teste Amadeus v3
BASE_URL = "https://test.api.amadeus.com"

amadeus = Client(
    client_id=DefaultConfig.AMADEUS_API_KEY,
    client_secret=DefaultConfig.AMADEUS_API_SECRET
)

def get_amadeus_token():
    url = f"{BASE_URL}/v1/security/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": DefaultConfig.AMADEUS_API_KEY,
        "client_secret": DefaultConfig.AMADEUS_API_SECRET,
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

def buscar_hoteis(hotel_ids, checkin, checkout, adultos=1):
    token = get_amadeus_token()
    url = f"{BASE_URL}/v3/shopping/hotel-offers"
    # Use até 50 hotelIds para aumentar as chances
    ids_para_busca = hotel_ids[:50] if len(hotel_ids) > 50 else hotel_ids
    params = {
        "hotelIds": ",".join(ids_para_busca),
        "adults": adultos,
        "checkInDate": checkin,
        "checkOutDate": checkout,
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        print("Erro Amadeus:", response.text)
        return []
    data = response.json()
    opcoes = []
    for i, hotel in enumerate(data.get("data", [])):
        nome = hotel.get("hotel", {}).get("name", "Hotel desconhecido")
        estrelas = hotel.get("hotel", {}).get("rating", "N/A")
        endereco = hotel.get("hotel", {}).get("address", {}).get("lines", [""])[0]
        offers = hotel.get("offers", [])
        if offers:
            preco = offers[0].get("price", {}).get("total", "N/A")
            moeda = offers[0].get("price", {}).get("currency", "")
        else:
            preco = "N/A"
            moeda = ""
        opcoes.append(f"{i+1}. {nome} - {estrelas} estrelas - {endereco} - {preco} {moeda}")
    return opcoes

def buscar_voos(origem, destino, data, adultos=1):
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origem,
            destinationLocationCode=destino,
            departureDate=data,
            adults=adultos,
            max=5
        )
        voos = response.data
        opcoes = []
        for i, v in enumerate(voos):
            segmento = v['itineraries'][0]['segments'][0]
            partida = segmento['departure']['at']
            chegada = segmento['arrival']['at']
            cia = segmento['carrierCode']
            preco = v['price']['total']
            moeda = v['price']['currency']
            opcoes.append(f"{i+1}. {origem}->{destino} {partida[:10]} {partida[11:16]}-{chegada[11:16]} {cia} - {preco} {moeda}")
        return opcoes
    except ResponseError as error:
        print("Erro Amadeus (voos):", error.response.body)
        return []
