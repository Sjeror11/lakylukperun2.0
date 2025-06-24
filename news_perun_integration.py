#!/usr/bin/env python3
"""
News-Perun Trading Integration
Napojení crypto news sentiment analýzy na Perun trading systém
Autor: Claude + LakyLuk  
Datum: 24.6.2025
Inspirováno YouTube-Perun integrací
"""

import json
import time
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import signal
import sys

# Import News modulů
try:
    from news_scraper import CryptoNewsScraper
    from translator import CryptoNewsTranslator
    from sentiment_analyzer import CryptoSentimentAnalyzer
    from news_notifications import NewsNotifications
    # Import z hlavního Perun systému
    import perun_tradingview_multi as perun_main
except ImportError as e:
    print(f"❌ Chyba importu News modulů: {e}")
    sys.exit(1)

class NewsPerunIntegration:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Konfigurace (scheduled mode)
        self.config = {
            'scheduled_times': ['11:00', '20:00'],  # Analýza 2x denně
            'sentiment_threshold': 0.4,  # Práh pro generování signálů
            'confidence_threshold': 0.6,  # Minimální důvěryhodnost
            'max_news_influence': 0.3,  # Max vliv News na rozhodování (30%)
            'enabled_cryptos': ['BTCUSD', 'ETHUSD', 'XRPUSD', 'SOLUSD', 'ADAUSD', 'ARBUSD', 'AVAXUSD', 'DOTUSD'],
            'max_articles_to_analyze': 15  # Limit článků pro rychlost
        }
        
        # News analyzery
        self.scraper = None
        self.translator = None
        self.analyzer = None
        self.last_news_analysis = None
        self.last_analysis_time = None
        
        # Signály pro Perun
        self.news_signals = {}
        
        # Notifikace
        self.notifier = NewsNotifications()
        
        # Status
        self.running = False
        
        self.logger.info("🚀 NewsPerunIntegration inicializován")
    
    def setup_logging(self):
        """Nastavení logování"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('news_perun_integration.log'),
                logging.StreamHandler()
            ]
        )
    
    def initialize_analyzers(self):
        """Inicializace News analyzérů"""
        try:
            self.logger.info("🔧 Inicializuji News analyzéry...")
            
            self.scraper = CryptoNewsScraper()
            self.translator = CryptoNewsTranslator() 
            self.analyzer = CryptoSentimentAnalyzer()
            
            # Načtení cache pro rychlost
            self.translator.load_cache()
            
            self.logger.info("✅ News analyzéry inicializovány")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Chyba při inicializaci analyzérů: {e}")
            return False
    
    def perform_news_analysis(self):
        """Hlavní News analýza"""
        try:
            self.logger.info("📰 Spouštím News sentiment analýzu...")
            self.notifier.notify_analysis_started()
            
            # 1. Scraping článků
            self.logger.info("📡 Stahuji crypto články...")
            articles = self.scraper.scrape_all_sources()
            
            if not articles:
                self.logger.warning("⚠️ Žádné články nenalezeny")
                return None
            
            self.logger.info(f"✅ Nalezeno {len(articles)} článků")
            
            # 2. Limitace pro rychlost (jako u YouTube)
            articles_to_analyze = articles[:self.config['max_articles_to_analyze']]
            
            # 3. Překlad
            self.logger.info("🌐 Překládám články...")
            translated_articles = self.translator.translate_articles_batch(articles_to_analyze)
            
            # 4. Sentiment analýza
            self.logger.info("🤖 AI sentiment analýza...")
            analyzed_articles = self.analyzer.analyze_articles_batch(translated_articles)
            
            # 5. Generování souhrnu
            summary = self.analyzer.generate_summary_report(analyzed_articles)
            
            # 6. Uložení cache
            self.translator.save_cache()
            
            # 7. Uložení výsledků
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'news_analysis_{timestamp}.json'
            
            analysis_data = {
                'timestamp': datetime.now().isoformat(),
                'summary': summary,
                'articles': analyzed_articles[:10],  # Pouze top 10 pro rychlost
                'total_articles_found': len(articles),
                'articles_analyzed': len(analyzed_articles)
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.last_news_analysis = analysis_data
            self.last_analysis_time = datetime.now()
            
            # Notifikace o dokončení
            self.notifier.notify_analysis_completed(summary)
            
            self.logger.info(f"✅ News analýza dokončena: {filename}")
            return analysis_data
            
        except Exception as e:
            self.logger.error(f"❌ Chyba při News analýze: {e}")
            return None
    
    def generate_news_signals(self, analysis_data):
        """Generování trading signálů z News analýzy"""
        if not analysis_data:
            return {}
        
        signals = {}
        summary = analysis_data.get('summary', {})
        articles = analysis_data.get('articles', [])
        
        try:
            # Celkový sentiment
            overall_sentiment = summary.get('average_sentiment', 0.0)
            total_articles = summary.get('total_articles', 0)
            
            # Pro každou kryptoměnu
            for crypto in self.config['enabled_cryptos']:
                crypto_base = crypto.replace('USD', '')  # BTC, ETH, XRP...
                
                # Najít články relevantní pro tuto kryptoměnu
                relevant_articles = []
                for article in articles:
                    sentiment_data = article.get('sentiment', {})
                    crypto_coins = sentiment_data.get('crypto_coins', [])
                    
                    # Mapping coins na symboly
                    if (crypto_base in crypto_coins or 
                        crypto_base.lower() in [c.lower() for c in crypto_coins]):
                        relevant_articles.append(article)
                
                # Výpočet sentiment pro tuto kryptoměnu
                if relevant_articles:
                    crypto_sentiment = sum(
                        a.get('sentiment', {}).get('sentiment', 0) 
                        for a in relevant_articles
                    ) / len(relevant_articles)
                    
                    crypto_confidence = sum(
                        a.get('sentiment', {}).get('confidence', 0) 
                        for a in relevant_articles
                    ) / len(relevant_articles)
                    
                    article_count = len(relevant_articles)
                else:
                    # Použij celkový sentiment pokud není specifický
                    crypto_sentiment = overall_sentiment * 0.5  # Oslabený vliv
                    crypto_confidence = 0.3  # Nižší confidence
                    article_count = 0
                
                # Generování signálu (stejná logika jako YouTube)
                signal_strength = 0.0
                signal_type = "NEUTRAL"
                
                if (abs(crypto_sentiment) > self.config['sentiment_threshold'] and 
                    crypto_confidence > self.config['confidence_threshold']):
                    
                    if crypto_sentiment > 0:
                        signal_type = "BUY"
                        signal_strength = min(crypto_sentiment * crypto_confidence, 1.0)
                    else:
                        signal_type = "SELL" 
                        signal_strength = min(abs(crypto_sentiment) * crypto_confidence, 1.0)
                
                signals[crypto] = {
                    'signal': signal_type,
                    'strength': signal_strength,
                    'sentiment': crypto_sentiment,
                    'confidence': crypto_confidence,
                    'article_count': article_count,
                    'source': 'crypto_news',
                    'timestamp': datetime.now().isoformat()
                }
            
            self.news_signals = signals
            self.logger.info(f"📈 Vygenerováno {len(signals)} News signálů")
            
            # Notifikace o silných signálech
            self.notifier.notify_multiple_signals(signals)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"❌ Chyba při generování signálů: {e}")
            return {}
    
    def get_news_sentiment_for_symbol(self, symbol):
        """Získání News sentimentu pro konkrétní symbol (používá Perun)"""
        if symbol not in self.news_signals:
            return None
        
        signal_data = self.news_signals[symbol]
        
        # Kontrola stáří dat (stejně jako YouTube)
        try:
            signal_time = datetime.fromisoformat(signal_data['timestamp'])
            if datetime.now() - signal_time > timedelta(hours=2):
                self.logger.warning(f"⚠️ Starý News signál pro {symbol}")
                return None
        except:
            pass
        
        return {
            'sentiment': signal_data['sentiment'],
            'confidence': signal_data['confidence'],
            'strength': signal_data['strength'],
            'signal': signal_data['signal'],
            'source': 'crypto_news',
            'article_count': signal_data.get('article_count', 0)
        }
    
    def enhance_trading_signal(self, tv_signal, symbol):
        """Vylepšení TradingView signálu pomocí News sentimentu"""
        news_sentiment = self.get_news_sentiment_for_symbol(symbol)
        
        if not news_sentiment:
            return tv_signal, 0.0  # Žádný News vliv
        
        try:
            # Základní logika (stejná jako YouTube)
            news_influence = min(
                news_sentiment['strength'] * self.config['max_news_influence'],
                self.config['max_news_influence']
            )
            
            # Kombination signálů
            if news_sentiment['signal'] == 'BUY' and tv_signal > 0:
                enhanced_signal = tv_signal + (tv_signal * news_influence)
                enhanced_signal = min(enhanced_signal, 1.0)
            elif news_sentiment['signal'] == 'SELL' and tv_signal < 0:
                enhanced_signal = tv_signal + (tv_signal * news_influence) 
                enhanced_signal = max(enhanced_signal, -1.0)
            else:
                # Konfliktní signály - minimální vliv
                enhanced_signal = tv_signal + (news_sentiment['sentiment'] * news_influence * 0.3)
                enhanced_signal = max(-1.0, min(1.0, enhanced_signal))
            
            self.logger.info(
                f"📰 News enhancement {symbol}: "
                f"TV={tv_signal:.3f} → Enhanced={enhanced_signal:.3f} "
                f"(News: {news_sentiment['signal']}, vliv: {news_influence:.3f})"
            )
            
            return enhanced_signal, news_influence
            
        except Exception as e:
            self.logger.error(f"❌ Chyba při enhancement: {e}")
            return tv_signal, 0.0
    
    def should_run_analysis(self):
        """Kontrola, zda je čas na analýzu"""
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        
        # Kontrola scheduled časů
        for scheduled_time in self.config['scheduled_times']:
            # Tolerance 5 minut před a po
            scheduled_dt = datetime.strptime(scheduled_time, '%H:%M').replace(
                year=now.year, month=now.month, day=now.day
            )
            
            time_diff = abs((now - scheduled_dt).total_seconds())
            
            # Pokud jsme v rozmezí 5 minut od scheduled času
            if time_diff <= 300:  # 5 minut = 300 sekund
                # Kontrola, zda už analýza proběhla dnes v tomto čase
                if self.last_analysis_time:
                    last_analysis_scheduled = self.last_analysis_time.strftime('%H:%M')
                    last_analysis_date = self.last_analysis_time.date()
                    
                    # Pokud už analýza dnes v tomto čase proběhla, přeskočit
                    if (last_analysis_date == now.date() and 
                        last_analysis_scheduled == scheduled_time):
                        return False
                
                self.logger.info(f"⏰ Čas pro News analýzu: {scheduled_time} (aktuální: {current_time})")
                return True
        
        return False
    
    def next_analysis_time(self):
        """Vrátí čas další analýzy"""
        now = datetime.now()
        
        for scheduled_time in self.config['scheduled_times']:
            scheduled_dt = datetime.strptime(scheduled_time, '%H:%M').replace(
                year=now.year, month=now.month, day=now.day
            )
            
            if scheduled_dt > now:
                return scheduled_dt
        
        # Pokud už jsou všechny časy dnes za námi, vrátit první čas zítra
        tomorrow = now + timedelta(days=1)
        first_time = self.config['scheduled_times'][0]
        return datetime.strptime(first_time, '%H:%M').replace(
            year=tomorrow.year, month=tomorrow.month, day=tomorrow.day
        )

    def run_analysis_cycle(self):
        """Jeden cyklus News analýzy (jen pokud je čas)"""
        if not self.should_run_analysis():
            return
        
        try:
            # Provedení analýzy
            analysis_data = self.perform_news_analysis()
            
            if analysis_data:
                # Generování signálů
                self.generate_news_signals(analysis_data)
                
                self.logger.info("✅ News analýza cyklus dokončen")
            else:
                self.logger.warning("⚠️ News analýza selhala")
                
        except Exception as e:
            self.logger.error(f"❌ Chyba v News cyklu: {e}")
    
    def start(self):
        """Spuštění News-Perun integrace"""
        self.logger.info("🚀 Spouštím News-Perun integraci...")
        
        if not self.initialize_analyzers():
            self.logger.error("❌ Inicializace selhala")
            self.notifier.notify_error("Inicializace News analyzérů selhala")
            return False
        
        self.running = True
        
        # Info o scheduled časech
        next_time = self.next_analysis_time()
        self.logger.info(f"⏰ Scheduled analýzy: {', '.join(self.config['scheduled_times'])}")
        self.logger.info(f"⏰ Další analýza: {next_time.strftime('%d.%m.%Y %H:%M')}")
        
        self.notifier.notify_system_status("started", f"Monitoring crypto zpráv 2x denně: {', '.join(self.config['scheduled_times'])}")
        
        # První analýza pouze pokud je čas
        self.run_analysis_cycle()
        
        # Hlavní smyčka
        while self.running:
            try:
                time.sleep(60)  # Kontrola každou minutu
                
                # Analýza podle schedule
                self.run_analysis_cycle()
                
                # Aktualizace info o další analýze
                if datetime.now().minute == 0:  # Každou hodinu
                    next_time = self.next_analysis_time()
                    self.logger.info(f"⏰ Další analýza: {next_time.strftime('%d.%m.%Y %H:%M')}")
                
            except KeyboardInterrupt:
                self.logger.info("⏹️ Přerušení uživatelem")
                break
            except Exception as e:
                self.logger.error(f"❌ Chyba v hlavní smyčce: {e}")
                time.sleep(30)  # Krátká pauza při chybě
        
        self.stop()
        return True
    
    def stop(self):
        """Zastavení integrace"""
        self.logger.info("⏹️ Zastavuji News-Perun integraci...")
        self.running = False
        
        # Notifikace o zastavení
        self.notifier.notify_system_status("stopped")
        
        # Uložení finální cache
        if self.translator:
            self.translator.save_cache()

def main():
    """Hlavní funkce pro standalone spuštění"""
    integration = NewsPerunIntegration()
    
    # Signal handlers
    def signal_handler(sig, frame):
        print("\n⏹️ Zastavuji News-Perun integraci...")
        integration.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Spuštění
    integration.start()

if __name__ == "__main__":
    main()