import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

# Načtení proměnných prostředí z .env souboru
load_dotenv()

# Získání API klíčů z proměnných prostředí
api_key = os.getenv("ALPACA_API_KEY")
api_secret = os.getenv("ALPACA_SECRET_KEY")
base_url = os.getenv("ALPACA_BASE_URL")

print(f"API Key: {api_key}")
print(f"API Secret: {api_secret}")
print(f"Base URL: {base_url}")

# Inicializace Alpaca API
api = tradeapi.REST(api_key, api_secret, base_url, api_version="v2")

try:
    # Pokus o získání informací o účtu
    account = api.get_account()
    print(f"Účet je aktivní: {account.status}")
    print(f"Hotovost: ${account.cash}")
    print(f"Hodnota portfolia: ${account.portfolio_value}")
    print(f"Nákupní síla: ${account.buying_power}")
except Exception as e:
    print(f"Chyba při připojení k Alpaca API: {e}")
