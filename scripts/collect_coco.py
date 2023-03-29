

import os
from ..file_schema.coco import CocoData
from ..file_schema.schema_logic import load_schema_from_file, save_schema_to_file

# Recursively searches for a filename in a folder and it's sub folders, up to a 
def search_files(filename, folderpath='.', depth=-1):

    files = []
    for root, dirs, filenames in os.walk(folderpath):
        
        # check if depth limit is reached
        if depth != -1:
            level = root.replace(folderpath, '').count(os.sep)
            if level > depth:
                continue
        
        for file in filenames:
            if file == filename:
                files.append(os.path.join(root, file))
    
    return files


def folder_difference(input_path: str, output_path: str) -> str:
    """
    This function takes two file paths as input and returns the relative
    path difference between the two folders.
    """
    # Get the absolute paths of the input files
    abs_input_path = os.path.abspath(input_path)
    abs_output_path = os.path.abspath(output_path)
    
    # Split the paths into lists of directory names
    split_input_path = abs_input_path.split(os.sep)
    split_output_path = abs_output_path.split(os.sep)
    
    # Remove the filename from the end of each path list
    split_input_path.pop()
    split_output_path.pop()
    
    # Join the path lists back into strings using the path separator
    path1_str = os.sep.join(split_input_path)
    path2_str = os.sep.join(split_output_path)
    
    commonprefix = os.path.commonprefix([path1_str, path2_str])
    
    res = path1_str[len(commonprefix):]
    
    print(res)
    
    return res



in_folder_path = "/home/hansaskov/Desktop/code/mmdetection/data/icbin/test"
in_coco_filename = "scene_gt_coco.json"
out_coco_filepath = "/home/hansaskov/Desktop/code/mmdetection/data/icbin/test/new_coco.json"

# Search directory for all files with the defined coco filename and return their filepath
coco_paths = search_files(filename= in_coco_filename, folderpath=in_folder_path, depth= 2)
coco_paths.sort()

# Load the filepaths to a list on the CocoData format
coco_data_list = [ load_schema_from_file(file_path= coco_path, data_class= CocoData) for coco_path in coco_paths ] 

new_coco_data = CocoData(
    info= coco_data_list[0].info,
    licenses= coco_data_list[0].licenses,
    categories= coco_data_list[0].categories,
    annotations= [],
    images= [],
)

img_id_count = 0
ann_id_count = 0

for data_class, path in zip(coco_data_list, coco_paths):
    scene_path = folder_difference(path, out_coco_filepath )
    for image in data_class.images:
        annotations = list(filter(lambda elem: elem.image_id == image.id, data_class.annotations))
        image.id = img_id_count
        image.file_name = scene_path + "/" + image.file_name
        for ann in annotations: 
            ann.id = ann_id_count
            ann.image_id = image.id
            new_coco_data.annotations.append(ann)
            ann_id_count += 1

        new_coco_data.images.append(image)
        img_id_count += 1
        print("Processing img:", img_id_count)


print("Saving to disk, please wait")
save_schema_to_file(data_class=new_coco_data, file_path=out_coco_filepath)

