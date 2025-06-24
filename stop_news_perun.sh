#!/bin/bash
# News-Perun Integration Stop Script
# Zastavení News monitoring systému

echo "⏹️ News-Perun Integration Stop"
echo "=============================="

cd /home/laky/lakylukperun2.0

echo "🔍 Hledám běžící News procesy..."

# Zastavení News-Perun Integration
if [ -f "news_perun.pid" ]; then
    PID=$(cat news_perun.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "📰 Zastavuji News-Perun Integration (PID: $PID)..."
        kill $PID
        sleep 2
        
        # Force kill pokud stále běží
        if kill -0 $PID 2>/dev/null; then
            echo "💥 Force kill News-Perun Integration..."
            kill -9 $PID
        fi
        
        echo "✅ News-Perun Integration zastaven"
    else
        echo "⚠️ News-Perun Integration neběží"
    fi
    rm -f news_perun.pid
else
    echo "⚠️ news_perun.pid nenalezen"
fi

# Zastavení Web Monitoru (pouze pokud běží pro News)
if [ -f "web_final.pid" ]; then
    WEB_PID=$(cat web_final.pid)
    if kill -0 $WEB_PID 2>/dev/null; then
        echo "🌐 Zastavuji Web Monitor (PID: $WEB_PID)..."
        kill $WEB_PID
        sleep 2
        
        # Force kill pokud stále běží
        if kill -0 $WEB_PID 2>/dev/null; then
            echo "💥 Force kill Web Monitor..."
            kill -9 $WEB_PID
        fi
        
        echo "✅ Web Monitor zastaven"
    else
        echo "⚠️ Web Monitor neběží"
    fi
    rm -f web_final.pid
else
    echo "⚠️ web_final.pid nenalezen"
fi

# Kontrola dalších News procesů
echo "🔍 Kontrola dalších News procesů..."
NEWS_PROCS=$(ps aux | grep -E "(news_|sentiment_|translator)" | grep -v grep | grep python)
if [ ! -z "$NEWS_PROCS" ]; then
    echo "⚠️ Nalezeny další News procesy:"
    echo "$NEWS_PROCS"
    echo ""
    read -p "Chcete je také zastavit? (y/n): " kill_others
    if [[ $kill_others =~ ^[Yy]$ ]]; then
        pkill -f "news_"
        pkill -f "sentiment_"
        pkill -f "translator"
        echo "✅ Další News procesy zastaveny"
    fi
fi

echo ""
echo "📊 Finální status:"
if ! pgrep -f "news_perun_integration" > /dev/null; then
    echo "✅ News-Perun Integration: Zastaven"
else
    echo "❌ News-Perun Integration: Stále běží"
fi

if ! pgrep -f "web_monitor_final" > /dev/null; then
    echo "✅ Web Monitor: Zastaven"
else
    echo "❌ Web Monitor: Stále běží"
fi

echo ""
echo "🧹 Čištění log souborů..."
if [ -f "news_perun.log" ]; then
    echo "📝 news_perun.log: $(wc -l < news_perun.log) řádků"
fi

echo ""
echo "✅ News-Perun systém úplně zastaven!"
echo "🚀 Pro opětovné spuštění: ./start_news_perun.sh"