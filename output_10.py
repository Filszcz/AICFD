import os
import random
import numpy as np
import pyvista as pv

# --- Configuration ---
INPUT_DIR = "data_output"
OUTPUT_DIR = "sample_visualization"

def convert_to_vtp(file_path, output_path):
    # 1. Load Data
    try:
        # Load the file
        raw = np.load(file_path, allow_pickle=True)
        
        # UNPACKING LOGIC (The Fix)
        if raw.ndim == 0:
            # It's a 0-D array wrapping the dictionary
            loaded = raw.item()
        elif isinstance(raw, np.lib.npyio.NpzFile):
             # It's a zipped .npz file
            loaded = raw
        else:
            # It's a direct array (unlikely given your gen script, but possible)
            print(f"Skipping {os.path.basename(file_path)}: Unknown format.")
            return

    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return

    # 2. Extract Data Array
    if 'data' not in loaded:
        print(f"Skipping {os.path.basename(file_path)}: 'data' key missing.")
        return

    # [x, y, z, u, v, w, p, y_wall, is_fluid, is_wall, is_inlet, is_outlet]
    raw_data = loaded['data']
    
    if raw_data.ndim != 2 or raw_data.shape[1] != 12:
        print(f"Skipping {os.path.basename(file_path)}: Data shape {raw_data.shape} mismatch (Expected N, 12).")
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
    cloud.point_data["is_fluid"]  = raw_data[:, 8].astype(int)
    cloud.point_data["is_wall"]   = raw_data[:, 9].astype(int)
    cloud.point_data["is_inlet"]  = raw_data[:, 10].astype(int)
    cloud.point_data["is_outlet"] = raw_data[:, 11].astype(int)

    # Create "Zone_ID" for easier coloring in Paraview
    # 0=Fluid, 1=Wall, 2=Inlet, 3=Outlet
    zone_id = np.zeros(len(points), dtype=int)
    zone_id[raw_data[:, 9] == 1] = 1  # Wall
    zone_id[raw_data[:, 10] == 1] = 2 # Inlet
    zone_id[raw_data[:, 11] == 1] = 3 # Outlet
    cloud.point_data["Zone_ID"] = zone_id

    # 5. Add Global Metadata (Simulation Parameters)
    try:
        # Check if 'params' exists in the dictionary
        if isinstance(loaded, dict) and 'params' in loaded:
            params = loaded['params'] # It's already a dict inside the loaded dict
            
            # Handle standard params
            for key in ["L", "D", "Ux", "nu_val", "turb_intensity"]:
                if key in params:
                    cloud.field_data[key] = [float(params[key])]
                    
            # Handle shape-specific params
            for k, v in params.items():
                if k not in ["L", "D", "Ux", "nu_val", "turb_intensity"]:
                    # PyVista field data usually wants lists/arrays
                    cloud.field_data[k] = [float(v)]

        if isinstance(loaded, dict) and 'shape_name' in loaded:
            cloud.field_data["Shape_Name"] = [str(loaded['shape_name'])]
            
    except Exception as e:
        print(f"Warning: Could not attach metadata for {os.path.basename(file_path)}: {e}")

    # 6. Save as VTP
    cloud.save(output_path)
    print(f"Converted: {os.path.basename(output_path)} (N={len(points)})")

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get list of all generated files
    all_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".npy")]

    if not all_files:
        print(f"No .npy files found in {INPUT_DIR}!")
        exit()

    # Select 10 random files (or fewer if less exist)
    sample_size = min(10, len(all_files))
    selected_files = random.sample(all_files, sample_size)

    print(f"Converting {sample_size} random cases to VTP (ParaView) format...\n")

    for filename in selected_files:
        input_path = os.path.join(INPUT_DIR, filename)
        
        # Fix extension replacement logic (Handle .npy correctly)
        name_no_ext = os.path.splitext(filename)[0]
        output_filename = f"{name_no_ext}.vtp"
        
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        convert_to_vtp(input_path, output_path)

    print(f"\nDone! Files saved to ./{OUTPUT_DIR}/")
    print("Open these .vtp files in ParaView.")