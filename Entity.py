from blenderproc import loader
import open3d as o3d
import numpy as np
import os
import hashlib
from typing import List
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.api.object import delete_multiple
from scene_file import Position, Element
from dataclasses import dataclass
from config_file import Component_data, Bin_data, Config_file
import time

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
    
    print("Downsampling mesh of " + input_file)
    # Generate simpler mesh and save file
    mesh_out = mesh_in.simplify_quadric_decimation(target_number_of_triangles= num_of_triangles)
    o3d.io.write_triangle_mesh(cached_file, mesh_out)
    return cached_file
      
@dataclass
class Component():
    def __init__(self, name: str, path: str, random_color: bool, mm_2_m: bool):
        self.name = name
        self.path = path
        self.random_color = random_color
        self.mm_2_m = mm_2_m
      
    def load(self, build_convex: bool, downsample_mesh = False, ): 
        
        # Downsample mesh if necesarry
        if downsample_mesh:
            self.path = choose_mesh(self.path)
        
        # Load mesh
        self.obj = loader.load_obj(self.path)[0]
        if build_convex:
            self.obj.enable_rigidbody(active= True, collision_shape="COMPOUND")
            self.obj.build_convex_decomposition_collision_shape(vhacd_path='resources/vhacd', cache_dir='resources/vhacd/decomp_cache/')
        
        self.obj.set_shading_mode('auto')
        self.obj.set_cp("category_id", self.name)
        
        if (self.mm_2_m):
            self.obj.set_scale([1/1000, 1/1000, 1/1000])
        
        # Get component name and save output path.
        self.volume = self.obj.get_bound_box_volume()
        self.material = self.obj.get_materials()
        
        # Dreate new list of dublicate objects
        self.obj_list: list[MeshObject] = [self.obj]

    def add_to_obj_list(self, max: int):
        
        difference = max - len(self.obj_list)
        if difference > 0:
            for i in range(difference):
                self.obj_list.append(self.obj.duplicate())
            
                        
    def get_element(self):
        name = self.name
        pos = [Position(location=obj.get_location().tolist(), orientation= obj.get_rotation_euler().tolist()) for obj in self.obj_list]

        return Element(name, pos)
    
    def from_element(self, positions: List[Position]):
        # Set the component amount
        self.add_to_obj_list(max= len(positions))
        
        # Set position of all new objects. 
        for (position, obj) in zip(positions, self.obj_list):
            obj.set_location(position.location)
            obj.set_rotation_euler(position.orientation)
            
class Bin():
    def __init__(self, name: str, path: str, random_color: bool, mm_2_m: bool, dimensions: List[float]):
        self.name = name
        self.path = path
        self.random_color = random_color
        self.mm_2_m = mm_2_m
        self.dimensions = dimensions

        if self.mm_2_m:
                self.dimensions =np.multiply(self.dimensions, 1 / 1000)
                
    def load(self, build_convex: bool, downsample_mesh = False, ): 
        
        # Downsample mesh if necesarry
        if downsample_mesh:
            self.path = choose_mesh(self.path)
        
        # Load mesh
        self.obj = loader.load_obj(self.path)[0]
        
        # Enable physics and construct decomposition.
        if build_convex:
            self.obj.enable_rigidbody(active= False, collision_shape="COMPOUND")
            self.obj.build_convex_decomposition_collision_shape(vhacd_path='resources/vhacd', cache_dir='resources/vhacd/decomp_cache/')
        
        if self.mm_2_m:
            self.obj.set_scale([1/1000, 1/1000, 1/1000])
        
        self.obj.set_location([0, 0, 0])
        self.obj.set_shading_mode('auto')
        self.obj.set_cp("category_id", self.name)
        

    
    def to_element(self):
        name = self.name
        pos = Position(self.obj.get_location().tolist(), self.obj.get_rotation_euler().tolist())
        
        return Element(name, [pos])
    
    def from_element(self, position: Position):
        self.obj.set_location(position.location)
        self.obj.set_rotation_euler(position.orientation)
        