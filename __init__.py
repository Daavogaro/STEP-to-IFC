bl_info = {
    "name": "PLM-to-IFC",
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

# Some links that could be usefull:
# - icons: https://wilkinson.graphics/blender-icons/
# - blender API documentation: https://docs.blender.org/api/current/index.html