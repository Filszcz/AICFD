import os
import numpy as np
from pathlib import Path

# CONFIG
INPUT_DIR = Path("data_output")
OUTPUT_DIR = Path("extracted_data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Grid Resolution used in generation
DL_RESOLUTION = (256, 64, 1) # X, Y, Z

def get_type_encoding(ix, iy, nx, ny):
    """
    Returns one-hot [is_fluid, is_wall, is_inlet, is_outlet]
    based on grid position.
    """
    # Default: Fluid
    encoding = [1, 0, 0, 0]
    
    # Inlet (Left edge)
    if ix == 0:
        encoding = [0, 0, 1, 0]
    # Outlet (Right edge)
    elif ix == nx - 1:
        encoding = [0, 0, 0, 1]
    # Walls (Top and Bottom edges)
    elif iy == 0 or iy == ny - 1:
        encoding = [0, 1, 0, 0]
        
    return encoding

def process_npz_to_npy():
    files = list(INPUT_DIR.glob("*.npz"))
    print(f"Found {len(files)} .npz files. Converting to Point Cloud .npy...")

    for i, f in enumerate(files):
        try:
            # 1. Load Data
            data = np.load(f)
            L = float(data['L'])
            D = float(data['D'])
            
            # 2. Reconstruct Grid Coordinates
            nx, ny = DL_RESOLUTION[0], DL_RESOLUTION[1]
            x_range = np.linspace(0, L, nx)
            y_range = np.linspace(-D/2, D/2, ny)
            grid_x, grid_y = np.meshgrid(x_range, y_range, indexing='ij')
            
            # Flatten everything to list of points (N, ...)
            X = grid_x.flatten()
            Y = grid_y.flatten()
            Z = np.zeros_like(X) # 2D problem, Z=0
            
            # Stack Coordinates
            coords = np.column_stack((X, Y, Z))
            
            # 3. Stack Physics
            # Reshape to (-1, C) flattens in the same order as meshgrid 'ij'
            U = data['U'].reshape(-1, 3)
            p = data['p'].reshape(-1, 1)
            y_dist = data['y'].reshape(-1, 1)
            
            # 4. Generate Types (Fluid/Wall/Inlet/Outlet)
            # Create a grid of types matching the meshgrid
            # We iterate indices to assign types
            types = []
            for ix in range(nx):
                for iy in range(ny):
                    types.append(get_type_encoding(ix, iy, nx, ny))
            types = np.array(types)
            
            # 5. Assemble Final Array
            # Format: [x, y, z, u, v, w, p, is_fluid, is_wall, is_inlet, is_outlet, wall_dist]
            final_array = np.column_stack((coords, U, p, types, y_dist))
            
            # 6. Save
            save_name = OUTPUT_DIR / f"{f.stem}.npy"
            np.save(save_name, final_array)
            
            if i % 100 == 0:
                print(f"[{i}/{len(files)}] Converted {f.name}")

        except Exception as e:
            print(f"Error converting {f.name}: {e}")

    print("Conversion Complete.")

if __name__ == "__main__":
    process_npz_to_npy()