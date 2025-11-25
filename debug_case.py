import os
import shutil
import subprocess
import numpy as np

# --- Configuration ---
TEMPLATE_DIR = "base_template"
DEBUG_DIR = "debug_run"

# Test Parameters
L = 5.0
D = 0.5
Ux = 1.0
ref = 0

def generate_blockmesh_dict(L, D, ref_level):
    dens_mult = [1.0, 1.25, 1.5, 1.75, 2.0][ref_level]
    r = D / 2.0
    z = 0.05
    y_cells = int(20 * dens_mult)
    x_cells = int((L / D * 20) * dens_mult)
    if y_cells % 2 != 0: y_cells += 1
    
    # Note: Added explicit spaces in the vertices definition to ensure safety
    return f"""
    FoamFile {{ version 2.0; format ascii; class dictionary; object blockMeshDict; }}
    convertToMeters 1;
    vertices
    (
        (0 {-r} {-z}) ({L} {-r} {-z}) ({L} {r} {-z}) (0 {r} {-z})
        (0 {-r} {z}) ({L} {-r} {z}) ({L} {r} {z}) (0 {r} {z})
    );
    blocks ( hex (0 1 2 3 4 5 6 7) ({x_cells} {y_cells} 1) simpleGrading (1 1 1) );
    edges ();
    boundary
    (
        inlet  {{ type patch; faces ((0 4 7 3)); }}
        outlet {{ type patch; faces ((1 2 6 5)); }}
        walls  {{ type wall;  faces ((0 1 5 4) (3 7 6 2)); }}
        frontAndBack {{ type empty; faces ((0 3 2 1) (4 5 6 7)); }}
    );
    mergePatchPairs ();
    """

def run_debug():
    if os.path.exists(DEBUG_DIR): shutil.rmtree(DEBUG_DIR)
    shutil.copytree(TEMPLATE_DIR, DEBUG_DIR)
    
    # Write blockMeshDict
    with open(os.path.join(DEBUG_DIR, "system", "blockMeshDict"), "w") as f:
        f.write(generate_blockmesh_dict(L, D, ref))
        
    print("Running blockMesh...")
    # Capture output this time
    result = subprocess.run(
        ["blockMesh"], 
        cwd=DEBUG_DIR, 
        capture_output=True, 
        text=True
    )
    
    if result.returncode != 0:
        print("!!! blockMesh FAILED !!!")
        print("STDERR:", result.stderr)
        print("STDOUT:", result.stdout)
    else:
        print("blockMesh success!")
        print(result.stdout)

if __name__ == "__main__":
    run_debug()