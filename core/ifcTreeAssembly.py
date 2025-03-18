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

def return_ifc_class(self,obj,meshes_names,classes_column,predefined_type_column):
    ret1=None
    ret2=None
    for mesh_name, class_name,predefined_type in zip( meshes_names,classes_column,predefined_type_column):
        if mesh_name == obj.name:
            if obj.data:
                if pd.isna(class_name):
                    class_name = None
                if pd.isna(predefined_type):
                    predefined_type = None
                ret1=class_name
                ret2=predefined_type
                
            else:
                print(f"The object {obj.name} has not a Mesh")
                
        else:
            print(f"The object {obj.name} is not the same of {mesh_name}")
    return ret1,ret2



def addIfcElementAssembly(self,obj,father=None):
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

    
def addIfcElement(self,obj,meshes_names,classes_column,predefined_type_column,father=None):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    element_class,element_predefined_type=return_ifc_class(self,obj,meshes_names,classes_column,predefined_type_column)
    if not element_class == None:
        print(f"The class is {element_class}")
        bpy.ops.bim.assign_class(ifc_class=element_class)
        bpy.ops.object.select_all(action='DESELECT')
        new_ifc_element=bpy.context.view_layer.objects.active
        if not element_predefined_type == None:
            print(f"The Predefined Type is {element_predefined_type}")
            bpy.ops.bim.enable_editing_attributes(mass_operation=False)
            new_ifc_element.BIMAttributeProperties.attributes[5].enum_value = element_predefined_type
            bpy.ops.bim.edit_attributes()
        if not father == None:
            print(f"The father is: {father}")
            print(new_ifc_element.BIMObjectProperties.ifc_definition_id)
            bpy.ops.bim.enable_editing_aggregate()
            new_ifc_element.BIMObjectAggregateProperties.relating_object = father
            bpy.ops.bim.aggregate_assign_object(relating_object=father.BIMObjectProperties.ifc_definition_id)
            new_ifc_element.parent= father
    bpy.ops.object.select_all(action='DESELECT')
    

    
def createIfcAssemblyTree(self,obj,meshes_names,classes_column,predefined_type_column,father=None):
    addIfcElementAssembly(self,obj,father)
    new_ifc_assembly=bpy.context.view_layer.objects.active
    for child in obj.children:
        if child.type == 'MESH':
            addIfcElement(self,child,meshes_names,classes_column,predefined_type_column,new_ifc_assembly)
        if child.type not in ['MESH', 'MATERIAL']:
            createIfcAssemblyTree(self,child,meshes_names,classes_column,predefined_type_column,new_ifc_assembly)
