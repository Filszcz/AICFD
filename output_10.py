import os
import random
import numpy as np
import pyvista as pv

# --- Configuration ---
INPUT_DIR = "data_output"
OUTPUT_DIR = "sample_visualization"

def convert_npz_to_vtp(npz_path, output_path):
    # 1. Load Data
    try:
        # allow_pickle=True is required to load the 'params' dictionary and string data
        loaded = np.load(npz_path, allow_pickle=True)
    except Exception as e:
        print(f"Error loading {npz_path}: {e}")
        return

    # 2. Check for New Data Format
    if 'data' not in loaded:
        print(f"Skipping {os.path.basename(npz_path)}: 'data' array missing. Format mismatch.")
        return

    # Extract the main matrix (N, 12)
    # [x, y, z, u, v, w, p, y_wall, is_fluid, is_wall, is_inlet, is_outlet]
    raw_data = loaded['data']
    
    if raw_data.shape[1] != 12:
        print(f"Skipping {os.path.basename(npz_path)}: Expected 12 columns, found {raw_data.shape[1]}.")
        return

    # 3. Create PyVista PolyData (Point Cloud)
    # Columns 0, 1, 2 are X, Y, Z
    points = raw_data[:, 0:3]
    cloud = pv.PolyData(points)

    # 4. Attach Physics Fields
    # Columns 3, 4, 5 are Velocity vectors
    cloud.point_data["U"] = raw_data[:, 3:6]
    
    # Column 6 is Pressure
    cloud.point_data["p"] = raw_data[:, 6]
    
    # Column 7 is Wall Distance
    cloud.point_data["y_wall"] = raw_data[:, 7]
    
    # Columns 8-11 are Boolean Flags
    cloud.point_data["is_fluid"]  = raw_data[:, 8]
    cloud.point_data["is_wall"]   = raw_data[:, 9]
    cloud.point_data["is_inlet"]  = raw_data[:, 10]
    cloud.point_data["is_outlet"] = raw_data[:, 11]

    # Optional: Create a single integer "Zone_ID" for easier coloring in Paraview
    # 0=Fluid, 1=Wall, 2=Inlet, 3=Outlet
    zone_id = np.zeros(len(points), dtype=int)
    zone_id[raw_data[:, 9] == 1] = 1  # Wall
    zone_id[raw_data[:, 10] == 1] = 2 # Inlet
    zone_id[raw_data[:, 11] == 1] = 3 # Outlet
    cloud.point_data["Zone_ID"] = zone_id

    # 5. Add Global Metadata
    # The new format stores physical params in a dictionary called 'params'
    try:
        if 'shape_name' in loaded:
            cloud.field_data["Shape_Name"] = [str(loaded['shape_name'])]
        
        if 'params' in loaded:
            # np.load wraps dicts in a 0-d array, use .item() to extract
            params = loaded['params'].item()
            
            # Extract specific known keys if they exist
            for key in ["L", "D", "Ux", "nu_val", "turb_intensity"]:
                if key in params:
                    cloud.field_data[key] = [float(params[key])]
                    
            # Specific shape params (valve_opening, bend_angle, etc)
            for k, v in params.items():
                if k not in ["L", "D", "Ux", "nu_val", "turb_intensity"]:
                    cloud.field_data[k] = [float(v)]
                    
    except Exception as e:
        print(f"Warning: Could not attach full metadata for {os.path.basename(npz_path)}: {e}")

    # 6. Save as VTP
    cloud.save(output_path)
    print(f"Converted: {os.path.basename(output_path)} (N={len(points)})")

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get list of all generated files
    all_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".npz")]

    if not all_files:
        print(f"No .npz files found in {INPUT_DIR}!")
        exit()

    # Select 10 random files (or fewer if less exist)
    sample_size = min(10, len(all_files))
    selected_files = random.sample(all_files, sample_size)

    print(f"Converting {sample_size} random cases to VTP (Point Cloud) for Paraview...\n")

    for filename in selected_files:
        input_path = os.path.join(INPUT_DIR, filename)
        # Change extension to .vtp
        output_filename = filename.replace(".npz", ".vtp")
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        convert_npz_to_vtp(input_path, output_path)

    print(f"\nDone! Files saved to ./{OUTPUT_DIR}/")
    print("Open these .vtp files in Paraview.")
    print("Tip: Color by 'Zone_ID' to check geometry, or 'U'/'p' for physics.")