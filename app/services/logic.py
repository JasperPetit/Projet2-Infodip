#VERSION=4.3.1
class composant:
    """
    Cette classe represente une exigence/composant d'une machine. Nous l'avons créer car elle nous permet de suivre le nom des eigence, les machines aquel elle sont relié ainsi que leur position, ce qui nous facilite grandement l'insertion dans le excel.
    Attributs:
    - name (str): le nom de l'exigence
    - liste_machines (list): la liste des machines DE TYPE MACHINE auquel l'exigence est relié. Ceci nous permet de boucler sur la liste des machines lors de l'insertion dans le excel et d'insérer l'exigence dans la bonne machine.
    - categorie (str): la categorie de l'exigence.
    - ligne (int): la ligne de l'exigence lors de l'insertion dans le excel
    - colonne (int): la colonne de l'exigence lors de l'insertion dans le excel

    """
    def __init__(self, name:str, categorie:str):
        self.name:str = str(name)
        self.liste_machines:machine = []
        self.categorie:str = categorie

    def ajouter_machine(self,machine):
        self.liste_machines.append(machine)
    
    def ajouter_coordonnee(self,ligne,colonne):
        self.ligne = ligne
        self.colonne = colonne

    def compare(self, composant_to_compare):
        print(f"Comparaison entre {self.name} ({type(self.name)}) et {composant_to_compare.name}({type(composant_to_compare.name)})")
        return self.name.lower() == composant_to_compare.name.lower()
        

class machine:
    """
    Similairement a la classe composant, machine represente une machine. Elle contient également son nom ainsi que ses coordonnées lors de l'nsertion. C
    attributs:
    - name (str): le nom de la machine
    - ligne (int): la ligne de la machine lors de l'insertion dans le excel
    - colonne (int): la colonne de la machine lors de l'insertion dans le excel
    """
    def __init__(self,name:str):
        self.name:str = str(name)
    
    def ajouter_coordonnee(self,ligne,colonne):
        self.ligne = ligne
        self.colonne = colonne



