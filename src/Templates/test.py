"""
Script de test
"""

import time
import threading
from client import Client

def test_connexion_directe():
    """
    Test 1: Connexion directe
    """
    print("étape 1: connexion directe entre 2 clients")
    print("=" * 50)
    
    # Création des 2 clients
    a = Client("Client_A")
    b = Client("Client_B", port=9002)
    
    # Démarrage de l'écoute
    if a.ecoute():
        print("✅ Client_A en écoute sur port 9001")
    else:
        print("❌ Erreur Client_A")
        return
        
    if b.ecoute():
        print("✅ Client_B en écoute sur port 9002")
    else:
        print("❌ Erreur Client_B")
        return
    
    # Attente que les sockets soient prêts
    time.sleep(1)
    
    # Test 1: Client_A envoie à Client_B
    print("\n📤 Test: Client_A -> Client_B")
    success1 = a.envoie_message("localhost", 9002, "Bonjour de Client_A!")
    print("✅ Message envoyé" if success1 else "Échec envoi")
    
    time.sleep(1)
    
    # Test 2: Client_B envoie à Client_A
    print("\n📤 Test: Client_B -> Client_A")
    success2 = b.envoie_message("localhost", 9001, "Salut de Client_B!")
    print("✅ Message envoyé" if success2 else "Échec envoi")
    
    time.sleep(1)
    
    # Affichage des historiques
    print("\n" + "=" * 50)
    print("📋 HISTORIQUE Client_A:")
    for msg in a.historique_des_messages:
        print(f"\t{msg}")
    
    print("\n📋 HISTORIQUE Client_B:")
    for msg in b.historique_des_messages:
        print(f"\t{msg}")
    
    a.stop()
    b.stop()

def test_avec_threads():
    """
    Test 2: Communication simultanée
    """
    print("\nTEST 2: Communication simultanée")
    print("=" * 50)
    
    c = Client("Client_C", port=9003)
    d = Client("Client_D", port=9004)
    
    c.ecoute()
    d.ecoute()
    
    # On attend que les sockets ils sont prês
    time.sleep(1)
    
    def envoyer_messages_paralleles():
        """Envoi de messages en parallèle"""
        threads: list[threading.Thread] = []
        
        # C vers D
        for i in range(3):
            t: threading.Thread = threading.Thread(target=c.envoie_message, args=("localhost", 9004, f"Message {i+1} de C"))
            threads.append(t)
            t.start()
        
        # D vers C
        for i in range(3):
            t: threading.Thread = threading.Thread(target=d.envoie_message, args=("localhost", 9003, f"Message {i+1} de D"))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
    
    # Lancement des envois parallèles
    envoyer_messages_paralleles()
    
    time.sleep(2)
    
    print("\nRésumé après communication parallèle:")
    print(f"Client_C: {len(c.historique_des_messages)} messages reçus")
    print(f"Client_D: {len(d.historique_des_messages)} messages reçus")
    
    c.stop()
    d.stop()

if __name__ == "__main__":
    test_connexion_directe()
    test_avec_threads()
    
    print("\nTous les tests sont terminés!")