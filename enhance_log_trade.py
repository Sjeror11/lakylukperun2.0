#!/usr/bin/env python3

def enhance_log_trade():
    """
    Vylepšená funkce log_trade, která zobrazuje více informací o obchodech.
    """
    enhanced_code = '''
def log_trade(symbol, action, price, quantity, signal_source, additional_info=None):
    """Zaznamená obchod do logovacího souboru s rozšířenými informacemi."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Základní informace o obchodu
    log_entry = f"[{timestamp}] {action} {symbol}: {quantity} za cenu {price:.2f} USD (signál: {signal_source})"
    
    # Přidání dalších informací, pokud jsou k dispozici
    if additional_info:
        for key, value in additional_info.items():
            if isinstance(value, float):
                log_entry += f"\\n[{timestamp}]   - {key}: {value:.2f}"
            else:
                log_entry += f"\\n[{timestamp}]   - {key}: {value}"
    
    # Získání aktuálních pozic pro kontext
    positions = get_positions()
    position_info = "Žádné otevřené pozice"
    
    for pos in positions:
        pos_symbol = pos.get("symbol")
        pos_qty = pos.get("qty")
        pos_price = pos.get("avg_entry_price")
        current_price = pos.get("current_price")
        
        if current_price and pos_price:
            profit_loss = ((float(current_price) - float(pos_price)) / float(pos_price)) * 100
            log_entry += f"\\n[{timestamp}]   - Aktuální pozice: {pos_symbol} {pos_qty} ks, vstup: {pos_price} USD, aktuálně: {current_price} USD, P/L: {profit_loss:.2f}%"
    
    # Zápis do logu
    with open("trading_log.txt", "a") as log_file:
        log_file.write(log_entry + "\\n")
    
    # Výpis do konzole
    print(log_entry)
    
    return log_entry
'''
    return enhanced_code

def enhance_execute_trade():
    """
    Vylepšená funkce execute_trade, která předává více informací do log_trade.
    """
    enhanced_code = '''
def execute_trade(symbol, action, signal_source, tv_recommendation=None, macd_signal=None, rsi_value=None):
    """Provede obchod na základě signálu."""
    try:
        # Kontrola, zda již nemáme otevřenou pozici pro daný symbol
        positions = get_positions()
        has_position = False
        
        for position in positions:
            if position.get("symbol") == symbol:
                has_position = True
                position_side = position.get("side")
                
                # Pokud máme pozici ve stejném směru jako signál, přeskočíme
                if (position_side == "long" and action == "BUY") or (position_side == "short" and action == "SELL"):
                    log_message = f"Přeskočeno: Již máme otevřenou pozici {position_side.upper()} pro {symbol}, přeskakuji"
                    print(log_message)
                    with open("trading_log.txt", "a") as log_file:
                        log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {log_message}\\n")
                    return None
                
                # Pokud máme pozici v opačném směru, uzavřeme ji
                if (position_side == "long" and action == "SELL") or (position_side == "short" and action == "BUY"):
                    close_position(symbol)
        
        # Získání aktuální ceny
        price = get_price_from_api(symbol)
        if not price:
            print(f"❌ Nelze získat cenu pro {symbol}, obchod nebude proveden")
            return None
        
        # Výpočet množství na základě velikosti pozice
        quantity = calculate_position_size(price, POSITION_SIZE)
        
        # Provedení obchodu
        if action == "BUY":
            response = place_market_order(symbol, quantity, "buy")
        else:  # SELL
            response = place_market_order(symbol, quantity, "sell")
        
        if response and response.get("id"):
            # Příprava dodatečných informací pro log
            additional_info = {
                "TradingView doporučuje": tv_recommendation if tv_recommendation else "N/A",
                "MACD signál": macd_signal if macd_signal else "N/A",
                "RSI hodnota": rsi_value if rsi_value else "N/A",
                "Objednávka ID": response.get("id")
            }
            
            # Zaznamenání obchodu do logu
            log_trade(symbol, action, price, quantity, signal_source, additional_info)
            return response
        else:
            print(f"❌ Chyba při provádění obchodu {action} pro {symbol}")
            return None
    except Exception as e:
        print(f"❌ Výjimka při provádění obchodu: {e}")
        return None
'''
    return enhanced_code

if __name__ == "__main__":
    print("Vylepšená funkce log_trade:")
    print(enhance_log_trade())
    print("\nVylepšená funkce execute_trade:")
    print(enhance_execute_trade())
