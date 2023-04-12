import numpy as np
import blenderproc.api.loader as loader
from file_schema.config import BinData
from file_schema.scene import ElementData, PositionData
from entities.entities_logic import get_downsampled_mesh

class Bin():
    def __init__(self, data: BinData):
        self.name = data.name
        self.path = data.path
        self.random_color = data.random_color
        self.random_texture = data.random_texture
        self.mm_2_m = data.mm_2_m
        self.dimensions = data.dimensions

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
            self.obj.enable_rigidbody(active= False, collision_shape="COMPOUND", friction = 100.0, linear_damping = 0.99, angular_damping = 0.99)
            self.obj.build_convex_decomposition_collision_shape(vhacd_path='resources/vhacd', cache_dir='resources/vhacd/decomp_cache/')
        
        # Check if mesh has a valid UV-mapping
        if not self.obj.has_uv_mapping:
            # Add UV-mapping
            self.obj.add_uv_mapping("smart")

        # Use vertex color for texturing
        for mat in self.obj.get_materials():
            mat.map_vertex_color()

        # Scale down
        if self.mm_2_m:
            self.obj.set_scale([1/1000, 1/1000, 1/1000])
        
        # Set at middle
        self.obj.set_location([0, 0, 0])
        self.obj.set_shading_mode('auto')
        self.obj.set_cp("category_id", 0)
        

    def to_element(self):
        name = self.name
        pos = PositionData(
            location= self.obj.get_location().tolist(), 
            orientation= self.obj.get_rotation_euler().tolist()
            )
        
        return ElementData(name= name, pos=[pos])
    
    def from_element(self, position: PositionData):
        self.obj.set_location(position.location)
        self.obj.set_rotation_euler(position.orientation)
        