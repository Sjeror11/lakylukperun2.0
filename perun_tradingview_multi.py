#!/usr/bin/env python3
"""
Perun Trading System - Multi-Crypto verze s TradingView API
Specializovaná verze pro obchodování s více kryptoměnami 24/7 využívající technické indikátory z TradingView.
Podporuje obchodování s více kryptoměnami současně.
"""

import os
import sys
import time
import json
import random
import requests
import traceback
from tradingview_ta import TA_Handler, Interval
from datetime import datetime, timedelta

# API klíče
ALPACA_API_KEY = "AKR88AOYG2LSYZL1RCVC"
ALPACA_API_SECRET = "jT363CePWmEYd9UizVMd6k20YjdjOhnZgNf4K2SJ"
ALPACA_BASE_URL = "https://api.alpaca.markets/v2"  # Trading API
DATA_BASE_URL = "https://data.alpaca.markets/v1beta3"  # Market Data API

# Nastavení pro TradingView API
TV_EXCHANGE = "BINANCE"
TV_SCREENER = "crypto"
TV_INTERVAL = Interval.INTERVAL_1_HOUR

# Hlavičky pro Alpaca API požadavky
ALPACA_HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_API_SECRET,
    "Content-Type": "application/json"
}

# 🔥 ENHANCED Hlavičky pro Data API
ALPACA_DATA_HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_API_SECRET
}

# 🔥 ENHANCED Kryptoměny pro obchodování - ALTSEASON READY (8 párů)
CRYPTO_SYMBOLS = ["BTCUSD", "ETHUSD", "XRPUSD", "SOLUSD", "ADAUSD", "ARBUSD", "AVAXUSD", "DOTUSD"]

# 🔥 ENHANCED Nastavení rizika - VARIANTA A (Agresivní)
MAX_POSITION_SIZE = 50  # Zvýšeno z $30 na $50 (8.7% portfolia)
MIN_POSITION_SIZE = 25  # Zvýšeno z $10 na $25
MAX_TOTAL_POSITIONS = 8  # Zvýšeno z 6 na 8 pro více párů
MAX_EXPOSURE = 400  # Max $400 v pozicích (70% portfolia)
RISK_LIMIT_PERCENT = 0.02  # Maximální riziko na obchod (2% portfolia)

# Nastavení obchodní strategie
STRATEGY_NAME = "TradingView Strategy"
STRATEGY_DESCRIPTION = "Strategie využívající technické indikátory z TradingView pro generování obchodních signálů."

# Funkce pro práci s Alpaca API
def get_account():
    """Získá informace o účtu."""
    try:
        response = requests.get(f"{ALPACA_BASE_URL}/account", headers=ALPACA_HEADERS)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Chyba při získávání informací o účtu: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Výjimka při získávání informací o účtu: {e}")
        return None

def get_positions():
    """Získá aktuální pozice."""
    try:
        response = requests.get(f"{ALPACA_BASE_URL}/positions", headers=ALPACA_HEADERS)
        if response.status_code == 200:
            positions = response.json()
            # Filtrujeme pouze kryptoměnové pozice
            crypto_positions = [p for p in positions if p.get("symbol") in CRYPTO_SYMBOLS]
            return crypto_positions
        else:
            print(f"❌ Chyba při získávání pozic: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Výjimka při získávání pozic: {e}")
        return []


def get_orders():
    """Získá aktuální objednávky."""
    try:
        response = requests.get(f"{ALPACA_BASE_URL}/orders", headers=ALPACA_HEADERS)
        if response.status_code == 200:
            orders = response.json()
            # Filtrujeme pouze kryptoměnové objednávky
            crypto_orders = [o for o in orders if o.get("symbol") in CRYPTO_SYMBOLS]
            return crypto_orders
        else:
            print(f"❌ Chyba při získávání objednávek: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Výjimka při získávání objednávek: {e}")
        return []

def place_crypto_order(symbol, qty, side, order_type="market", time_in_force="gtc"):
    """Zadá objednávku na kryptoměnu."""
    try:
        data = {
            "symbol": symbol,
            "qty": str(qty),  # Alpaca vyžaduje qty jako string pro kryptoměny
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force
        }
        response = requests.post(f"{ALPACA_BASE_URL}/orders", headers=ALPACA_HEADERS, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Chyba při zadávání objednávky: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Výjimka při zadávání objednávky: {e}")
        return None

def cancel_order(order_id):
    """Zruší objednávku."""
    try:
        response = requests.delete(f"{ALPACA_BASE_URL}/orders/{order_id}", headers=ALPACA_HEADERS)
        if response.status_code == 204:
            return True
        else:
            print(f"❌ Chyba při rušení objednávky: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Výjimka při rušení objednávky: {e}")
        return False
def get_tradingview_analysis(symbol):
    """Získá analýzu z TradingView pro daný symbol."""
    try:
        # Převod symbolu na formát pro TradingView (např. BTCUSD -> BINANCE:BTCUSDT)
        if symbol == "BTC/USD":
            tv_symbol = "BTCUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "ETH/USD":
            tv_symbol = "ETHUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "XRP/USD":
            tv_symbol = "XRPUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "SOL/USD":
            tv_symbol = "SOLUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "DOGE/USD":
            tv_symbol = "DOGEUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "ADA/USD":  # 🔥 NOVÉ
            tv_symbol = "ADAUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "ARB/USD":  # 🔥 NOVÉ
            tv_symbol = "ARBUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "XMRUSD":
            tv_symbol = "XMRUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "ETH/USD":
            tv_symbol = "ETHUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "SOL/USD":
            tv_symbol = "SOLUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "AVAX/USD":
            tv_symbol = "AVAXUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "LINKUSD":
            tv_symbol = "LINKUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "MATICUSD":
            tv_symbol = "MATICUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "DOT/USD":
            tv_symbol = "DOTUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "UNIUSD":
            tv_symbol = "UNIUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "AAVEUSD":
            tv_symbol = "AAVEUSDT"
            exchange = TV_EXCHANGE
        elif symbol == "LTCUSD":
            tv_symbol = "LTCUSDT"
            exchange = TV_EXCHANGE
        else:
            tv_symbol = symbol
            exchange = TV_EXCHANGE
            
        print(f"�� Získávám analýzu z TradingView pro {exchange}:{tv_symbol}...")
        
        # Vytvoření handleru pro TradingView
        handler = TA_Handler(
            symbol=tv_symbol,
            exchange=exchange,
            screener=TV_SCREENER,
            interval=TV_INTERVAL,
            timeout=10
        )
        
        # Získání analýzy
        analysis = handler.get_analysis()
        
        # Výpis výsledků
        print(f"  Doporučení: {analysis.summary["RECOMMENDATION"]}")
        print(f"  RSI: {analysis.indicators["RSI"]}")
        print(f"  MACD: {analysis.indicators["MACD.macd"]}")
        print(f"  MACD Signal: {analysis.indicators["MACD.signal"]}")
        print(f"  Bollinger Bands (horní): {analysis.indicators["BB.upper"]}")
        print(f"  Bollinger Bands (dolní): {analysis.indicators["BB.lower"]}")
        
        return analysis
    except Exception as e:
        print(f"❌ Výjimka při získávání analýzy z TradingView: {e}")
        traceback.print_exc()
        return None

def get_rsi(symbol):
    """Získá RSI hodnotu z TradingView API."""
    analysis = get_tradingview_analysis(symbol)
    if analysis:
        return analysis.indicators["RSI"]
    else:
        # Pokud se nepodařilo získat analýzu, vrátíme simulovanou hodnotu
        print("Používám simulovaný RSI indikátor")
        base = random.random()  # 0.0 až 1.0
        if base < 0.1:  # 10% šance na přeprodanost (nízké RSI)
            return random.uniform(20, 30)
        elif base > 0.9:  # 10% šance na překoupenost (vysoké RSI)
            return random.uniform(70, 80)
        else:  # 80% šance na neutrální hodnotu
            return random.uniform(40, 60)
def get_price(symbol):
    """🔥 ENHANCED - Získá reálnou cenu z Alpaca API."""
    # Získá reálnou cenu z Alpaca API
    price = get_price_from_api(symbol)
    
    if price is not None:
        print(f"💰 Reálná cena {symbol}: ${price:,.2f}")
        return price
    
    # Fallback - pouze pro emergenci s aktualizovanými cenami
    print(f"⚠️ Nelze získat reálnou cenu pro {symbol}, používám fallback")
    fallback_prices = {
        "BTCUSD": 105842.0,   # Aktuálná BTC cena
        "ETHUSD": 2532.0,     # Aktuálná ETH cena
        "XRPUSD": 2.18,       # Aktuálná XRP cena
        "SOLUSD": 150.47,     # Aktuálná SOL cena
        "ADAUSD": 0.8084,     # Aktuálná ADA cena (z CoinGecko)
        "ARBUSD": 1.003       # Aktuálná ARB cena (z CoinGecko)
    }
    return fallback_prices.get(symbol, 1.0)

def get_price_from_api(symbol):
    """🔥 OPRAVENO - Získá aktuální cenu pro daný symbol z Alpaca API."""
    try:
        # Převod z BTCUSD na BTC/USD formát
        if symbol == "BTCUSD":
            api_symbol = "BTC/USD"
        elif symbol == "ETHUSD":
            api_symbol = "ETH/USD"
        elif symbol == "XRPUSD":
            api_symbol = "XRP/USD"
        elif symbol == "SOLUSD":
            api_symbol = "SOL/USD"
        elif symbol == "ADAUSD":
            # ADA není dostupná v Alpaca US
            print(f"💰 ADA fallback cena: $0.8084")
            return 0.8084
        elif symbol == "ARBUSD":
            # ARB není dostupný v Alpaca US  
            print(f"💰 ARB fallback cena: $1.003")
            return 1.003
        else:
            api_symbol = symbol
        
        # Správný Alpaca endpoint
        url = f"https://data.alpaca.markets/v1beta3/crypto/us/snapshots?symbols={api_symbol}"
        
        response = requests.get(url, headers=ALPACA_DATA_HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            if "snapshots" in data and api_symbol in data["snapshots"]:
                price = float(data["snapshots"][api_symbol]["latestTrade"]["p"])
                print(f"💰 Reálná cena {symbol}: ${price:,.2f}")
                return price
            else:
                print(f"⚠️ Symbol {api_symbol} nenalezen v odpovědi")
                return None
        else:
            print(f"❌ Chyba při získávání ceny: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Výjimka při získávání ceny: {e}")
        return None
        return analysis.indicators["RSI"]
    else:
        # Pokud se nepodařilo získat analýzu, vrátíme simulovanou hodnotu
        print("Používám simulovaný RSI indikátor")
        base = random.random()  # 0.0 až 1.0
        if base < 0.1:  # 10% šance na přeprodanost (nízké RSI)
            return random.uniform(20, 30)
        elif base > 0.9:  # 10% šance na překoupenost (vysoké RSI)
            return random.uniform(70, 80)
        else:  # 80% šance na neutrální hodnotu
            return random.uniform(40, 60)
    """Získá aktuální cenu pro daný symbol z Alpaca API."""
    try:
        # Použijeme Alpaca API místo TAAPI.IO pro získání ceny
        response = requests.get(f"{ALPACA_BASE_URL}/assets/{symbol}", headers=ALPACA_HEADERS)
        if response.status_code == 200:
            data = response.json()
            return float(data.get("price", 0))
        else:
            print(f"❌ Chyba při získávání ceny z Alpaca: {response.status_code}")
            print(f"Odpověď: {response.text}")
            
            # Záložní metoda - použijeme cenu z pozice, pokud existuje
            positions = get_positions()
            for position in positions:
                if position.get("symbol") == symbol:
                    return float(position.get("current_price", 0))
            
            return None
    except Exception as e:
        print(f"❌ Výjimka při získávání ceny: {e}")
        return None

# Funkce pro analýzu a generování obchodních signálů
# Funkce pro analýzu a generování obchodních signálů
def analyze_crypto(symbol):
    """Analyzuje kryptoměnu a generuje obchodní signál na základě TradingView indikátorů."""
    print(f"🔍 Analyzuji {symbol}...")

    # Získání ceny z Alpaca API
    current_price = get_price(symbol)

    # Získání analýzy z TradingView
    analysis = get_tradingview_analysis(symbol)
    
    # Kontrola, zda se podařilo získat analýzu
    if not analysis or not current_price:
        print(f"❌ Nepodařilo se získat všechny indikátory pro {symbol}")
        return None

    # Inicializace signálu a důvěry
    signal = None
    confidence = 0.5
    reasons = []

    # Analýza doporučení
    recommendation = analysis.summary["RECOMMENDATION"]
    if "BUY" in recommendation or "STRONG_BUY" in recommendation:
        signal = "buy"
        confidence += 0.3
        reasons.append(f"TradingView doporučuje {recommendation}")
    elif "SELL" in recommendation or "STRONG_SELL" in recommendation:
        signal = "sell"
        confidence += 0.3
        reasons.append(f"TradingView doporučuje {recommendation}")

    # Analýza RSI
    rsi = analysis.indicators["RSI"]
    if rsi < 30:  # Překoupeno - signál k nákupu
        if signal != "buy":
            confidence += 0.1
        signal = "buy"
        reasons.append(f"RSI je nízké ({rsi:.2f} < 30) - překoupeno, signál k nákupu")
    elif rsi > 70:  # Přeprodáno - signál k prodeji
        if signal != "sell":
            confidence += 0.1
        signal = "sell"
        reasons.append(f"RSI je vysoké ({rsi:.2f} > 70) - přeprodáno, signál k prodeji")

    # Analýza MACD
    macd = analysis.indicators["MACD.macd"]
    macd_signal = analysis.indicators["MACD.signal"]
    if macd > macd_signal:  # MACD nad signální linií - signál k nákupu
        if signal != "buy":
            confidence += 0.1
        signal = "buy"
        reasons.append(f"MACD ({macd:.2f}) je nad signální linií ({macd_signal:.2f}) - signál k nákupu")
    elif macd < macd_signal:  # MACD pod signální linií - signál k prodeji
        if signal != "sell":
            confidence += 0.1
        signal = "sell"
        reasons.append(f"MACD ({macd:.2f}) je pod signální linií ({macd_signal:.2f}) - signál k prodeji")

    # Analýza Bollinger Bands
    bb_upper = analysis.indicators["BB.upper"]
    bb_lower = analysis.indicators["BB.lower"]
    if current_price <= bb_lower:  # Cena pod dolní hranicí - signál k nákupu
        if signal != "buy":
            confidence += 0.1
        signal = "buy"
        reasons.append(f"Cena ({current_price:.2f}) je pod dolní hranicí Bollinger Bands ({bb_lower:.2f}) - signál k nákupu")
    elif current_price >= bb_upper:  # Cena nad horní hranicí - signál k prodeji
        if signal != "sell":
            confidence += 0.1
        signal = "sell"
        reasons.append(f"Cena ({current_price:.2f}) je nad horní hranicí Bollinger Bands ({bb_upper:.2f}) - signál k prodeji")

    # Pokud nemáme signál, vrátíme None
    if signal is None:
        print(f"  {symbol}: Žádný obchodní signál")
        return None

    # 🧠 SMART SELL: Pro SELL používat skutečnou pozici
    if signal == "sell":
        # Pro SELL - najdi existující pozici
        positions = get_positions()
        existing_qty = 0
        
        if positions:
            for pos in positions:
                if pos.get("symbol") == symbol:
                    existing_qty = float(pos.get("qty", 0))
                    break
        
        if existing_qty <= 0:
            print(f"  {symbol}: Žádná pozice k prodeji")
            return None
            
        # Prodej celé existující pozice
        qty = existing_qty
        print(f"  🎯 SELL: Prodávám celou pozici {qty:.8f} {symbol}")
        
    else:
        # Pro BUY - původní výpočet
        account = get_account()
        if not account:
            return None

        portfolio_value = float(account.get("portfolio_value", 0))
        risk_amount = portfolio_value * RISK_LIMIT_PERCENT

        # Omezení velikosti pozice
        max_qty_by_risk = risk_amount / current_price
        max_qty_by_limit = MAX_POSITION_SIZE / current_price
        qty = min(max_qty_by_risk, max_qty_by_limit)

        # Zajištění minimální velikosti pozice
        min_qty = MIN_POSITION_SIZE / current_price
        qty = max(qty, min_qty)
        # Zaokrouhlení na 8 desetinných míst (běžné pro kryptoměny)
        qty = round(qty, 8)

        # Minimální množství pro obchodování
        if qty < 0.0001:
            qty = 0.0001

    return {
        "symbol": symbol,
        "side": signal,
        "qty": qty,
        "price": current_price,
        "confidence": confidence,
        "reasons": reasons,
        "indicators": {
            "recommendation": recommendation,
            "rsi": rsi,
            "macd": macd,
            "macd_signal": macd_signal,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower
        }
    }

def format_money(amount):
    """Formátuje peněžní částku."""
    return f"${amount:.2f}"
def format_crypto(amount):
    """Formátuje množství kryptoměny."""
    if amount < 0.001:
        return f"{amount:.8f}"
    elif amount < 1:
        return f"{amount:.6f}"
    else:
        return f"{amount:.4f}"

def log_to_file(message, log_file="trading_log.txt"):
    """Zapíše zprávu do logovacího souboru."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def run_crypto_trading_system():
    """Spouští obchodní systém pro kryptoměny."""
    print("=" * 60)
    print("🔥 PERUN ENHANCED - ALTSEASON READY TRADING SYSTEM")
    print("=" * 60)
    print("Spouštím VYLEPŠENÝ obchodní systém s reálnými cenami a altseason páry.")
    print(f"🚀 Obchodované symboly: {', '.join(CRYPTO_SYMBOLS)}")
    print(f"💰 Position size: ${MAX_POSITION_SIZE} | Max pozice: {MAX_TOTAL_POSITIONS}")
    print(f"🎯 Confidence threshold: 0.65 | Interval: 10 minut")
    print(f"⚡ Strategie: {STRATEGY_NAME} - Enhanced")
    print("=" * 50)
    
    # Vytvoření logovacího souboru
    log_file = "trading_log.txt"
    log_to_file("=== SPUŠTĚNÍ OBCHODNÍHO SYSTÉMU ===", log_file)
    
    # Získání informací o účtu
    account = get_account()
    if not account:
        print("❌ Nelze získat informace o účtu. Ukončuji.")
        return
    
    print(f"\n📊 Informace o účtu:")
    print(f"ID účtu: {account.get('id')}")
    print(f"Status účtu: {account.get('status')}")
    print(f"Hotovost: {format_money(float(account.get('cash', 0)))}")
    print(f"Hodnota portfolia: {format_money(float(account.get('portfolio_value', 0)))}")
    
    log_to_file(f"Počáteční hodnota portfolia: {format_money(float(account.get('portfolio_value', 0)))}", log_file)
    
    # Hlavní smyčka
    try:
        cycle = 0
        while True:
            cycle += 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n{'=' * 20} CYKLUS {cycle} ({now}) {'=' * 20}")
            log_to_file(f"CYKLUS {cycle} ({now})", log_file)
            
            # Získání informací o účtu pro portfolio přehled
            account = get_account()
            if account:
                cash = float(account.get("cash", 0))
                portfolio_value = float(account.get("portfolio_value", 0))
                print(f"\n💰 Portfolio přehled:")
                print(f"  Hotovost: {format_money(cash)}")
                print(f"  Hodnota portfolia: {format_money(portfolio_value)}")
            
            # Získání aktuálních pozic
            positions = get_positions()
            print(f"\n📈 Aktuální krypto pozice ({len(positions)}):")
            for position in positions:
                symbol = position.get("symbol")
                qty = float(position.get("qty", 0))
                avg_entry_price = float(position.get("avg_entry_price", 0))
                current_price = float(position.get("current_price", 0))
                market_value = float(position.get("market_value", 0))
                unrealized_pl = float(position.get("unrealized_pl", 0))
                unrealized_plpc = float(position.get("unrealized_plpc", 0)) * 100
                
                position_info = f"{symbol}: {format_crypto(qty)} @ {format_money(avg_entry_price)} | Aktuální cena: {format_money(current_price)} | P/L: {format_money(unrealized_pl)} ({unrealized_plpc:.2f}%)"
                print(f"  {position_info}")
                log_to_file(f"Pozice: {position_info}", log_file)
            
            # Získání aktuálních objednávek
            orders = get_orders()
            print(f"\n📋 Aktuální krypto objednávky ({len(orders)}):")
            for order in orders:
                order_id = order.get("id")
                symbol = order.get("symbol")
                side = order.get("side")
                qty = float(order.get("qty", 0))
                order_type = order.get("type")
                status = order.get("status")
                
                order_info = f"{symbol}: {side.upper()} {format_crypto(qty)} ({order_type}) | Status: {status}"
                print(f"  {order_info}")
                log_to_file(f"Objednávka: {order_info}", log_file)
            
            # Analýza a generování obchodních signálů
            for symbol in CRYPTO_SYMBOLS:
                signal = analyze_crypto(symbol)
                if signal:
                    side = signal.get("side")
                    qty = signal.get("qty")
                    price = signal.get("price")
                    confidence = signal.get("confidence")
                    reasons = signal.get("reasons", [])
                    indicators = signal.get("indicators", {})
                    
                    print(f"\n🔔 Obchodní signál pro {symbol}:")
                    print(f"  Akce: {side.upper()}")
                    print(f"  Množství: {format_crypto(qty)}")
                    print(f"  Cena: {format_money(price)}")
                    print(f"  Důvěra: {confidence:.2f}")
                    print(f"  Důvody:")
                    for reason in reasons:
                        print(f"    - {reason}")
                    
                    print(f"  Indikátory:")
                    print(f"    - Doporučení: {indicators['recommendation']}")
                    print(f"    - RSI: {indicators['rsi']:.2f}")
                    print(f"    - MACD: {indicators['macd']:.2f}")
                    print(f"    - MACD Signal: {indicators['macd_signal']:.2f}")
                    print(f"    - BB Upper: {indicators['bb_upper']:.2f}")
                    print(f"    - BB Lower: {indicators['bb_lower']:.2f}")
                    
                    signal_info = f"{symbol}: {side.upper()} {format_crypto(qty)} @ {format_money(price)} | Důvěra: {confidence:.2f}"
                    log_to_file(f"Signál: {signal_info}", log_file)
                    for reason in reasons:
                        log_to_file(f"  - {reason}", log_file)
                    
                    # Provedení obchodu na základě signálu
                    if confidence > 0.65:  # 🔥 ENHANCED: Sníženo z 0.7 na 0.65 pro více signálů
                        # 🔥 PANIC/PROFIT TAKING: Pouze při extrémních situacích
                        if side == "sell":
                            # Kontrola, zda máme pozici k prodeji
                            existing_position = next((p for p in positions if p.get("symbol") == symbol), None)
                            
                            if not existing_position:
                                no_position_message = f"SELL blokován - nemáme pozici k prodeji pro {symbol}"
                                print(f"  🛡️ {no_position_message}")
                                log_to_file(f"Bez pozice: {no_position_message}", log_file)
                                continue
                            
                            # Získáme údaje o pozici
                            entry_price = float(existing_position.get("avg_entry_price", 0))
                            current_price = price
                            
                            if entry_price > 0:
                                profit_pct = (current_price - entry_price) / entry_price * 100
                                
                                # Získáme aktuální analýzu pro dodatečnou kontrolu
                                analysis = get_tradingview_analysis(symbol)
                                rsi = 50  # default
                                if analysis:
                                    rsi = analysis.indicators["RSI"]
                                
                                # 🔥 ENHANCED PANIC/PROFIT TAKING podmínky (Varianta B):
                                # 1. Profit taking: Zisk > 2% A RSI > 75 (vyvážené)
                                # 2. Quick profit: Zisk > 8% (bez dalších podmínek)
                                # 3. Stop loss: Ztráta < -4% (ochrana kapitálu)
                                # 4. Time stop: Pozice starší 24h s jakýmkoli ziskem
                                
                                # Kontrola stáří pozice
                                try:
                                    # Pozice API vrací created_at v ISO formátu
                                    position_created = datetime.fromisoformat(position.get('created_at', '').replace('Z', '+00:00'))
                                    position_age_hours = (datetime.now().astimezone() - position_created).total_seconds() / 3600
                                except:
                                    position_age_hours = 0  # fallback
                                
                                profit_taking = (profit_pct > 2 and rsi > 75)
                                quick_profit = (profit_pct > 8)
                                stop_loss = (profit_pct < -4)
                                time_stop = (position_age_hours > 24 and profit_pct > 0)
                                
                                if not (profit_taking or quick_profit or stop_loss or time_stop):
                                    panic_block_message = f"SELL blokován - nesplněny podmínky (P/L: {profit_pct:+.1f}%, RSI: {rsi:.1f}, Stáří: {position_age_hours:.1f}h). Potřeba: Zisk>2% a RSI>75 NEBO zisk>8% NEBO ztráta<-4% NEBO 24h+ s ziskem"
                                    print(f"  🛡️ {panic_block_message}")
                                    log_to_file(f"Panic blok: {panic_block_message}", log_file)
                                    continue
                                else:
                                    if quick_profit:
                                        reason = "Quick profit (8%+)"
                                    elif profit_taking:
                                        reason = "Profit taking (2%+ při RSI>75)"
                                    elif time_stop:
                                        reason = f"Time stop (24h+ pozice s ziskem, stáří: {position_age_hours:.1f}h)"
                                    else:
                                        reason = "Stop loss (-4%)"
                                    panic_sell_message = f"SELL povolen - {reason} (P/L: {profit_pct:+.1f}%, RSI: {rsi:.1f}, Entry: ${entry_price:.2f}, Current: ${current_price:.2f})"
                                    print(f"  💰 {panic_sell_message}")
                                    log_to_file(f"Panic sell: {panic_sell_message}", log_file)
                            else:
                                entry_error_message = f"SELL blokován - nelze určit vstupní cenu pozice"
                                print(f"  ⚠️ {entry_error_message}")
                                log_to_file(f"Entry chyba: {entry_error_message}", log_file)
                                continue
                            
                        # 🔥 ENHANCED kontroly pro BUY signály
                        if side == "buy":
                            # Kontrola počtu pozic
                            if len(positions) >= MAX_TOTAL_POSITIONS:
                                max_positions_message = f"BUY blokován - dosažen maximální počet pozic ({len(positions)}/{MAX_TOTAL_POSITIONS})"
                                print(f"  🛡️ {max_positions_message}")
                                log_to_file(f"Max pozice: {max_positions_message}", log_file)
                                continue
                            
                            # Kontrola celkového exposure (70% portfolia)
                            total_market_value = sum(float(p.get("market_value", 0)) for p in positions)
                            if total_market_value + (qty * price) > MAX_EXPOSURE:
                                exposure_message = f"BUY blokován - překročen max exposure (${total_market_value:.2f} + ${qty * price:.2f} > ${MAX_EXPOSURE})"
                                print(f"  🛡️ {exposure_message}")
                                log_to_file(f"Max exposure: {exposure_message}", log_file)
                                continue
                        
                        # Kontrola, zda již nemáme otevřenou pozici
                        existing_position = next((p for p in positions if p.get("symbol") == symbol), None)
                        
                        # Pokud máme pozici a signál je stejný směr, přeskočíme
                        if existing_position:
                            position_side = "sell" if float(existing_position.get("qty", 0)) < 0 else "buy"
                            if position_side == side:
                                skip_message = f"Již máme otevřenou pozici {position_side.upper()} pro {symbol}, přeskakuji"
                                print(f"  ⚠️ {skip_message}")
                                log_to_file(f"Přeskočeno: {skip_message}", log_file)
                                continue
                        
                        trade_message = f"Provádím obchod: {side.upper()} {format_crypto(qty)} {symbol} @ {format_money(price)}"
                        print(f"  ✅ {trade_message}")
                        
                        log_to_file(f"Obchod: {trade_message}", log_file)
                        

                        result = place_crypto_order(symbol, qty, side)
                        if result:
                            success_message = f"Obchod zadán: ID objednávky {result.get('id')}"
                            print(f"  ✅ {success_message}")
                            log_to_file(f"Úspěch: {success_message}", log_file)
                        else:
                            error_message = f"Obchod se nezdařil"
                            print(f"  ❌ {error_message}")
                            log_to_file(f"Chyba: {error_message}", log_file)
                    else:
                        low_confidence_message = f"Důvěra signálu je příliš nízká ({confidence:.2f}), neprovádím obchod"
                        print(f"  ⚠️ {low_confidence_message}")
                        log_to_file(f"Nízká důvěra: {low_confidence_message}", log_file)
                else:
                    no_signal_message = f"{symbol}: Žádný obchodní signál"
                    print(f"  {no_signal_message}")
                    log_to_file(no_signal_message, log_file)
            
            # Čekání na další cyklus
            wait_time = 600  # 🔥 ENHANCED: 10 minut mezi cykly (zrychleno pro altseason)
            print(f"\n⏱️ Čekám {wait_time} sekund na další cyklus...")
            log_to_file(f"Čekání {wait_time} sekund na další cyklus", log_file)
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        print("\n\n�� Obchodní systém ukončen uživatelem")
        log_to_file("=== UKONČENÍ OBCHODNÍHO SYSTÉMU UŽIVATELEM ===", log_file)
        
        # Získání aktuálních informací o účtu
        final_account = get_account()
        if final_account:
            final_value = float(final_account.get("portfolio_value", 0))
            initial_value = float(account.get("portfolio_value", 0))
            profit = final_value - initial_value
            profit_percent = (profit / initial_value) * 100 if initial_value > 0 else 0
            
            print(f"💰 Konečná hodnota portfolia: {format_money(final_value)}")
            print(f"📊 Zisk/Ztráta: {format_money(profit)} ({profit_percent:.2f}%)")
            
            log_to_file(f"Konečná hodnota portfolia: {format_money(final_value)}", log_file)
            log_to_file(f"Zisk/Ztráta: {format_money(profit)} ({profit_percent:.2f}%)", log_file)
        
        sys.exit(0)

if __name__ == "__main__":
    run_crypto_trading_system()


def get_crypto_prices_bulk(symbols):
    """Získá ceny více kryptoměn najednou přes správný Alpaca endpoint."""
    if not symbols:
        return {}
    
    try:
        # Spojení symbolů do jednoho řetězce
        symbols_str = ",".join(symbols)
        url = f"https://data.alpaca.markets/v1beta3/crypto/us/snapshots?symbols={symbols_str}"
        
        response = requests.get(url, headers=ALPACA_HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            snapshots = data.get('snapshots', {})
            
            prices = {}
            for symbol, snapshot in snapshots.items():
                # Preferujeme latest trade price
                latest_trade = snapshot.get('latestTrade', {})
                trade_price = latest_trade.get('p')
                
                if trade_price:
                    prices[symbol] = float(trade_price)
                else:
                    # Fallback na ask cenu z quote
                    latest_quote = snapshot.get('latestQuote', {})
                    ask_price = latest_quote.get('ap')
                    if ask_price:
                        prices[symbol] = float(ask_price)
            
            return prices
        else:
            print(f"❌ Chyba při získávání cen: {response.status_code} - {response.text}")
            return {}
            
    except Exception as e:
        print(f"❌ Výjimka při získávání cen: {e}")
        return {}

def get_crypto_price(symbol):
    """Získá aktuální cenu kryptoměny přes správný Alpaca endpoint."""
    try:
        url = f"https://data.alpaca.markets/v1beta3/crypto/us/snapshots?symbols={symbol}"
        response = requests.get(url, headers=ALPACA_HEADERS)
        if response.status_code == 200:
            data = response.json()
            snapshots = data.get('snapshots', {})
            snapshot = snapshots.get(symbol, {})
            
            # Preferujeme latest trade price
            latest_trade = snapshot.get('latestTrade', {})
            trade_price = latest_trade.get('p')
            
            if trade_price:
                return float(trade_price)
            
            # Fallback na ask cenu
            latest_quote = snapshot.get('latestQuote', {})
            ask_price = latest_quote.get('ap')
            if ask_price:
                return float(ask_price)
            
            return None
        else:
            print(f"❌ Chyba při získávání ceny {symbol}: {response.status_code}")
            print(f"Odpověď: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Výjimka při získávání ceny {symbol}: {e}")
        return None

def get_current_crypto_price(symbol):
    """Alias pro get_crypto_price pro zpětnou kompatibilitu."""
    return get_crypto_price(symbol)
