import os
import random
import numpy as np
import pyvista as pv

INPUT_DIR = "data_output"
OUTPUT_DIR = "sample_raw_viz"

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".npz")]
    
    if not files:
        print("No data found.")
        exit()

    sample = random.sample(files, min(10, len(files)))
    print(f"Converting {len(sample)} files to .vtp for Paraview...")

    for f in sample:
        data = np.load(os.path.join(INPUT_DIR, f))
        
        # Create PolyData (Point Cloud)
        cloud = pv.PolyData(data['pos'])
        
        # Add Fields
        cloud["U"] = data['U']
        cloud["p"] = data['p']
        cloud["k"] = data['k']
        cloud["y"] = data['y']
        cloud["type"] = data['type'] # 1-hot encoded vector
        
        # Save
        out_name = os.path.join(OUTPUT_DIR, f.replace(".npz", ".vtp"))
        cloud.save(out_name)
        print(f"Saved {out_name} (Points: {cloud.n_points})")