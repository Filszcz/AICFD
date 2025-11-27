import os
import shutil
import subprocess
import textwrap
import sys
import numpy as np

# Import your shape generators
import shapes.straight, shapes.bend, shapes.valve, shapes.obstacle
import shapes.venturi, shapes.manifold

# --- Configuration ---
DEBUG_DIR = "debug_runs"
BASE_CELL_SIZE = 0.05  # Coarse mesh for fast debugging

# Standard physical params for testing
PARAMS = {
    "L": 10.0,
    "D": 1.0,
    "Ux": 1.0,
    "ref": 0,
    "nu_val": 1e-6,
    "turb_intensity": 0.05
}

# Shape-specific test parameters (Known "Safe" defaults)
SHAPE_TEST_PARAMS = {
    "straight": {},
    "bend": {"bend_angle": 90, "bend_radius": 1.5},
    "valve": {"valve_opening": 0.5, "valve_thickness": 0.2},
    "obstacle": {"obs_size": 0.3, "obs_offset": 0.0},
    "venturi": {"throat_ratio": 0.5, "conv_len_ratio": 0.25, "div_len_ratio": 0.5},
    "manifold": {"branch_width_ratio": 0.5, "branch_height_ratio": 1.5}
}

SHAPE_HANDLERS = {
    "straight": shapes.straight.generate,
    "bend": shapes.bend.generate,
    "valve": shapes.valve.generate,
    "obstacle": shapes.obstacle.generate,
    "venturi": shapes.venturi.generate,
    "manifold": shapes.manifold.generate
}

def write_file(path, content):
    with open(path, "w") as f:
        f.write(textwrap.dedent(content))

def setup_case(run_dir, shape_name, bm_content):
    os.makedirs(os.path.join(run_dir, "system"), exist_ok=True)
    os.makedirs(os.path.join(run_dir, "constant"), exist_ok=True)
    os.makedirs(os.path.join(run_dir, "0"), exist_ok=True)

    # 1. blockMeshDict
    write_file(os.path.join(run_dir, "system", "blockMeshDict"), f"""
        FoamFile {{ version 2.0; format ascii; class dictionary; object blockMeshDict; }}
        convertToMeters 1;
        {bm_content}
    """)

    # 2. controlDict (Minimal)
    write_file(os.path.join(run_dir, "system", "controlDict"), """
        FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }
        application     simpleFoam;
        startFrom       latestTime;
        startTime       0;
        stopAt          endTime;
        endTime         1;
        deltaT          1;
        writeControl    timeStep;
        writeInterval   1;
    """)
    
    # 3. fvSchemes (Standard)
    write_file(os.path.join(run_dir, "system", "fvSchemes"), """
        FoamFile { version 2.0; format ascii; class dictionary; object fvSchemes; }
        ddtSchemes { default steadyState; }
        gradSchemes { default Gauss linear; }
        divSchemes { default none; div(phi,U) bounded Gauss linearUpwind grad(U); div(phi,k) bounded Gauss upwind; div(phi,epsilon) bounded Gauss upwind; }
        laplacianSchemes { default Gauss linear corrected; }
        interpolationSchemes { default linear; }
        snGradSchemes { default corrected; }
    """)

    # 4. fvSolution (Standard)
    write_file(os.path.join(run_dir, "system", "fvSolution"), """
        FoamFile { version 2.0; format ascii; class dictionary; object fvSolution; }
        solvers { p { solver GAMG; tolerance 1e-6; relTol 0.1; smoother GaussSeidel; } "(U|k|epsilon)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0.1; } }
        SIMPLE { nNonOrthogonalCorrectors 0; consistent yes; }
        relaxationFactors { equations { U 0.9; k 0.7; epsilon 0.7; } }
    """)

def run_debug():
    if os.path.exists(DEBUG_DIR): shutil.rmtree(DEBUG_DIR)
    os.makedirs(DEBUG_DIR, exist_ok=True)

    print(f"--- Starting Debug Run in folder: {DEBUG_DIR} ---")
    print(f"Target Cell Size: {BASE_CELL_SIZE}")

    for shape_name, generator in SHAPE_HANDLERS.items():
        print(f"\nTesting Shape: [{shape_name}]")
        case_dir = os.path.join(DEBUG_DIR, shape_name)
        
        # Get Params
        kwargs = SHAPE_TEST_PARAMS[shape_name]
        
        try:
            # Generate String
            bm_content = generator(PARAMS["L"], PARAMS["D"], BASE_CELL_SIZE, **kwargs)
            
            # Write Files
            setup_case(case_dir, shape_name, bm_content)
            
            # 1. Run blockMesh
            print("  > Running blockMesh...", end="")
            res = subprocess.run(["blockMesh"], cwd=case_dir, capture_output=True, text=True)
            
            if res.returncode != 0:
                print(" FAILED!")
                print("-" * 60)
                print("BLOCKMESH ERROR LOG:")
                print(res.stderr)
                print("-" * 60)
                print("GENERATED blockMeshDict (Partial):")
                print("\n".join(bm_content.splitlines()[:50])) # Print first 50 lines
                print("..." + "\n".join(bm_content.splitlines()[-20:])) # Print last 20 lines
                print("-" * 60)
                continue
            else:
                print(" OK.")

            # 2. Run checkMesh (Checks for negative volume / topology errors)
            print("  > Running checkMesh...", end="")
            res = subprocess.run(["checkMesh"], cwd=case_dir, capture_output=True, text=True)
            if "Mesh OK." not in res.stdout:
                print(" FAILED (Bad Quality)!")
                print(res.stdout[-500:]) # Print last 500 chars of checkMesh
                continue
            else:
                print(" OK.")
                
            print(f"  > [SUCCESS] {shape_name} is valid.")

        except Exception as e:
            print(f"  > PYTHON ERROR: {str(e)}")

if __name__ == "__main__":
    run_debug()