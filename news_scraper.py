#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 LakyLuk Crypto News Analyzer - RSS Feed Scraper
Autor: LakyLuk | Datum: 24.6.2025
"""

import feedparser
import requests
from datetime import datetime, timedelta
import json
import re
from typing import List, Dict, Any
import time

class CryptoNewsScraper:
    def __init__(self):
        self.crypto_sources = {
            'kryptonovinky': {
                'url': 'https://www.kryptonovinky.cz/feed/',
                'name': 'KryptoNovinky.cz',
                'priority': 1,
                'language': 'cs'
            },
            'coindesk': {
                'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
                'name': 'CoinDesk',
                'priority': 1,
                'language': 'en'
            },
            'cointelegraph': {
                'url': 'https://cointelegraph.com/rss',
                'name': 'Cointelegraph', 
                'priority': 1,
                'language': 'en'
            },
            'decrypt': {
                'url': 'https://decrypt.co/feed',
                'name': 'Decrypt',
                'priority': 2,
                'language': 'en'
            },
            'theblock': {
                'url': 'https://www.theblock.co/rss.xml',
                'name': 'The Block',
                'priority': 2,
                'language': 'en'
            },
            'blockworks': {
                'url': 'https://blockworks.co/feed/',
                'name': 'Blockworks',
                'priority': 3,
                'language': 'en'
            }
        }
        
        self.crypto_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'ripple', 'xrp',
            'solana', 'sol', 'cardano', 'ada', 'arbitrum', 'arb',
            'avalanche', 'avax', 'polkadot', 'dot', 'crypto', 'cryptocurrency',
            'blockchain', 'defi', 'altcoin', 'altseason',
            # České klíčové slova
            'krypto', 'kryptoměna', 'kryptoměny', 'altcoin', 'altcoiny',
            'blockchain', 'blokchain', 'těžba', 'mining', 'pump', 'dump'
        ]
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
    
    def scrape_source(self, source_key: str) -> List[Dict[str, Any]]:
        """Scrape jednoho RSS zdroje"""
        source = self.crypto_sources[source_key]
        articles = []
        
        try:
            print(f"📡 Scrapuji {source['name']}...")
            
            # Stažení RSS feedu
            response = self.session.get(source['url'], timeout=10)
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                print(f"⚠️ Problém s RSS feed: {source['name']}")
                return articles
            
            # Zpracování článků
            for entry in feed.entries[:20]:  # Max 20 článků
                # Kontrola relevance pro crypto
                if self._is_crypto_relevant(entry.title + ' ' + entry.get('summary', '')):
                    article = {
                        'title': entry.title,
                        'summary': entry.get('summary', ''),
                        'link': entry.link,
                        'published': self._parse_date(entry.get('published')),
                        'source': source['name'],
                        'source_key': source_key,
                        'priority': source['priority'],
                        'language': source.get('language', 'en'),
                        'crypto_coins': self._extract_crypto_coins(entry.title + ' ' + entry.get('summary', ''))
                    }
                    articles.append(article)
            
            print(f"✅ {source['name']}: {len(articles)} crypto článků")
            
        except Exception as e:
            print(f"❌ Chyba při scrapování {source['name']}: {e}")
        
        return articles
    
    def scrape_all_sources(self) -> List[Dict[str, Any]]:
        """Scrape všech zdrojů"""
        all_articles = []
        
        print(f"🚀 Spouštím scraping {len(self.crypto_sources)} zdrojů...")
        
        for source_key in self.crypto_sources:
            articles = self.scrape_source(source_key)
            all_articles.extend(articles)
            time.sleep(1)  # Slušnost k serverům
        
        # Seřazení podle priority a data
        all_articles.sort(key=lambda x: (x['priority'], x['published']), reverse=True)
        
        print(f"📰 Celkem nalezeno: {len(all_articles)} crypto článků")
        return all_articles
    
    def _is_crypto_relevant(self, text: str) -> bool:
        """Kontrola, zda je článek o kryptoměnách"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.crypto_keywords)
    
    def _extract_crypto_coins(self, text: str) -> List[str]:
        """Extrakce zmíněných kryptoměn"""
        text_lower = text.lower()
        found_coins = []
        
        coin_mapping = {
            'bitcoin': 'BTC', 'btc': 'BTC',
            'ethereum': 'ETH', 'eth': 'ETH', 
            'ripple': 'XRP', 'xrp': 'XRP',
            'solana': 'SOL', 'sol': 'SOL',
            'cardano': 'ADA', 'ada': 'ADA',
            'arbitrum': 'ARB', 'arb': 'ARB',
            'avalanche': 'AVAX', 'avax': 'AVAX',
            'polkadot': 'DOT', 'dot': 'DOT'
        }
        
        for keyword, symbol in coin_mapping.items():
            if keyword in text_lower and symbol not in found_coins:
                found_coins.append(symbol)
        
        return found_coins
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parsing data publikace"""
        if not date_str:
            return datetime.now()
        
        try:
            return datetime.fromtimestamp(time.mktime(time.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')))
        except:
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                return datetime.now()
    
    def save_articles(self, articles: List[Dict[str, Any]], filename: str = None):
        """Uložení článků do JSON"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data/crypto_news_{timestamp}.json"
        
        # Konverze datetime objektů na string
        for article in articles:
            if isinstance(article['published'], datetime):
                article['published'] = article['published'].isoformat()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Články uloženy: {filename}")
        return filename

def main():
    """Test funkce"""
    scraper = CryptoNewsScraper()
    articles = scraper.scrape_all_sources()
    
    if articles:
        filename = scraper.save_articles(articles)
        
        print("\n📊 PŘEHLED ČLÁNKŮ:")
        for i, article in enumerate(articles[:5], 1):
            print(f"{i}. {article['title'][:80]}...")
            print(f"   🏢 {article['source']} | 🪙 {', '.join(article['crypto_coins']) or 'N/A'}")
            print()

if __name__ == "__main__":
    main()