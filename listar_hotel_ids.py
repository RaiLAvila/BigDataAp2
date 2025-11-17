from amadeus import Client, ResponseError
from bot_reserva.config import DefaultConfig  # ajuste o import conforme o nome do diretório

amadeus = Client(
    client_id=DefaultConfig.AMADEUS_API_KEY,
    client_secret=DefaultConfig.AMADEUS_API_SECRET
)

def listar_hotel_ids(city_code):
    try:
        response = amadeus.reference_data.locations.hotels.by_city.get(cityCode=city_code)
        hotel_ids = [h['hotelId'] for h in response.data]
        print(f"HotelIds encontrados para {city_code}:")
        for hotel_id in hotel_ids:
            print(hotel_id)
    except ResponseError as error:
        print("Erro Amadeus:", error.response.body)

if __name__ == "__main__":
    # Exemplo: listar hotelIds para Paris (PAR)
    listar_hotel_ids("PAR")
