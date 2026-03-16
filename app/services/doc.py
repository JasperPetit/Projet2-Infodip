#VERSION = 4.3.2
#Ces lignes sont des constantes qui definissent les positions de départ pour l'ajout des machines et des composant dans le fichier excel.
#Si vous voulez les modifier, il faut considerer que A=1,B=2,etc et que ligne 1=1, ligne=2=2,etc.
COLONNE_DEBUT_MACHINE = 5
LIGNE_DEBUT_MACHINE = 10
COLONNE_DEBUT_CATEGORIE = 2
COLONNE_DEBUT_MANDATORY = 3
LIGNE_DEBUT_MANDATORY = 13

LIGNE_TITRES_DEBUT = 12
COLONNE_TITRES_DEBUT = 2

POSITION_JUSTIFICATION = (4,27)
POSITION_QUESTION = (5,27)

POURCENTAGE_SIMILARITE = 0.95

CHEMIN_TEMPLATE = "app/static/template.xlsx"



import ollama
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

# Import des types d'éléments pour les reconnaître
from docling_core.types.doc.document import TextItem, TableItem, PictureItem
import time
import pytesseract
import app.services.logic as logic
import json
from ollama import Client
import pytesseract
import openpyxl
import os
from openpyxl.styles import Border, Side, PatternFill
from sentence_transformers import SentenceTransformer, util

ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
client = Client(host=ollama_host)

MODEL_LLM = "llama3.3:70b"
MODEL_EMBEDDING_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
MODEL_EMBEDDING = SentenceTransformer(MODEL_EMBEDDING_NAME)

BORDER = Border(left=Side(style='medium'), right=Side(style='medium'), top=Side(style='medium'), bottom=Side(style='medium'))
BORDER_MACHINE_HAUT = Border(left=Side(style='medium'), right=Side(style='medium'), top=Side(style='medium'),bottom=Side(style='thin'))
BORDER_MACHINE_BAS = Border(left=Side(style='medium'), right=Side(style='medium'), bottom=Side(style='medium'),top=Side(style='thin'))

FOND = PatternFill(start_color="D3D3D3",end_color="D3D3D3",fill_type = "solid")


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
    # doc.iterate_items() lit le document de haut en bas, dans le bon ordre 
    for item, level in doc.iterate_items():
        
        # CAS A : C'est du texte normal
        if isinstance(item, TextItem):
            texte_final += f"{item.text}\n\n"
            
        # CAS B : C'est un tableau et on garde le format markdown 
        elif isinstance(item, TableItem):
            texte_final += f"{item.export_to_markdown()}\n\n"
            
        # CAS C : C'est une image et on utlise Tessetact 
        elif isinstance(item, PictureItem):
            
            # On récupère l'image sous forme de variable (format PIL Image)
            image_pil = item.get_image(doc)
            
            if image_pil is not None:
                texte_image = pytesseract.image_to_string(image_pil, lang='fra+eng')
                
                # On ajoute des balises pour aider le LLM à comprendre d'où ça vient
                texte_final += f"{texte_image.strip()}"
                
    print(texte_final)
    return texte_final




def ChatOllama(texte_complet):

    # response: ollama.ChatResponse = ollama.chat(
    #     model=MODEL_LLM,
    #     messages=[
    #         {
    #             'role': 'system', 
    #             'content': 'Tu es une IA experte chez INFODIP, une société française qui reçoit des commandes d’ordinateurs/PC qu’elle doit mettre en rack ou en baie puis les fournir à ses clients. Tu reçois des cahiers des charges et des documents contenant des exigences et ton rôle est de les analyser afin d\'en extraire la liste des ordinateurs décrite et de fournir un résultat en JSON sous la forme d’une liste de machines. Tu n’inventes aucune information et n’ajoutes rien qui n’est pas écrit dans les documents. Tu ne changes pas la manière dont sont écrites les informations, reprends uniquement ce qui est dans le document. Tu ajoutes dans le JSON seulement les PC qui sont commandés, pas ceux déjà présents chez le client, et seulement les machines d\'un type correspondant aux types suivants : ["workstation","SAN","laptop","pc", "NAS", "serveurs"].'
    #         },
    #         {'role':"user",
    #          'content': f"""
    #             Ce document est un cahier des charges. Dans celui-ci est décrite une/plusieurs machine(s) informatique(s)/ordinateur(s) que l’entreprise voudrait commander à Infodip.
    #             Je voudrais que tu récupères dans ce document la liste de noms de toutes les machines qui sont commandées.
    #             Tu me répondras sous la forme d’une liste JSON stricte contenant uniquement les noms des differentes machines sans autre parametre ou attribut, juste le nom, je ne veux PAS D'AUTRE TEXTE OU EXPLICATION QUE LE JSON. 

    #             Voici le document : {texte_complet}
    #          """
    #          }
    #     ],
    #     format="json",
    #     options={"temperature": 0}
    # )
    # liste_machines = json.loads(response.message.content)
    # print("======================================LISTE DES MACHINES :======================================")
    # print(f"{liste_machines}")
    # JSON_COMPLET = {}
    # for machine in liste_machines:
    #     response_machine: ollama.ChatResponse = ollama.chat(
    #         model=MODEL_LLM,
    #         messages=[
    #             {
    #                 'role': 'system',
    #                 'content': 'Tu es une IA experte chez INFODIP, une société française qui reçoit des commandes d’ordinateurs/PC qu’elle doit mettre en rack ou en baie puis les fournir à ses clients. Tu reçois des cahiers des charges et des documents contenant des exigences et ton rôle est de les analyser afin d\'en extraire la liste des ordinateurs décrite et de fournir un résultat en JSON sous la forme d’une liste de machines. Tu n’inventes aucune information et n’ajoutes rien qui n’est pas écrit dans les documents. Tu ne changes pas la manière dont sont écrites les informations, reprends uniquement ce qui est dans le document. Tu ajoutes dans le JSON seulement les PC qui sont commandés, pas ceux déjà présents chez le client, et seulement les machines d\'un type correspondant aux types suivants : ["workstation","SAN","laptop","pc", "NAS", "serveurs"].'
    #             },
    #             {
    #                 "role": "user",
    #                 "content": f"""
    #                 Je veux que tu me donnes la configuration complète de la machine {machine} en reprenant uniquement les éléments écrits dans le document. 
    #                 Tu me répondras sous la forme d’un JSON strict uniquement, je ne veux PAS D'AUTRE TEXTE OU EXPLICATION QUE LE JSON. 
    #                 Tu interpréteras tout seul la catégorie en choisissant celle qui te paraît la plus pertinente pour chaque exigence, en faisant attention à les ajouter à une seule catégorie. 

    #                 <template>
    #                 {{
    #                 "Format":["<format demandé>"],
    #                 "CPU":["<CPU demandé>"],
    #                 "Memory":["<Memory demandé>"],
    #                 "Audio component":["<Audio component demandé>"],
    #                 "GPU":["<GPU demandé>"],
    #                 "Network":["<Network demandé>"],
    #                 "Out of band management":["<Out of band management>"],
    #                 "USB":["<USB>"],
    #                 "OS":["<OS>"],
    #                 "Storage":["<Storage>"],
    #                 "Noise":["<Noise>"],
    #                 "Warranty":["<Warranty>"],
    #                 "License":["<License>"],
    #                 "Other":["<Other>"]
    #                 }}
    #                 </template>
    #                 Si une machine a plusieurs composants du même type, alors tu les ajouteras dans la liste des composants comme plusieurs instances. Voici un exemple pour la clé "Other" s'il y avait 3 éléments du texte Other1, Other2 et Other3 qui correspondaient à une seule et même machine/ordinateur, mais cela s’applique pour toutes les catégories : <example> "Other":["<Other1>", "<Other2>", "<Other3>"]</example>."

    #                 Voici le document : {texte_complet}
    #                  """
    #             }
    #         ]
    #     )

    #     reponse_JSON = json.loads(response_machine.message.content)
    #     JSON_COMPLET[machine] = reponse_JSON
    # print("======================================JSON COMPLET :======================================")
    # print(f"{JSON_COMPLET}")


    response: ollama.ChatResponse = ollama.chat(
        model=MODEL_LLM,
        messages=[
            {
                'role': 'system', 
                'content': 'Tu es une IA experte chez INFODIP, une société française qui reçoit des commandes d’ordinateurs/PC qu’elle doit mettre en rack ou en baie puis les fournir à ses clients. Tu reçois des cahiers des charges et des documents contenant des exigences et ton rôle est de les analyser afin d\'en extraire la liste des ordinateurs décrite et de fournir un résultat en JSON sous la forme d’une liste de machines. Tu n’inventes aucune information et n’ajoutes rien qui n’est pas écrit dans les documents. Tu ne changes pas la manière dont sont écrites les informations, reprends uniquement ce qui est dans le document. Tu ajoutes dans le JSON seulement les PC qui sont commandés, pas ceux déjà présents chez le client, et seulement les machines d\'un type correspondant aux types suivants : ["workstation","SAN","laptop","pc", "NAS", "serveurs"].'
            },
            {   
                "role": "user", 
             "content": f'''Ce document est un cahier des charges. Dans celui-ci est décrite une/plusieurs machine(s) informatique(s)/ordinateur(s) que l’entreprise voudrait commander à Infodip. Je voudrais que tu récupères dans ce document la liste de toutes les machines qui sont commandées. 
                Tu me répondras sous la forme d’une liste JSON stricte uniquement, je ne veux PAS D'AUTRE TEXTE OU EXPLICATION QUE LE JSON. Si 2 PC ont exactement la même configuration à un composant de différence près, alors tu les traiteras comme 2 machines distinctes. Lorsqu’un élément est en quantité multiple, tu lui mettras “yx” en préfixe où y est la quantité et x représente le symbole fois. 
                Tu interpréteras tout seul la catégorie en choisissant celle qui te paraît la plus pertinente pour chaque exigence, en faisant attention à les ajouter à une seule catégorie. 
                Voici le texte : {texte_complet}
                Pour chaque machine que tu trouveras, tu l’ajouteras au JSON avec le format suivant. Le texte entre chevrons est un exemple de valeur, ce n’est pas le texte que tu dois mettre dans le JSON final :
                <template>
                {{
                "<nom d’une machine>":{{
                "Format":["<format demandé>"],
                "CPU":["<CPU demandé>"],
                "Memory":["<Memory demandé>"],
                "Audio component":["<Audio component demandé>"],
                "GPU":["<GPU demandé>"],
                "Network":["<Network demandé>"],
                "Out of band management":["<Out of band management>"],
                "USB":["<USB>"],
                "OS":["<OS>"],
                "Storage":["<Storage>"],
                "Noise":["<Noise>"],
                "Warranty":["<Warranty>"],
                "License":["<License>"],
                "Other":["<Other>"]
                }}
                }}
                </template>
                Si une machine a plusieurs composants du même type, alors tu les ajouteras dans la liste des composants comme plusieurs instances. Voici un exemple pour la clé "Other" s'il y avait 3 éléments du texte Other1, Other2 et Other3 qui correspondaient à une seule et même machine/ordinateur, mais cela s’applique pour toutes les catégories : <example> "Other":["<Other1>", "<Other2>", "<Other3>"]</example>."
                 '''
            }

        ],
        format="json",
        options={"temperature": 0}
    )
    reponse_JSON = json.loads(response.message.content)

    

    return reponse_JSON


def check_doublon(dictionnaire_composant:dict, composant_ajoute:logic.composant):
    for exigence_compare in dictionnaire_composant[composant_ajoute.categorie]:
        if exigence_compare.compare(composant_ajoute):
            print(f"ON A DETECTE UN DOUBLON ENTRE {exigence_compare.name} ET {composant_ajoute.name}")
            return exigence_compare
        embedding1 = MODEL_EMBEDDING.encode(exigence_compare.name)
        embedding2 = MODEL_EMBEDDING.encode(composant_ajoute.name)
        similarity = util.cos_sim(embedding1, embedding2)
        if similarity > POURCENTAGE_SIMILARITE:
            print(f"ON A DETECTE UN DOUBLON ENTRE {exigence_compare.name} ET {composant_ajoute.name}")
            return exigence_compare
    return False

def conversion_machine(tableau_machine:list):
    resultat = []
    for machine in tableau_machine:
        new_machine = logic.machine(machine)
        resultat.append(new_machine)
    return resultat

def conversion_composant(dictionnaire:dict, liste_machines:list):
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

    
    for machine in liste_machines:
        categorie:list = dictionnaire[machine.name].keys()
        for current_categorie in categorie:
            for current_composant in dictionnaire[machine.name][current_categorie]:
                
                new_composant = logic.composant(current_composant,current_categorie)
                doublon = check_doublon(config_dict,new_composant)
                if doublon != False:
                    doublon.ajouter_machine(machine)
                else:
                    new_composant.ajouter_machine(machine)
                    config_dict[current_categorie].append(new_composant)
    return config_dict


def insertion_excel(config_dict:dict, liste_machines:list, nom_fichier:str):
    wb = openpyxl.load_workbook(CHEMIN_TEMPLATE)
    ws = wb.active
    ws.cell(row=1,column=1).value = MODEL_LLM
    for this_row in range(1, ws.max_row +1):
        for col_original, col_destination in [(6, 6+ len(liste_machines)), (7, 7+ len(liste_machines))] :
            value_to_move = ws.cell(this_row, col_original).value
            ws.cell(this_row, col_destination).value = value_to_move
            ws.cell(this_row, col_original).value = None
    #Cette partie sert a ajouter les machines au tableau
    for indice_machine in range(len(liste_machines)):

        current_machine = liste_machines[indice_machine]
        current_row = LIGNE_DEBUT_MACHINE
        current_column = COLONNE_DEBUT_MACHINE + indice_machine

        ws.cell(row=current_row, column=current_column).value = current_machine.name        #On ajoute le nom de la machine( grace a l'attribut d'objet 'name') au spreadsheet
        ws.cell(row=current_row, column=current_column).border = BORDER_MACHINE_HAUT        
        ws.cell(row=current_row+1, column=current_column).border = BORDER_MACHINE_BAS
        liste_machines[indice_machine].ajouter_coordonnee(ligne=current_row, colonne=current_column)        #On sauvegarde la position de la case de la machine grace a la methode ajouter_coordonnee de la classe machine

    #Cette partie sert a ajouter les exigences au tableau
    current_row = LIGNE_DEBUT_MANDATORY
    for indice_categorie, categorie in enumerate(config_dict.keys()):
        ws.cell(row=current_row, column=COLONNE_DEBUT_CATEGORIE).value = categorie      #On ajoute une seul fois le nom de la categorie au spreadsheet dans la colonne a gauche

        for composant in config_dict[categorie]:
            ws.cell(row=current_row, column=COLONNE_DEBUT_MANDATORY).value = composant.name     #On ajoute le nom du composant dans la colonne des composants en utilisant l'attribut d'objet 'name' de la classe composant. La ligne est current_row, qui augmente a chaque exigence qu'on ajoute et la colonne est COLONNE_DEBUT_MANDATORY qui est la colonne des composants, elle nous bouge pas ce qui nous permet d'utiliser une constante.
            print(composant.liste_machines)
            for machine in composant.liste_machines:
                colonne_machine = machine.colonne
                ws.cell(row=current_row, column=colonne_machine).value = '1'
            current_row += 1

    #Ces lignes permettent la mise en forme du tableau dans le fichier excel.
    for row in ws.iter_rows(min_row=LIGNE_DEBUT_MANDATORY-1, max_col=ws.max_column,min_col=COLONNE_DEBUT_CATEGORIE, max_row=current_row):
        for cell in row:
            cell.border = BORDER
    for row in ws.iter_rows(min_row=LIGNE_TITRES_DEBUT, max_row=LIGNE_TITRES_DEBUT, min_col=COLONNE_TITRES_DEBUT, max_col=ws.max_column):
        for cell in row:
            cell.fill = FOND
    


    #Changer l'extension du fichier ici ci l'extension de la template change
    # wb.save(f"resultat/{nom_fichier}.xlsx")
    # return f"resultat/{nom_fichier}.xlsx"
    wb.save(f'{nom_fichier}.xlsx')
    return f'{nom_fichier}.xlsx'
    



def matrice_conformite(resultat_JSON, fichier_txt):


    liste_machines = conversion_machine(resultat_JSON.keys())       #Conversion du JSON en liste de machines de la classe machine (logic.py)
    liste_composants = conversion_composant(dictionnaire=resultat_JSON, liste_machines=liste_machines)      

    return insertion_excel(config_dict=liste_composants, liste_machines=liste_machines, nom_fichier=fichier_txt)      #Insertion des machines et des composants dans le fichier excel et sauvegarde du fichier excel final dans le dossier resultat
    


