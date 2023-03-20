from dataclasses import asdict
import hashlib
import json
import os
from typing import Type, TypeVar

from dacite import from_dict
import numpy as np
from file_schema.config import ConfigData
from file_schema.scene import SceneData


T = TypeVar("T")

# How to handle objects for serailization/deserialization. If it is a ndarray convert it to a list
def default(obj):
    if type(obj).__module__ == np.__name__:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj.item()
    raise TypeError('Unknown type:', type(obj))
    
def load_schema_from_file(file_path, data_class: Type[T] ):
    with open(file_path, 'r') as f:
        scene_dict = json.load(f)
    data: data_class = from_dict(data_class=data_class, data=scene_dict) 
    return data

def save_schema_to_file(data: Type[T], file_path: str):
    with open(file_path, 'w') as f:
        dictionary = asdict(data)
        json.dump(dictionary, f, default=default,  indent=4)
    
def save_schema_to_folder(data: ConfigData | SceneData, folder_path: str):
    
    # Create unique file name        
    d_str = json.dumps(asdict(data), default= default, sort_keys=True).encode('utf-8')
    hash = hashlib.sha1(d_str).hexdigest()
    filename = hash[:8] + ".json"
    
    # Create the folder if it does not exist 
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    file_path = folder_path + "/" + filename
    
    with open(file_path, 'w') as f:
        data = asdict(data)
        json.dump(data, f, default=default, indent=4)
        
        
