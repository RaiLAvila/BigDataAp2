from amadeus import Client, ResponseError
from config import DefaultConfig

amadeus = Client(
    client_id=DefaultConfig.AMADEUS_API_KEY,
    client_secret=DefaultConfig.AMADEUS_API_SECRET
)

def listar_hotel_ids(city_code):
    try:
        response = amadeus.reference_data.locations.hotels.by_city.get(cityCode=city_code)
        print(f"HotelIds encontrados para {city_code}:")
        for h in response.data:
            hotel_id = h['hotelId']
            nome = h.get('name', '')
            print(f"{hotel_id} - {nome}")
    except ResponseError as error:
        print("Erro Amadeus:", error.response.body)

if __name__ == "__main__":
    # Exemplo: listar hotelIds para Paris (PAR)
    listar_hotel_ids("PAR")
