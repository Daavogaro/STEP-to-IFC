import bpy

class MyProperties(bpy.types.PropertyGroup):
    my_float: bpy.props.FloatProperty(
        name="",
        description="A custom float property",
        default=0.1,
        min=0.0,
        max=0.5
    )

class CustomPanel_DeleteSmallElements(bpy.types.Panel):
    bl_label = "Delete Small Objects"
    bl_idname = "Custom_panel_DeleteSmallElements"
    bl_space_type = 'VIEW_3D'  # Sidebar in 3D View
    bl_region_type = 'UI'       # Places it in the side panel
    bl_category = "PLM-to-IFC"    # New tab in the N-panel
    def draw(self, context): #This function is mandatory and is to draw the panel in the UI
        layout = self.layout #The layout is reffered to the layout of the panel that we are creating
        obj = context.object #With this we can ensure that the layout (button, properties, etc...) that we want to add are shown only when an object is selected

        if obj:
            # If an object is selected then the layout is shown
            row = layout.row(align=True,heading="Delete object smaller than [m]:")
            row.prop(obj.my_properties, "my_float") # Add a float operator called "my_float" and contanined in the registered class "my_properties"
            row2 = layout.row(align=True)
            row2.label(text="Delete small elements")
            row2.operator("object.run_script", text="", icon="TRASH") # The operator has the bl_idname "object.run_script" and you can find it in the operators file
        else:
            # If an object is not selected then the layout is not shown, but only a label 
            layout.label(text="No object selected")

class CustomPanel_CSVPrint(bpy.types.Panel):
    bl_label = "Print CSV of the components"
    bl_idname = "Custom_panel_CSVPrint"
    bl_space_type = 'VIEW_3D'  # Sidebar in 3D View
    bl_region_type = 'UI'       # Places it in the side panel
    bl_category = "PLM-to-IFC"    # New tab in the N-panel
    def draw(self, context):
        layout = self.layout
        obj = context.object
        if obj:
            # If an object is selected then the layout is shown
            # Edit, Download, Upload buttons (aligned to the right)
            row = layout.row(align=True)
            row.label(text="Click to download")
            row.operator("csv.download", text="", icon="IMPORT")  
        else:
            # If an object is not selected then the layout is not shown, but only a label 
            layout.label(text="No object selected")

              



def register():
    bpy.utils.register_class(MyProperties)
    bpy.types.Object.my_properties = bpy.props.PointerProperty(type=MyProperties)
 
    bpy.utils.register_class(CustomPanel_DeleteSmallElements)
    bpy.utils.register_class(CustomPanel_CSVPrint)


def unregister():
    bpy.utils.unregister_class(CustomPanel_DeleteSmallElements)
    bpy.utils.unregister_class(CustomPanel_CSVPrint)
    del bpy.types.Object.my_properties
    bpy.utils.unregister_class(MyProperties)

