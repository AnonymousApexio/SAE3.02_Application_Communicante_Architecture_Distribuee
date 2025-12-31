import sys
import socket
import threading
import mysql.connector
import signal # Pour gérée les interruptions clavier (grâce à signal.SIGINT), j'étais obligé pour géré le fait que le port resté occupé après fermeture
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QCloseEvent
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path: 
    sys.path.insert(0, project_root)

def chargement_conf_bdd() -> dict:
    """
    Charge la configuration depuis config.conf

    Returns:
        dict: la configuration sous forme de dictionnaire
    """
    config: dict = {}
    try:
        with open('src/Configuration/config.conf', 'r') as f:
            for line in f:
                clé: str
                val: str
                clé, val = line.strip().split('=', 1) # a
                config[clé.strip()] = val.strip()
                print(f"Chargé: {clé.strip()} = {val.strip()}")
    except FileNotFoundError:
        print("Fichier config.conf non trouvé.")
        input("Appuyez sur Entrée pour continuer...")
        exit(1)
    return config

DB_CONFIG = chargement_conf_bdd()

def trouve_ip_local():
    """
    Le nom explique la fonction

    Returns:
        _RetAddress: L'adresse IP locale du serveur master
    """
    s: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip: socket._RetAddress = s.getsockname()[0]
    except Exception: 
        ip = '127.0.0.1'
    finally: 
        s.close()
    return ip

class MasterServer(threading.Thread):
    """
    Initialisation du serveur master qui gère les enregistrements des routeurs et clients, ainsi que la journalisation dans la base de données de MariaDB.

    Args:
        threading.Thread (Class): Héritage de threading.Thread ce qui permet l'exécution en arrière-plan.
    """
    def __init__(self, port: int, log_callback: callable) -> None:
        """
        Initialisation du serveur.

        Args:
            port (str): Port d'écoute du serveur
            log_callback (callable): Fonction de callback pour afficher les logs sur l'interface graphique
        """
        super().__init__()
        self.port: int = port
        self.log_callback = log_callback
        self.en_cours: bool = True
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.port))
        self.init_bdd()

    def init_bdd(self) -> None:
        """
        Initialise la connexion à la base de donnée et réinitialise la table des routeurs.
        """
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            curseur = conn.cursor()
            curseur.execute("DELETE FROM routeurs")
            conn.commit()
            curseur.close()
            conn.close()
            self.log_callback("BASE DE DONNÉE", "Table 'routeurs' réinitialisée. Logs conservés.")
        except Exception as e:
            self.log_callback("BASE DE DONNÉE", f"Erreur SQL: {e}")

    def sauvegarde_log(self, event_type, details) -> None:
        """

        Enregistre une log dans la base de données.

        Args:
            event_type (str): Type d'événement
            details (str): Description de l'événement
        """
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            curseur = conn.cursor()
            requête = "INSERT INTO logs (event_type, details) VALUES (%s, %s)"
            curseur.execute(requête, (event_type, details))
            conn.commit()
            curseur.close()
            conn.close()
            self.log_callback(event_type, details)
        except Exception as e:
            print(f"Erreur DB Log: {e}")

    def stop(self) -> None:
        """
        Arrête le serveur master proprement en ce connectant à lui même pour débloquer l'accept() de run().
        """
        self.en_cours = False
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('127.0.0.1', self.port))
        self.sock.close()

    def run(self) -> None:
        """
        Méthode run() overloadé de thread qui lance la boucle principale du serveur master:
        - Accepte les connexions entrantes.
        - Traite les messages reçus.
        - Gère les enregistrements des routeurs et clients.
        - Envoie la liste des routeurs aux clients sur demande.
        - Journalise les événements dans la base de données.
        """
        self.sock.listen()
        while self.en_cours:
            try:
                client, addr = self.sock.accept()
                if not self.en_cours: 
                    break
                threading.Thread(target=self.gère_client, args=(client,)).start()
            except: 
                pass

    def gère_client(self, socket_client: socket.socket) -> None:
        """
        Gère les connexions des clients

        Args:
            socket_client (socket.socket): Socket du client connecté
        """
        try:
            donnee = socket_client.recv(65536).decode('utf-8')
            if not donnee: 
                return
            parties = donnee.split('|')
            cmd = parties[0]
            
            conn = mysql.connector.connect(**DB_CONFIG)
            curseur = conn.cursor(dictionary=True)

            # Juste question de sécurité, une faille d'injection basique pourrait être évitée ici
            if cmd not in ["ENREGISTREMENT_ROUTEUR", "DEENREGISTREMENT_ROUTEUR", "ENREGISTREMENT_CLIENT", "LISTE_ROUTEURS"]:
                socket_client.send("ERREUR|Commande inconnue".encode('utf-8'))
                self.log_callback("ERROR", "Format de de commande invalide")
                return
            
            # Format: ENREGISTREMENT_ROUTEUR|ID_routeur|ip|port|clé_publique_n|clé_publique_e
            if cmd == "ENREGISTREMENT_ROUTEUR":
                if len(parties) != 6:
                    self.log_callback("ERROR", "Format de d'enregistrement de routeur invalide")
                    return
                r_id, r_ip, r_port, r_n, r_e = parties[1], parties[2], parties[3], parties[4], parties[5]
                requête: str = "INSERT INTO routeurs (router_id, ip_address, port, public_key_n, public_key_e) VALUES (%s, %s, %s, %s, %s)"
                curseur.execute(requête, (r_id, r_ip, r_port, r_n, r_e))
                conn.commit()
                self.sauvegarde_log(cmd, f"Le routeur {r_id} a rejoint le réseau sur {r_ip}:{r_port}")
                socket_client.send("ACK".encode('utf-8'))
                print(f"[Master] Routeur {r_id} enregistré avec succès")

            # Format: DEENREGISTREMENT_ROUTEUR|ID_routeur
            elif cmd == "DEENREGISTREMENT_ROUTEUR":
                if len(parties) != 2:
                    self.log_callback("ERROR", "Format de désenregistrement invalide")
                    return
                r_id = parties[1]
                
                curseur.execute("SELECT * FROM routeurs WHERE router_id = %s", (r_id,))
                routeur: dict = curseur.fetchone()
                
                if routeur:
                    curseur.execute("DELETE FROM routeurs WHERE router_id = %s", (r_id,))
                    conn.commit()
                    self.sauvegarde_log(cmd, f"Le routeur {r_id} a quitté le réseau")
                    socket_client.send("ACK".encode('utf-8'))
                    print(f"[Master] Routeur {r_id} désenregistré avec succès")
                else:
                    socket_client.send("ERREUR|Routeur inconnu".encode('utf-8'))
                    self.log_callback("WARNING", f"Tentative de désenregistrement d'un routeur inconnu: {r_id}")

            # Format: ENREGISTREMENT_CLIENT|nom_hôte
            elif cmd == "ENREGISTREMENT_CLIENT":
                self.sauvegarde_log(cmd, f"Nouveau client connecter")
                socket_client.send("ACK".encode('utf-8'))

            # Format: LISTE_ROUTEURS
            elif cmd == "LISTE_ROUTEURS":
                curseur.execute("SELECT * FROM routeurs")
                rangé = curseur.fetchall()
                list_r = []
                for routeur in rangé:
                    list_r.append(f"{routeur['router_id']}:{routeur['ip_address']}:{routeur['port']}:{routeur['public_key_n']}:{routeur['public_key_e']}")
                # Format: ROUTEURS|ID_ROUTEUR:IP:PORT:N:E;ID:IP:PORT:N:E;
                socket_client.send(("ROUTEURS|" + ";".join(list_r)).encode('utf-8'))
                self.sauvegarde_log(cmd, f"Liste des routeurs envoyée à un client")
            conn.close()
            socket_client.close()
        except Exception as e:
            self.log_callback("ERROR", str(e))

class MasterWindow(QMainWindow):
    """
    Initialisation de la fenêtre de l'application

    Args:
        QMainWindow (Class): Héritage de QMainWindow pour créer une fenêtre principale PyQt6
    """
    def __init__(self, port: int):
        """
        Initialisation de la fenêtre principale.
        
        Args:
            port (int): Port d'écoute du serveur master
        """
        super().__init__()
        self.setWindowTitle("SAE 3.02 - ADMINISTRATION")
        self.resize(900, 600)
        self.setStyleSheet("""
            /* Main window */
            QMainWindow { 
                background-color: #0f172a;
            }
            
            /* Labels */
            QLabel { 
                color: #cbd5e1;
                font-weight: 600; 
                font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
                font-size: 10pt;
            }
            
            /* Log display */
            QTextEdit { 
                background-color: #1e293b; 
                color: #e2e8f0;  /* Better contrast than cyan */
                border: 2px solid #334155; 
                border-radius: 8px;
                font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
                font-size: 10pt; 
                padding: 12px;
                selection-background-color: #3b82f6;
                selection-color: #ffffff;
            }
            
            /* Scrollbar styling */
            QScrollBar:vertical {
                border: none;
                background: #1e293b;
                width: 10px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical {
                background: #475569;
                border-radius: 4px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #64748b;
            }
            
            /* Button if you add any */
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            
            QPushButton:hover {
                background-color: #2563eb;
            }
            
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)
        contenaire = QWidget()
        layout = QVBoxLayout(contenaire)
        
        entête = QLabel(f"SERVEUR MASTER ACTIF - {trouve_ip_local()}:{port}")
        entête.setStyleSheet("color: #f8fafc; font-size: 18px; margin-bottom: 10px;")
        entête.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.display_logs = QTextEdit()
        self.display_logs.setReadOnly(True)

        # In your layout setup
        status_label = QLabel("Serveur en cours d'exécution")
        status_label.setStyleSheet("""
            QLabel {
                background-color: #10b981;
                color: white;
                padding: 8px;
                border-radius: 6px;
                font-weight: 500;
            }
        """)
        layout.addWidget(status_label)

        clear_btn = QPushButton("Effacer les logs")
        clear_btn.clicked.connect(self.display_logs.clear)

        export_btn = QPushButton("Exporter logs")
        export_btn.clicked.connect(self.export_logs)

        button_layout = QHBoxLayout()
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        layout.addWidget(entête)
        layout.addWidget(self.display_logs)
        self.setCentralWidget(contenaire)
        
        self.server = MasterServer(port, self.ajout_log_ui)
        self.server.start()

    def ajout_log_ui(self, événement: str, message: str) -> None:
        """
        Ajoute les logs à l'interface graphique.

        Args:
            événement (str): Type d'événement
            message (str): Message de l'événement
        """

        couleurs = {
            "BASE DE DONNÉE": "#10b981",     # Vert
            "ENREGISTREMENT": "#3b82f6",  # Bleu  
            "ERROR": "#ef4444",        # Rouge
            "WARNING": "#f59e0b",      # Ambre
            "INFO": "#8b5cf6"          # Violet
        }
        
        couleur = couleurs.get(événement, "#688aba") 
        
        timestamp = QDateTime.currentDateTime().toString("HH:mm:ss")
        formatted = f"""
        <div style="margin-bottom: 4px;">
            <span style="color: #64748b; font-size: 9pt;">[{timestamp}]</span>
            <span style="color: {couleur}; font-weight: 600;">[{événement}]</span>
            <span style="color: #e2e8f0;"> {message}</span>
        </div>
        """
        self.display_logs.append(formatted)

    def export_logs(self) -> None:
        """
        Exporte les logs affichés dans un fichier texte horodaté.
        """
        try:
            contenu = self.display_logs.toPlainText()
            nom_fichier = f"logs_master_{QDateTime.currentDateTime().toString('yyyyMMdd_HHmmss')}.txt"
            with open(nom_fichier, 'w', encoding='utf-8') as f:
                f.write(contenu)
            self.ajout_log_ui("INFO", f"Logs exportés vers {nom_fichier}")
        except Exception as e:
            self.ajout_log_ui("ERROR", f"Échec de l'exportation des logs: {e}")
    
    def FermeEvent(self, événement: QCloseEvent) -> None:
        """
        Appelée lors de la fermeture de la fenêtre.

        Args:
            événement (QCloseEvent): Événement de fermeture
        """
        self.server.stop()
        self.server.join()
        événement.accept()

if __name__ == "__main__":
    application = QApplication(sys.argv)
    fenêtre = MasterWindow(9000)
    fenêtre.show()

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(application.exec())