#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 LakyLuk Crypto News Analyzer - Translator Module
Autor: LakyLuk | Datum: 24.6.2025
"""

from googletrans import Translator
import time
import json
from typing import List, Dict, Any
import re

class CryptoNewsTranslator:
    def __init__(self):
        self.translator = Translator()
        self.translation_cache = {}
        self.max_retries = 3
        self.delay_between_requests = 0.5
    
    def detect_language(self, text: str) -> str:
        """Detekce jazyka textu"""
        try:
            detection = self.translator.detect(text)
            return detection.lang
        except Exception as e:
            print(f"⚠️ Chyba při detekci jazyka: {e}")
            return 'en'  # Default na angličtinu
    
    def translate_to_czech(self, text: str, source_lang: str = 'auto') -> str:
        """Překlad textu do češtiny"""
        if not text or text.strip() == '':
            return text
        
        # Ošetření pro již české texty
        if source_lang == 'cs' or self.detect_language(text) == 'cs':
            return text
        
        # Cache kontrola
        cache_key = f"{source_lang}_{hash(text)}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
        
        # Pokus o překlad s retry
        for attempt in range(self.max_retries):
            try:
                time.sleep(self.delay_between_requests)
                
                # Překlad do češtiny
                result = self.translator.translate(text, src=source_lang, dest='cs')
                translated_text = result.text
                
                # Uložení do cache
                self.translation_cache[cache_key] = translated_text
                
                return translated_text
                
            except Exception as e:
                print(f"⚠️ Pokus {attempt + 1}: Chyba při překladu: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"❌ Překlad se nezdařil po {self.max_retries} pokusech")
                    return text  # Vrácení původního textu
    
    def translate_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Překlad celého článku"""
        translated_article = article.copy()
        
        # Překlad pouze anglických článků
        if article.get('language', 'en') == 'en':
            print(f"🔄 Překládám: {article['title'][:50]}...")
            
            # Překlad titulku
            translated_article['title_cs'] = self.translate_to_czech(
                article['title'], 'en'
            )
            
            # Překlad shrnutí
            if article.get('summary'):
                # Ošetření HTML tagů
                clean_summary = self.clean_html(article['summary'])
                translated_article['summary_cs'] = self.translate_to_czech(
                    clean_summary, 'en'
                )
            
            # Označení jako přeloženo
            translated_article['translated'] = True
        else:
            # České články nepřekládáme
            translated_article['title_cs'] = article['title']
            translated_article['summary_cs'] = article.get('summary', '')
            translated_article['translated'] = False
        
        return translated_article
    
    def translate_articles_batch(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch překlad všech článků"""
        translated_articles = []
        
        print(f"🌐 Spouštím překlad {len(articles)} článků...")
        
        for i, article in enumerate(articles, 1):
            print(f"📝 {i}/{len(articles)}: {article['source']}")
            
            try:
                translated_article = self.translate_article(article)
                translated_articles.append(translated_article)
            except Exception as e:
                print(f"❌ Chyba při překladu článku {i}: {e}")
                # Přidání nepřeloženého článku
                article['translated'] = False
                article['title_cs'] = article['title']
                article['summary_cs'] = article.get('summary', '')
                translated_articles.append(article)
        
        print(f"✅ Překlad dokončen: {len(translated_articles)} článků")
        return translated_articles
    
    def clean_html(self, text: str) -> str:
        """Ošetření HTML tagů v textu"""
        if not text:
            return text
        
        # Odstranění HTML tagů
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # Odstranění nadbytečných mezer
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        return clean_text.strip()
    
    def save_cache(self, filename: str = 'data/translation_cache.json'):
        """Uložení cache překladu"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)
            print(f"💾 Cache uložena: {filename}")
        except Exception as e:
            print(f"❌ Chyba při ukládání cache: {e}")
    
    def load_cache(self, filename: str = 'data/translation_cache.json'):
        """Načtení cache překladu"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.translation_cache = json.load(f)
            print(f"📥 Cache načtena: {len(self.translation_cache)} položek")
        except FileNotFoundError:
            print("📁 Cache soubor neexistuje, začínám s prázdnou cache")
        except Exception as e:
            print(f"❌ Chyba při načítání cache: {e}")

def main():
    """Test funkce translatoru"""
    # Import scraper pro test
    import sys
    sys.path.append('.')
    from news_scraper import CryptoNewsScraper
    
    # Scraping článků
    scraper = CryptoNewsScraper()
    articles = scraper.scrape_all_sources()
    
    if not articles:
        print("❌ Žádné články k překladu")
        return
    
    # Test překladu
    translator = CryptoNewsTranslator()
    translator.load_cache()
    
    # Překlad pouze prvních 3 článků pro test
    test_articles = articles[:3]
    translated_articles = translator.translate_articles_batch(test_articles)
    
    # Uložení cache
    translator.save_cache()
    
    # Zobrazení výsledků
    print("\n🇨🇿 PŘELOŽENÉ ČLÁNKY:")
    for i, article in enumerate(translated_articles, 1):
        print(f"\n{i}. {article['source']} ({'EN→CS' if article['translated'] else 'CZ'})")
        print(f"   📰 {article['title_cs'][:80]}...")
        if article.get('summary_cs'):
            print(f"   📄 {article['summary_cs'][:100]}...")

if __name__ == "__main__":
    main()