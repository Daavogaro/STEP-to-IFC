bl_info = {
    "name": "STEP-to-IFC",
    "blender": (3, 0, 0),  # Compatible Blender version
    "category": "Object",  # Category in Blender UI
    "author": "Davide Avogaro - davide.avogaro.2@phd.unipd.it",
    "description": "A simple add-on",
}

from . import operators, panels  # Import other scripts

# This function register all the panel, operator, properties, etc... that the user register in the other files
def register():
    panels.register()
    operators.register()  


def unregister():
    operators.unregister()
    panels.unregister()

if __name__ == "__main__":
    register()

# Some links that could be useful:
# - icons: https://wilkinson.graphics/blender-icons/
# - blender API documentation: https://docs.blender.org/api/current/index.html


# COSE DA FARE:
# - Metti gli errori degli utenti non come print ma come self.report({'ERROR', "..."})
# - Controllare che tutti gli script siano riferiti all'oggetto attivo e non a gli oggetti di scena, se no si fa un casino
# - Ottimizzare il codice soprattutto per la lettura dei CSV: evitare che vengano letti ogni ciclo, ma solo una volta