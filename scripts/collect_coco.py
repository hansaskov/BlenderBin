import sys
import os
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from file_schema.coco import CocoData
from file_schema.schema_logic import load_schema_from_file, save_schema_to_file

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
    
    # Remove leading separators
    res = res.lstrip(os.sep)
    
    print(res)
    
    return res

def find_non_unique_annotations(annotations):
    seen_ids = set()
    non_unique_annotations = []

    for annotation in annotations:
        if annotation.id in seen_ids:
            non_unique_annotations.append(annotation)
        else:
            seen_ids.add(annotation.id)

    return non_unique_annotations


def merge_coco_datasets(coco_paths, out_coco_filepath):
    coco_data_list = [load_schema_from_file(file_path=coco_path, data_class=CocoData) for coco_path in coco_paths]

    # Initialize counters for new image ids and annotation ids
    img_id_count = 0
    ann_id_count = 0

    # Create a new CocoData object with info, licenses, and categories from the first dataset
    merged_coco_data = CocoData(
        info=coco_data_list[0].info,
        licenses=coco_data_list[0].licenses,
        categories=coco_data_list[0].categories,
        annotations=[],
        images=[],
    )

    # Iterate over each CocoData object (representing a dataset)
    for data_class, path in zip(coco_data_list, coco_paths):
        # Create a dictionary mapping image ids to their related annotations
        image_to_annotations = {image.id: [] for image in data_class.images}
        for ann in data_class.annotations:
            image_to_annotations[ann.image_id].append(ann)

        # Calculate scene path for current data_class
        scene_path = folder_difference(path, out_coco_filepath)

        # Iterate over each image in the dataset
        for image in data_class.images:
            old_image_id = image.id  # Save the old image id
            image.id = img_id_count  # Assign a new, unique image id
            image.file_name = scene_path + "/" + image.file_name  # Update the file name with scene path
            merged_coco_data.images.append(image)  # Add the image to the merged dataset
            img_id_count += 1  # Increment the image id counter

            # Assign new, unique ids to each annotation associated with the current image
            for ann in image_to_annotations[old_image_id]:
                ann.id = ann_id_count  # Assign a new, unique annotation id
                ann.image_id = image.id  # Update the image id in the annotation
                ann.iscrowd = 0  # Ensure that iscrowd is set to 0
                merged_coco_data.annotations.append(ann)  # Add the annotation to the merged dataset
                ann_id_count += 1  # Increment the annotation id counter

    return merged_coco_data




# Define command line arguments
parser = argparse.ArgumentParser(description='Merge COCO datasets and find non-unique annotations.')
parser.add_argument('--folderpath', type=str, help='Path to the folder containing COCO files.')
parser.add_argument('--filename', type=str, default="scene_gt_coco.json" ,help='Name of the COCO file to merge.')
args = parser.parse_args()

# Set the input folder path, input COCO filename, and output COCO file path
in_folder_path = args.folderpath
in_coco_filename = args.filename
out_coco_filepath = in_folder_path + "/" + in_coco_filename

# Search directory for all files with the defined COCO filename and return their filepath
coco_paths = search_files(filename=in_coco_filename, folderpath=in_folder_path, depth=2)
coco_paths.sort()

# Merge the COCO datasets from the input files into a new dataset
new_coco_data = merge_coco_datasets(coco_paths, out_coco_filepath)

# Find annotations with non-unique IDs in the new COCO dataset
non_unique_annotations = find_non_unique_annotations(new_coco_data.annotations)

# Print the IDs of annotations with non-unique IDs
for annotation in non_unique_annotations:
    print(f"Annotation with non-unique id {annotation.id} found.")

# Save the merged dataset to disk
print("Saving to disk, please wait")
save_schema_to_file(data_class=new_coco_data, file_path=out_coco_filepath)

