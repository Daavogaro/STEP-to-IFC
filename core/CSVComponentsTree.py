# Function to get only leaf objects (objects without children)
def get_leaf_objects(obj, hierarchy):
    """Recursively get only objects without children."""
    # If the object has no children, it is a leaf
    if not obj.children:
        return [hierarchy + [obj.name]]
    
    # Otherwise, continue checking children
    rows = []
    for child in obj.children:
        rows.extend(get_leaf_objects(child, hierarchy + [obj.name]))
    return rows

# Function to get the collection tree with only leaf objects
def get_collection_tree(obj, hierarchy):
    """Recursively get only the leaf objects in a collection."""
    rows = []
    # For each top-level object, get leaf objects
    rows.extend(get_leaf_objects(obj, hierarchy))
    
    # For each child collection, recurse
    for child in obj.children:
        rows.extend(get_collection_tree(child, hierarchy + [obj.name]))

    return rows





