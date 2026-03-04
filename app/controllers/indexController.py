from flask import render_template, redirect, url_for, request, send_file, session
from app import app
import json
import app.services.doc as doc  #c'est le doc.py 
from werkzeug.utils import secure_filename
import os 

UPLOAD_DIRECTORY = 'app/uploads/'

ALLOWED_EXTENSIONS = set(['.pdf', '.docx', '.txt'])
class IndexController:


    @app.route('/')
    def index():
        return render_template('index2.html', methods = ['GET'])

    @app.route('/upload', methods=['POST'])
    def uploadAndAnalyze():
        file = request.files['document']
        
        
        if file and file.filename != '': 
            extension = os.path.splitext(file.filename)[1]
            if extension not in ALLOWED_EXTENSIONS:
                
                return "Le format du fichier n'est pas valide. Veuillez charger un fichier pdf, docx ou txt."
            
            file_path = os.path.join(UPLOAD_DIRECTORY, secure_filename(file.filename))
            file.save(file_path)
            text = doc.extraction_sur_mesure(file_path)
            json_final = doc.ChatOllama(text)
            session['matrice'] = doc.matrice_conformite(json_final, file_path)
            os.remove(file_path)
            


           
        
        else:
            direct_text = request.form.get('texte_manuel')
            json_final_txt = doc.ChatOllama(direct_text)
            matrice_txt=doc.matrice_conformite(json_final_txt, None)
            os.remove(file_path)  
        

        return redirect('/')
   
   
   
   
    @app.route('/download', methods=['GET'])
    def download():

        return send_file(session['matrice'], as_attachment=True)
    
    def 







        
       

