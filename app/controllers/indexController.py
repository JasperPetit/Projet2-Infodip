from flask import render_template, redirect, url_for, request
from app import app
import json
import doc 

class IndexController:
    @app.route('/')
    def index():
        return render_template('index.html', methods = ['GET'])

    @app.route('/analyser', methods=['POST'])
    def submit():
        file = request.files['fichier']

        