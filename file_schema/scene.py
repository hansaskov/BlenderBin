import json
import os
from dataclasses import dataclass, asdict
from typing import  List
import hashlib
from dacite import from_dict

@dataclass
class PositionData():
    location: List[float]
    orientation: List[float]
    
@dataclass
class ElementData(): 
    name: str
    pos: List[PositionData]
    
@dataclass
class SceneData():
    config_path: str
    comps: List[ElementData]
    bin: ElementData
        
def save_scene_to_folder(scene: SceneData, folder_path: str):
    
    # Create unique file name        
    d_str = json.dumps(asdict(scene), sort_keys=True).encode('utf-8')
    hash = hashlib.sha1(d_str).hexdigest()
    filename = hash[:8] + ".json"
    
    # Create the folder if it does not exist 
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    file_path = folder_path + "/" + filename
    
    with open(file_path, 'w') as f:
        data = asdict(scene)
        json.dump(data, f, indent=4)
        

def load_scene_from_file(file_path):
    with open(file_path, 'r') as f:
        scene_dict = json.load(f)
        
    return from_dict(data_class=SceneData, data=scene_dict)