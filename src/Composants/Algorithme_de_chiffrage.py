import sympy
from typing import Tuple, List

class RSA:
    def __init__(self, taille_clé: int = 1024):
        """
        Initialise la classe RSA

        Args:
            taille_clé (int): Taille de la clé en bits
        """
        self.taille_clé = taille_clé
        self.clé_publique: Tuple[int, int] = None
        self.clé_privé: Tuple[int, int] = None

    def generate_keys(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Génère une paire de clés publique et privée

        Returns:
            Tuple[Tuple[int, int], Tuple[int, int]]: (clé_publique, clé_privée)
        """
        p: int = sympy.randprime(2**(self.taille_clé//2 - 1), 2**(self.taille_clé//2))
        q: int = sympy.randprime(2**(self.taille_clé//2 - 1), 2**(self.taille_clé//2))
        n: int = p * q
        phi: int = (p - 1) * (q - 1)
        e: int = 65537
        d: int = pow(e, -1, phi)
        
        self.clé_publique = (n, e)
        self.clé_privé = (n, d)
        return self.clé_publique, self.clé_privé

    def encrypt(self, message: str, clé_publique: Tuple[int, int]) -> str:
        """
        Retourne une string de nombres séparés par des virgules

        Args:
            message (str): Le message à chiffrer
            clé_publique (Tuple[int, int]): La clé publique (n, e)
        """
        n: int
        e: int
        n, e = clé_publique
        taille_bloque: int = (self.taille_clé // 8) - 11 
        entiers_chiffré: list[int] = []
        octets_message = message.encode('utf-8')

        
        for i in range(0, len(octets_message), taille_bloque):
            bloc: bytes = octets_message[i:i+taille_bloque]
            m_int = int.from_bytes(bloc, 'big')
            c_int = pow(m_int, e, n)
            entiers_chiffré.append(str(c_int))
            
        return ",".join(entiers_chiffré)

    def decrypt(self, encrypted_str: str) -> str:
        """
        Prend une string de nombres séparés par virgules

        Args:
            encrypted_str (str): Le message chiffré
        """
        if not self.clé_privé: 
            raise ValueError("Pas de clé privée")
        n, d = self.clé_privé
        
        try:
            chunks: List[int] = []
            for x in encrypted_str.split(','):
                if x.strip():
                    chunks.append(int(x))
        except ValueError:
            return ""

        message_decrypté = ""
        for c_int in chunks:
            m_int = pow(c_int, d, n)
            try:
                message_decrypté += m_int.to_bytes((m_int.bit_length() + 7) // 8, 'big').decode('utf-8')
            except:
                pass 
        return message_decrypté