#!/bin/bash
# News-Perun Integration Startup Script
# Spuštění kompletního News monitoring systému s Perun integrací

echo "🔥 News-Perun Integration Startup"
echo "================================="

# Přejít do správného adresáře
cd /home/laky/lakylukperun2.0

# Kontrola virtuálního prostředí
if [ ! -d "venv" ]; then
    echo "❌ Virtuální prostředí neexistuje. Vytvářím..."
    python3 -m venv venv
fi

# Aktivace venv
source venv/bin/activate

# Kontrola a instalace závislostí
echo "📦 Kontroluji závislosti..."
if [ ! -f "requirements_news.txt" ]; then
    echo "📝 Vytvářím requirements_news.txt..."
    cat > requirements_news.txt << EOF
feedparser>=6.0.11
requests>=2.31.0
googletrans==4.0.0rc1
google-generativeai>=0.8.3
httpx==0.13.3
python-dotenv>=0.19.0
EOF
fi

pip install -r requirements_news.txt

echo ""
echo "🚀 Dostupné možnosti spuštění:"
echo "1. News Analyzer + Perun Integration + Web Monitor (DOPORUČENO)"
echo "2. Pouze News Analyzer (standalone)"
echo "3. Pouze Perun Integration"
echo "4. Test News API klíčů"
echo "5. Zastavit všechny News služby"
echo ""

# Čtení vstupu
if [ -t 0 ]; then
    read -p "Vyberte možnost (1-5): " choice
else
    # Pro pipe input (echo "1" | ./start_news_perun.sh)
    read choice
fi

case $choice in
    1)
        echo "🚀 Spouštím kompletní News-Perun systém..."
        
        # Zastavení starých procesů
        if [ -f "news_perun.pid" ]; then
            echo "⏹️ Zastavuji starý News-Perun proces..."
            kill $(cat news_perun.pid) 2>/dev/null || true
            rm -f news_perun.pid
        fi
        
        if [ -f "web_final.pid" ]; then
            echo "⏹️ Zastavuji starý Web Monitor..."
            kill $(cat web_final.pid) 2>/dev/null || true
            rm -f web_final.pid
        fi
        
        # Spuštění News-Perun integrace
        echo "📰 Spouštím News-Perun integraci..."
        nohup python3 news_perun_integration.py > news_perun.log 2>&1 & echo $! > news_perun.pid
        
        # Krátké čekání
        sleep 3
        
        # Spuštění Web Monitoru
        echo "🌐 Spouštím Web Monitor na portu 8084..."
        nohup python3 web_monitor_final.py > web_final.log 2>&1 & echo $! > web_final.pid
        
        echo "✅ Kompletní systém spuštěn!"
        echo "📱 Web Monitor: http://localhost:8084"
        echo "📝 Logy: tail -f news_perun.log web_final.log"
        ;;
        
    2)
        echo "📰 Spouštím standalone News Analyzer..."
        python3 news_perun_integration.py
        ;;
        
    3)
        echo "🔗 Spouštím pouze Perun Integration..."
        if [ -f "news_perun.pid" ]; then
            kill $(cat news_perun.pid) 2>/dev/null || true
            rm -f news_perun.pid
        fi
        nohup python3 news_perun_integration.py > news_perun.log 2>&1 & echo $! > news_perun.pid
        echo "✅ News-Perun integrace spuštěna na pozadí"
        echo "📝 Log: tail -f news_perun.log"
        ;;
        
    4)
        echo "🧪 Testuje News API klíče..."
        python3 -c "
from news_scraper import CryptoNewsScraper
from translator import CryptoNewsTranslator
from sentiment_analyzer import CryptoSentimentAnalyzer

print('📡 Test RSS scraping...')
scraper = CryptoNewsScraper()
articles = scraper.scrape_all_sources()
print(f'✅ Nalezeno {len(articles)} článků')

print('🌐 Test Google Translate...')
translator = CryptoNewsTranslator()
test_text = 'Bitcoin price is rising today'
translated = translator.translate_to_czech(test_text, 'en')
print(f'✅ Překlad: {translated}')

print('🤖 Test Gemini AI...')
analyzer = CryptoSentimentAnalyzer()
result = analyzer.analyze_sentiment('Bitcoin bull market incoming', 'Test')
print(f'✅ Sentiment: {result.get(\"sentiment\", 0):.2f}')

print('🎉 Všechny API klíče fungují!')
"
        ;;
        
    5)
        echo "⏹️ Zastavuji všechny News služby..."
        
        # News-Perun Integration
        if [ -f "news_perun.pid" ]; then
            echo "📰 Zastavuji News-Perun integraci..."
            kill $(cat news_perun.pid) 2>/dev/null || true
            rm -f news_perun.pid
        fi
        
        # Web Monitor (pouze pokud běží pro News)
        if [ -f "web_final.pid" ]; then
            echo "🌐 Zastavuji Web Monitor..."
            kill $(cat web_final.pid) 2>/dev/null || true
            rm -f web_final.pid
        fi
        
        echo "✅ Všechny News služby zastaveny"
        ;;
        
    *)
        echo "❌ Neplatná volba. Ukončuji."
        exit 1
        ;;
esac

echo ""
echo "📊 Status služeb:"
if [ -f "news_perun.pid" ] && kill -0 $(cat news_perun.pid) 2>/dev/null; then
    echo "✅ News-Perun Integration: Běží (PID: $(cat news_perun.pid))"
else
    echo "❌ News-Perun Integration: Neběží"
fi

if [ -f "web_final.pid" ] && kill -0 $(cat web_final.pid) 2>/dev/null; then
    echo "✅ Web Monitor: Běží (PID: $(cat web_final.pid)) - http://localhost:8084"
else
    echo "❌ Web Monitor: Neběží"
fi

echo ""
echo "🔧 Užitečné příkazy:"
echo "📝 Sledování logů: tail -f news_perun.log"
echo "🌐 Web Monitor: http://localhost:8084"
echo "⏹️ Zastavení: ./stop_news_perun.sh"