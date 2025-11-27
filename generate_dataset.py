import os
import shutil
import numpy as np
import subprocess
import textwrap
import sys
import random
import itertools
from multiprocessing import Pool
import pyvista as pv

# Import Shapes
import shapes.straight, shapes.bends, shapes.valve, shapes.obstacle
import shapes.step, shapes.venturi, shapes.cylinder

# --- Configuration ---
TEMPLATE_DIR = "base_template"
OUTPUT_DIR = "data_output"
N_CORES = 12  # Adjust to your CPU
SAMPLES_PER_SHAPE = 50  # How many random variations per shape?

# Global Ranges
LENGTHS = np.linspace(8, 15, 3)
DIAMETERS = np.linspace(0.8, 1.5, 3)
VELOCITIES = np.linspace(1, 5, 3)
REFINEMENTS = [0] # Keep low for speed during testing

# Shape Registry
SHAPE_HANDLERS = {
    "straight": shapes.straight.generate,
    "bend": shapes.bends.generate_90,
    "valve": shapes.valve.generate,
    "obstacle": shapes.obstacle.generate,
    "step": shapes.step.generate,
    "venturi": shapes.venturi.generate,
    "cylinder": shapes.cylinder.generate
}

def get_random_shape_params(shape_name):
    """Returns a dictionary of valid random parameters for the specific shape."""
    params = {}
    if shape_name == "valve":
        params["valve_opening"] = round(random.uniform(0.2, 0.8), 2)
        params["valve_pos"] = round(random.uniform(0.3, 0.7), 2)
    elif shape_name == "obstacle":
        params["obs_size_ratio"] = round(random.uniform(0.2, 0.5), 2)
        params["obs_pos"] = round(random.uniform(0.3, 0.7), 2)
    elif shape_name == "step":
        params["expansion_ratio"] = round(random.uniform(1.5, 2.5), 2)
    elif shape_name == "venturi":
        params["throat_ratio"] = round(random.uniform(0.3, 0.7), 2)
    elif shape_name == "cylinder":
        params["cyl_size_ratio"] = round(random.uniform(0.2, 0.6), 2)
    elif shape_name == "bend":
        params["curve_radius_ratio"] = round(random.uniform(1.2, 2.5), 2)
    return params

def write_foam_file(path, content):
    with open(path, "w") as f:
        f.write(textwrap.dedent(content))

def generate_case_files(run_dir, shape_key, L, D, ref, Ux, shape_params):
    os.makedirs(os.path.join(run_dir, "0"), exist_ok=True)
    
    # 1. BlockMesh
    dens_mult = 1.2 ** ref
    generator = SHAPE_HANDLERS[shape_key]
    # PASS THE RANDOM PARAMS HERE using **unpacking
    bm_content = generator(L, D, dens_mult, **shape_params)
        
    write_foam_file(os.path.join(run_dir, "system", "blockMeshDict"), f"""\
        FoamFile {{ version 2.0; format ascii; class dictionary; object blockMeshDict; }}
        convertToMeters 1;
        {bm_content}
    """)
    
    # 2. Physics (Water)
    # k-epsilon estimation
    turb_int = 0.05
    k_val = max(1.5 * (Ux * turb_int)**2, 1e-8)
    l_mix = 0.07 * D
    eps_val = max((0.09**0.75 * k_val**1.5) / l_mix, 1e-8)

    write_foam_file(os.path.join(run_dir, "0", "U"), f"""\
        FoamFile {{ version 2.0; format ascii; class volVectorField; object U; }}
        dimensions [0 1 -1 0 0 0 0]; internalField uniform ({Ux} 0 0);
        boundaryField {{ 
            ".*inlet.*" {{ type fixedValue; value uniform ({Ux} 0 0); }}
            ".*outlet.*" {{ type zeroGradient; }}
            walls {{ type noSlip; }}
            frontAndBack {{ type empty; }} 
        }}
    """)
    
    # Standard pressure and turbulence files
    write_foam_file(os.path.join(run_dir, "0", "p"), """\
        FoamFile { version 2.0; format ascii; class volScalarField; object p; }
        dimensions [0 2 -2 0 0 0 0]; internalField uniform 0;
        boundaryField { ".*inlet.*" { type zeroGradient; } ".*outlet.*" { type fixedValue; value uniform 0; } walls { type zeroGradient; } frontAndBack { type empty; } }
    """)
    write_foam_file(os.path.join(run_dir, "0", "k"), f"""\
        FoamFile {{ version 2.0; format ascii; class volScalarField; object k; }}
        dimensions [0 2 -2 0 0 0 0]; internalField uniform {k_val};
        boundaryField {{ ".*inlet.*" {{ type fixedValue; value uniform {k_val}; }} ".*outlet.*" {{ type zeroGradient; }} walls {{ type kqRWallFunction; value uniform {k_val}; }} frontAndBack {{ type empty; }} }}
    """)
    write_foam_file(os.path.join(run_dir, "0", "epsilon"), f"""\
        FoamFile {{ version 2.0; format ascii; class volScalarField; object epsilon; }}
        dimensions [0 2 -3 0 0 0 0]; internalField uniform {eps_val};
        boundaryField {{ ".*inlet.*" {{ type fixedValue; value uniform {eps_val}; }} ".*outlet.*" {{ type zeroGradient; }} walls {{ type epsilonWallFunction; value uniform {eps_val}; }} frontAndBack {{ type empty; }} }}
    """)
    write_foam_file(os.path.join(run_dir, "0", "nut"), """\
        FoamFile { version 2.0; format ascii; class volScalarField; object nut; }
        dimensions [0 2 -1 0 0 0 0]; internalField uniform 0;
        boundaryField { ".*inlet.*" { type calculated; value uniform 0; } ".*outlet.*" { type calculated; value uniform 0; } walls { type nutkWallFunction; value uniform 0; } frontAndBack { type empty; } }
    """)

def run_case(params):
    # Unpack parameters
    shape_key, L, D, Ux, ref, unique_id = params
    
    # Generate random shape-specific parameters on the fly
    shape_params = get_random_shape_params(shape_key)
    
    case_name = f"{shape_key}_{unique_id}"
    run_dir = os.path.join("temp_runs", case_name)
    output_path = os.path.join(OUTPUT_DIR, f"{case_name}.npz")

    if os.path.exists(output_path): return None

    try:
        if os.path.exists(run_dir): shutil.rmtree(run_dir)
        shutil.copytree(TEMPLATE_DIR, run_dir)
        
        generate_case_files(run_dir, shape_key, L, D, ref, Ux, shape_params)
        
        # Execute OpenFOAM
        subprocess.run(["blockMesh"], cwd=run_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["simpleFoam"], cwd=run_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Extract Data
        touch_file = os.path.join(run_dir, "case.foam")
        open(touch_file, 'a').close()
        reader = pv.POpenFOAMReader(touch_file)
        reader.set_active_time_value(reader.time_values[-1])
        data = reader.read()
        internal = data["internalMesh"]
        
        # Helper for fields
        def get_f(name, dim):
            if name in internal.array_names: return internal[name]
            return np.zeros((internal.n_cells,) + dim)

        # Save Data + Metadata (Include the random parameters!)
        np.savez_compressed(
            output_path,
            shape_name=shape_key,
            L=L, D=D, Ux=Ux, 
            pos=internal.cell_centers().points,
            U=get_f("U", (3,)),
            p=get_f("p", ()),
            k=get_f("k", ()),
            epsilon=get_f("epsilon", ()),
            # Save the specific shape params used so you know ground truth for training
            **shape_params 
        )
        return None

    except Exception as e:
        return f"Err: {case_name} - {str(e)}"
    finally:
        if os.path.exists(run_dir): shutil.rmtree(run_dir)

if __name__ == "__main__":
    if not os.path.exists("shapes"):
        print("Run setup_shapes.py first!")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("temp_runs", exist_ok=True)
    
    # Create the Task List
    tasks = []
    ctr = 0
    
    # Loop 1: Grid Search for Global Variables
    base_combinations = list(itertools.product(LENGTHS, DIAMETERS, VELOCITIES, REFINEMENTS))
    
    # Loop 2: Random Sampling for Shape Specifics
    for shape in SHAPE_HANDLERS.keys():
        # Pick N random global combinations for this shape
        # Or iterate all globals? Let's just do SAMPLES_PER_SHAPE total to save time
        
        for _ in range(SAMPLES_PER_SHAPE):
            L, D, U, Ref = random.choice(base_combinations)
            tasks.append((shape, L, D, U, Ref, ctr))
            ctr += 1
            
    print(f"Queue: {len(tasks)} simulations on {N_CORES} cores.")
    
    with Pool(N_CORES) as pool:
        for i, res in enumerate(pool.imap_unordered(run_case, tasks)):
            pct = ((i+1)/len(tasks))*100
            sys.stdout.write(f"\r[{pct:.1f}%] Completed. {res if res else ''}")
            sys.stdout.flush()
            
    print("\nData generation complete.")