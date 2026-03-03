
#Ces lignes sont des constantes qui definissent les positions de départ pour l'ajout des machines et des composant dans le fichier excel.
#Si vous voulez les modifier, il faut considerer que A=1,B=2,etc et que ligne 1=1, ligne=2=2,etc.
COLONNE_DEBUT_MACHINE = 5
LIGNE_DEBUT_MACHINE = 10
COLONNE_DEBUT_MANDATORY = 2
LIGNE_DEBUT_MANDATORY = 12


import ollama
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

# Import des types d'éléments pour les reconnaître
from docling_core.types.doc.document import TextItem, TableItem, PictureItem
import time
import pytesseract
import logic
import json

import pytesseract
import openpyxl
import os



def extraction_sur_mesure(chemin_fichier):
    print(f"\n--- Démembrement du document : {chemin_fichier} ---")

    
    # 1. Configuration : On force Docling à "découper" physiquement les images
    options = PdfPipelineOptions()
    options.generate_picture_images = True # Indispensable pour récupérer l'image PIL
    
    convertisseur = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=options)
        }
    )
    
    print("1. Scan de la structure par Docling...")
    resultat = convertisseur.convert(chemin_fichier)
    doc = resultat.document
    texte_final = ""
    
    print("2. Parcours intelligent des éléments...")
    # doc.iterate_items() lit le document de haut en bas, dans le bon ordre !
    for item, level in doc.iterate_items():
        
        # CAS A : C'est du texte normal (paragraphes, titres...)
        if isinstance(item, TextItem):
            texte_final += f"{item.text}\n\n"
            
        # CAS B : C'est un tableau (on garde le beau format Markdown pour Qwen)
        elif isinstance(item, TableItem):
            texte_final += f"{item.export_to_markdown()}\n\n"
            
        # CAS C : C'est une image ! (On sort l'arme lourde : Tesseract)
        elif isinstance(item, PictureItem):
            
            # On récupère l'image sous forme de variable (format PIL Image)
            image_pil = item.get_image(doc)
            
            if image_pil is not None:
                # Ton code Tesseract classique entre en action
                texte_image = pytesseract.image_to_string(image_pil, lang='fra+eng')
                
                # On ajoute des balises pour aider Qwen à comprendre d'où ça vient
                texte_final += f"{texte_image.strip()}"
                
    print(texte_final)
    return texte_final




def ChatOllama(texte_complet):
    response: ollama.ChatResponse = ollama.chat(
        model="qwen2.5-coder:32b",
        messages=[
            {
                'role': 'system', 
                'content': 'Tu est une IA experte chez INFODIP une societe francaise qui récoit des commandes d’ordinateurs/pc qu’elle doit mettre en rack ou baie puis les fournir a ses clients. Tu recevoie des cahier des charges et documents contenant des exigences et ton role est de les analyser afin de ressortir la liste des ordinateur décrite et de ressortir un résultat en JSON sous la forme d’une liste de machines. Tu n’invente aucune informations et n’ajoute rien qui n’est pas écrit sur les documents. Tu ne change pas la maniere dont sont écrite les informations, reprend ce qui est dans le document uniquement. Tu ajout dans le JSON seulement les pc qui sont commandés, pas ceux déja présent chez le client, et seulement les machine dun type correspondant au types suiavnts: ["pc","NAS","serveurs"]'
            },
            {   
                "role": "user", 
             "content": f'''Ce document est un cahier des charges. Dans celui-ci est décrit une/plusieurs machine informatique/ordinateur que l’entreprise voudrais commander a Infodip. Je voudrais que tu réccupere dans ce document la liste de toutes les machines qui sont commander. 
                Tu me repondera sous une forme d’une liste JSON strict uniquement, je ne veux PAS D4AUTRE TEXTE OU EXPLICATION QUE JE JSON. Si 2 pc on exactement la meme configuration a un composant de difference alors tu les traitera comme 2 machine disctincte. Lorsqu’un element est en quantité multiple tu lu mettera “yx” en préfixe ou y est ka quantité et x represente le symbole fois. 
                Tu interprettera tout seul la catégorie en choisissant celle qui te parait la plus pertinente de chaque exigence en faisant attention a les ajouter a une seul catégorie. 
                Voici le texte : {texte_complet}
                Pour chaque machine que tu trouvera tu l’ajoutera au JSON avec le format suivant le texte entre chevron est un exemple de valeur, ce n’est pas le texte que dtu doit mettre dans le JSON final :
                <template>
                {{
                <nom d’une machine>:{{
                “Format”":[“<format demandé>”],
                “CPU”:[“<CPU demandé>”],
                “Memory”:[<Memory demandé>],
                “Audio component”:[<Audio component demandé>],
                “GPU”:[“<GPU demandé>”],
                “Network”:[“<Network demandé>”],
                “Out of band management”:[“<Out of band management>”],
                “USB”:[“<USB>“],
                “OS”:[“<OS>”],
                “Storage”:[“<Storage>“],
                “Noise”:[“<Noise>“],
                “Warranty”:[“<Warranty>“],
                “License”:[“<License>“],
                “Other”:[“<Other>“]
                }}
                }}
                </template>
                Si une machine a plusieurs composant du meme type alors tu ajoutera dans la liste des composant comme plusieurs instance. Voici un exemple pour la clé “Other” si il y avait 3 élements du texte Other1,Other2 et Other3 et qui correspondait a une seul et meme machine/ordinateur, mais cela s’applique pour toute les catégories : <example> “Other”:[“<Other1>“,“<Other2>“,“<Other3>“]</example>."
                '''
            }
        ],
        format="json",
        options={"temperature": 0}
    )
    print(response.message.content)
    reponse_JSON = json.loads(response.message.content)
    return reponse_JSON


#def check_doublon(dictionnaire_composant:dict, composant_ajoute:logic.composant):



def conversion_machine(tableau_machine:list):
    resultat = []
    for machine in tableau_machine:
        new_machine = logic.machine(machine)
        resultat.append(new_machine)
    return resultat

def conversion_composant(dictionnaire:dict):
    config_dict:dict = {
        "Format": [],
        "CPU": [],
        "Memory": [],
        "Audio component": [],
        "GPU": [],
        "Network": [],
        "Out of band management": [],
        "USB": [],
        "OS": [],
        "Storage": [],
        "Noise": [],
        "Warranty": [],
        "License": [],
        "Other": []
    }

    liste_machines:list = dictionnaire.keys()
    for machine in liste_machines:
        categorie:list = dictionnaire[machine].keys()
        for current_categorie in categorie:
            for current_composant in dictionnaire[machine][current_categorie]:
                
                new_composant = logic.composant(current_composant,current_categorie)
#                check_doublon(new_composant,config_dict)
                config_dict[current_categorie].append(new_composant)
    return config_dict


def insertion_excel(config_dict:dict, liste_machines:list, nom_fichier:str):
    wb = openpyxl.load_workbook("template.xlsx")
    ws = wb.active
    for indice_machine in range(len(liste_machines)):

        current_machine = liste_machines[indice_machine]
        current_row = LIGNE_DEBUT_MACHINE
        current_column = COLONNE_DEBUT_MACHINE + indice_machine

        ws.cell(row=current_row, column=current_column).value = current_machine.name
    nom_coupe = nom_fichier.split('.')[0] 
    #Changer l'extension du fichier ici ci l'extension de la template change
    wb.save(f"resultat/{nom_coupe}.xlsx")



if __name__ == "__main__":
    choix = input("Voulez-vous faire une extraction sur mesure (1) ou utiliser le dernier JSON traité (2) ? ")
    start = time.time()
    fichier_pdf = "CDC Arcelor mittal.pdf" 

    if choix == "1" :
        txt = extraction_sur_mesure(fichier_pdf)
        print(txt)
        print("=================RESULTAT DE L'EXTRACTION===========")
        endRead = time.time()
        reponse_JSON = ChatOllama(txt)
        endLLM = time.time()
        with open("resultat.json", "w") as f:
            json.dump(reponse_JSON, f, indent=4)
        print(reponse_JSON)
        print("=================PERFORMANCE===========")
        print(f"Temps d'extraction : {endRead - start}")
        print(f"Temps de traitement LLM : {endLLM - endRead}")
        print(f"Temps total : {endLLM - start}")

    if choix == "2" : 
        print("=================LECTURE DU DERNIER JSON TRAITE===========")
        with open("resultat.json", "r") as f:
            precedent_JSON = json.load(f)
        liste_composants = conversion_composant(precedent_JSON)
        liste_machines = conversion_machine(precedent_JSON.keys())
        insertion_excel(config_dict=liste_composants, liste_machines=liste_machines, nom_fichier=fichier_pdf)
        # print("=============MACHINES====================")
        # print(liste_machines)
        # print("=================COMPOSANTS=============")
        # print(liste_composants)



    print("=================FIN DU PROGRAMME===========")
