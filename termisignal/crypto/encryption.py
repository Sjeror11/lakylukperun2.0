"""
Modul pro end-to-end šifrování zpráv
"""

import base64
import nacl.utils
import nacl.secret
import nacl.public
from nacl.encoding import Base64Encoder

class Encryption:
    """
    Třída pro šifrování a dešifrování zpráv pomocí NaCl (PyNaCl)
    """
    
    def __init__(self):
        # Generování klíčového páru pro asymetrické šifrování
        self.private_key = nacl.public.PrivateKey.generate()
        self.public_key = self.private_key.public_key
        
    def get_public_key(self):
        """
        Vrátí veřejný klíč ve formátu Base64
        """
        return base64.b64encode(bytes(self.public_key)).decode('utf-8')
    
    def encrypt_message(self, message, recipient_public_key_b64):
        """
        Zašifruje zprávu pro příjemce pomocí jeho veřejného klíče
        """
        # Dekódování veřejného klíče příjemce
        recipient_public_key_bytes = base64.b64decode(recipient_public_key_b64)
        recipient_public_key = nacl.public.PublicKey(recipient_public_key_bytes)
        
        # Vytvoření boxu pro šifrování
        box = nacl.public.Box(self.private_key, recipient_public_key)
        
        # Šifrování zprávy
        nonce = nacl.utils.random(nacl.public.Box.NONCE_SIZE)
        encrypted = box.encrypt(message.encode('utf-8'), nonce)
        
        # Vrácení zašifrované zprávy ve formátu Base64
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_message(self, encrypted_message_b64, sender_public_key_b64):
        """
        Dešifruje zprávu od odesílatele pomocí jeho veřejného klíče
        """
        # Dekódování veřejného klíče odesílatele
        sender_public_key_bytes = base64.b64decode(sender_public_key_b64)
        sender_public_key = nacl.public.PublicKey(sender_public_key_bytes)
        
        # Vytvoření boxu pro dešifrování
        box = nacl.public.Box(self.private_key, sender_public_key)
        
        # Dešifrování zprávy
        encrypted_message = base64.b64decode(encrypted_message_b64)
        decrypted = box.decrypt(encrypted_message)
        
        # Vrácení dešifrované zprávy
        return decrypted.decode('utf-8')
