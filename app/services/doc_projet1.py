import ollama
import openpyxl
from openpyxl.styles import Border, Side
from openpyxl.utils import get_column_letter
import re
import time
from app.services.tables_utils import TableTools
import os
from ollama import Client

DOSSIER_DOC = os.path.dirname(os.path.abspath(__file__)) # /app/app/services
DOSSIER_APP = os.path.dirname(DOSSIER_DOC) # /app/app
CHEMIN_TEMPLATE = os.path.join(DOSSIER_APP, 'static', 'Matrice-conformité-Infodip-avec-prompts.xlsx')


ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
client = Client(host=ollama_host)

#Modification déjà faite 
def load_excel(file_path):
    
    if file_path is not None:
        table_tool = TableTools(file_path)
        table_tool.current_sheet = 0
        return table_tool
    return None


def estimate_sheets_pertinence(t, model):
    print("Estimating sheets pertinence...")
    if t is not None:
        #t = st.session_state.t
        sheet_pertinences = []
        for s in range(len(t.sheetnames)):
            text = t.serialize_sheet(s, "Markdown")
            messages = [
                {"role": "system", "content": "You are an assistant. You will be given a table full of information, and (a) user query(ies) related to this table. "
                                            "Your role is to answer to the user query by using only the information contained in given table. " },
                {"role": "assistant", "content": text},
                {"role": "user", "content": "Please give a level of confidence as a percentage that this table provides detailed hardware specifications about a physical device or a list of physical devices. "
                                            "Pay attention to the table name and to its content. "
                                            "Please give only the percentage value, without justification or comment." } ]

            response = client.chat( model, messages = messages, options  = {"temperature": 0.01 })
            result = response.message.content

            # Extraire le nombre donné dans la réponse
            match = re.findall(r'\d+', result)
            if match: sheet_pertinences.append(int(match[0]))
            else:     sheet_pertinences.append(0)
        
        return sheet_pertinences
    
    return []


def suggest_machine_names(t, model):

    messages = set_preprompt(t)
    messages.append( {"role": "user", "content": "Please suggest a list of possible machine names that could be found in these tables."
                                       "The machine names are short single words. Provide only the list as a comma-separated string."} )
    response = client.chat(model, messages=messages, options={"temperature": 0.01})
    result = response.message.content

    # Faire une liste des noms fournis
    devices = result.split(',')
    devices = [device.strip() for device in devices if device.strip()]

    return devices 



def set_preprompt(t, machine="", machines=[]):


    # machine = st.session_state.machine
    # machines = [m.strip() for m in st.session_state.machines_text.split(',') if m.strip()]
    if len(machine) > 0 and machine in machines:

        # Selectionner et réduire les feuilles qui concernent la machine
        print("Reducing table(s) for machine", machine)
        content = ""
        for s in range(len(t)):
            if t.selected[s]:
                r, _ = t.find_cell(machine)
                if r >= 0:
                    text = t.reduce_and_serialize(s, machine, machines, "Markdown")
                    if text == "":
                        content += t.serialize_sheet(s, "Markdown")
                    else:
                        content += text
    else:
        content = t.serialize_selected_sheets("Markdown")

    if content:
        print("Setting pre-prompt...")

        messages = [
            {"role": "system", "content": "You are an assistant. You will be given a table full of information, and (a) user query(ies) related to this table. "
                                          "Your role is to answer to the user query by using only the information contained in given table. "
                                          "The table is provided in Markdown format. " },
            {"role": "assistant", "content": content} ]
        return messages
    else:
        messages = []
        return messages
    


def notice_similar_features(val1, val2, ce_mode, liste_doublons, model):

    # cross entropie :
    score = ce_mode.predict([(val1, val2)])[0]

    # Comparaison de vecteurs (produit vectoriel) <== ne calculer embeddings1 qu'une fois
    #embeddings_1 = st.session_state["ce_mode"].encode(value, batch_size=2, max_length=256)['dense_vecs']
    #embeddings_2 = st.session_state["ce_mode"].encode(val)['dense_vecs']
    #score = embeddings_1 @ embeddings_2.T

    if score > 0:
    #if score > 0.6:

        # Demander au LLM d'évaluer la similarité semantique des deux intitulés.
        msgs = [
            {"role": "system", "content": "You are an assistant. Please answer to the user question. "},
            {"role": "user", "content": f"Are the indications '{val1}' and '{val2}' semantically identical? "
                                        "Please answer with percentage value where 0 is for NO and 100 is for YES. "
                                        "Please answer only with the value, withou any comment. "}]
        resp = client.chat(
            model    = model,
            messages = msgs,
            options  = {"temperature": 0.0 },
        )
        res = resp.message.content
        match = re.findall(r'\d+', res)
        if match: eval = int(match[0])
        else:     eval = 0

        if eval >= 90:  # 70 90
            liste_doublons.append({"val1": val1, "val2": val2})
    




def build_compliance_matrix(model, machines, t, loaded_file):

    t_start = time.time()
    ce_mode = None

    if ce_mode is None:
        # Charger un modèle pré-entraîné de cross entropie:
        from sentence_transformers import CrossEncoder

        modelPath = "./ce_model/ms-marco-MiniLM-L6-v2"
        try:
            ce_mode = CrossEncoder(modelPath)
            print("Cross-encodeur charge localement")
        except:
            ce_mode = CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2')
            ce_mode.save(modelPath)
            print("Cross-encodeur rechargé...")

        # Charger un modèle pré-entraîné de vectorisation
        #from FlagEmbedding import BGEM3FlagModel
        #st.session_state["ce_mode"] = BGEM3FlagModel('BAAI/bge-m3') # use_fp16=True) # plus rapide mais un peu moins précis

    # Ouvrir le modèle de matrice de compatibilité vide
    wb = openpyxl.load_workbook(CHEMIN_TEMPLATE)
    ws = wb["Matrice type"]

    # Initialiser la 1ere ligne de caractéristique et la dernière
    feature_start_row = 13
    feature_end_row = 27

    # Récupérer la liste des catégories de caractéristiques (de A13 à A25)
    # -> TODO: détecter la position au lieu de ce codage "en dur"
    feature_types = [ ws.cell(row=r, column=2).value for r in range(feature_start_row, feature_end_row)]
    feature_lines = [ r for r in range(feature_start_row, feature_end_row)]
    feature_lines.append(feature_end_row)
    nb_of_features = len(feature_types)

    # Recuperer les aide pour les prompts dans la colonne F, puis la retirer
    feature_helps = [ ws.cell(row=r, column=8).value for r in range(feature_start_row, feature_end_row)]
    ws.delete_cols(8, 1)


    # Procéder machine par machine
    liste_doublons = []
    for m, machine in enumerate(machines):

        print(f"Analyse de la machine : {machine}", flush=True)

        # Selectionner la feuille qui concerne la machine
        #t = st.session_state.t
        for s in range(len(t.sheetnames)):
            t.current_sheet = s
            if machine in t.sheetnames[s]:
                break
            if t.selected[s]:
                r, _ = t.find_cell(machine)
                if r >= 0:
                    break
        else:
            continue  # Machine non trouvee: on zappe (!). Ou s'arrêter avec status "failed" ?

        text = t.reduce_and_serialize(s, machine, machines, "Markdown")
        if text == None or text == "":
            text = t.serialize_sheet(s, "Markdown")

        # A part pour la première machine, une colonne doit être créée dans la CM
        if m != 0:
            ws.insert_cols(m+5)

        # Ecrire le nom de la machine à la rangée 10
        # TODO: détecter la rangée au lieu de cette valeur 10 en dur.
        ws.cell(row=10, column=m+5).value = machine

        for f, feature in enumerate(feature_types):

            help = feature_helps[f]
            if help is None: help = ""

            # Demander au LLM d'extraire les informations pour cette catégorie et cette machine
            if f == 0:
                messages = [
                    {"role": "system", "content": "You are an assistant. You will be given a table full of information, and a user query related to this table. "
                                                "Your role is to answer to the user by using only the information contained in the table. " },
                    {"role": "assistant", "content": text} ]

            messages.append(
                    {"role": "user", "content": f"What does the table indicate for the {machine} {feature} feature? {help}"
                                                "Please put between square brackets the text found in the table for this feature. "
                                                "If the feature is described in different cells of the table, please put each cell content between separate brackets. "
                                                "If there is no information in the table about this feature, just answer '[None]'. "
                                                "If you found a number, consider it as a multiplication factor. "
                    })

            print("\n----------- Messages -------------")
            for msg in messages:
                print (msg["role"] + ": " + msg["content"])

            response = client.chat(
                model    = model,
                messages = messages,
                options  = {"temperature": 0.0 },
            )
            result = response.message.content

            print("\n----------- Answer ---------------")
            print (response.message.role + ": " + result)
            print("----------------------------------")

            # Extraire le(s) texte(s) entre crochets '[' et ']'
            msg_content = ""
            while True:
                start_index = result.find('[')
                end_index = result.find(']')
                if start_index == -1 or end_index == -1:
                    break

                info = result[start_index + 1 : end_index].strip()
                result = result[end_index +1:]

                # Retirer 'xxx: ' ou 'xxx | ' que des LLMs mettent parfois au début (phi4:14b)
                if info.find(feature + ': ') == 0:
                    index = info.find(': ')
                    info = info[index+2:]
                if info.find(' | ') >= 0:
                    index = info.find(' | ')
                    info = info[index+3:]

                # Filtrer les message indiquant qu'aucune caractéristique n'a été trouvée
                if info.lower()[:2] != 'no' and info.lower()[:2] != 'n/' and info.lower()[:2] != '--' and 0 < len(info) < 200:

                    msg_content += '[' + info + ']'

                    # Function pour trouver ou insérer dans la CM la rangée de la caractéristique trouvée
                    def find_or_insert_row(f, value):
                        if ws.cell(row=feature_lines[f], column=3).value == None or ws.cell(row=feature_lines[f], column=3).value == "":
                            ws.cell(row=feature_lines[f], column=3).value = value
                            return feature_lines[f]

                        for r in range(feature_lines[f], feature_lines[f+1]):
                            if ws.cell(row=r, column=3).value == value:
                                return r

                        # Lister des intitulés semblant équivalents
                        # Comparer le nouvel intitulé avec les intitulés de la catégorie deux à deux
                        for r in range(feature_lines[f], feature_lines[f+1]):

                            val = ws.cell(row=r, column=3).value
                            notice_similar_features(val, value, ce_mode, liste_doublons, model)

                        # Si l'intitulé est nouveau, l'ajouter à la fin de la section
                        r = feature_lines[f+1]
                        ws.insert_rows(r)
                        ws.cell(row=r, column=3).value = value
                        for _f in range(f+1, nb_of_features+1):
                            feature_lines[_f] += 1
                        return r

                    # Placer la nouvelle caractéristique à la bonne rangée
                    r = find_or_insert_row(f, info)

                    # Mettre "1" à l'intersection avec la colonne de la machine
                    ws.cell(row=r, column=m+5).value = "1"

            # Resumer la question et ajouter la réponse dans le chat
            messages[-1] = {"role": "user", "content": f"What is the {feature} feature for {machine} ?"}
            if msg_content == "": msg_content = "[None]"
            messages.append({"role": "assistant", "content": msg_content})

    # Mises en forme: mettre des bordures aux cellules ajoutées
    border = Border(left=Side(style='medium'), right=Side(style='medium'), top=Side(style='medium'), bottom=Side(style='medium'))

    feature_end_row = feature_lines[-1]

    for row in ws['D10': get_column_letter(ws.max_column-2) + "12"]:
        for cell in row:
            cell.border = border

    for row in ws['B' + str(feature_start_row): get_column_letter(ws.max_column) + str(feature_end_row-1)]:
        for cell in row:
            cell.border = border

    # Ajuster les largeurs de colonnes
    for column_cells in ws.columns:
        length = max(len(as_text(cell.value)) for cell in column_cells)
        length = min(50, length) + 2
        ws.column_dimensions[column_cells[0].column_letter].width = length

    # Ecrire le nom du fichier source en case B7
    # TODO: détecter la cellule au lieu de cette valeur en dur.
    #file_name = st.session_state["loaded_file"].name
    file_name = os.path.basename(loaded_file) 
    ws.cell(row=7, column=3).value = file_name

    t_end = time.time()
    print("===> temps passé:", t_end - t_start, "secondes")

    return wb, liste_doublons



#Fonction déjà modifiée.
def as_text(value):
        
        if value is None: 
              return ""
        
        return str(value)


def merge_similar_features(chemin_fichier, decisions_utilisateur):
    """
    chemin_fichier : le chemin vers l'Excel temporaire (ex: "uploads/temp.xlsx")
    decisions_utilisateur : une liste de dictionnaires envoyée par ta page Web
    ex: [{"val1": "Vitesse", "val2": "Vitesse max", "choix": "Vitesse"}, ...]
    """
    
    # 1. On recharge l'Excel depuis le disque dur
    wb = openpyxl.load_workbook(chemin_fichier)
    ws = wb["Matrice type"]

    # 2. On boucle sur les décisions que l'utilisateur a cliquées sur ta page Web
    for decision in decisions_utilisateur:
        val1 = decision["val1"]
        val2 = decision["val2"]
        val = decision["choix"]

        # Si l'utilisateur a dit "Non", on passe au doublon suivant
        if val == "Non": 
            continue

        for r in range(ws.max_row, 12, -1):
            for c in range(3, ws.max_column + 1):
                
                cell_value = ws.cell(row=r, column=c).value
                
                if cell_value == "1":
                    if ws.cell(row=r, column=3).value == val1:
                        ws.cell(row=r, column=3).value = val
                        
                    elif ws.cell(row=r, column=3).value == val2:
                        ws.delete_rows(r)

    chemin_final = "uploads/matrice_finale_validee.xlsx"
    wb.save(chemin_final)
    
    return chemin_final


def save_compliance_matrix(wb, nom_fichier):
    
    # 1. On définit le dossier de destination
    dossier_destination = "uploads"
    
    # Sécurité : on s'assure que le dossier 'uploads' existe bien, sinon on le crée
    if not os.path.exists(dossier_destination):
        os.makedirs(dossier_destination)
        
    # 2. On fabrique le chemin complet (ex: "uploads/matrice_machine1.xlsx")
    chemin_complet = os.path.join(dossier_destination, nom_fichier)
    
    # 3. On sauvegarde le fichier Excel sur le disque dur
    wb.save(chemin_complet)
    
    print(f"Fichier sauvegardé avec succès : {chemin_complet}", flush=True)
    
    # 4. On retourne le chemin pour que ton contrôleur sache où aller le chercher !
    return chemin_complet





