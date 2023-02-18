import blenderproc as bproc
import open3d as o3d
import argparse
import numpy as np
import json
import random
import sys
import os

myDir = os.getcwd()
sys.path.append(myDir)

from Scene import Scene
from Entity import Component, Bin

from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.types.MaterialUtility import Material

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
    def __init__(self, args: argparse.Namespace):
        bproc.init()
        
        self.config_path = str(args.config_path)
        
        with open(self.config_path, 'r') as f:
            data = json.load(f)
                  
        self.components = list(map(lambda comp: Component(comp), data["components"]))
        self.bins = list(map(lambda bin: Bin(bin), data["bins"]))
        
        self.bin = self.bins[0]
        self.walls = Walls()
        
        self.bin.load(build_convex=True, downsample_mesh=True)
        
        for entities in self.components:
            entities.load(build_convex=True, downsample_mesh= True)
                  
    def sample_pose(self, obj: MeshObject):
        # Get dimensions of bin
        x, y, z =  (self.bin.dimensions)

        # Calculate volume diffrence between components and bin
        total_volume = sum(list(map(lambda comp: comp.volume * len(comp.obj_list), self.components)))
        box_volume = x * y * z
        volume_frac = total_volume / box_volume

        obj.set_rotation_euler(bproc.sampler.uniformSO3())
        obj.set_location(np.random.uniform(
            [ -x*0.35, -y*0.35, z * 1.1 ], 
            [ x*0.35,  y*0.35,  z * 5 * volume_frac  ]
        ))
        
    def get_all_comp_objs(self): 
        return sum(list(map(lambda comp: comp.obj_list, self.components)), [])
    
    def get_amount_of_components(self):
        return sum(list(map(lambda comp: len(comp.obj_list), self.components)))
    
    def get_scene(self):
        comps = [ comp.get_element() for comp in self.components ]
        bin = self.bin.to_element() 
        
        return Scene(self.config_path, comps, bin)
        
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
            max_tries= 300,
            mode_on_failure='last_pose',
        )
        
        # Remove walls if not used in sim
        if use_walls: 
            # Run the physics simulation without
            bproc.object.simulate_physics(
            min_simulation_time=1,
            max_simulation_time=2,
            check_object_interval= 0.5,
            object_stopped_location_threshold = 0.01,
            object_stopped_rotation_threshold = 5,
            substeps_per_frame = 30,
            solver_iters= 20,
            ) 
        
        self.walls.set_home_pos()
            
        # Run the physics simulation without
        bproc.object.simulate_physics_and_fix_final_poses(
            min_simulation_time=2,
            max_simulation_time=3,
            check_object_interval= 0.5,
            object_stopped_location_threshold = 0.01,
            object_stopped_rotation_threshold = 5,
            substeps_per_frame = 30,
            solver_iters= 20,
        )  
        
parser = argparse.ArgumentParser()
parser.add_argument('--comp-amount-min',  nargs='?', default='1', help='The min amount of components that should be in the bin')
parser.add_argument('--comp-amount-max',  nargs='?', default='15', help='The max amount of components that can be in the bin')
parser.add_argument('--number-of-runs',   nargs='?', default='25', help='The number of simulations you would like to do')
parser.add_argument('--config-path',      nargs='?', default='config.json', help='filepath to configuration JSON file')
args = parser.parse_args()

simulator = Simulator(args= args)

low = int(args.comp_amount_min)
high= int(args.comp_amount_max)
size= int(args.number_of_runs)

comp_amount_list = np.random.randint(low=low, high=high, size=size)
comp_amount_list.sort()

for comp_amount in comp_amount_list:
    simulator.run(comp_amount, False)
    scene = simulator.get_scene()
    scene.save_to_folder("./resources/simulations/queue")