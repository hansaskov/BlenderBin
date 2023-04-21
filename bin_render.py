import blenderproc as bproc
import sys
import os
from blenderproc.python.camera.CameraUtility import bpy
from blenderproc.python.types.MeshObjectUtility import MeshObject

myDir = os.getcwd()
sys.path.append(myDir)

from file_schema.scene import PositionData, SceneData
from file_schema.config import ConfigData
from file_schema.schema_logic import get_next_sim_folder, load_config_from_folder, load_schema_from_file, save_schema_to_folder
from entities.component import Component
from entities.bin import Bin
from typing import List

import math
import colorsys
import argparse
import numpy as np

import time
import shutil
from enum import Enum


haven_path = "resources/haven"
output_dir = "data"

class Render:
                           
    def __init__(self, config_data: ConfigData, use_metadata: bool):
        bproc.init()
        self.use_metadata = use_metadata
        self.config_data = config_data
        self.camera = config_data.camera
        self.components = [ Component(comp_data) for comp_data in config_data.components ] 
        self.bins = [Bin(bin_data) for bin_data in config_data.bins ]
        self.bin = self.bins[0]

        K = [
            [self.camera.fx, 0, self.camera.cx],
            [0, self.camera.fy, self.camera.cy],
            [0, 0, 1]
        ]
        
        self.light = bproc.types.Light()


        # Collect all texture images 
        self.texure_images = []
        textures_path = 'resources/haven/textures'
        for subdir, dirs, files in os.walk(textures_path):
            for file in files:
                self.texure_images.append(os.path.join(subdir, file))
        
        self.bin.load(build_convex=False)
        
        for entities in self.components:
            entities.load(build_convex=False, downsample_mesh=False)
            
        bproc.camera.set_intrinsics_from_K_matrix(K=K, image_height=self.camera.height, image_width=self.camera.width)
        bproc.renderer.enable_depth_output(activate_antialiasing=False)
        bproc.renderer.set_max_amount_of_samples(50)

    def get_all_comp_objs(self): 
        return sum([comp.obj_list for comp in self.components], [])
    
    def get_amount_of_components(self):
        return sum([len(comp.obj_list) for comp in self.components])
    
    def randomize_light(self):
        # Randomize light source
        light_type = np.random.choice(["POINT", "SUN", "SPOT", "AREA"])
        self.light.set_type(light_type)

        # Move the light
        self.light.set_location(np.random.uniform([-1, -1, 5], [1, 1, 20]))
        self.light.set_rotation_euler(np.random.uniform([-0.5, -0.5, -0.5], [0.5, 0.5, 61]))
        self.light.set_color([1, 1, 1])
        self.light.set_energy(np.random.uniform(0.5, 1))

    def randomize_materials(self, random_texture):
        # Make a random material
        material = bproc.material.create('RandomMat')
        
        if random_texture:
            # Assign a random texture
            image = bpy.data.images.load(filepath=str(np.random.choice(self.texure_images)))
            material.set_principled_shader_value("Base Color", image)
        else:
            # Assign a random color
            h, l, s = np.random.uniform(0.1, 0.9, 3)
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            material.set_principled_shader_value("Base Color", [r, g, b, 1])

        material.set_principled_shader_value("Roughness", np.random.uniform(1, 10.0))
        material.set_principled_shader_value("Specular", np.random.uniform(0, 1))
        material.set_principled_shader_value("Metallic", np.random.uniform(0, .2))

        return material

    def calculate_camera_pose(self, bin_dimensions: List[float]):
        x, y, z = bin_dimensions

        # Calculate a random point of interest
        poi = np.array([np.random.uniform(-0.3 * x, 0.3 * x),
                        np.random.uniform(-0.3 * y, 0.3 * y),
                        np.random.uniform(-0.1 * z, 0.3 * z)])

        # Sample random location
        location = bproc.sampler.shell(
            center=[0, 0, self.camera.positioning.height],
            radius_min=self.camera.positioning.radius_min,
            radius_max=self.camera.positioning.radius_max,
            elevation_min=self.camera.positioning.angle_min,
            elevation_max=self.camera.positioning.angle_max,
            uniform_volume=True
        )

        # Calculate rotation towards point of interest
        rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location, inplane_rot=np.random.uniform(-0.7854, 0.7854))

        # Make transformation matrix from location (x, y, z) and rotation matrix
        cam2world = bproc.math.build_transformation_mat(location, rotation_matrix)

        return cam2world
    
    def get_visible_components_from_camera(self, cam2world):

        # Compute raycasting to only show visible objects
        sqrt_rays = round(math.sqrt(self.camera.height * self.camera.width) / 4)
        obj_visible = bproc.camera.visible_objects(cam2world, sqrt_rays)

        # Filter visible components
        all_comps = set(self.get_all_comp_objs())
        comp_visible = obj_visible.intersection(all_comps)
        
        return comp_visible

    def run(self, scene: SceneData, random_background = True, img_amount = 4, random_camera_positions = True) -> List[PositionData]:
        
        # Set bin location
        for bin in self.bins:
            if bin.name == scene.bin.name:
                bin.from_element(scene.bin.pos[0])
                
        # Find matching components and set their position. 
        for element in scene.comps:
            for comp in self.components:
                if comp.name == element.name:
                    comp.from_element(element.pos)
                    
        # Randomize material for bin
        if self.bin.random_color or self.bin.random_texture:
            material = self.randomize_materials(self.bin.random_texture)
            self.bin.obj.replace_materials(material)

        # Randomize material for components.
        for comp in self.components:
            if comp.random_color or comp.random_texture:
                material = self.randomize_materials(comp.random_texture)
                for comp in comp.obj_list:
                    comp.replace_materials(material)
                    
        # Randomize lighting
        self.randomize_light()    
                
        # Set a random background
        if random_background: 
            haven_hdri_path = bproc.loader.get_random_world_background_hdr_img_path_from_haven(haven_path)
            bproc.world.set_world_background_hdr_img(haven_hdri_path)

        # Randomize camera positions
        if not scene.cameras or random_camera_positions:
            scene.cameras = [self.calculate_camera_pose(self.bin.dimensions) for i in range(img_amount) ]
        
        # Render the scene for each camera viewpoint and save it in the bop format
        all_visible_comp: set[MeshObject] = set()
        
        for cam2world in scene.cameras:
            bproc.camera.add_camera_pose(cam2world)
            visible_comps = self.get_visible_components_from_camera(cam2world)
            all_visible_comp = all_visible_comp.union(visible_comps)
            
        # Render Pipeline
        data = bproc.renderer.render()
        
        bproc.writer.write_bop(
            output_dir=os.path.join(output_dir),
            dataset=self.config_data.dataset_name,
            target_objects=  all_visible_comp,
            colors=data['colors'],
            depths=data['depth'],
            color_file_format="JPEG",
            append_to_existing_output=True,
            save_world2cam=True,
            depth_scale=0.1, 
            calc_mask_info_coco= self.use_metadata
            )
        
        # Reset keyframe and restart.
        bproc.utility.reset_keyframes()
        
        # Reset location. 
        for obj in self.get_all_comp_objs():
            obj.set_location([1000,1000,100])


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--sim-path',      nargs='?', default='./resources/simulations', help='path the the directory with the simulations')
    parser.add_argument('--img-amount', nargs='?', default=4, help="Amount of images per scene")
    parser.add_argument('--random-cam', action=argparse.BooleanOptionalAction, default=True, help="Use the previous camera positions")
    parser.add_argument('--random-bg', action=argparse.BooleanOptionalAction, default=True, help="Add a random background to the skybox from the haven benchmark")
    parser.add_argument('--metadata', action=argparse.BooleanOptionalAction, default=True, help="Calculate masks, info and coco annotations")

    args = parser.parse_args()

    simulation_path = args.sim_path
    use_metadata = args.metadata
    
    folder_path = get_next_sim_folder(folder_path= simulation_path)
    
    config = load_config_from_folder(folder_path)
    # Create an instance of the Renderer class
    rend = Render(config_data=config, use_metadata= use_metadata)

    complete_dir = folder_path + "/complete/"
    queue_dir = folder_path + "/queue/"
    tmp_dir = folder_path + "/tmp/"

    i = 0
    try:
        while i < 6:
            files = os.listdir(queue_dir)

            if not files:
                print("No Scenes to render, waiting...")
                i = i + 1
                time.sleep(5)
            else:
                print("Scene found! Processing...")
                file = files[0]

                # Move the file to the tmp directory
                shutil.move(queue_dir + file, tmp_dir + file)

                # Load the scene from the file
                scene = load_schema_from_file(file_path= tmp_dir + file, data_class=SceneData)

                # Render the scene
                rend.run(scene, img_amount= int(args.img_amount), random_background= args.random_bg, random_camera_positions = args.random_cam)
                
                # Save scene to complete folder (with new camera positions)
                save_schema_to_folder(scene, complete_dir)
                
                # Remove file from tmp dir
                os.remove(path= tmp_dir + file)
                
                i = 0

        print("Timeout, no new scenes to render for 30 seconds")

    except KeyboardInterrupt:
        print("\n Render stopped by user")
        

