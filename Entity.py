from blenderproc import loader
import open3d as o3d
import numpy as np
import os
import hashlib
from blenderproc.python.types.MeshObjectUtility import MeshObject

from Scene import Position, Element


class Entity:
    
    def __init__(self, data: dict):
        self.name = str(data["name"])
        self.path = str(data["path"])
        self.random_color = bool(data["random_color"])
        self.mm_2_m = bool(data["mm_2_m"])
        self.vhacd_path = 'resources/vhacd'
        self.cache_path = 'resources/vhacd/decomp_cache/'
        
    def to_dict(self):
        return {
            "name": self.name,
            "path": self.path,
            "random_color": self.random_color,
            "mm_2_m": self.mm_2_m
        }
        
    # Reduce vertecies in mesh for simulation
    def choose_mesh(self, input_file: str, cache_folder: str = "./resources/simulations/obj_cache/", num_of_triangles: int = 8192):
        # Load in mesh
        mesh_in = o3d.io.read_triangle_mesh(input_file)
        
        # Check if optimization is needed
        if len(mesh_in.triangles) < num_of_triangles:
            return input_file
        
        # Calculate mesh
        print("Hashing mesh of " + self.name)
        mesh_data = np.asarray(mesh_in.triangles)
        mesh_data = mesh_data * num_of_triangles
        hash_digits = hashlib.sha1(mesh_data.tobytes()).hexdigest()
        hash_digits = hash_digits[:6]
        
        # Check if optimized obj already exist
        cached_file = cache_folder + self.name + "-" + str(num_of_triangles) + '-' + hash_digits + ".ply"
        if os.path.isfile(cached_file):
            return cached_file
        
        print("Downsampling mesh of " + self.name)
        # Generate simpler mesh and save file
        mesh_out = mesh_in.simplify_quadric_decimation(target_number_of_triangles= num_of_triangles)
        o3d.io.write_triangle_mesh(cached_file, mesh_out)
        return cached_file
       
    def load(self, is_active: bool, downsample_mesh = False):
        
        if downsample_mesh:
            self.path = self.choose_mesh(self.path)
        
        # Load component
        self.obj = loader.load_obj(self.path)[0]
        self.obj.enable_rigidbody(active= is_active, collision_shape="COMPOUND")
        self.obj.build_convex_decomposition_collision_shape(self.vhacd_path, cache_dir=self.cache_path)
                
        # Scale comp if given in mm
        if (self.mm_2_m):
            self.obj.set_scale([1/1000, 1/1000, 1/1000])
            
        # Set obj variables
        self.obj.set_shading_mode('auto')
        self.obj.set_cp("category_id", self.name)
        
        # Get component name and save output path.
        self.volume = self.obj.get_bound_box_volume()
        self.material = self.obj.get_materials()
        
        
class Component(Entity):
                
    def load(self): 
        super().load(is_active= True, downsample_mesh= True)
        # Dreate new list of dublicate objects
        self.obj_list: list[MeshObject] = [self.obj]

    def add_to_obj_list(self, amount: int):
        # Check if new components needs to be added
        for i in range(amount):
            self.obj_list.append(self.obj.duplicate())
            
    def get_element(self):
        name = self.name
        pos = [Position(location=obj.get_location().tolist(), orientation= obj.get_rotation_euler().tolist()) for obj in self.obj_list]

        return Element(name, pos)

            


class Bin(Entity):
    
    def __init__(self, data: dict):
        super().__init__( data)
        self.dimensions = list(data["dimensions"])
        if self.mm_2_m:
                self.dimensions =np.multiply(self.dimensions, 1 / 1000)
                
    def to_dict(self):
        dict = super().to_dict()
        dict["dimensions"] = self.dimensions
        return dict
        
    def load(self):
        super().load(is_active= False)
        self.obj.set_location([0, 0, 0])
    
    def get_element(self):
        name = self.name
        pos = Position(self.obj.get_location().tolist(), self.obj.get_rotation_euler().tolist())
        
        return Element(name, [pos])
        
       