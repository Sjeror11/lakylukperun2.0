#!/usr/bin/env python3
"""
Finální webový monitor s přímým API přístupem
"""

import http.server
import socketserver
import os
import json
import requests
from datetime import datetime
import glob

# API klíče
ALPACA_API_KEY = "AKR88AOYG2LSYZL1RCVC"
ALPACA_API_SECRET = "jT363CePWmEYd9UizVMd6k20YjdjOhnZgNf4K2SJ"
ALPACA_BASE_URL = "https://api.alpaca.markets/v2"
ALPACA_DATA_URL = "https://data.alpaca.markets/v1beta3"

ALPACA_HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_API_SECRET,
    "Content-Type": "application/json"
}

def get_account_info():
    """Získá info o účtu přes API"""
    try:
        response = requests.get(f"{ALPACA_BASE_URL}/account", headers=ALPACA_HEADERS)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_positions_info():
    """Získá pozice přes API"""
    try:
        response = requests.get(f"{ALPACA_BASE_URL}/positions", headers=ALPACA_HEADERS)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def get_crypto_prices(symbols):
    """Získá aktuální ceny kryptoměn"""
    try:
        # Převod na správný formát pro API (BTC/USD místo BTCUSD)
        converted_symbols = []
        for symbol in symbols:
            if symbol.endswith('USD'):
                base = symbol[:-3]
                converted_symbols.append(f"{base}/USD")
            else:
                converted_symbols.append(symbol)
        
        symbols_str = ','.join(converted_symbols)
        response = requests.get(f"{ALPACA_DATA_URL}/crypto/us/latest/quotes?symbols={symbols_str}", headers=ALPACA_HEADERS)
        if response.status_code == 200:
            data = response.json()
            prices = {}
            for symbol, quote_data in data.get('quotes', {}).items():
                if quote_data:
                    # Převod zpět na původní formát (BTC/USD -> BTCUSD)
                    original_symbol = symbol.replace('/', '')
                    prices[original_symbol] = quote_data['bp']  # bid price
            return prices
    except Exception as e:
        print(f"Error getting prices: {e}")
    return {}

def get_crypto_history(symbol, timeframe="1Day", limit=30):
    """Získá historická data pro kryptoměnu"""
    try:
        # Převod na správný formát pro API (BTCUSD -> BTC/USD)
        if symbol.endswith('USD') and '/' not in symbol:
            base = symbol[:-3]
            api_symbol = f"{base}/USD"
        else:
            api_symbol = symbol
            
        response = requests.get(f"{ALPACA_DATA_URL}/crypto/us/bars?symbols={api_symbol}&timeframe={timeframe}&limit={limit}", headers=ALPACA_HEADERS)
        if response.status_code == 200:
            data = response.json()
            bars = data.get('bars', {}).get(api_symbol, [])
            return bars
    except Exception as e:
        print(f"Error getting history for {symbol}: {e}")
    return []

def get_youtube_analysis():
    """Získá nejnovější YouTube analýzu"""
    try:
        # Najde nejnovější YouTube analýzu
        analysis_files = glob.glob('youtube_analysis_*.json')
        if not analysis_files:
            return None
        
        # Seřadí podle času a vezme nejnovější
        latest_file = max(analysis_files, key=os.path.getmtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    except Exception as e:
        print(f"Error loading YouTube analysis: {e}")
        return None

def get_news_analysis():
    """Získá nejnovější News analýzu"""
    try:
        # Najde nejnovější News analýzu
        analysis_files = glob.glob('news_analysis_*.json')
        if not analysis_files:
            return None
        
        # Seřadí podle času a vezme nejnovější
        latest_file = max(analysis_files, key=os.path.getmtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    except Exception as e:
        print(f"Error loading News analysis: {e}")
        return None

def analyze_trading_performance():
    """Analyzuje úspěšnost tradingu z logů"""
    try:
        wins = 0
        losses = 0
        buys = 0
        sells = 0
        blocked_sells = 0
        
        with open('trading_log.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                # Počítáme BUY signály
                if 'Signál:' in line and 'BUY' in line and 'Přeskočeno:' not in line:
                    buys += 1
                
                # Počítáme provedené SELL transakce
                if 'Úspěch:' in line and 'prodán' in line:
                    if '+$' in line or 'zisk' in line.lower():
                        wins += 1
                    elif '-$' in line or 'ztráta' in line.lower():
                        losses += 1
                    sells += 1
                
                # Počítáme blokované SELL signály
                if 'Panic blok:' in line or 'SELL blokován' in line:
                    blocked_sells += 1
        
        # Pokud nemáme dokončené obchody, použijeme aktuální pozice
        if wins + losses == 0:
            positions = get_positions_info()
            for pos in positions:
                unrealized_pl = float(pos.get('unrealized_pl', 0))
                if unrealized_pl > 0:
                    wins += 1
                elif unrealized_pl < 0:
                    losses += 1
        
        total = wins + losses
        win_ratio = (wins / total * 100) if total > 0 else 0
        
        return {
            'wins': wins, 
            'losses': losses, 
            'win_ratio': win_ratio,
            'buys': buys,
            'sells': sells,
            'blocked_sells': blocked_sells
        }
    except Exception as e:
        print(f"Error analyzing performance: {e}")
        return {'wins': 0, 'losses': 0, 'win_ratio': 0, 'buys': 0, 'sells': 0, 'blocked_sells': 0}

class LogHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Refresh', '30')
            self.end_headers()
            
            html = """
<!DOCTYPE html>
<html>
<head>
    <title>Perun Trading Monitor</title>
    <meta charset="utf-8">
    <style>
        body { font-family: monospace; background: #1e1e1e; color: #fff; margin: 20px; }
        .log { background: #2d2d2d; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .title { color: #4fc3f7; font-size: 18px; margin-bottom: 10px; }
        .content { white-space: pre-wrap; font-size: 14px; }
        .timestamp { color: #81c784; }
        .error { color: #f44336; }
        .success { color: #4caf50; }
        .warning { color: #ff9800; }
        .profit { color: #4caf50; }
        .loss { color: #f44336; }
    </style>
</head>
<body>
    <h1>🔥 Perun Trading Monitor</h1>
    <p>Automatická obnova každých 30 sekund</p>
            """
            
            # Portfolio Status s API daty
            account = get_account_info()
            positions = get_positions_info()
            
            html += '<div class="log"><div class="title">💰 Portfolio Status</div><div class="content">'
            if account:
                cash = float(account.get('cash', 0))
                portfolio_value = float(account.get('portfolio_value', 0))
                html += f'Hotovost: ${cash:.2f}\n'
                html += f'Hodnota portfolia: ${portfolio_value:.2f}\n\n'
                
                html += 'Aktuální pozice:\n'
                if positions:
                    for pos in positions:
                        symbol = pos['symbol']
                        qty = float(pos['qty'])
                        current_price = float(pos['current_price'])
                        avg_entry_price = float(pos['avg_entry_price'])
                        purchase_value = qty * avg_entry_price
                        unrealized_pl = float(pos['unrealized_pl'])
                        unrealized_plpc = float(pos['unrealized_plpc']) * 100
                        
                        pl_class = "profit" if unrealized_pl >= 0 else "loss"
                        sign = "+" if unrealized_pl >= 0 else ""
                        
                        html += f'<span class="{pl_class}">{symbol}: {qty:.6f} @ ${current_price:.2f} (nakoupeno za ${purchase_value:.2f}) | P/L: {sign}${unrealized_pl:.2f} ({sign}{unrealized_plpc:.2f}%)</span>\n'
                else:
                    html += 'Žádné otevřené pozice\n'
            else:
                html += 'Nelze načíst portfolio data - zkontrolujte API připojení\n'
            html += '</div></div>'
            
            # YouTube Sentiment Analysis
            youtube_data = get_youtube_analysis()
            if youtube_data:
                html += '<div class="log"><div class="title">📺 YouTube Sentiment Analysis</div><div class="content">'
                
                # Časové razítko analýzy
                timestamp = youtube_data.get('timestamp', 'N/A')
                if timestamp != 'N/A':
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%d.%m.%Y %H:%M')
                        html += f'<span class="timestamp">Poslední analýza: {time_str}</span>\\n\\n'
                    except:
                        html += f'<span class="timestamp">Poslední analýza: {timestamp}</span>\\n\\n'
                
                # Celkový sentiment
                perun_signals = youtube_data.get('perun_signals', {})
                summary = perun_signals.get('summary', {})
                overall_sentiment = summary.get('overall_sentiment', 0)
                total_channels = summary.get('total_channels', 0)
                
                sentiment_class = "profit" if overall_sentiment > 0.5 else "loss" if overall_sentiment < 0.4 else "warning"
                html += f'<span class="{sentiment_class}">Celkový sentiment: {overall_sentiment:.2f} ({total_channels} kanálů)</span>\\n\\n'
                
                # Top sentiment kryptoměny
                youtube_sentiment = perun_signals.get('youtube_sentiment', {})
                if youtube_sentiment:
                    html += 'Top sentiment kryptoměny:\\n'
                    # Seřadí podle sentimentu
                    sorted_cryptos = sorted(youtube_sentiment.items(), key=lambda x: x[1], reverse=True)[:5]
                    for crypto, sentiment in sorted_cryptos:
                        confidence = perun_signals.get('confidence_scores', {}).get(crypto, 0)
                        sentiment_class = "profit" if sentiment > 0.6 else "loss" if sentiment < 0.4 else "warning"
                        html += f'  <span class="{sentiment_class}">{crypto}: {sentiment:.2f} (conf: {confidence:.2f})</span>\\n'
                
                html += '\\n'
                
                # Kanály
                channels = youtube_data.get('channel_analyses', [])
                if channels:
                    html += 'Analyzované kanály:\\n'
                    for channel in channels[:4]:  # Top 4 kanály
                        name = channel.get('channel_name', 'Unknown')
                        sentiment = channel.get('overall_sentiment', 0)
                        confidence = channel.get('overall_confidence', 0)
                        videos = channel.get('videos_analyzed', 0)
                        
                        sentiment_class = "profit" if sentiment > 0.5 else "loss" if sentiment < 0.4 else "warning"
                        html += f'  <span class="{sentiment_class}">{name}: {sentiment:.2f}</span> ({videos} videí, conf: {confidence:.2f})\\n'
                
                html += '</div></div>'
            else:
                html += '<div class="log"><div class="title">📺 YouTube Sentiment</div><div class="content">'
                html += '<span class="warning">Žádná YouTube analýza nenalezena</span>\\n'
                html += 'Spusť: python3 youtube_analyzer.py</div></div>'
            
            # Crypto News Sentiment Analysis
            news_data = get_news_analysis()
            if news_data:
                html += '<div class="log"><div class="title">📰 Crypto News Sentiment Analysis</div><div class="content">'
                
                # Časové razítko analýzy
                timestamp = news_data.get('timestamp', 'N/A')
                if timestamp != 'N/A':
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%d.%m.%Y %H:%M')
                        html += f'<span class="timestamp">Poslední analýza: {time_str}</span>\\n\\n'
                    except:
                        html += f'<span class="timestamp">Poslední analýza: {timestamp}</span>\\n\\n'
                
                # Celkový sentiment ze souhrnu
                summary = news_data.get('summary', {})
                avg_sentiment = summary.get('average_sentiment', 0)
                total_articles = summary.get('total_articles', 0)
                articles_analyzed = news_data.get('articles_analyzed', 0)
                market_mood = summary.get('market_mood', 'N/A')
                
                sentiment_class = "profit" if avg_sentiment > 0.1 else "loss" if avg_sentiment < -0.1 else "warning"
                html += f'<span class="{sentiment_class}">Celkový sentiment: {avg_sentiment:.3f} ({market_mood})</span>\\n'
                html += f'<span class="info">Analyzováno: {articles_analyzed}/{total_articles} článků</span>\\n\\n'
                
                # Top kryptoměny
                top_cryptos = summary.get('top_cryptocurrencies', [])
                if top_cryptos:
                    html += '<strong>🪙 Top kryptoměny:</strong>\\n'
                    for crypto in top_cryptos[:5]:
                        symbol = crypto['symbol']
                        mentions = crypto['mentions']
                        html += f'  <span class="info">{symbol}: {mentions} zmínek</span>\\n'
                    html += '\\n'
                
                # Trading doporučení
                recommendation = summary.get('recommendation', 'N/A')
                if recommendation != 'N/A':
                    rec_class = "profit" if "nakup" in recommendation.lower() or "bullish" in recommendation.lower() else "warning"
                    html += f'<span class="{rec_class}">💡 Doporučení: {recommendation}</span>\\n\\n'
                
                # Nejnovější články (top 3)
                articles = news_data.get('articles', [])
                if articles:
                    html += '<strong>📰 Nejnovější články:</strong>\\n'
                    for i, article in enumerate(articles[:3], 1):
                        title = article.get('title_cs', article.get('title', 'N/A'))[:60] + '...'
                        source = article.get('source', 'N/A')
                        sentiment = article.get('sentiment', {})
                        sent_score = sentiment.get('sentiment', 0)
                        sent_class = "profit" if sent_score > 0.1 else "loss" if sent_score < -0.1 else "warning"
                        html += f'  {i}. <span class="{sent_class}">{title}</span>\\n'
                        html += f'     {source} | Sentiment: {sent_score:.2f}\\n'
                
                html += '</div></div>'
            else:
                html += '<div class="log"><div class="title">📰 Crypto News Sentiment</div><div class="content">'
                html += '<span class="warning">Žádná News analýza nenalezena</span>\\n'
                html += 'Spusť: python3 news_perun_integration.py</div></div>'
            
            # Trading log (posledních 30 řádků)
            try:
                with open('trading_log.txt', 'r') as f:
                    lines = f.readlines()[-30:]
                html += '<div class="log"><div class="title">📊 Trading Log (posledních 30 řádků)</div><div class="content">'
                for line in lines:
                    css_class = ""
                    if "Chyba" in line or "❌" in line:
                        css_class = "error"
                    elif "Úspěch" in line or "✅" in line:
                        css_class = "success"
                    elif "⚠️" in line:
                        css_class = "warning"
                    elif "[2025-" in line:
                        css_class = "timestamp"
                    
                    html += f'<span class="{css_class}">{line.strip()}</span>\n'
                html += '</div></div>'
            except:
                html += '<div class="log"><div class="title">📊 Trading Log</div><div class="content">Nelze načíst trading log</div></div>'
            
            
            html += """
</body>
</html>
            """
            
            self.wfile.write(html.encode())
        
        else:
            super().do_GET()

if __name__ == "__main__":
    PORT = 8084
    os.chdir('/home/laky/lakylukperun2.0')
    
    try:
        with socketserver.TCPServer(("", PORT), LogHandler) as httpd:
            print(f"🌐 Finální monitor s API běží na portu {PORT}")
            print(f"📡 Přístupné na: http://100.69.193.112:{PORT}")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"❌ Port {PORT} je obsazený, zkouším port 8085")
            PORT = 8085
            with socketserver.TCPServer(("", PORT), LogHandler) as httpd:
                print(f"🌐 Finální monitor s API běží na portu {PORT}")
                print(f"📡 Přístupné na: http://100.69.193.112:{PORT}")
                httpd.serve_forever()
        else:
            raise