#ma venv c'est docenv
# from docling.document_converter import DocumentConverter

# def messi(source): 
   
#     converter = DocumentConverter()
#     result = converter.convert(source)
#     mark = result.document.export_to_markdown()

#     with open('fichier_markdown.txt', 'w', encoding='utf-8') as f:
#         f.write(mark)
#         print("ok")


# if __name__ == "__main__":
#     fichier_pdf = "Mail TALC SI.docx" 
#     messi(fichier_pdf)


import ollama
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
import json 
# Import des types d'éléments pour les reconnaître
from docling_core.types.doc.document import TextItem, TableItem, PictureItem

import pytesseract

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
    print("===========Resultat===========")
    print(resultat)
    print("============FIN DE RESULTAT===========")
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
            print("   -> Image détectée ! Lancement du scan Tesseract...")
            
            # On récupère l'image sous forme de variable (format PIL Image)
            image_pil = item.get_image(doc)
            
            if image_pil is not None:
                # Ton code Tesseract classique entre en action
                texte_image = pytesseract.image_to_string(image_pil, lang='fra+eng')
                
                # On ajoute des balises pour aider Qwen à comprendre d'où ça vient
                texte_final += f"--- DÉBUT TEXTE LU SUR IMAGE ---\n{texte_image.strip()}\n--- FIN TEXTE LU SUR IMAGE ---\n\n"
                
    print("\nVICTOIRE ! Assemblage terminé.")
    print(texte_final)
    return texte_final


def ChatOllama(texte_final):
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
                Voici le texte : {texte_final}
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
    dict= json.load(response.message.content)



if __name__ == "__main__":
    # Tu peux mettre un .pdf ou un .docx ici !
    fichier = "CDC Arcelor mittal.pdf" 
    
    # On lance la nouvelle extraction magique
    texte_propre = extraction_sur_mesure(fichier)
    
    # On sauvegarde pour que tu puisses vérifier à l'oeil nu (très utile pour débugger)
    with open('resultat_docling.md', 'w', encoding='utf-8') as f:
        f.write(texte_propre)
    
    # On envoie le Markdown parfait à ton Qwen
    print("\n--- Envoi à Qwen pour génération du JSON ---")
    ChatOllama(texte_propre)
    
    print("\n================= FIN DU PROGRAMME ===============")