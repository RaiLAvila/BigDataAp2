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
