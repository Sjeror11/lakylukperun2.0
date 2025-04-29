#!/usr/bin/env python3

import sys
import traceback
from tradingview_ta import TA_Handler, Interval

print("Spouštím jednoduchý test TradingView API...", flush=True)

try:
    # Vytvoření handleru pro TradingView
    handler = TA_Handler(
        symbol="BTCUSDT",
        exchange="BINANCE",
        screener="crypto",
        interval=Interval.INTERVAL_1_HOUR,
        timeout=10
    )
    print("Handler vytvořen", flush=True)

    # Získání analýzy
    analysis = handler.get_analysis()
    print("Analýza získána!", flush=True)

    # Výpis výsledků
    print(f"Doporučení: {analysis.summary['RECOMMENDATION']}", flush=True)
    print(f"RSI: {analysis.indicators['RSI']}", flush=True)
    print(f"MACD: {analysis.indicators['MACD.macd']}", flush=True)
    print(f"MACD Signal: {analysis.indicators['MACD.signal']}", flush=True)
    print(f"Bollinger Bands (horní): {analysis.indicators['BB.upper']}", flush=True)
    print(f"Bollinger Bands (dolní): {analysis.indicators['BB.lower']}", flush=True)

    print("Test TradingView API úspěšný!", flush=True)
except Exception as e:
    print(f"Chyba: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)
