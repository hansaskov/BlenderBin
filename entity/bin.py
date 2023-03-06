import numpy as np
import blenderproc.api.loader as loader
from file_schema.config import Bin_data
from file_schema.scene import Element_data, Position_data
from entity.choose_mesh import get_downsampled_mesh


class Bin():
    def __init__(self, data: Bin_data):
        self.name = data["name"]
        self.path = data["path"]
        self.random_color = data["random_color"]
        self.mm_2_m = data["mm_2_m"]
        self.dimensions = data["dimensions"]

        if self.mm_2_m:
                self.dimensions =np.multiply(self.dimensions, 1 / 1000)
                
    def load(self, build_convex: bool, downsample_mesh = False, ): 
        
        # Downsample mesh if necesarry
        if downsample_mesh:
            self.path = get_downsampled_mesh(self.path)
        
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
        self.obj.set_cp("category_id", "bin")
        

    
    def to_element(self):
        name = self.name
        pos = Position_data(
            location= self.obj.get_location().tolist(), 
            orientation= self.obj.get_rotation_euler().tolist()
            )
        
        return Element_data(name= name, pos=[pos])
    
    def from_element(self, position: Position_data):
        self.obj.set_location(position["location"])
        self.obj.set_rotation_euler(position["orientation"])
        