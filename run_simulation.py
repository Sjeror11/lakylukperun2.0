#!/usr/bin/env python3
"""
Jednoduchý skript pro spuštění Perun Trading System v simulačním režimu.
"""

import os
import sys
import time
import random
from datetime import datetime

# Nastavení simulačního režimu
print("=" * 50)
print("PERUN TRADING SYSTEM - SIMULAČNÍ REŽIM")
print("=" * 50)
print("Spouštím v simulačním režimu s generovanými daty.")
print("Žádné skutečné obchody nebudou provedeny.")
print("=" * 50)

# Simulace obchodování
symbols = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA"]
portfolio = {
    "cash": 100000.0,
    "equity": 100000.0,
    "positions": {}
}

def generate_price(symbol, base_price=None):
    """Generuje náhodnou cenu pro symbol."""
    if base_price is None:
        # Základní ceny pro známé symboly
        base_prices = {
            "AAPL": 170.0,
            "MSFT": 350.0,
            "GOOG": 140.0,
            "AMZN": 180.0,
            "TSLA": 180.0
        }
        base_price = base_prices.get(symbol, random.uniform(50.0, 500.0))
    
    # Náhodná změna ceny (-1% až +1%)
    change = random.uniform(-0.01, 0.01)
    return base_price * (1 + change)

def simulate_market():
    """Simuluje tržní data."""
    market_data = {}
    for symbol in symbols:
        price = generate_price(symbol)
        market_data[symbol] = {
            "price": price,
            "change": random.uniform(-0.05, 0.05),
            "volume": random.randint(100000, 10000000)
        }
    return market_data

def simulate_trade(symbol, side, quantity, price):
    """Simuluje obchod."""
    if side == "BUY":
        cost = quantity * price
        if cost > portfolio["cash"]:
            print(f"⚠️ Nedostatek hotovosti pro nákup {quantity} akcií {symbol} za ${price:.2f} (celkem ${cost:.2f})")
            return False
        
        portfolio["cash"] -= cost
        if symbol in portfolio["positions"]:
            # Aktualizace existující pozice
            position = portfolio["positions"][symbol]
            total_qty = position["quantity"] + quantity
            total_cost = position["quantity"] * position["avg_price"] + quantity * price
            position["avg_price"] = total_cost / total_qty
            position["quantity"] = total_qty
        else:
            # Vytvoření nové pozice
            portfolio["positions"][symbol] = {
                "quantity": quantity,
                "avg_price": price
            }
        print(f"✅ Nákup: {quantity} akcií {symbol} za ${price:.2f} (celkem ${cost:.2f})")
        return True
    
    elif side == "SELL":
        if symbol not in portfolio["positions"]:
            print(f"⚠️ Nelze prodat {symbol}: Pozice neexistuje")
            return False
        
        position = portfolio["positions"][symbol]
        if position["quantity"] < quantity:
            print(f"⚠️ Nelze prodat {quantity} akcií {symbol}: Máte pouze {position['quantity']} akcií")
            return False
        
        proceeds = quantity * price
        portfolio["cash"] += proceeds
        position["quantity"] -= quantity
        if position["quantity"] == 0:
            del portfolio["positions"][symbol]
        print(f"✅ Prodej: {quantity} akcií {symbol} za ${price:.2f} (celkem ${proceeds:.2f})")
        return True

def update_portfolio(market_data):
    """Aktualizuje hodnotu portfolia na základě aktuálních tržních dat."""
    equity = portfolio["cash"]
    for symbol, position in list(portfolio["positions"].items()):
        if symbol in market_data:
            price = market_data[symbol]["price"]
            market_value = position["quantity"] * price
            equity += market_value
            
            # Výpočet zisku/ztráty
            cost_basis = position["quantity"] * position["avg_price"]
            unrealized_pl = market_value - cost_basis
            unrealized_plpc = (price / position["avg_price"] - 1.0) * 100
            
            print(f"📊 {symbol}: {position['quantity']} akcií @ ${position['avg_price']:.2f} | Aktuální cena: ${price:.2f} | P/L: ${unrealized_pl:.2f} ({unrealized_plpc:.2f}%)")
    
    portfolio["equity"] = equity
    return equity

def generate_trading_signal():
    """Generuje obchodní signál na základě simulované analýzy."""
    if random.random() < 0.3:  # 30% šance na obchodní signál
        symbol = random.choice(symbols)
        side = random.choice(["BUY", "SELL"])
        quantity = random.randint(1, 10)
        return {
            "symbol": symbol,
            "side": side,
            "quantity": quantity
        }
    return None

def run_simulation():
    """Spouští simulaci obchodování."""
    print("\n📈 Spouštím simulaci obchodování...")
    print(f"💰 Počáteční kapitál: ${portfolio['cash']:.2f}")
    print(f"🏦 Symboly: {', '.join(symbols)}")
    
    try:
        cycle = 0
        while True:
            cycle += 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n{'=' * 20} CYKLUS {cycle} ({now}) {'=' * 20}")
            
            # Simulace tržních dat
            market_data = simulate_market()
            for symbol in symbols:
                data = market_data[symbol]
                change_pct = data["change"] * 100
                change_dir = "▲" if data["change"] > 0 else "▼"
                print(f"🔍 {symbol}: ${data['price']:.2f} {change_dir} {abs(change_pct):.2f}% | Objem: {data['volume']:,}")
            
            # Aktualizace portfolia
            equity = update_portfolio(market_data)
            print(f"\n💼 Portfolio: Hotovost ${portfolio['cash']:.2f} | Celková hodnota ${equity:.2f} | Pozice: {len(portfolio['positions'])}")
            
            # Generování obchodního signálu
            signal = generate_trading_signal()
            if signal:
                print(f"\n🔔 Obchodní signál: {signal['side']} {signal['quantity']} {signal['symbol']}")
                price = market_data[signal['symbol']]['price']
                simulate_trade(signal['symbol'], signal['side'], signal['quantity'], price)
            
            # Čekání na další cyklus
            print(f"\n⏱️ Čekám 5 sekund na další cyklus...")
            time.sleep(5)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Simulace ukončena uživatelem")
        print(f"💰 Konečný kapitál: ${portfolio['equity']:.2f}")
        print(f"📊 Zisk/Ztráta: ${portfolio['equity'] - 100000.0:.2f} ({(portfolio['equity'] / 100000.0 - 1.0) * 100:.2f}%)")
        sys.exit(0)

if __name__ == "__main__":
    run_simulation()
