import blenderproc as bproc
from typing import List
import argparse
import numpy as np
import os
import math
import json
import random

from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.types.MaterialUtility import Material

objs = bproc.loader.load_obj('3d_models/comp/coffee_cup.ply')


# set shading
for j, obj in enumerate(objs):
    obj.set_shading_mode('auto')
    obj.set_cp("category_id", 'coffee_cup')
        
# Set light source
light_point = bproc.types.Light()
light_point.set_energy(1000)
light_point.set_location([0, 0, -0.8])

# activate depth rendering
bproc.renderer.enable_depth_output(activate_antialiasing=False)
bproc.renderer.set_max_amount_of_samples(50)

# render the cameras of the current scene
data = bproc.renderer.render()

# Write data to bop format
bproc.writer.write_bop(os.path.join('data', 'bop_data'),
                       depths = data["depth"],
                       colors=data["colors"],
                       save_world2cam=False) # world coords are arbitrary in most real BOP datasets
