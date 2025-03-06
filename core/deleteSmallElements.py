import bpy

# Function to hide collections if all their children are hidden
def hideLeafWithNoMesh(obj):
    # Vengono cercati i figli di obj
    children = list(obj.children)
    # Tutti quelli che non hanno figli e che non sono né mesh né materiali devono essere nascosti
    if not children and not obj.type == 'MESH' and not obj.type == 'MATERIAL':
        obj.hide_set(True)
    # Quelli che hanno figli devono reiterare questa cosa funzione nei loro figli
    for child in children:
        hideLeafWithNoMesh(child)

# Questa funzione nasconde il padre se tutti i figli sono nascosti
def hideParentsWithHiddenChildren(obj):
    # Vengono cercati i figli di obj
    children = list(obj.children)
    # Se non ha figli a posto, vuol dire che è una mesh o un materiale
    if not children:
        return
    # Ipotizziamo che tutti i figli sono nascosti
    all_children_hidden = True
    for child in children:
        hideParentsWithHiddenChildren(child)
        # Se i figli non sono nascosti la nostra ipotesi era sbagliata
        if not child.hide_get():
            all_children_hidden = False
        # Se tutti i figli sono nascosti allora dobbiamo nascondere il padre
    if all_children_hidden:
        obj.hide_set(True)


# Function to select mesh objects in the hierarchy (including the active object)
def isSmallerThan(obj,min_size):
    # Select the current object if it's a mesh
    
    if obj.type == 'MESH':
        dimensions = obj.dimensions
        if dimensions.x < min_size and dimensions.y < min_size and dimensions.z < min_size:
            obj.hide_set(True)
    
    # Recursively check and select mesh objects from the children
    for child in obj.children:
        isSmallerThan(child,min_size)

def delete_hidden_elements(obj):
    # Vengono cercati i figli di obj
    children = list(obj.children)
    
    # Vengono eliminati ricorsivamente gli elementi nascosti
    for child in children:
        delete_hidden_elements(child)
        
        # Se il figlio è nascosto, rimuovilo dalla scena
        if child.hide_get():
            print(f"Deleting hidden object: {child.name}")
            bpy.data.objects.remove(child, do_unlink=True)
