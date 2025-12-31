import sys
import socket
import random
import os
import signal
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QSpinBox, QFrame, QStatusBar
from PyQt6.QtCore import QThread, pyqtSignal, QDateTime
from PyQt6.QtGui import QCloseEvent

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path: sys.path.insert(0, project_root)

from src.Composants.Algorithme_de_chiffrage import RSA

class ÉcouteClient(QThread):
    """
    Thread d'écoute pour recevoir les messages du serveur

    Raises:
        e: Erreur lors de l'initialisation
    """
    message_recu = pyqtSignal(str) # Cette seul ligne de code m'a fait perdre 2 heures de ma vie à cause d'un "ç" au lieu de "c"
    
    def __init__(self, port: int):
        """
        Initialise le thread d'écoute

        Args:
            port (int): Port d'écoute

        Raises:
            e: Erreur lors de l'initialisation
        """
        super().__init__()
        try:
            self.port = int(port)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception as e:
            print(f"[ERREUR INIT THREAD] {e}")
            raise e

    def run(self):
        """
        Méthode overloadée pour démarrer le thread d'écoute
        """
        try:
            self.sock.bind(('0.0.0.0', self.port))
            self.sock.listen(50)
            while True:
                conn, _ = self.sock.accept()
                try:
                    data = conn.recv(4096).decode('utf-8')
                    if "|" in data:
                        msg_content = data.split('|')[1]
                        self.message_recu.emit(msg_content)
                except Exception as e:
                    print(f"Erreur lecture socket: {e}")
                finally:
                    conn.close()
        except OSError as e:
            print(f"[ERREUR CRITIQUE] Le port {self.port} est probablement deja occupe.\nDetails: {e}")
        except Exception as e:
            print(f"[ERREUR RUN] {e}")

    def stop(self):
        """
        Arrête le thread d'écoute
        """
        try:
            if hasattr(self, 'sock'):
                self.sock.close()
            self.terminate()
        except:
            pass

class ApplicationClient(QMainWindow):
    """
    Classe principale de l'application client

    Args:
        QMainWindow (Class): Fenêtre principale PyQt6
    """
    def __init__(self, m_ip: str, m_port: str, port_client: str):
        """
        Initialise la classe ApplicationClient

        Args:
            m_ip (str): L'adresse IP du master
            m_port (str): Le port du master
            port_client (str): Le port du client
        """
        super().__init__()
        self.addr_master = (m_ip, int(m_port))
        self.port_client = int(port_client)
        self.cipher = RSA()
        
        self.setup_ui()
        self.setup_ecoute()
        self.enregistre_client()

    def setup_ui(self):
        """
        Configure l'interface utilisateur
        """
        self.setWindowTitle(f"Client - Port {self.port_client}")
        self.resize(900, 600) 
        
        self.setStyleSheet("""
            /* Fenêtre principal */
            QMainWindow { 
                background-color: #0f172a;
            }
            
            /* Barre de côte */
            QFrame#CoteBar{ 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e293b, stop:1 #0f172a);
                border-right: 2px solid #334155;
            }
            
            /* Titre de sections */
            QLabel.section {
                color: #38bdf8;
                font-size: 12px;
                font-weight: bold;
                margin-top: 15px;
                margin-bottom: 5px;
            }
            
            /* Les inputs */
            QLineEdit, QSpinBox { 
                background-color: #1e293b; 
                color: #f1f5f9; 
                border: 2px solid #475569;
                border-radius: 6px; 
                padding: 8px;
                font-size: 12px;
            }
            /* Quand on les focus (Presse dessus pour les edites)*/
            QLineEdit:focus, QSpinBox:focus { 
                border-color: #3b82f6; 
            }
            
            /* Boutons */
            QPushButton { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #1d4ed8);
                color: white; 
                border-radius: 8px; 
                padding: 12px 20px;
                font-weight: 600;
                font-size: 12px;
                border: none;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #60a5fa, stop:1 #3b82f6);
            }
            QPushButton:pressed { 
                background: #1e40af; 
            }
            QPushButton:disabled {
                background: #475569;
                color: #94a3b8;
            }
            
            /* Le chat */
            QTextEdit#ChatDisplay { 
                background-color: #020617; 
                color: #e2e8f0; 
                border: none;
                border-left: 2px solid #334155;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11pt;
                padding: 15px;
                selection-background-color: #3b82f6;
            }
            
            /* Indiacteur de status */
            QFrame#Indicateur_etat {
                background-color: #10b981;
                border-radius: 3px;
                min-width: 10px;
                max-width: 10px;
                min-height: 10px;
                max-height: 10px;
            }
        """)

        pièce_centrale = QWidget()
        layout_principal = QHBoxLayout(pièce_centrale)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        barre_coté_principale = QFrame()
        barre_coté_principale.setObjectName("CoteBar")
        barre_coté_principale.setFixedWidth(240)
        bar_cote = QVBoxLayout(barre_coté_principale)
        bar_cote.setContentsMargins(20, 20, 20, 20)
        bar_cote.setSpacing(10)
        
        layout_du_status = QHBoxLayout()
        indicateur_etat = QFrame()
        indicateur_etat.setObjectName("Indicateur_etat")
        label_etat = QLabel("Connecte au reseau")
        label_etat.setStyleSheet("color: #10b981; font-weight: 500;")
        layout_du_status.addWidget(indicateur_etat)
        layout_du_status.addWidget(label_etat)
        layout_du_status.addStretch()
        bar_cote.addLayout(layout_du_status)
        
        bar_cote.addSpacing(20)
        
        label_config = QLabel("⚙️ CONFIGURATION")
        label_config.setObjectName("section")
        bar_cote.addWidget(label_config)
        
        bar_cote.addWidget(QLabel("Adresse IP Cible:"))
        self.ip_destination = QLineEdit("127.0.0.1")
        self.ip_destination.setPlaceholderText("ex: 192.168.1.100")
        self.ip_destination.textChanged.connect(self.valide_ip)
        bar_cote.addWidget(self.ip_destination)

        self.label_erreur_ip = QLabel("")
        self.label_erreur_ip.setStyleSheet("color: #ef4444; font-size: 9px;")
        self.label_erreur_ip.setVisible(False)
        bar_cote.addWidget(self.label_erreur_ip)
        
        bar_cote.addWidget(QLabel("Port Destination:"))
        self.port_destination = QSpinBox()
        self.port_destination.setRange(1, 65535)
        self.port_destination.setValue(8001)
        bar_cote.addWidget(self.port_destination)
        
        bar_cote.addWidget(QLabel("Nombre de Sauts:"))
        self.sauts = QSpinBox()
        self.sauts.setRange(0, 50)
        self.sauts.setValue(3)
        self.sauts.setSuffix(" routeurs")
        bar_cote.addWidget(self.sauts)
        
        bar_cote.addSpacing(20)
        
        label_informatif = QLabel("🌐 RÉSEAU")
        label_informatif.setObjectName("section")
        bar_cote.addWidget(label_informatif)
        
        label_master = QLabel(f"Master: {self.addr_master[0]}:{self.addr_master[1]}")
        label_master.setStyleSheet("color: #94a3b8; font-size: 11px;")
        bar_cote.addWidget(label_master)
        
        label_connexion_local = QLabel(f"ecoute sur: 0.0.0.0:{self.port_client}")
        label_connexion_local.setStyleSheet("color: #94a3b8; font-size: 11px;")
        bar_cote.addWidget(label_connexion_local)
        
        bar_cote.addStretch()
        
        bouton_rafraiche = QPushButton("🔄️ Actualiser les routeurs")
        bouton_rafraiche.clicked.connect(self.actualise_routeurs)
        bar_cote.addWidget(bouton_rafraiche)

        zone_chat = QVBoxLayout()
        zone_chat.setContentsMargins(0, 0, 0, 0)
        
        entête = QHBoxLayout()
        titre = QLabel("💬 Messages Chiffrés")
        titre.setStyleSheet("""
            color: #f8fafc; 
            font-size: 16px; 
            font-weight: bold;
            padding: 15px;
        """)
        entête.addWidget(titre)
        entête.addStretch()
        
        clear_btn = QPushButton("Effacer")
        clear_btn.clicked.connect(self.chat_clear)
        clear_btn.setFixedWidth(80)
        entête.addWidget(clear_btn)
        
        zone_chat.addLayout(entête)
        
        self.display_de_chat = QTextEdit()
        self.display_de_chat.setObjectName("ChatDisplay")
        self.display_de_chat.setReadOnly(True)
        zone_chat.addWidget(self.display_de_chat)
        
        layout_input = QHBoxLayout()
        layout_input.setContentsMargins(15, 10, 15, 15)
        
        self.input_du_message = QLineEdit()
        self.input_du_message.setPlaceholderText("Tapez votre message...")
        self.input_du_message.setFixedHeight(45)
        self.input_du_message.returnPressed.connect(self.envoie_message)
        
        bouton_envoie = QPushButton("Envoyer")
        bouton_envoie.setFixedWidth(100)
        bouton_envoie.setFixedHeight(45)
        bouton_envoie.clicked.connect(self.envoie_message)
        
        layout_input.addWidget(self.input_du_message)
        layout_input.addWidget(bouton_envoie)
        
        zone_chat.addLayout(layout_input)

        layout_principal.addWidget(barre_coté_principale)
        layout_principal.addLayout(zone_chat)
        self.setCentralWidget(pièce_centrale)
        
        self.bar_de_status = QStatusBar()
        self.bar_de_status.showMessage(f"Client actif sur le port {self.port_client}")
        self.setStatusBar(self.bar_de_status)

    def valide_ip(self, texte_ip: str) -> bool:
        """
        Valide l'adresse IP entrée et met à jour l'interface

        Args:
            texte_ip (str): L'adresse IP entrée par l'utilisateur
        """
        texte_ip = texte_ip.strip()
        
        if not texte_ip:
            self.label_erreur_ip.setText("")
            self.label_erreur_ip.setVisible(False)
            self.ip_destination.setStyleSheet("""
                background-color: #1e293b; 
                color: #f1f5f9; 
                border: 2px solid #475569;
                border-radius: 6px; 
                padding: 8px;
                font-size: 12px;
            """)
            return False
        
        try:
            parties: list[str] = texte_ip.split('.')
            if len(parties) != 4:
                raise ValueError("L'adresse IP doit contenir 4 octets")
 
            ip = list(map(str, texte_ip.split('.')))

            for nombre in ip:
                if int(nombre) < 0 or int(nombre) > 255:
                    return False
            
            socket.inet_aton(texte_ip)
            
            self.label_erreur_ip.setText("")
            self.label_erreur_ip.setVisible(False)
            self.ip_destination.setStyleSheet("""
                background-color: #1e293b; 
                color: #10b981; 
                border: 2px solid #10b981;
                border-radius: 6px; 
                padding: 8px;
                font-size: 12px;
            """)
            return True
            
        except (ValueError, socket.error) as e:
            error_msg = str(e)
            if "inet_aton" in error_msg:
                error_msg = "Format d'adresse IP invalide"
            
            self.label_erreur_ip.setText(f"⚠ {error_msg}")
            self.label_erreur_ip.setVisible(True)
            self.ip_destination.setStyleSheet("""
                background-color: #1e293b; 
                color: #ef4444; 
                border: 2px solid #ef4444;
                border-radius: 6px; 
                padding: 8px;
                font-size: 12px;
            """)
            return False

    def setup_ecoute(self):
        """
        Configure le thread d'écoute des messages entrants
        """
        self.ecouteur = ÉcouteClient(self.port_client)
        self.ecouteur.message_recu.connect(self.affichage_message_recu)
        self.ecouteur.start()

    def affichage_message_recu(self, message):
        """Format les messages recus dans le chat display"""
        temp_actuel = QDateTime.currentDateTime().toString("HH:mm:ss")
        html = f"""
        <div style="margin: 8px 0;">
            <div style="color: #64748b; font-size: 9pt;">[{temp_actuel}]</div>
            <div style="background: #1e293b; padding: 10px; border-radius: 8px; margin: 5px 0;">
                <span style="color: #f59e0b;"><b>Distant:</b></span>
                <span style="color: #e2e8f0;"> {message}</span>
            </div>
            <div style="margin-left: 10px; color: #94a3b8; font-size: 9pt;">
                ↻ Message reçu
            </div>
        </div>
        """
        self.display_de_chat.append(html)
        
        barre_de_scrolle = self.display_de_chat.verticalScrollBar()
        barre_de_scrolle.setValue(barre_de_scrolle.maximum())

    def chat_clear(self):
        """
        Méthode simple qui efface le contenu du chat display
        """
        self.display_de_chat.clear()

    def actualise_routeurs(self):
        """
        Recupère la liste des routeurs depuis le master et met a jour l'interface
        """
        self.bar_de_status.showMessage("Actualisation des routeurs...")
        routers = self.recois_routeurs()
        if routers:
            self.bar_de_status.showMessage(f"{len(routers)} routeurs disponibles.")

    def enregistre_client(self):
        """
        Enregistre le client auprès du serveur master
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(self.addr_master)
            s.send(f"ENREGISTREMENT_CLIENT|{socket.gethostname()}|{self.port_client}".encode())
            s.close()
        except: self.display_de_chat.append("<i>Serveur Master hors ligne</i>")

    def recois_routeurs(self) -> list[dict]:
        """
        Récupère la liste des routeurs depuis le master
        
        Returns:
            list[dict]: Liste des routeurs avec leurs informations
        """
        try:
            s: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(self.addr_master)
            s.send("LISTE_ROUTEURS".encode())
            rep: str = s.recv(65356).decode().split('|')[1]
            s.close()
            routeurs: list[dict] = []
            for r in rep.split(';'):
                if not r:
                    continue
                p = r.split(':')
                routeurs.append({"id":p[0],"ip":p[1],"port":int(p[2]),"key":(int(p[3]),int(p[4]))})
            print(f"[INFO] {len(routeurs)} routeurs reçus du master.")
            return routeurs
        except Exception as e:
            print(f"[ERREUR RECEPTION ROUTEURS] {e}") 
            return []

    def envoie_message(self):
        """
        Envoie un message via le réseau de routeurs
        """
        msg: str = self.input_du_message.text()
        if not msg:
            return

        dest_ip = self.ip_destination.text()
        if not self.valide_ip(dest_ip):
            self.display_de_chat.append("<span style='color:#ef4444'>❌ Adresse IP invalide. Veuillez corriger l'adresse IP avant d'envoyer.</span>")
            return
        
        nombre_sauts = self.sauts.value()
    
        if nombre_sauts == 0:
            try:
                dest_port = int(self.port_destination.text())
                
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5.0)
                s.connect((dest_ip, dest_port))
                s.send(f"MESSAGE|{msg}".encode())
                s.close()
                
                temp_actuel = QDateTime.currentDateTime().toString("HH:mm:ss")
                html = f"""
                <div style="margin: 8px 0;">
                    <div style="color: #64748b; font-size: 9pt;">[{temp_actuel}]</div>
                    <div style="background: #0c4a6e; padding: 10px; border-radius: 8px; margin: 5px 0;">
                        <span style="color: #38bdf8;"><b>Moi:</b></span>
                        <span style="color: #e2e8f0;"> {msg}</span>
                    </div>
                    <div style="margin-left: 10px; color: #22c55e; font-size: 9pt;">
                        ✓ Message envoyé directement à {dest_ip}:{dest_port}
                    </div>
                </div>
                """
                self.display_de_chat.append(html)
                self.input_du_message.clear()
            except Exception as e:
                print(f"Erreur d'envoi direct: {e}")
                temp_actuel = QDateTime.currentDateTime().toString("HH:mm:ss")
                html = f"""
                <div style="margin: 8px 0;">
                    <div style="color: #64748b; font-size: 9pt;">[{temp_actuel}]</div>
                    <div style="background: #0c4a6e; padding: 10px; border-radius: 8px; margin: 5px 0;">
                        <span style="color: #38bdf8;"><b>Moi:</b></span>
                        <span style="color: #e2e8f0;"> {msg}</span>
                    </div>
                    <div style="margin-left: 10px; color: #ef4444; font-size: 9pt;">
                        ✗ Échec de l'envoi direct: {str(e)[:50]}...
                    </div>
                </div>
                """
                self.display_de_chat.append(html)
            return
    
        liste_r: list[dict] = self.recois_routeurs()
        
        if len(liste_r) < nombre_sauts:
            self.display_de_chat.append("<span style='color:red'>Pas assez de routeurs !</span>")
            return

        chemin: list = random.sample(liste_r, nombre_sauts)
        message_envoye: str = f"{self.ip_destination.text()}|{self.port_destination.text()}|{msg}"
        
        for i in range(len(chemin)-1, -1, -1):
            r: int = chemin[i]
            if i == len(chemin)-1:
                prochain_saut = "FINALE|0"
            else:
                prochain_saut = f"{chemin[i+1]['ip']}|{chemin[i+1]['port']}"
            message_envoye = self.cipher.encrypt(f"{prochain_saut}|{message_envoye}", r["key"])

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((chemin[0]["ip"], chemin[0]["port"]))
            s.send(message_envoye.encode())
            s.close()
            temp_liste_routeur: list = []
            for r in chemin:
                temp_liste_routeur.append(r['id'])
            
            temp_actuel = QDateTime.currentDateTime().toString("HH:mm:ss")
            
            html = f"""
            <div style="margin: 8px 0;">
                <div style="color: #64748b; font-size: 9pt;">[{temp_actuel}]</div>
                <div style="background: #0c4a6e; padding: 10px; border-radius: 8px; margin: 5px 0;">
                    <span style="color: #38bdf8;"><b>Moi:</b></span>
                    <span style="color: #e2e8f0;"> {msg}</span>
                </div>
                <div style="margin-left: 10px; color: #22c55e; font-size: 9pt;">
                    ✓ Message envoyé (via {', '.join(temp_liste_routeur)})
                </div>
            </div>
            """
            self.display_de_chat.append(html)
            self.input_du_message.clear()
        except Exception as e:
            print(f"Erreur d'envoi: {e}")
            temp_actuel = QDateTime.currentDateTime().toString("HH:mm:ss")
            html = f"""
            <div style="margin: 8px 0;">
                <div style="color: #64748b; font-size: 9pt;">[{temp_actuel}]</div>
                <div style="background: #0c4a6e; padding: 10px; border-radius: 8px; margin: 5px 0;">
                    <span style="color: #38bdf8;"><b>Moi:</b></span>
                    <span style="color: #e2e8f0;"> {msg}</span>
                </div>
                <div style="margin-left: 10px; color: #ef4444; font-size: 9pt;">
                    ✗ Échec de l'envoi
                </div>
            </div>
            """
            self.display_de_chat.append(html)

    def closeEvent(self, event: QCloseEvent):
        """Handle window close - clean up threads"""
        if hasattr(self, 'ecouteur'):
            self.ecouteur.stop()
        event.accept()

def help():
    """
    Affiche le message d'aide pour l'utilisation du client, je ne pense pas qu'il y ait besoin de plus d'explications.
    """
    print("""Client - Utilisation:\n
            \tpython client.py [PORT_CLIENT] [IP_MASTER] [PORT_MASTER]\n
          
            \t--------------------------------------------\n
            \tOptions:\n
            \t\t-h, --help: Affiche ce message d'aide\n
            \t\t-p, --client-port: Port d'écoute local (defaut: 8001)\n
            \t\t-m, --master-ip: Adresse IP du serveur master (defaut: 127.0.0.1)\n
            \t\t-mp, --master-port: Port du serveur master (defaut: 9000)\n

            \tArguments:\n
            \t\tPORT_CLIENT: Port d'écoute local (Par defaut: 8001)\n
            \t\tIP_MASTER: Adresse du serveur master (Par defaut: 127.0.0.1)\n
            \t\tPORT_MASTER: Port du serveur master (defaut: 9000)\n
          
            \tExemples:
            \t\tpython client.py                      # Port 8001, master local:9000\n
            \t\tpython client.py 8001                 # Port 8001, master local:9000\n
            \t\tpython client.py 8001 -m 192.168.1.100   # Port 8001, master 192.168.1.100:9000\n
            \t\tpython client.py 8001 -m 192.168.1.100 -mp 9999  # Master sur port 9999\n
        """)
    sys.exit(0)

if __name__ == "__main__":
    application = QApplication(sys.argv)
    # Permet de fermer l'application avec Ctrl+C dans le terminal car PyQt capture le signal autrement et empêche la fermeture depuis le terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Paramêtres par défaut
    client_port: int = 8001
    master_ip: str = "127.0.0.1"
    master_port: int = 9000
    
    match len(sys.argv):
        case 1:
            pass  # Utilise les valeurs par défaut
        case 2:
            try:
                client_port = int(sys.argv[1])
            except ValueError:
                print(f"Port client invalide: {sys.argv[1]}. Utilisation du port par défaut: {client_port}")
        case 4:
            if sys.argv[2] != "-m" and sys.argv[2] != "--master-ip":
                print(f"L'option {sys.argv[2]} est invalide.")
                help()
            try:
                client_port = int(sys.argv[1])
                master_ip = sys.argv[3]
            except ValueError:
                print(f"Port client invalide: {sys.argv[1]}. Utilisation du port par défaut: {client_port}")
        case 6:
            if (sys.argv[2] != "-m" and sys.argv[2] != "--master-ip") or (sys.argv[4] != "-mp" and sys.argv[4] != "--master-port"):
                help()
            try:
                client_port = int(sys.argv[1])
                master_ip = sys.argv[3]
                master_port = int(sys.argv[5])
            except ValueError:
                print(f"Port client invalide: {sys.argv[1]}. Utilisation du port par défaut: {client_port}")
                print(f"Port master invalide: {sys.argv[5]}. Utilisation du port par défaut: {master_port}")
        case _:
            print(len(sys.argv))
            help()
            sys.exit(1)

    # Pour le débuggage
    print(f"""Lancement du Client:\n- Port client:     {client_port}\n - Serveur master:  {master_ip}:{master_port}""")
    
    try:
        ex: ApplicationClient = ApplicationClient(master_ip, master_port, client_port)
        ex.show()
        sys.exit(application.exec())
    except Exception as e:
        print(f"Erreur lors du émarrage: {e}")
        sys.exit(1)