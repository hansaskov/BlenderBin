import os
import json
import shutil
import argparse
import open3d as o3d


def save_obj_as_ply(obj_path, save_path, number):
    mesh = o3d.io.read_triangle_mesh(obj_path)
    o3d.io.write_triangle_mesh(save_path + "obj_" + str(number).zfill(6) + '.ply', mesh, write_ascii=True)


def get_current_folder(lid_path):
    # Know which number folder we are at in for the component
    number_of_img_folders = 0
    if os.path.exists(lid_path + '/train_pbr/'):
        for root, dirs, files in os.walk(lid_path + '/train_pbr/'):
            for dir in dirs:
                if '0' in dir:
                    number_of_img_folders = number_of_img_folders + 1
                    folder_name = str(number_of_img_folders - 1).zfill(6)
                    img_path = lid_path + '/train_pbr/' + folder_name
        return img_path
    else: 
        os.makedirs(lid_path + '/train_pbr/000000/rgb')
        os.makedirs(lid_path + '/train_pbr/000000/depth')
        return lid_path + '/train_pbr/000000'


def get_next_current_images(img_path):
    # Know the amount of images we have in the folder
    number_of_files = 0
    for root, dirs, files in os.walk(img_path + '/rgb/'):
        for file in files:
            number_of_files = number_of_files + 1
    return number_of_files


def get_folders(name, obj_path, box_path):
    cwd = os.getcwd()
    path = cwd + '/data/'
    out_path = path + name
    camera_path = out_path + '/camera.json'
    # Check if the camera.json file already exists in the collected folder
    camera_exists = os.path.isfile(camera_path)

    # If there is no collected directory, create a new one
    if not os.path.exists(out_path):
        print(out_path)
        os.makedirs(out_path + '/models/')
        # Save ply from object files
        save_obj_as_ply(obj_path, out_path + '/models/', 1) 
        save_obj_as_ply(box_path, out_path + '/models/', 2)  
        # Move obj and mtl from 3D models  
        shutil.copy(obj_path, out_path + '/models/obj_' + '1'.zfill(6) + '.obj')
        shutil.copy(box_path, out_path + '/models/obj_' + '2'.zfill(6) + '.obj')
        obj_mtl_path = obj_path[:-4] + '.mtl' 
        obj_mtl_path = box_path[:-4] + '.mtl'
        if os.path.exists(obj_path[:-4] + '.mtl'):
            shutil.copy(obj_mtl_path, out_path + '/models/' + name + '.mtl')
        if os.path.exists(box_path[:-4] + '.mtl'):
            shutil.copy(obj_mtl_path, out_path + '/models/' + box_path[:-4].split('/')[-1] + '.mtl')
    
    img_path = get_current_folder(out_path)

    number_of_files = get_next_current_images(img_path)
    if number_of_files >= 1000:
        number_of_files = 0
        img_path = img_path[:-6] + str(int(img_path[-6:]) + 1).zfill(6)
        os.makedirs(img_path + '/rgb')
        os.makedirs(img_path + '/depth')

    try:
        main_scene_camera = json.load(open(img_path + '/scene_camera.json'))
        main_scene_gt = json.load(open(img_path + '/scene_gt.json'))     
    except:
        main_scene_camera = {}
        main_scene_gt = {}

    
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            if name in dir and name != dir:
                comp_path = path + dir + '/train_pbr/'
                # Make sure the component folder has the camera.json file
                if not camera_exists:
                    shutil.move(path + dir + '/camera.json', camera_path)
                    camera_exists = True
                    print('camera.json moved')
                for comp_root, comp_dirs, comp_files in os.walk(comp_path):
                    for comp_dir in comp_dirs:
                        for comp_root_fol, comp_dirs_fol, comp_files_fol in os.walk(comp_path + '/' + comp_dir):
                            # Inside the 0 folder
                            scene_camera = json.load(open(comp_path + '/' + comp_dir + '/scene_camera.json'))
                            scene_gt = json.load(open(comp_path + '/' + comp_dir + '/scene_gt.json'))
                            for comp_root_fol_rgb, comp_dirs_fol_rgb, comp_files_fol_rgb in os.walk(comp_path + '/' + comp_dir + '/rgb/'):
                                # Inside the RGB folder
                                for fil in comp_files_fol_rgb:
                                    num = fil[:-4]
                                    shutil.move(comp_path + '/' + comp_dir + '/rgb/' + num + '.jpg', img_path + '/rgb/' + str(number_of_files).zfill(6) + '.jpg')
                                    shutil.move(comp_path + '/' + comp_dir + '/depth/' + num + '.png', img_path + '/depth/' + str(number_of_files).zfill(6) + '.png')
                                    sc_c = scene_camera[str(int(num))]
                                    sc_gt = scene_gt[str(int(num))]
                                    main_scene_camera.update({str(len(main_scene_camera)): sc_c})
                                    main_scene_gt.update({str(len(main_scene_gt)): sc_gt})
                                    number_of_files = number_of_files + 1
                                    if number_of_files >= 1000:
                                        # Save the json files
                                        with open(img_path + '/scene_camera.json', 'w') as outfile:
                                            json.dump(main_scene_camera, outfile, indent=2)
                                        with open(img_path + '/scene_gt.json', 'w') as outfile:
                                            json.dump(main_scene_gt, outfile, indent=2)
                                        number_of_files = 0
                                        main_scene_camera = {}
                                        main_scene_gt = {}
                                        img_path = img_path[:-6] + str(int(img_path[-6:]) + 1).zfill(6)
                                        os.makedirs(img_path + '/rgb')
                                        os.makedirs(img_path + '/depth')
                            shutil.rmtree(comp_path + '/' + comp_dir)
                    shutil.rmtree(path + dir)
        # Save the json files
        with open(img_path + '/scene_camera.json', 'w') as outfile:
            json.dump(main_scene_camera, outfile, indent=2)
        with open(img_path + '/scene_gt.json', 'w') as outfile:
            json.dump(main_scene_gt, outfile, indent=2)
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', nargs='?', default='lid', help='Name of the component')
    parser.add_argument('--obj',  nargs='?', default='/home/robotlab/Desktop/HAOV/DragonFeeding/3D_model/lid.obj', help='Path to the component object file')
    parser.add_argument('--box',  nargs='?', default='3d_models/bins/DragonBoxEnvironment.obj', help='Path to the box object file')
    args = parser.parse_args()
    get_folders(name=args.dataset, obj_path=args.obj, box_path=args.box)
