import json
from typing import List
import hashlib

from dataclasses import dataclass, asdict


@dataclass    
class Position:
    location: List[float]
    orientation: List[float]

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, dict_obj):
        return cls(**dict_obj)

@dataclass
class Element: 
    name: str
    pos: List[Position]

    def to_dict(self):
       pos_dict = [p.to_dict() for p in self.pos]
       return {
           "name": self.name,
           "pos": pos_dict
       }
       
    @staticmethod
    def from_dict(d: dict):
        return Element(d["name"], [Position.from_dict(p) for p in d["pos"]])

@dataclass
class Scene_file:
    config_path: str
    comps: List[Element]
    bin: Element
        
    def to_dict(self):
        comps_dict = [c.to_dict() for c in self.comps]
        return {
            "config_path" : self.config_path,
            "comps" : comps_dict,
            "bin" : self.bin.to_dict()
        }
        
    @staticmethod
    def from_dict(d: dict):
        config_path = d["config_path"]
        comps_dict = d["comps"]
        bin_dict = d["bin"]
        
        comps = [Element.from_dict(c) for c in comps_dict]
        bin = Element.from_dict(bin_dict)
        return Scene_file(config_path, comps, bin)


    def save_to_folder(self, folder_path):
        scene_dict = self.to_dict()
        
        # Create unique file name        
        d_str = json.dumps(scene_dict, sort_keys=True).encode('utf-8')
        hash = hashlib.sha1(d_str).hexdigest()
        filename = hash[:8] + ".json"
        
        file_path = folder_path + "/" + filename
        
        with open(file_path, 'w') as f:
            json.dump(scene_dict, f, indent=4)
        
    @staticmethod
    def load_from_file(file_path):
        with open(file_path, 'r') as f:
            scene_dict = json.load(f)
        return Scene_file.from_dict(scene_dict)