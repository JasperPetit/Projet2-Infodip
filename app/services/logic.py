#VERSION=4.3.1
class composant:
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
    def __init__(self,name:str):
        self.name:str = str(name)
    
    def ajouter_coordonnee(self,ligne,colonne):
        self.ligne = ligne
        self.colonne = colonne



