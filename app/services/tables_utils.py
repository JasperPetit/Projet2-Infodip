import openpyxl
from openpyxl.utils import get_column_letter

#-----------------------------------------------------------------------------
# Classe permettant de stocker une table comme une liste de listes, puis
# de la manipuler via des fonctions ("tools") que l'on peut mettre a
# disposition pour le LLM
#-----------------------------------------------------------------------------
class TableTools:

    def __init__(self, file_path):

        self.data = []
        self.sheetnames = []
        self.selected = []

        wb = openpyxl.load_workbook(file_path)
        for sheetname in wb.sheetnames:

            self.sheetnames.append(sheetname)
            self.selected.append(False)
            ws = wb[sheetname]

            # Je détermine la dernière colonne et et la dernière ligne avec des données
            last_row = min(ws.max_row, 256)
            last_col = min(ws.max_column, 676)  # 'ZZ' -> (26 * 26 = 676)
            while last_col > 0:
                cl = get_column_letter(last_col)
                for r in range(1, last_row + 1):
                    if ws[cl + str(r)].value is not None:
                        break
                else:
                    last_col -= 1
                    continue
                break

            while last_row > 0:
                rl = str(last_row)
                for c in range(1, last_col + 1):
                    if ws[get_column_letter(c) + rl].value is not None:
                        break
                else:
                    last_row -= 1
                    continue
                break

            sheet_data = []
            if last_row >= 1 and last_col >= 1:

                # Je détermine la première colonne avec des données
                def get_first_col_with_data():
                    for c in range(1, last_col + 1):
                        cl = get_column_letter(c)
                        for r in range(1, last_row + 1):
                            if ws[cl + str(r)].value is not None:
                                return c
                first_col = get_first_col_with_data()

                # Je détermine la ligne des entêtes
                def infer_header_row():
                    nb_cols = last_col - first_col + 1
                    for r in range(1, last_row + 1):
                        rl = str(r)
                        nb_filled = 0
                        for c in range(first_col, last_col + 1):
                            if ws[get_column_letter(c) + rl].value is not None:
                                nb_filled += 1
                        if nb_cols > 2 and nb_filled >= nb_cols - 1: return r
                        if nb_cols > 3 and nb_filled >= nb_cols - 2: return r
                        if nb_cols > 5 and nb_filled >= nb_cols - 3: return r
                        if nb_cols > 9 and nb_filled >= nb_cols - 4: return r
                        if nb_filled == 4: return r
                    return 1
                first_row = infer_header_row()

                for r in range(first_row, last_row + 1):
                    row_data = []
                    rl = str(r)
                    for c in range(first_col, last_col + 1):
                        cell_value = ws[get_column_letter(c) + rl].value
                        cell = ''
                        if cell_value is not None and str(cell_value)[0:1] != '=':
                            # Enlever les \n and limiter a 100 caracteres.
                            cell = str(cell_value).replace('\n', ' ')[:100]
                        row_data.append(cell)
                    sheet_data.append(row_data)

            self.data.append(sheet_data)

    def __len__(self):
        return len(self.data)

    #-----------------------------------------------------------------------------
    def get_row(self, row):
        r = int(row)
        sheet = self.data[self.current_sheet]
        if r < len(sheet):
            return sheet[r]
        return None

    def get_col(self, col):
        c = int(col)
        sheet = self.data[self.current_sheet]
        if c < len(sheet[0]):
            return [sheet[r][c] for r in range(len(sheet)) ]
        return None

    def get_text(self, row, col):
        r = int(row)
        c = int(col)
        sheet = self.data[self.current_sheet]
        if r < len(sheet) and c < len(sheet[0]):
            return sheet[r][c]
        return None

    def find_cell(self, text: str):
        sheet = self.data[self.current_sheet]
        text = str(text).lower()
        for r in range(len(sheet)):
            for c in range(len(sheet[r])):
                val = str(sheet[r][c]).lower()
                if text in val:
                    return r, c
        return -1, -1

    #-----------------------------------------------------------------------------
    def serialize_sheet(self, s, format):

        text = "The table name is '" + self.sheetnames[s] + "' and its content is below:\n\n"

        first_row = True
        for row_data in self.data[s]:

            if   format == 'Markdown': text += "| "
            elif format == 'JSONL':    text += "{['"

            for cell in row_data:
                if format == 'CSV': cell = cell.replace(',', ' ')  # CSV => retirer les virgules.
                text += cell
                if   format == 'Markdown': text += " | "
                elif format == 'JSONL':    text += "', "
                elif format == 'TSV':      text += "\t"
                elif format == 'CSV':      text += ","
            if format == 'JSONL': text = text[:-2] + "]}\n"
            else:                 text = text[:-1] + "\n"

            # Pour Markdown, ajouter une ligne '| --- | --- | ... |' apres la 1ere ligne
            if format == 'Markdown' and first_row: 
                for c in range(len(row_data)):
                    text += "| --- "
                text += "|\n"
            first_row = False
        return text + "\n"

    #-----------------------------------------------------------------------------
    def serialize_selected_sheets(self, format):

        text = ""
        first_sheet = -1
        for s in range(len(self.data)):
            if self.selected[s]:
                text += self.serialize_sheet(s, format)
                if first_sheet == -1:
                    self.current_sheet = s
                    first_sheet = s
        return text

    #-----------------------------------------------------------------------------
    def layout_detect(self, headers):

        layout = "no_header"

        for header in headers:
            if layout == "no_header":
                row, col = self.find_cell(header)
                if row >= 0:
                    layout = "unknown"
                    continue

            r, c = self.find_cell(header)
            if r < 0:
                continue
            if c != col and r == row:
                if layout == "unknown":
                    layout = "column"
                elif layout == "row":
                    return "unknown"
            if r != row and c == col:
                if layout == "unknown":
                    layout = "row"
                elif layout == "column":
                    return "unknown"

        return layout

    #-----------------------------------------------------------------------------
    def reduce_and_serialize(self, s, machine, machines, format):

        self.current_sheet = s

        # Vérifier si la machine est presente dans la feuille
        row, col = self.find_cell(machine)
        if row == -1: return None

        data = self.data[s]
        nb_rows = len(data)
        nb_cols = len(data[0])

        # Detecter la forme de la table
        layout = self.layout_detect(machines)

        text = "The table name is '" + self.sheetnames[s] + "' and its content is below:\n\n"
        prev_first_cell = ""

        # Génération du texte de la table réduite : cas d'une table avec une colonne par machine
        if layout == "column":

            for r in range(nb_rows):

                # Répliquer les catégories à chaque ligne
                cell = data[r][0]
                if cell == None or cell == "":
                    cell = prev_first_cell
                prev_first_cell = cell

                # Retirer les lignes vides pour la machine sélectionnée
                if data[r][col] == "":
                    continue
                if format == "Markdown": text += "| "
                remaining_cols = 0

                # Ne pas inclure les colonnes des machines non sélectionnées
                for c in range(nb_cols):
                    if c == col or data[row][c] not in machines:
                        remaining_cols += 1
                        if c > 0: cell = data[r][c]
                        text += str(cell) if cell is not None else ""
                        if   format == "CSV":      text += ","
                        elif format == "Markdown": text += " | "
                text = text[:-1] + "\n"
                if format == "Markdown" and r == 0:
                    text += "|" + " --- |" * remaining_cols + "\n"
            return text

        # Génération du texte de la table réduite : cas d'une table avec une rangée par machine
        # On transpose la table pour avoir une colonne par machine
        if layout == "row":

            for c in range(nb_cols):

                # Répliquer les catégories à chaque colonne
                cell = data[0][c]
                if cell == None or cell == "":
                    cell = prev_first_cell
                prev_first_cell = cell

                # Retirer les colonnes vides pour la machine sélectionnée
                if data[row][c] == "":
                    continue
                if format == "Markdown": text += "| "
                remaining_cols = 0

                # Ne pas inclure les colonnes des machines non sélectionnées
                for r in range(nb_rows):
                    if r == row or data[r][col] not in machines:
                        remaining_cols += 1
                        if r > 0: cell = data[r][c]
                        text += str(cell) if cell is not None else ""
                        if   format == "CSV":      text += ","
                        elif format == "Markdown": text += " | "
                text = text[:-1] + "\n"
                if format == "Markdown" and c == 0:
                    text += "|" + " --- |" * remaining_cols + "\n"
            return text

        return ""

    #-----------------------------------------------------------------------------
    def tools_info(self):
        info = [
            {
                "type": "function",
                "function": {
                    "name": "get_row",
                    "description": "Return a full row by index (0-based)",
                    "parameters": {
                        "type": "object",
                        "properties": {"row": {"type": "integer"}}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_col",
                    "description": "Return all values in a column by index (0-based)",
                    "parameters": {
                        "type": "object",
                        "properties": {"col": {"type": "integer"}}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_text",
                    "description": "Return the value of a specific cell by row and column index (0-based)",
                    "parameters": {
                        "type": "object",
                        "properties": {"row": {"type": "integer"}, "col": {"type": "integer"}}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_cell",
                    "description": "Find first cell containing the given text. return row and column indexes (0-based)",
                    "parameters": {
                        "type": "object",
                        "properties": {"text": {"type": "string"}}
                    }
                }
            }
        ]
        return info
