#!/usr/bin/env python3
"""
YouTube-Perun Trading Integration (Scheduled)
Napojení YouTube sentiment analýzy na Perun trading systém
Autor: Claude + LakyLuk  
Datum: 24.6.2025 - Scheduled verze (11:00 a 20:00)
"""

import json
import time
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import signal
import sys

# Import stávajících Perun modulů
try:
    from youtube_analyzer import YouTubeAnalyzer, CZECH_CRYPTO_CHANNELS
    # Import z hlavního Perun systému
    import perun_tradingview_multi as perun_main
except ImportError as e:
    print(f"❌ Chyba importu: {e}")
    sys.exit(1)

class YouTubePerunIntegration:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Konfigurace - SCHEDULED MODE
        self.config = {
            'scheduled_times': ['11:00', '20:00'],  # Analýza 2x denně
            'sentiment_threshold': 0.4,  # Práh pro generování signálů
            'confidence_threshold': 0.6,  # Minimální důvěryhodnost
            'max_youtube_influence': 0.3,  # Max vliv YouTube na rozhodování (30%)
            'enabled_cryptos': ['BTCUSD', 'ETHUSD', 'XRPUSD', 'SOLUSD', 'ADAUSD', 'ARBUSD', 'AVAXUSD', 'DOTUSD']
        }
        
        # YouTube analyzer
        self.youtube_analyzer = None
        self.last_youtube_analysis = None
        self.last_analysis_time = None
        
        # Signály pro Perun
        self.youtube_signals = {}
        
        # Status
        self.running = False
        
        self.logger.info("🚀 YouTubePerunIntegration (Scheduled) inicializován")
    
    def setup_logging(self):
        """Nastavení logování"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('youtube_perun_scheduled.log'),
                logging.StreamHandler()
            ]
        )
    
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
                
                self.logger.info(f"⏰ Čas pro analýzu: {scheduled_time} (aktuální: {current_time})")
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
    
    def initialize_youtube_analyzer(self):
        """Inicializace YouTube analyzéru"""
        try:
            self.logger.info("🔧 Inicializuji YouTube analyzér...")
            
            # YouTube API klíč z prostředí nebo souboru
            youtube_api_key = os.getenv('YOUTUBE_API_KEY', 'AIzaSyBl_jZfiEu_t3VzPEVKhJGKqicVz9fJ4Hc')
            
            self.youtube_analyzer = YouTubeAnalyzer(
                api_key=youtube_api_key,
                channels=CZECH_CRYPTO_CHANNELS
            )
            
            self.logger.info("✅ YouTube analyzér inicializován")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Chyba při inicializaci YouTube analyzéru: {e}")
            return False
    
    def perform_youtube_analysis(self):
        """Hlavní YouTube analýza"""
        try:
            self.logger.info("📺 Spouštím YouTube sentiment analýzu...")
            
            # Analýza všech kanálů
            analysis_data = self.youtube_analyzer.analyze_all_channels()
            
            if not analysis_data or not analysis_data.get('channels'):
                self.logger.warning("⚠️ Žádná YouTube data nenalezena")
                return None
            
            # Uložení výsledků
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'youtube_analysis_{timestamp}.json'
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.last_youtube_analysis = analysis_data
            self.last_analysis_time = datetime.now()
            
            self.logger.info(f"✅ YouTube analýza dokončena: {filename}")
            return analysis_data
            
        except Exception as e:
            self.logger.error(f"❌ Chyba při YouTube analýze: {e}")
            return None
    
    def generate_youtube_signals(self, analysis_data):
        """Generování trading signálů z YouTube analýzy"""
        if not analysis_data:
            return {}
        
        signals = {}
        
        try:
            # Zpracování dat pro každou kryptoměnu
            for crypto in self.config['enabled_cryptos']:
                crypto_base = crypto.replace('USD', '')  # BTC, ETH, XRP...
                
                # Najít relevantní sentimenty
                relevant_sentiments = []
                
                for channel_data in analysis_data.get('channels', {}).values():
                    if 'sentiment_summary' in channel_data:
                        sentiment_summary = channel_data['sentiment_summary']
                        
                        # Hledat zmínky o této kryptoměně
                        for coin_sentiment in sentiment_summary.get('crypto_sentiments', []):
                            if coin_sentiment.get('coin', '').upper() == crypto_base:
                                relevant_sentiments.append(coin_sentiment)
                
                # Výpočet průměrného sentimentu
                if relevant_sentiments:
                    avg_sentiment = sum(s.get('sentiment', 0) for s in relevant_sentiments) / len(relevant_sentiments)
                    avg_confidence = sum(s.get('confidence', 0) for s in relevant_sentiments) / len(relevant_sentiments)
                    
                    # Generování signálu
                    signal_strength = 0.0
                    signal_type = "NEUTRAL"
                    
                    if (abs(avg_sentiment) > self.config['sentiment_threshold'] and 
                        avg_confidence > self.config['confidence_threshold']):
                        
                        if avg_sentiment > 0:
                            signal_type = "BUY"
                            signal_strength = min(avg_sentiment * avg_confidence, 1.0)
                        else:
                            signal_type = "SELL"
                            signal_strength = min(abs(avg_sentiment) * avg_confidence, 1.0)
                    
                    signals[crypto] = {
                        'signal': signal_type,
                        'strength': signal_strength,
                        'sentiment': avg_sentiment,
                        'confidence': avg_confidence,
                        'mentions': len(relevant_sentiments),
                        'source': 'youtube_scheduled',
                        'timestamp': datetime.now().isoformat()
                    }
            
            self.youtube_signals = signals
            self.logger.info(f"📈 Vygenerováno {len(signals)} YouTube signálů")
            
            return signals
            
        except Exception as e:
            self.logger.error(f"❌ Chyba při generování signálů: {e}")
            return {}
    
    def get_youtube_sentiment_for_symbol(self, symbol):
        """Získání YouTube sentimentu pro konkrétní symbol (používá Perun)"""
        if symbol not in self.youtube_signals:
            return None
        
        signal_data = self.youtube_signals[symbol]
        
        # Kontrola stáří dat (max 24 hodin pro scheduled mode)
        try:
            signal_time = datetime.fromisoformat(signal_data['timestamp'])
            if datetime.now() - signal_time > timedelta(hours=24):
                self.logger.warning(f"⚠️ Starý YouTube signál pro {symbol}")
                return None
        except:
            pass
        
        return {
            'sentiment': signal_data['sentiment'],
            'confidence': signal_data['confidence'],
            'strength': signal_data['strength'],
            'signal': signal_data['signal'],
            'source': 'youtube_scheduled',
            'mentions': signal_data.get('mentions', 0)
        }
    
    def enhance_trading_signal(self, tv_signal, symbol):
        """Vylepšení TradingView signálu pomocí YouTube sentimentu"""
        youtube_sentiment = self.get_youtube_sentiment_for_symbol(symbol)
        
        if not youtube_sentiment:
            return tv_signal, 0.0  # Žádný YouTube vliv
        
        try:
            # Základní logika stejná jako v původním systému
            youtube_influence = min(
                youtube_sentiment['strength'] * self.config['max_youtube_influence'],
                self.config['max_youtube_influence']
            )
            
            # Kombination signálů
            if youtube_sentiment['signal'] == 'BUY' and tv_signal > 0:
                enhanced_signal = tv_signal + (tv_signal * youtube_influence)
                enhanced_signal = min(enhanced_signal, 1.0)
            elif youtube_sentiment['signal'] == 'SELL' and tv_signal < 0:
                enhanced_signal = tv_signal + (tv_signal * youtube_influence)
                enhanced_signal = max(enhanced_signal, -1.0)
            else:
                # Konfliktní signály - minimální vliv
                enhanced_signal = tv_signal + (youtube_sentiment['sentiment'] * youtube_influence * 0.3)
                enhanced_signal = max(-1.0, min(1.0, enhanced_signal))
            
            self.logger.info(
                f"📺 YouTube enhancement {symbol}: "
                f"TV={tv_signal:.3f} → Enhanced={enhanced_signal:.3f} "
                f"(YouTube: {youtube_sentiment['signal']}, vliv: {youtube_influence:.3f})"
            )
            
            return enhanced_signal, youtube_influence
            
        except Exception as e:
            self.logger.error(f"❌ Chyba při enhancement: {e}")
            return tv_signal, 0.0
    
    def run_analysis_cycle(self):
        """Jeden cyklus YouTube analýzy (jen pokud je čas)"""
        if not self.should_run_analysis():
            return
        
        try:
            # Provedení analýzy
            analysis_data = self.perform_youtube_analysis()
            
            if analysis_data:
                # Generování signálů
                self.generate_youtube_signals(analysis_data)
                
                self.logger.info("✅ YouTube analýza cyklus dokončen")
            else:
                self.logger.warning("⚠️ YouTube analýza selhala")
                
        except Exception as e:
            self.logger.error(f"❌ Chyba v YouTube cyklu: {e}")
    
    def start(self):
        """Spuštění YouTube-Perun integrace"""
        self.logger.info("🚀 Spouštím YouTube-Perun integraci (Scheduled Mode)...")
        
        if not self.initialize_youtube_analyzer():
            self.logger.error("❌ Inicializace selhala")
            return False
        
        self.running = True
        
        # Info o scheduled časech
        next_time = self.next_analysis_time()
        self.logger.info(f"⏰ Scheduled analýzy: {', '.join(self.config['scheduled_times'])}")
        self.logger.info(f"⏰ Další analýza: {next_time.strftime('%d.%m.%Y %H:%M')}")
        
        # Hlavní smyčka
        while self.running:
            try:
                # Kontrola každou minutu
                time.sleep(60)
                
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
        self.logger.info("⏹️ Zastavuji YouTube-Perun integraci...")
        self.running = False

def main():
    """Hlavní funkce pro standalone spuštění"""
    integration = YouTubePerunIntegration()
    
    # Signal handlers
    def signal_handler(sig, frame):
        print("\\n⏹️ Zastavuji YouTube-Perun integraci...")
        integration.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Spuštění
    integration.start()

if __name__ == "__main__":
    main()