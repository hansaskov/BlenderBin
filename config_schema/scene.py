import json
import os
from typing import TypedDict, List
import hashlib

class Position_data(TypedDict):
    location: List[float]
    orientation: List[float]

class Element_data(TypedDict): 
    name: str
    pos: List[Position_data]

class Scene_data(TypedDict):
    config_path: str
    comps: List[Element_data]
    bin: Element_data
        
def save_scene_to_folder(scene: Scene_data, folder_path: str):
    
    # Create unique file name        
    d_str = json.dumps(scene, sort_keys=True).encode('utf-8')
    hash = hashlib.sha1(d_str).hexdigest()
    filename = hash[:8] + ".json"
    
    # Create the folder if it does not exist 
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    file_path = folder_path + "/" + filename
    
    with open(file_path, 'w') as f:
        json.dump(scene, f, indent=4)
    

def load_scene_from_file(file_path):
    with open(file_path, 'r') as f:
        
        scene_dict = json.load(f)
        
    return Scene_data(scene_dict)