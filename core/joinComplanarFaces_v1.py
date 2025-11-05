import bpy
import bmesh
from mathutils import Vector
from collections import defaultdict

# General tolerances
NORMAL_TOL = 1e-4
DIST_TOL = 1e-4

# This function returns a canonicalized normal vector
def canonicalize_normal(n: Vector) -> Vector:
    n = n.normalized() 
    abs_vals = [abs(n.x), abs(n.y), abs(n.z)]
    idx = abs_vals.index(max(abs_vals))
    if (idx == 0 and n.x < 0) or (idx == 1 and n.y < 0) or (idx == 2 and n.z < 0):
        return -n
    return n

# ----------------------------
# Solve boundary loops
# ----------------------------
def solve_boundary_loops(boundary_edges):
    adj = defaultdict(list)
    for v1, v2 in boundary_edges:
        adj[v1].append(v2)
        adj[v2].append(v1)

    visited_edges = set()
    loops = []

    for start in list(adj.keys()):
        for nxt in adj[start]:
            edge = tuple(sorted((start, nxt)))
            if edge in visited_edges:
                continue

            loop = [start]
            cur = nxt
            prev = start
            visited_edges.add(edge)

            while True:
                loop.append(cur)
                found = False
                for nb in adj[cur]:
                    e = tuple(sorted((cur, nb)))
                    if nb != prev and e not in visited_edges:
                        visited_edges.add(e)
                        prev, cur = cur, nb
                        found = True
                        break
                if cur == start:
                    loops.append(loop.copy())
                    break
                if not found:
                    break
    return loops

# This function finds coplanar groups of faces
def find_coplanar_groups(mesh, polygons):
    normal_groups = defaultdict(list) # This group contains all the normals of the faces
    for p in polygons:
        cn = canonicalize_normal(p.normal)
        key = tuple(round(v, 5) for v in cn)
        normal_groups[key].append(p.index)

    coplanar = []
    for key, indices in normal_groups.items():
        buckets = []
        for pi in indices:
            p = mesh.polygons[pi]
            pt = mesh.vertices[p.vertices[0]].co
            d = Vector(key).dot(pt)
            placed = False
            for rep_d, lst in buckets:
                if abs(rep_d - d) <= DIST_TOL:
                    lst.append(pi)
                    placed = True
                    break
            if not placed:
                buckets.append([d, [pi]])
        for rep_d, lst in buckets:
            coplanar.append(lst)
    return coplanar

# ----------------------------
# Main planar merge
# ----------------------------
def planar_merge(obj):
    mesh = obj.data
    polygons = [p for p in mesh.polygons if p.select]
    groups = find_coplanar_groups(mesh, polygons)

    # Save transforms, materials, collections
    obj_name = obj.name
    obj_matrix = obj.matrix_world.copy()
    parent_obj = obj.parent
    obj_colls = list(obj.users_collection)
    obj_mats = [slot.material for slot in obj.material_slots]

    bm = bmesh.new()
    bm_verts = {v.index: bm.verts.new(v.co) for v in mesh.vertices}
    bm.verts.ensure_lookup_table()

    # Process each coplanar group
    for group in groups:
        # Split in connected components
        adj_faces = defaultdict(set)
        for pi in group:
            p = mesh.polygons[pi]
            for pi2 in group:
                if pi2 != pi and set(p.edge_keys) & set(mesh.polygons[pi2].edge_keys):
                    adj_faces[pi].add(pi2)
                    adj_faces[pi2].add(pi)

        visited = set()
        components = []
        for pi in group:
            if pi in visited:
                continue
            stack = [pi]
            comp = set()
            while stack:
                x = stack.pop()
                if x not in visited:
                    visited.add(x)
                    comp.add(x)
                    stack.extend(adj_faces[x])
            components.append(list(comp))

        # Build faces for each connected component
        for comp in components:
            boundary_edges = []
            for pi in comp:
                p = mesh.polygons[pi]
                for ei in p.edge_keys:
                    if sum(1 for pi2 in comp if pi2 != pi and ei in mesh.polygons[pi2].edge_keys) == 0:
                        boundary_edges.append(ei)

            loops = solve_boundary_loops(boundary_edges)
            if not loops:
                continue

            # Sort loops: largest = outer, rest = holes
            loops.sort(key=lambda L: -len(L))
            outer = loops[0]
            holes = loops[1:]

            # Create NGon for outer
            try:
                bm.faces.new([bm_verts[v] for v in outer])
            except:
                pass

            # Create NGon separata per hole
            for hloop in holes:
                try:
                    bm.faces.new([bm_verts[v] for v in hloop])
                except:
                    pass

    bm.faces.ensure_lookup_table()
    bm.normal_update()

    # Create new mesh
    original_mesh_name = mesh.name
    original_object_name = obj.name
    mesh.name = f"{original_mesh_name}_old"
    obj.name = f"{original_object_name}_old"
    
    new_mesh_data = bpy.data.meshes.new(original_mesh_name)
    bm.to_mesh(new_mesh_data)
    bm.free()
    new_mesh_data.update()

    # Create new object
    new_obj = bpy.data.objects.new(original_object_name, new_mesh_data)
    new_obj.matrix_world = obj_matrix
    new_obj.parent = parent_obj

    # Copy materials
    for m in obj_mats:
        if m:
            new_mesh_data.materials.append(m)

    # Link to collections
    for col in obj_colls:
        col.objects.link(new_obj)

    # Remove old object
    bpy.data.objects.remove(obj, do_unlink=True)

    print(f"✅ Processed {obj_name}: {len(groups)} coplanar groups (fori gestiti come facce separate!)")

# ----------------------------
# Run for all meshes
# ----------------------------
print("─────────────────────────────────────────────")
for obj in [o for o in bpy.data.objects if o.type == 'MESH']:
    bpy.context.view_layer.objects.active = obj
    planar_merge(obj)

print("\n✅ Finished planar grouping + NGon merging for all meshes!")
