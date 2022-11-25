# Introduction 
Simulate many objects falling in a bin and create high detailed annotated images.

# Dependencies
Ubuntu >= 18.04 

Pip

Cmake

Python

# Getting Started

1. Install blenderproc to your python env
``` 
git clone https://github.com/DLR-RM/BlenderProc
cd BlenderProc
pip install -e .
```

If you are having problems with BlenderProc please refer to BlenderProc's guide at their github https://github.com/DLR-RM/BlenderProc 

2. Download haven background dataset
```
cd ~DragonFeeding
blenderproc download haven resources/blenderproc/haven
```

1. Install requirements
```
pip install -r requirements.txt
```

# Build and Test
You will need a box or environment 3D model and a 3D model of your component, in .obj format. 
These models will be loaded into the scene and the box will be filled with duplicates of the component. 

The render can be run with the following command:
```
blenderproc run Simulation/render.py --comp-amount-max MAX_COMP_AMOUNT --comp-amount-min MIN_COMP_AMOUNT --comp-number COMP_NUMBER --comp-object PATH_TO_COMP --number-of-runs NUM_RUNS --image-height IMAGE_HEIGHT --image-width IMAGE_WIDTH --bin-object PATH_TO_BIN --bin-length-x BIN_LENGTH_X --bin-length-y BIN_LENGTH_Y --bin-length-z BIN_LENGTH_Z --bop-dataset-name DATASET_NAME
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