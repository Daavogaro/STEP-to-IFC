def makeMeshesUniques(obj,array=[]):
    for child in obj.children:
        if child.type == 'MESH':
            array.append(child)
        makeMeshesUniques(child,array)
    enum = 1
    for mesh in array:
        if mesh.data.users > 1:
            mesh.data = mesh.data.copy()
    array = []
