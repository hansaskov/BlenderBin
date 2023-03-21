from dataclasses import dataclass
from typing import List


@dataclass
class ComponentData():
    name: str
    path: str
    obj_id: int
    random_color: bool
    random_texture: bool
    mm_2_m: float

@dataclass
class BinData():
    name: str
    path: str
    random_color: bool
    random_texture: bool
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
