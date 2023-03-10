from dataclasses import dataclass
from typing import  List

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