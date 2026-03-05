from flask import Flask, render_template, redirect, url_for, request, send_file, session
from app import app
import json
import app.services.doc as doc  #c'est le doc.py 
from werkzeug.utils import secure_filename
import os 

# UPLOAD_DIRECTORY = 'app/uploads/'

ALLOWED_EXTENSIONS = set(['.pdf', '.docx', '.txt'])


DOSSIER_CONTROLLERS = os.path.dirname(os.path.abspath(__file__))

DOSSIER_APP = os.path.dirname(DOSSIER_CONTROLLERS)

UPLOAD_DIRECTORY = os.path.join(DOSSIER_APP, 'uploads')

os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)



app.secret_key = 'Infodip-1986-v2'

@app.route('/')
def index():
    if not request.args.get('actualiser_upload'):

        session.pop('matrice', None)

    matrice_generee = session.get('matrice')
    return render_template('index2.html', excel = matrice_generee)

@app.route('/upload', methods=['POST'])
def uploadAndAnalyze():
        session.pop('matrice', None)
        file = request.files['document']
        
        
        if file and file.filename != '': 
            extension = os.path.splitext(file.filename)[1]
            if extension not in ALLOWED_EXTENSIONS:
                
                return "Le format du fichier n'est pas valide. Veuillez charger un fichier pdf, docx ou txt."
            
            file_path = os.path.join(UPLOAD_DIRECTORY, secure_filename(file.filename))
            file.save(file_path)
            text = doc.extraction_sur_mesure(file_path)
            json_final = doc.ChatOllama(text)

            chemin_propre = os.path.splitext(file_path)[0]
            session['matrice'] = doc.matrice_conformite(json_final, chemin_propre)
           
           
            #session['matrice'] = doc.matrice_conformite(json_final, file_path)
            os.remove(file_path)
            


           
        
        else:
            direct_text = request.form.get('texte_manuel')
            json_final_txt = doc.ChatOllama(direct_text)
            session['matrice'] = doc.matrice_conformite(json_final_txt, None)
            

        return redirect(url_for('index', actualiser_upload=True))
   
   
   
   
@app.route('/download', methods=['GET'])
def download():
        chemin_excel = session.get('matrice')

        if not chemin_excel:
            return redirect('/')
        
        session.pop('matrice', None)

        return send_file(chemin_excel, as_attachment=True)

# @app.after_request
# def remove_file(response):
#     chemin_excel = session.get('matrice')
#     if chemin_excel:
#         os.remove(chemin_excel)
#     return response
    








        
       

