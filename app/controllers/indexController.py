from flask import render_template, redirect, url_for, request
from app import app
import json
import doc  #c'est le doc.py 
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
            return doc.ChatOllama(text)
        else:
            direct_text = request.form.get('texte_manuel')
            return doc.ChatOllama(direct_text)

        return redirect('/')
        
       

#SE RENSEIGNER ET TESTER LE CODE EN DESSOUS :


#       ## uploading specs ##
# UPLOAD_FOLDER = '/tmp/'
# ALLOWED_EXTENSIONS = set(['deb'])

# def allowed_file(filename):
#     return '.' in filename and \
#     filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# ## index page stuff ##
# @app.route('/index', methods = ['GET', 'POST'])
# def index():
# ## kerberos username
#     secuser = request.environ.get('REMOTE_USER')

#     user = { 'nick': secuser }


# ## file uploading stuff
# if request.method == 'POST': 
#     file = request.files['file']
#     if file and allowed_file(file.filename):
#         filename = secure_filename(file.filename)
#         file.save(os.path.join(UPLOAD_FOLDER, filename))
#         return redirect(url_for('/index',     
#                         filename=filename))

# ## main return
# return render_template("index.html",
#     user = user)

        