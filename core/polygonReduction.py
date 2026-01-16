import bpy

def reduce_mesh(obj):
    if obj.type == 'MESH':
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        print(obj.name)
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.tris_convert_to_quads()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete_loose()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.face_make_planar()
        # bpy.ops.mesh.select_all(action='SELECT')
        # bpy.ops.mesh.dissolve_limited()   
        # bpy.ops.mesh.dissolve_limited(angle_limit=0.261799)
        # bpy.ops.mesh.dissolve_limited(angle_limit=0.04)
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.select_all(action='DESELECT')

    # Recurse children
    for child in obj.children:
        reduce_mesh(child)
