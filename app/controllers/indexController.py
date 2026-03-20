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
    try:
        if file_path:
            text = doc.extraction_sur_mesure(file_path)
            json_final = doc.ChatOllama(text)
            chemin_propre = os.path.splitext(file_path)[0]
            chemin_excel = doc.matrice_conformite(json_final, chemin_propre)
            
        elif texte_manuel:
            json_final = doc.ChatOllama(texte_manuel)
            fichier_txt_path = os.path.join(UPLOAD_DIRECTORY, 'texte_manuel')
            chemin_excel = doc.matrice_conformite(json_final, fichier_txt_path)
            
        resultats_ia[ticket_id] = chemin_excel
    except Exception as e:
        print(f"Erreur pendant l'analyse : {e}")
        resultats_ia[ticket_id] = "erreur"
        
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path) 

def travail_de_lia_excel(ticket_id, file_path, onglets_choisis, liste_machines):
    try:
        outil_table = doc_p1.load_excel(file_path)
        
        outil_table.selected = [True if nom in onglets_choisis else False for nom in outil_table.sheetnames]

        print(f"Début de l'analyse Excel pour les machines : {liste_machines}")
        wb, liste_doublons = doc_p1.build_compliance_matrix("qwen2.5-coder:32b", liste_machines, outil_table, file_path)

        nom_fichier_temp = f"matrice_temp_{ticket_id}.xlsx"
        chemin_temp = doc_p1.save_compliance_matrix(wb, nom_fichier_temp)

        if len(liste_doublons) > 0:
            resultats_ia[ticket_id] = {"statut": "doublons", "chemin": chemin_temp, "doublons": liste_doublons}
        else:
            resultats_ia[ticket_id] = {"statut": "termine", "chemin": chemin_temp}

    except Exception as e:
        print(f"Erreur pendant l'analyse Excel : {e}")
        resultats_ia[ticket_id] = "erreur"

    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


@app.route('/')
def index():
   if not request.args.get('actualiser_upload'):
       session.pop('matrice', None)


   matrice_generee = session.get('matrice')
   return render_template('index2.html', excel=matrice_generee)


@app.route('/upload', methods=['POST'])
def uploadAndAnalyze():
   session.pop('matrice', None)
   ticket_id = str(uuid.uuid4())
  
   file = request.files.get('document')
   texte_manuel = request.form.get('texte_manuel')


   if file and file.filename != '':
       session['nom_fichier_original'] = os.path.splitext(secure_filename(file.filename))[0]
       extension = os.path.splitext(file.filename)[1]
       if extension not in ALLOWED_EXTENSIONS:
           return "Le format du fichier n'est pas valide. Veuillez charger un fichier pdf, docx ou txt."
       
       if extension in DOCUMENTS_EXTENSION:
       
        file_path = os.path.join(UPLOAD_DIRECTORY, secure_filename(file.filename))
        file.save(file_path)


        resultats_ia[ticket_id] = "en_cours"
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
       resultats_ia[ticket_id] = "en_cours"
       thread = threading.Thread(target=travail_de_lia, args=(ticket_id, None, texte_manuel))
       thread.start()
      
       return redirect(url_for('page_attente', ticket_id=ticket_id))


   return redirect(url_for('index'))


@app.route('/attente/<ticket_id>')
def page_attente(ticket_id):
   statut = resultats_ia.get(ticket_id)
  
   if statut == "en_cours":
       return render_template('attente.html')
   
   elif isinstance(statut, dict):
        
    
        if statut["statut"] == "doublons":

            session['matrice_temp'] = statut["chemin"]
            session['liste_doublons'] = statut["doublons"]
            resultats_ia.pop(ticket_id, None)
        
            return redirect(url_for('validation_doublons'))
            
        elif statut["statut"] == "termine":
            session['matrice'] = statut["chemin"]
            resultats_ia.pop(ticket_id, None)

            return redirect(url_for('index', actualiser_upload=True))
      
   elif statut and statut != "erreur":
       session['matrice'] = statut
       resultats_ia.pop(ticket_id, None)

       return redirect(url_for('index', actualiser_upload=True))
      
   else:
       return "Une erreur est survenue pendant l'analyse par l'IA."


@app.route('/download', methods=['GET'])
def download():
   chemin_excel = session.get('matrice')
   if not chemin_excel:
       return redirect('/')
   return send_file(chemin_excel, as_attachment=True)

##################################### ROUTE POUR LE TRAITEMENT DES EXCEL ############################################

@app.route('/traitement_machines', methods=['POST'])
def traitement_machines():
   
    filename = request.form.get('filename')
    onglets_choisis = request.form.getlist('onglets_choisis')
    machines_brutes = request.form.get('machines')
   
    liste_machines = [m.strip() for m in machines_brutes.split(',') if m.strip()]
  
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)
    ticket_id = str(uuid.uuid4())
    
    resultats_ia[ticket_id] = "en_cours"

    thread = threading.Thread(target=travail_de_lia_excel, args=(ticket_id, file_path, onglets_choisis, liste_machines))
    thread.start()

    return redirect(url_for('page_attente', ticket_id=ticket_id))



@app.route('/doublons', methods=['GET'])
def validation_doublons():
    
    liste_doublons = session.get('liste_doublons')
    if not liste_doublons:
        return redirect(url_for('index'))

    return render_template('validation_doublons.html', doublons=liste_doublons)       


@app.route('/fusionner', methods=['POST'])
def fusionner():
   
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
    # On renvoie directement le texte brut, pas un dictionnaire
    return doc.get_status()