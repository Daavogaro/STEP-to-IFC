import bpy
import pandas as pd
import bonsai.tool.ifc as ifcTool
import bonsai.tool.pset as psetTool


# Function for append all the children of an object in array
def appendHierarchy(obj,array):
    array.append(obj) # Append the object to the array
    if obj.children: # If there are children
        for child in obj.children: # For each child reiterate the function
            appendHierarchy(child,array)

# Function to return for each elemetn
def return_psets(name,meshes_names,psets_columns):
    counter = 0 # Initialize the counter for the index 
    objs=[] # Array for the Psets of the selected object
    for mesh_name in meshes_names: # Find in the column of the meshes the row of the selected object
        if name == mesh_name:
            row = psets_columns.iloc[counter] # Select the right row
            psets = [col for col in row.index] # Array of the columns name of the Pset
            
            for pset in psets: # For each column (each Pset)
                property_value=row[pset] # Select the value of the Pset
                if pd.notna(property_value): 
                    # If is not empty create the object for the Pset
                    split_values= pset.split('/') # Split the Pset name and the Single Property name
                    pset_name,property_name=split_values
                    # Create an object with the Pset name, the Single Property name and the Property Value 
                    pset_obj={"name":pset_name,"properties":{property_name:property_value}}
                    pset_is_contained=False # Suppose that the Pset is not contained in the objs array
                    for obj in objs:
                        # Check if the pset is already in objs
                        if obj["name"] == pset_obj["name"]:
                            # If it exists, append only the new property to the existing Pset
                            obj["properties"][property_name] = property_value
                            pset_is_contained = True # Update the variable
                            break  # Exit loop once found
                    if not pset_is_contained: # If the variable is False (the Pset is not in objs array)
                        objs.append(pset_obj) # Append the complete Pset in the array
        counter += 1 # Update the counter
    return objs # Return the array

# Function to assign the Pset 
def assign_pset(meshes_names,psets_columns):
    # Now we select all the IFC object in the tree under the active_obj
    active_obj = bpy.context.view_layer.objects.active
    all_obj=[]
    appendHierarchy(active_obj,all_obj)
    all_obj_set=set(all_obj) # Clean the eventual duplicates
    file=ifcTool.Ifc.get() # Function that return the object of the IFC file even it's not saved
    file_path=ifcTool.Ifc.get_path() # Function that return the path of the IFC file even it's not saved
    
    
    for obj in all_obj_set:
        print("____________________________________________________")
        ifc_obj=(ifcTool.Ifc.get_entity(obj)) # Select the IFC object
        psets=return_psets(ifc_obj.Name,meshes_names,psets_columns) # Return the Psets related to that object in the CSV
        if len(psets)>0:
            for pset in psets:
                is_applicable=psetTool.Pset.is_pset_applicable(ifc_obj,pset['name']) # If the Pset is applicable
                if is_applicable:
                    print(f"For the obj {ifc_obj.Name} the {pset['name']} is applicable")
                    ifc_pset=ifcTool.Ifc.run("pset.add_pset",product=ifc_obj,name=pset['name']) # Add the Pset
                    for property_name, property_value in pset['properties'].items(): # Assign all the Single Properties and Values
                        print(f"{property_name}:{property_value}")
                        ifcTool.Ifc.run("pset.edit_pset",pset=ifc_pset,properties={property_name:property_value})
                else: 
                    print(f"The {pset['name']} is not applicable")
    file.write(file_path) # Write the new data in the Ifc File 
    print(f"IFC file saved: {file_path}")

