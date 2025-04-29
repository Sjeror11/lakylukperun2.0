#!/usr/bin/env python3
import paramiko
import os
import time

# Konfigurace
host = '192.168.1.139'
username = 'sjeror'
password = 'heslo'  # Toto bude potřeba zadat při spuštění

# Obsah souborů
ts_server_content = '''#!/usr/bin/env python3
"""
Jednoduchý server pro TermiSignal
"""

import socket
import threading
import json
import time
import sys
import signal
import os

# Konfigurace serveru
HOST = '0.0.0.0'  # Naslouchá na všech rozhraních
PORT = 5000       # Port pro komunikaci
MAX_CLIENTS = 100 # Maximální počet klientů
DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# Globální proměnné
clients = {}      # Slovník připojených klientů {username: (conn, addr)}
users_db = {}     # Jednoduchá databáze uživatelů {username: password}
messages = {}     # Zprávy pro offline uživatele {username: [messages]}
lock = threading.Lock()  # Zámek pro přístup ke sdíleným proměnným

def save_users_db():
    """Uloží databázi uživatelů do souboru"""
    try:
        with open(os.path.join(DATA_DIR, 'users.json'), 'w') as f:
            json.dump(users_db, f)
        print("Databáze uživatelů uložena")
    except Exception as e:
        print(f"Chyba při ukládání databáze: {e}")

def load_users_db():
    """Načte databázi uživatelů ze souboru"""
    global users_db
    try:
        with open(os.path.join(DATA_DIR, 'users.json'), 'r') as f:
            users_db = json.load(f)
        print(f"Databáze uživatelů načtena, {len(users_db)} uživatelů")
    except FileNotFoundError:
        print("Databáze uživatelů neexistuje, vytvářím novou")
        users_db = {}
    except Exception as e:
        print(f"Chyba při načítání databáze: {e}")
        users_db = {}

def register_user(username, password):
    """Registruje nového uživatele"""
    with lock:
        if username in users_db:
            return False, "Uživatel již existuje"
        
        users_db[username] = password
        save_users_db()
        return True, "Uživatel byl úspěšně zaregistrován"

def authenticate_user(username, password):
    """Ověří uživatele"""
    if username not in users_db:
        return False, "Uživatel neexistuje"
    
    if users_db[username] != password:
        return False, "Nesprávné heslo"
    
    return True, "Přihlášení úspěšné"

def broadcast_online_users():
    """Odešle seznam online uživatelů všem připojeným klientům"""
    online_users = list(clients.keys())
    message = {
        "type": "online_users",
        "users": online_users
    }
    
    with lock:
        for username, (conn, _) in clients.items():
            try:
                conn.sendall(json.dumps(message).encode() + b'\\n')
            except:
                # Pokud se nepodaří odeslat, klient je pravděpodobně odpojený
                pass

def handle_client(conn, addr):
    """Obsluha připojeného klienta"""
    print(f"Nové připojení z {addr}")
    
    username = None
    
    try:
        while True:
            # Přijmutí dat od klienta
            data = b''
            while not data.endswith(b'\\n'):
                chunk = conn.recv(1024)
                if not chunk:
                    raise ConnectionError("Klient se odpojil")
                data += chunk
            
            # Zpracování přijatých dat
            message = json.loads(data.decode().strip())
            message_type = message.get("type", "")
            
            if message_type == "register":
                # Registrace nového uživatele
                success, result = register_user(message["username"], message["password"])
                response = {
                    "type": "register_response",
                    "success": success,
                    "message": result
                }
                conn.sendall(json.dumps(response).encode() + b'\\n')
            
            elif message_type == "login":
                # Přihlášení uživatele
                success, result = authenticate_user(message["username"], message["password"])
                
                if success:
                    username = message["username"]
                    with lock:
                        # Pokud je uživatel již přihlášen, odpojíme předchozí připojení
                        if username in clients:
                            old_conn, _ = clients[username]
                            try:
                                old_conn.sendall(json.dumps({
                                    "type": "error",
                                    "message": "Přihlášení z jiného zařízení"
                                }).encode() + b'\\n')
                                old_conn.close()
                            except:
                                pass
                        
                        # Uložení nového připojení
                        clients[username] = (conn, addr)
                    
                    # Odeslání odpovědi
                    response = {
                        "type": "login_response",
                        "success": True,
                        "message": "Přihlášení úspěšné"
                    }
                    conn.sendall(json.dumps(response).encode() + b'\\n')
                    
                    # Odeslání offline zpráv
                    if username in messages and messages[username]:
                        for msg in messages[username]:
                            conn.sendall(json.dumps(msg).encode() + b'\\n')
                        messages[username] = []
                    
                    # Aktualizace seznamu online uživatelů
                    broadcast_online_users()
                else:
                    response = {
                        "type": "login_response",
                        "success": False,
                        "message": result
                    }
                    conn.sendall(json.dumps(response).encode() + b'\\n')
            
            elif message_type == "message" and username:
                # Přeposlání zprávy příjemci
                recipient = message["recipient"]
                
                # Přidání informací o odesílateli
                message["sender"] = username
                message["timestamp"] = time.time()
                
                with lock:
                    if recipient in clients:
                        # Příjemce je online, pošleme zprávu
                        recipient_conn, _ = clients[recipient]
                        try:
                            recipient_conn.sendall(json.dumps(message).encode() + b'\\n')
                        except:
                            # Pokud se nepodaří odeslat, uložíme zprávu pro pozdější doručení
                            if recipient not in messages:
                                messages[recipient] = []
                            messages[recipient].append(message)
                    else:
                        # Příjemce je offline, uložíme zprávu pro pozdější doručení
                        if recipient not in messages:
                            messages[recipient] = []
                        messages[recipient].append(message)
                
                # Potvrzení odeslání zprávy
                response = {
                    "type": "message_sent",
                    "recipient": recipient,
                    "timestamp": message["timestamp"]
                }
                conn.sendall(json.dumps(response).encode() + b'\\n')
            
            elif message_type == "get_users" and username:
                # Odeslání seznamu online uživatelů
                online_users = list(clients.keys())
                response = {
                    "type": "online_users",
                    "users": online_users
                }
                conn.sendall(json.dumps(response).encode() + b'\\n')
            
            elif message_type == "logout" and username:
                # Odhlášení uživatele
                with lock:
                    if username in clients:
                        del clients[username]
                
                # Aktualizace seznamu online uživatelů
                broadcast_online_users()
                
                # Ukončení spojení
                break
    
    except json.JSONDecodeError:
        print(f"Chyba při dekódování JSON od {addr}")
    except ConnectionError:
        print(f"Klient {addr} se odpojil")
    except Exception as e:
        print(f"Chyba při obsluze klienta {addr}: {e}")
    
    finally:
        # Odpojení klienta
        if username and username in clients:
            with lock:
                del clients[username]
            broadcast_online_users()
        
        conn.close()
        print(f"Spojení s {addr} ukončeno")

def start_server():
    """Spustí server"""
    # Načtení databáze uživatelů
    load_users_db()
    
    # Vytvoření socketu
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Navázání socketu na adresu a port
        server_socket.bind((HOST, PORT))
        server_socket.listen(MAX_CLIENTS)
        print(f"Server běží na {HOST}:{PORT}")
        
        # Obsluha signálů pro korektní ukončení
        def handle_signal(sig, frame):
            print("\\nUkončuji server...")
            server_socket.close()
            save_users_db()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        
        # Hlavní smyčka serveru
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
    
    except Exception as e:
        print(f"Chyba serveru: {e}")
    
    finally:
        server_socket.close()
        save_users_db()

if __name__ == "__main__":
    start_server()
'''

start_server_content = '''#!/bin/bash
cd /volume1/homes/sjeror/termisignal
nohup python3 ts_server.py > server.log 2>&1 &
echo "TermiSignal server spuštěn. Log je v souboru server.log"
'''

def main():
    # Získání hesla
    password = input("Zadejte heslo pro uživatele sjeror na Synology: ")
    
    # Vytvoření SSH klienta
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Připojení k serveru
        print(f"Připojuji se k {host}...")
        ssh.connect(host, username=username, password=password)
        
        # Vytvoření adresáře
        print("Vytvářím adresář...")
        ssh.exec_command('mkdir -p /volume1/homes/sjeror/termisignal')
        
        # Vytvoření souboru ts_server.py
        print("Vytvářím soubor ts_server.py...")
        stdin, stdout, stderr = ssh.exec_command('cat > /volume1/homes/sjeror/termisignal/ts_server.py')
        stdin.write(ts_server_content)
        stdin.flush()
        stdin.channel.shutdown_write()
        
        # Vytvoření souboru start_server.sh
        print("Vytvářím soubor start_server.sh...")
        stdin, stdout, stderr = ssh.exec_command('cat > /volume1/homes/sjeror/termisignal/start_server.sh')
        stdin.write(start_server_content)
        stdin.flush()
        stdin.channel.shutdown_write()
        
        # Nastavení oprávnění
        print("Nastavuji oprávnění...")
        ssh.exec_command('chmod +x /volume1/homes/sjeror/termisignal/ts_server.py /volume1/homes/sjeror/termisignal/start_server.sh')
        
        # Kontrola instalace
        print("Kontroluji instalaci...")
        stdin, stdout, stderr = ssh.exec_command('ls -la /volume1/homes/sjeror/termisignal')
        print(stdout.read().decode())
        
        # Spuštění serveru
        print("Spouštím server...")
        stdin, stdout, stderr = ssh.exec_command('/volume1/homes/sjeror/termisignal/start_server.sh')
        time.sleep(2)
        
        # Kontrola běhu serveru
        print("Kontroluji běh serveru...")
        stdin, stdout, stderr = ssh.exec_command('ps aux | grep ts_server.py')
        print(stdout.read().decode())
        
        print("Instalace dokončena!")
        
    except Exception as e:
        print(f"Chyba: {e}")
    
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
