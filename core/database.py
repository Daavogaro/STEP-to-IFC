import os
import csv
import pandas as pd  # Library for handling CSV files
import bpy
from mathutils import Vector
from . import importCSV
from . import deleteSmallElements

def get_objects(obj, written_names=None,csv_changed=False):
    
    if written_names is None:
        written_names = set()

    # Clean and normalize name
    old_name = obj.name
    obj.name = old_name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("<", "_").replace(">", "_")
    parts = obj.name.split(".")
    base_name = ".".join(parts[:-1]) if len(parts) > 1 else obj.name

    level = obj.get("LevelOfDetail", None)
    rows = []

    # --- LEAF CASE ---
    if not obj.children:
        if base_name not in written_names:
            written_names.add(base_name)
            csv_changed=True
            if obj.get("JoinChildren", False) is True and obj != bpy.context.view_layer.objects.active:
                row = [base_name, "Yes", level,"","" if level else ""]
                rows.append(row)
            else:
                rows.append([base_name])
        return rows, csv_changed 

    # --- JOINED CHILDREN CASE ---
    if obj.get("JoinChildren", False) is True and obj != bpy.context.view_layer.objects.active:
        print(f"The active obj is {bpy.context.view_layer.objects.active.name} and the object is {obj.name}")
        if base_name not in written_names:
            row = [base_name, "Yes", level,"","" if level else ""]
            rows.append(row)
            csv_changed=True
            written_names.add(base_name)
        return rows,csv_changed

    # --- RECURSION CASE ---
    for child in obj.children:
        child_rows, child_changed = get_objects(child, written_names, csv_changed)
        rows.extend(child_rows)
        if child_changed:
            csv_changed = True

    return rows,csv_changed


def create_or_find_csv(obj, database_path):
    if "/" in obj.name:
        old_name = obj.name
        obj.name = old_name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("<", "_").replace(">", "_")
    parts = obj.name.split(".")
    file_name = ".".join(parts[:-1]) if len(parts) > 1 else obj.name
    # ✅ Process this object if JoinChildren True
    if obj.get("JoinChildren", False) is True:
        completed_file_path = os.path.join(database_path, "Completed", f"{file_name}.csv")
        to_be_completed_file_path = os.path.join(database_path, "To be completed", f"{file_name}.csv")

        if os.path.exists(completed_file_path):
            print(f"Already completed: {completed_file_path}")
            df = pd.read_csv(completed_file_path,encoding="utf-8",sep=";",engine="python")
            old_rows = df.values.tolist()  # Converts all existing CSV rows to list of lists
            old_rows = df.fillna("").values.tolist()  # Replace NaN with empty string
            if "Element Name" not in df.columns:
                print(f"{completed_file_path} has not Element Name column")
                return
            element_names = df["Element Name"].dropna().astype(str).tolist()
            bpy.context.view_layer.objects.active=obj
            rows, csv_changed = get_objects(obj,set(element_names))
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
                    rows, csv_changed = get_objects(obj)
                    writer.writerows(rows)
            else:
                print(f"____________________________________________")

    # ✅ ALWAYS go through children — even if current object didn’t match
    for child in obj.children:
        create_or_find_csv(child, database_path)

def control_database(obj,database_path):
    completed_folder_path = os.path.join(database_path, "Completed")
    for filename in os.listdir(completed_folder_path):
        if filename.lower().endswith('.csv'):
            filename_string = filename[:-4]
            obj.name = obj.name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("<", "_").replace(">", "_")
            parts = obj.name.split(".")
            name = ".".join(parts[:-1]) if len(parts) > 1 else obj.name
            if name == filename_string:
                print(filename_string)
                obj["JoinChildren"]=True    




def find_meshes_inside(obj, array=None):
    """
    Recursively collect all MESH objects under obj,
    ignoring objects with JoinChildren=True (except the active root).
    """
    if array is None:
        array = []

    active_root = bpy.context.view_layer.objects.active

    # Skip only this object if JoinChildren=True and not active root
    if obj.get("JoinChildren", False) is True and not obj==bpy.context.view_layer.objects.active:
        return
    else:
        if obj.type == 'MESH':
            array.append(obj)

    # Always recurse through children
    for child in obj.children:
        find_meshes_inside(child, array)

    return array


def find_children_meshes(obj, meshes=None):
    if meshes is None:
        meshes = []
    for child in obj.children:
        if child.get("JoinChildren", False):
            continue  
        if child.type == "MESH":
            meshes.append(child)
        find_children_meshes(child, meshes)
    return meshes

def select_hierarchy(obj):
    obj.select_set(True)
    for child in obj.children:
        select_hierarchy(child)

def find_completed_csv(obj,database_path):
    completed_folder_path = os.path.join(database_path, "Completed")
    # Replace "/" in object name
    obj.name = obj.name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("<", "_").replace(">", "_")
    
    parts = obj.name.split(".")
    file_name = ".".join(parts[:-1]) if len(parts) > 1 else obj.name
    file_path = os.path.join(completed_folder_path, f"{file_name}.csv")
    
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, encoding="utf-8", delimiter=";")
        # FOR PRODUCTS IN THE DB
        if "Product in DB" not in df.columns:
            return
        df_filtered = df[df["Product in DB"] == "Yes"]
        element_names = df_filtered["Element Name"].dropna().astype(str).tolist()
        bpy.ops.object.select_all(action='DESELECT')
        select_hierarchy(obj)
        objects = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')
        object_to_iterate=[]
        for object in objects:
            object.name = object.name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("<", "_").replace(">", "_")
            parts = object.name.split(".")
            file_name = ".".join(parts[:-1]) if len(parts) > 1 else object.name
            for element_name in element_names:
                if file_name == element_name:
                    object_to_iterate.append(object)
        if len(object_to_iterate)>0:
#            print(f"Elements name are {object_to_iterate}")
            for o in object_to_iterate:
                find_completed_csv(o,database_path)
        # FOR ELEMENT NOT IN DB
        if "To be deleted" not in df.columns:
            return        
        df_del_filtered = df[df["To be deleted"] == "Yes"]
        if "MID: To be simplified" not in df.columns:
            return        
        df_sim_filtered = df[df["MID: To be simplified"] == "Yes"]
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
        else:
            meshes=find_children_meshes(obj)
            print(f"For the object {obj.name} there are {len(meshes)} mesehes to process")
            to_delete=df_del_filtered["Element Name"].dropna().astype(str).tolist()
            to_simplify=df_sim_filtered["Element Name"].dropna().astype(str).tolist()
            new_meshes=[]
            for mesh in meshes:
                parts = mesh.name.split(".")
                file_name = ".".join(parts[:-1]) if len(parts) > 1 else mesh.name
                if obj.get("LevelOfDetail", False) == "LOW":
                    if file_name in to_delete:
                        bpy.data.objects.remove(mesh, do_unlink=True)
                    else:
                        bbox=importCSV.create_bbox(mesh)
                        new_meshes.append(bbox)
                        bpy.data.objects.remove(mesh, do_unlink=True)
                    continue
                if obj.get("LevelOfDetail", False) == "MEDIUM" or obj.get("LevelOfDetail", False) and not obj.get("LevelOfDetail", False) == "HIGH" :
                    if file_name in to_delete:
                        bpy.data.objects.remove(mesh, do_unlink=True)
                    else:
                        if file_name in to_simplify:
                            bbox=importCSV.create_bbox(mesh)
                            new_meshes.append(bbox)
                            bpy.data.objects.remove(mesh, do_unlink=True)
                        else:
                            new_meshes.append(mesh)
                    continue     
                if obj.get("LevelOfDetail", False) == "HIGH":
                    new_meshes.append(mesh)
                    continue

            for mesh in new_meshes:    
                mesh.parent=obj        
            deleteSmallElements.hideLeafWithNoMesh(obj)
            deleteSmallElements.hideParentsWithHiddenChildren(obj)
            deleteSmallElements.delete_hidden_elements(obj)
            meshes_to_join=[]
            for child in obj.children:
                if child.get("JoinChildren", False) is True:
                    continue
                if child.type == 'MESH':
                    meshes_to_join.append(child)
            bpy.ops.object.select_all(action='DESELECT')
            if len(meshes_to_join)>0:
                bpy.context.view_layer.objects.active = meshes_to_join[0]
                for mesh in meshes_to_join:
                    mesh.select_set(True)
                meshes_to_join=[]
                for area in bpy.context.window.screen.areas:
                    if area.type == 'VIEW_3D':
                        with bpy.context.temp_override(area=area):
                            bpy.ops.object.join()
                        break
            
                joined_obj=bpy.context.view_layer.objects.active

                
                old_name = obj.name
                level = obj.get("LevelOfDetail", None)
                if level is not None:
                    joined_obj["LevelOfDetail"] = level
                parent = obj.parent
                if parent is not None:
                    joined_obj.parent = parent
                    children = obj.children
                    joined_children=[]
                    for child in children:
                        if child.type=="MESH" and child.get("JoinChildren", False) is True:
                            joined_children.append(child)
                    if len(joined_children)>0:
                        new_obj= bpy.data.objects.new(joined_obj.name,joined_obj.data)
                        for collection in obj.users_collection:
                            collection.objects.link(new_obj)
                         
                        for child in children:
                            child.parent = new_obj

                        bpy.data.objects.remove(joined_obj, do_unlink=True)
                        bpy.data.objects.remove(obj, do_unlink=True)
                        new_obj.name = old_name
                        new_obj.data.name = old_name
                        new_obj["JoinChildren"]=True
                        new_obj.parent = parent
                        if level is not None:
                            new_obj["LevelOfDetail"] = level
                    else:


                        bpy.data.objects.remove(obj, do_unlink=True)
                        joined_obj.name = old_name
                        joined_obj.data.name = old_name
                        joined_obj["JoinChildren"]=True
                else:
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


def addIfcElementAssembly(obj,database_path,father=None):
    if obj.type == "MESH" and len(obj.children)==0:
        addIfcElement(obj,"IfcElementAssembly",father)
    if obj.type == "MESH" and len(obj.children)>0:
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
        
        # This time we don't add a new IFC element, but we convert the mesh in an IfcElement
        bpy.ops.bim.assign_class(ifc_class="IfcElementAssembly")
        bpy.ops.object.select_all(action='DESELECT')
        new_ifc_assembly_part=bpy.context.view_layer.objects.active
        bpy.ops.bim.enable_editing_attributes(mass_operation=False) # Enable the editing attributes mode
        new_ifc_assembly_part.BIMAttributeProperties.attributes[1].string_value = f"{original_name}_Part" # Edit the Name attribute
        bpy.ops.bim.edit_attributes()
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.bim.enable_editing_aggregate()
        new_ifc_assembly_part.BIMObjectAggregateProperties.relating_object = new_ifc_assembly
        bpy.ops.bim.aggregate_assign_object(relating_object=new_ifc_assembly.BIMObjectProperties.ifc_definition_id)
        
        # Recreate the tree in the Blender Menu giving the parent relation to the Blender Object. Is not necessary for the IFC sake, but is useful for the Blender visualization
        new_ifc_assembly_part.parent= new_ifc_assembly
        for child in new_ifc_assembly_part.children:
            parts = original_name.split(".")
            file_name = ".".join(parts[:-1]) if len(parts) > 1 else original_name
            file_path = os.path.join(database_path, f"{file_name}.csv")
            if os.path.exists(file_path):
                df = pd.read_csv(file_path, encoding="utf-8", delimiter=";")
                # FOR PRODUCTS IN THE DB
                if "Product in DB" not in df.columns:
                    return
                df_filtered = df[df["Product in DB"] == "Yes"]
                element_names = df_filtered["Element Name"].dropna().astype(str).to_dict()
                ifc_class     = df_filtered["IfcClass"].astype(str).to_dict()
                child_parts= child.name.split(".")
                child_name=".".join(child_parts[:-1]) if len(child_parts) > 1 else child.name
                for idx, name in element_names.items():
                    if child_name == name:
                        if ifc_class[idx]=="IfcElementAssembly":
                            addIfcElementAssembly(child,database_path,new_ifc_assembly)
                        else:
                            addIfcElement(child,ifc_class[idx],new_ifc_assembly)
            
        bpy.context.view_layer.objects.active=new_ifc_assembly
    else:    
        print("_  _  _  _  _  _  _  _  _  _  _  _  _  _  _  ")
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
def addIfcElement(obj,element_class,father=None):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    # With this function if an object in the CSV has no Ifc Class value compiled, it won't be created and then it will be deleted.
    if not element_class == None:
        print("________________________________________________________________________")
        print(f"A new {element_class} for object: {obj.name}")
        original_name=obj.name
        # This time we don't add a new IFC element, but we convert the mesh in an IfcElement
        bpy.ops.bim.assign_class(ifc_class=element_class)
        bpy.ops.object.select_all(action='DESELECT')
        new_ifc_element=bpy.context.view_layer.objects.active
        bpy.ops.bim.enable_editing_attributes(mass_operation=False) # Enable the editing attributes mode
        new_ifc_element.BIMAttributeProperties.attributes[1].string_value = original_name # Edit the Name attribute
#        if not element_predefined_type == None:
#            new_ifc_element.BIMAttributeProperties.attributes[5].enum_value = element_predefined_type # Edit the Predefined Type
#            print(f"    And its predefined type is: {element_predefined_type}")
#            if not element_object_type == None:
#                new_ifc_element.BIMAttributeProperties.attributes[3].string_value = element_object_type # Edit the Object Type
#                print(f"    With Object Type: {element_object_type}")
        bpy.ops.bim.edit_attributes() # Confirm the editing
        if not father == None:
            bpy.ops.bim.enable_editing_aggregate()
            new_ifc_element.BIMObjectAggregateProperties.relating_object = father
            bpy.ops.bim.aggregate_assign_object(relating_object=father.BIMObjectProperties.ifc_definition_id)
            new_ifc_element.parent= father
            print(f"    And its father is: {father.name}")
    bpy.ops.object.select_all(action='DESELECT')

def createIfcAssemblyTree(obj,database_path, ifc_entity="IfcElementAssembly",father=None):
    completed_folder_path = os.path.join(database_path, "Completed")
    
    parts = obj.name.split(".")
    file_name = ".".join(parts[:-1]) if len(parts) > 1 else obj.name
    file_path = os.path.join(completed_folder_path, f"{file_name}.csv")
    
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, encoding="utf-8", delimiter=";")
        # FOR PRODUCTS IN THE DB
        if "Product in DB" not in df.columns:
            return
        df_filtered = df[df["Product in DB"] == "Yes"]
        element_names = df_filtered["Element Name"].dropna().astype(str).to_dict()
        ifc_class     = df_filtered["IfcClass"].astype(str).to_dict()
        bpy.ops.object.select_all(action='DESELECT')
        select_hierarchy(obj)
        objects = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')
        object_to_iterate={}
        for object in objects:
            parts = object.name.split(".")
            file_name = ".".join(parts[:-1]) if len(parts) > 1 else object.name
            for idx, name in element_names.items():
                if file_name == name:
                    object_to_iterate[object]=ifc_class[idx]

        
        
        print(f"{obj.name} is a {ifc_entity}")
        if ifc_entity=="IfcElementAssembly":
            addIfcElementAssembly(obj,completed_folder_path,father)
            new_ifc_assembly=bpy.context.view_layer.objects.active
        else:
            addIfcElement(obj,ifc_entity,father)
            
        if len(object_to_iterate)>0:
            for o in object_to_iterate:
                createIfcAssemblyTree(o,database_path,object_to_iterate[o],new_ifc_assembly)