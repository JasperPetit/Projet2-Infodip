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


from pdf2image import convert_from_path
import pytesseract
import ollama

def extraction_tesseract(fichier_pdf):
    print(f"1. Découpage du PDF '{fichier_pdf}'...")
    pages = convert_from_path(fichier_pdf)
    texte_complet = ""

    print(f"2. Lecture par Tesseract ({len(pages)} pages)...")
    for index, page_img in enumerate(pages):
        print(f"-> Scan foudroyant de la page {index + 1}...")
        
        # Le scan OCR pur et dur (langue configurée sur Français + Anglais)
        texte = pytesseract.image_to_string(page_img, lang='fra+eng')
        
        texte_complet += f"\n\n=== PAGE {index + 1} ===\n{texte}\n"
    return texte_complet


def ChatOllama(texte_complet):
    response: ollama.ChatResponse = ollama.chat(
        model="llama3.3:70b",
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

if __name__ == "__main__":
    fichier_pdf = "VEGA-Banc-Besoin_Materiel_banc -A.pdf" 
    txt = extraction_tesseract(fichier_pdf)
    print(txt)
    ChatOllama(txt)
    print("=================FIN DU PROGRAMME===========")