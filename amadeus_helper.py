from amadeus import Client, ResponseError
from config import DefaultConfig

amadeus = Client(
    client_id=DefaultConfig.AMADEUS_API_KEY,
    client_secret=DefaultConfig.AMADEUS_API_SECRET
)

def buscar_hoteis(cidade, checkin, checkout):
    try:
        response = amadeus.shopping.hotel_offers.get(
            cityCode=cidade,
            checkInDate=checkin,
            checkOutDate=checkout,
            adults=1
        )
        hoteis = response.data
        opcoes = []
        for i, h in enumerate(hoteis):
            nome = h['hotel']['name']
            estrelas = h['hotel'].get('rating', 'N/A')
            endereco = h['hotel']['address'].get('lines', [''])[0]
            preco = h['offers'][0]['price']['total'] if h.get('offers') else 'N/A'
            moeda = h['offers'][0]['price']['currency'] if h.get('offers') else ''
            opcoes.append(f"{i+1}. {nome} - {estrelas} estrelas - {endereco} - {preco} {moeda}")
        return opcoes
    except ResponseError as error:
        print(error)
        return []

def buscar_voos(origem, destino, data, adults=1):
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origem,
            destinationLocationCode=destino,
            departureDate=data,
            adults=adults,
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
