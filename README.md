# Introduction

Simulate many objects falling in a bin and create high detailed annotated images with the BlenderBin repository.
Dependencies

# Dependencies

To use the BlenderBin repository, a Linux-based operating system is required. The repository has been tested on Ubuntu 18.04 and 22.04. Additionally, CMake must be installed.
Getting Started

To begin, download the repository:

``` bash
git clone https://github.com/hansaskov/BlenderBin
cd ./BlenderBin
```

Next, install the necessary dependencies:

``` bash
pip install -r requirements.txt
```
For the bin_render.py script, download the Haven background:

``` bash
blenderproc download haven resources/blenderproc/haven
```
For the bop_render.py script, download the CC_Textures:

``` bash
blenderproc download cc_textures resources/blenderproc/cctextures
```
Note that these commands may take some time to complete. It is recommended to run them in separate terminals.
Running the Render

# Running the Render

To test the program, run the following command using the default component and bin:


``` bash
blenderproc run bin_render.py
```
To use your own objects, you will need a 3D model of a box or environment and a 3D model of your component, in either .obj format. These models must be set in the config.json file.

To adjust runtime settings, such as the number of components to simulate and the number of runs, you can use the following arguments:


``` bash
blenderproc run bin_render.py \
--comp-amount-min 1 \
--comp-amount-max 10 \
--number-of-runs 10 \
--instance-num 1 \
```
