#!/usr/bin/env python3

import alpaca_trade_api as tradeapi

# API klíče
ALPACA_API_KEY = "AKJYB42QYBVD1EKBDQJ8"
ALPACA_API_SECRET = "SczRiShhbzjejIYP8KKcg50XIhJMIyR895vi1hGI"
ALPACA_BASE_URL = "https://api.alpaca.markets"

# Vytvoření API klienta
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_API_SECRET, ALPACA_BASE_URL)

# Získání informací o účtu
account = api.get_account()
print(f"ID účtu: {account.id}")
print(f"Status účtu: {account.status}")
print(f"Hotovost: ${float(account.cash):.2f}")
print(f"Hodnota portfolia: ${float(account.portfolio_value):.2f}")

# Získání pozic
positions = api.list_positions()
print(f"\nAktuální pozice ({len(positions)}):")
for position in positions:
    print(f"  {position.symbol}: {position.qty} @ ${float(position.avg_entry_price):.2f} | Aktuální cena: ${float(position.current_price):.2f} | P/L: ${float(position.unrealized_pl):.2f}")

# Získání objednávek
orders = api.list_orders(status="open")
print(f"\nAktuální objednávky ({len(orders)}):")
for order in orders:
    print(f"  {order.symbol}: {order.side.upper()} {order.qty} ({order.type}) | Status: {order.status}")
