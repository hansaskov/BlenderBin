import argparse
import sys

sys.path.append('/home/robotlab/Desktop/HAOV/BlenderBin/resources/bop_toolkit')
import resources.bop_toolkit.scripts.calc_gt_masks as masks
import resources.bop_toolkit.scripts.calc_gt_info as info
import resources.bop_toolkit.scripts.calc_gt_coco as coco
import resources.bop_toolkit.scripts.calc_model_info as model




class DataParams():
    def __init__(self, data_path, name, split, split_type, obj_ids, sym, height, width):
        self.dataset_path = data_path
        self.name = name
        self.split = split
        self.split_type = split_type
        self.obj_ids = obj_ids
        self.sym = sym
        self.height = height
        self.width = width

    def get_object_ids(self):
        ids = []
        objs = self.obj_ids.split(', ')
        for obj in objs:
            ids.append(int(obj))
        return ids

    def get_sym_ids(self):
        if len(self.sym) <= 1: return []
        ids = []
        objs = self.sym.split(', ')
        for obj in objs:
            ids.append(int(obj))
        return ids


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-path',  nargs='?', default='data',                                           help='The full path to the BOP dataset')
    parser.add_argument('--name',       nargs='?', default='lid',                                                      help='Name of the component')
    parser.add_argument('--split',      nargs='?', default='train',                                                     help='Dataset split. Options: "train", "test"')
    parser.add_argument('--split-type', nargs='?', default='pbr',                                                       help='Dataset split type.')
    parser.add_argument('--obj-ids',    nargs='?', default='1, 2',                                                      help='IDs of the objects, in the form: "1, 2" for two objects')
    parser.add_argument('--sym',        nargs='?', default='1',                                                         help='IDs of the objects with symmetries, in the form: "1, 2" for two objects')
    parser.add_argument('--run-num',    nargs='?', default='2',                                                         help='Run "1" first, then run "2". These two programs can\'t run together, and have therefore been seperated. Please hold the rest of the arguments the same.')
    parser.add_argument('--img-height', nargs='?', default='720',                                                       help='Height of input image')
    parser.add_argument('--img-width',  nargs='?', default='540',                                                       help='Width of input image')
   
    args = parser.parse_args()

    par = DataParams(
        args.data_path, 
        args.name, 
        args.split, 
        args.split_type, 
        args.obj_ids, 
        args.sym,
        args.img_height,
        args.img_width
    )

    if int(args.run_num) == 1:
        masks.mask(par)
    elif int(args.run_num) == 2:
        info.info(par)
        coco.coco(par)
        model.model(par)
