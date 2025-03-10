import bpy
import os
import csv
from .core import deleteSmallElements
from .core import exportCSVComponentsTree
from .core import importCSV


class DeleteSmallElements_RunScript(bpy.types.Operator):
    bl_idname = "object.run_script" # ID of the script runned by the operator
    bl_label = "Delete small elements" # Title in the pop-up when the cursor pass on the operator
    bl_description = "This button delete all elements smaller than the dimension insert in the toogle below" # Description in the pop-up when the cursor pass on the operator

    # This script is executed when the operator is clicked
    def execute(self,context): # These arguments are mandatory
        min_size = context.object.my_properties.my_float # The minimum size for the X, Y and Z dimension is given by the user using the float property
        # The script will run on the active object (is different from selected object: you can select a lot of object, but you can have only one active object) and all its hiearchy
        active_obj = bpy.context.view_layer.objects.active
        # Unhide all objects because the following script initally hide the object to be deleted, so is necessary that all the object are unhidden in order to prevent accidentaly deleting
        for obj in bpy.data.objects:
            obj.hide_set(False)

        if active_obj: # If the active object exist
            # Converting geometries from proprietary software to other formats it could be that are generated some leaf object (leaf=at the end of the component tree) without mesh (the mesh is aggregated under other object).
            # The following function select all the leaf object of the "active_obj" tree without mesh and hide them
            deleteSmallElements.hideLeafWithNoMesh(active_obj) 
            # This function hide all the meshes smaller than the variable "min_size"
            deleteSmallElements.hideSmallerThan(active_obj,min_size)
            # At this point the tree of "active_obj" has some leaf that are hidden object. If a parent in the tree has all the children that are hidden, the function hide the father.
            deleteSmallElements.hideParentsWithHiddenChildren(active_obj)
            # This function delete all the hidden objects
            deleteSmallElements.delete_hidden_elements(active_obj)
            # This command purge all unused data left by deleted objects. In this way the memory is released
            bpy.ops.outliner.orphans_purge(do_recursive=False)
        else:
            self.report({'ERROR_INVALID_INPUT'},"No active object selected.")
        self.report({'INFO'},"Small objects has been deleted!")
        return {'FINISHED'}
        

class CSVPrint_Runscript(bpy.types.Operator):
    bl_idname = "csv.download"
    bl_label = "Download Resource"
    bl_description = "Save a CSV file in a chosen directory"
    filepath: bpy.props.StringProperty(subtype="DIR_PATH")  # Property for selecting a directory where the CSV will be saved

    def execute(self, context):
        if bpy.context.view_layer.objects.active:
            active_obj = bpy.context.view_layer.objects.active
            # Define the filename and path for the CSV file
            csv_filename = os.path.join(self.filepath, "componentsTree.csv")
            # Initialize the CSV data with a header row
            tree_data = [["Level_" + str(i) for i in range(20)]+["To be deleted","To be simplified","To be grouped under"]]
            # Retrieve the hierarchical tree structure of objects in the scene
            tree_data.extend(exportCSVComponentsTree.get_object_tree(active_obj, []))   
            # Try to write the CSV file
            try:
                with open(csv_filename, 'w', newline='') as file:
                    writer = csv.writer(file) # Write the file
                    writer.writerows(tree_data) # Write the rows based on tree_data
                # Report success message in Blender
                self.report({'INFO'}, f"CSV saved to {csv_filename}")
            # Handle potential errors
            except Exception as e: 
                self.report({'ERROR'}, f"Failed to save CSV: {e}")
                return {'CANCELLED'} # Cancel operation if there is an error
            self.report({'INFO'},"The CSV has been printed!")   
            return {'FINISHED'} # Successfully completed operation
        else:
            self.report({'ERROR_INVALID_INPUT'},"No active object selected.")

        # Check if the file path is set
        if not self.filepath:
            self.report({'ERROR'}, "No folder selected")
            return {'CANCELLED'} # Cancel operation
        
    # This method open the file browser and make the user select a directory
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self) # Open file browser for directory selection
        return {'RUNNING_MODAL'} # Keep the operator running until user selects a folder

# Global variable to store CSV file path
csv_filepath = ""

# Operator to import CSV
class CSVImport_Runscript(bpy.types.Operator):
    bl_idname = "csv.import"
    bl_label = "Import CSV"
    bl_description = "Select a CSV file to import"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # File selection

    def execute(self, context):
        global csv_filepath  # Access global variable
        if not self.filepath:
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}
        # Ensure file is a CSV
        if not self.filepath.lower().endswith('.csv'):
            self.report({'ERROR'}, "Selected file is not a CSV")
            return {'CANCELLED'}
        # Save CSV path in the global variable 
        csv_filepath = self.filepath
        try:
            with open(csv_filepath, 'r', newline='') as file:
                reader = csv.reader(file)
                data = list(reader)
            if not data:
                self.report({'WARNING'}, "CSV file is empty")
                return {'CANCELLED'}
            self.report({'INFO'}, f"Imported {len(data)} rows from CSV")

        except Exception as e:
            self.report({'ERROR'}, f"Failed to read CSV: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class deleteCSVObject_RunScript(bpy.types.Operator):
    bl_idname = "csv.delete"
    bl_label = "Delete object based on CSV"
    bl_description = "Delete all the object with the parameter 'To be deleted' set on 'Yes'"

    def execute(self, context):
        global csv_filepath  # Access global variable

        if not csv_filepath:
            self.report({'ERROR'}, "No CSV file imported yet")
            return {'CANCELLED'}

        # Read and process CSV file
        try:
            active_obj = bpy.context.view_layer.objects.active
            for obj in bpy.data.objects:
                obj.hide_set(False)

            if active_obj: # If the active object exist
                importCSV.deleteCSVElement(self, csv_filepath) # Read the CSV and delete objects with "Yes" in the "To be deleted" column
                deleteSmallElements.hideLeafWithNoMesh(active_obj) # Hide leaf without meshes
                deleteSmallElements.hideParentsWithHiddenChildren(active_obj) # Hide parents with hidden children
                deleteSmallElements.delete_hidden_elements(active_obj) # Delete hidden elements
                bpy.ops.outliner.orphans_purge(do_recursive=False) # Release the memory
            else:
                self.report({'ERROR'}, "No active object selected.")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to process CSV: {e}")
            return {'CANCELLED'}
        self.report({'INFO'}, "Deleted elements based on CSV")
        return {'FINISHED'}


class simplifyCSVObject_RunScript(bpy.types.Operator):
    bl_idname = "csv.simplify"
    bl_label = "Simplify object based on CSV"
    bl_description = "Simplify all the object with the parameter 'To be simiplified' set on 'Yes'"

    def execute(self, context):
        global csv_filepath
        if not csv_filepath:
            self.report({'ERROR'}, "No CSV file imported yet")
            return {'CANCELLED'}
        try:
            active_obj = bpy.context.view_layer.objects.active
            for obj in bpy.data.objects:
                obj.hide_set(False)
            if active_obj:
                importCSV.simplifyCSVElement(self, csv_filepath) # Read the CSV and simplify  objects with "Yes" in the "To be simiplified" column
                bpy.ops.outliner.orphans_purge(do_recursive=False)
                bpy.context.view_layer.objects.active = active_obj
                active_obj.select_set(True)
            else:
                self.report({'ERROR'}, "No active object selected.")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to process CSV: {e}")
            return {'CANCELLED'}
        self.report({'INFO'}, "Simplified elements based on CSV")
        return {'FINISHED'}

class regroupCSVObject_RunScript(bpy.types.Operator):
    bl_idname = "csv.regroup"
    bl_label = "Regroup object based on CSV"
    bl_description = "Regroup object based on the parameter 'To be grouped'"

    def execute(self, context):
        global csv_filepath
        if not csv_filepath:
            self.report({'ERROR'}, "No CSV file imported yet")
            return {'CANCELLED'}
        try:
            active_obj = bpy.context.view_layer.objects.active
            for obj in bpy.data.objects:
                obj.hide_set(False)
            if active_obj: 
                importCSV.groupCSVElement(self,csv_filepath) # Read the CSV and regrup objects under the object inserted in the "To be grouped" column
                deleteSmallElements.hideLeafWithNoMesh(active_obj) 
                deleteSmallElements.hideParentsWithHiddenChildren(active_obj)
                deleteSmallElements.delete_hidden_elements(active_obj)
                importCSV.merge_contained_meshes(active_obj) # Merge all the meshes under the same father into a unique mesh
                importCSV.rename_meshes_with_parent_name(active_obj) # The new mesh is renamed with the name of the father
                bpy.ops.outliner.orphans_purge(do_recursive=False)
            else:
                self.report({'ERROR'}, "No active object selected.")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to process CSV: {e}")
            return {'CANCELLED'}
        self.report({'INFO'}, "Regrouped elements based on CSV")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(DeleteSmallElements_RunScript)
    bpy.utils.register_class(CSVPrint_Runscript)
    bpy.utils.register_class(CSVImport_Runscript)
    bpy.utils.register_class(deleteCSVObject_RunScript)
    bpy.utils.register_class(simplifyCSVObject_RunScript)
    bpy.utils.register_class(regroupCSVObject_RunScript)

def unregister():
    bpy.utils.unregister_class(DeleteSmallElements_RunScript)
    bpy.utils.unregister_class(CSVPrint_Runscript)
    bpy.utils.unregister_class(CSVImport_Runscript)
    bpy.utils.unregister_class(deleteCSVObject_RunScript)
    bpy.utils.unregister_class(simplifyCSVObject_RunScript)
    bpy.utils.unregister_class(regroupCSVObject_RunScript)
