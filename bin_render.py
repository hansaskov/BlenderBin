import blenderproc as bproc
import argparse
import numpy as np
import os
import math
import time
import colorsys

from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.types.MaterialUtility import Material

class Render:
    def __init__(self, args):
        bproc.init()

        self.comp_scale = 1 / 1000
        self.bin_scale = 1 / 1000
        self.scene_scale = 1

        self.bin_path = args.bin_path
        self.comp_path = args.comp_path
        self.instance_num = int(args.instance_num)
        self.comp_amount_max =  int(args.comp_amount_max)
        self.comp_amount_min =  int(args.comp_amount_min)
        self.number_of_runs = int(args.number_of_runs)
        self.image_height = int(args.height)
        self.image_width = int(args.width)
        self.bin_length_x = float(args.bin_length_x) * self.bin_scale
        self.bin_length_y = float(args.bin_length_y) * self.bin_scale
        self.bin_length_z = float(args.bin_length_z) * self.bin_scale
        self.vhacd_path = 'resources/vhacd'
        self.cache_path = 'resources/vhacd/decomp_cache'
        self.haven_path = 'resources/blenderproc/haven/'

        self.comp_rand = bool(int(args.comp_rand_color))
        self.bin_rand = bool(int(args.bin_rand_color))

        K = np.array([[
                                6045.585213009336,
                                0.0,
                                1209.1873115324627
                            ],
                            [
                                0.0,
                                6045.2679752027225,
                                1094.2715614796484
                            ],
                            [
                                0.0,
                                0.0,
                                1.0
                            ]])
            

        bproc.renderer.enable_depth_output(activate_antialiasing=False)
        bproc.renderer.set_max_amount_of_samples(50)
        bproc.camera.set_intrinsics_from_K_matrix(K=K, 
                                                    image_width= 2448, 
                                                    image_height= 2048
        )
        bproc.camera.set_resolution(self.image_width, self.image_height)
        print(bproc.camera.get_intrinsics_as_K_matrix())


        # Create lighting
        self.light = bproc.types.Light()

        # Load the bin with the environment
        self.load_bin()

        # Load the component
        self.load_component()


    def load_bin(self):
        # Load a bin object that gonna catch the components objects
        # Make the bin object actively participate in the physics simulation (they should fall into the bin)
        # Also use convex decomposition as collision shapes
        
        self.bin_obj = bproc.loader.load_obj(self.bin_path)[0]
        self.bin_obj.enable_rigidbody(active=False, collision_shape="COMPOUND")
        self.bin_obj.build_convex_decomposition_collision_shape(self.vhacd_path, cache_dir= self.cache_path)
        self.bin_obj.set_scale([self.bin_scale, self.bin_scale, self.bin_scale])
        self.bin_obj.set_location([0, 0, 0]) 
        self.bin_obj.set_shading_mode('auto')
        self.bin_obj.set_cp("category_id", 2)
        self.bin_material = self.bin_obj.get_materials()

    
    def load_component(self):
        # Load component.
        # Enable collision, create convex decomposition and copy to a list. 
        self.comp_obj = bproc.loader.load_obj(self.comp_path)[0]
        self.comp_obj.enable_rigidbody(active=True, collision_shape="COMPOUND")
        self.comp_obj.build_convex_decomposition_collision_shape(self.vhacd_path, cache_dir=self.cache_path)
        self.comp_obj.set_scale( [self.comp_scale, self.comp_scale, self.comp_scale])
        self.comp_obj.set_shading_mode('auto')
        self.comp_obj.set_cp("category_id", 1)
        
        # Get dimensions of the component and set longest x,y,z dimension
        comp_bounding_box = self.comp_obj.get_bound_box().flatten()
        self.comp_length = max(abs(comp_bounding_box))

        # Get component name and save output path. 
        self.comp_name = self.comp_obj.get_name()   
        self.output_dir = 'data/'
        self.comp_volume = self.comp_obj.get_bound_box_volume()
        self.comp_material = self.bin_obj.get_materials()

        # Make a list of all the components (max components)
        self.comp_obj_list: list[MeshObject] = [self.comp_obj]


    def sample_pose(self, obj: MeshObject):
        # Define a function that samples random 6-DoF poses
        obj.set_rotation_euler(bproc.sampler.uniformSO3())

        box_volume = ( self.bin_length_x - 2 * self.comp_length) * ( self.bin_length_y - 2 * self.comp_length) * self.bin_length_z
        comp_list_volume = self.comp_volume * len(self.comp_obj_list)
        volume_frac = comp_list_volume / box_volume

        obj.set_location(np.random.uniform(
            [
                -self.bin_length_x/2 + self.comp_length, 
                -self.bin_length_y/2 + self.comp_length, 
                self.bin_length_z * 1.1
            ], [
                self.bin_length_x/2 - self.comp_length, 
                self.bin_length_y/2 - self.comp_length, 
                self.bin_length_z * (1.1 + volume_frac * 3)
            ]
        ))

    def randomize_light(self):
        # Randomize light source
        light_type = np.random.choice(["POINT", "SUN", "SPOT", "AREA"])
        self.light.set_type(light_type)

        # Move the light
        self.light.set_location(np.multiply(np.random.uniform([-1, -1, 5], [1, 1, 20]), self.scene_scale))
        self.light.set_rotation_euler(np.random.uniform([-0.5, -0.5, -0.5], [0.5, 0.5, 61]))
        self.light.set_color([1, 1, 1])
        self.light.set_energy(np.random.uniform(0.5, 1))
    

    def randomize_materials(self):
        # Make a random material
        material = bproc.material.create("random color")

        r, g, b = np.random.uniform(0.1, 0.9, 3)

        material.set_principled_shader_value("Base Color", [r, g, b, 1])
        material.set_principled_shader_value("Roughness", np.random.uniform(1, 10.0))
        material.set_principled_shader_value("Specular", np.random.uniform(0, 1))
        material.set_principled_shader_value("Metallic", np.random.uniform(0, .2))

        return material


    def set_material(self, obj: MeshObject, material: Material):

        number_of_materials = len(obj.get_materials())
        if number_of_materials > 0:          
            for index in range(number_of_materials):
                    obj.set_material(index, material)
        else: 
            obj.add_material(material)

        


    def add_to_comp_list(self, amount: int):
        # Check if new components needs to be added
        for i in range (amount - len(self.comp_obj_list)):
            self.comp_obj_list.append(self.comp_obj.duplicate())


    def randomize_camera_poses(self, amount):
        all_visible_comp = set()

        for i in range(amount):
            # Only get the point of intrest for components that is stationary above the z axis. 
            comp_in_bin = list(filter(lambda comp: comp.get_location()[2] > 0, self.comp_obj_list)) 
            poi = bproc.object.compute_poi(np.random.choice(comp_in_bin, size=3))
            
            # Sample location
            location = bproc.sampler.shell(
                center= np.multiply([0, 0, 0.64], self.scene_scale ),
                radius_min=0.025 * self.scene_scale,
                radius_max=0.020* self.scene_scale,
                elevation_min=-10,
                elevation_max=89.5,
                uniform_volume=True
            )
            # calculate rotation towards point of intrest
            rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location, inplane_rot=np.random.uniform(-0.7854, 0.7854))

            # Make tansformation matrix from location (x, y, z) and rotation matrix
            cam2world = bproc.math.build_transformation_mat(location, rotation_matrix)

            # Add camera in scene, with location and rotation. 
            bproc.camera.add_camera_pose(cam2world)

            # Compute raycasting
            sqrt_rays = round( math.sqrt(self.image_height * self.image_width)/ 4)
            obj_visible = bproc.camera.visible_objects(cam2world, sqrt_rays) 

            # Filter to only show components
            visible_comp = list(set(obj_visible) - (set(obj_visible) - set(self.comp_obj_list)))

            # Find if the camera can see new visible components not previously seen
            new_visible_comp = set(visible_comp) - set(all_visible_comp)

            # Add newly visible components to the list of all visible components
            all_visible_comp = all_visible_comp | new_visible_comp

        return all_visible_comp


    def run(self):
        # Randomize the number of components to use
        comp_amount_list =  np.random.randint(low=self.comp_amount_min, high=self.comp_amount_max, size=self.number_of_runs)
        comp_amount_list.sort()

        for amount in comp_amount_list:
        
            # Make a list out of the components that should be used
            self.add_to_comp_list(amount)          

            # Sample the poses of all component objects above the ground without any collisions in-between
            bproc.object.sample_poses(
                self.comp_obj_list,
                sample_pose_func=self.sample_pose,
                objects_to_check_collisions=self.comp_obj_list + [self.bin_obj],
                max_tries= 1000
            )

            # Run the physics simulation
            bproc.object.simulate_physics_and_fix_final_poses(
                min_simulation_time=2,
                max_simulation_time=3,
                check_object_interval= 0.5,
                object_stopped_location_threshold = self.comp_length * 0.1,
                object_stopped_rotation_threshold = 5,
                substeps_per_frame = 30,
                solver_iters= 20,
            )

            # Change material of the bin
            if self.bin_rand:
                bin_material = self.randomize_materials()
                self.set_material(self.bin_obj, bin_material)

            # Randomize material and set component to that material. 
            if self.comp_rand:
                comp_material = self.randomize_materials()
                for comp in self.comp_obj_list: 
                    self.set_material(comp, comp_material)

            # Set a random background
            haven_hdri_path = bproc.loader.get_random_world_background_hdr_img_path_from_haven(self.haven_path)
            bproc.world.set_world_background_hdr_img(haven_hdri_path)

            # Make lighting
            self.randomize_light()

            # Make 4 random camera poses
            all_visible_comp = self.randomize_camera_poses(4)

            # render pipeline
            data = bproc.renderer.render()

            # Save data in the bop format
            bproc.writer.write_bop(
                output_dir=os.path.join(self.output_dir),
                dataset= self.comp_name + "_" + str(self.instance_num),
                target_objects= all_visible_comp | set([self.bin_obj]),
                colors=data['colors'],
                depths=data['depth'],
                color_file_format="JPEG",
                ignore_dist_thres=20 * self.scene_scale,
                append_to_existing_output=True,
                save_world2cam=True,
                depth_scale= 0.01,
            )

            # Reset sim and restart. 
            bproc.utility.reset_keyframes()

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--comp-amount-min',  nargs='?', default= '1',                                      help='The min amount of components that should be in the bin')
    parser.add_argument('--comp-amount-max',  nargs='?', default= '10',                                     help='The max amount of components that can be in the bin')
    parser.add_argument('--number-of-runs',   nargs='?', default= '25',                                      help='The number of simulations you would like to do')
    parser.add_argument('--instance-num',     nargs='?', default= '1',                                      help='Give each component a different number')
    parser.add_argument('--width',            nargs='?', default= "720",                                    help='The width of the rendered images')
    parser.add_argument('--height',           nargs='?', default= "540",                                    help='The height of the rendered images')                             
    parser.add_argument('--comp-path',        nargs='?', default= "/home/robotlab/Desktop/HAOV/DragonFeeding/3D_model/lid.obj",                 help='Path to the component object file')
    parser.add_argument('--bin-path',         nargs='?', default= "3d_models/bins/DragonBoxEnvironment.obj", help='Path to the box object file')
    parser.add_argument('--comp-rand-color',  nargs='?', default= '1',                                      help='1 if you want to randomize the colors, 0 if there should be no randomization of color')
    parser.add_argument('--bin-rand-color',   nargs='?', default= '1',                                       help='1 if you want to randomize the colors, 0 if there should be no randomization of color')
    parser.add_argument('--bin-length-x',     nargs='?', default= "176",                                    help='Length of the bin in the x axis in mm')
    parser.add_argument('--bin-length-y',     nargs='?', default= "156",                                    help='Length of the bin in the y axis in mm')
    parser.add_argument('--bin-length-z',     nargs='?', default= "100",                                    help='Height of the bin in mm')

    args = parser.parse_args()

    # Start simulation
    rend = Render(args)
    rend.run()

