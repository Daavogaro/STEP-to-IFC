import bpy
import pandas as pd

# Function for append all the children of an object in array
def appendHierarchy(self,obj,array):
    array.append(obj) # Append the object to the array
    if obj.children: # If there are children
        for child in obj.children: # For each child reiterate the function
            appendHierarchy(self,child,array)

# Function to delete all the element of an array
def deleteArray(self,array):
    for obj in array: # Select each object in the array
        obj.select_set(True)
    bpy.ops.object.delete() # Delete all the selected objects

# Function to return the Ifc data from the CSV
def return_ifc_data(self,obj,meshes_names,classes_column,predefined_type_column,object_type_column):
    # Initialize the variables with the parameter "None". In this way if the values in the CSV are not compiled, the function return a Null value
    ifc_class=None
    ifc_predefined_type=None
    ifc_object_type= None
    # From the CSV are given some arrays of the corresponding columns of the CSV. Arrays are passed sincronously, like for rows
    for mesh_name, class_name,predefined_type,object_type in zip( meshes_names,classes_column,predefined_type_column,object_type_column):
        if mesh_name == obj.name: # If the name of the object is the same of the name of the mesh in the CSV
            if obj.data: # If the object has mesh data (so is not empty)
                if pd.notna(predefined_type): # If the Predefined Type value in the CSV is not empty
                    ifc_predefined_type=predefined_type 
                    if predefined_type == 'USERDEFINED': # If the Predefined Type value in the CSV is 'USERDEFINED'
                        if pd.notna(object_type): # And the Object Type value in the CSV in not empty
                            ifc_object_type=object_type 
                ifc_class=class_name                           
            else:
                print(f"The object {obj.name} has not Mesh Data")
    
    return ifc_class,ifc_predefined_type,ifc_object_type


# Fucntion to create IfcElementAssembly. This class allows to recreate the relationship of the component tree in 
def addIfcElementAssembly(self,obj,father=None):
    print("________________________________________________________________________")
    print(f"A new IfcElementAssembly for object: {obj.name}") # The print of the name is before the command because then it change name
    # These lines are for open the scene for add a new Ifc entity
    bpy.context.scene.BIMRootProperties.ifc_product = 'IfcElement'
    bpy.context.scene.BIMRootProperties.ifc_class = 'IfcElementAssembly'
    bpy.ops.bim.add_element() 
    new_ifc_assembly=bpy.context.view_layer.objects.active # Insert in a variable the active object (the ifcElementAssembly that has been created)
    # These lines are for editing the name
    bpy.ops.bim.enable_editing_attributes(mass_operation=False)
    new_ifc_assembly.BIMAttributeProperties.attributes[1].string_value = obj.name
    bpy.ops.bim.edit_attributes()
    bpy.ops.object.select_all(action='DESELECT')
    # If father is not None
    if not father == None:
        print(f"    And its father is: {father.name}")
        # Aggregate the new IfcElementAssmebly under its father
        bpy.ops.bim.enable_editing_aggregate()
        new_ifc_assembly.BIMObjectAggregateProperties.relating_object = father
        bpy.ops.bim.aggregate_assign_object(relating_object=father.BIMObjectProperties.ifc_definition_id)
        # Recreate the tree in the Blender Menu giving the parent relation to the Blender Object. Is not necessary for the IFC sake, but is useful for the Blender visualization
        new_ifc_assembly.parent= father 

# Function for adding IfcElement based on the CSV values 
def addIfcElement(self,obj,meshes_names,classes_column,predefined_type_column,object_type_column,father=None):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    # Obtain the value of the CSV values from the function "return_ifc_data"
    element_class,element_predefined_type,element_object_type=return_ifc_data(self,obj,meshes_names,classes_column,predefined_type_column,object_type_column)
    # With this function if an object in the CSV has no Ifc Class value compiled, it won't be created and then it will be deleted.
    if not element_class == None:
        print("________________________________________________________________________")
        print(f"A new {element_class} for object: {obj.name}")
        # This time we don't add a new IFC element, but we convert the mesh in an IfcElement
        bpy.ops.bim.assign_class(ifc_class=element_class)
        bpy.ops.object.select_all(action='DESELECT')
        new_ifc_element=bpy.context.view_layer.objects.active
        bpy.ops.bim.enable_editing_attributes(mass_operation=False) # Enable the editing attributes mode
        if not element_predefined_type == None:
            new_ifc_element.BIMAttributeProperties.attributes[5].enum_value = element_predefined_type # Edit the Predefined Type
            print(f"    And its predefined type is: {element_predefined_type}")
            if not element_object_type == None:
                new_ifc_element.BIMAttributeProperties.attributes[3].string_value = element_object_type # Edit the Object Type
                print(f"    With Object Type: {element_object_type}")
        bpy.ops.bim.edit_attributes() # Confirm the editing
        if not father == None:
            bpy.ops.bim.enable_editing_aggregate()
            new_ifc_element.BIMObjectAggregateProperties.relating_object = father
            bpy.ops.bim.aggregate_assign_object(relating_object=father.BIMObjectProperties.ifc_definition_id)
            new_ifc_element.parent= father
            print(f"    And its father is: {father.name}")
    bpy.ops.object.select_all(action='DESELECT')
    

# Create the tree of IfcElementAssembly with IfcElement as leaf objects
def createIfcAssemblyTree(self,obj,meshes_names,classes_column,predefined_type_column,object_type_column,father=None):
    addIfcElementAssembly(self,obj,father) # The hypotesis is that the first object is a container for other object
    new_ifc_assembly=bpy.context.view_layer.objects.active
    for child in obj.children:
        if child.type == 'MESH':
            # All the meshes need to be converted in Ifc Elements
            addIfcElement(self,child,meshes_names,classes_column,predefined_type_column,object_type_column,new_ifc_assembly)
        if child.type not in ['MESH', 'MATERIAL']:
            # All the objects that are not meshes or material (so Blender objects) are converted in IfcElementAssembly
            createIfcAssemblyTree(self,child,meshes_names,classes_column,predefined_type_column,object_type_column,new_ifc_assembly)
