# bin_simulator.py
import blenderproc as bproc

import os
import sys

myDir = os.getcwd()
sys.path.append(myDir)

from file_schema.scene import SceneData
from file_schema.config import ConfigData
from file_schema.schema_logic import load_schema_from_file, save_schema_to_folder
from blenderproc.python.types.MeshObjectUtility import MeshObject
from entities.component import Component
from entities.bin import Bin
import argparse
import numpy as np
import random

# Global variables
vhacd_path = 'resources/vhacd'
cache_path = vhacd_path + '/decomp_cache'

class Walls:
    
    def __init__(self):
        self.planes = [
            bproc.object.create_primitive('PLANE', scale=[20, 20, 1], rotation=[-1.570796, 0, 0]),
            bproc.object.create_primitive('PLANE', scale=[20, 20, 1],  rotation=[1.570796, 0, 0]),
            bproc.object.create_primitive('PLANE', scale=[20, 20, 1],  rotation=[0, -1.570796, 0]),
            bproc.object.create_primitive('PLANE', scale=[20, 20, 1],  rotation=[0, 1.570796, 0])
        ]
        self.set_home_pos()
        
        for wall in self.planes:
            wall.enable_rigidbody(active=False, collision_shape="COMPOUND")
            wall.build_convex_decomposition_collision_shape(vhacd_path, cache_dir=cache_path)
            
    def set_pos(self, bin_shape):
        self.planes[0].set_location([0, bin_shape[1]/2, 0])
        self.planes[1].set_location([0, -bin_shape[1]/2, 0])
        self.planes[2].set_location([bin_shape[0]/2,0 , 0])
        self.planes[3].set_location([-bin_shape[0]/2, 0, 0])
        
    def set_home_pos(self):
        self.set_pos([-1000, -1000, 0])

class Simulator:
    def __init__(self, config_path: str, config_data: ConfigData  ):       
        self.config_path = config_path   
        self.components = [Component(comp_data) for comp_data in config_data.components]
        self.bins = [Bin(bin_data) for bin_data in config_data.bins]        
        
        self.bin = self.bins[0]
        self.walls = Walls()
        
        self.bin.load(build_convex=True, downsample_mesh=True)
        
        for entities in self.components:
            entities.load(build_convex=True, downsample_mesh= True)
                  
    def sample_pose(self, obj: MeshObject):
        # Get dimensions of bin
        x, y, z =  (self.bin.dimensions)

        # Calculate volume diffrence between components and bin
        total_volume = sum([comp.volume * len(comp.obj_list) for comp in self.components])
        box_volume = x * y * z
        volume_frac = total_volume / box_volume

        obj.set_rotation_euler(bproc.sampler.uniformSO3())
        obj.set_location(np.random.uniform(
            [ -x*0.35, -y*0.35, z * 1.1 ], 
            [ x*0.35,  y*0.35,  z * 5 * volume_frac  ]
        ))
        
    def get_all_comp_objs(self): 
        return sum([comp.obj_list for comp in self.components], [])
    
    def get_amount_of_components(self):
        return sum([len(comp.obj_list) for comp in self.components])
    
    def to_scene(self):
        comps = [ comp.to_element() for comp in self.components ]
        bin = self.bin.to_element()         
        return SceneData(config_path= self.config_path, comps=comps, bin=bin, cameras= None)
        
    def run(self, amount_of_components, use_walls = False):
        
        # Add components to list
        comp = random.choice(self.components)
        comp.add_to_obj_list(max= amount_of_components)
        
        # Set walls for sampling
        self.walls.set_pos(self.bin.dimensions)
        
        # Sample the poses of all component objects above the ground without any collisions in-between
        bproc.object.sample_poses(
            objects_to_sample= self.get_all_comp_objs(),
            sample_pose_func=self.sample_pose,
            objects_to_check_collisions=self.get_all_comp_objs() + [self.bin.obj] + self.walls.planes,
            max_tries= 1000,
            mode_on_failure='last_pose',
        )
        
        # Remove walls if not used in sim
        if use_walls: 
            # Run the physics simulation without
            bproc.object.simulate_physics(
            min_simulation_time=2,
            max_simulation_time=3,
            check_object_interval= 0.5,
            object_stopped_location_threshold = 0.01,
            object_stopped_rotation_threshold = 5,
            substeps_per_frame = 30,
            solver_iters= 20,
            ) 
        
        self.walls.set_home_pos()
            
        # Run the physics simulation without
        bproc.object.simulate_physics_and_fix_final_poses(
            min_simulation_time=0.99,
            max_simulation_time=1,
            check_object_interval= 0.5,
            object_stopped_location_threshold = 0.01,
            object_stopped_rotation_threshold = 5,
            substeps_per_frame = 30,
            solver_iters= 20,
        )  
        
parser = argparse.ArgumentParser()
parser.add_argument('--comp-amount-min', nargs='?', default='1', help='The min amount of components that should be in the bin')
parser.add_argument('--comp-amount-max', nargs='?', default='15', help='The max amount of components that can be in the bin')
parser.add_argument('--runs',  nargs='?', default='5', help='The number of simulations you would like to do')
parser.add_argument('--walls', action=argparse.BooleanOptionalAction, default=False, help="Simulate twice, first with walls, afterwards without")
parser.add_argument('--config-path',     nargs='?', default='config.json', help='filepath to configuration JSON file')
args = parser.parse_args()

config_file = str(args.config_path)

config_data = load_schema_from_file(file_path=config_file, data_class= ConfigData)
simulator = Simulator(config_path= config_file, config_data= config_data)

low = int(args.comp_amount_min)
high= int(args.comp_amount_max)
size= int(args.runs)

comp_amount_list = np.random.randint(low=low, high=high, size=size)
comp_amount_list.sort()

for comp_amount in comp_amount_list:
    simulator.run(comp_amount, use_walls= args.walls)
    scene = simulator.to_scene()
    save_schema_to_folder(data= scene, folder_path= "./resources/simulations/queue")