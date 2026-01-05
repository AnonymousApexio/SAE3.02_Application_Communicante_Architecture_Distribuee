Projet SAE 3.02 : Architecture Multi-Distribuée & Routage en Oignon
Ce projet est une implémentation d'un réseau de routage en oignon (type Tor) développé en Python. Il a pour but de démontrer les principes d'anonymisation des flux réseaux via une architecture distribuée comprenant un serveur maître (annuaire), des routeurs relais et des clients communicants.

# Table des Matières:
- [Architecture](#-architecture)

- [Fonctionnalités](#fonctionnalités)

- [Prérequis](#-prérequis)

- [Installation](#-Installation)

- [Configuration de la Base de Données](#Configuration-de-la-Base-de-Données)

- [Utilisation](#-utilisation)

- [Structure du projet](#structure-du-projet)

- [Vidéo de démo](#vidéo-de-démo)

- [Auteur](#auteur)

# 🏗 Architecture:
Le système repose sur trois composants principaux (Voir [Documentation Technique](./Documentation/Documentation_Technique_SAE_302.pdf)):

## Le Master (Annuaire):
- Gère une base de données MariaDB des routeurs actifs et des logs.
- Fournit la liste des routeurs et leurs clés publiques aux clients.
- Surveille le réseau via une interface graphique.

## Les Routeurs (Relais):
- S'enregistrent auprès du Master.
- Relayent les paquets chiffrés.
- Effectuent un chiffrement/déchiffrement RSA.

## Les Clients:
- Récupèrent la topologie du réseau depuis le Master.
- Construisent un circuit aléatoire.
- Chiffrent le message en couches successives (Oignon).
- Envoient le message à travers le circuit.

# Fonctionnalités:
- Cryptographie RSA: Implémentation manuelle de l'algorithme RSA (génération de clés, chiffrement/déchiffrement) sans librairie de crypto externe.
- Protocole Custom: Communication via Sockets TCP bruts avec un protocole textuel délimité. Voir documentation technique (Documentation/)
- Anonymisation: Le système garantit que les routeurs intermédiaires ne connaissent pas les deux extrémités de la communication.
- Interface Graphique: GUI moderne réalisée avec PyQt6 pour le Client et le Master.
- Persistance: Stockage des clés et logs dans MariaDB.

# 📋 Prérequis:
- Python 3.11 ou supérieur.

Pour Windows:
Installez depuis: https://www.python.org/downloads/


Pour Linux:
Utilisez votre gestionnaire de paquets. Par exemple, sur Debian/Ubuntu:
```bash
sudo apt update
sudo apt install python3 python3-venv pip
```
Voir la version de votre installation avec:
```bash
python --version
```

ou
```bash
python3 --version
```

- Dépendance Python: Voir requirements.txt pour la liste complète.

- MariaDB Serveur installé et lancé.

Voir https://mariadb.org/download/ pour les instructions d'installation.

- Système d'exploitation: Windows ou Linux (Testé sur VM).

# 🚀 Installation:

Installer Git si ce n'est pas déjà fait:
# Windows
Téléchargez depuis: https://git-scm.com/install/windows
https://git-scm.com/install/linux
https://git-scm.com/install/mac

Note: Attention, lors de l'installation, choisissez d'ajouter Git au PATH pour un usage en ligne de commande. Et ouvrez Powershell ou CMD APRÈS l'installation pour que les changements soient pris en compte.

# Linux
```bash
apt install git
```
# Mac
```bash
brew install git
```

Cloner le dépôt:
```bash
git clone https://github.com/AnonymousApexio/SAE3.02_Application_Communicante_Architecture_Distribuee.git
cd SAE3.02_Application_Communicante_Architecture_Distribuee
Installer les dépendances: Je vous recommande d'utiliser un environnement virtuel.
```

# Windows
Note: Attention sous Windows, Powershell peut nécessiter l'activation de l'exécution de scripts. Ouvrez Powershell en mode administrateur et exécutez:
```bash
Set-ExecutionPolicy Unrestricted -Scope CurrentUser -Force
```

```bash
python -m venv venv
.\venv\Scripts\activate
```

# Linux / Mac
```bash
python3 -m venv venv
source venv/bin/activate
```

# Installation
Windows:
```bash
pip install -r .\requirements.txt
```
Linux / Mac:
```bash
pip install -r requirements.txt
```

# Configuration de la Base de Données
### Note: La procédure suivante assume que vous souhaitez installé tout le système par vous-même (Master, Routeurs, Clients). Pour des tests locaux, tout peut être lancé sur une seule machine avec des ports différents. Si vous avez déjà un serveur MariaDB/MySQL fonctionnel, et que vos routeurs sont activés (Comme par exemple si vous utilisé l'infrastructure d'une autre personne), vous pouvez directement passer à la section 3 de [Utilisation](#-Utilisation) et juste activé les clients.

### Note: Je recommende d'utiliser MariaDB/MySQL sur Windows. 

Créer la base de données et les tables: Connectez-vous à votre console MariaDB/MySQL et exécutez les commandes suivantes (Copiez-collez tout):

```SQL

CREATE DATABASE IF NOT EXISTS routage_couche;
USE routage_couche;

-- Table pour les routeurs
CREATE TABLE IF NOT EXISTS routeurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    router_id VARCHAR(50) UNIQUE NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    port INT NOT NULL,
    public_key_n TEXT NOT NULL,
    public_key_e TEXT NOT NULL,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAM
);

-- Table pour les logs anonymisés
CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(50),
    details TEXT
);
```
Note: Si vous utilisez une authentification Windows/Plugin, assurez-vous de créer un utilisateur avec mysql_native_password.

Configurer la connexion: Ouvrez le fichier src/Configuration/config.conf et adaptez les identifiants:

```ini
host=<ip_machine_BDD>
user=<votre_utilisateur>
password=<votre_mot_de_passe>
db_name=routage_couche
```

Note: Si vous recevez l'erreur "Erreur SQL: 2003: Can't connect to MySQL server on ':3306' (Errno 11001: getaddrinfo failed)", vos identifiants sont incorrecte.

# 🎮 Utilisation

## Troubleshooting Graphique sous Linux:
Note: Attention, si vous utilisez une machine linux, vous pourriez tombez sur des problèmes d'interface graphique avec PyQt6 (Problèmes entre le moteur Wayland ou X11). Si cela arrive. Essayez de réinstaller PyQt6 via pip:
```bash
pip uninstall PyQt6
pip install PyQt6
```

### Note: Normalement si vous n'essayez pas d'exécuter l'interface graphique avec l'utilisateur root (Qui peut casser Qt), tout devrait bien fonctionner. Mais si vous avez des problèmes d'affichage sous Linux, essayez d'exécuter les commandes suivantes dans le terminal avant de lancer le client.py:

Si cela ne fonctionne pas, essayez d'installer les dépendances graphiques manquantes via votre gestionnaire de paquets. Par exemple, sur Debian/Ubuntu:
```bash
nano /etc/gdm3/daemon.conf
```

Décommentez la ligne:
```ini
WaylandEnable=false
```

Et faites:
```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)

export WAYLAND_DISPLAY=wayland-0
export QT_QPA_PLATFORM=wayland

python3 src/Templates/client.py 8001 -m <IP_MASTER>
```

## Démarrage des Composants:

L'ordre de démarrage est important: Master -> Routeurs -> Clients.

1. Démarrer le Serveur Master sur votre première machine:
Le Master doit être lancé en premier pour accepter les enregistrements.

```Bash

# Lance le master sur le port 9000 (par défaut)
python src/Composants/master.py -p 9000
```
Note: Le master utilise par défaut le port 9000. Si vous modifiez ce port, assurez-vous d'ajuster les paramètres des routeurs et clients en conséquence. 
Le master doit toujours être arrêté avec Ctrl+C dans le terminal pour assurer une fermeture propre des connexions. (Fermer la fenêtre GUI ne suffit pas)

2. Démarrer les Routeurs sur votre seconde machine (ou plusieurs machines):
Lancez plusieurs routeurs (minimum 3 pour un test réaliste) dans des terminaux et/ou machines séparés.

```Bash
# Syntaxe : python router.py [ID] -m [IP_MASTER] -mp [PORT_MASTER] -p [PORT_LOCAL]

# Routeur 1
python src/Templates/router.py R1 -m 127.0.0.1 -mp 9000 -p 8010

# Routeur 2
python src/Templates/router.py R2 -m 127.0.0.1 -mp 9000 -p 8011

# Routeur 3
python src/Templates/router.py R3 -m 127.0.0.1 -mp 9000 -p 8012
```

Les routeurs doivent également être arrêtés proprement avec Ctrl+C dans le terminal.

3. Démarrer les Clients sur votre troisième machine (ou plusieurs machines):
Lancez au minimum deux clients (un émetteur, un destinataire). (Démarrage en CLI mais utilisation via GUI)
```Bash
# Syntaxe : python client.py [PORT_LOCAL] -m [IP_MASTER] -mp [PORT_MASTER]

# Si vous avez modifié le port du Master, ajustez -mp en conséquence sinon il utilise 9000 par défaut.

# Client A (Port 8001)
python src/Templates/client.py 8001 -m 127.0.0.1

# Client B (Port 8002)
python src/Templates/client.py 8002 -m 127.0.0.1
```


# 📶 Tester la communication:
Sur l'interface du Client A:
- Entrez l'IP 127.0.0.1 (Ou celle de la machine sur laquel vous souhaitez l'envoyez) et le port 8002 (celui du Client B).

- Choisissez le nombre de sauts (ex: 3).

- Écrivez un message et cliquez sur Envoyer.

- Observez les logs dans les terminaux des routeurs: vous verrez le paquet transiter de manière chiffrée.

- Le Client B recevra le message déchiffré.

# Structure du projet:

```bash
└── 📁SAE3.02_Application_Communicante_Architecture_Distribuee
    └── 📁Documentation
        ├── Documentation_Technique_SAE_302.pdf # Documentation technique de la SAE
        ├── Fiche_Individuelle_SAE_302.pdf # Liste des compétences apprise/améliorer et conclusion de la SAE
    └── 📁src
        └── 📁Composants
            ├── __init__.py
            ├── Algorithme_de_chiffrage.py # Module du chiffrage RSA
            ├── master.py # Programme du serveur maître
        └── 📁Configuration
            ├── config.conf # Fichier de configuration de la base de donnée
        └── 📁Templates
            ├── __init__.py
            ├── client.py # Template pour le lancement d'un client
            ├── router.py # Template pour le lancement d'un routeur
        ├── __init__.py
    ├── README.md # La page que vous êtes entrain de lire
    └── requirements.txt # La liste des dépendances à installer
```

# Vidéo de démo:


Voir Documentation/Vidéo_SAE_302.mp4


# Auteur
Projet réalisé dans un cadre académique de la SAÉ 3.02 (IUT Réseaux & Télécoms).

Amory Ryan - Maïtre d'oeuvre du projet
