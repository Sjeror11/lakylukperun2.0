#!/usr/bin/env python3
"""
Test všech News API klíčů a modulů
Autor: LakyLuk | Datum: 24.6.2025
"""

import sys
import time

def test_rss_scraping():
    """Test RSS scrapingu"""
    print("📡 Testuje RSS scraping...")
    try:
        from news_scraper import CryptoNewsScraper
        
        scraper = CryptoNewsScraper()
        print(f"   ✅ Inicializace: OK")
        print(f"   📊 Sledované zdroje: {len(scraper.crypto_sources)}")
        
        # Test jednoho zdroje
        print("   🔍 Test KryptoNovinky.cz...")
        articles = scraper.scrape_source('kryptonovinky')
        print(f"   ✅ KryptoNovinky: {len(articles)} článků")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Chyba: {e}")
        return False

def test_google_translate():
    """Test Google Translate"""
    print("🌐 Testuje Google Translate...")
    try:
        from translator import CryptoNewsTranslator
        
        translator = CryptoNewsTranslator()
        print(f"   ✅ Inicializace: OK")
        
        # Test překladu
        test_text = "Bitcoin price is rising today due to institutional adoption"
        print(f"   🔄 Překládám: {test_text[:30]}...")
        
        translated = translator.translate_to_czech(test_text, 'en')
        print(f"   ✅ Překlad: {translated}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Chyba: {e}")
        return False

def test_gemini_ai():
    """Test Gemini AI sentiment"""
    print("🤖 Testuje Gemini AI...")
    try:
        from sentiment_analyzer import CryptoSentimentAnalyzer
        
        analyzer = CryptoSentimentAnalyzer()
        print(f"   ✅ Inicializace: OK")
        print(f"   🔑 API klíč: {analyzer.api_key[:20]}...")
        
        # Test sentiment analýzy
        test_title = "Bitcoin bull market incoming"
        test_content = "Institutional investors are buying Bitcoin massively"
        print(f"   🧠 Analyzuji sentiment...")
        
        result = analyzer.analyze_sentiment(test_content, test_title)
        
        sentiment = result.get('sentiment', 0)
        confidence = result.get('confidence', 0)
        signal = result.get('trading_signal', 'N/A')
        
        print(f"   ✅ Sentiment: {sentiment:.3f}")
        print(f"   ✅ Confidence: {confidence:.3f}")
        print(f"   ✅ Signal: {signal}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Chyba: {e}")
        return False

def test_integration():
    """Test celé integrace"""
    print("🔗 Testuje News-Perun integraci...")
    try:
        from news_perun_integration import NewsPerunIntegration
        
        integration = NewsPerunIntegration()
        print(f"   ✅ Inicializace: OK")
        print(f"   ⚙️ Config: {len(integration.config)} parametrů")
        print(f"   🪙 Kryptoměny: {len(integration.config['enabled_cryptos'])}")
        
        # Test inicializace analyzérů
        print("   🔧 Inicializuji analyzéry...")
        success = integration.initialize_analyzers()
        
        if success:
            print("   ✅ Analyzéry: OK")
            return True
        else:
            print("   ❌ Analyzéry: CHYBA")
            return False
        
    except Exception as e:
        print(f"   ❌ Chyba: {e}")
        return False

def main():
    """Hlavní test funkce"""
    print("🚀 TEST NEWS-PERUN API KLÍČŮ")
    print("="*40)
    print()
    
    tests = [
        ("RSS Scraping", test_rss_scraping),
        ("Google Translate", test_google_translate), 
        ("Gemini AI", test_gemini_ai),
        ("News-Perun Integration", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"🧪 {test_name}")
        print("-" * 30)
        
        start_time = time.time()
        success = test_func()
        duration = time.time() - start_time
        
        results.append((test_name, success, duration))
        
        if success:
            print(f"   ⏱️ Doba: {duration:.2f}s")
            print(f"   🎉 ÚSPĚCH")
        else:
            print(f"   💥 SELHÁNÍ")
        
        print()
    
    # Souhrnné výsledky
    print("📊 SOUHRN TESTŮ")
    print("="*40)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"✅ Úspěšné: {passed}/{total}")
    print(f"❌ Selhané: {total - passed}/{total}")
    print()
    
    for test_name, success, duration in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.2f}s)")
    
    print()
    
    if passed == total:
        print("🎉 VŠECHNY TESTY PROŠLY!")
        print("🚀 News-Perun systém je připraven k použití")
        return True
    else:
        print("⚠️ NĚKTERÉ TESTY SELHALY!")
        print("🔧 Zkontroluj API klíče a dependencies")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)