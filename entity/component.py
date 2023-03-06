
from typing import List
import blenderproc.api.loader as loader
from blenderproc.python.types.MeshObjectUtility import MeshObject
from file_schema.config import ComponentData
from file_schema.scene import ElementData, PositionData
from entity.choose_mesh import get_downsampled_mesh

class Component():
    def __init__(self, data: ComponentData):
        self.name = data.name
        self.obj_id = data.obj_id
        self.path = data.path
        self.random_color = data.random_color
        self.mm_2_m = data.mm_2_m
      
    def load(self, build_convex: bool, downsample_mesh = False): 
        
        # Downsample mesh if necesarry
        if downsample_mesh:
            self.path = get_downsampled_mesh(self.path)
        
        # Load mesh
        self.obj = loader.load_obj(self.path)[0]
        if build_convex:
            self.obj.enable_rigidbody(active= True, collision_shape="COMPOUND")
            self.obj.build_convex_decomposition_collision_shape(vhacd_path='resources/vhacd', cache_dir='resources/vhacd/decomp_cache/')
        
        self.obj.set_shading_mode('auto')
        self.obj.set_cp("category_id", self.obj_id)
        
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
            
                        
    def to_element(self):
        name = self.name
        pos = [ PositionData(location=obj.get_location().tolist(), orientation= obj.get_rotation_euler().tolist()) for obj in self.obj_list ]

        return ElementData(name=name, pos=pos)
    
    def from_element(self, positions: List[PositionData]):
        
        self.add_to_obj_list(max= len(positions))
        
        # Set position of all new objects. 
        for (position, obj) in zip(positions, self.obj_list):
            obj.set_location(position.location)
            obj.set_rotation_euler(position.orientation)
            