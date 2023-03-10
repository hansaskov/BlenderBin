from dataclasses import asdict
import hashlib
import json
import os

from dacite import from_dict
from file_schema.config import ConfigData
from file_schema.scene import SceneData


def save_schema_to_file(data: ConfigData | SceneData, file_path: str):
    with open(file_path, 'w') as f:
        dictionary = asdict(data)
        json.dump(dictionary, f, indent=4)
        
def load_schema_from_file(file_path, data_class: ConfigData | SceneData):
    with open(file_path, 'r') as f:
        scene_dict = json.load(f)
    return from_dict(data_class=data_class, data=scene_dict)

def save_schema_to_folder(data: ConfigData | SceneData, folder_path: str):
    
    # Create unique file name        
    d_str = json.dumps(asdict(data), sort_keys=True).encode('utf-8')
    hash = hashlib.sha1(d_str).hexdigest()
    filename = hash[:8] + ".json"
    
    # Create the folder if it does not exist 
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    file_path = folder_path + "/" + filename
    
    with open(file_path, 'w') as f:
        data = asdict(data)
        json.dump(data, f, indent=4)