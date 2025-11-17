from enum import Enum

class Intent(Enum):
    CANCELAR_HOTEL = "CancelarHotel"
    CANCELAR_VOO = "CancelarVoo"
    COMPRAR_VOO = "ComprarVoo"
    CONSULTAR_HOTEL = "ConsultarHotel"
    CONSULTAR_VOO = "ConsultarVoo"
    RESERVAR_HOTEL = "ReservarHotel"