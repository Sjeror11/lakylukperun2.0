#!/usr/bin/env python3
"""
Klient pro TermiSignal s podporou komunikace přes internet
"""

import socket
import threading
import json
import time
import os
import sys
import getpass
import signal

# Barvy pro terminál
class Colors:
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

# Konfigurace klienta
SERVER_HOST = 'sjeror11.direct.quickconnect.to'  # Adresa serveru - změňte na adresu vašeho Synology
SERVER_PORT = 5000         # Port serveru
CONFIG_FILE = os.path.expanduser("~/.termisignal/config.json")

# Globální proměnné
socket_lock = threading.Lock()
client_socket = None
online_users = []
current_user = None
running = True
messages = []

def clear_screen():
    """Vyčistí obrazovku"""
    os.system('clear' if os.name == 'posix' else 'cls')

def save_config(config):
    """Uloží konfiguraci do souboru"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def load_config():
    """Načte konfiguraci ze souboru"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_username": "", "server": SERVER_HOST}

def connect_to_server():
    """Připojí se k serveru"""
    global client_socket, SERVER_HOST
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        return True
    except Exception as e:
        print(f"{Colors.RED}Chyba při připojení k serveru: {e}{Colors.RESET}")
        return False

def send_message(message_data):
    """Odešle zprávu na server"""
    global client_socket
    
    try:
        with socket_lock:
            client_socket.sendall(json.dumps(message_data).encode() + b'\n')
        return True
    except Exception as e:
        print(f"{Colors.RED}Chyba při odesílání zprávy: {e}{Colors.RESET}")
        return False

def receive_messages():
    """Přijímá zprávy ze serveru"""
    global client_socket, online_users, running
    
    buffer = b''
    
    while running:
        try:
            # Přijmutí dat ze serveru
            chunk = client_socket.recv(1024)
            if not chunk:
                print(f"{Colors.RED}Spojení se serverem bylo přerušeno{Colors.RESET}")
                running = False
                break
            
            buffer += chunk
            
            # Zpracování kompletních zpráv
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                message = json.loads(line.decode())
                process_message(message)
        
        except Exception as e:
            print(f"{Colors.RED}Chyba při příjmu zpráv: {e}{Colors.RESET}")
            running = False
            break

def process_message(message):
    """Zpracuje přijatou zprávu"""
    global online_users, messages
    
    message_type = message.get("type", "")
    
    if message_type == "online_users":
        # Aktualizace seznamu online uživatelů
        online_users = message["users"]
    
    elif message_type == "message":
        # Přidání zprávy do seznamu
        messages.append(message)
        
        # Zobrazení notifikace
        sender = message["sender"]
        content = message["content"]
        print(f"\n{Colors.GREEN}Nová zpráva od {sender}: {content}{Colors.RESET}")
        print("> ", end="", flush=True)
    
    elif message_type == "error":
        # Zobrazení chybové zprávy
        print(f"\n{Colors.RED}Chyba: {message['message']}{Colors.RESET}")
        print("> ", end="", flush=True)

def register_user():
    """Registrace nového uživatele"""
    clear_screen()
    print(f"{Colors.GREEN}{Colors.BOLD}TermiSignal - Registrace{Colors.RESET}")
    print()
    
    username = input("Uživatelské jméno: ")
    password = getpass.getpass("Heslo: ")
    password_confirm = getpass.getpass("Heslo znovu: ")
    
    if password != password_confirm:
        print(f"{Colors.RED}Hesla se neshodují{Colors.RESET}")
        time.sleep(2)
        return False, None
    
    # Odeslání registračního požadavku
    register_data = {
        "type": "register",
        "username": username,
        "password": password
    }
    
    if not send_message(register_data):
        return False, None
    
    # Čekání na odpověď
    buffer = b''
    while b'\n' not in buffer:
        chunk = client_socket.recv(1024)
        if not chunk:
            print(f"{Colors.RED}Spojení se serverem bylo přerušeno{Colors.RESET}")
            return False, None
        buffer += chunk
    
    line, _ = buffer.split(b'\n', 1)
    response = json.loads(line.decode())
    
    if response["type"] == "register_response":
        if response["success"]:
            print(f"{Colors.GREEN}{response['message']}{Colors.RESET}")
            time.sleep(1)
            return True, username
        else:
            print(f"{Colors.RED}{response['message']}{Colors.RESET}")
            time.sleep(2)
            return False, None
    
    return False, None

def login_user():
    """Přihlášení uživatele"""
    global current_user
    
    clear_screen()
    print(f"{Colors.GREEN}{Colors.BOLD}TermiSignal - Přihlášení{Colors.RESET}")
    print()
    
    # Načtení posledního uživatelského jména
    config = load_config()
    last_username = config.get("last_username", "")
    
    username = input(f"Uživatelské jméno [{last_username}]: ") or last_username
    password = getpass.getpass("Heslo: ")
    
    # Odeslání přihlašovacího požadavku
    login_data = {
        "type": "login",
        "username": username,
        "password": password
    }
    
    if not send_message(login_data):
        return False
    
    # Čekání na odpověď
    buffer = b''
    while b'\n' not in buffer:
        chunk = client_socket.recv(1024)
        if not chunk:
            print(f"{Colors.RED}Spojení se serverem bylo přerušeno{Colors.RESET}")
            return False
        buffer += chunk
    
    line, _ = buffer.split(b'\n', 1)
    response = json.loads(line.decode())
    
    if response["type"] == "login_response":
        if response["success"]:
            print(f"{Colors.GREEN}{response['message']}{Colors.RESET}")
            current_user = username
            
            # Uložení uživatelského jména
            config["last_username"] = username
            save_config(config)
            
            time.sleep(1)
            return True
        else:
            print(f"{Colors.RED}{response['message']}{Colors.RESET}")
            time.sleep(2)
            return False
    
    return False

def logout():
    """Odhlášení uživatele"""
    global current_user, running
    
    if current_user:
        logout_data = {
            "type": "logout"
        }
        send_message(logout_data)
        current_user = None
    
    running = False

def chat_screen():
    """Obrazovka chatu"""
    global running, messages, online_users
    
    # Spuštění vlákna pro příjem zpráv
    receive_thread = threading.Thread(target=receive_messages)
    receive_thread.daemon = True
    receive_thread.start()
    
    # Vyžádání seznamu online uživatelů
    send_message({"type": "get_users"})
    
    while running:
        clear_screen()
        print(f"{Colors.GREEN}{Colors.BOLD}TermiSignal - Chat{Colors.RESET}")
        print(f"{Colors.CYAN}Přihlášen jako: {current_user}{Colors.RESET}")
        print()
        
        # Zobrazení seznamu online uživatelů
        print(f"{Colors.YELLOW}Online uživatelé:{Colors.RESET}")
        for user in online_users:
            if user != current_user:
                print(f"  {user}")
        
        print()
        
        # Zobrazení posledních zpráv
        print(f"{Colors.YELLOW}Poslední zprávy:{Colors.RESET}")
        displayed_messages = messages[-10:] if len(messages) > 10 else messages
        for msg in displayed_messages:
            if msg["type"] == "message":
                sender = msg["sender"]
                recipient = msg["recipient"]
                content = msg["content"]
                
                if sender == current_user:
                    print(f"{Colors.BLUE}Vy -> {recipient}: {content}{Colors.RESET}")
                else:
                    print(f"{Colors.GREEN}{sender} -> Vy: {content}{Colors.RESET}")
        
        print()
        print(f"{Colors.YELLOW}Příkazy:{Colors.RESET}")
        print("  /msg <uživatel> <zpráva> - Poslat zprávu")
        print("  /users - Aktualizovat seznam uživatelů")
        print("  /exit - Odhlásit se")
        print()
        
        command = input("> ")
        
        if command.startswith("/msg "):
            # Odeslání zprávy
            try:
                _, recipient, *content_parts = command.split(" ")
                content = " ".join(content_parts)
                
                if not content:
                    print(f"{Colors.RED}Prázdná zpráva{Colors.RESET}")
                    time.sleep(1)
                    continue
                
                message_data = {
                    "type": "message",
                    "recipient": recipient,
                    "content": content
                }
                
                if send_message(message_data):
                    # Přidání zprávy do seznamu
                    messages.append({
                        "type": "message",
                        "sender": current_user,
                        "recipient": recipient,
                        "content": content,
                        "timestamp": time.time()
                    })
            except ValueError:
                print(f"{Colors.RED}Neplatný formát příkazu{Colors.RESET}")
                time.sleep(1)
        
        elif command == "/users":
            # Aktualizace seznamu uživatelů
            send_message({"type": "get_users"})
        
        elif command == "/exit":
            # Odhlášení
            logout()
            break

def main():
    """Hlavní funkce aplikace"""
    global SERVER_HOST, running
    
    # Načtení konfigurace
    config = load_config()
    SERVER_HOST = config.get("server", SERVER_HOST)
    
    # Obsluha signálů pro korektní ukončení
    def handle_signal(sig, frame):
        global running
        print("\nUkončuji aplikaci...")
        logout()
        running = False
        if client_socket:
            client_socket.close()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Hlavní smyčka aplikace
    while running:
        clear_screen()
        print(f"{Colors.GREEN}{Colors.BOLD}TermiSignal - Terminálová šifrovaná komunikační aplikace{Colors.RESET}")
        print(f"{Colors.CYAN}Verze: 0.2.0{Colors.RESET}")
        print()
        
        # Připojení k serveru
        if not connect_to_server():
            print(f"{Colors.YELLOW}Zadejte adresu serveru:{Colors.RESET}")
            SERVER_HOST = input(f"Server [{SERVER_HOST}]: ") or SERVER_HOST
            config["server"] = SERVER_HOST
            save_config(config)
            continue
        
        print(f"{Colors.GREEN}Připojeno k serveru {SERVER_HOST}:{SERVER_PORT}{Colors.RESET}")
        print()
        
        print(f"{Colors.YELLOW}1. Přihlásit se{Colors.RESET}")
        print(f"{Colors.YELLOW}2. Registrovat se{Colors.RESET}")
        print(f"{Colors.YELLOW}3. Ukončit{Colors.RESET}")
        print()
        
        choice = input("Vyberte možnost (1-3): ")
        
        if choice == "1":
            # Přihlášení
            if login_user():
                chat_screen()
        
        elif choice == "2":
            # Registrace
            success, username = register_user()
            if success and username:
                current_user = username
                config["last_username"] = username
                save_config(config)
                chat_screen()
        
        elif choice == "3":
            # Ukončení
            running = False
            break
        
        else:
            print(f"{Colors.RED}Neplatná volba!{Colors.RESET}")
            time.sleep(1)
    
    # Ukončení spojení
    if client_socket:
        client_socket.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}Děkujeme za použití TermiSignal!{Colors.RESET}")
        sys.exit(0)
