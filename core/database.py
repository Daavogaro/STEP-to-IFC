import os
import csv
import pandas as pd  # Library for handling CSV files
import bpy
import bonsai.tool.ifc as ifcTool
import ifcopenshell
import bonsai.tool as tool
from mathutils import Vector
from . import importCSV
from . import deleteSmallElements

# TODO: Controllare se servono tutte le sostituzioni di caratteri
# TODO: Controllare che ci siano solo le funzioni che servono

def print_rows(obj, written_names=None,csv_changed=False):
    # Written names is a set that contains the names already written in the CSV, to avoid duplicates
    if written_names is None:
        written_names = set()
    # Clean and normalize name
    old_name = obj.name
    obj.name = old_name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("<", "_").replace(">", "_")
    parts = obj.name.split(".")
    base_name = ".".join(parts[:-1]) if len(parts) > 1 else obj.name
    level = obj.get("LevelOfDetail", None)
    rows = []

    # For the leaf nodes (no children)
    if not obj.children:
        if base_name not in written_names: # If is not already written
            written_names.add(base_name)
            csv_changed=True
            if obj.get("JoinChildren", False) is True and obj != bpy.context.view_layer.objects.active: # If JoinChildren is True and is not the active object
                row = [base_name, "Yes", level,"","" if level else ""]
                rows.append(row)
            else:
                rows.append([base_name])
        return rows, csv_changed 

    # For the nodes with JoinChildren True (non-leaf)
    if obj.get("JoinChildren", False) is True and obj != bpy.context.view_layer.objects.active:
        print(f"The active obj is {bpy.context.view_layer.objects.active.name} and the object is {obj.name}")
        if base_name not in written_names:
            row = [base_name, "Yes", level,"","" if level else ""]
            rows.append(row)
            csv_changed=True
            written_names.add(base_name)
        return rows,csv_changed

    # For the recursion case
    for child in obj.children:
        child_rows, child_changed = print_rows(child, written_names, csv_changed)
        rows.extend(child_rows)
        if child_changed:
            csv_changed = True

    return rows,csv_changed


def create_or_find_csv(obj, database_path):
    # Replace not allowed characters in object name
    obj.name = obj.name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("<", "_").replace(">", "_")
    parts = obj.name.split(".")
    # Select only the base name without the progression number that Blender/CATIA adds automatically
    file_name = ".".join(parts[:-1]) if len(parts) > 1 else obj.name
    # Process this object if JoinChildren True
    if obj.get("JoinChildren", False) is True:
        completed_file_path = os.path.join(database_path, "Completed", f"{file_name}.csv") # Path to the completed CSV file
        to_be_completed_file_path = os.path.join(database_path, "To be completed", f"{file_name}.csv") # Path to the "to be completed" CSV file
        # If the completed CSV exists in the completed folder
        if os.path.exists(completed_file_path): 
            print(f"Already completed: {completed_file_path}")
            # Read existing CSV to add new rows if there are new objects
            # ! Still problems with new rows addition: in the file X.csv the second time it runs it write a X row, even if it should not
            df = pd.read_csv(completed_file_path,encoding="utf-8",sep=";",engine="python")
            old_rows = df.values.tolist()  # Converts all existing CSV rows to list of lists
            old_rows = df.fillna("").values.tolist()  # Replace NaN with empty string
            # Check if "Element Name" column exists
            if "Element Name" not in df.columns:
                print(f"{completed_file_path} has not Element Name column")
                return
            element_names = df["Element Name"].dropna().astype(str).tolist()
            bpy.context.view_layer.objects.active=obj
            rows, csv_changed = print_rows(obj,set(element_names)) # It returns the new rows to add and if there was any change
            # If there are new rows, append them to the completed CSV
            if csv_changed is True:
                print(obj.name)
                with open(to_be_completed_file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file, delimiter=';')
                    all_rows = old_rows + rows
                    # Header
                    writer.writerow(
                        ["Element Name","Product in DB","LOD Preset","To be deleted","MID: To be simplified","IfcClass","PredefinedType","ObjectType","Pset_NameXX/Prop_NameYY","Pset_NameXX/Prop_NameYY"]
                    )
                    writer.writerows(all_rows)
        # If the completed CSV does not exist, create a new "to be completed" CSV    
        else:
            if not os.path.exists(to_be_completed_file_path):
                 with open(to_be_completed_file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file, delimiter=';')
                    bpy.context.view_layer.objects.active=obj
                    # Header
                    writer.writerow(
                        ["Element Name","Product in DB","LOD Preset","To be deleted","MID: To be simplified","IfcClass","PredefinedType","ObjectType","Pset_NameXX/Prop_NameYY","Pset_NameXX/Prop_NameYY"]
                    )
                    # Data rows
                    rows, csv_changed = print_rows(obj)
                    writer.writerows(rows)

    # Iterate through children
    for child in obj.children:
        create_or_find_csv(child, database_path)

# Function to control if the object is in the database and set JoinChildren and LOD properties
def control_database(obj,database_path):
    completed_folder_path = os.path.join(database_path, "Completed")
    parts = obj.name.split(".")
    file_name = ".".join(parts[:-1]) if len(parts) > 1 else obj.name
    file_path = os.path.join(completed_folder_path, f"{file_name}.csv")
    if os.path.exists(file_path):
        # Read existing CSV to get the simplification info
        df = pd.read_csv(file_path, encoding="utf-8", delimiter=";")
        # Now we want to select only the nodes of our assembly
        if "Product in DB" not in df.columns:
            return
        if "LOD Preset" not in df.columns:
            return
        df_filtered = df[df["Product in DB"] == "Yes"] # Filter rows where "Product in DB" is "Yes"
        element_names = df_filtered["Element Name"].dropna().astype(str) # Get the list of element names
        df_lod_filtered = df["LOD Preset"].dropna().astype(str).tolist()
        bpy.ops.object.select_all(action='DESELECT')
        select_hierarchy(obj) # Select the entire hierarchy of the object selected. This because there could be more objects that have the same base name around the assembly. We want to process only the children of the selected assembly
        objects = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')
        object_to_iterate=[] # List of objects that are nodes in the database, for which we have to reiterate the simplification

        for object in objects: # Between the selected objects, find the ones that are in the database and append them to the list
            parts = object.name.split(".")
            file_name = ".".join(parts[:-1]) if len(parts) > 1 else object.name
            for idx, element_name in element_names.items():
                if file_name == element_name:
                    object["JoinChildren"]=True
                    object["LevelOfDetail"] = df_lod_filtered[idx]
                    object_to_iterate.append(object)
        if len(object_to_iterate)>0: # If there are objects to iterate, call the function recursively
            for o in object_to_iterate:    
                control_database(o,database_path)   



# Recursive function to find all meshes inside an object
def find_meshes_inside(obj, array=None):
    if array is None:
        array = []
    # active_root = bpy.context.view_layer.objects.active # Penso si possa eliminare

    # Skip only this object if JoinChildren=True and not active root, in order to avoid to skip the entire subtree only because the first active object has JoinChildren=True
    if obj.get("JoinChildren", False) is True and not obj==bpy.context.view_layer.objects.active:
        return
    else:
        if obj.type == 'MESH':
            array.append(obj)
    # Always recurse through children
    for child in obj.children:
        find_meshes_inside(child, array)
    return array

# Recursive function to find all meshes inside an object
def find_children_meshes(obj, meshes=None):
    if meshes is None:
        meshes = []
    
    for child in obj.children:
        if child.get("JoinChildren", False): # It does not go deeper if JoinChildren is True
            continue  
        if child.type == "MESH":
            meshes.append(child)
        find_children_meshes(child, meshes)
    return meshes

# Recursive function to select an object and all its children
def select_hierarchy(obj):
    obj.select_set(True)
    for child in obj.children:
        select_hierarchy(child)


def simplify_geometries_csv(obj,database_path):
    completed_folder_path = os.path.join(database_path, "Completed")
    # Replace all not allowed characters in object name
    obj.name = obj.name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("<", "_").replace(">", "_")
    # Select only the base name without the progression number that Blender/CATIA adds automatically
    parts = obj.name.split(".")
    file_name = ".".join(parts[:-1]) if len(parts) > 1 else obj.name
    file_path = os.path.join(completed_folder_path, f"{file_name}.csv")
    # If the completed CSV exists in the completed folder
    if os.path.exists(file_path):
        # Read existing CSV to get the simplification info
        df = pd.read_csv(file_path, encoding="utf-8", delimiter=";")
        # Now we want to select only the nodes of our assembly
        if "Product in DB" not in df.columns:
            return
        df_filtered = df[df["Product in DB"] == "Yes"] # Filter rows where "Product in DB" is "Yes"
        element_names = df_filtered["Element Name"].dropna().astype(str).tolist() # Get the list of element names
        bpy.ops.object.select_all(action='DESELECT')
        select_hierarchy(obj) # Select the entire hierarchy of the object selected. This because there could be more objects that have the same base name around the assembly. We want to process only the children of the selected assembly
        objects = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')

        object_to_iterate=[] # List of objects that are nodes in the database, for which we have to reiterate the simplification

        for object in objects: # Between the selected objects, find the ones that are in the database and append them to the list
            object.name = object.name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("<", "_").replace(">", "_")
            parts = object.name.split(".")
            file_name = ".".join(parts[:-1]) if len(parts) > 1 else object.name
            for element_name in element_names:
                if file_name == element_name:
                    object_to_iterate.append(object)
        if len(object_to_iterate)>0: # If there are objects to iterate, call the function recursively
            for o in object_to_iterate:
                simplify_geometries_csv(o,database_path)
        # For element under our nodes, apply the simplification or deletion
        if "To be deleted" not in df.columns:
            return        
        df_del_filtered = df[df["To be deleted"] == "Yes"]
        if "MID: To be simplified" not in df.columns:
            return        
        df_sim_filtered = df[df["MID: To be simplified"] == "Yes"]
        # If the selected node is a mesh itself (for objects that are already merged from other softwares), so it is a leaf node
        if obj.type == "MESH":
            if obj.get("LevelOfDetail", False) == "LOW":
                bbox=importCSV.create_bbox(obj)
                level = obj.get("LevelOfDetail", None)
                if level is not None:
                    bbox["LevelOfDetail"] = level
                bbox["JoinChildren"]=True
                bpy.data.objects.remove(obj, do_unlink=True)
            if obj.get("LevelOfDetail", False) == "MEDIUM" or obj.get("LevelOfDetail", False) and not obj.get("LevelOfDetail", False) == "HIGH" :
                parts = obj.name.split(".")
                file_name = ".".join(parts[:-1]) if len(parts) > 1 else obj.name
                to_simplify=df_sim_filtered["Element Name"].dropna().astype(str).tolist()
                if file_name in to_simplify:
                    bbox=importCSV.create_bbox(obj)
                    level = obj.get("LevelOfDetail", None)
                    if level is not None:
                        bbox["LevelOfDetail"] = level
                    bbox["JoinChildren"]=True
                    bpy.data.objects.remove(obj, do_unlink=True)
        # If the selected node is not a mesh, so it has children to process and to join, in order to create a leaf node
        else:
            # Find all meshes inside the object
            meshes=find_children_meshes(obj)
            print(f"For the object {obj.name} there are {len(meshes)} mesehes to process")
            to_delete=df_del_filtered["Element Name"].dropna().astype(str).tolist() # Name list of elements to delete
            to_simplify=df_sim_filtered["Element Name"].dropna().astype(str).tolist() # Name list of elements to simplify
            remaining_meshes=[] # List of all the meshes simplified or not to join later
            for mesh in meshes:
                parts = mesh.name.split(".")
                file_name = ".".join(parts[:-1]) if len(parts) > 1 else mesh.name
                # For the LOD "LOW" we delete the mesh that in the CSV is marked as "to be deleted" and we create a bbox for the all the remaining meshes
                if obj.get("LevelOfDetail", False) == "LOW":
                    if file_name in to_delete:
                        bpy.data.objects.remove(mesh, do_unlink=True)
                    else:
                        bbox=importCSV.create_bbox(mesh)
                        remaining_meshes.append(bbox)
                        bpy.data.objects.remove(mesh, do_unlink=True)
                    continue
                # For the LOD "MEDIUM" we delete the mesh that in the CSV is marked as "to be deleted", we simplify the ones marked as "to be simplified" and we keep the remaining ones
                if obj.get("LevelOfDetail", False) == "MEDIUM" or obj.get("LevelOfDetail", False) and not obj.get("LevelOfDetail", False) == "HIGH" :
                    if file_name in to_delete:
                        bpy.data.objects.remove(mesh, do_unlink=True)
                    else:
                        if file_name in to_simplify:
                            bbox=importCSV.create_bbox(mesh)
                            remaining_meshes.append(bbox)
                            bpy.data.objects.remove(mesh, do_unlink=True)
                        else:
                            remaining_meshes.append(mesh)
                    continue
                # For the LOD "HIGH" we do not delete any meshes and we keep all the meshes as they are     
                if obj.get("LevelOfDetail", False) == "HIGH":
                    remaining_meshes.append(mesh)
                    continue
            # Now we have the list of remaining meshes to join, we move them as children of the main object to keep the hierarchy
            for mesh in remaining_meshes:    
                mesh.parent=obj
            # We delete all the hierarchy that not contains meshes anymore        
            deleteSmallElements.hideLeafWithNoMesh(obj)
            deleteSmallElements.hideParentsWithHiddenChildren(obj)
            deleteSmallElements.delete_hidden_elements(obj)
            # TODO Prova a semplifcare utiliuzzando direttamente le mesh in remaining_meshes senza creare un nuovo array
            # Select only the remaining meshes to join them
            meshes_to_join=[]
            for child in obj.children:
                if child.get("JoinChildren", False) is True:
                    continue
                if child.type == 'MESH':
                    meshes_to_join.append(child)
            bpy.ops.object.select_all(action='DESELECT')
            if len(meshes_to_join)>0:
                bpy.context.view_layer.objects.active = meshes_to_join[0] #Set the first element as active
                for mesh in meshes_to_join: # Select all the meshes to join
                    mesh.select_set(True)
                meshes_to_join=[]
                # Join all the meshes
                for area in bpy.context.window.screen.areas:
                    if area.type == 'VIEW_3D':
                        with bpy.context.temp_override(area=area):
                            bpy.ops.object.join()
                        break
                # Now the active object is the joined one
                joined_obj=bpy.context.view_layer.objects.active
                # Give it proper name and properties
                old_name = obj.name
                level = obj.get("LevelOfDetail", None)
                if level is not None:
                    joined_obj["LevelOfDetail"] = level
                parent = obj.parent
                # If there is a parent
                if parent is not None:
                    joined_obj.parent = parent # TODO Controllare se serve o se è una riassegnazione inutile
                    children = obj.children
                    joined_children=[]
                    # If in the children there are other nodes with JoinChildren True, we don't want to delete the father node (empty Blender object), with a mesh. So we substitute the father node with a mesh node of the joined elements, and as children we put the other joined meshes
                    # This way we keep the hierarchy when the STEP model is a little bit messy and all the parts are not properly grouped
                    for child in children:
                        if child.type=="MESH" and child.get("JoinChildren", False) is True:
                            joined_children.append(child)
                    if len(joined_children)>0:
                        # Sobstitute the father node with a mesh node that contains the joined meshes
                        new_obj= bpy.data.objects.new(joined_obj.name,joined_obj.data)
                        for collection in obj.users_collection:
                            collection.objects.link(new_obj)
                        new_obj.matrix_world =joined_obj.matrix_world.copy()
                        # Reassign all the nodes to the new object
                        for child in children:
                            old_world = child.matrix_world.copy()
                            child.parent = new_obj
                            child.matrix_world = old_world
                        # Reassign the properties
                        bpy.data.objects.remove(joined_obj, do_unlink=True)
                        bpy.data.objects.remove(obj, do_unlink=True)
                        new_obj.name = old_name
                        new_obj.data.name = old_name
                        new_obj["JoinChildren"]=True
                        new_obj.parent = parent
                        if level is not None:
                            new_obj["LevelOfDetail"] = level
                    else:
                        # If the STEP model is well organized, sobsitute the empty father node with the joined mesh
                        bpy.data.objects.remove(obj, do_unlink=True)
                        joined_obj.name = old_name
                        joined_obj.data.name = old_name
                        joined_obj["JoinChildren"]=True
                else: # If there is not a parent, simply sobsitute the empty father node with the joined mesh
                    print(f"{obj} has not a father")
                    children = obj.children
                    new_obj= bpy.data.objects.new(joined_obj.name,joined_obj.data)
                    new_obj.matrix_world =joined_obj.matrix_world.copy()
                    for collection in obj.users_collection:
                        collection.objects.link(new_obj)
                    for child in children:
                        child_matrix = child.matrix_world.copy()
                        child.parent = new_obj
                        child.matrix_world = child_matrix 
                    bpy.data.objects.remove(joined_obj, do_unlink=True)
                    bpy.data.objects.remove(obj, do_unlink=True)
                    new_obj.name = old_name
                    new_obj.data.name = old_name
                    new_obj["JoinChildren"]=True
                    if level is not None:
                        new_obj["LevelOfDetail"] = level
            else: 
                meshes_to_join=[]
                return

    else:
        print(f"No CSV found for '{obj.name}' at {file_path}")

# Function for adding IfcElementAssembly based on the CSV values
def addIfcElementAssembly(obj,database_path,father=None,predefined_type="NOTDEFINED", object_type=None,psets=None):
    # For the Nodes that are leafs and they are IfcAssemblies without children. This should not happen, but if the STEP model is messy it could happen
    if obj.type == "MESH" and len(obj.children)==0:
        addIfcElement(obj,"IfcElementAssembly",predefined_type,object_type,psets,father,None)
    # For the Nodes that are meshes with children (this shouldn't happen, but if the STEP model is messy it could happen)
    if obj.type == "MESH" and len(obj.children)>0:
        print("________________________________________________________________________")
        # We create a new IfcElementAssembly for the father mesh, but we create it empty, and then we convert the mesh in an IfcElement that is part of the IfcElementAssembly. In fact an IfcElementAssembly can't have geometry if it aggregates other elements
        original_name=obj.name
        bpy.context.scene.BIMRootProperties.ifc_product = 'IfcElement'
        bpy.context.scene.BIMRootProperties.ifc_class = 'IfcElementAssembly'
        bpy.context.scene.BIMRootProperties.representation_template = 'EMPTY'
        bpy.context.scene.BIMRootProperties.name = obj.name
        bpy.ops.bim.add_element()
        new_ifc_assembly=bpy.context.view_layer.objects.active
        bpy.ops.bim.enable_editing_attributes(mass_operation=False) # Enable the editing attributes mode
        new_ifc_assembly.BIMAttributeProperties.attributes[1].string_value = original_name
        bpy.ops.bim.edit_attributes()
        bpy.ops.object.select_all(action='DESELECT')
        if not father == None:
            print(f"    And its father is: {father.name}")
            # Aggregate the new IfcElementAssmebly under its father
            bpy.ops.bim.enable_editing_aggregate()
            new_ifc_assembly.BIMObjectAggregateProperties.relating_object = father
            bpy.ops.bim.aggregate_assign_object(relating_object=father.BIMObjectProperties.ifc_definition_id)
            # Recreate the tree in the Blender Menu giving the parent relation to the Blender Object. Is not necessary for the IFC sake, but is useful for the Blender visualization
            new_ifc_assembly.parent= father
        bpy.context.view_layer.objects.active=obj
        
        # The real mesh of the father mesh is converted in an IfcElementAssembly adding _Part to the name
        bpy.ops.bim.assign_class(ifc_class="IfcElementAssembly")
        bpy.ops.object.select_all(action='DESELECT')
        new_ifc_assembly_part=bpy.context.view_layer.objects.active
        bpy.ops.bim.enable_editing_attributes(mass_operation=False)
        new_ifc_assembly_part.BIMAttributeProperties.attributes[1].string_value = f"{original_name}_Part"
        bpy.ops.bim.edit_attributes()
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.bim.enable_editing_aggregate()
        new_ifc_assembly_part.BIMObjectAggregateProperties.relating_object = new_ifc_assembly
        bpy.ops.bim.aggregate_assign_object(relating_object=new_ifc_assembly.BIMObjectProperties.ifc_definition_id)
        new_ifc_assembly_part.parent = new_ifc_assembly
        # When we create the IfcElementAssembly_Part, its children are moved under it, but they are not IfcElements yet. So we have to read the CSV and convert them properly
        for child in new_ifc_assembly_part.children:
            parts = original_name.split(".")
            file_name = ".".join(parts[:-1]) if len(parts) > 1 else original_name
            file_path = os.path.join(database_path, f"{file_name}.csv")
            if os.path.exists(file_path):
                df = pd.read_csv(file_path, encoding="utf-8", delimiter=";")
                if "Product in DB" not in df.columns:
                    return
                df_filtered = df[df["Product in DB"] == "Yes"]
                element_names = df_filtered["Element Name"].dropna().astype(str).to_dict()
                ifc_class = df_filtered["IfcClass"].astype(str).to_dict()
                predefined_type = df_filtered["PredefinedType"].astype(str).to_dict()
                object_type = df_filtered["ObjectType"].astype(str).to_dict()
                df_psets = [col for col in df.columns if col.startswith("Pset_") or col.startswith("Qto_")]
                psets_columns=df_filtered[df_psets].astype(str).to_dict()
                child_parts = child.name.split(".")
                child_name=".".join(child_parts[:-1]) if len(child_parts) > 1 else child.name
                for idx, name in element_names.items():
                    if child_name == name:
                        local_predefined = "NOTDEFINED"
                        local_objecttype = None
                        local_psets = None
                        psets_list = return_Psets(psets_columns, idx)
                        if len(psets_list) > 0:
                            local_psets = psets_list
                        if predefined_type[idx] != "nan":
                            local_predefined = predefined_type[idx]
                        if object_type[idx] != "nan":
                            local_objecttype = object_type[idx]

                        if ifc_class[idx]=="IfcElementAssembly":
                            addIfcElementAssembly(child,database_path,new_ifc_assembly,local_predefined,local_objecttype,local_psets)
                        else:
                            addIfcElement(child,ifc_class[idx],local_predefined,local_objecttype,local_psets,new_ifc_assembly)
        bpy.context.view_layer.objects.active=new_ifc_assembly
    # For the Nodes that are not meshes, but empty objects with children
    else:    
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
            new_ifc_assembly.parent = father 

def create_empty_at_cursor_with_element_orientation( element: ifcopenshell.entity_instance) -> bpy.types.Object:
    element_obj = tool.Ifc.get_object(element)
    name="Port_" + element.Name
    obj = bpy.data.objects.new(name, None)
    obj.matrix_world = element_obj.matrix_world.copy()
    obj.matrix_world.translation = bpy.context.scene.cursor.matrix.translation
    # bpy.context.scene.collection.objects.link(obj)
    return obj

def add_port(ifc: type[tool.Ifc], system: type[tool.System], element: ifcopenshell.entity_instance) -> bpy.types.Object:
    system.load_ports(element, system.get_ports(element))
    obj = create_empty_at_cursor_with_element_orientation(element)
    port = system.run_root_assign_class(obj=obj, ifc_class="IfcDistributionPort", should_add_representation=False)
    ifc.run("system.assign_port", element=element, port=port)
    return obj



# Function for adding IfcElement based on the CSV values 
def addIfcElement(obj,element_class,predefined_type="NOTDEFINED", object_type=None,psets=None, father=None,object_to_iterate=None):

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    # With this function if an object in the CSV has no Ifc Class value compiled, it won't be created and then it will be deleted.
    if not element_class == None:
        print("     _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _")
        print(f"    A new {element_class} - {predefined_type} for object: {obj.name}")
        original_name=obj.name
        # This time we don't add a new IFC element, but we convert the mesh in an IfcElement
        bpy.ops.bim.assign_class(ifc_class=element_class)
        bpy.ops.object.select_all(action='DESELECT')
        new_ifc_element=bpy.context.view_layer.objects.active
        bpy.ops.bim.enable_editing_attributes(mass_operation=False) # Enable the editing attributes mode
        new_ifc_element.BIMAttributeProperties.attributes[1].string_value = original_name # Edit the Name attribute
        if element_class == "IfcElementAssembly":
            if predefined_type != "NOTDEFINED":
                new_ifc_element.BIMAttributeProperties.attributes[6].enum_value = predefined_type # Edit the Predefined Type
            if object_type != None:
                if predefined_type == "USERDEFINED":
                    if object_type != None:
                        new_ifc_element.BIMAttributeProperties.attributes[3].string_value = object_type # Edit the Object Type
                        print(f"        With Object Type: {object_type}")
                else:
                    print(f"        Predefined Type is not USERDEFINED, so Object Type is not set")
            bpy.ops.bim.edit_attributes() # Confirm the editing
        else:
            if predefined_type != "NOTDEFINED":
                new_ifc_element.BIMAttributeProperties.attributes[5].enum_value = predefined_type # Edit the Predefined Type
            if object_type != None:
                if predefined_type == "USERDEFINED":
                    if object_type != None:
                        new_ifc_element.BIMAttributeProperties.attributes[3].string_value = object_type # Edit the Object Type
                        print(f"        With Object Type: {object_type}")
                else:
                    print(f"        Predefined Type is not USERDEFINED, so Object Type is not set")
            bpy.ops.bim.edit_attributes() # Confirm the editing
        if not father == None:
            if father.type != 'MESH':
                bpy.ops.bim.enable_editing_aggregate()
                new_ifc_element.BIMObjectAggregateProperties.relating_object = father
                bpy.ops.bim.aggregate_assign_object(relating_object=father.BIMObjectProperties.ifc_definition_id)
            new_ifc_element.parent= father
            new_ifc_element.matrix_world = obj.matrix_world.copy()
            print(f"        And its father is: {father.name}")
        ifc_obj=ifcTool.Ifc.get_entity(new_ifc_element)
        if psets != None:
            # TODO Ci sarà da aggiungere anche dei controlli sull'applicabilitä dei Pset
            
            for pset_name, properties in psets.items():
                if pset_name.startswith("Pset_"):
                    ifc_pset=ifcTool.Ifc.run("pset.add_pset",product=ifc_obj,name=pset_name)
                    print(f"        Adding Pset: {pset_name}")
                    for prop,val in properties.items():
                        ifcTool.Ifc.run("pset.edit_pset",pset=ifc_pset,properties={prop:val})
                        print(f"            Adding Property: {prop} with value: {val}")
                if pset_name.startswith("Qto_"):
                    ifc_qto=ifcTool.Ifc.run("pset.add_qto",product=ifc_obj,name=pset_name)
                    print(f"        Adding Qto: {pset_name}")
                    for prop,val in properties.items():
                        ifcTool.Ifc.run("pset.edit_qto",qto=ifc_qto,properties={prop:val})
                        print(f"            Adding Quantity: {prop} with value: {val}")
        if element_class=="IfcDistributionElement":
            
            port=add_port(tool.Ifc,tool.System,ifc_obj)
            # bpy.ops.bim.enable_editing_attributes(mass_operation=False)
            # port.BIMAttributeProperties.attributes[1].string_value = f"Port_{original_name}"
            # bpy.ops.bim.edit_attributes()
            
            port.parent=new_ifc_element
            port.matrix_world = new_ifc_element.matrix_world.copy()
            

        bpy.ops.object.select_all(action='DESELECT')
        if len(obj.children)>0:
            print(obj.children)
            for child in obj.children:
                if object_to_iterate is not None:
                    for key, value in object_to_iterate.items():
                        if child == key:                       
                            addIfcElement(child,value["IfcClass"],value["PredefinedType"],value["ObjectType"],value["Psets"],new_ifc_element,object_to_iterate)

                        
                    




def convert_value(v):
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v

def return_Psets(psets_columns,idx):
    psets={}
    for pset,list in psets_columns.items():
        pset_name = pset.split("/")[0]
        prop_name = pset.split("/")[1]
        if pset_name != "Pset_NameXX" and prop_name != "Prop_NameYY":
            if list[idx]!="nan":
                if pset_name not in psets:
                    psets[pset_name]={prop_name:convert_value(list[idx])}
                else:
                    psets[pset_name][prop_name] = convert_value(list[idx])
    return psets

# Recursive function to create the IfcAssembly tree based on the CSV values
def createIfcAssemblyTree(obj,database_path, ifc_entity="IfcElementAssembly",predefined_type="NOTDEFINED", object_type=None,psets=None, father=None):
    completed_folder_path = os.path.join(database_path, "Completed")
    parts = obj.name.split(".")
    file_name = ".".join(parts[:-1]) if len(parts) > 1 else obj.name
    file_path = os.path.join(completed_folder_path, f"{file_name}.csv")
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, encoding="utf-8", delimiter=";")
        if "Product in DB" not in df.columns:
            return
        df_filtered = df[df["Product in DB"] == "Yes"]
        df_element_names = df_filtered["Element Name"].dropna().astype(str).to_dict()
        df_ifc_class = df_filtered["IfcClass"].astype(str).to_dict()
        df_predefined_type = df_filtered["PredefinedType"].astype(str).to_dict()
        df_object_type = df_filtered["ObjectType"].astype(str).to_dict()

        df_psets = [col for col in df.columns if col.startswith("Pset_") or col.startswith("Qto_")]
        psets_columns=df_filtered[df_psets].astype(str).to_dict()
        bpy.ops.object.select_all(action='DESELECT')
        select_hierarchy(obj)
        objects = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')
        # With object_to_iterate we want to select only the nodes that are in the database, in order to simplify the tree structure
        object_to_iterate={}
        for object in objects:
            parts = object.name.split(".")
            file_name = ".".join(parts[:-1]) if len(parts) > 1 else object.name

            for idx, name in df_element_names.items():
                if file_name == name:

                    # LOCAL VARIABLES — each object gets its own clean set
                    local_predefined = "NOTDEFINED"
                    local_objecttype = None
                    local_psets = None

                    psets_list = return_Psets(psets_columns, idx)
                    if len(psets_list) > 0:
                        local_psets = psets_list

                    if df_predefined_type[idx] != "nan":
                        local_predefined = df_predefined_type[idx]

                    if df_object_type[idx] != "nan":
                        local_objecttype = df_object_type[idx]

                    # save clean values
                    object_to_iterate[object] = {
                        "IfcClass": df_ifc_class[idx],
                        "PredefinedType": local_predefined,
                        "ObjectType": local_objecttype,
                        "Psets": local_psets
                    }         
        if ifc_entity=="IfcElementAssembly":
            addIfcElementAssembly(obj,completed_folder_path,father)
            parent_ifc_obj = bpy.context.view_layer.objects.active
        else:
            addIfcElement(obj,ifc_entity,predefined_type,object_type,psets,father,object_to_iterate)
            parent_ifc_obj = bpy.context.view_layer.objects.active
        if len(object_to_iterate)>0:
            for o in object_to_iterate:
                createIfcAssemblyTree(o,database_path,object_to_iterate[o]["IfcClass"],object_to_iterate[o]["PredefinedType"],object_to_iterate[o]["ObjectType"],object_to_iterate[o]["Psets"],parent_ifc_obj)