class composant:
    def __init__(self, name, categorie):
        self.name = name
        self.liste_machine:machine = []
        self.categorie:str = categorie

    def ajouter_machine(self,machine):
        self.liste_machine.append(machine)
    
    def ajouter_coordonnee(self,x,y):
        self.ligne = x
        self.colonne = y

class machine:
    def __init__(self,name):
        self.name = name
    
    def ajouyter_coordonnee(self,x,y):
        self.ligne = x
        self.colonne = y



