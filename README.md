#  		Génération de Matrice de conformité 

## Equipe
- [**@D4CJ**](https://github.com/D4CJ) Dimitar DIMITROV
- [**@JasperPetit**](https://github.com/JasperPetit) Jasper PETIT

## Sommaire
- [Génération de Matrice de conformité](#génération-de-matrice-de-conformité)
  - [Sommaire](#sommaire)
  - [Description :](#description-)
  - [Quick start :](#quick-start-)
    - [Prérequis](#prérequis)
    - [Lancement avec containers](#lancement-avec-containers)
    - [Lancement localhost](#lancement-localhost)
  - [Maintenance](#maintenance)
    - [Relancer l'application](#relancer-lapplication)
    - [Installer de nouveaux modèles](#installer-de-nouveaux-modèles)
    - [Commandes pratiques](#commandes-pratiques)
  - [Explication du fonctionnement](#explication-du-fonctionnement)
    - [Déroulement communication](#déroulement-communication)
    - [Requirements](#requirements)

## Description : 

Infodip est une société française qui reçoit des commandes de PC qu'elle doit mettre en rack ou en baie pour ses clients. Le but de ce projet est de pouvoir générer une matrice de conformité à partir d’un cahier des charges donné par le client. L’accent a été mis sur la confidentialité, on ne peut pas passer par des IA comme ChatGpt, Gemini ou encore Claude pour générer ces matrices, c’est pour cela qu’on a utilisé des solutions open source.

Ce projet, va être mis à disposition au service commerciale pour leur faire gagner du temps sur cette tâche. 

Une première partie a été faite ultérieurement, la génération de matrices à partir d’un fichier de type tableurs (xlsx, xlsm). Notre objectif était de pouvoir générer cette matrice via un cahier des charges de type document et du texte. Puis implémenter la première partie avec la nôtre dans une application.

## Quick start :

### Prérequis 
- Avoir git sur la machine et cloner le projet avec la commande : 
    
        git clone https://github.com/JasperPetit/Projet2-Infodip.git

- Avant de démarrer l’application veillez à faire attention que la GPU de la DGX Spark soit à jour. Pour cela, accédez à http://localhost:11000/ ou cherchez DGX DASHBOARD dans les fichiers de l’ordinateur, puis vérifiez qu’il n’y a pas de mise à jour à réaliser. Attendez quelques secondes sur la page, l'icône de mise à jour peut prendre du temps à apparaître (cliquer sur le bouton “settings” peut parfois le faire apparaître). S'il y a une mise à jour, faites-la et la machine redémarrera tout seule à la fin. Veillez bien à vous reconnecter à la machine.

- Dans le fichier main.py, assurez vous que la bonne ligne soit commentée et que l'autre non
- Dans le fichier .env.example, decommanter la ligne de la variable FLASK_SECRET_KEY et remplacfer mdp par le mot de passe secret de votre choix. Ensuite, renommer .env.example en .env

### Lancement avec containers

Pour lancer l'application en local sur la dgx afin qu'elle soit accessible à distance veuillez :
 
 - Rentrer dans le répertoire de l'application (avec main.py, .dockerfile et docker-compose.yml)

 - Ouvrez main.py et faites en sorte qu'il ressemble a ceci :
 ```python
 from app import app
 from waitress import serve

 if __name__ == '__main__':
    #app.run(host="localhost", port=8000, debug=True)
    serve(app, host='0.0.0.0', port=5000, threads=4)
 ```

 - Exécuter la ligne suivante dans le terminal :
           
```bash
[sudo] docker compose up -d --build #sudo n’est pas obligatoire si vous avez les droits pour Docker
```
 - Le container est maintenant lancé et l'application est accessible sur le réseau local. Vous pouvez y accéder avec l'URL : 
 ```
 http://<adresse ip>/5000
```
- Vous pouvez retrouver votre adresse ip en tapant dans le terminal :
  ``` bash 
  ifconfig
  ```
  Pensez bien à adapter l'adresse ip en fonction du réseau dans lequel vous êtes, ce n'est pas la même pour l'accès wifi et ethernet.


### Lancement localhost

Si vous souhaitez accéder à l'application uniquement sur la machine afin d'essayer des modifications alors il vous faudra :

- Vous rendre dans le répertoire de l'application
- Ouvrez main.py et faites en sorte qu'il ressemble à ceci :
 ```python
 from app import app
 from waitress import serve

 if __name__ == '__main__':
    app.run(host="localhost", port=8000, debug=True)
    #serve(app, host='0.0.0.0', port=5000, threads=4)
 ```
- Exécutez les lignes suivantes dans le terminal :
```bash
#On créer la venv
python3 -m venv .venv
#On active la venv 
source .venv/bin/activate
#On télécharge les requirements dans la venv
pip install -r requirements.txt
#On lance le site en local
python3 main.py
```
- Le site devrait être accessible sur http://localhost:5000/
  
- Pour arrêter l'application, vous devez exécuter ctrl+c dans le terminal.
  
- Une fois que vous avez créé la venv vous n'aurez plus a exécuter toutes les lignes pour lancer l'application, mais seulement 
```bash
 source .venv/bin/activate
 python3 main.py
```

## Maintenance

### Relancer l'application
*Nous ne traiterons dans les lignes suivantes que le cas où l'application est lancée avec docker, car c'est le cas d'utilisation le plus courant.*

Si l'application n'est plus accessible en ligne ou que vous avez apporté des modifications au code, vous devrez alors vous rendre dans le répertoire de l'application et exécuter la ligne suivante dans le terminal :
```bash
[sudo] docker compose up -d --build
```
Vous pouvez vérifier que les deux containers roule bien avec la commande :
```bash
docker ps
```

### Installer de nouveaux modèles

Si vous souhaitez essayer de nouveaux modèles, exécutez dans le terminal :
```bash
docker exec -it ollama_projet_2 ollama pull <mon_modele>
```

Rendez-vous ensuite dans doc.py et doc_projet_1.py et changer la constante MODEL_LLM :
```python
MODEL_LLM = <mon_modele>
```

### Commandes pratiques 

Consulter la liste des modèles installés :
```bash
docker exec -it ollama_projet_2 ollama list
```

Consulter les logs de l'application : 
```bash
docker logs app_projet_2
```

## Explication du fonctionnement

Ce code est divisé en 2 parties, le backend et le frontend. Pour ce projet, nous avons décidé d’utiliser Flask pour le côté serveur, ce qui nous permet de relier du code python avec une interface en HTML, CSS et JS.

Dans le fichier docker-compose.yml, nous définissons 2 containers qui sont utilisés par l'application, app_projet_2 qui est l'ensemble de notre code et ollama_projet_2 qui est le container contenant ollama.


Le serveur Flask n'est pas conçu pour un environnement de production. Bien qu'il soit pratique pour le développement, il n'est pas optimisé pour la sécurité ou les performances réelles. Pour ce projet, le choix s'est porté sur Waitress. C’est un serveur web de production (WSGI) qui agit comme intermédiaire entre le réseau et l'application Flask. Son rôle principal est de gérer de nombreuses requêtes simultanées de manière robuste.

Nous avons décidé de partir sur un système de traitement non-bloquant plutôt que purement synchrone. Un système strictement synchrone aurait convenu pour des requêtes courtes, mais pour des tâches longues comme les nôtres (extraction de texte, utilisation d’un LLM et insertions dans la matrice), l’application serait devenue inutilisable. Le serveur mettrait trop de temps à répondre au navigateur, ce qui finirait par déclencher une erreur Timeout.

Pour régler ce problème, nous avons utilisé le multi-threading. Quand un utilisateur upload un fichier, le contrôleur (indexController.py) ne va pas directement exécuter les fonctions de génération de matrices, mais va plutôt lancer un thread secondaire :

```python
thread = threading.Thread(target=travail_de_lia, args=(ticket_id, file_path, None)) 
thread.start()
```

Une fois ce thread lancé, l’utilisateur est immédiatement redirigé vers une page d’attente. Pendant ce temps, le thread exécute en arrière-plan la fonction travail_de_lia ou travail_de_lia_excel. Comme le cycle de réponse HTTP est terminé, le serveur reste disponible pour d'autres utilisateurs.

Cependant, comme le thread travaille de son côté, il faut un moyen pour que le serveur sache où en est le travail. Puisque les threads partagent la même mémoire que l'application principale, nous avons utilisé un système de tickets couplé à un dictionnaire (resultats_ia = {}) pour stocker et consulter l’état du processus à tout moment.

### Déroulement communication
Lorsque le thread est créé, resultat_ia est initialisé avec la valeur “en cours”. Ensuite, la page d’attente se rafraîchit régulièrement et interroge à chaque fois la route /attente/<ticket_id> pour connaître la valeur du dictionnaire resultat_ia. Si la valeur est {“statut” : “en cours”} alors on reste sur la page d’attente. Si la valeur est  {"statut": "termine", "chemin": chemin_temp} on revient sur la page d’accueil avec le bouton de téléchargement de la matrice de conformité. Sinon, si la valeur est {"status": "doublons", "chemin": chemin_temp, "doublons": liste_doublons} c’est qu’on a trouvé des exigences en doublons et donc ça nous redirige vers la page validation_doublons.

### Requirements
- **ollama :** Nous permet de communiquer avec le modèle de LLM. 
- **pytesseract :** Librairie de l'ocr tesseract, on l'utilise lorsqu'il y a des images dans le pdf.
- **docling :** utilisé dans doc.py pour convertir le document en pdf si besoin ainsi qu'extraire le contenu du document.
 - **tesserocr :** l'ocr tesseract.
 - **flask :** le framework qui nous permet de faire du backend en python. 
 - **sentence_transformers :** Nous permet de faire le test d'embedding pour éviter les doublons dans doc.py.
 - **werkzeug :** nous permet de récupérer de façon sécurisée les noms de fichiers déposés par l'utilisateur. (pas d'espace, etc).
 - **openpyxl :** Utilisé pour ouvrir et remplir l'excel final.
 - **python-dotenv :** Nous permet de récupérer la clé secrète de session contenu dans le .env.
 - **waiteress :** permet a plusieurs personne d'utiliser waiteress en même temps ainsi que de garder l'échange avec le navigateur actif bien que la génération de matrices prenne du temps.
