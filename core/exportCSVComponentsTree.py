# Function to get only leaf objects (objects without children)
def get_leaf_objects(obj, hierarchy):
    # If the object has no children, it is considered a leaf node
    if not obj.children:
        return [hierarchy + [obj.name]]  # Return the hierarchy path ending with the leaf object
    
    # If the object has children, continue traversing
    rows = []
    for child in obj.children:
        # Recursively call the function for each child and extend the results
        rows.extend(get_leaf_objects(child, hierarchy + [obj.name]))
    return rows  # Return the accumulated list of leaf objects with their hierarchy

# Function to get the object tree with only leaf objects
def get_object_tree(obj, hierarchy): 
    rows = []
    # Get all leaf objects under the current object
    rows.extend(get_leaf_objects(obj, hierarchy))
    return rows  # Return the complete hierarchical tree containing only leaf objects
