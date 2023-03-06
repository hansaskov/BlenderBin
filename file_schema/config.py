from dataclasses import asdict, dataclass
from typing import List
from dacite import from_dict

import json

@dataclass
class ComponentData():
    name: str
    path: str
    obj_id: int
    random_color: bool
    mm_2_m: float

@dataclass
class BinData():
    name: str
    path: str
    random_color: bool
    mm_2_m: float
    dimensions: List[float]

@dataclass
class CameraData():
    cx: float
    cy: float
    fx: float 
    fy: float
    height: int 
    width: int 
    
@dataclass
class ConfigData():
    dataset_name: str
    components: List[ComponentData]
    bins: List[BinData]
    camera: CameraData

     
def load_config_from_file(file_path: str):
    with open(file_path, 'r') as f:
        dict_obj = json.load(f)
        return from_dict(data_class=ConfigData, data=dict_obj)
    
def save_config_to_file(config: ConfigData, file_path: str):
    with open(file_path, 'w') as f:
        dictionary = asdict(config)
        json.dump(dictionary, f, indent=4)

