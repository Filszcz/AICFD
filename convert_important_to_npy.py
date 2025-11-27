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

    count = 0
    for i, f in enumerate(files):
        try:
            # 1. Load Data (allow_pickle=True needed if metadata dicts are present)
            loaded = np.load(f, allow_pickle=True)
            
            final_array = None

            # --- CASE A: New Format (Single 'data' array) ---
            if 'data' in loaded:
                final_array = loaded['data']
                
                # Validation check
                if final_array.shape[1] != 12:
                    print(f"Skipping {f.name}: Expected 12 columns, found {final_array.shape[1]}")
                    continue

            # --- CASE B: Old Format (Separate arrays 'pos', 'U', etc.) ---
            elif 'pos' in loaded:
                # Reconstruct the stack for legacy files
                pos = loaded['pos']       # (N, 3)
                U = loaded['U']           # (N, 3)
                p = loaded['p'].reshape(-1, 1)
                y_dist = loaded['y'].reshape(-1, 1)
                types = loaded['type']    # (N, 4)
                
                final_array = np.hstack((pos, U, p, y_dist, types))

            else:
                print(f"Skipping {f.name}: Unknown file structure.")
                continue

            # 2. Save
            # Save as .npy for fast loading in PyTorch/TensorFlow
            save_name = OUTPUT_DIR / f"{f.stem}.npy"
            np.save(save_name, final_array)
            
            count += 1
            if count % 50 == 0:
                print(f"[{i+1}/{len(files)}] Converted {f.name} (N={final_array.shape[0]})")

        except Exception as e:
            print(f"Error converting {f.name}: {e}")

    print("\nConversion Complete.")
    print(f"Successfully converted {count} files.")
    print(f"Data saved to: {OUTPUT_DIR.absolute()}")

if __name__ == "__main__":
    process_npz_to_npy()