def log_trade(symbol, action, price, quantity, signal_source, additional_info=None):
    """Zaznamená obchod do logovacího souboru."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Základní informace o obchodu
    log_entry = f"[{timestamp}] {action} {symbol}: {quantity} za cenu {price:.2f} USD (signál: {signal_source})"
    
    # Přidání dalších informací, pokud jsou k dispozici
    if additional_info:
        for key, value in additional_info.items():
            if isinstance(value, float):
                log_entry += f"\n[{timestamp}]   - {key}: {value:.2f}"
            else:
                log_entry += f"\n[{timestamp}]   - {key}: {value}"
    
    # Zápis do logu
    with open("trading_log.txt", "a") as log_file:
        log_file.write(log_entry + "\n")
    
    # Výpis do konzole
    print(log_entry)
    
    return log_entry
