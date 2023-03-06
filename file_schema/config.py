from typing import List, TypedDict
import json

class Component_data(TypedDict):
    name: str
    path: str
    obj_id: int
    random_color: bool
    mm_2_m: float

class Bin_data(TypedDict):
    name: str
    path: str
    random_color: bool
    mm_2_m: float
    dimensions: List[float]

class Camera_data(TypedDict):
    cx: float
    cy: float
    fx: float 
    fy: float
    height: int 
    width: int 

class Config_data(TypedDict):
    dataset_name: str
    components: List[Component_data]
    bins: List[Bin_data]
    camera: Camera_data

     
def load_config_from_file(filename):
    with open(filename, 'r') as f:
        dict_obj = json.load(f)
        return Config_data(dict_obj)
