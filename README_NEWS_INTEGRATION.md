# 📰 NEWS-PERUN INTEGRATION - KOMPLETNÍ PRŮVODCE

**AI-powered crypto news sentiment analysis integrovaná do LakyLuk Perun 2.0**

## 🎉 HOTOVO - KOMPLETNÍ IMPLEMENTACE

### ✅ Co bylo implementováno:

1. **🔧 News-Perun Bridge** - `news_perun_integration.py`
2. **📊 Web Monitor rozšíření** - přidána News sekce 
3. **⚡ Automatizace** - management skripty
4. **📱 Desktop notifikace** - real-time alerts
5. **🧪 Testování** - všechny API klíče fungují
6. **⏰ Scheduled Mode** - analýzy 2x denně (11:00 a 20:00)

---

## 🚀 SPUŠTĚNÍ NEWS-PERUN SYSTÉMU

### **Možnost 1: Interaktivní spuštění**
```bash
cd /home/laky/lakylukperun2.0
./start_news_perun.sh
# Vyberte možnost 1: Kompletní systém
```

### **Možnost 2: Přímé spuštění**
```bash
cd /home/laky/lakylukperun2.0
echo "1" | ./start_news_perun.sh
```

### **Zastavení systému:**
```bash
./stop_news_perun.sh
```

---

## 📊 TRIPLE ENHANCEMENT SYSTEM

### **🎯 Kombinované signály:**
1. **📈 TradingView** (70%) - technické indikátory
2. **📺 YouTube** (15%) - influencer sentiment  
3. **📰 News** (15%) - fundamentální analýza

### **Příklad rozhodnutí:**
```
🚀 PERUN ENHANCED DECISION - BTCUSD
=====================================

📈 TradingView: BUY (0.75)
📺 YouTube: BULLISH (+0.6) 
📰 News: BULLISH (+0.8)

🎯 FINAL SIGNAL: STRONG BUY (0.85)
💡 Enhanced by News: +15% strength
```

---

## 🌐 WEB MONITOR ROZŠÍŘENÍ

### **Nová sekce: 📰 Crypto News Sentiment Analysis**
- **URL**: `http://localhost:8084`
- **Obsah**:
  - Celkový market sentiment
  - Nejnovější analyzované články
  - Top kryptoměny podle zmínek
  - Trading doporučení AI
  - Real-time refresh každých 30s

---

## 📱 DESKTOP NOTIFIKACE

### **Typy notifikací:**
- **🚀 Systémové**: Start/stop News systému
- **📰 Analýza**: Dokončení News analýzy
- **⚡ Silné signály**: BUY/SELL doporučení
- **❌ Chyby**: Problémy s API nebo systémem

### **Nastavení urgency:**
- **Low**: Běžné analýzy a status
- **Normal**: Neutrální signály
- **Critical**: Silné BUY/SELL signály

---

## 🔧 TECHNICKÉ DETAILY

### **News zdroje:**
- **KryptoNovinky.cz** 🇨🇿 (české zprávy)
- **CoinDesk, Cointelegraph** 🇺🇸 (breaking news)
- **Decrypt, The Block, Blockworks** 🇺🇸 (analýzy)

### **AI pipeline:**
1. **RSS scraping** → články z 6 zdrojů
2. **Google Translate** → překlad do češtiny
3. **Gemini AI** → sentiment analýza (-1.0 až +1.0)
4. **Trading signály** → BUY/SELL/HOLD/NEUTRAL

### **Konfigurace (Scheduled Mode):**
```python
config = {
    'scheduled_times': ['11:00', '20:00'], # 2x denně místo 30 minut
    'sentiment_threshold': 0.4,            # Práh signálů
    'confidence_threshold': 0.6,           # Min jistota
    'max_news_influence': 0.3,             # Max 30% vliv
    'max_articles_to_analyze': 15          # Rychlost
}
```

---

## 📝 SOUBORY A LOGY

### **Klíčové soubory:**
```
lakylukperun2.0/
├── news_perun_integration.py     # Hlavní News-Perun bridge
├── news_scraper.py               # RSS scraping
├── translator.py                 # Google Translate
├── sentiment_analyzer.py         # Gemini AI
├── news_notifications.py         # Desktop notifikace
├── web_monitor_final.py          # Rozšířený web monitor
├── start_news_perun.sh          # Spouštěcí skript
├── stop_news_perun.sh           # Stop skript
└── test_news_apis.py            # Test všech API
```

### **Logy a výstupy:**
```
news_perun.log                   # Hlavní News log
news_analysis_YYYYMMDD_HHMMSS.json  # AI analýzy
news_perun.pid                   # Process ID
web_final.log                    # Web monitor log
```

---

## 🧪 TESTOVÁNÍ A DEBUGOVÁNÍ

### **Test API klíčů:**
```bash
./start_news_perun.sh
# Vyberte možnost 4: Test News API
```

### **Standalone test:**
```bash
python3 test_news_apis.py
```

### **Sledování logů:**
```bash
tail -f news_perun.log
tail -f web_final.log
```

### **Status check:**
```bash
ps aux | grep news_perun
ps aux | grep web_monitor
```

---

## ⚠️ ŘEŠENÍ PROBLÉMŮ

### **News analýza neběží:**
```bash
# Restart systému
./stop_news_perun.sh
./start_news_perun.sh
```

### **Chybějící dependencies:**
```bash
source venv/bin/activate
pip install googletrans==4.0.0rc1 google-generativeai feedparser
```

### **API klíče nefungují:**
- **Google Translate**: Automatické (free tier)
- **Gemini AI**: `AIzaSyDianaJzYYlmG9pvVVSjGWn9PAwokRMCNI`

### **Notifikace nefungují:**
```bash
# Instalace notify-send
sudo apt install libnotify-bin
```

---

## 📈 OČEKÁVANÉ VÝSLEDKY

### **Scheduled analýzy 2x denně (11:00 a 20:00):**
- ✅ 15+ crypto článků analyzováno
- ✅ Překlad do češtiny
- ✅ AI sentiment skóre
- ✅ Trading signály pro 8 crypto párů
- ✅ Desktop notifikace při silných signálech
- ✅ Platnost signálů: 24 hodin (místo 2 hodin)

### **Web monitor upgrade:**
- ✅ Real-time News sentiment sekce
- ✅ Top kryptoměny podle zmínek  
- ✅ AI trading doporučení
- ✅ Integrováno s YouTube + TradingView daty

### **Non-invasive enhancement:**
- ✅ Max 30% vliv na Perun rozhodnutí
- ✅ Kombinace s TradingView (70%) + YouTube (15%)
- ✅ Ochrana proti konfliktním signálům

---

## 🎯 DALŠÍ MOŽNOSTI

### **Rozšíření zdrojů:**
- Přidat další české crypto weby
- Twitter/X crypto účty
- Reddit crypto subreddity

### **AI vylepšení:**
- Claude 3.5 Sonnet místo Gemini
- Vlastní fine-tuned model
- Multi-language sentiment

### **Trading integrace:**
- Direct Bybit API integrace
- Futures trading signály
- Portfolio management

---

## ✅ FINÁLNÍ STATUS

🎉 **NEWS-PERUN INTEGRATION KOMPLETNĚ IMPLEMENTOVÁNA!**

Systém je připraven k provozu a plně integrován s LakyLuk Perun 2.0. 
Stejný přístup jako YouTube Analyst - spolehlivé, non-invasive enhancement trading signálů.

**Spuštění:** `./start_news_perun.sh` → volba 1  
**Web Monitor:** `http://localhost:8084`  
**Status:** ✅ Všechny testy prošly  

---

*Autor: LakyLuk + Claude | Datum: 24.6.2025 | Verze: 1.0*