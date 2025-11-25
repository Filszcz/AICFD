import os
import numpy as np
from pathlib import Path

# CONFIG
INPUT_DIR = Path("data_output")
OUTPUT_DIR = Path("extracted_data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def process_npz_to_npy():
    files = list(INPUT_DIR.glob("*.npz"))
    
    if not files:
        print(f"No .npz files found in {INPUT_DIR}")
        return

    print(f"Found {len(files)} .npz files. Converting to Point Cloud .npy...")
    print("Output Format: [x, y, z, u, v, w, p, y_wall, is_fluid, is_wall, is_inlet, is_outlet]")

    for i, f in enumerate(files):
        try:
            # 1. Load Data
            data = np.load(f)
            
            # 2. Extract Fields (Raw Point Cloud Data)
            # These are already in shape (N, 3) or (N,)
            pos = data['pos']  # (N, 3)
            U = data['U']      # (N, 3)
            
            # Reshape scalars to (N, 1) for stacking
            p = data['p'].reshape(-1, 1)
            y_dist = data['y'].reshape(-1, 1)
            
            # Type is already (N, 4)
            types = data['type']

            # 3. Stack into single matrix (N, 12)
            # Columns: 
            # 0-2:   Position (x,y,z)
            # 3-5:   Velocity (u,v,w)
            # 6:     Pressure
            # 7:     Wall Distance
            # 8-11: Type (Fluid, Wall, Inlet, Outlet)
            
            final_array = np.hstack((
                pos, 
                U, 
                p, 
                y_dist, 
                types
            ))
            
            # 4. Save
            save_name = OUTPUT_DIR / f"{f.stem}.npy"
            np.save(save_name, final_array)
            
            if i % 100 == 0:
                print(f"[{i}/{len(files)}] Converted {f.name} (N={pos.shape[0]})")

        except Exception as e:
            print(f"Error converting {f.name}: {e}")

    print("\nConversion Complete.")
    print(f"Data saved to: {OUTPUT_DIR.absolute()}")

if __name__ == "__main__":
    process_npz_to_npy()