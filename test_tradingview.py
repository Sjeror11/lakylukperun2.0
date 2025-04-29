#!/usr/bin/env python3

import traceback
import sys

print("Python verze:", sys.version)
print("Cesta k Python:", sys.executable)
print("Cesta k modulům:", sys.path)

print("Importuji tradingview_ta...")
sys.stdout.flush()

try:
    from tradingview_ta import TA_Handler, Interval
    print("Import úspěšný!")
    sys.stdout.flush()

    print("Test TradingView API:")
    sys.stdout.flush()

    handler = TA_Handler(
        symbol="BTCUSDT",
        exchange="BINANCE",
        screener="crypto",
        interval=Interval.INTERVAL_1_HOUR,
        timeout=10
    )
    print("Handler vytvořen")
    sys.stdout.flush()

    print("Získávám analýzu...")
    sys.stdout.flush()
    analysis = handler.get_analysis()
    print("Analýza získána!")
    sys.stdout.flush()

    print(f"  Doporučení: {analysis.summary['RECOMMENDATION']}")
    print(f"  RSI: {analysis.indicators['RSI']}")
    print(f"  MACD: {analysis.indicators['MACD.macd']}")
    print(f"  MACD Signal: {analysis.indicators['MACD.signal']}")
    print(f"  Bollinger Bands (horní): {analysis.indicators['BB.upper']}")
    print(f"  Bollinger Bands (dolní): {analysis.indicators['BB.lower']}")
    print("Test TradingView API úspěšný!")
    sys.stdout.flush()
except Exception as e:
    print(f"Chyba: {e}")
    traceback.print_exc()
    sys.stdout.flush()
