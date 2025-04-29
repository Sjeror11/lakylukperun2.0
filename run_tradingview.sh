#!/bin/bash

# Spuštění Perun Trading System s TradingView API
cd /home/laky/perun
source .venv/bin/activate

echo "Test TradingView API:"
python -c "from tradingview_ta import TA_Handler, Interval; handler = TA_Handler(symbol='BTCUSDT', exchange='BINANCE', screener='crypto', interval=Interval.INTERVAL_1_HOUR); analysis = handler.get_analysis(); print(f'Doporučení: {analysis.summary[\"RECOMMENDATION\"]}'); print(f'RSI: {analysis.indicators[\"RSI\"]}'); print(f'MACD: {analysis.indicators[\"MACD.macd\"]}'); print(f'MACD Signal: {analysis.indicators[\"MACD.signal\"]}'); print(f'Bollinger Bands (horní): {analysis.indicators[\"BB.upper\"]}'); print(f'Bollinger Bands (dolní): {analysis.indicators[\"BB.lower\"]}')"

echo -e "\nSpouštím Perun Trading System s TradingView API..."
python perun_tradingview.py
