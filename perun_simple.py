#!/usr/bin/env python3
"""
Perun Trading System - Jednoduchá verze s TradingView API
Specializovaná verze pro obchodování s kryptoměnami 24/7 využívající technické indikátory z TradingView.
"""

import sys
import time
import traceback
from datetime import datetime
from tradingview_ta import TA_Handler, Interval

# Vypnout buffering stdout
try:
    sys.stdout.reconfigure(line_buffering=True)
except AttributeError:
    # Pro starší verze Pythonu
    import os
    os.environ['PYTHONUNBUFFERED'] = '1'

# API klíče
ALPACA_API_KEY = "AKJYB42QYBVD1EKBDQJ8"
ALPACA_API_SECRET = "SczRiShhbzjejIYP8KKcg50XIhJMIyR895vi1hGI"
ALPACA_BASE_URL = "https://api.alpaca.markets/v2"

# Hlavičky pro Alpaca API požadavky
ALPACA_HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_API_SECRET,
    "Content-Type": "application/json"
}

# Kryptoměny pro obchodování
CRYPTO_SYMBOLS = ["BTCUSD"]  # Obchodujeme BTC/USD

# Nastavení rizika
MAX_POSITION_SIZE = 25  # Maximální velikost pozice v USD
MAX_TOTAL_POSITIONS = 2  # Maximální počet současných pozic
RISK_LIMIT_PERCENT = 0.02  # Maximální riziko na obchod (2% portfolia)

# Nastavení obchodní strategie
STRATEGY_NAME = "TradingView Strategy"
STRATEGY_DESCRIPTION = "Strategie využívající technické indikátory z TradingView pro generování obchodních signálů."

def get_tradingview_analysis(symbol):
    """Získá analýzu z TradingView pro daný symbol."""
    try:
        # Převod symbolu na formát pro TradingView (např. BTCUSD -> BINANCE:BTCUSDT)
        if symbol == "BTCUSD":
            tv_symbol = "BTCUSDT"
            exchange = "BINANCE"
        elif symbol == "ETHUSD":
            tv_symbol = "ETHUSDT"
            exchange = "BINANCE"
        else:
            tv_symbol = symbol
            exchange = "BINANCE"

        print(f"📊 Získávám analýzu z TradingView pro {exchange}:{tv_symbol}...")

        # Vytvoření handleru pro TradingView
        handler = TA_Handler(
            symbol=tv_symbol,
            exchange=exchange,
            screener="crypto",
            interval=Interval.INTERVAL_1_HOUR,
            timeout=10
        )

        # Získání analýzy
        analysis = handler.get_analysis()

        # Výpis výsledků
        print(f"  Doporučení: {analysis.summary['RECOMMENDATION']}")
        print(f"  RSI: {analysis.indicators['RSI']}")
        print(f"  MACD: {analysis.indicators['MACD.macd']}")
        print(f"  MACD Signal: {analysis.indicators['MACD.signal']}")
        print(f"  Bollinger Bands (horní): {analysis.indicators['BB.upper']}")
        print(f"  Bollinger Bands (dolní): {analysis.indicators['BB.lower']}")

        return analysis
    except Exception as e:
        print(f"❌ Výjimka při získávání analýzy z TradingView: {e}")
        traceback.print_exc()
        return None

def main():
    """Hlavní funkce programu."""
    print("=" * 50)
    print("PERUN TRADING SYSTEM - JEDNODUCHÁ VERZE S TRADINGVIEW")
    print("=" * 50)
    print("Spouštím obchodní systém pro kryptoměny 24/7 s využitím TradingView.")
    print(f"Obchodované symboly: {', '.join(CRYPTO_SYMBOLS)}")
    print(f"Strategie: {STRATEGY_NAME}")
    print(f"Popis: {STRATEGY_DESCRIPTION}")
    print("=" * 50)

    try:
        # Hlavní smyčka
        cycle = 0
        while True:
            cycle += 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n{'=' * 20} CYKLUS {cycle} ({now}) {'=' * 20}")

            # Analýza a generování obchodních signálů
            for symbol in CRYPTO_SYMBOLS:
                print(f"🔍 Analyzuji {symbol}...")

                # Získání analýzy z TradingView
                analysis = get_tradingview_analysis(symbol)

                if analysis:
                    # Inicializace signálu a důvěry
                    signal = None
                    confidence = 0.5
                    reasons = []

                    # Analýza doporučení
                    recommendation = analysis.summary['RECOMMENDATION']
                    if "BUY" in recommendation or "STRONG_BUY" in recommendation:
                        signal = "buy"
                        confidence += 0.3
                        reasons.append(f"TradingView doporučuje {recommendation}")
                    elif "SELL" in recommendation or "STRONG_SELL" in recommendation:
                        signal = "sell"
                        confidence += 0.3
                        reasons.append(f"TradingView doporučuje {recommendation}")

                    # Analýza RSI
                    rsi = analysis.indicators['RSI']
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
                    macd = analysis.indicators['MACD.macd']
                    macd_signal = analysis.indicators['MACD.signal']
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

                    # Výpis výsledků
                    if signal:
                        print(f"\n🔔 Obchodní signál pro {symbol}:")
                        print(f"  Akce: {signal.upper()}")
                        print(f"  Důvěra: {confidence:.2f}")
                        print(f"  Důvody:")
                        for reason in reasons:
                            print(f"    - {reason}")
                    else:
                        print(f"  {symbol}: Žádný obchodní signál")
                else:
                    print(f"  {symbol}: Nepodařilo se získat analýzu")

            # Čekání na další cyklus
            wait_time = 900  # 15 minut mezi cykly
            print(f"\n⏱️ Čekám {wait_time} sekund na další cyklus...")
            time.sleep(wait_time)

    except KeyboardInterrupt:
        print("\n\n🛑 Obchodní systém ukončen uživatelem")
        sys.exit(0)

if __name__ == "__main__":
    main()
