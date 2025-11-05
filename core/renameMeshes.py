import bpy
# This script traverses the hierarchy of a given object, applies transforms to non-mesh objects (in order to do not have problems with mesh substitution in the next steps)
# and ensures that all mesh objects have unique mesh data.
def makeMeshesUnique_and_ApplyNonMeshTransforms(obj, mesh_list=None):
    # If the array is not provided, initialize it
    if mesh_list is None:
        mesh_list = []

    for child in obj.children:
        # If is a mesh, append it in the array
        if child.type == 'MESH':
            mesh_list.append(child)
       
        # If is not a mesh, apply transforms
        if child.type != 'MESH':
            bpy.ops.object.select_all(action='DESELECT')
            child.select_set(True)
            bpy.context.view_layer.objects.active = child
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True, properties=True)
        # Recurse through children
        makeMeshesUnique_and_ApplyNonMeshTransforms(child, mesh_list)

    # After traversal at root level → ensure mesh data is unique
    for mesh_obj in mesh_list:
        if mesh_obj.data.users > 1:
            mesh_obj.data = mesh_obj.data.copy()
