from amadeus import Client
from config import DefaultConfig

# Carrega as configurações que contêm as chaves da API
CONFIG = DefaultConfig()

# Cria a instância do cliente Amadeus com as credenciais
# e a disponibiliza para ser importada em outros arquivos.
amadeus = Client(
    client_id=CONFIG.AMADEUS_API_KEY,
    client_secret=CONFIG.AMADEUS_API_SECRET,
)
