import blenderproc as bproc
import colorsys
import argparse
import os
import numpy as np

from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.types.MaterialUtility import Material

bproc.init()

bop_parent_path = "3d_models/bop"
cc_textures_path = "resources/blenderproc/cctextures"
comp_path = "/home/robotlab/Desktop/HAOV/DragonFeeding/3D_model/lid.obj"
dataset_name = "lid_1"
min_comp_amount = 10
max_comp_amount = 50
number_of_runs = 125
resolution = (720, 540)



def sample_pose_func(obj: bproc.types.MeshObject):
        min = np.random.uniform([-0.3, -0.3, 0.0], [-0.2, -0.2, 0.0])
        max = np.random.uniform([0.2, 0.2, 0.4], [0.3, 0.3, 0.6])
        obj.set_location(np.random.uniform(min, max))
        obj.set_rotation_euler(bproc.sampler.uniformSO3())


def comp_load(): 
    comp = bproc.loader.load_obj(comp_path)[0]
    comp.set_scale( [1/1000, 1/1000, 1/1000])
    comp.enable_rigidbody(True, friction = 100.0, linear_damping = 0.99, angular_damping = 0.99)
    comp.set_shading_mode('auto')
    comp.set_cp("category_id", 1)
    comp.set_cp("bop_dataset_name", dataset_name) 
    return comp     

def increase_dublicates(amount: int, obj: MeshObject, obj_list: "list[MeshObject]" ):
    for i in range(amount - len(obj_list)):
        obj_list.append(obj.duplicate())

def distractor_load(): 
    # set shading and physics properties and randomize PBR materials
    distractor_bop_objs = bproc.loader.load_bop_objs(bop_dataset_path = os.path.join(bop_parent_path, 'tless'),
                                        model_type = 'cad',
                                        mm2m = True,
                                        sample_objects = True,
                                        num_of_objs_to_sample = 5)
    distractor_bop_objs += bproc.loader.load_bop_objs(bop_dataset_path = os.path.join(bop_parent_path, 'lmo'),
                                        mm2m = True,
                                        sample_objects = True,
                                        num_of_objs_to_sample = 3,
                                        obj_instances_limit = 5)

    for j, obj in enumerate(distractor_bop_objs):
        obj.enable_rigidbody(True, friction = 100.0, linear_damping = 0.99, angular_damping = 0.99)
        obj.set_shading_mode('auto')
        
        gray = obj.get_cp("bop_dataset_name") in ['itodd', 'tless']
        mat = obj.get_materials()[0]

        randomize_materials(mat, gray= gray)    

    return distractor_bop_objs


def create_room():
    room_planes = [bproc.object.create_primitive('PLANE', scale=[2, 2, 1]),
               bproc.object.create_primitive('PLANE', scale=[2, 2, 1], location=[0, -2, 2], rotation=[-1.570796, 0, 0]),
               bproc.object.create_primitive('PLANE', scale=[2, 2, 1], location=[0, 2, 2], rotation=[1.570796, 0, 0]),
               bproc.object.create_primitive('PLANE', scale=[2, 2, 1], location=[2, 0, 2], rotation=[0, -1.570796, 0]),
               bproc.object.create_primitive('PLANE', scale=[2, 2, 1], location=[-2, 0, 2], rotation=[0, 1.570796, 0])]

    for plane in room_planes:
        plane.enable_rigidbody(False, collision_shape='BOX', friction = 100.0, linear_damping = 0.99, angular_damping = 0.99)

    return room_planes

def randomize_materials(material: Material,rgb = False, gray = False):

    if gray:
        v = np.random.uniform(0.1, 0.9) 
        material.set_principled_shader_value("Base Color", [v, v, v, 1])

    if rgb:
        h, s, v = np.random.rand(3)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        material.set_principled_shader_value("Base Color", [r, g, b, 1])
    
    material.set_principled_shader_value("Roughness", np.random.uniform(1, 10.0))
    material.set_principled_shader_value("Specular", np.random.uniform(0, 1))
    material.set_principled_shader_value("Metallic", np.random.uniform(0, .2))


def set_material(obj: MeshObject, material: Material):
    for index in range(len(obj.get_materials())):
            obj.set_material(index, material)


def sample_camera_pose(amount: int):
        # BVH tree used for camera obstacle checks
    bop_bvh_tree = bproc.object.create_bvh_tree_multi_objects(comp_obj_list + distractor_bop_objs)

    poses = 0
    while poses < amount:
        # Sample location
        location = bproc.sampler.shell(center = [0, 0, 0],
                                radius_min = 0.61,
                                radius_max = 1.24,
                                elevation_min = 5,
                                elevation_max = 89,
                                uniform_volume = False)
        # Determine point of interest in scene as the object closest to the mean of a subset of objects
        poi = bproc.object.compute_poi(np.random.choice(comp_obj_list, size=10))
        # Compute rotation based on vector going from location towards poi
        rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location, inplane_rot=np.random.uniform(-0.7854, 0.7854))
        # Add homog cam pose based on location an rotation
        cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
        # Check that obstacles are at least 0.3 meter away from the camera and make sure the view interesting enough
        if bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, {"min": 0.3}, bop_bvh_tree):
            # Persist camera pose
            bproc.camera.add_camera_pose(cam2world_matrix)
            poses += 1



####################### Begin ############################3

bproc.renderer.enable_depth_output(activate_antialiasing=False)
bproc.renderer.set_max_amount_of_samples(50)
bproc.camera.set_resolution(resolution[0], resolution[1])

comp_obj = comp_load()
comp_obj_list = [comp_obj]

distractor_bop_objs = distractor_load()

room_planes = create_room()

cc_textures = bproc.loader.load_ccmaterials(cc_textures_path)

# sample point light on shell
light_point = bproc.types.Light()
light_point.set_energy(200)

# sample light color and strenght from ceiling
light_plane = bproc.object.create_primitive('PLANE', scale=[3, 3, 1], location=[0, 0, 10])
light_plane.set_name('light_plane')
light_plane_material = bproc.material.create('light_material')

comp_amount_list =  np.random.randint(low=min_comp_amount, high=max_comp_amount, size=number_of_runs)
comp_amount_list.sort()

for amount in comp_amount_list:

    increase_dublicates(amount, comp_obj, comp_obj_list)

    # Randomize spot light
    light_point.set_color(np.random.uniform([0.5,0.5,0.5],[1,1,1]))
    location = bproc.sampler.shell(center = [0, 0, 0], radius_min = 1, radius_max = 1.5, elevation_min = 5, elevation_max = 89, uniform_volume = False)
    light_point.set_location(location)

    # Randomize overhead light
    light_plane_material.make_emissive(emission_strength=np.random.uniform(3,6),  emission_color=np.random.uniform([0.5, 0.5, 0.5, 1.0], [1.0, 1.0, 1.0, 1.0]))    
    light_plane.replace_materials(light_plane_material)

    # sample CC Texture and assign to room planes
    random_cc_texture = np.random.choice(cc_textures)
    for plane in room_planes:
        plane.replace_materials(random_cc_texture)

    # Randomize component materials
    mat = comp_obj.get_materials()[0]
    randomize_materials(mat, rgb=True)
    for comp in comp_obj_list: 
        set_material(comp, mat)

    # Sample object poses and check collisions 
    bproc.object.sample_poses(objects_to_sample = comp_obj_list + distractor_bop_objs,
                            sample_pose_func = sample_pose_func, 
                            max_tries = 1000)
            
    # Physics Positioning
    bproc.object.simulate_physics_and_fix_final_poses(min_simulation_time=3,
                                                    max_simulation_time=10,
                                                    check_object_interval=1,
                                                    substeps_per_frame = 20,
                                                    solver_iters=25)
    sample_camera_pose(4)

    # render the whole pipeline
    data = bproc.renderer.render()

    # Write data in bop format
    bproc.writer.write_bop(
                        output_dir='data/',
                        dataset = dataset_name ,
                    # target_objects = sampled_bop_objs,
                        colors=data['colors'],
                        depths=data['depth'],
                        color_file_format = "JPEG",
                        ignore_dist_thres = 20,
                        append_to_existing_output=True,
                        save_world2cam=True)

    # Reset sim and restart. 
    bproc.utility.reset_keyframes()