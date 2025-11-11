import os
import bpy
import csv

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
