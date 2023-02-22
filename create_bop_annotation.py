import argparse
import sys
import os

myDir = os.getcwd()
sys.path.append(myDir)

import resources.bop_toolkit.scripts.calc_gt_masks as masks
import resources.bop_toolkit.scripts.calc_gt_info as info
import resources.bop_toolkit.scripts.calc_gt_coco as coco
import resources.bop_toolkit.scripts.calc_model_info as model

from config_file import Config_file

import open3d as o3d

def save_obj_as_ply(obj_path, save_folder, number):
    mesh = o3d.io.read_triangle_mesh(obj_path)
    o3d.io.write_triangle_mesh(save_folder + "obj_" + str(number).zfill(6) + '.ply', mesh, write_ascii=True)

class DataParams():
    def __init__(self, data_path, name, split, split_type, obj_ids, sym_ids, height, width):
        self.dataset_path = data_path
        self.name = name
        self.split = split
        self.split_type = split_type
        self.obj_ids = obj_ids
        self.sym_ids = sym_ids
        self.height = height
        self.width = width


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',  nargs='?', default='./config.json', help='The full path to the config file')
    parser.add_argument('--scripts', help="Which script do you want to complete?, choose from \'mask\' \'info\' \'coco\' \'model\' or do more than one by seperating the input by a comma: \'mask, coco\' ")
    args = parser.parse_args()
    
    
    
    config = Config_file.load_from_file(args.config)
    
    dir = "./data/" + config.dataset + "/models/"
    if not os.path.exists(dir):
            os.makedirs(dir)
            for comp in config.components:
                save_obj_as_ply(obj_path= comp.path, save_folder= dir, number=comp.obj_id)
    
    
    
    par = DataParams(
        data_path=  "data",
        name=       config.dataset,
        split=      "train",
        split_type= "pbr",
        obj_ids=    [comp.obj_id for comp in config.components],
        sym_ids=        "",
        height=     config.camera.height,
        width=      config.camera.width  
    )
    
    input = str(args.scripts)
    scripts = input.split(',')
    scripts = list(map(lambda s: s.strip(), scripts))
    print(scripts)
    
    
    if 'mask' in scripts:
        masks.mask(par)
        
    if 'info' in scripts:
        info.info(par)
        
    if 'coco' in scripts:
        coco.coco(par)
        
    if 'model' in scripts:
        model.model(par)
