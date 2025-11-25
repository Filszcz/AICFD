import os
import random
import numpy as np
import pyvista as pv

# --- Configuration ---
INPUT_DIR = "data_output"
OUTPUT_DIR = "sample_visualization"
DL_RESOLUTION = (256, 64, 1)

def convert_npz_to_vtk(npz_path, output_path):
    # 1. Load Data
    try:
        data = np.load(npz_path)
    except Exception as e:
        print(f"Error loading {npz_path}: {e}")
        return

    # 2. Extract Metadata to Reconstruct Geometry
    L = float(data['L'])
    D = float(data['D'])
    Ux = float(data['Ux_in'])
    Ref = int(data['Ref'])

    # 3. Reconstruct Mesh (Must match generation logic exactly)
    # We use indexing='ij' because that's how we generated the data
    x = np.linspace(0, L, DL_RESOLUTION[0])
    y = np.linspace(-D/2, D/2, DL_RESOLUTION[1])
    z = np.array([0])
    
    grid_x, grid_y, grid_z = np.meshgrid(x, y, z, indexing='ij')
    
    # Create PyVista StructuredGrid
    grid = pv.StructuredGrid(grid_x, grid_y, grid_z)

    # 4. Attach Field Data
    # Note: PyVista expects flat arrays (N_points, Components)
    # We flatten using default (C-style) row-major order which matches the reshaping
    
    # Velocity (Vector)
    grid.point_data["U"] = data['U'].reshape(-1, 3)
    
    # Scalars
    grid.point_data["p"] = data['p'].flatten()
    grid.point_data["k"] = data['k'].flatten()
    grid.point_data["epsilon"] = data['epsilon'].flatten()
    grid.point_data["y"] = data['y'].flatten()

    # 5. Add Metadata (Optional, useful in Paraview 'Field Data' tab)
    grid.field_data["Length"] = [L]
    grid.field_data["Diameter"] = [D]
    grid.field_data["Inlet_Velocity"] = [Ux]
    grid.field_data["Refinement_Level"] = [Ref]

    # 6. Save
    grid.save(output_path)
    print(f"Converted: L={L:.1f}, D={D:.2f}, U={Ux:.1f} -> {os.path.basename(output_path)}")

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get list of all generated files
    all_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".npz")]

    if not all_files:
        print("No .npz files found in data_output!")
        exit()

    # Select 10 random files
    # (If less than 10 exist, take all of them)
    sample_size = min(10, len(all_files))
    selected_files = random.sample(all_files, sample_size)

    print(f"Converting {sample_size} random cases to VTK for Paraview inspection...\n")

    for filename in selected_files:
        input_path = os.path.join(INPUT_DIR, filename)
        # Rename output extension to .vts (XML Structured Grid)
        output_filename = filename.replace(".npz", ".vts")
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        convert_npz_to_vtk(input_path, output_path)

    print(f"\nDone! Files saved to ./{OUTPUT_DIR}/")
    print("Open these .vts files directly in Paraview.")