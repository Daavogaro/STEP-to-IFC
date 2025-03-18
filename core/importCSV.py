import bpy  # Blender Python API
import pandas as pd  # Library for handling CSV files
import bmesh  # Blender's module for working with mesh data

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


# Function to find the external vertices (bounding box corners) of a mesh object
def find_external_vertices(obj):
    if obj.type != 'MESH':
        return None  # Only process mesh objects
    bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects
    obj.select_set(True)  # Select the given object
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')  # Ensure we are in object mode
    # Create a BMesh instance to manipulate the mesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()  # Ensure vertex lookup is available
    # Compute bounding box min/max coordinates
    min_x = min(bm.verts, key=lambda v: v.co.x).co.x
    max_x = max(bm.verts, key=lambda v: v.co.x).co.x
    min_y = min(bm.verts, key=lambda v: v.co.y).co.y
    max_y = max(bm.verts, key=lambda v: v.co.y).co.y
    min_z = min(bm.verts, key=lambda v: v.co.z).co.z
    max_z = max(bm.verts, key=lambda v: v.co.z).co.z
    # List of external vertices (bounding box corners)
    external_verts = [
        (min_x, min_y, min_z), (min_x, min_y, max_z),
        (min_x, max_y, min_z), (min_x, max_y, max_z),
        (max_x, min_y, min_z), (max_x, min_y, max_z),
        (max_x, max_y, min_z), (max_x, max_y, max_z)
    ]
    bm.free()  # Free the BMesh memory
    return external_verts


# Function to create a new cube from the external vertices of an object
def create_cube_from_vertices(verts, obj):
    # Store original names
    original_mesh_name = obj.data.name
    original_object_name = obj.name
    # Change the name of the object (in this way we can apply the original name when we recreate the object)
    obj.data.name = f"{original_mesh_name}_old"
    obj.name = f"{original_object_name}_old"
    # Create a new mesh and object
    mesh = bpy.data.meshes.new(original_mesh_name)
    cube = bpy.data.objects.new(original_object_name, mesh)
    # Link the new cube to the same collection as the original object
    for collection in obj.users_collection:
        collection.objects.link(cube)
    # Define the cube's faces using the provided vertices
    mesh.from_pydata(verts, [], [
        (0, 1, 3, 2), (4, 5, 7, 6),
        (0, 1, 5, 4), (2, 3, 7, 6),
        (0, 2, 6, 4), (1, 3, 7, 5)
    ])
    mesh.update()
    # Copy materials from the original object
    if obj.material_slots:
        for material_slot in obj.material_slots:
            cube.data.materials.append(material_slot.material)
    # Maintain hierarchy by assigning the same parent
    cube.parent = obj.parent
    # Copy position, rotation, and scale
    cube.location = obj.location
    cube.rotation_euler = obj.rotation_euler
    cube.scale = obj.scale

    return cube


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
                verts = find_external_vertices(obj)
                if verts:
                    create_cube_from_vertices(verts, obj)
                    bpy.data.objects.remove(obj, do_unlink=True)
                    print(f"Object '{value}' has been replaced with a cube.")
                else:
                    print(f"Vertices could not be calculated for the object '{value}'.")


def select_hierarchy(obj):
    obj.select_set(True)
    for child in obj.children:
        child.select_set(True)
        select_hierarchy(child)

def groupCSVElement(self,file_path):
    # Carica il CSV
    df = pd.read_csv(file_path, encoding="utf-8",delimiter=";")

    # Verifica che la colonna "To be deleted" esista
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