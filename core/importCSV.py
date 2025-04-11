import bpy  # Blender Python API
import pandas as pd  # Library for handling CSV files
from mathutils import Vector

# Function to delete objects in Blender based on a CSV file
def deleteCSVElement(self,file_path):
    # Load the CSV file
    df = pd.read_csv(file_path, encoding="utf-8", delimiter=";")
    # Check if the "To be deleted" column exists
    if "To be deleted" not in df.columns:
        self.report({'ERROR'},"Error: The column 'To be deleted' does not exist in the CSV file.")
        return

    # Filter rows where "To be deleted" is "Yes"
    df_filtered = df[df["To be deleted"] == "Yes"]

    # Select only columns that start with "Level_"
    columns = [col for col in df.columns if col.startswith('Level_')]
    if not columns:
        self.report({'ERROR'},"Error: No column 'Level_X' found in CSV file.")
        return

    # For rows where "To be deleted" is "Yes", in the column that start with "Level", select the last element (the object)
    last_values = df_filtered[columns].apply(lambda row: row.dropna().iloc[-1] if not row.dropna().empty else None, axis=1)

    # Iterate over extracted object names and delete them from Blender
    for value in last_values:
        if value and isinstance(value, str):  # Ensure it's a valid string
            obj = bpy.data.objects.get(value)  # Get the object from Blender
            if obj:
                bpy.data.objects.remove(obj, do_unlink=True)  # Remove the object
    self.report({'INFO'},"Deletion completed.") 


# Function to create a new cube from the external vertices of an object
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



# Function to replace objects with a simplified cube based on the CSV file
def simplifyCSVElement(self,file_path):
    df = pd.read_csv(file_path, encoding="utf-8", delimiter=";")
    if "To be simplified" not in df.columns:
        self.report({'ERROR'},"Error: The column 'To be simiplified' does not exist in the CSV file.")
        return
    df_filtered = df[df["To be simplified"] == "Yes"]
    columns = [col for col in df.columns if col.startswith('Level_')]
    if not columns:
        self.report({'ERROR'},"Error: No column 'Level_X' found in CSV file.")
        return
    last_values = df_filtered[columns].apply(lambda row: row.dropna().iloc[-1] if not row.dropna().empty else None, axis=1)
    for value in last_values:
        if value and isinstance(value, str):
            obj = bpy.data.objects.get(value)
            if obj:
                create_bbox(obj)
                bpy.data.objects.remove(obj, do_unlink=True)
                print(f"Object '{value}' has been replaced with a cube.")
            else:
                print(f"Vertices could not be calculated for the object '{value}'.")


def select_hierarchy(obj):
    obj.select_set(True)
    for child in obj.children:
        child.select_set(True)
        select_hierarchy(child)

def select_hierarchy_not_mesh(obj):
    # obj.select_set(True)
    for child in obj.children:
        if not child.type  == 'MESH':
            child.select_set(True)
        select_hierarchy_not_mesh(child)

def groupCSVElement(self,file_path):
    # Carica il CSV
    df = pd.read_csv(file_path, encoding="utf-8",delimiter=";")

    # Verifica che la colonna "To be grouped under" esistarr
    if "To be grouped under" not in df.columns:
        self.report({'ERROR'},"Error: The column 'To be grouped under' does not exist in the CSV file.")
        return
    columns = [col for col in df.columns if col.startswith('Level_')]
    if not columns:
        self.report({'ERROR'},"Error: No column 'Level_X' found in CSV file.")
        return
    levels = df[columns]
    father_column = df['To be grouped under']
    meshes_names = levels.apply(lambda row: row.dropna().iloc[-1] if not row.dropna().empty else None, axis=1)

    for mesh_name,new_father_name in zip(meshes_names,father_column):
        if pd.isna(mesh_name) or pd.isna(new_father_name):
            continue
        # Check if the mesh exists in Blender
        if mesh_name not in bpy.data.objects:
            print(f"Warning: Mesh '{mesh_name}' not found in Blender.")
            continue

        # Check if the parent exists in Blender
        if new_father_name not in bpy.data.objects:
            print(f"Warning: Parent object '{new_father_name}' not found in Blender.")
            continue
        mesh_obj = bpy.data.objects[mesh_name]
        parent_obj = bpy.data.objects[new_father_name]
        # Move the mesh under the specified parent
        mesh_obj.parent = parent_obj
        
# Function to group objects under a new parent based on CSV
def merge_contained_meshes(obj):
    # Create two arrays:
    mesh_children = [] # For children that are meshes
    object_children = [] # For children that are not meshes
    for child in obj.children: # Append each child in the right array
        if child.type == 'MESH':
            mesh_children.append(child)
        if not child.type  == 'MESH' or not child.type  == 'MATERIAL':
            object_children.append(child)
    if len(object_children)>0: # If the object_children array is not empty, iterate the function
        for object_child in object_children:
            merge_contained_meshes(object_child)
    if len(mesh_children)>0: # If the mesh_children array is not empty
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = mesh_children[0] # Make the first child active
        for mesh_child in mesh_children: # Select all the children
            mesh_child.select_set(True)        
        # Force the opening of that window area to join elements
        for area in bpy.context.window.screen.areas:
            if area.type == 'VIEW_3D':
                with bpy.context.temp_override(area=area):
                    try:
                        bpy.ops.object.join()
                        print(f"Mesh merged under '{obj.name}'.")
                    except RuntimeError as e:
                        print(f"Error when joining meshes below '{obj.name}': {e}")
                break


# Function to rename meshes with their parent's name
def rename_meshes_with_parent_name(obj):
    parent_name = obj.name.split(".")[0]
    for child in obj.children:
        if child.type == 'MESH' and child.parent:
            old_name = child.name
            child.name = parent_name
            print(f"Renamed the mesh '{old_name}' in '{child.name}'")
        rename_meshes_with_parent_name(child)