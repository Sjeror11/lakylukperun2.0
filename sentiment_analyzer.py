#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 LakyLuk Crypto News Analyzer - Gemini AI Sentiment Analyzer
Autor: LakyLuk | Datum: 24.6.2025
Využívá stejný Gemini API klíč jako LakyLuk Perun 2.0
"""

import google.generativeai as genai
import json
import time
from typing import List, Dict, Any, Tuple
from datetime import datetime
import re

class CryptoSentimentAnalyzer:
    def __init__(self):
        # Stejný Gemini API klíč jako v LakyLuk Perun
        self.api_key = "AIzaSyDianaJzYYlmG9pvVVSjGWn9PAwokRMCNI"
        genai.configure(api_key=self.api_key)
        
        # Gemini model pro české texty
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Cache pro analýzy
        self.sentiment_cache = {}
        
        # Crypto mapping pro trading signály
        self.crypto_mapping = {
            'bitcoin': 'BTCUSD', 'btc': 'BTCUSD',
            'ethereum': 'ETHUSD', 'eth': 'ETHUSD',
            'ripple': 'XRPUSD', 'xrp': 'XRPUSD',
            'solana': 'SOLUSD', 'sol': 'SOLUSD',
            'cardano': 'ADAUSD', 'ada': 'ADAUSD',
            'arbitrum': 'ARBUSD', 'arb': 'ARBUSD',
            'avalanche': 'AVAXUSD', 'avax': 'AVAXUSD',
            'polkadot': 'DOTUSD', 'dot': 'DOTUSD'
        }
    
    def analyze_sentiment(self, text: str, title: str = "") -> Dict[str, Any]:
        """AI sentiment analýza pomocí Gemini"""
        # Cache kontrola
        cache_key = hash(f"{title}_{text}")
        if cache_key in self.sentiment_cache:
            return self.sentiment_cache[cache_key]
        
        # Prompt pro Gemini (v češtině pro lepší analýzu)
        prompt = f"""
Analyzuj sentiment tohoto crypto článku a výsledek vrať POUZE jako JSON:

TITULEK: {title}
OBSAH: {text}

Analýza:
1. Sentiment: hodnotou od -1.0 (velmi bearish) do +1.0 (velmi bullish)
2. Confidence: jistota analýzy od 0.0 do 1.0
3. Crypto coins: seznam zmíněných kryptoměn (BTC, ETH, XRP, SOL, ADA, ARB, AVAX, DOT)
4. Key points: 3 hlavní body v češtině
5. Trading signal: "BUY", "SELL", "HOLD" nebo "NEUTRAL"

Vrať POUZE JSON ve formátu:
{{
    "sentiment": číslo,
    "confidence": číslo,
    "crypto_coins": ["seznam"],
    "key_points": ["bod1", "bod2", "bod3"],
    "trading_signal": "signál"
}}
"""
        
        try:
            # Gemini analýza
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Ošetření Markdown formátu
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Parsing JSON odpovědi
            result = json.loads(response_text)
            
            # Validace a normalizace
            sentiment_result = {
                'sentiment': max(-1.0, min(1.0, float(result.get('sentiment', 0.0)))),
                'confidence': max(0.0, min(1.0, float(result.get('confidence', 0.5)))),
                'crypto_coins': result.get('crypto_coins', []),
                'key_points': result.get('key_points', []),
                'trading_signal': result.get('trading_signal', 'NEUTRAL'),
                'analyzed_at': datetime.now().isoformat()
            }
            
            # Uložení do cache
            self.sentiment_cache[cache_key] = sentiment_result
            
            return sentiment_result
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Chyba při parsing JSON: {e}")
            print(f"Raw response: {response_text}")
            return self._default_sentiment()
        except Exception as e:
            print(f"❌ Chyba při Gemini analýze: {e}")
            return self._default_sentiment()
    
    def _default_sentiment(self) -> Dict[str, Any]:
        """Fallback sentiment při chybě"""
        return {
            'sentiment': 0.0,
            'confidence': 0.0,
            'crypto_coins': [],
            'key_points': ['Analýza se nezdařila'],
            'trading_signal': 'NEUTRAL',
            'analyzed_at': datetime.now().isoformat()
        }
    
    def analyze_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Analýza celého článku"""
        analyzed_article = article.copy()
        
        # Použití českého překladu pokud existuje
        title = article.get('title_cs', article.get('title', ''))
        content = article.get('summary_cs', article.get('summary', ''))
        
        print(f"🧠 Analyzuji sentiment: {title[:50]}...")
        
        # Sentiment analýza
        sentiment_result = self.analyze_sentiment(content, title)
        
        # Přidání sentiment dat k článku
        analyzed_article['sentiment'] = sentiment_result
        
        # Mapování crypto coins na trading symboly
        trading_symbols = []
        for coin in sentiment_result['crypto_coins']:
            symbol = self.crypto_mapping.get(coin.lower())
            if symbol and symbol not in trading_symbols:
                trading_symbols.append(symbol)
        
        analyzed_article['trading_symbols'] = trading_symbols
        
        # Krátké zpoždění mezi requesty
        time.sleep(0.5)
        
        return analyzed_article
    
    def analyze_articles_batch(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch analýza všech článků"""
        analyzed_articles = []
        
        print(f"🤖 Spouštím Gemini AI analýzu {len(articles)} článků...")
        
        for i, article in enumerate(articles, 1):
            print(f"📈 {i}/{len(articles)}: {article['source']}")
            
            try:
                analyzed_article = self.analyze_article(article)
                analyzed_articles.append(analyzed_article)
            except Exception as e:
                print(f"❌ Chyba při analýze článku {i}: {e}")
                # Přidání bez analýzy
                article['sentiment'] = self._default_sentiment()
                article['trading_symbols'] = []
                analyzed_articles.append(article)
        
        print(f"✅ AI analýza dokončena: {len(analyzed_articles)} článků")
        return analyzed_articles
    
    def generate_summary_report(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generování souhrnné zprávy"""
        if not articles:
            return {}
        
        # Statistiky
        total_articles = len(articles)
        bullish_count = sum(1 for a in articles if a.get('sentiment', {}).get('sentiment', 0) > 0.2)
        bearish_count = sum(1 for a in articles if a.get('sentiment', {}).get('sentiment', 0) < -0.2)
        neutral_count = total_articles - bullish_count - bearish_count
        
        # Průměrný sentiment
        avg_sentiment = sum(a.get('sentiment', {}).get('sentiment', 0) for a in articles) / total_articles
        
        # Top crypto coins
        all_coins = []
        for article in articles:
            all_coins.extend(article.get('trading_symbols', []))
        
        from collections import Counter
        top_coins = Counter(all_coins).most_common(5)
        
        # Trading signály
        buy_signals = [a for a in articles if a.get('sentiment', {}).get('trading_signal') == 'BUY']
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_articles': total_articles,
            'sentiment_distribution': {
                'bullish': bullish_count,
                'bearish': bearish_count,
                'neutral': neutral_count
            },
            'average_sentiment': round(avg_sentiment, 3),
            'market_mood': self._get_market_mood(avg_sentiment),
            'top_cryptocurrencies': [{'symbol': coin, 'mentions': count} for coin, count in top_coins],
            'buy_signals_count': len(buy_signals),
            'recommendation': self._get_trading_recommendation(avg_sentiment, bullish_count, total_articles)
        }
        
        return summary
    
    def _get_market_mood(self, sentiment: float) -> str:
        """Určení nálady trhu"""
        if sentiment > 0.3:
            return "🟢 Velmi Bullish"
        elif sentiment > 0.1:
            return "🟢 Mírně Bullish"
        elif sentiment > -0.1:
            return "🟡 Neutrální"
        elif sentiment > -0.3:
            return "🔴 Mírně Bearish"
        else:
            return "🔴 Velmi Bearish"
    
    def _get_trading_recommendation(self, avg_sentiment: float, bullish_count: int, total: int) -> str:
        """Trading doporučení"""
        bullish_ratio = bullish_count / total if total > 0 else 0
        
        if avg_sentiment > 0.3 and bullish_ratio > 0.6:
            return "🚀 Silné nakupování - Altseason možná blízko"
        elif avg_sentiment > 0.1 and bullish_ratio > 0.4:
            return "📈 Zvážit nákup - Pozitivní sentiment"
        elif avg_sentiment < -0.3 and bullish_ratio < 0.2:
            return "⚠️ Opatrnost - Bearish sentiment"
        else:
            return "⏸️ Vyčkat - Neutrální trh"

def main():
    """Test funkce analyzeru"""
    # Import předchozích modulů
    import sys
    sys.path.append('.')
    from news_scraper import CryptoNewsScraper
    from translator import CryptoNewsTranslator
    
    print("🔄 Načítám články a překládám...")
    
    # Scraping a překlad
    scraper = CryptoNewsScraper()
    articles = scraper.scrape_all_sources()
    
    if not articles:
        print("❌ Žádné články k analýze")
        return
    
    # Překlad (pouze prvních 3 pro test)
    translator = CryptoNewsTranslator()
    test_articles = articles[:3]
    translated_articles = translator.translate_articles_batch(test_articles)
    
    # Sentiment analýza
    analyzer = CryptoSentimentAnalyzer()
    analyzed_articles = analyzer.analyze_articles_batch(translated_articles)
    
    # Souhrnná zpráva
    summary = analyzer.generate_summary_report(analyzed_articles)
    
    # Výsledky
    print("\n🤖 GEMINI AI SENTIMENT ANALÝZA:")
    print(f"📊 Celkový sentiment: {summary['average_sentiment']} ({summary['market_mood']})")
    print(f"📈 Distribuce: {summary['sentiment_distribution']}")
    print(f"🪙 Top kryptoměny: {summary['top_cryptocurrencies']}")
    print(f"💡 Doporučení: {summary['recommendation']}")
    
    print("\n📰 DETAILNÍ ANALÝZA ČLÁNKŮ:")
    for i, article in enumerate(analyzed_articles, 1):
        sentiment = article['sentiment']
        print(f"\n{i}. {article['source']} | Sentiment: {sentiment['sentiment']:.2f}")
        print(f"   📰 {article['title_cs'][:60]}...")
        print(f"   📊 Signál: {sentiment['trading_signal']} | Jistota: {sentiment['confidence']:.2f}")
        print(f"   🪙 Coins: {', '.join(sentiment['crypto_coins']) or 'N/A'}")

if __name__ == "__main__":
    main()