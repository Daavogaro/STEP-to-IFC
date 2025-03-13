import bpy


def addIfcElementAssembly(obj,father=None):
    print(f"The name is: {obj.name}")

    bpy.context.scene.BIMRootProperties.ifc_product = 'IfcElement'
    bpy.context.scene.BIMRootProperties.ifc_class = 'IfcElementAssembly'
    bpy.ops.bim.add_element()
    new_ifc_assembly=bpy.context.view_layer.objects.active
    bpy.ops.bim.enable_editing_attributes(mass_operation=False)
    new_ifc_assembly.BIMAttributeProperties.attributes[1].string_value = obj.name
    bpy.ops.bim.edit_attributes()
    bpy.ops.object.select_all(action='DESELECT')
    if not father == None:
        print(f"The father is: {father}")
        print(new_ifc_assembly.BIMObjectProperties.ifc_definition_id)
        bpy.ops.bim.enable_editing_aggregate()
        new_ifc_assembly.BIMObjectAggregateProperties.relating_object = father
        bpy.ops.bim.aggregate_assign_object(relating_object=father.BIMObjectProperties.ifc_definition_id)
        new_ifc_assembly.parent= father

    
def addIfcElement(obj,father=None):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.bim.assign_class(ifc_class='IfcSlab')
    bpy.ops.object.select_all(action='DESELECT')
    new_ifc_assembly=bpy.context.view_layer.objects.active
    
    if not father == None:
        print(f"The father is: {father}")
        print(new_ifc_assembly.BIMObjectProperties.ifc_definition_id)
        bpy.ops.bim.enable_editing_aggregate()
        new_ifc_assembly.BIMObjectAggregateProperties.relating_object = father
        bpy.ops.bim.aggregate_assign_object(relating_object=father.BIMObjectProperties.ifc_definition_id)
        new_ifc_assembly.parent= father
    

    
def createIfcAssemblyTree(obj,father=None):
    addIfcElementAssembly(obj,father)
    new_ifc_assembly=bpy.context.view_layer.objects.active
    for child in obj.children:
        if child.type == 'MESH':
            addIfcElement(child,new_ifc_assembly)
        if child.type not in ['MESH', 'MATERIAL']:
            print(child.name)
            createIfcAssemblyTree(child,new_ifc_assembly)
            
def appendHierarchy(obj,array):
    array.append(obj)
    if obj.children:
        for child in obj.children:
            appendHierarchy(child,array)

def deleteArray(array):
    for obj in array:
        obj.select_set(True)
    bpy.ops.object.delete()
    
    

active_obj = bpy.context.view_layer.objects.active
createIfcAssemblyTree(active_obj)
objects_to_delete = []
appendHierarchy(active_obj,objects_to_delete)
deleteArray(objects_to_delete)
