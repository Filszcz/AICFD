# AICFD - AI-Powered CFD Flow Prediction

A machine learning pipeline for predicting fluid flow fields in pipe geometries using PointNet neural networks trained on OpenFOAM CFD simulation data.

## Overview

This project generates synthetic CFD datasets across various pipe geometries (straight, bends, valves, obstacles, venturi, manifolds) and trains a PointNet model to predict velocity and pressure fields from 3D point clouds.

## Workflow

The complete pipeline consists of **four sequential steps**:

### 1. Setup Shape Generators
```bash
python setup_shapes.py
```
- **Purpose**: Creates `shapes/` module with geometry generators
- **Output**: Python files for 6 different pipe geometries
- **Run once**: Only needed for initial setup
- **Duration**: <1 second

### 2. Reset OpenFOAM Template
```bash
python reset_template.py
```
- **Purpose**: Creates clean OpenFOAM case template
- **Output**: `base_template/` directory with system files
- **Run**: Before each dataset generation (optional)
- **Duration**: <1 second

### 3. Generate CFD Dataset
```bash
python generate_dataset.py
```
- **Purpose**: Runs 300 OpenFOAM simulations with varying parameters
- **Output**: `.npy` files in `data_output/` (each ~200-1500 KB)
- **Duration**: 2-6 hours (on 10 cores)
- **Requirements**: OpenFOAM v13+ installed and sourced
- **Configuration**: Edit lines 18-26 to adjust samples, cores, parameters

### 4. Train PointNet Model
```bash
python train_pointnetv1.py
```
- **Purpose**: Trains neural network to predict flow from geometry
- **Output**: `weights/best_model.pth` + training logs in `wandb/`
- **Duration**: 6-12 hours (500 epochs on GPU)
- **Requirements**: PyTorch with CUDA, wandb, matplotlib
- **Configuration**: Edit `DEFAULT_CONFIG` (line 20-34) for hyperparameters

## Requirements

### System Dependencies
- **OpenFOAM**: v2312 or v13+ (for mesh generation and CFD solving)
  - Ensure `blockMesh` and `simpleFoam` are in PATH
- **Conda**: For Python environment management

### Python Environment (P12)
```bash
conda create -n P12 python=3.10
conda activate P12
pip install numpy scipy pyvista torch wandb matplotlib scikit-learn
```

**Key packages**:
- `numpy`, `scipy`: Data processing
- `pyvista`: OpenFOAM result reading
- `torch`: PointNet training
- `wandb`: Experiment tracking
- `matplotlib`: Visualization

## Configuration Guide

### Dataset Generation (`generate_dataset.py`)
```python
N_CORES = 10                # Parallel workers (auto-limited to CPU count)
SAMPLES_PER_SHAPE = 50      # Samples per geometry type
LENGTHS = [10.0, 15.0]      # Pipe lengths (m)
DIAMETERS = [1.0]           # Pipe diameters (m)  
VELOCITIES = [1.0, 5.0]     # Inlet velocities (m/s)
REFINEMENTS = [0, 1]        # Mesh refinement levels
```

### Model Training (`train_pointnetv1.py`)
```python
batch_size = 8              # Batch size (reduce if OOM)
learning_rate = 1e-4        # Initial learning rate
epochs = 500                # Total training epochs
scaling = 1.0               # Model width (0.25-2.0)
val_split = 0.2             # Validation data ratio
```

## Output Data Format

### Dataset Files (`.npy`)
Each file contains an `(N, 12)` array where N = number of mesh points:

| Column | Description | Type |
|--------|-------------|------|
| 0-2 | x, y, z coordinates | float |
| 3-5 | u, v, w velocity components | float |
| 6 | p pressure | float |
| 7 | y_wall (distance to wall) | float |
| 8 | is_fluid flag | bool |
| 9-11 | is_wall, is_inlet, is_outlet flags | bool |

### Model Checkpoints
- `weights/best_model.pth`: Best validation loss model
- State dict format (use `model.load_state_dict()`)

## Training Features

The training pipeline includes several stability improvements:

1. **Gradient Clipping**: Prevents gradient explosion (max_norm=1.0)
2. **Target Normalization**: Velocity by magnitude, pressure by standard deviation
3. **Learning Rate Scheduling**: ReduceLROnPlateau with patience=10
4. **Masked Loss**: Only computes loss on fluid cells (excludes boundaries)
5. **Auto Offline Mode**: Falls back to offline wandb if no API key

## Performance Expectations

| Metric | Value |
|--------|-------|
| Dataset Size | 300 samples (~150 MB) |
| Generation Time | 2-6 hours (10 cores) |
| Training Time | 6-12 hours (GPU, 500 epochs) |
| Best Val Loss | 0.02-0.04 (normalized MSE) |
| Model Parameters | ~1.5M (scaling=1.0) |

## Troubleshooting

**OpenFOAM not found**
```bash
source /opt/openfoam13/etc/bashrc  # Or your OpenFOAM path
```

**CUDA out of memory**
- Reduce `batch_size` from 8 to 4 or 2
- Reduce `scaling` from 1.0 to 0.5

**Training instability / NaN loss**
- Already fixed with gradient clipping
- If persists, increase clipping strength (reduce `max_norm`)

**Slow dataset generation**
- Increase `N_CORES` up to CPU count
- Use coarser mesh (increase `BASE_CELL_SIZE`)

## Project Structure

```
AICFD/
├── reset_template.py          # Generates base_template/
├── setup_shapes.py             # Generates shapes/ module
├── generate_dataset.py         # Creates data_output/*.npy
├── train_pointnetv1.py         # Trains model → weights/
├── shapes/                     # Geometry generators
│   ├── straight.py
│   ├── bend.py
│   ├── valve.py
│   └── ...
├── base_template/              # OpenFOAM template
│   ├── system/
│   └── constant/
├── data_output/               # Generated datasets
└── weights/                   # Trained models
```

## Citation

If you use this code, please cite:
```
AICFD: AI-Powered CFD Flow Prediction using PointNet
```
