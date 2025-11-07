import bpy
# This script traverses the hierarchy of a given object, applies transforms to non-mesh objects (in order to do not have problems with mesh substitution in the next steps)
# and ensures that all mesh objects have unique mesh data.
def applyTransformsToNonMesh(obj, location, rotation, scale, properties):
    for child in obj.children:
        # If is not a mesh, apply transforms
        if child.type != 'MESH':
            bpy.ops.object.select_all(action='DESELECT')
            child.select_set(True)
            bpy.context.view_layer.objects.active = child
            bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale, properties=properties)
        # Recurse through children
        applyTransformsToNonMesh(child, location, rotation, scale, properties)


# This function copy the mesh data when has multiple data users. In this way each mesh will be unique, and is possible to 
# perform operations as transformations, etc... without having system errors
def makeMeshesUniques(obj,array=[]):
    for child in obj.children:
        if child.type == 'MESH':
            array.append(child)
        makeMeshesUniques(child,array)
    for mesh in array:
        if mesh.data.users > 1:
            mesh.data = mesh.data.copy()
    array = []
