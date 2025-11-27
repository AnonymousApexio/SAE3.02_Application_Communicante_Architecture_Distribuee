"""
Client simple pour connexion basique sans chiffrement implémenté
"""

import socket
import threading
import time

class Client:
    """
    Client basique pour tests de connexion sans chiffrement
    """
    
    def __init__(self, id_client: str, hote: str = 'localhost', port: int = 9001) -> None:
        """
        Constructeur de la classe Client

        Args:
            id_client (str): ID du client (Son nom)
            hote (str, optional): Le nom/IP de l'hôte, défaut à 'localhost'.
            port (int, optional): Le numéro du port d'écoute, défaut à 9001.
        """
        self.id_client: str = id_client
        self.hote: str = hote
        self.port: int = port
        
        self.est_en_ligne: bool = False
        self.est_en_ecoute: bool = False
        self.historique_des_messages: list[str] = []
        
        self.socket_ecoutante: socket.socket = None
        
        self.logs: list[str] = []
        self._log(f"Client {id_client} initialisé")

    def _log(self, message: str):
        """
        Méthode interne permettant le log des intéractions réseaux

        Args:
            message (str): un message, souvent une erreur ou une réponse.
        """
        timestamp = time.strftime("%H:%M:%S")
        entree_log = f"[{timestamp}] {message}"
        self.logs.append(entree_log)
        # Ajout de l'envoie des logs vers le master dans le future
        print(entree_log)

    def ecoute(self) -> bool:
        """
        Méthode démarrant l'écoute sur la socket.

        Returns:
            bool: Retourne un booléen pour voir si la socket est bien en écoute.
        """
        try:
            self.socket_ecoutante = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_ecoutante.bind((self.hote, self.port))
            # écoute jusqu'à 5 connexions
            self.socket_ecoutante.listen(5)
            self.port = self.socket_ecoutante.getsockname()[1]
            
            self.est_en_ecoute = True
            
            # Thread d'écoute
            thread_ecoute = threading.Thread(target=self._composant_ecoute_message, daemon=True)
            thread_ecoute.start()
            
            self._log(f"En écoute sur {self.hote}:{self.port}")
            return True
            
        except Exception as e:
            self._log(f"Erreur démarrage écoute: {e}")
            return False

    def _composant_ecoute_message(self) -> None:
        """
        Méthode interne écoutant les connexions entrantes
        """
        while self.est_en_ecoute:
            try:
                socket_client: socket.socket
                address: socket._RetAddress
                socket_client, address = self.socket_ecoutante.accept()
                self._log(f"Connexion reçue de {address}")
                
                # Traitement du message dans un thread séparé
                thread_message: threading.Thread = threading.Thread(
                    target=self._gestionnaire_de_message,
                    args=(socket_client,),
                    daemon=True
                )
                thread_message.start()
                
            except Exception as e:
                if self.est_en_ecoute:
                    self._log(f"Erreur écoute: {e}")

    def _gestionnaire_de_message(self, socket_client: socket.socket):
        """
        Traite un message reçu

        Args:
            socket_client (socket.socket): la socket courante.
        """
        try:
            donnee_message: str = socket_client.recv(1024).decode('utf-8')
            self._log(f"Message reçu: {donnee_message}")
            
            # Formattage du message
            parties: list[str] = donnee_message.split('|')
            if len(parties) >= 3:
                message_type: str = parties[0]
                sender: str = parties[1]
                message_content: str = parties[2]
                
                if message_type == "MSG":
                    entree_log: str = f"📨 De {sender}: {message_content}"
                    self.historique_des_messages.append(entree_log)
                    self._log(entree_log)
                    
                    réponse: str = f"ACK|{self.id_client}|Message reçu"
                    socket_client.send(réponse.encode('utf-8'))
            else:
                raise TypeError
        
            socket_client.close()
        except TypeError as e:
            self._log(f"Erreur: Le message est mal formatté.")
            try:
                socket_client.close()
            except:
                pass

        except Exception as e:
            self._log(f"Erreur: Erreur traitement message: {e}")
            try:
                socket_client.close()
            except:
                pass

    def envoie_message(self, hote_cible: str, port_cible: int, message: str) -> bool:
        """
        Méthode d'envoie un message direct à un autre client

        Args:
            hote_cible (str): IP de la cible.
            port_cible (int): Port de la cible
            message (str): Un message du format: TYPE|EXPEDITEUR|MESSAGE

        Returns:
            bool: Retourne un booléen pour voir si ça à fonctionné ou non.
        """
        try:
            self._log(f"Envoi à {hote_cible}:{port_cible} : {message}")
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((hote_cible, port_cible))
                
                # Format du message: 
                donnee_message = f"MSG|{self.id_client}|{message}"
                sock.send(donnee_message.encode('utf-8'))
                
                réponse: str = sock.recv(1024).decode('utf-8')
                self._log(f"Réponse: {réponse}")
                
                return True
                
        except Exception as e:
            self._log(f"Erreur envoi message: {e}")
            return False

    def get_status(self) -> dict[str, str|int|bool]:
        """
        Getter du statut du client

        Returns:
            dict[str, str|int|bool]: Un dictionnaire des 
        """
        return {
            'id_client': self.id_client,
            'hote': self.hote,
            'port': self.port,
            'écoute': self.est_en_ecoute,
            'nombre_messages': len(self.historique_des_messages)
        }

    def stop(self):
        """
        Méthode d'arrêt du client
        """
        self.est_en_ecoute = False
        if self.socket_ecoutante:
            self.socket_ecoutante.close()
        self._log("Client arrêté")