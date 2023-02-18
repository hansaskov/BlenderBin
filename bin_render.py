import blenderproc as bproc
import math
import colorsys
import open3d as o3d
import argparse
import numpy as np
import json
import sys
import os
import time
import random
import shutil

myDir = os.getcwd()
sys.path.append(myDir)


from Scene import Scene
from Entity import Component, Bin

from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.types.MaterialUtility import Material

haven_path = "resources/blenderproc/haven"
output_dir = "data"


class Camera:
    def __init__(self, json_data):
        self.cx: float = json_data['cx']
        self.cy: float = json_data['cy']
        self.fx: float = json_data['fx']
        self.fy: float = json_data['fy']
        self.height: int = json_data['height']
        self.width: int = json_data['width']

class Render:
                           
    def __init__(self, args: argparse.Namespace):
        bproc.init()

        self.random_background = bool(args.random_bg)
        self.config_path = str(args.config_path)
        
        with open(self.config_path, 'r') as f:
            data = json.load(f)
                  
        self.components = list(map(lambda comp: Component(comp), data["components"]))
        self.bins = list(map(lambda bin: Bin(bin), data["bins"]))
        self.bin = self.bins[0]
        self.camera = Camera(data['camera'])
        
        K = [
            [self.camera.fx, 0, self.camera.cx],
            [0, self.camera.fy, self.camera.cy],
            [0, 0, 1]
        ]
        
        bproc.camera.set_intrinsics_from_K_matrix(K=K, image_height=self.camera.height, image_width=self.camera.width)
        bproc.renderer.enable_depth_output(activate_antialiasing=False)
        bproc.renderer.set_max_amount_of_samples(50)
        

        self.light = bproc.types.Light()

        self.bin.load(build_convex=False)
        
        for entities in self.components:
            entities.load(build_convex=False, downsample_mesh= False)

    def get_all_comp_objs(self): 
        return sum(list(map(lambda comp: comp.obj_list, self.components)), [])
    
    def get_amount_of_components(self):
        return sum(list(map(lambda comp: len(comp.obj_list), self.components)))
    
    def hide_components(self):
        for comp in self.components:
            for obj in comp.obj_list:
                obj.set_location([1000, 1000, 1000])

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
            
            x, y, z = self.bin.dimensions

            # Calculate a random point of interest
            poi = np.array([np.random.uniform(-0.3*x, 0.3*x), 
                            np.random.uniform(-0.3*y, 0.3*y), 
                            np.random.uniform(-0.1*z, 0.3*z)])

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

    def run(self, scene: Scene):
        
        # set bin location
        for bin in self.bins:
            if bin.name == scene.bin.name:
                bin.from_element(scene.bin.pos[0])
                
        # Find matching components and set their position. 
        for element in scene.comps:
            for comp in self.components:
                if comp.name == element.name:
                    comp.from_element(element.pos)
                    
        # Randomize material for bin
        if self.bin.random_color:
            material = self.randomize_materials()
            self.bin.obj.replace_materials(material)

        # Randomize material for components.
        for comp in self.components:
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
            dataset=self.components[0].name,
            target_objects= all_visible_comp | set([self.bin.obj]),
            colors=data['colors'],
            depths=data['depth'],
            color_file_format="JPEG",
            ignore_dist_thres=50,
            append_to_existing_output=True,
            save_world2cam=True,
            depth_scale=0.01,
        )

        # Hide components
        self.hide_components()

        # Reset sim and restart.
        bproc.utility.reset_keyframes()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--config-path',      nargs='?', default='config.json', help='filepath to configuration JSON file')
    parser.add_argument('--random-bg', action=argparse.BooleanOptionalAction, default=True, help="Add a random background to the skybox from the haven benchmark")
    args = parser.parse_args()

    # Create an instance of the Renderer class
    rend = Render(args)
    
    # Define the relative paths of the directories
    queue_dir = "./resources/simulations/queue/"
    tmp_dir = "./resources/simulations/tmp/"
    complete_dir = "./resources/simulations/complete/"

    try:
        while True:
            print("Looping...")
            files = os.listdir(queue_dir)

            if not files:
                print("No Scenes to render, waiting...")
                time.sleep(10)
            else:
                print("Scene found! Processing...")
                file = random.choice(files)

                # Move the file to the tmp directory
                shutil.move(queue_dir + file, tmp_dir + file)

                # Load the scene from the file
                scene = Scene.load_from_file(tmp_dir + file)

                # Render the scene
                rend.run(scene)

                # Move the file to the complete directory
                shutil.move(tmp_dir + file, complete_dir + file)

    except KeyboardInterrupt:
        print("\n Render stopped by user")
        

