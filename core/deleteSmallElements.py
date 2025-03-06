import bpy

# Converting geometries from proprietary software to other formats it could be that are generated some leaf object without mesh. 
# A leaf object is an object at the end of the component tree (the root is the object that we select, a leaf is a child that have no children: the last element of the brach)
# The mesh is aggregated under other object, for example in the case of multiple holes for multiple screws
# The following function select all the leaf object of the "active_obj" tree without mesh and hide them
def hideLeafWithNoMesh(obj):
    children = list(obj.children) # A list of all children of obj
    if not children and not obj.type == 'MESH' and not obj.type == 'MATERIAL': # If there are no children and is not a mesh and is not a material the object is hidden
        obj.hide_set(True)
    for child in children: # This function is iterate for the children of each child until there are no more children left
        hideLeafWithNoMesh(child)

# This function hide all the meshes smaller than the variable "min_size"
def hideSmallerThan(obj,min_size):
    if obj.type == 'MESH': # If the object is a mesh
        dimensions = obj.dimensions
        if dimensions.x < min_size and dimensions.y < min_size and dimensions.z < min_size: # And if the mesh has X, Y and Z dimension < than "min_size" then hide the object
            obj.hide_set(True)
    for child in obj.children: # This function is iterate for the children of each child until there are no more children left
        hideSmallerThan(child,min_size)

# If a parent in the tree has all the children that are hidden, the function hide the father.
def hideParentsWithHiddenChildren(obj):
    children = list(obj.children) # A list of all children of obj
    if not children: # If has no children it means that it is a mesh or a material
        return
    all_children_hidden = True # Assume that all children of "obj" are hidden
    for child in children:
        hideParentsWithHiddenChildren(child) # This function is iterate for the children of each child until there are no more children left
        if not child.hide_get(): # If at least a child is not hidden, the assumption done before is wrong
            all_children_hidden = False
    if all_children_hidden: # But if all children are hidden (so the assumption done before is correct), hide the father
        obj.hide_set(True)

# This function delete all the hidden objects
def delete_hidden_elements(obj):
    children = list(obj.children) # A list of all children of obj
    
    # Vengono eliminati ricorsivamente gli elementi nascosti
    for child in children: # This function is iterate for the children of each child until there are no more children left
        delete_hidden_elements(child)
        if child.hide_get(): # If a child is hidden, then remove from the scene
            print(f"Deleting hidden object: {child.name}")
            bpy.data.objects.remove(child, do_unlink=True)
