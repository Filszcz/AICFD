import os
import numpy as np
from pathlib import Path

# CONFIG
INPUT_DIR = Path("data_output")
OUTPUT_DIR = Path("extracted_data_csv") 
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def process_npz_to_csv():
    files = list(INPUT_DIR.glob("*.npz"))
    
    if not files:
        print(f"No .npz files found in {INPUT_DIR}")
        return

    print(f"Found {len(files)} .npz files. Converting to Point Cloud .csv...")
    print("Output Format: [x, y, z, u, v, w, p, y_wall, is_fluid, is_wall, is_inlet, is_outlet]")

    count = 0
    for i, f in enumerate(files):
        try:
            # 1. Load Data
            # allow_pickle=True is required because the new format includes a metadata dictionary
            data = np.load(f, allow_pickle=True)
            
            final_array = None

            # --- CASE A: New Format (Single 'data' array) ---
            if 'data' in data:
                # The new generator saves data stacked as (N, 12)
                final_array = data['data']
                
                # Sanity Check
                if final_array.shape[1] != 12:
                    print(f"Skipping {f.name}: Expected 12 columns, found {final_array.shape[1]}")
                    continue

            # --- CASE B: Old Format (Separate arrays) ---
            elif 'pos' in data:
                # Reconstruct to match the new 12-column format
                # Note: Old files might have 'k' and 'epsilon', but we omit them 
                # to keep CSV structure consistent with new files.
                pos = data['pos']       # (N, 3)
                U = data['U']           # (N, 3)
                p = data['p'].reshape(-1, 1)
                y_dist = data['y'].reshape(-1, 1)
                types = data['type']    # (N, 4)
                
                final_array = np.hstack((
                    pos, 
                    U, 
                    p, 
                    y_dist, 
                    types
                ))
            else:
                print(f"Skipping {f.name}: Unknown file structure.")
                continue

            # 3. Save as CSV
            save_name = OUTPUT_DIR / f"{f.stem}.csv"
            
            # Updated Header for 12 columns
            csv_header = "x,y,z,u,v,w,p,y_wall,is_fluid,is_wall,is_inlet,is_outlet"
            
            np.savetxt(
                save_name, 
                final_array, 
                delimiter=",", 
                header=csv_header, 
                comments="", 
                fmt='%.6e'   
            )
            
            count += 1
            if count % 50 == 0:
                print(f"[{i+1}/{len(files)}] Converted {f.name} (N={final_array.shape[0]})")

        except Exception as e:
            print(f"Error converting {f.name}: {e}")

    print("\nConversion Complete.")
    print(f"Successfully converted {count} files.")
    print(f"Data saved to: {OUTPUT_DIR.absolute()}")

if __name__ == "__main__":
    process_npz_to_csv()