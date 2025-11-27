import os
import numpy as np
from pathlib import Path

# CONFIG
INPUT_DIR = Path("data_output")
OUTPUT_DIR = Path("extracted_data_csv") # Changed folder name to avoid mixing types
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def process_npz_to_csv():
    files = list(INPUT_DIR.glob("*.npz"))
    
    if not files:
        print(f"No .npz files found in {INPUT_DIR}")
        return

    print(f"Found {len(files)} .npz files. Converting to Point Cloud .csv...")
    print("Output Format: [x, y, z, u, v, w, p, k, eps, y_wall, is_fluid, is_wall, is_inlet, is_outlet]")

    for i, f in enumerate(files):
        try:
            # 1. Load Data
            data = np.load(f)
            
            # 2. Extract Fields (Raw Point Cloud Data)
            pos = data['pos']  # (N, 3)
            U = data['U']      # (N, 3)
            
            # Reshape scalars to (N, 1) for stacking
            p = data['p'].reshape(-1, 1)
            k = data['k'].reshape(-1, 1)
            eps = data['epsilon'].reshape(-1, 1)
            y_dist = data['y'].reshape(-1, 1)
            
            # Type is already (N, 4)
            types = data['type']

            # 3. Stack into single matrix (N, 14)
            final_array = np.hstack((
                pos, 
                U, 
                p, 
                k, 
                eps, 
                y_dist, 
                types
            ))
            
            # 4. Save as CSV
            save_name = OUTPUT_DIR / f"{f.stem}.csv"
            
            # Define the header for the CSV file
            csv_header = "x,y,z,u,v,w,p,k,eps,y_wall,is_fluid,is_wall,is_inlet,is_outlet"
            
            # Save using np.savetxt
            # fmt='%.6e' ensures scientific notation with reasonable precision. 
            # You can change it to '%.9f' for standard floats or omit it for default behavior.
            np.savetxt(
                save_name, 
                final_array, 
                delimiter=",", 
                header=csv_header, 
                comments="", # Set comments to empty string so the header doesn't start with '#'
                fmt='%.6e'   
            )
            
            if i % 100 == 0:
                print(f"[{i}/{len(files)}] Converted {f.name} to CSV (N={pos.shape[0]})")

        except Exception as e:
            print(f"Error converting {f.name}: {e}")

    print("\nConversion Complete.")
    print(f"Data saved to: {OUTPUT_DIR.absolute()}")

if __name__ == "__main__":
    process_npz_to_csv()