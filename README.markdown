# S2 Deep Resolve Using NAIP Imagery

This repository contains scripts for super-resolution of Sentinel-2 imagery using high-resolution NAIP (National Agriculture Imagery Program) aerial imagery. The pipeline leverages NAIP's sub-meter resolution to enhance Sentinel-2 data, with cloud masking, patch generation, and data augmentation for deep learning. Tested on Ubuntu with dependencies like `geotile` and `GDAL`.

## Overview

- **Data Preprocessing**: Intersect Sentinel-2 and NAIP imagery in Google Earth Engine (GEE) with a 1-day temporal delta. Apply Sentinel-2 cloud masks to NAIP and export to a Google Cloud Storage bucket.
- **Patch Generation**: Create image patches using the `geotile` package.
- **Data Augmentation**: Augment patches for deep learning using `PIL`.
- **Deep Learning**: Train a super-resolution model (requires significant GPU resources).

- ![Image A](images/a.png)
- ![Image B](images/b.png)
- ![Image C](images/c.png)

## Prerequisites

### System Requirements
- **Operating System**: Ubuntu (tested on 20.04)
- **Hardware**: GPU with substantial VRAM (e.g., NVIDIA GPUs with CUDA support)
- **Storage**: Sufficient space for NAIP and Sentinel-2 imagery (several GBs)
- **Google Cloud**: Access to a Google Cloud Storage bucket
- **Google Earth Engine**: Account and authentication for GEE

### Software Dependencies
- **Python**: 3.8 or higher
- **GDAL**: Required for `geotile`
- **Python Packages**:
  - `geotile`: For patch generation
  - `PIL` (Pillow): For image augmentation
  - Others (e.g., `numpy`, `tensorflow`/`pytorch` for deep learning)

## Installation

### Step 1: Install GDAL
GDAL is required for `geotile`. Install on Ubuntu:

```
sudo add-apt-repository ppa:ubuntugis/ppa
sudo apt update
sudo apt install gdal-bin
```

Verify:
```
gdalinfo --version
```

More info: https://launchpad.net/~ubuntugis/+archive/ubuntu/ppa

### Step 2: Install geotile
```
pip install geotile
```

More info: https://geotile.readthedocs.io/en/latest/pages/install.html

### Step 3: Install Other Packages
```
pip install Pillow numpy
```

For deep learning:
```
pip install tensorflow
# OR
pip install torch torchvision
```

### Step 4: Set Up Google Earth Engine
Authenticate GEE:
```
earthengine authenticate
```

Ensure access to a Google Cloud Storage bucket.

## Usage

### Script 1: Data Preprocessing
Intersects Sentinel-2 and NAIP imagery in GEE, applies cloud mask, and exports to bucket.

1. Configure GEE credentials and bucket details.
2. Run:
```
python preprocess.py
```

**Input**:
- NAIP imagery collection in GEE
- Sentinel-2 imagery collection in GEE
- Temporal delta: 1 day

**Output**:
- Cloud-masked NAIP imagery in bucket

### Script 2: Patch Generation
Generates patches using `geotile`.

1. Ensure GDAL and `geotile` are installed.
2. Specify input imagery and output directory.
3. Run:
```
python generate_patches.py
```

**Input**:
- Preprocessed NAIP and Sentinel-2 imagery

**Output**:
- Patches in specified directory

### Script 3: Data Augmentation
Augments patches using `PIL`.

1. Install `Pillow`.
2. Specify input patch directory and output directory.
3. Run:
```
python augment.py
```

**Input**:
- Patches from previous step

**Output**:
- Augmented patches in specified directory

### Training
Configure model architecture and parameters in training script. Example:
```
see notebook
```

Ensure GPU drivers and CUDA are configured.

## Notes
- **NAIP Resolution**: Sub-meter (<1m) resolution ideal for super-resolution.
- **Cloud Masking**: Sentinel-2 cloud mask ensures clean NAIP imagery.
- **GPU Requirements**: Training requires significant GPU power.
