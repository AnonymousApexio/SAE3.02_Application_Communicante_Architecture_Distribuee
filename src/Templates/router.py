import sys
import socket
import threading
import os
import signal # Même raison que pour le master

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path: 
    sys.path.insert(0, project_root)

from src.Composants.Algorithme_de_chiffrage import RSA

def trouve_ip_local() -> str:
    """Trouve l'adresse IP locale"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception: 
        ip = '127.0.0.1'
    finally: 
        s.close()
    return ip

class Routeur:
    def __init__(self, id_routeur: str, ip_master: str, master_port: int, port_router: int):
        self.id: str = id_routeur
        self.master_addr: tuple[str, int] = (ip_master, int(master_port))
        self.port: int = int(port_router)
        self.ip: str = trouve_ip_local()
        self.en_cours: bool = True
        self.threads_actifs: list[threading.Thread] = []
        self.cipher: RSA = RSA()
        self.clé_publique, self.clé_privée = self.cipher.generate_keys()

        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.settimeout(1.0) 

    def gestionnaire_arrêt(self, sig, frame):
        """Gère l'arrêt propre avec CTRL+C"""
        print(f"\n[!] Signal d'arrêt reçu pour le routeur {self.id}...")
        self.arrêt_propre()

    def arrêt_propre(self):
        """Arrêt propre du routeur"""
        if not self.en_cours:
            return
            
        print(f"[!] Arrêt en cours du routeur {self.id}...")
        self.en_cours = False
        
        if hasattr(self, 'server_sock') and self.server_sock:
            try:
                self.server_sock.close()
                print(f"Info: Socket serveur fermé")
            except Exception as e:
                print(f"Erreur: Erreur fermeture socket: {e}")
        
        print(f"Attente de la fin des {len(self.threads_actifs)} threads...")
        for thread in self.threads_actifs[:]:
            if thread.is_alive():
                try:
                    thread.join(timeout=2.0)
                    if thread.is_alive():
                        print(f"[!] Thread non terminé: {thread.name}")
                except Exception as e:
                    print(f"[!] Erreur attente thread: {e}")
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect(self.master_addr)
            s.send(f"DEENREGISTREMENT_ROUTEUR|{self.id}".encode('utf-8'))
            s.close()
            print(f"Info: Déconnecté du master")
        except:
            print(f"Erreur: Impossible de contacter le master pour le déenregistrement")
        
        print(f"Info: Routeur {self.id} arrêté proprement")
        sys.exit(0)

    def enregistrement_vers_master(self):
        """Enregistre le routeur auprès du master"""
        msg = f"ENREGISTREMENT_ROUTEUR|{self.id}|{self.ip}|{self.port}|{self.clé_publique[0]}|{self.clé_publique[1]}"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5.0)
            s.connect(self.master_addr)
            s.send(msg.encode('utf-8'))
            s.close()
            print(f"Info: Enregistré sur Master ({self.ip}:{self.port})")
        except Exception as e:
            print(f"Erreur: Erreur Master: {e}")

    def start(self):
        """Démarre le routeur"""
        # Configurer les signaux
        signal.signal(signal.SIGINT, self.gestionnaire_arrêt) # Utilisateur
        signal.signal(signal.SIGTERM, self.gestionnaire_arrêt) # Système
        
        self.enregistrement_vers_master()
        
        try:
            self.server_sock.bind(('0.0.0.0', self.port))
            self.server_sock.listen(10)  # Backlog augmenté
            print(f"Info: Routeur {self.id} prêt sur {self.ip}:{self.port}")
            print(f"Appuyez sur CTRL+C pour arrêter")
        except Exception as e:
            print(f"Erreur: Erreur démarrage serveur: {e}")
            self.arrêt_propre()
            return
        
        while self.en_cours:
            try:
                client, addr = self.server_sock.accept()
                client.settimeout(10.0)
                
                if self.en_cours:
                    thread = threading.Thread(
                        target=self.gestionnaire_paquet,
                        args=(client, addr),
                        daemon=True
                    )
                    thread.start()
                    self.threads_actifs.append(thread)
                    threads_vivants = []
                    for t in self.threads_actifs: # Nettoyage des threads terminés pour éviter la fuite mémoire
                        if t.is_alive():
                            threads_vivants.append(t)
                    self.threads_actifs = threads_vivants

                    
            except socket.timeout:
                continue
            except OSError as e:
                if self.en_cours:
                    print(f"Erreur: Erreur accept: {e}")
                break
            except Exception as e:
                if self.en_cours:
                    print(f"Erreur: Erreur inattendue: {e}")
                break
        
        self.arrêt_propre()

    def gestionnaire_paquet(self, client_sock: socket.socket, addr: tuple):
        """Gère un paquet reçu"""
        try:
            donnee = client_sock.recv(65536).decode('utf-8')  # 64KB max
            if not donnee:
                return
            
            print(f"[Router {self.id}] Message de {addr}: {donnee[:100]}...")
            
            decrypté = self.cipher.decrypt(donnee)
            print(f"[Router {self.id}] Décrypté: {decrypté}")
            
            if "|" not in decrypté:
                print(f"[Router {self.id}] Format invalide")
                return

            parties = decrypté.split('|', 2)
            if len(parties) < 3:
                print(f"[Router {self.id}] Pas assez de parties")
                return
                
            prochaine_ip, prochaine_port, payload = parties[0], parties[1], parties[2]

            if prochaine_ip == "FINALE":
                f_parts = payload.split('|', 2)
                if len(f_parts) >= 3:
                    ip_destination, port_destination, actual_message = f_parts
                    print(f"[Router {self.id}] Destination finale: {ip_destination}:{port_destination}")
                    self.gestionnaire_envoie(ip_destination, port_destination, f"MESSAGE|{actual_message}")
                else:
                    print(f"[Router {self.id}] Payload FINAL malformé: {payload}")
            else:
                print(f"[Router {self.id}] Relay vers: {prochaine_ip}:{prochaine_port}")
                self.gestionnaire_envoie(prochaine_ip, prochaine_port, payload)
                
        except Exception as e:
            print(f"[Router {self.id}] Erreur traitement paquet: {e}")
        finally:
            try:
                client_sock.close()
            except:
                pass

    def gestionnaire_envoie(self, ip: str, port: int, donnee: str):
        """Envoie un message à une destination"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5.0)
            s.connect((ip, int(port)))
            s.send(donnee.encode('utf-8'))
            s.close()
            print(f"[Router {self.id}] Message envoyé à {ip}:{port}")
        except Exception as e:
            print(f"[Router {self.id}] Échec vers {ip}:{port}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python router.py <router_id> [-m master_ip] [-mp master_port] [-p router_port]")
        print("Exemple: python router.py R1 -m 127.0.0.1 -mp 9000 -p 9001")
        sys.exit(1)
    
    rid = sys.argv[1]
    
    # Valeurs par défaut
    m = "127.0.0.1"
    mp = 9000
    p = 8000
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "-m" and i + 1 < len(sys.argv):
            m = sys.argv[i + 1]
            i += 1
        elif arg == "-mp" and i + 1 < len(sys.argv):
            mp = int(sys.argv[i + 1])
            i += 1
        elif arg == "-p" and i + 1 < len(sys.argv):
            p = int(sys.argv[i + 1])
            i += 1
        elif arg in ["-h", "--help"]:
            print("Usage: python router.py <router_id> [-m master_ip] [-mp master_port] [-p router_port]")
            sys.exit(0)
        i += 1
    
    print(f"Info: Démarrage routeur {rid} sur le port {p}")
    print(f"Info: Master: {m}:{mp}")
    
    try:
        routeur = Routeur(rid, m, mp, p)
        routeur.start()
    except KeyboardInterrupt:
        print("\n[!] Arrêt par CTRL+C")
        if 'routeur' in locals():
            routeur.arrêt_propre()
    except Exception as e:
        print(f"[!] Erreur démarrage: {e}")
        sys.exit(1)