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

def return_ifc_class(self,file_path,obj):
    # Carica il CSV
    df = pd.read_csv(file_path, encoding="utf-8",delimiter=";")

    # Verifica che la colonna "To be deleted" esista
    if "Ifc Class" not in df.columns:
        self.report({'ERROR'},"Error: The column 'Ifc Class' does not exist in the CSV file.")
        return
    if "Predefined Type" not in df.columns:
        self.report({'ERROR'},"Error: The column 'Predefined Type' does not exist in the CSV file.")
        return
    columns = [col for col in df.columns if col.startswith('Level_')]
    if not columns:
        self.report({'ERROR'},"Error: No column 'Level_X' found in CSV file.")
        return
    levels = df[columns]
    classes_column = df['Ifc Class']
    predefined_type_column = df['Predefined Type']
    meshes_names = levels.apply(lambda row: row.dropna().iloc[-1] if not row.dropna().empty else None, axis=1)
    for mesh_name, class_name,predefined_type in zip( meshes_names,classes_column,predefined_type_column):
        if mesh_name == obj.name:
            if obj.data:
                return class_name, predefined_type
            else:
                print(f"The object {obj} has not a Mesh")
        else:
            print(f"The object {obj} is not in the CSV")



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

    
def addIfcElement(self,obj,file_path,father=None):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    obj.transform_apply(location=False, rotation=True, scale=True)
    element_class,element_predefined_type=return_ifc_class(self,file_path,obj)
    if not pd.isna(element_class):
        bpy.ops.bim.assign_class(ifc_class=element_class)
        bpy.ops.object.select_all(action='DESELECT')
        new_ifc_element=bpy.context.view_layer.objects.active
        if not pd.isna(element_predefined_type):
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
    

    
def createIfcAssemblyTree(self,obj,file_path,father=None):
    addIfcElementAssembly(self,obj,father)
    new_ifc_assembly=bpy.context.view_layer.objects.active
    for child in obj.children:
        if child.type == 'MESH':
            addIfcElement(self,child,file_path,new_ifc_assembly)
        if child.type not in ['MESH', 'MATERIAL']:
            createIfcAssemblyTree(self,child,file_path,new_ifc_assembly)
            

