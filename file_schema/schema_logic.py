from dataclasses import asdict
import hashlib
import json
import os
from typing import Type, TypeVar
import glob

from dacite import from_dict
import numpy as np
from file_schema.config import ConfigData
from file_schema.scene import SceneData


T = TypeVar("T")

def get_json_files_from_folder(folder_path: str): 
    json_files = glob.glob(os.path.join(folder_path, "*.json"))
    return json_files

def get_subdirectories(folder_path: str):
    subdirectories = glob.glob(os.path.join(folder_path, "*/"))
    return subdirectories

def get_folder_name(folder_path: str):
    folder_name = os.path.basename(os.path.normpath(folder_path))
    return folder_name

# How to handle objects for serailization/deserialization. If it is a ndarray convert it to a list
def default(obj):
    if type(obj).__module__ == np.__name__:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj.item()
    raise TypeError('Unknown type:', type(obj))
    
# Convert dataclass to a hash
def hash_data_class(data_class: Type[T]):
    # Convert dataclass to bytes
    d_str = json.dumps(asdict(data_class), default= default, sort_keys=True).encode('utf-8')
    # Hash the bytes and return as string of hexdecimal digits
    hash = hashlib.sha1(d_str).hexdigest()
    
    return hash


def save_schema_to_file(data_class: Type[T], file_path: str):
    with open(file_path, 'w') as f:
        dictionary = asdict(data_class)
        json.dump(dictionary, f, default=default,  indent=4)
    
def load_schema_from_file(file_path: str, data_class: Type[T] ):
    with open(file_path, 'r') as f:
        scene_dict = json.load(f)
    data: data_class = from_dict(data_class=data_class, data=scene_dict) 
    return data

def save_schema_to_folder(data_class: Type[T], folder_path: str):
    
    hash = hash_data_class(data_class)
    filename = hash[:8] + ".json"
    
    # Create the folder if it does not exist 
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    file_path = folder_path + "/" + filename
    
    with open(file_path, 'w') as f:
        data_class = asdict(data_class)
        json.dump(data_class, f, default=default, indent=4)
        
def save_scene(scene: SceneData, config: ConfigData, folder_path: str): 
    
    # Hash Config file
    config_hash = hash_data_class(data_class= config)
    
    # Create name of config
    config_name = "/config_" +  config_hash[:6]
    
    # Create path for config file
    folder_path = folder_path + config_name
       
    # Create subfolders if it does not exist
    for dir in ["/complete/", "/queue/", "/tmp/"]:
        if not os.path.exists(folder_path + dir):
            os.makedirs(folder_path + dir)
    
    # Save SceneData to folder_path/queue
    queue_folder_path = folder_path + "/queue"
    save_schema_to_folder(scene, queue_folder_path)
    
    # Save config to our new folder if it does not exist
    config_file_path = folder_path + "/" + config_name + ".json"
    if not os.path.exists(config_file_path):
        save_schema_to_file(config, config_file_path)
    
def get_next_sim_folder(folder_path: str):
    config_folders = get_subdirectories(folder_path= folder_path)
    
    if not config_folders:
        return None
    
    return config_folders[0]

def load_config_from_folder(folder_path: str):
    folder_name = get_folder_name(folder_path)
    config_name = folder_name + ".json"
    config_path = os.path.join(folder_path, config_name)

    json_files = get_json_files_from_folder(folder_path)

    if not config_path in json_files:
        raise FileNotFoundError(f"Configuration file '{config_name}' not found in folder '{folder_path}'")

    return load_schema_from_file(data_class=ConfigData, file_path=config_path)

    
    
    
    
    
    
    
    
    


    
