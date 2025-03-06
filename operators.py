import bpy
import os
import csv
from .core import deleteSmallElements
from .core import CSVComponentsTree


class DeleteSmallElements_RunScript(bpy.types.Operator):
    bl_idname = "object.run_script"
    bl_label = "Delete small elements"
    bl_description = "This button delete all elements smaller than the dimension insert in the toogle below"

    def execute(self,context):
        min_size = context.object.my_properties.my_float
        # Unhide all objects
        for obj in bpy.data.objects:
            obj.hide_set(False)
        if bpy.context.view_layer.objects.active:
            active_obj = bpy.context.view_layer.objects.active
            deleteSmallElements.hideLeafWithNoMesh(active_obj)
            deleteSmallElements.isSmallerThan(active_obj,min_size)
            deleteSmallElements.hideParentsWithHiddenChildren(active_obj)
            deleteSmallElements.delete_hidden_elements(active_obj)
            bpy.ops.outliner.orphans_purge(do_recursive=True)
            print(f"The selected object is: {active_obj.name}")
        else:
            print("No active object selected.")

        return {'FINISHED'}

class RESOURCE_OT_Download(bpy.types.Operator):
    bl_idname = "csv.download"
    bl_label = "Download Resource"
    bl_description = "Save a CSV file in a chosen directory"
    filepath: bpy.props.StringProperty(subtype="DIR_PATH")  # Directory selection

    def execute(self, context):
        if bpy.context.view_layer.objects.active:
            active_obj = bpy.context.view_layer.objects.active
            # Define CSV filename
            csv_filename = os.path.join(self.filepath, "componentsTree.csv")
            # Retrieve the tree with only leaf objects
            tree_data = [["Level_" + str(i) for i in range(20)]+["To be deleted","To be simpified","To be grouped under"]]  # Header row
            tree_data.extend(CSVComponentsTree.get_collection_tree(active_obj, []))

    
            # Write CSV file
            try:
                with open(csv_filename, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerows(tree_data)
                self.report({'INFO'}, f"CSV saved to {csv_filename}")
            except Exception as e:
                self.report({'ERROR'}, f"Failed to save CSV: {e}")
                return {'CANCELLED'}
    
            return {'FINISHED'}
        else:
            print("No active object selected.")
        if not self.filepath:
            self.report({'ERROR'}, "No folder selected")
            return {'CANCELLED'}
    def invoke(self, context, event):
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        
    
    
def register():
    bpy.utils.register_class(DeleteSmallElements_RunScript)
    bpy.utils.register_class(RESOURCE_OT_Download)

def unregister():
    bpy.utils.unregister_class(DeleteSmallElements_RunScript)
    bpy.utils.unregister_class(RESOURCE_OT_Download)
