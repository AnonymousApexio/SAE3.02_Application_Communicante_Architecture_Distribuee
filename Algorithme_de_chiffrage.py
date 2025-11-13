"""
Module de chiffrement RSA personnalisé pour le projet de routage onion
Implémentation manuelle sans bibliothèques externes de cryptographie
"""

import random
import json
from typing import Tuple, List, Union


class CustomRSA:
    """
    Implémentation personnalisée du chiffrement RSA
    Respecte les contraintes du projet : pas de librairie de cryptographie
    """
    
    @staticmethod
    def gcd(a: int, b: int) -> int:
        """
        Algorithme d'Euclide pour le calcul du PGCD
        Utilise l'itération pour de meilleures performances
        """
        while b != 0:
            a, b = b, a % b
        return a

    @staticmethod
    def multiplicative_inverse(e: int, phi: int) -> int:
        """
        Algorithme étendu d'Euclide pour trouver l'inverse multiplicatif
        """
        t0, t1 = 0, 1
        r0, r1 = phi, e
        
        while r1 != 0:
            quotient = r0 // r1
            t0, t1 = t1, t0 - quotient * t1
            r0, r1 = r1, r0 - quotient * r1
        
        if r0 != 1:
            raise ValueError("Aucun inverse multiplicatif n'existe")
        
        if t0 < 0:
            t0 += phi
            
        return t0

    @staticmethod
    def is_prime(num: int) -> bool:
        """
        Vérifie si un nombre est premier
        """
        if num == 2:
            return True
        if num < 2 or num % 2 == 0:
            return False
        for n in range(3, int(num**0.5) + 2, 2):
            if num % n == 0:
                return False
        return True

    @staticmethod
    def generate_primes(bits: int = 16) -> Tuple[int, int]:
        """
        Génère deux nombres premiers pour les clés RSA
        Utilise 64 bits par défaut pour des performances raisonnables
        """
        while True:
            p = random.getrandbits(bits)
            if p % 2 == 0:
                p += 1
            if CustomRSA.is_prime(p):
                break
        
        while True:
            q = random.getrandbits(bits)
            if q % 2 == 0:
                q += 1
            if CustomRSA.is_prime(q) and q != p:
                break
                
        return p, q

    @staticmethod
    def generate_keypair(p: int = None, q: int = None) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Génère une paire de clés publique/privée RSA
        
        Args:
            p, q: Nombres premiers (générés automatiquement si non fournis)
            
        Returns:
            Tuple: (clé_publique, clé_privée) où chaque clé est (exposant, modulus)
        """
        if p is None or q is None:
            p, q = CustomRSA.generate_primes()
        
        if not (CustomRSA.is_prime(p) and CustomRSA.is_prime(q)):
            raise ValueError('Les deux nombres doivent être premiers.')
        elif p == q:
            raise ValueError('p et q ne peuvent pas être égaux')
      
        n = p * q
        phi = (p - 1) * (q - 1)

        # Choisir un e valide
        e = random.randrange(3, phi)
        while CustomRSA.gcd(e, phi) != 1:
            e = random.randrange(3, phi)

        d = CustomRSA.multiplicative_inverse(e, phi)
        
        return ((e, n), (d, n))

    @staticmethod
    def encrypt(pk: Tuple[int, int], plaintext: Union[str, bytes]) -> List[int]:
        """
        Chiffre un message avec la clé publique
        
        Args:
            pk: Clé publique (e, n)
            plaintext: Message à chiffrer (string ou bytes)
            
        Returns:
            List[int]: Message chiffré sous forme de liste d'entiers
        """
        key, n = pk
        
        if isinstance(plaintext, bytes):
            # Convertir les bytes en string UTF-8 pour le traitement
            plaintext = plaintext.decode('utf-8', errors='ignore')
        
        # Chiffrement caractère par caractère (simplifié pour l'exemple)
        cipher = [pow(ord(char), key, n) for char in plaintext]
        
        return cipher

    @staticmethod
    def decrypt(pk: Tuple[int, int], ciphertext: List[int]) -> str:
        """
        Déchiffre un message avec la clé privée
        
        Args:
            pk: Clé privée (d, n)
            ciphertext: Message chiffré sous forme de liste d'entiers
            
        Returns:
            str: Message déchiffré
        """
        key, n = pk
        
        try:
            plain = [chr(pow(char, key, n)) for char in ciphertext]
            return ''.join(plain)
        except (ValueError, OverflowError):
            # Gestion des erreurs de déchiffrement
            raise ValueError("Erreur lors du déchiffrement - clé invalide ou données corrompues")

    @staticmethod
    def encrypt_for_router(pk: Tuple[int, int], next_hop: str, payload: str) -> str:
        """
        Formate un message pour le routage onion
        Structure: {next_hop}|{payload_chiffré}
        
        Args:
            pk: Clé publique du routeur cible
            next_hop: Adresse du prochain saut
            payload: Données à transmettre
            
        Returns:
            str: Message formaté pour le routage
        """
        message_data = f"{next_hop}|{payload}"
        encrypted_payload = CustomRSA.encrypt(pk, message_data)
        return json.dumps(encrypted_payload)

    @staticmethod
    def decrypt_from_router(pk: Tuple[int, int], encrypted_message: str) -> Tuple[str, str]:
        """
        Déchiffre un message reçu par un routeur
        Extrait le next_hop et le payload
        
        Args:
            pk: Clé privée du routeur
            encrypted_message: Message chiffré reçu
            
        Returns:
            Tuple: (next_hop, payload_déchiffré)
        """
        try:
            ciphertext = json.loads(encrypted_message)
            decrypted = CustomRSA.decrypt(pk, ciphertext)
            next_hop, payload = decrypted.split('|', 1)
            return next_hop, payload
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Erreur lors du déchiffrement du message: {e}")


class KeyManager:
    """
    Gestionnaire de clés pour le système de routage onion
    """
    
    def __init__(self):
        self.public_keys = {}  # {router_id: (e, n)}
        self.private_keys = {}  # {router_id: (d, n)}
    
    def generate_router_keys(self, router_id: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Génère une paire de clés pour un routeur
        """
        public_key, private_key = CustomRSA.generate_keypair()
        self.public_keys[router_id] = public_key
        self.private_keys[router_id] = private_key
        return public_key, private_key
    
    def get_public_key(self, router_id: str) -> Tuple[int, int]:
        """
        Récupère la clé publique d'un routeur
        """
        return self.public_keys.get(router_id)
    
    def get_private_key(self, router_id: str) -> Tuple[int, int]:
        """
        Récupère la clé privée d'un routeur
        """
        return self.private_keys.get(router_id)


# Tests unitaires pour validation
if __name__ == '__main__':
    def test_rsa_implementation():
        """Test complet de l'implémentation RSA"""
        print("🧪 Test de l'implémentation RSA personnalisée")
        
        # Génération des clés
        print("1. Génération des clés...")
        public_key, private_key = CustomRSA.generate_keypair()
        print(f"   Clé publique: (e={public_key[0]}, n={public_key[1]})")
        print(f"   Clé privée: (d={private_key[0]}, n={private_key[1]})")
        
        # Test de chiffrement/déchiffrement
        print("2. Test chiffrement/déchiffrement...")
        message = "Hello Onion Routing!"
        encrypted = CustomRSA.encrypt(public_key, message)
        decrypted = CustomRSA.decrypt(private_key, encrypted)
        
        print(f"   Message original: {message}")
        print(f"   Message chiffré: {encrypted[:5]}...")  # Affiche seulement les 5 premiers
        print(f"   Message déchiffré: {decrypted}")
        print(f"   ✅ Test réussi: {message == decrypted}")
        
        # Test format routage onion
        print("3. Test format routage onion...")
        next_hop = "192.168.1.3:8080"
        payload = "Message secret pour le client B"
        onion_message = CustomRSA.encrypt_for_router(public_key, next_hop, payload)
        decrypted_hop, decrypted_payload = CustomRSA.decrypt_from_router(private_key, onion_message)
        
        print(f"   Next hop original: {next_hop}")
        print(f"   Payload original: {payload}")
        print(f"   Next hop déchiffré: {decrypted_hop}")
        print(f"   Payload déchiffré: {decrypted_payload}")
        print(f"   ✅ Test routage réussi: {next_hop == decrypted_hop and payload == decrypted_payload}")
    
    # Exécution des tests
    test_rsa_implementation()