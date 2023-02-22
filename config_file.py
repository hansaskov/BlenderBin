from dataclasses import dataclass, asdict
from typing import List
import json

@dataclass
class Component_data:
    name: str
    path: str
    obj_id: int
    random_color: bool
    mm_2_m: float

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, dict_obj):
        return cls(**dict_obj)

@dataclass
class Bin_data:
    name: str
    path: str
    random_color: bool
    mm_2_m: float
    dimensions: List[float]

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, dict_obj):
        return cls(**dict_obj)

@dataclass
class Camera_data:
    cx: float
    cy: float
    fx: float 
    fy: float
    height: int 
    width: int 

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, dict_obj):
        return cls(**dict_obj)

@dataclass
class Config_file:
    dataset: str
    components: List[Component_data]
    bins: List[Bin_data]
    camera: Camera_data

    def to_dict(self):
        return {
            'dataset': self.dataset,
            'components': [component.to_dict() for component in self.components],
            'bins': [bin.to_dict() for bin in self.bins],
            'camera': self.camera.to_dict(),
        }

    @classmethod
    def from_dict(cls, dict_obj):
        dataset = dict_obj['dataset']
        components = [Component_data.from_dict(component_dict) for component_dict in dict_obj['components']]
        bins = [Bin_data.from_dict(bin_dict) for bin_dict in dict_obj['bins']]
        camera = Camera_data.from_dict(dict_obj['camera'])
        return cls(dataset, components=components, bins=bins, camera=camera)
    
    #def save_to_file(self, filename):
    #    with open(filename, 'w') as f:
    #        json.dump(self.to_dict(), f)
    
    @classmethod    
    def load_from_file(clc, filename):
        with open(filename, 'r') as f:
            dict_obj = json.load(f)
            return Config_file.from_dict(dict_obj)
