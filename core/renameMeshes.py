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
