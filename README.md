# Introduction 
Simulate many objects falling in a bin and create high detailed annotated images.

# Dependencies
Ubuntu >= 18.04 

Pip

Cmake

# Getting Started

Install dependencies
``` 
pip install .
```


For bin_render.py Download haven background dataset into the resource folder.
```
blenderproc download haven resources/blenderproc/haven
```

# Build and Test
You will need a box or environment 3D model and a 3D model of your component, in .obj format. 
These models will be loaded into the scene and the box will be filled with duplicates of the component. 

The render can be run with the following command:
```
blenderproc run bin_render.py \
--comp-amount-max 10 \
--comp-amount-min 1 \
--number-of-runs 10 \
--instance-num 1 \
--width 720 \
--height 540 \
--comp-path 3d_models/comp/ape.obj \
--bin-path 3d_models/bins/DragonBoxEnvironment.obj \
--comp-rand-color 1 \
--bin-rand-color 1  \
--bin-length-x 176 \
--bin-length-y 156 \
--bin-length-z 100 
```

MAX_COMP_AMOUNT is the maximum number of components that can/should be in the bin. 

MIN_COMP_AMOUNT is the minimum number of components that should be in the bin.

COMP_NUMBER is a number for the component. If you're using more than one component in your simulations, we suggest that you use a different number for different components.

PATH_TO_COMP is the path to the components .obj or .ply file.

NUM_RUNS is the amount of iterations you want to do. Each iteration generates between two to four images.

IMAGE_HEIGHT is the number of pixels in the image's y axis.

IMAGE_WIDTH is the number of pixels in the image's x axis.

PATH_TO_BIN is the path to the bin or environment's .obj or .ply file.

BIN_LENGTH_X is the bin's length in the x axis.

BIN_LENGTH_Y is the bin's length in the y axis.

BIN_LENGTH_Z is the bin's length in the z axis.

DATASET_NAME is the desired name for your BOP dataset


Side note: If you're going to run multiple simulations with the same bin and/or the same components, we recommend going into the Simulation/render.py file and add your arguments as the default arguments in order to save you time in the future.