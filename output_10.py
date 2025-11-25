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
        data = np.load(npz_path)
    except Exception as e:
        print(f"Error loading {npz_path}: {e}")
        return

    # 2. Check for correct data format (Raw Point Cloud)
    if 'pos' not in data:
        print(f"Skipping {os.path.basename(npz_path)}: 'pos' array missing. Is this an old interpolated file?")
        return

    # 3. Create PyVista PolyData (Unstructured Point Cloud)
    # Unlike StructuredGrid, we don't define dimensions, just a list of X,Y,Z points
    points = data['pos']
    cloud = pv.PolyData(points)

    # 4. Attach Physics Fields
    # The arrays in the .npz are already (N, 3) or (N,), matching the points
    cloud.point_data["U"] = data['U']
    cloud.point_data["p"] = data['p']
    cloud.point_data["k"] = data['k']
    cloud.point_data["epsilon"] = data['epsilon']
    cloud.point_data["y"] = data['y']
    cloud.point_data["type"] = data['type'] # One-Hot Encoded boundaries

    # 5. Add Global Metadata
    cloud.field_data["Length"] = [float(data['L'])]
    cloud.field_data["Diameter"] = [float(data['D'])]
    cloud.field_data["Inlet_Velocity"] = [float(data['Ux_in'])]
    cloud.field_data["Refinement_Level"] = [int(data['Ref'])]

    # 6. Save as VTP (VTK XML PolyData)
    # .vtp is the correct format for point clouds in Paraview
    cloud.save(output_path)
    print(f"Converted: N={len(points)} pts -> {os.path.basename(output_path)}")

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get list of all generated files
    all_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".npz")]

    if not all_files:
        print("No .npz files found in data_output!")
        exit()

    # Select 10 random files
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
    print("Tip: In Paraview, change 'Coloring' to 'U' or 'p' to see the data.")