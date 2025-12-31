Projet SAE 3.02 : Architecture Multi-Distribuée & Routage en Oignon
Ce projet est une implémentation d'un réseau de routage en oignon (type Tor) développé en Python. Il a pour but de démontrer les principes d'anonymisation des flux réseaux via une architecture distribuée comprenant un serveur maître (annuaire), des routeurs relais et des clients communicants.

# Table des Matières:
- [Architecture](#🏗-Architecture)

- [Fonctionnalités](#Fonctionnalités)

- [Prérequis](#-Prérequis)

- [Installation](#-Installation)

- [Configuration de la Base de Données](#Configuration-de-la-Base-de-Données)

- [Utilisation](#-Utilisation)

- [Auteur](#-Auteurs)

# 🏗 Architecture:
Le système repose sur trois composants principaux (Voir [Documentation Technique](./Documentation/)):

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

Installez depuis: https://www.python.org/downloads/

Voir la version de votre installation avec:
```bash
python --version
```

- Dépendance Python: Voir requirements.txt pour la liste complète.

- MariaDB Serveur installé et lancé.

Voir https://mariadb.org/download/ pour les instructions d'installation.

- Système d'exploitation: Windows ou Linux (Testé sur VM).

# 🚀 Installation:
Cloner le dépôt:
```bash
git clone https://github.com/AnonymousApexio/SAE3.02_Application_Communicante_Architecture_Distribuee.git
cd SAE3.02_Application_Communicante_Architecture_Distribuee
Installer les dépendances: Je vous recommande d'utiliser un environnement virtuel.
```

# Windows
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
pip install -r requirements.txt


# Configuration de la Base de Données
Créer la base de données et les tables: Connectez-vous à votre console MariaDB/MySQL et exécutez les commandes suivantes:

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
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
host=<votre_hôte>
user=<votre_utilisateur>
password=<votre_mot_de_passe>
db_name=routage_couche
```


# 🎮 Utilisation
L'ordre de démarrage est important: Master -> Routeurs -> Clients.

1. Démarrer le Serveur Master
Le Master doit être lancé en premier pour accepter les enregistrements.

```Bash

# Lance le master sur le port 9000 (par défaut)
python src/Composants/master.py -p 9000
```


2. Démarrer les Routeurs
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

3. Démarrer les Clients:  
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

# 👥 Auteurs
Projet réalisé dans le cadre de la SAÉ 3.02 (IUT Réseaux & Télécoms).

Amory Ryan - Maïtre d'oeuvre du projet