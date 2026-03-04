class composant:
    def __init__(self, name:str, categorie:str):
        self.name:str = str(name)
        self.liste_machine:machine = []
        self.categorie:str = categorie

    def ajouter_machine(self,machine):
        self.liste_machine.append(machine)
    
    def ajouter_coordonnee(self,x,y):
        self.ligne = x
        self.colonne = y

    def compare(self, composant_to_compare):
        print(f"Comparaison entre {self.name} ({type(self.name)}) et {composant_to_compare.name}({type(composant_to_compare.name)})")
        return self.name.lower() == composant_to_compare.name.lower()
        

class machine:
    def __init__(self,name:str):
        self.name:str = str(name)
    
    def ajouyter_coordonnee(self,x,y):
        self.ligne = x
        self.colonne = y



