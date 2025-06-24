#!/usr/bin/env python3
"""
News Desktop Notifications
Autor: LakyLuk | Datum: 24.6.2025
Desktop notifikace pro News-Perun systém
"""

import subprocess
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

class NewsNotifications:
    def __init__(self):
        self.app_name = "News-Perun"
        self.icon_path = "/home/laky/crypto-news-analyzer/icon.png"
        
        # Check if notify-send is available
        self.notifications_available = self._check_notifications()
        
    def _check_notifications(self) -> bool:
        """Kontrola dostupnosti notify-send"""
        try:
            subprocess.run(['which', 'notify-send'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ notify-send není dostupný")
            return False
    
    def send_notification(self, title: str, message: str, 
                         urgency: str = "normal", timeout: int = 5000):
        """Odeslání desktop notifikace"""
        if not self.notifications_available:
            # Fallback na konzolový výstup
            print(f"🔔 {title}: {message}")
            return
        
        try:
            cmd = [
                'notify-send',
                '--app-name', self.app_name,
                '--urgency', urgency,
                '--expire-time', str(timeout),
                '--icon', self.icon_path,
                title,
                message
            ]
            
            subprocess.run(cmd, capture_output=True)
            
        except Exception as e:
            print(f"❌ Chyba při odeslání notifikace: {e}")
    
    def notify_analysis_started(self):
        """Notifikace o spuštění analýzy"""
        self.send_notification(
            "📰 News Analysis",
            "Spouštím analýzu crypto zpráv...",
            urgency="low",
            timeout=3000
        )
    
    def notify_analysis_completed(self, summary: Dict[str, Any]):
        """Notifikace o dokončení analýzy"""
        if not summary:
            return
        
        avg_sentiment = summary.get('average_sentiment', 0)
        total_articles = summary.get('total_articles', 0)
        market_mood = summary.get('market_mood', 'N/A')
        recommendation = summary.get('recommendation', '')
        
        # Emoji podle sentimentu
        if avg_sentiment > 0.2:
            emoji = "🟢"
            urgency = "normal"
        elif avg_sentiment < -0.2:
            emoji = "🔴"
            urgency = "critical"
        else:
            emoji = "🟡"
            urgency = "low"
        
        title = f"{emoji} News Analysis Dokončena"
        message = f"Sentiment: {avg_sentiment:.3f} ({market_mood})\n"
        message += f"Analyzováno: {total_articles} článků\n"
        if recommendation:
            message += f"💡 {recommendation[:50]}..."
        
        self.send_notification(title, message, urgency=urgency, timeout=8000)
    
    def notify_strong_signal(self, symbol: str, signal_data: Dict[str, Any]):
        """Notifikace o silném trading signálu"""
        signal = signal_data.get('signal', 'NEUTRAL')
        sentiment = signal_data.get('sentiment', 0)
        confidence = signal_data.get('confidence', 0)
        article_count = signal_data.get('article_count', 0)
        
        # Pouze pro silné signály
        if confidence < 0.7 or abs(sentiment) < 0.5:
            return
        
        if signal == 'BUY':
            emoji = "🚀"
            urgency = "critical"
        elif signal == 'SELL':
            emoji = "⚠️"
            urgency = "critical"
        else:
            return  # Nenotifikovat neutral
        
        title = f"{emoji} Silný News Signál - {symbol}"
        message = f"Signál: {signal}\n"
        message += f"Sentiment: {sentiment:.3f}\n"
        message += f"Jistota: {confidence:.2f}\n"
        message += f"Založeno na {article_count} článcích"
        
        self.send_notification(title, message, urgency=urgency, timeout=10000)
    
    def notify_multiple_signals(self, signals: Dict[str, Dict[str, Any]]):
        """Notifikace o více signálech najednou"""
        strong_signals = []
        
        for symbol, signal_data in signals.items():
            confidence = signal_data.get('confidence', 0)
            sentiment = signal_data.get('sentiment', 0)
            signal = signal_data.get('signal', 'NEUTRAL')
            
            if confidence > 0.6 and abs(sentiment) > 0.3 and signal != 'NEUTRAL':
                strong_signals.append((symbol, signal, sentiment))
        
        if not strong_signals:
            return
        
        if len(strong_signals) == 1:
            # Jednotlivý signál
            symbol, signal, sentiment = strong_signals[0]
            self.notify_strong_signal(symbol, signals[symbol])
        else:
            # Více signálů
            buy_count = sum(1 for _, signal, _ in strong_signals if signal == 'BUY')
            sell_count = sum(1 for _, signal, _ in strong_signals if signal == 'SELL')
            
            title = "📊 Více News Signálů"
            message = f"🟢 BUY: {buy_count} signálů\n"
            message += f"🔴 SELL: {sell_count} signálů\n"
            message += f"Coins: {', '.join([s[0] for s in strong_signals[:3]])}"
            if len(strong_signals) > 3:
                message += f" +{len(strong_signals)-3} dalších"
            
            urgency = "critical" if (buy_count > 2 or sell_count > 2) else "normal"
            
            self.send_notification(title, message, urgency=urgency, timeout=12000)
    
    def notify_error(self, error_message: str):
        """Notifikace o chybě"""
        self.send_notification(
            "❌ News-Perun Chyba",
            f"Chyba v systému:\n{error_message[:100]}...",
            urgency="critical",
            timeout=15000
        )
    
    def notify_system_status(self, status: str, details: str = ""):
        """Notifikace o stavu systému"""
        if status == "started":
            emoji = "🚀"
            title = "News-Perun Spuštěn"
            message = "Monitoring crypto zpráv aktivní"
            urgency = "low"
        elif status == "stopped":
            emoji = "⏹️"
            title = "News-Perun Zastaven"
            message = "Monitoring crypto zpráv ukončen"
            urgency = "low"
        else:
            emoji = "ℹ️"
            title = f"News-Perun {status.title()}"
            message = details
            urgency = "low"
        
        full_message = message
        if details:
            full_message += f"\n{details}"
        
        self.send_notification(f"{emoji} {title}", full_message, 
                             urgency=urgency, timeout=5000)

# Test funkce
def test_notifications():
    """Test notifikací"""
    print("🧪 Testuje desktop notifikace...")
    
    notifier = NewsNotifications()
    
    # Test základní notifikace
    notifier.send_notification(
        "📰 Test Notifikace",
        "Toto je test News-Perun notifikací",
        urgency="normal"
    )
    
    print("✅ Test notifikace odeslána")
    
    # Test analysis completed
    test_summary = {
        'average_sentiment': 0.65,
        'total_articles': 15,
        'market_mood': '🟢 Velmi Bullish',
        'recommendation': '🚀 Silné nakupování - Altseason možná blízko'
    }
    
    notifier.notify_analysis_completed(test_summary)
    print("✅ Test analysis completed notifikace")
    
    # Test strong signal
    test_signal = {
        'signal': 'BUY',
        'sentiment': 0.8,
        'confidence': 0.9,
        'article_count': 5
    }
    
    notifier.notify_strong_signal('BTCUSD', test_signal)
    print("✅ Test strong signal notifikace")

if __name__ == "__main__":
    test_notifications()