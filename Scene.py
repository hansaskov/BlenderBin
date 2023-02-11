import json
from typing import List
import hashlib

# location and orientation are 3d vectors representing x,y,z and rx, ry, rz respectively
class Position:
    def __init__(self, location: List[float], orientation: List[float]):
        self.location = location
        self.orientation = orientation
        
    def to_dict(self):
        return {
            "location": self.location,
            "orientation": self.orientation
        }

    @staticmethod
    def from_dict(d: dict):
        return Position(d["location"], d["orientation"])

class Element:
   def __init__(self, name: str, pos: List[Position]):
       self.name = name
       self.pos = pos
       
   def to_dict(self):
       pos_dict = [p.to_dict() for p in self.pos]
       return {
           "name": self.name,
           "pos": pos_dict
       }
   @staticmethod
   def from_dict(d: dict):
        return Element(d["name"], [Position.from_dict(p) for p in d["pos"]])

class Scene: 
    def __init__(self, config_path: str, comps: List[Element], bin: Element):
        self.config_path = config_path
        self.comps = comps
        self.bin = bin
        
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
        return Scene(config_path, comps, bin)
    
    def save_to_folder(self, folder_path):
        d = self.to_dict()
        
        # Create unique file name        
        d_str = json.dumps(d, sort_keys=True).encode('utf-8')
        hash = hashlib.sha1(d_str).hexdigest()
        filename = hash[:8] + ".json"
        
        file_path = folder_path + "/" + filename
        
        with open(file_path, 'w') as f:
            json.dump(d, f, indent=4)

def load_from_file(file_path):
    with open(file_path, 'r') as f:
        scene_dict = json.load(f)
    return Scene.from_dict(scene_dict)