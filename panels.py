import bpy

class MyProperties(bpy.types.PropertyGroup):
    my_float: bpy.props.FloatProperty(
        name="[m]",
        description="Set the minimum X,Y and Z dimensions of an object",
        default=0.1,
        min=0.0,
        max=0.5
    )



class CustomPanel_GeomAndTreeSempl(bpy.types.Panel):
    bl_label = "Geometry and tree assembly simplification" # Title of the panel
    bl_idname = "Custom_panel_GeoAndTreeSempl" # ID of the panel
    bl_space_type = 'VIEW_3D' # Sidebar in 3D View
    bl_region_type = 'UI' # Places it in the side panel
    bl_category = "STEP-to-IFC" # New tab in the N-panel
    def draw(self, context): # This function is mandatory and is to draw the panel in the UI
        layout = self.layout # The layout is reffered to the layout of the panel that we are creating
        obj = context.object # With this we can ensure that the layout (button, properties, etc...) that we want to add are shown only when an object is selected

        if obj:
            # If an object is selected then the layout is shown
            # Create a row for making meshes uniques
            row1 = layout.row(align=True)
            row1.label(text="Make meshes uniques")
            row1.operator("meshesunique.run_script", text="", icon="MESH_DATA")
            # Create a row for deleting small objects
            row2 = layout.row(align=True)
            # Left side: label and float
            col_left = row2.column()
            row_left = col_left.row(align=True)
            row_left_split = row_left.split(factor=0.60)
            row_left_split.label(text="Delete object smaller than:")
            row_left_split.prop(obj.my_properties, "my_float", text="[m]")  # Add a float operator called "my_float" and contanined in the registered class "my_properties"
            row2.operator("object.run_script", text="", icon="TRASH") # The operator has the bl_idname "object.run_script" and you can find it in the operators file
            row3 = layout.row(align=True)
            row3.label(text="CSV to add system properties")
            row3.operator("csv.download", text="", icon="IMPORT")
            row3.operator("csv.import", text="", icon="EXPORT") 

            # Row for deleting objects based on the imported CSV
            row4 = layout.row(align=True)
            row4.label(text="Delete objects")
            row4.operator("csv.delete", text="", icon="TRASH")
            # Row for simplify objects based on the imported CSV
            row5 = layout.row(align=True)
            row5.label(text="Simplify geometries")
            row5.operator("csv.simplify", text="", icon="MESH_CUBE")
            # Row for regrouping objects based on the imported CSV
            row6 = layout.row(align=True)
            row6.label(text="Parse assemblies")
            row6.operator("csv.regroup", text="", icon="OUTLINER")
        else:
            # If an object is not selected then the layout is not shown, but only a label 
            layout.label(text="No object selected")
            
# For reading rapidity sake, comments from now won't repeat the same thing said before
# Panel for assign the IFC classes and Psets to meshes
class CustomPanel_IFCAssgignment(bpy.types.Panel):
    bl_label = "Assign IFC classes and PSets"
    bl_idname = "CustomPanel_IFCAssignment"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "STEP-to-IFC" # Using the same category, we put the panel in the same category of the panel before

    def draw(self, context):
        layout = self.layout
        obj = context.object # With this we can ensure that the layout (button, properties, etc...) that we want to add are shown only when an object is selected

        if obj:
            # Row for download and upload the CSV of the components with the IFC classes, and PSets
            row1 = layout.row(align=True)
            row1.label(text="CSV to add IFC properties")
            row1.operator("csv.exportifc", text="", icon="IMPORT")
            row1.operator("csv.importifc", text="", icon="EXPORT")
            # Row for assign IFC classes and attributes
            row2 = layout.row(align=True)
            row2.label(text="Assign IFC classes")
            row2.operator("ifc.assign", text="", icon="HOME")
            # Row for assign PSets and properties
            row3 = layout.row(align=True)
            row3.label(text="Assign PSets to IFC elements")
            row3.operator("psets.assign", text="", icon="LONGDISPLAY")
        else:
            # If an object is not selected then the layout is not shown, but only a label 
            layout.label(text="No object selected")



# This function is to register classes in Blender. We make Blender know that this class esist and it's necessary to show them
def register():
    bpy.utils.register_class(MyProperties)
    bpy.types.Object.my_properties = bpy.props.PointerProperty(type=MyProperties)

    bpy.utils.register_class(CustomPanel_GeomAndTreeSempl)
    bpy.utils.register_class(CustomPanel_IFCAssgignment)

# This funciton is the contrary of the register functon. Is to tell Blender to close the classes that we have registered when we close the menu
def unregister():
    bpy.utils.unregister_class(CustomPanel_GeomAndTreeSempl)
    bpy.utils.unregister_class(CustomPanel_IFCAssgignment)
    del bpy.types.Object.my_properties
    bpy.utils.unregister_class(MyProperties)

