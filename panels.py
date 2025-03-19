import bpy

class MyProperties(bpy.types.PropertyGroup):
    my_float: bpy.props.FloatProperty(
        name="[m]",
        description="A custom float property",
        default=0.1,
        min=0.0,
        max=0.5
    )



class CustomPanel_DeleteSmallElements(bpy.types.Panel):
    bl_label = "Delete Small Objects" # Title of the panel
    bl_idname = "Custom_panel_DeleteSmallElements" # ID of the panel
    bl_space_type = 'VIEW_3D' # Sidebar in 3D View
    bl_region_type = 'UI' # Places it in the side panel
    bl_category = "PLM-to-IFC" # New tab in the N-panel
    def draw(self, context): # This function is mandatory and is to draw the panel in the UI
        layout = self.layout # The layout is reffered to the layout of the panel that we are creating
        obj = context.object # With this we can ensure that the layout (button, properties, etc...) that we want to add are shown only when an object is selected

        if obj:
            # If an object is selected then the layout is shown
            # Create a row for the float
            row = layout.row(align=True,heading="Delete object smaller than:")
            row.prop(obj.my_properties, "my_float") # Add a float operator called "my_float" and contanined in the registered class "my_properties"
            # Create another row for the delete button
            row2 = layout.row(align=True)
            row2.label(text="Delete small elements")
            row2.operator("object.run_script", text="", icon="TRASH") # The operator has the bl_idname "object.run_script" and you can find it in the operators file
        else:
            # If an object is not selected then the layout is not shown, but only a label 
            layout.label(text="No object selected")

# For reading rapidity sake, comments from now won't repeat the same thing said before
# Panel for makinf meshes uniques
class CustomPanel_MakeMeshesUnique(bpy.types.Panel):
    bl_label = "Make meshes uniques" 
    bl_idname = "CustomPanel_MakeMeshesUnique"
    bl_space_type = 'VIEW_3D' 
    bl_region_type = 'UI' 
    bl_category = "PLM-to-IFC" # Using the same category, we put the panel in the same category of the panel before
    def draw(self, context): 
        layout = self.layout 
        obj = context.object 
        if obj:
            row = layout.row(align=True)
            row.label(text="Make meshes uniques")
            row.operator("meshesunique.run_script", text="", icon="MESH_DATA")
        else:
            layout.label(text="No object selected")

# Panel to download and upload the CSV of the components 
class CustomPanel_CSVComponents(bpy.types.Panel):
    bl_label = "CSV of the components"
    bl_idname = "Custom_panel_CSVPrint" 
    bl_space_type = 'VIEW_3D' 
    bl_region_type = 'UI' 
    bl_category = "PLM-to-IFC" 
    def draw(self, context):
        layout = self.layout
        obj = context.object
        if obj:
            row = layout.row(align=True)
            row.label(text="Download and upload")
            row.operator("csv.download", text="", icon="IMPORT")
            row.operator("csv.import", text="", icon="EXPORT")  
        else:
            layout.label(text="No object selected")

# Panel with Import & Process buttons
class CustomPanel_TreeAndGeometrySemplification(bpy.types.Panel):
    bl_label = "Simplify geometries and tree"
    bl_idname = "CustomPanel_TreeAndGeometrySemplification"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PLM-to-IFC"

    def draw(self, context):
        layout = self.layout
        # Row for deleting objects based on the imported CSV
        row1 = layout.row(align=True)
        row1.label(text="Delete objects")
        row1.operator("csv.delete", text="", icon="TRASH")
        # Row for simplify objects based on the imported CSV
        row2 = layout.row(align=True)
        row2.label(text="Simplify geometries")
        row2.operator("csv.simplify", text="", icon="MESH_CUBE")
        # Row for regrouping objects based on the imported CSV
        row3 = layout.row(align=True)
        row3.label(text="Group elements")
        row3.operator("csv.regroup", text="", icon="OUTLINER")             

# Panel for download and upload the CSV of the components with the IFC classes, and PSets
class CustomPanel_CSVIFC(bpy.types.Panel):
    bl_label = "CSV of the components for IFC"
    bl_idname = "CustomPanel_CSVIFC"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PLM-to-IFC"

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(text="Download and load CSV template for IFC")
        row.operator("csv.exportifc", text="", icon="IMPORT")
        row.operator("csv.importifc", text="", icon="EXPORT")

# Panel for assign the IFC classes and Psets to meshes
class CustomPanel_IFCClassAssgignment(bpy.types.Panel):
    bl_label = "Assign IFC classes and PSets"
    bl_idname = "CustomPanel_IFCClassAssignment"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PLM-to-IFC"

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(text="Assign IFC classes and PSets")
        row.operator("ifc.assign", text="", icon="HOME")



# This function is to register classes in Blender. We make Blender know that this class esist and it's necessary to show them
def register():
    bpy.utils.register_class(MyProperties)
    bpy.types.Object.my_properties = bpy.props.PointerProperty(type=MyProperties)
    
    bpy.utils.register_class(CustomPanel_MakeMeshesUnique)
    bpy.utils.register_class(CustomPanel_DeleteSmallElements)
    bpy.utils.register_class(CustomPanel_CSVComponents)
    bpy.utils.register_class(CustomPanel_TreeAndGeometrySemplification)
    bpy.utils.register_class(CustomPanel_CSVIFC)
    bpy.utils.register_class(CustomPanel_IFCClassAssgignment)

# This funciton is the contrary of the register functon. Is to tell Blender to close the classes that we have registered when we close the menu
def unregister():
    bpy.utils.unregister_class(CustomPanel_MakeMeshesUnique)
    bpy.utils.unregister_class(CustomPanel_DeleteSmallElements)
    bpy.utils.unregister_class(CustomPanel_CSVComponents)
    bpy.utils.unregister_class(CustomPanel_TreeAndGeometrySemplification)
    bpy.utils.unregister_class(CustomPanel_CSVIFC)
    bpy.utils.unregister_class(CustomPanel_IFCClassAssgignment)
    del bpy.types.Object.my_properties
    bpy.utils.unregister_class(MyProperties)

