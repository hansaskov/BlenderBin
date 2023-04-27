

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/hansaskov/BlenderBin/blob/master/examples/colab.ipynb)
# BlenderBin

Simulate objects falling in a bin and create your synthetic dataset with perfectly annotated images.
<p align="center">
  <img  src="images/Coco-annotations.PNG">
</p>

# Installation

To use the BlenderBin repository, a Linux-based operating system is required. The repository has been tested on Ubuntu 18.04 and 22.04. Additionally, CMake must be installed.

To begin, download the repository:

```bash
git clone --recurse-submodules https://github.com/hansaskov/BlenderBin
cd ./BlenderBin
```

Next, install the necessary dependencies
First dependencies related to BlenderProc

```bash
pip install -e BlenderProc
```
Then we will inject extra dependencies to the BlenderProc environment
```bash
blenderproc pip install GitPython dacite open3d
```

To run the rendering with random background or a random texture download the haven collection. To run without a random backround enable the `--no-random-bg` flag.

```bash
blenderproc download haven resources/haven
```

Note that these commands may take some time to complete.

# Using BlenderBin

First, start by simulating scenes in the render.

```bash
blenderproc run bin_simulator.py
```

In another console start the render

```bash
blenderproc run bin_render.py
```

When a scene has been simulated four imges are rendered of the scene. The scenes are also saved in a folder for easy reuse with other parameters. Check out the resources/simulations folder.

To adjust runtime settings, such as the number of components to simulate and the number of runs, you can use the following arguments:

```bash
blenderproc run bin_render.py \
--comp-amount-min 1 \
--comp-amount-max 10 \
--number-of-runs 10 \
```

To use your own objects, you will need a 3D model of a box or environment and a 3D model of your component, in either the .ply or .obj format. These changes must be made in the config.json file.

```json
    "components": [
        {
            "name" : "obj_000001",
            "obj_id" : 1,
            "path" : "./3d_models/bop/icbin/models/obj_000001.ply",
            "random_color" : false,
            "random_texture" : false,
            "mm_2_m" : true
        },
    ],

    "bins" :  [
        {
            "name" : "box_bin",
            "path" : "./3d_models/bins/boxbin.obj",
            "random_color" : true, 
            "random_texture" : true,
            "mm_2_m": true,
            "dimensions": [
                420,
                300,
                100
            ]
        }
    ],

    "camera":  "..." 

```

Do note that "random_texture" overrides the "random_color", as the random texture is of higher priority.

# Program Architecture

We have split the render and simulator apart as it makes it easier to scale the simulation and rendering independently of each other. The flow of data can be described from the image below.
![Dataflow](images/BlenderBin-dataflow.png)
