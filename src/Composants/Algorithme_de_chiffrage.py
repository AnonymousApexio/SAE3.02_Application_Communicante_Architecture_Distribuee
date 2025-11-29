"""
Module de chiffrement RSA personnalisé pour le projet de routage onion
Implémentation manuelle sans bibliothèques externes de cryptographie
"""

import random
# Ajout de isprime et suppression de mon ancienne fonction car simpy.isprime est beaucoup plus efficace (Passe de 256 bits prenant 30s à 1024 bits en quelque secondes.)
from sympy import isprime
from typing import List, Tuple, Union, Dict

class RSA:
    """
    Initialisation de la classe RSA
    """
    
    @staticmethod
    def _pgcd(a: int, b: int) -> int:
        """
        Méthode statique de l'algorithme d'euclide pour le calcul du PGCD (Plus grand commun diviseur)
        Utilise l'itération pour de meilleures performances

        Args:
            a (int): nombre 1
            b (int): nombre 2
        """
        while b != 0:
            a, b = b, a % b
        return a

    @staticmethod
    def _multiplicative_inverse(e: int, phi: int) -> int:
        """
        Méthode statique de l'algorithme étendu d'Euclide pour trouver l'inverse multiplicative

        Args:
            e (int): exposant public
            phi (int): valeur de phi(n)
        """
        t0: int
        t1: int
        r0: int
        r1: int
        t0, t1 = 0, 1
        r0, r1 = phi, e
        
        while r1 != 0:
            quotient: int = r0 // r1
            t0, t1 = t1, t0 - quotient * t1
            r0, r1 = r1, r0 - quotient * r1
        
        if r0 != 1:
            raise ValueError("Aucun inverse multiplicatif n'existe")
        
        if t0 < 0:
            t0 += phi
            
        return t0

    @staticmethod
    def generate_primes(bits: int = 1024) -> tuple[int, int]:
        """
        Génère deux nombres premiers pour les clés RSA

        Args:
            bits (int): Le nombre de bit pour les clés RSA. Défaut à 64 bits.
        """
        while True:
            p: int = random.getrandbits(bits)
            if p % 2 == 0:
                p += 1
            if isprime(p):
                break
        
        while True:
            q: int = random.getrandbits(bits)
            if q % 2 == 0:
                q += 1
            if isprime(q) and q != p:
                break
        return p, q

    @staticmethod
    def generate_keypair(p: Union[int, None] = None, q: Union[int, None] = None) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Génère une paire de clés publique/privée RSA
        
        Args:
            p, q (int): Nombres premiers (générés automatiquement si non fournis)
            
        Returns:
            Tuple: (clé_publique, clé_privée) où chaque clé est (exposant, modulus)
        """
        if p is None or q is None:
            p, q = RSA.generate_primes()
        
        if not (isprime(p) and isprime(q)):
            raise ValueError('Les deux nombres doivent être premiers.')
        elif p == q:
            raise ValueError('p et q ne peuvent pas être égaux')

        n: int = p * q
        phi: int = (p - 1) * (q - 1)

        # Choisi un nombre e valide
        e: int = random.randrange(3, phi)
        while RSA._pgcd(e, phi) != 1:
            e = random.randrange(3, phi)

        d: int = RSA._multiplicative_inverse(e, phi)
        return ((e, n), (d, n))

    @staticmethod
    def _encrypt(pk: Tuple[int, int], plaintext: Union[str, bytes]) -> List[int]:
        """
        Chiffre un message avec la clé publique
        
        Args:
            pk (Tuple[int, int]): Clé publique (e, n)
            plaintext (Union[str, bytes]): Message à chiffrer (string ou bytes)
            
        Returns:
            List[int]: Message chiffré sous forme de liste d'entiers
        """
        key: int
        n: int
        key, n = pk
        
        if isinstance(plaintext, bytes):
            plaintext = plaintext.decode('utf-8')
        
        cipher: List[int] = []
        for char in plaintext:
            c: int = pow(ord(char), key, n)
            cipher.append(c)
        return cipher

    @staticmethod
    def _decrypt(pk: Tuple[int, int], ciphertext: List[int]) -> str:
        """
        Déchiffre un message avec la clé privée
        
        Args:
            pk (Tuple[int, int]): Clé privée (d, n)
            ciphertext (List[int]): Message chiffré sous forme de liste d'entiers
            
        Returns:
            str: Message déchiffré
        """
        key: int
        n: int
        key, n = pk
        
        try:
            plain: List[str] = []
            for char in ciphertext:
                decrypted_char: int = pow(char, key, n)
                c: str = chr(decrypted_char)
                plain.append(c)
            return ''.join(plain)
        except (ValueError, OverflowError):
            raise ValueError("Erreur lors du déchiffrement - clé invalide ou données corrompues")

    @staticmethod
    def _serialize_ciphertext(ciphertext: List[int]) -> str:
        """
        Sérialise une liste d'entiers en string
        
        Args:
            ciphertext (List[int]): Liste d'entiers à sérialiser
            
        Returns:
            str: String sérialisée
        """
        serialized_text: str = ""
        for i, num in enumerate(ciphertext):
            if i > 0:
                serialized_text += ","
            serialized_text += str(num)
        return serialized_text

    @staticmethod
    def _deserialize_ciphertext(serialized: str) -> List[int]:
        """
        Désérialise une string en liste d'entiers
        
        Args:
            serialized (str): String sérialisée
            
        Returns:
            List[int]: Liste d'entiers désérialisée
        """
        try:
            if not serialized:
                return []
            
            parts: List[str] = serialized.split(',')
            deserialized_text: List[int] = []
            for part in parts:
                if part.strip():
                    deserialized_text.append(int(part))
            return deserialized_text
        except ValueError as e:
            raise ValueError(f"Erreur lors de la désérialisation: {e}")

    @staticmethod
    def encrypt_for_router(pk: Tuple[int, int], next_hop: str, payload: str) -> str:
        """
        Formate un message pour le routage onion
        Structure: pk({next_hop}, {payload_chiffré})
        
        Args:
            pk (Tuple[int, int]): Clé publique du routeur cible
            next_hop (str): Adresse du prochain saut
            payload (str): Données à transmettre
            
        Returns:
            str: Message formaté pour le routage
        """
        message_data: str = f"{next_hop}|{payload}"
        encrypted_payload: List[int] = RSA._encrypt(pk, message_data)
        return RSA._serialize_ciphertext(encrypted_payload)

    @staticmethod
    def decrypt_from_router(pk: Tuple[int, int], encrypted_message: str) -> Tuple[str, str]:
        """
        Déchiffre un message reçu par un routeur
        Extrait le next_hop et le payload
        
        Args:
            pk (Tuple[int, int]): Clé privée du routeur
            encrypted_message (str): Message chiffré reçu
            
        Returns:
            Tuple: (next_hop, payload_déchiffré)
        """
        try:
            ciphertext: List[int] = RSA._deserialize_ciphertext(encrypted_message)
            decrypted: str = RSA._decrypt(pk, ciphertext)
            parts: List[str] = decrypted.split('|', 1)
            if len(parts) != 2:
                raise ValueError("Format de message invalide")
            next_hop: str = parts[0]
            payload: str = parts[1]
            return next_hop, payload
        except (ValueError, IndexError) as e:
            raise ValueError(f"Erreur lors du déchiffrement du message: {e}")

class KeyManager:
    """
    Gestionnaire de clés pour le système de routage onion
    """
    
    def __init__(self):
        self.public_keys: Dict[str, Tuple[int, int]] = {}
        self.private_keys: Dict[str, Tuple[int, int]] = {}
    
    def generate_router_keys(self, router_id: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Génère une paire de clés pour un routeur
        """
        public_key, private_key = RSA.generate_keypair()
        self.public_keys[router_id] = public_key
        self.private_keys[router_id] = private_key
        return public_key, private_key
    
    def get_public_key(self, router_id: str) -> Union[Tuple[int, int], None]:
        """
        Récupère la clé publique d'un routeur
        """
        return self.public_keys.get(router_id)
    
    def get_private_key(self, router_id: str) -> Union[Tuple[int, int], None]:
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
        public_key, private_key = RSA.generate_keypair()
        print(f"   Clé publique: (e={public_key[0]}, n={public_key[1]})")
        print(f"   Clé privée: (d={private_key[0]}, n={private_key[1]})")
        
        # Test de chiffrement/déchiffrement
        print("2. Test chiffrement/déchiffrement...")
        message = "Message"
        encrypted = RSA._encrypt(public_key, message)
        decrypted = RSA._decrypt(private_key, encrypted)
        
        print(f"   Message original: {message}")
        print(f"   Message chiffré: {encrypted}")
        print(f"   Message déchiffré: {decrypted}")
        print(f"   ✅ Test réussi: {message == decrypted}")
        
        # Test format routage onion
        print("3. Test format routage onion...")
        next_hop = "192.168.1.3:8080"
        payload = "Message secret pour le client B"
        onion_message = RSA.encrypt_for_router(public_key, next_hop, payload)
        print(f"   Message onion: {onion_message}")
        
        decrypted_hop, decrypted_payload = RSA.decrypt_from_router(private_key, onion_message)
        
        print(f"   Next hop original: {next_hop}")
        print(f"   Payload original: {payload}")
        print(f"   Next hop déchiffré: {decrypted_hop}")
        print(f"   Payload déchiffré: {decrypted_payload}")
        print(f"   ✅ Test routage réussi: {next_hop == decrypted_hop and payload == decrypted_payload}")
    
    # Exécution des tests
    test_rsa_implementation()