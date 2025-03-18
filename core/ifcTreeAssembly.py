import bpy
import pandas as pd

def appendHierarchy(self,obj,array):
    array.append(obj)
    if obj.children:
        for child in obj.children:
            appendHierarchy(self,child,array)

def deleteArray(self,array):
    for obj in array:
        obj.select_set(True)
    bpy.ops.object.delete()

def return_ifc_class(self,obj,meshes_names,classes_column,predefined_type_column,object_type_column):
    ifc_class=None
    ifc_predefined_type=None
    ifc_object_type= None
    for mesh_name, class_name,predefined_type,object_type in zip( meshes_names,classes_column,predefined_type_column,object_type_column):
        if mesh_name == obj.name:
            if obj.data:
                if pd.notna(predefined_type):
                    ifc_predefined_type=predefined_type 
                    if predefined_type == 'USERDEFINED':
                        if pd.notna(object_type):
                            ifc_object_type=object_type
                ifc_class=class_name                           
            else:
                print(f"The object {obj.name} has not a Mesh")
    return ifc_class,ifc_predefined_type,ifc_object_type



def addIfcElementAssembly(self,obj,father=None):
    print("________________________________________________________________________")
    print(f"A new IfcElementAssembly for object: {obj.name}")
    bpy.context.scene.BIMRootProperties.ifc_product = 'IfcElement'
    bpy.context.scene.BIMRootProperties.ifc_class = 'IfcElementAssembly'
    bpy.ops.bim.add_element()
    new_ifc_assembly=bpy.context.view_layer.objects.active
    bpy.ops.bim.enable_editing_attributes(mass_operation=False)
    new_ifc_assembly.BIMAttributeProperties.attributes[1].string_value = obj.name
    bpy.ops.bim.edit_attributes()
    bpy.ops.object.select_all(action='DESELECT')
    if not father == None:
        print(f"    And its father is: {father.name}")
        bpy.ops.bim.enable_editing_aggregate()
        new_ifc_assembly.BIMObjectAggregateProperties.relating_object = father
        bpy.ops.bim.aggregate_assign_object(relating_object=father.BIMObjectProperties.ifc_definition_id)
        new_ifc_assembly.parent= father

    
def addIfcElement(self,obj,meshes_names,classes_column,predefined_type_column,object_type_column,father=None):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    element_class,element_predefined_type,element_object_type=return_ifc_class(self,obj,meshes_names,classes_column,predefined_type_column,object_type_column)
    if not element_class == None:
        print("________________________________________________________________________")
        print(f"A new {element_class} for object: {obj.name}")
        bpy.ops.bim.assign_class(ifc_class=element_class)
        bpy.ops.object.select_all(action='DESELECT')
        new_ifc_element=bpy.context.view_layer.objects.active
        if not element_predefined_type == None:
            bpy.ops.bim.enable_editing_attributes(mass_operation=False)
            new_ifc_element.BIMAttributeProperties.attributes[5].enum_value = element_predefined_type
            bpy.ops.bim.edit_attributes()
            print(f"    And its predefined type is: {element_predefined_type}")
            if not element_object_type == None:
                bpy.ops.bim.enable_editing_attributes(mass_operation=False)
                new_ifc_element.BIMAttributeProperties.attributes[3].string_value = element_object_type
                bpy.ops.bim.edit_attributes()
                print(f"    With Object Type: {element_object_type}")
        if not father == None:
            bpy.ops.bim.enable_editing_aggregate()
            new_ifc_element.BIMObjectAggregateProperties.relating_object = father
            bpy.ops.bim.aggregate_assign_object(relating_object=father.BIMObjectProperties.ifc_definition_id)
            new_ifc_element.parent= father
            print(f"    And its father is: {father.name}")
    bpy.ops.object.select_all(action='DESELECT')
    

    
def createIfcAssemblyTree(self,obj,meshes_names,classes_column,predefined_type_column,object_type_column,father=None):
    addIfcElementAssembly(self,obj,father)
    new_ifc_assembly=bpy.context.view_layer.objects.active
    for child in obj.children:
        if child.type == 'MESH':
            addIfcElement(self,child,meshes_names,classes_column,predefined_type_column,object_type_column,new_ifc_assembly)
        if child.type not in ['MESH', 'MATERIAL']:
            createIfcAssemblyTree(self,child,meshes_names,classes_column,predefined_type_column,object_type_column,new_ifc_assembly)
