
import os
import json
from typing import TypedDict




bop_path = '/home/hansaskov/Desktop/code/mmdetection/data'
dataset_name = 'icbin'
split = 'train'
split_type = None
coco_filename = "scene_gt_coco.json"

folder_path = bop_path + "/" + dataset_name + "/" + split 
if split_type is not None: folder_path = folder_path + "_" + split_type 
scene_folder_path = folder_path + "/" + "{scene_id:06d}/"

# How many folders exists in folder
folder_amount = len(next(os.walk(folder_path))[1])
if folder_amount <= 1: raise FileNotFoundError("The dataset split folder must container more than 1. folder")

# Load all coco.json files and save it as a dictionary in the dicts variable. 
dicts = []
for i in range(folder_amount):
    scene_folder = scene_folder_path.format(scene_id = i)
    coco_path = scene_folder + coco_filename
    
    with open(coco_path, 'r') as f:
        dicts.append(json.load(f))


# Verify that the constant variables are the same across all dicts an save it to the new dict. 
isInfoEqual =       [dic["info"]        == dicts[0]["info"] for dic in dicts]
isLicensesEqual =   [dic["licenses"]    == dicts[0]["licenses"] for dic in dicts]
isCategoriesEqual = [dic["categories"]  == dicts[0]["categories"] for dic in dicts]

if False in isInfoEqual:        LookupError("Info is not equal for all folders")
if False in isLicensesEqual:    LookupError("License is not equal for all folders")
if False in isCategoriesEqual:  LookupError("Category is not equal for all folders")


#Initialize new dictionary to be saved
new_dict = {
    "info": dicts[0]["info"],
    "license": dicts[0]["licenses"],
    "categories": dicts[0]["categories"],
    "images": [],
    "annotations": [],
}


# 3. 
#   Iterate through all dictionaries 
#       Iterate through images
#           get associated annotations
#           change images:id
#           Change images:file_name
#           Iterate through annotations to image
#               Change annotation:id
#               Change annotation:img_id        

img_id_count = 0
ann_id_count = 0

for scene_id, coco_dict in enumerate(dicts):
    scene_path = "{scene_id:06d}/".format(scene_id = scene_id)
    for image in coco_dict["images"]:
        annotations = list(filter(lambda elem: elem["image_id"] == image["id"], coco_dict["annotations"]))
        image["id"] = img_id_count
        image["file_name"] = scene_path + image["file_name"]
        for ann in annotations: 
            ann["id"] = ann_id_count
            ann["image_id"] = image["id"]
            new_dict["annotations"].append(ann)
            ann_id_count += 1

        new_dict["images"].append(image)
        img_id_count += 1
        if img_id_count % 100 == 2: print("Processing img:", img_id_count)


print("Saving to disk, please wait")
with open(folder_path + "/test.json", "w") as fp:
    json.dump(new_dict,fp, indent=4) 