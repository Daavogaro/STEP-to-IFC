import os
import csv
import pandas as pd  # Library for handling CSV files
import bpy
from mathutils import Vector

# Function to get only leaf objects (objects without children)
def get_leaf_objects(obj, hierarchy=None,max_levels=20):
    """
    Returns a list of lists. Each sublist represents a leaf object with its hierarchy.
    hierarchy: list of names from root down to parent
    """
    if hierarchy is None:
        hierarchy = []

    # Current path including this object
    current_path = hierarchy + [obj.name]

    # If the object has no children, it's a leaf — return its path
    if not obj.children:
        return [current_path]
    if obj.get("JoinChildren", False) is True and not obj==bpy.context.view_layer.objects.active:
        padded = current_path + [""] * (max_levels - len(current_path))
        row = padded+["Yes","","","",""]
        return [row]
    # Otherwise, recursively process children
    rows = []
    for child in obj.children:
        rows.extend(get_leaf_objects(child, current_path))
    return rows

def create_or_find_csv(obj,database_path):
    if "/" in obj.name:
        old_name = obj.name
        obj.name = old_name.replace("/","_")
    parts = obj.name.split(".")
    file_name = ".".join(parts[:-1]) if len(parts) > 1 else obj.name
    # ✅ Process this object if JoinChildren True
    if obj.get("JoinChildren", False) is True:
        completed_file_path = os.path.join(database_path, "Completed", f"{file_name}.csv")
        to_be_completed_file_path = os.path.join(database_path, "To be completed", f"{file_name}.csv")

        if os.path.exists(completed_file_path):
            print(f"Already completed: {completed_file_path}")
        else:
            if not os.path.exists(to_be_completed_file_path):
                
                with open(to_be_completed_file_path, 'w', newline='') as file:
                    writer = csv.writer(file)
                    bpy.context.view_layer.objects.active=obj
                    # Header
                    writer.writerow(
                        ["Level_" + str(i) for i in range(20)] +
                        ["Product in DB","LOW: To be deleted","LOW: To be simplified","MID: To be deleted","MID: To be simplified"]
                    )

                    # Data rows
                    rows = get_leaf_objects(obj)
                    writer.writerows(rows)
            else:
                print(f"CSV exists: {to_be_completed_file_path}")

    # ✅ ALWAYS go through children — even if current object didn’t match
    for child in obj.children:
        create_or_find_csv(child, database_path)

def control_database(obj,database_path):
    completed_folder_path = os.path.join(database_path, "Completed")
    for filename in os.listdir(completed_folder_path):
        if filename.lower().endswith('.csv'):
            filename_string = filename[:-4]
            obj.name = obj.name.replace("/", "_")
            parts = obj.name.split(".")
            name = ".".join(parts[:-1]) if len(parts) > 1 else obj.name
            if name == filename_string:
                print(filename_string)
                obj["JoinChildren"]=True    


def create_bbox(obj):
    # Store original names
    original_mesh_name = obj.data.name
    original_object_name = obj.name
    # Change the name of the object (in this way we can apply the original name when we recreate the object)
    obj.data.name = f"{original_mesh_name}_old"
    obj.name = f"{original_object_name}_old"
    # Get world-space bounding box corners
    bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

    # Define the 8 vertices of the box
    verts = bbox_corners

    # Define the faces using the vertex indices
    faces = [
        (0, 1, 2, 3),  # Bottom
        (4, 5, 6, 7),  # Top
        (0, 1, 5, 4),  # Front
        (2, 3, 7, 6),  # Back
        (1, 2, 6, 5),  # Right
        (0, 3, 7, 4)   # Left
    ]

    # Create a new mesh and object
    mesh_data = bpy.data.meshes.new(original_mesh_name)
    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update()

    bbox_obj = bpy.data.objects.new(original_object_name, mesh_data)
    bbox_obj.parent = obj.parent
     # Link the new cube to the same collection as the original object
    for collection in obj.users_collection:
        collection.objects.link(bbox_obj)
    # Copy materials from the original object
    if obj.material_slots:
        for material_slot in obj.material_slots:
            bbox_obj.data.materials.append(material_slot.material)
    # Maintain hierarchy by assigning the same parent
    print(f"Bounding box mesh created for '{original_object_name}'.")


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

def hideLeafWithNoMesh(obj):
    children = list(obj.children) # A list of all children of obj
    if not children and not obj.type == 'MESH' and not obj.type == 'MATERIAL': # If there are no children and is not a mesh and is not a material the object is hidden
        obj.hide_set(True)
    for child in children: # This function is iterate for the children of each child until there are no more children left
        hideLeafWithNoMesh(child)
# If a parent in the tree has all the children that are hidden, the function hide the father.
def hideParentsWithHiddenChildren(obj):
    children = list(obj.children) # A list of all children of obj
    if not children: # If has no children it means that it is a mesh or a material
        return
    all_children_hidden = True # Assume that all children of "obj" are hidden
    for child in children:
        hideParentsWithHiddenChildren(child) # This function is iterate for the children of each child until there are no more children left
        if not child.hide_get(): # If at least a child is not hidden, the assumption done before is wrong
            all_children_hidden = False
    if all_children_hidden: # But if all children are hidden (so the assumption done before is correct), hide the father
        obj.hide_set(True)

# This function delete all the hidden objects
def delete_hidden_elements(obj):
    children = list(obj.children) # A list of all children of obj
    
    # Vengono eliminati ricorsivamente gli elementi nascosti
    for child in children: # This function is iterate for the children of each child until there are no more children left
        delete_hidden_elements(child)
        if child.hide_get(): # If a child is hidden, then remove from the scene
            print(f"Deleting hidden object: {child.name}")
            bpy.data.objects.remove(child, do_unlink=True)            
            

def find_completed_csv(obj,database_path):
    print("_______________________________________________________________")
    completed_folder_path = os.path.join(database_path, "Completed")
    # Replace "/" in object name
    obj.name = obj.name.replace("/", "_")
    
    parts = obj.name.split(".")
    file_name = ".".join(parts[:-1]) if len(parts) > 1 else obj.name
    file_path = os.path.join(completed_folder_path, f"{file_name}.csv")
    
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, encoding="utf-8", delimiter=";")
        if "Product in DB" not in df.columns:
            return
        df_filtered = df[df["Product in DB"] == "Yes"]
        
        columns = [col for col in df.columns if col.startswith('Level_')]
        if not columns:
            return
        last_values = df_filtered[columns].apply(lambda row: row.dropna().iloc[-1] if not row.dropna().empty else None, axis=1)
        for value in last_values:
            if value and isinstance(value, str):  # Ensure it's a valid string
                value = value.replace("/", "_").strip()  # sanitize
                grouped_obj = bpy.data.objects.get(value)
                if grouped_obj is not None:
                    print(f"{grouped_obj.name} is a grouped object")
                    find_completed_csv(grouped_obj,database_path)
                    
                
        if "MID: To be deleted" not in df.columns:
            return        
        df_del_filtered = df[df["MID: To be deleted"] == "Yes"]
        if "MID: To be simplified" not in df.columns:
            return        
        df_sim_filtered = df[df["MID: To be simplified"] == "Yes"]
        last_del_values = df_del_filtered[columns].apply(lambda row: row.dropna().iloc[-1] if not row.dropna().empty else None, axis=1)
        last_sim_values = df_sim_filtered[columns].apply(lambda row: row.dropna().iloc[-1] if not row.dropna().empty else None, axis=1)
        bpy.context.view_layer.objects.active = obj
        
        meshes=find_meshes_inside(obj)

        print(f"{len(meshes)} meshes, {len(last_del_values)} object to delete and {len(last_sim_values)} object to simplify")
        row_del_numbers = last_del_values.index.tolist()
        row_sim_numbers = last_sim_values.index.tolist()
        if obj.get("LevelOfDetail", False) == "LOW" or obj.get("LevelOfDetail", False) == "MEDIUM" or obj.get("LevelOfDetail", False) and not obj.get("LevelOfDetail", False) == "HIGH":
            for number in row_del_numbers:
                bpy.data.objects.remove(meshes[number], do_unlink=True)
                meshes[number]=None
            
        if obj.get("LevelOfDetail", False) == "MEDIUM" or obj.get("LevelOfDetail", False) and not obj.get("LevelOfDetail", False) == "HIGH" :
            for number in row_sim_numbers:
                create_bbox(meshes[number])
                bpy.data.objects.remove(meshes[number], do_unlink=True)
                meshes[number]=None
        if obj.get("LevelOfDetail", False) == "LOW":
            print("Basso")
            for mesh in meshes:
                if not mesh is None:
                    create_bbox(mesh)
                    bpy.data.objects.remove(mesh, do_unlink=True)
        meshes=find_meshes_inside(obj)
        for mesh in meshes:
            mesh.parent= obj
        hideLeafWithNoMesh(obj)
        hideParentsWithHiddenChildren(obj)
        delete_hidden_elements(obj)
        meshes_to_join=[]
        for child in obj.children:
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
            parent = obj.parent
            old_name = obj.name
            level = obj.get("LevelOfDetail", None)
            if level is not None:
                joined_obj["LevelOfDetail"] = level
            bpy.data.objects.remove(obj, do_unlink=True)

            joined_obj.name = old_name
            joined_obj.parent = parent
            joined_obj.data.name = old_name
            joined_obj["JoinChildren"]=True
        else:
            meshes_to_join=[]
            return
                
    else:
        print(f"No CSV found for '{obj.name}' at {file_path}")