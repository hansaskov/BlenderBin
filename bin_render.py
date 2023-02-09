import blenderproc as bproc
from typing import List
import argparse
import numpy as np
import os
import math
import json
import random
import colorsys

from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.types.MaterialUtility import Material

class Config:
    class Component:
        def __init__(self, json_data):
            self.name: str = json_data['name']
            self.path: str = json_data['path']
            self.random_color: bool = json_data['random_color']
            self.mm_2_m: bool = json_data['mm_2_m']

    class Bin:
        def __init__(self, json_data):
            self.path: str = json_data['path']
            self.random_color: bool = json_data['random_color']
            self.mm_2_m: bool = json_data['mm_2_m']
            self.dimensions: List[float] = json_data['dimensions']

    class Camera:
        def __init__(self, json_data):
            self.cx: float = json_data['cx']
            self.cy: float = json_data['cy']
            self.fx: float = json_data['fx']
            self.fy: float = json_data['fy']
            self.height: int = json_data['height']
            self.width: int = json_data['width']

    def __init__(self, json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)

        self.components = [self.Component(comp) for comp in data['comp']]
        self.bins = [self.Bin(bin) for bin in data['bins']]
        self.camera = self.Camera(data['camera'])


# Global variables
vhacd_path = 'resources/vhacd'
temp_path = vhacd_path + "/decomp_temp"
cache_path = vhacd_path + '/decomp_cache'
haven_path = 'resources/blenderproc/haven/'
output_dir = 'data/'

class Render:
    
    class Component:
        def __init__(self, comp_config: Config.Component):

            # Enable collision, create convex decomposition.
            self.obj = bproc.loader.load_obj(comp_config.path)[0]
            self.obj.enable_rigidbody(active=True, collision_shape="COMPOUND")
            self.obj.build_convex_decomposition_collision_shape(vhacd_path, cache_dir=cache_path)

            # Scale comp if given in mm
            if (comp_config.mm_2_m):
                self.obj.set_scale([1/1000, 1/1000, 1/1000])

            # Set obj variables
            self.obj.set_shading_mode('auto')
            self.obj.set_cp("category_id", comp_config.name)

            # Get component name and save output path.
            self.name = self.obj.get_name()
            self.volume = self.obj.get_bound_box_volume()
            self.material = self.obj.get_materials()
            self.name = comp_config.name
            self.path = comp_config.path
            self.mm_2_m = comp_config.mm_2_m
            self.random_color = comp_config.random_color

            # Make a list of all the components (max components)
            self.obj_list: list[MeshObject] = [self.obj]

        def add_to_obj_list(self, amount: int):
            # Check if new components needs to be added
            for i in range(amount):
                self.obj_list.append(self.obj.duplicate())

    class Bin:
        def __init__(self, bin_config: Config.Bin):

            # Enable collision, create convex decomposition.
            self.obj = bproc.loader.load_obj(bin_config.path)[0]
            self.obj.enable_rigidbody(active=False, collision_shape="COMPOUND")
            self.obj.build_convex_decomposition_collision_shape(vhacd_path, temp_dir=temp_path, cache_dir=cache_path)

            dimensions = bin_config.dimensions

            # Scale bin if given in mm
            if (bin_config.mm_2_m):
                self.obj.set_scale([1/1000, 1/1000, 1/1000])
                dimensions =np.multiply(dimensions, 1 / 1000)

            self.length_x = dimensions[0]
            self.length_y = dimensions[1]
            self.length_z = dimensions[2]

            self.obj.set_location([0, 0, 0])
            self.obj.set_shading_mode('auto')
            self.obj.set_cp("category_id", "bin")
            self.material = self.obj.get_materials()

            self.path = bin_config.path
            self.mm_2_m = bin_config.mm_2_m
            self.random_color = bin_config.random_color
            
    class Wall:
        def __init__(self, bin_shape):

            self.planes = [
                bproc.object.create_primitive('PLANE', scale=[bin_shape[0], 20, 1], location=[0, bin_shape[1]/2, 0], rotation=[-1.570796, 0, 0]),
               bproc.object.create_primitive('PLANE', scale=[bin_shape[0], 20, 1], location=[0, -bin_shape[1]/2, 0], rotation=[1.570796, 0, 0]),
               bproc.object.create_primitive('PLANE', scale=[20, bin_shape[1], 1], location=[bin_shape[0]/2,0 , 0], rotation=[0, -1.570796, 0]),
               bproc.object.create_primitive('PLANE', scale=[20,bin_shape[1], 1], location=[-bin_shape[0]/2, 0, 0], rotation=[0, 1.570796, 0])
            ]
            for wall in self.planes:
                wall.enable_rigidbody(active=False, collision_shape="COMPOUND")
                wall.build_convex_decomposition_collision_shape(vhacd_path, cache_dir=cache_path)
                wall.hide()
            
    def __init__(self, config: Config, args):
        bproc.init()

        self.instance_num = int(args.instance_num)
        self.number_of_runs = int(args.number_of_runs)
        self.comp_amount_max = int(args.comp_amount_max)
        self.comp_amount_min = int(args.comp_amount_min)
        self.random_background = bool(args.random_bg)

        self.camera = config.camera

        K = [
            [config.camera.fx, 0, config.camera.cx],
            [0, config.camera.fy, config.camera.cy],
            [0, 0, 1]
        ]
        bproc.camera.set_intrinsics_from_K_matrix(K=K, image_height=config.camera.height, image_width=config.camera.width)
        bproc.renderer.enable_depth_output(activate_antialiasing=False)
        bproc.renderer.set_max_amount_of_samples(50)

        # Create lighting
        self.light = bproc.types.Light()

        # Load the components in a list
        self.comps = list(map(lambda comp: self.Component(comp), config.components))

        # Load the bin with the environment
        self.bin = self.Bin(config.bins[0])
        
        # Load walls
        self.walls = self.Wall([self.bin.length_x, self.bin.length_y, self.bin.length_z ])


    def get_all_comp_objs(self): 
        return sum(list(map(lambda comp: comp.obj_list, self.comps)), [])


    def sample_pose(self, obj: MeshObject):
        # Define a function that samples random 6-DoF poses
        obj.set_rotation_euler(bproc.sampler.uniformSO3())

        # Calculate volume diffrence between components and bin
        total_volume = sum(list(map(lambda comp: comp.volume * len(comp.obj_list), self.comps)))
        box_volume = self.bin.length_x * self.bin.length_y * self.bin.length_z

        volume_frac = total_volume / box_volume

        obj.set_location(np.random.uniform(
            [
                -(self.bin.length_x)/2.2,
                -self.bin.length_y/2.2,
                self.bin.length_z * 1.1
            ], [
                self.bin.length_x/2.2,
                self.bin.length_y/2.2,
                self.bin.length_z * 10 * volume_frac 
            ]
        ))

    def randomize_light(self):
        # Randomize light source
        light_type = np.random.choice(["POINT", "SUN", "SPOT", "AREA"])
        self.light.set_type(light_type)

        # Move the light
        self.light.set_location(np.random.uniform([-1, -1, 5], [1, 1, 20]))
        self.light.set_rotation_euler(np.random.uniform([-0.5, -0.5, -0.5], [0.5, 0.5, 61]))
        self.light.set_color([1, 1, 1])
        self.light.set_energy(np.random.uniform(0.5, 1))

    def randomize_materials(self):
        # Make a random material
        material = bproc.material.create("random color")

        h, l, s = np.random.uniform(0.1, 0.9, 3)
        r, g, b = colorsys.hls_to_rgb(h, l, s)

        material.set_principled_shader_value("Base Color", [r, g, b, 1])
        material.set_principled_shader_value("Roughness", np.random.uniform(1, 10.0))
        material.set_principled_shader_value("Specular", np.random.uniform(0, 1))
        material.set_principled_shader_value("Metallic", np.random.uniform(0, .2))

        return material

    def randomize_camera_poses(self, amount):
        all_visible_comp = set()

        for i in range(amount):

            # Calculate a random point of interest
            poi = np.array([np.random.uniform(-0.3*self.bin.length_x, 0.3*self.bin.length_x), 
                            np.random.uniform(-0.3*self.bin.length_y, 0.3*self.bin.length_y), 
                            np.random.uniform(-0.1*self.bin.length_z, 0.3*self.bin.length_z)])

            # Sample random location
            location = bproc.sampler.shell(
                center=[0, 0, 1.64],
                radius_min=0.05,
                radius_max=0.2,
                elevation_min=-20,
                elevation_max=90,
                uniform_volume=True
            )
            # calculate rotation towards point of intrest
            rotation_matrix = bproc.camera.rotation_from_forward_vec( poi - location, inplane_rot=np.random.uniform(-0.7854, 0.7854))

            # Make tansformation matrix from location (x, y, z) and rotation matrix
            cam2world = bproc.math.build_transformation_mat(location, rotation_matrix)

            # Add camera in scene, with location and rotation.
            bproc.camera.add_camera_pose(cam2world)

            # Compute raycasting
            sqrt_rays = round(math.sqrt(self.camera.height * self.camera.width) / 4)
            obj_visible = bproc.camera.visible_objects(cam2world, sqrt_rays)

            # Filter to save shown components
            visible_comp = set(obj_visible) - (set(obj_visible) - set(self.get_all_comp_objs()) )

            # Add newly visible components to the list of all visible components
            all_visible_comp = all_visible_comp & visible_comp

        return all_visible_comp

    def run(self):
        # Randomize the number of components to use
        comp_amount_list = np.random.randint( low=self.comp_amount_min, high=self.comp_amount_max, size=self.number_of_runs)
        comp_amount_list.sort()

        for amount in comp_amount_list:

            # Make a list out of the components that should be used
            comp = random.choice(self.comps)
            comp.add_to_obj_list(amount - len(self.get_all_comp_objs()))

            # Sample the poses of all component objects above the ground without any collisions in-between
            bproc.object.sample_poses(
                objects_to_sample= self.get_all_comp_objs(),
                sample_pose_func=self.sample_pose,
                objects_to_check_collisions=self.get_all_comp_objs() + [self.bin.obj] + self.walls.planes,
                max_tries= 300,
                mode_on_failure='last_pose',
            )

            # Run the physics simulation
            bproc.object.simulate_physics_and_fix_final_poses(
                min_simulation_time=2,
                max_simulation_time=3,
                check_object_interval= 0.5,
                object_stopped_location_threshold = 0.01,
                object_stopped_rotation_threshold = 5,
                substeps_per_frame = 30,
                solver_iters= 20,
            )
        
            # Randomize material for bin
            if self.bin.random_color:
               material = self.randomize_materials()
               self.bin.obj.replace_materials(material)

            # Randomize material for components.
            for comp in self.comps:
                if comp.random_color:
                    material = self.randomize_materials()
                    for comp in comp.obj_list:
                        comp.replace_materials(material)

            # Set a random background
            if self.random_background: 
                haven_hdri_path = bproc.loader.get_random_world_background_hdr_img_path_from_haven(haven_path)
                bproc.world.set_world_background_hdr_img(haven_hdri_path)

            # Randomize lighting
            self.randomize_light()

            # Make random camera poses
            all_visible_comp = self.randomize_camera_poses(4)

            # Render Pipeline
            data = bproc.renderer.render()

            # Save data in the bop format
            bproc.writer.write_bop(
                output_dir=os.path.join(output_dir),
                dataset=self.comps[0].name + "_" + str(self.instance_num),
                target_objects= all_visible_comp | set([self.bin.obj]),
                colors=data['colors'],
                depths=data['depth'],
                color_file_format="JPEG",
                ignore_dist_thres=50,
                append_to_existing_output=True,
                save_world2cam=True,
                depth_scale=0.01,
            )

            # Reset sim and restart.
            bproc.utility.reset_keyframes()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--comp-amount-min',  nargs='?', default='3', help='The min amount of components that should be in the bin')
    parser.add_argument('--comp-amount-max',  nargs='?', default='4', help='The max amount of components that can be in the bin')
    parser.add_argument('--number-of-runs',   nargs='?', default='1', help='The number of simulations you would like to do')
    parser.add_argument('--instance-num',     nargs='?', default='1', help='Give each component a different number')
    parser.add_argument('--config-path',      nargs='?', default='config.json', help='filepath to configuration JSON file')
    parser.add_argument('--random-bg', action=argparse.BooleanOptionalAction, default=True, help="Add a random background to the skybox from the haven benchmark")
    args = parser.parse_args()

    config = Config(args.config_path)

    rend = Render(config, args)
    rend.run()
