import bpy
import os
import csv
import pandas as pd
import time
from .core import deleteSmallElements
from .core import exportCSVComponentsTree
from .core import importCSV
from .core import renameMeshes
from .core import ifcTreeAssembly
from .core import ifcAssignPsets


class DeleteSmallElements_RunScript(bpy.types.Operator):
    bl_idname = "object.run_script" # ID of the script runned by the operator
    bl_label = "Delete small elements" # Title in the pop-up when the cursor pass on the operator
    bl_description = "This button delete all elements smaller than the dimension insert in the toogle below" # Description in the pop-up when the cursor pass on the operator

    # This script is executed when the operator is clicked
    def execute(self,context): # These arguments are mandatory
        start_time = time.perf_counter() # Starting the counter for measure the execution time
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
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            print(f"Execution time: {elapsed_time:.6f} seconds")
        else:
            self.report({'ERROR_INVALID_INPUT'},"No active object selected.")
        self.report({'INFO'},"Small objects has been deleted!")
        return {'FINISHED'}
    
class MakeMeshesDataUniques_Runscript(bpy.types.Operator):
    bl_idname = "meshesunique.run_script"
    bl_label = "Make meshes data uniques"
    bl_description = "Some of the meshes' data could be duplicated. This could cause some issues with identification with excel file. For this reason is reccomanded to make meshes data unique with this command."        
    def execute(self, context):
        start_time = time.perf_counter()
        if bpy.context.view_layer.objects.active:
            active_obj = bpy.context.view_layer.objects.active
            try:
                renameMeshes.makeMeshesUniques(active_obj)
            except Exception as e:
                self.report({'ERROR'}, f"Failed to make data uniques: {e}")
                return {'CANCELLED'} # Cancel operation if there is an error
            self.report({'INFO'},"The CSV has been printed!")
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            print(f"Execution time: {elapsed_time:.6f} seconds")
        else:
            self.report({'ERROR_INVALID_INPUT'},"No active object selected.")
        self.report({'INFO'},"Meshes data made unique!")
        return {'FINISHED'}


class CSVPrint_Runscript(bpy.types.Operator):
    bl_idname = "csv.download"
    bl_label = "Download CSV"
    bl_description = "Save a CSV file in a chosen directory"
    filepath: bpy.props.StringProperty(subtype="DIR_PATH")  # Property for selecting a directory where the CSV will be saved

    def execute(self, context):
        start_time = time.perf_counter()
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
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                print(f"Execution time: {elapsed_time:.6f} seconds")
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
        start_time = time.perf_counter()
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
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            print(f"Execution time: {elapsed_time:.6f} seconds")
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
        start_time = time.perf_counter()
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
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                print(f"Execution time: {elapsed_time:.6f} seconds")
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
        start_time = time.perf_counter()
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
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                print(f"Execution time: {elapsed_time:.6f} seconds")
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
        start_time = time.perf_counter()
        global csv_filepath
        if not csv_filepath:
            self.report({'ERROR'}, "No CSV file imported yet")
            return {'CANCELLED'}
        try:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in bpy.data.objects:
                obj.hide_set(False)
            active_obj = bpy.context.view_layer.objects.active
            importCSV.select_hierarchy(active_obj)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            bpy.context.view_layer.objects.active = active_obj
            

            if active_obj: 
                importCSV.groupCSVElement(self,csv_filepath) # Read the CSV and regrup objects under the object inserted in the "To be grouped" column
                deleteSmallElements.hideLeafWithNoMesh(active_obj) 
                deleteSmallElements.hideParentsWithHiddenChildren(active_obj)
                deleteSmallElements.delete_hidden_elements(active_obj)
                importCSV.merge_contained_meshes(active_obj) # Merge all the meshes under the same father into a unique mesh
                importCSV.rename_meshes_with_parent_name(active_obj) # The new mesh is renamed with the name of the father
                bpy.ops.outliner.orphans_purge(do_recursive=False)
                bpy.context.view_layer.objects.active = active_obj
                active_obj.select_set(True)
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                print(f"Execution time: {elapsed_time:.6f} seconds")
            else:
                self.report({'ERROR'}, "No active object selected.")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to process CSV: {e}")
            return {'CANCELLED'}
        self.report({'INFO'}, "Regrouped elements based on CSV")
        return {'FINISHED'}

class CSVPrintIFC_Runscript(bpy.types.Operator):
    bl_idname = "csv.exportifc"
    bl_label = "Download CSV"
    bl_description = "Save a CSV file in a chosen directory"
    filepath: bpy.props.StringProperty(subtype="DIR_PATH")  # Property for selecting a directory where the CSV will be saved

    def execute(self, context):
        start_time = time.perf_counter()
        if bpy.context.view_layer.objects.active:
            active_obj = bpy.context.view_layer.objects.active
            # Define the filename and path for the CSV file
            csv_filename = os.path.join(self.filepath, "componentsTreeIFC.csv")
            # Initialize the CSV data with a header row
            tree_data = [["Level_" + str(i) for i in range(20)]+["Ifc Class","Predefined Type","Object Type","Pset_Name/Prop_Name/Prop_Value_1","Pset_Name/Prop_Name/Prop_Value_2"]]
            # Retrieve the hierarchical tree structure of objects in the scene
            tree_data.extend(exportCSVComponentsTree.get_object_tree(active_obj, []))   
            # Try to write the CSV file
            try:
                with open(csv_filename, 'w', newline='') as file:
                    writer = csv.writer(file) # Write the file
                    writer.writerows(tree_data) # Write the rows based on tree_data
                # Report success message in Blender
                self.report({'INFO'}, f"CSV saved to {csv_filename}")
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                print(f"Execution time: {elapsed_time:.6f} seconds")
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


# Global variable to store IFC CSV file path
csv_ifc_filepath = ""

class IFCCSVLoad_Runscript(bpy.types.Operator):
    bl_idname = "csv.importifc"
    bl_label = "Import CSV"
    bl_description = "Select a CSV to import"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # File selection

    def execute(self, context):
        start_time = time.perf_counter()
        global csv_ifc_filepath  # Access global variable
        if not self.filepath:
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}
        # Ensure file is a CSV
        if not self.filepath.lower().endswith('.csv'):
            self.report({'ERROR'}, "Selected file is not a CSV")
            return {'CANCELLED'}
        csv_ifc_filepath= self.filepath 
        try:
            with open(csv_ifc_filepath, 'r', newline='') as file:
                reader = csv.reader(file)
                data = list(reader)
            if not data:
                self.report({'WARNING'}, "CSV file is empty")
                return {'CANCELLED'}
            self.report({'INFO'}, f"Imported {len(data)} rows from CSV")
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            print(f"Execution time: {elapsed_time:.6f} seconds")

        except Exception as e:
            self.report({'ERROR'}, f"Failed to read CSV: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class IFCAssign_Runscript(bpy.types.Operator):
    bl_idname = "ifc.assign"
    bl_label = "Assign IFC classes"
    bl_description = "Assign IFC classes, predefined type and Property Sets based on the CSV"

    def execute(self, context):
        start_time = time.perf_counter()
        global csv_ifc_filepath
        if not csv_ifc_filepath:
            self.report({'ERROR'}, "No CSV file imported yet")
            return {'CANCELLED'}  
        try:
            active_obj = bpy.context.view_layer.objects.active
            if active_obj:
                df = pd.read_csv(csv_ifc_filepath, encoding="utf-8",delimiter=";")
                # Verifica che la colonna "To be deleted" esista
                if "Ifc Class" not in df.columns:
                    self.report({'ERROR'},"Error: The column 'Ifc Class' does not exist in the CSV file.")
                if "Predefined Type" not in df.columns:
                    self.report({'ERROR'},"Error: The column 'Predefined Type' does not exist in the CSV file.")
                if "Object Type" not in df.columns:
                    self.report({'ERROR'},"Error: The column 'Object Type' does not exist in the CSV file.")    
                columns = [col for col in df.columns if col.startswith('Level_')]
                if not columns:
                    self.report({'ERROR'},"Error: No column 'Level_X' found in CSV file.")
                df_filtered = df[df['Ifc Class'].notna()]
                classes_column = df_filtered['Ifc Class']
                predefined_type_column = df_filtered['Predefined Type']
                object_type_column = df_filtered['Object Type']

                meshes_names = df_filtered[columns].apply(lambda row: row.dropna().iloc[-1] if not row.dropna().empty else None, axis=1) 
                ifcTreeAssembly.createIfcAssemblyTree(self,active_obj,meshes_names,classes_column,predefined_type_column,object_type_column) # Create a component tree of the Ifc Elements
                objects_to_delete = []
                ifcTreeAssembly.appendHierarchy(self,active_obj,objects_to_delete) # Each object of the original component tree is appended to "objects_to_delete"
                ifcTreeAssembly.deleteArray(self,objects_to_delete) # Each element in the array is deleted (the original component tree is deleted)
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                print(f"Execution time: {elapsed_time:.6f} seconds")
            else:
                self.report({'ERROR'}, "No active object selected.")
        except Exception as e:
            self.report({'ERROR'}, f"Error in assigning IFC: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}
    

class PsetsAssign_Runscript(bpy.types.Operator):
    bl_idname = "psets.assign"
    bl_label = "Assign IFC Psets"
    bl_description = "Assign IFC Property Sets based on the CSV"

    def execute(self, context):
        start_time = time.perf_counter()
        global csv_ifc_filepath
        if not csv_ifc_filepath:
            self.report({'ERROR'}, "No CSV file imported yet")
            return {'CANCELLED'}  
        try:
            active_obj = bpy.context.view_layer.objects.active
            if active_obj:
                df = pd.read_csv(csv_ifc_filepath, encoding="utf-8",delimiter=";")


                if "Ifc Class" not in df.columns:
                    self.report({'ERROR'},"Error: The column 'Ifc Class' does not exist in the CSV file.")
                levels = [col for col in df.columns if col.startswith('Level_')]
                psets = [col for col in df.columns if col.startswith('Pset_')]
                if not levels:
                    self.report({'ERROR'},"Error: No column 'Level_...' found in CSV file.")
                if not psets:
                    self.report({'ERROR'},"Error: No column 'Psets_...' found in CSV file.")
                df_filtered = df[df['Ifc Class'].notna()]
                psets_columns=df_filtered[psets]
                meshes_names = df_filtered[levels].apply(lambda row: row.dropna().iloc[-1] if not row.dropna().empty else None, axis=1) 
                ifcAssignPsets.assign_pset(meshes_names,psets_columns)
                self.report({'INFO'}, "PSets are not visible in Blender, you have to save and reopen the IFC file!")
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                print(f"Execution time: {elapsed_time:.6f} seconds")
            else:
                self.report({'ERROR'}, "No active object selected.")
        except Exception as e:
            self.report({'ERROR'}, f"Error in assigning IFC: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MakeMeshesDataUniques_Runscript)
    bpy.utils.register_class(DeleteSmallElements_RunScript)
    bpy.utils.register_class(CSVPrint_Runscript)
    bpy.utils.register_class(CSVImport_Runscript)
    bpy.utils.register_class(deleteCSVObject_RunScript)
    bpy.utils.register_class(simplifyCSVObject_RunScript)
    bpy.utils.register_class(regroupCSVObject_RunScript)
    bpy.utils.register_class(CSVPrintIFC_Runscript)
    bpy.utils.register_class(IFCCSVLoad_Runscript)
    bpy.utils.register_class(IFCAssign_Runscript)
    bpy.utils.register_class(PsetsAssign_Runscript)

def unregister():
    bpy.utils.unregister_class(MakeMeshesDataUniques_Runscript)
    bpy.utils.unregister_class(DeleteSmallElements_RunScript)
    bpy.utils.unregister_class(CSVPrint_Runscript)
    bpy.utils.unregister_class(CSVImport_Runscript)
    bpy.utils.unregister_class(deleteCSVObject_RunScript)
    bpy.utils.unregister_class(simplifyCSVObject_RunScript)
    bpy.utils.unregister_class(regroupCSVObject_RunScript)
    bpy.utils.unregister_class(CSVPrintIFC_Runscript)
    bpy.utils.unregister_class(IFCCSVLoad_Runscript)
    bpy.utils.unregister_class(IFCAssign_Runscript)
    bpy.utils.unregister_class(PsetsAssign_Runscript)
