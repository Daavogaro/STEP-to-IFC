import bpy
import os
import csv
from .core import deleteSmallElements
from .core import CSVComponentsTree


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
            bpy.ops.outliner.orphans_purge(do_recursive=True)
            print(f"The selected object is: {active_obj.name}")
        else:
            print("No active object selected.")
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
            tree_data = [["Level_" + str(i) for i in range(20)]+["To be deleted","To be simpified","To be grouped under"]]
            # Retrieve the hierarchical tree structure of objects in the scene
            tree_data.extend(CSVComponentsTree.get_object_tree(active_obj, []))

    
            # Try to write the CSV file
            try:
                with open(csv_filename, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerows(tree_data)
                # Report success message in Blender
                self.report({'INFO'}, f"CSV saved to {csv_filename}")

            # Handle potential errors
            except Exception as e: 
                self.report({'ERROR'}, f"Failed to save CSV: {e}")
                return {'CANCELLED'} # Cancel operation if there is an error
    
            return {'FINISHED'} # Successfully completed operation
        else:
            print("No active object selected.")

        # Check if the file path is set
        if not self.filepath:
            self.report({'ERROR'}, "No folder selected")
            return {'CANCELLED'} # Cancel operation
        
    # This method open the file browser and make the user select a directory
    def invoke(self, context, event):
            context.window_manager.fileselect_add(self) # Open file browser for directory selection
            return {'RUNNING_MODAL'} # Keep the operator running until user selects a folder
        
    
    
def register():
    bpy.utils.register_class(DeleteSmallElements_RunScript)
    bpy.utils.register_class(CSVPrint_Runscript)

def unregister():
    bpy.utils.unregister_class(DeleteSmallElements_RunScript)
    bpy.utils.unregister_class(CSVPrint_Runscript)
