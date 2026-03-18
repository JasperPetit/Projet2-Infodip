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


ALLOWED_EXTENSIONS = set(['.pdf', '.docx', '.txt'])


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
           text, image_ou_tableau = doc.extraction_sur_mesure(file_path)
           json_final = doc.ChatOllama(text)
           chemin_propre = os.path.splitext(file_path)[0]
           chemin_excel = doc.matrice_conformite(json_final, chemin_propre)
          
       elif texte_manuel:
           json_final = doc.ChatOllama(texte_manuel)
           fichier_txt_path = os.path.join(UPLOAD_DIRECTORY, 'texte_manuel')
           chemin_excel = doc.matrice_conformite(json_final, fichier_txt_path)
           image_ou_tableau = False
          
       resultats_ia[ticket_id] = {
           "status": "termine",
           "chemin_excel": chemin_excel,
            "image_ou_tableau": image_ou_tableau
                                  }
   except Exception as e:
       print(f"Erreur pendant l'analyse : {e}")
       resultats_ia[ticket_id] = {"erreur": str(e)}


@app.route('/')
def index():
    if not request.args.get('actualiser_upload'):
        session.pop('matrice', None)
        session.pop('image_ou_tableau', None)

    image_ou_tableau=session.get('image_ou_tableau', False)
    print(image_ou_tableau)
    matrice_generee = session.get('matrice')
    return render_template('index2.html', excel=matrice_generee, tableau_ou_image=image_ou_tableau)


@app.route('/upload', methods=['POST'])
def uploadAndAnalyze():
   session.pop('matrice', None)
   ticket_id = str(uuid.uuid4())
  
   file = request.files.get('document')
   texte_manuel = request.form.get('texte_manuel')


   if file and file.filename != '':
       extension = os.path.splitext(file.filename)[1]
       if extension not in ALLOWED_EXTENSIONS:
           return "Le format du fichier n'est pas valide. Veuillez charger un fichier pdf, docx ou txt."
      
       file_path = os.path.join(UPLOAD_DIRECTORY, secure_filename(file.filename))
       file.save(file_path)


       resultats_ia[ticket_id] = {"status": "en_cours"}
       thread = threading.Thread(target=travail_de_lia, args=(ticket_id, file_path, None))
       thread.start()
      
       return redirect(url_for('page_attente', ticket_id=ticket_id))
     
   elif texte_manuel and texte_manuel.strip() != '':
       resultats_ia[ticket_id] = {"status": "en_cours"}
       thread = threading.Thread(target=travail_de_lia, args=(ticket_id, None, texte_manuel))
       thread.start()
      
       return redirect(url_for('page_attente', ticket_id=ticket_id))


   return redirect(url_for('index'))


@app.route('/attente/<ticket_id>')
def page_attente(ticket_id):
   statut = resultats_ia[ticket_id]["status"]
  
   if statut == "en_cours":
       return render_template('attente.html')
      
   elif statut and statut != "erreur":
       session['matrice'] = resultats_ia[ticket_id]["chemin_excel"]
       session['image_ou_tableau'] = resultats_ia[ticket_id]["image_ou_tableau"]
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



        
       
@app.route('/status', methods=['GET'])
def status():
    # On renvoie directement le texte brut, pas un dictionnaire
    return doc.get_status()