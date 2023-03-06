import os
import hashlib
import open3d as o3d
import numpy as np

# Reduce vertecies in mesh for simulation
def choose_mesh( input_file: str, cache_folder: str = "./resources/obj_cache/", num_of_triangles: int = 8192):

    # Load in mesh
    mesh_in = o3d.io.read_triangle_mesh(input_file)
    
    # Check if optimization is needed
    if len(mesh_in.triangles) < num_of_triangles:
        return input_file
    
    # Calculate mesh
    print("Hashing mesh of " + input_file)
    mesh_data = np.asarray(mesh_in.triangles)
    mesh_data = mesh_data * num_of_triangles
    hash_digits = hashlib.sha1(mesh_data.tobytes()).hexdigest()
    hash_digits = hash_digits[:6]
    
    # Check if optimized obj already exist
    cached_file = cache_folder + hash_digits + ".ply"
    if os.path.isfile(cached_file):
        return cached_file
    
    # Create the folder if it does not exist
    if not os.path.exists(cache_folder):
        os.makedirs(cache_folder)
    
    print("Downsampling mesh of " + input_file)
    # Generate simpler mesh and save file
    mesh_out = mesh_in.simplify_quadric_decimation(target_number_of_triangles= num_of_triangles)
    o3d.io.write_triangle_mesh(cached_file, mesh_out)
    return cached_file
      