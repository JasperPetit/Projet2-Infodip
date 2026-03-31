# from flask import Flask, render_template, redirect, url_for, request, send_file, session
# from app import app
# import json
# import app.services.doc as doc  #c'est le doc.py 
# from werkzeug.utils import secure_filename
# import os 
# import time
# from dotenv import load_dotenv

# # UPLOAD_DIRECTORY = 'app/uploads/'

# ALLOWED_EXTENSIONS = set(['.pdf', '.docx', '.txt'])


# DOSSIER_CONTROLLERS = os.path.dirname(os.path.abspath(__file__))

# DOSSIER_APP = os.path.dirname(DOSSIER_CONTROLLERS)

# UPLOAD_DIRECTORY = os.path.join(DOSSIER_APP, 'uploads')

# os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# load_dotenv()

# app.secret_key = os.getenv("FLASK_SECRET_KEY")

# @app.route('/')
# def index():
#     if not request.args.get('actualiser_upload'):

#         session.pop('matrice', None)

#     matrice_generee = session.get('matrice')
#     return render_template('index2.html', excel = matrice_generee)

# @app.route('/upload', methods=['POST'])
# def uploadAndAnalyze():
#         session.pop('matrice', None)
#         file = request.files['document']
        
        
#         if file and file.filename != '': 
#             extension = os.path.splitext(file.filename)[1]
#             if extension not in ALLOWED_EXTENSIONS:
                
#                 return "Le format du fichier n'est pas valide. Veuillez charger un fichier pdf, docx ou txt."
            
#             file_path = os.path.join(UPLOAD_DIRECTORY, secure_filename(file.filename))
#             file.save(file_path)

#             start_time = time.time()
#             text = doc.extraction_sur_mesure(file_path)
#             json_final = doc.ChatOllama(text)
#             chemin_propre = os.path.splitext(file_path)[0]
            
            
#             session['matrice'] = doc.matrice_conformite(json_final, chemin_propre)
            
#             end_time = time.time()
#             print(f"Temps d'exécution de matrice_conformite : {end_time - start_time} secondes")
           
           
#             #session['matrice'] = doc.matrice_conformite(json_final, file_path)
#             os.remove(file_path)
            


           
        
#         else:
#             direct_text = request.form.get('texte_manuel')
#             json_final_txt = doc.ChatOllama(direct_text)
#             file_path = os.path.join(UPLOAD_DIRECTORY, 'texte_manuel.txt')
#             print(file_path)
#             session['matrice'] = doc.matrice_conformite(json_final_txt, file_path)
            

#         return redirect(url_for('index', actualiser_upload=True))
   
   
   
   
# @app.route('/download', methods=['GET'])
# def download():
#         chemin_excel = session.get('matrice')

#         if not chemin_excel:
#             return redirect('/')
        
#         session.pop('matrice', None)

#         return send_file(chemin_excel, as_attachment=True)
        
 
    





from flask import render_template, redirect, url_for, request, send_file, session
from werkzeug.utils import secure_filename
from app import app
import app.services.doc as doc
import os
import threading
import uuid
from dotenv import load_dotenv
import app.services.doc_projet1 as doc_p1


ALLOWED_EXTENSIONS = set(['.pdf', '.docx', '.txt','.xlsx','.xlsm'])
DOCUMENTS_EXTENSION = set(['.pdf', '.docx', '.txt'])
EXCEL_EXTENSION = set(['.xlsx','.xlsm'])


DOSSIER_CONTROLLERS = os.path.dirname(os.path.abspath(__file__))
DOSSIER_APP = os.path.dirname(DOSSIER_CONTROLLERS)
UPLOAD_DIRECTORY = os.path.join(DOSSIER_APP, 'uploads')
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


load_dotenv()
app.secret_key = os.getenv("FLASK_SECRET_KEY")


# Carnet de notes en mémoire pour suivre l'état des analyses
resultats_ia = {}


def travail_de_lia(ticket_id, file_path=None, texte_manuel=None):
    '''
   args :
       - ticket_id : identifiant unique pour le suivi du travail du LLM
       - file_path : chemin du fichier uploadé
       - texte_manuel : texte saisi directement sur l'application
 
   description :


   Une fois que l'utilisateur upload un fichier de type (pdf, docx, txt) ou saisit un texte, cette fonction
   est exécutée dans un thread. Elle utilise les fonction dans doc.py qui permettent de générer la matrice de conformité.
   Le dictionnaire global est mis à jour avec le chemin du fichier Excel généré (ou "erreur").
   '''

    image_ou_tableau = False
    try:
        if file_path:
            text, image_ou_tableau = doc.extraction_sur_mesure(file_path)
            json_final = doc.ChatOllama(text)
            chemin_propre = os.path.splitext(file_path)[0]
            chemin_excel = doc.matrice_conformite(json_final, chemin_propre)
            
        elif texte_manuel:
            json_final = doc.ChatOllama(texte_manuel)
            fichier_txt_path = os.path.join(UPLOAD_DIRECTORY, 'texte_manuel')
            chemin_excel  = doc.matrice_conformite(json_final, fichier_txt_path)
            
        resultats_ia[ticket_id] = resultats_ia[ticket_id] = {
            "status": "termine",
            "chemin": chemin_excel,
            "image_ou_tableau": image_ou_tableau
        }
    except Exception as e:
        print(f"Erreur pendant l'analyse : {e}", flush=True)
        resultats_ia[ticket_id] = {"status": "erreur"}
        
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path) 

def travail_de_lia_excel(ticket_id, file_path, onglets_choisis, liste_machines):
    '''
   args :
       - ticket_id : identifiant unique pour le suivi du travail du LLM
       - file_path : chemin du fichier uploadé
       - texte_manuel : texte saisi directement sur l'application
 
   description :


   Une fois que l'utilisateur upload un fichier de type (pdf, docx, txt) ou saisit un texte, cette fonction
   est exécutée dans un thread. Elle utilise les fonction dans doc.py qui permettent de générer la matrice de conformité.
   Le dictionnaire global est mis à jour avec le chemin du fichier Excel généré (ou "erreur").
   '''

    try:
        outil_table = doc_p1.load_excel(file_path)
        
        outil_table.selected = [True if nom in onglets_choisis else False for nom in outil_table.sheetnames]

        print(f"Début de l'analyse Excel pour les machines : {liste_machines}")
        wb, liste_doublons = doc_p1.build_compliance_matrix(liste_machines, outil_table, file_path)

        nom_fichier_temp = f"matrice_temp_{ticket_id}.xlsx"
        chemin_temp = doc_p1.save_compliance_matrix(wb, nom_fichier_temp)

        if len(liste_doublons) > 0:
            resultats_ia[ticket_id] = {"status": "doublons", "chemin": chemin_temp, "doublons": liste_doublons}
        else:
            resultats_ia[ticket_id] = {"status": "termine", "chemin": chemin_temp}

    except Exception as e:
        print(f"Erreur pendant l'analyse Excel : {e}")
        resultats_ia[ticket_id] = {"status": "erreur"}

    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


@app.route('/')
def index():
    '''
   description : Cette route affiche la page d'accueil. Si la matrice de conformité à été générée, on peut la télécharger
   via un bouton qui apparait.


   return : index2.html, c'est-à-dire la page d'accueil avec ou sans le bouton de téléchargement selon si la matrice est générée
   ou pas.
  
  '''

    if not request.args.get('actualiser_upload'):
        session.pop('matrice', None)
        session.pop('image_ou_tableau', None)

    image_ou_tableau=session.get('image_ou_tableau', False)
    print(f"Tableau ou image : {image_ou_tableau}")
    matrice_generee = session.get('matrice')
    return render_template('index2.html', excel=matrice_generee, tableau_ou_image=image_ou_tableau)


@app.route('/upload', methods=['POST'])
def uploadAndAnalyze():
    '''
   description : Cette route gère l'upload d'un fichier ou la saisie d'un texte. Elle génère un ticket_id unique pour
   suivre le travail du LLM. De plus, elle utilise un thread pour exécuter la fonction travail_de_lia ou
   travail_de_lia_excel selon le type de fichier uploadé.


   return : une erreur si le format n'est pas valide. Si c'est un document ou du texte, ça redirige vers page_attente.html
   et si c'est un excel alors ça redirige vers la page choix_machines.html.
   '''

    session.pop('matrice', None)
    ticket_id = str(uuid.uuid4())
  
    file = request.files.get('document')
    texte_manuel = request.form.get('texte_manuel')


    if file and file.filename != '':
        session['nom_fichier_original'] = os.path.splitext(secure_filename(file.filename))[0]
        extension = os.path.splitext(file.filename)[1]
        if extension not in ALLOWED_EXTENSIONS:
            message_erreur = "Le format du fichier n'est pas valide. Veuillez charger un fichier pdf, docx ou txt."
            return render_template('index2.html', erreur_format = message_erreur)
        
        if extension in DOCUMENTS_EXTENSION:
        
            file_path = os.path.join(UPLOAD_DIRECTORY, secure_filename(file.filename))
            file.save(file_path)


            resultats_ia[ticket_id] = {"status": "en_cours"}
            thread = threading.Thread(target=travail_de_lia, args=(ticket_id, file_path, None))
            thread.start()
            
            return redirect(url_for('page_attente', ticket_id=ticket_id))
        
        if extension in EXCEL_EXTENSION: 
            file_path = os.path.join(UPLOAD_DIRECTORY, secure_filename(file.filename))
            file.save(file_path)
            outil_tableTools = doc_p1.load_excel(file_path)
            liste_onglets = outil_tableTools.sheetnames
            return render_template('choix_machines.html', liste_onglets = liste_onglets, filename= secure_filename(file.filename))
        
    elif texte_manuel and texte_manuel.strip() != '':
        resultats_ia[ticket_id] = {"status": "en_cours"}
        thread = threading.Thread(target=travail_de_lia, args=(ticket_id, None, texte_manuel))
        thread.start()
        
        return redirect(url_for('page_attente', ticket_id=ticket_id))


    return redirect(url_for('index'))


@app.route('/attente/<ticket_id>')
def page_attente(ticket_id):
    '''
   description : Cette route affiche la page d'attente pendant la génération de la matrice de conformiité.
   Elle vérifie régulièrement le dictionnaire resultats_ia pour voir si la matrice est prête ou
   s'il y a des doublons à valider.
  
   return : Si la matrice est prête, redirection vers la page d'accueil avec le bouton de téléchargement. Si des doublons sont détectés, redirection vers la page de validation des doublons.
   Sinon, on reste sur la page d'attente.
   '''

    statut = resultats_ia[ticket_id]["status"]

    if statut == "en_cours":
        return render_template('attente.html')

    elif statut == "excel_en_cours":
        return render_template('attente_excel.html')

    elif statut == "doublons":

        session['matrice_temp'] = resultats_ia[ticket_id]["chemin"]
        session['liste_doublons'] = resultats_ia[ticket_id]["doublons"]
        resultats_ia.pop(ticket_id, None)

        return redirect(url_for('validation_doublons'))
        
    elif statut == "termine":
        session['matrice'] = resultats_ia[ticket_id]["chemin"]
        session['image_ou_tableau'] = resultats_ia[ticket_id].get("image_ou_tableau", False)
        resultats_ia.pop(ticket_id, None)

        return redirect(url_for('index', actualiser_upload=True))
        
    elif statut and statut != "erreur":
        session['matrice'] = resultats_ia[ticket_id]["chemin"]
        session['image_ou_tableau'] = resultats_ia[ticket_id].get("image_ou_tableau", False)
        resultats_ia.pop(ticket_id, None)

        return redirect(url_for('index', actualiser_upload=True))
        
    else:
        return "Une erreur est survenue pendant l'analyse par l'IA."


@app.route('/download', methods=['GET'])
def download():
    '''
   description : Cette route gère le téléchargement de la matrice de conformité générée. Elle vérifie si le chemin
   du fichier Excel est présent dans la session, sinon elle redirige vers la page d'accueil.
  
   return : le fichier Excel en téléchargement ou redirection vers la page d'accueil si le chemin n'est pas trouvé.
   '''

    chemin_excel = session.get('matrice')
    if not chemin_excel:
        return redirect('/')
    return send_file(chemin_excel, as_attachment=True)

##################################### ROUTE POUR LE TRAITEMENT DES EXCEL ############################################

@app.route('/traitement_machines', methods=['POST'])
def traitement_machines():
    '''
   description : Cette route gère le traitement des fichiers Excel pour la génération de la matrice de conformité.
   Elle récupère les informations nécessaires (nom du fichier, onglets choisis, machines à analyser) depuis le
   formulaire soumis par l'utilisateur. Ensuite, elle génère un ticket_id unique et lance un thread pour exécuter la fonction travail_de_lia_excel.
  
   return : La page d'attente pendant la génération de la matrice.
   '''

    filename = request.form.get('filename')
    onglets_choisis = request.form.getlist('onglets_choisis')
    machines_brutes = request.form.get('machines')
   
    liste_machines = [m.strip() for m in machines_brutes.split(',') if m.strip()]
  
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)
    ticket_id = str(uuid.uuid4())
    
    resultats_ia[ticket_id] = {"status": "excel_en_cours"}

    thread = threading.Thread(target=travail_de_lia_excel, args=(ticket_id, file_path, onglets_choisis, liste_machines))
    thread.start()

    return redirect(url_for('page_attente', ticket_id=ticket_id))



@app.route('/doublons', methods=['GET'])
def validation_doublons():
    '''
   description : Cette route affiche la page de validation des doublons sémantiques détectés dans le fichier Excel.
   '''

    liste_doublons = session.get('liste_doublons')
    if not liste_doublons:
        return redirect(url_for('index'))

    return render_template('validation_doublons.html', doublons=liste_doublons)       


@app.route('/fusionner', methods=['POST'])
def fusionner():
    '''
    description : Cette route gère la fusion des doublons sémantiques détectés dans le fichier Excel.
    Elle récupère les décisions de l'utilisateur depuis le formulaire soumis, puis elle utilise la fonction
    merge_similar_features pour fusionner ou non les doublons selon les choix du user.


    return : La page d'accueil


    '''

    chemin_temp = session.get('matrice_temp')
    
    
    if not chemin_temp:
        return redirect(url_for('index'))
        
    
    try:
        total_doublons = int(request.form.get('total_doublons', 0))
    except ValueError:
        total_doublons = 0
        
  
    decisions_utilisateur = []
    
    for i in range(total_doublons):
      
        val1 = request.form.get(f'val1_{i}')
        val2 = request.form.get(f'val2_{i}')
        choix = request.form.get(f'choix_{i}')
        
        
        if val1 and val2 and choix:
            decisions_utilisateur.append({
                "val1": val1,
                "val2": val2,
                "choix": choix
            })
            
    nom_original = session.get('nom_fichier_original', 'Document')
    nom_final = f"CM_{nom_original}.xlsx"
    
    chemin_final = doc_p1.merge_similar_features(chemin_temp, decisions_utilisateur, nom_final)
    
    session.pop('matrice_temp', None)
    session.pop('liste_doublons', None)
    
    session['matrice'] = chemin_final
    
    return redirect(url_for('index', actualiser_upload=True))
       
@app.route('/status', methods=['GET'])
def status():
    '''
   description : Cette route retourne le statut actuel du traitement des fichiers Non Excel.


   return : Un texte indiquant l'état du traitement (PAS COMMENCE, EXTRACTION EN COURS, EXTRACTION TERMINEE,
   ANALYSE EN COURS, ANALYSE TERMINEE, CONVERSION EN COURS, CONVERSION TERMINEE, CONVERSION TERMINEE, INSERTION EN COURS,
   INSERTION TERMINEE,
   '''

    # On renvoie directement le texte brut, pas un dictionnaire
    return doc.get_status()

@app.route('/excel_status', methods=['GET'])
def excel_status():
    '''
   description : Cette route retourne le statut actuel du traitement des fichiers Excel.


   return : Un texte indiquant l'état du traitement (PAS COMMENCE, EXTRACTION EN COURS, EXTRACTION TERMINEE,
   ANALYSE EN COURS, ANALYSE TERMINEE, CONVERSION EN COURS, CONVERSION TERMINEE, CONVERSION TERMINEE, INSERTION EN COURS,
   INSERTION TERMINEE,
   '''

    # On renvoie directement le texte brut, pas un dictionnaire
    return doc_p1.get_status()