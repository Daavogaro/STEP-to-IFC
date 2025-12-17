import bpy
# This script traverses the hierarchy of a given object, applies transforms to non-mesh objects (in order to do not have problems with mesh substitution in the next steps)
# and ensures that all mesh objects have unique mesh data.
def applyTransformsToNonMesh(obj, location, rotation, scale, properties):
    # If is not a mesh, apply transforms
    if obj.type != 'MESH':
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale, properties=properties)
    for child in obj.children:
        # Recurse through children
        applyTransformsToNonMesh(child, location, rotation, scale, properties)


# This function copy the mesh data when has multiple data users. In this way each mesh will be unique, and is possible to 
# perform operations as transformations, etc... without having system errors
def makeMeshesUniques(obj,array=[]):
    original_name = obj.name
    clean_name = original_name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("<", "_").replace(">", "_").replace("|", "_").replace("#",".")
    # FINISCI DI SISTEMARE QUI
    parts = clean_name.split(".")
    name= ".".join(parts[:-1])
    enum=parts[-1]

    if len(parts) > 1:
        clean_name = name[:-1]+"."+enum if name.endswith(" ") else clean_name
    else:
        clean_name = clean_name[:-1]if clean_name.endswith(" ") else clean_name
    obj.name = clean_name
    for child in obj.children:
        if child.type == 'MESH':
            array.append(child)
        makeMeshesUniques(child,array)
    for mesh in array:
        if mesh.data.users > 1:
            mesh.data = mesh.data.copy()
    array = []
