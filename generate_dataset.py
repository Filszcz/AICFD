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
from scipy.spatial import cKDTree  # Efficient distance calculation

# Import your shape generators
import shapes.straight, shapes.bend, shapes.valve, shapes.obstacle
import shapes.venturi, shapes.manifold

# --- Configuration ---
TEMPLATE_DIR = "base_template"
OUTPUT_DIR = "data_output"
N_CORES = 10
SAMPLES_PER_SHAPE = 4 

LENGTHS = [5.0]
DIAMETERS = [0.25]
VELOCITIES = [0.5]
REFINEMENTS = [2, 4, 6, 8] 

BASE_CELL_SIZE = 0.05 

SHAPE_HANDLERS = {
    "straight": shapes.straight.generate,
    "bend": shapes.bend.generate,
    "valve": shapes.valve.generate,
    "obstacle": shapes.obstacle.generate,
    "venturi": shapes.venturi.generate,
    "manifold": shapes.manifold.generate
}

def get_random_params(shape_name):
    p = {}
    if shape_name == "valve":
        p["valve_opening"] = round(random.uniform(0.15, 0.85), 2)
        p["valve_thickness"] = round(random.uniform(0.1, 0.5), 2)
    elif shape_name == "obstacle":
        p["obs_size"] = round(random.uniform(0.2, 0.5), 2)
        p["obs_offset"] = round(random.uniform(-0.25, 0.25), 2)
    elif shape_name == "venturi":
        p["throat_ratio"] = round(random.uniform(0.3, 0.7), 2)
        p["conv_len_ratio"] = round(random.uniform(0.15, 0.35), 2)
        p["div_len_ratio"] = round(random.uniform(0.3, 0.6), 2)
    elif shape_name == "bend":
        p["bend_angle"] = random.choice([45, 90])
        p["bend_radius"] = round(random.uniform(1.0, 2.5), 2)
    elif shape_name == "manifold":
        p["branch_width_ratio"] = round(random.uniform(0.5, 0.9), 2)
        p["branch_height_ratio"] = round(random.uniform(1.5, 3.0), 2)
        
    p["nu_val"] = round(random.uniform(0.8e-6, 1.3e-6), 9)
    p["turb_intensity"] = round(random.uniform(0.01, 0.15), 3)
    return p

def write_foam_file(path, content):
    with open(path, "w") as f:
        f.write(textwrap.dedent(content))

def generate_case_files(run_dir, shape_key, L, D, ref, Ux, params):
    os.makedirs(os.path.join(run_dir, "0"), exist_ok=True)
    os.makedirs(os.path.join(run_dir, "constant"), exist_ok=True)
    
    current_cell_size = BASE_CELL_SIZE / (1.5 ** ref)
    
    generator = SHAPE_HANDLERS[shape_key]
    bm_content = generator(L, D, current_cell_size, **params)
        
    write_foam_file(os.path.join(run_dir, "system", "blockMeshDict"), f"""\
        FoamFile {{ version 2.0; format ascii; class dictionary; object blockMeshDict; }}
        convertToMeters 1;
        {bm_content}
    """)
    
    nu = params["nu_val"]
    write_foam_file(os.path.join(run_dir, "constant", "transportProperties"), f"""\
        FoamFile {{ version 2.0; format ascii; class dictionary; object transportProperties; }}
        transportModel Newtonian;
        nu [0 2 -1 0 0 0 0] {nu};
    """)

    turb_int = params["turb_intensity"]
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

def get_patch_one_hot(name):
    name = name.lower()
    if "inlet" in name: return [0, 1, 0] # [Wall, Inlet, Outlet]
    if "outlet" in name: return [0, 0, 1]
    return [1, 0, 0] # Wall

def run_case(p):
    shape_key, L, D, Ux, ref, unique_id = p
    case_params = get_random_params(shape_key)
    case_name = f"{shape_key}_{unique_id}"
    run_dir = os.path.join("temp_runs", case_name)
    # CHANGED: Extension from .npz to .npy
    output_path = os.path.join(OUTPUT_DIR, f"{case_name}.npy")

    if os.path.exists(output_path): return None

    try:
        if os.path.exists(run_dir): shutil.rmtree(run_dir)
        shutil.copytree(TEMPLATE_DIR, run_dir)
        
        generate_case_files(run_dir, shape_key, L, D, ref, Ux, case_params)
        
        # Run OpenFOAM
        subprocess.run(["blockMesh"], cwd=run_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["simpleFoam"], cwd=run_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Read Data
        touch_file = os.path.join(run_dir, "case.foam")
        open(touch_file, 'a').close()
        reader = pv.POpenFOAMReader(touch_file)
        reader.set_active_time_value(reader.time_values[-1])
        data = reader.read()
        
        # --- PREPARE FOR WALL DISTANCE CALCULATION ---
        wall_points = []
        if "boundary" in data.keys():
            boundaries = data["boundary"]
            for i in range(boundaries.n_blocks):
                name = boundaries.get_block_name(i)
                if name is None or "frontAndBack" in name or "empty" in name.lower(): continue
                
                # Check if it's a wall type (not inlet/outlet)
                is_wall = ("walls" in name.lower()) or ("cylinder" in name.lower())
                
                # If explicit "walls" patch, OR if generic patch that isn't inlet/outlet
                if is_wall or ("inlet" not in name.lower() and "outlet" not in name.lower()):
                    patch = boundaries[i]
                    if patch.n_cells > 0:
                        wall_points.append(patch.cell_centers().points)
        
        # Build KDTree for Walls
        kdtree = None
        if wall_points:
            all_wall_pts = np.vstack(wall_points)
            kdtree = cKDTree(all_wall_pts)

        # --- EXTRACT DATA ---
        internal = data["internalMesh"]
        n_fluid = internal.n_cells
        f_pos = internal.cell_centers().points
        
        if "U" in internal.array_names: f_U = internal["U"]
        else: f_U = np.zeros((n_fluid, 3))
            
        if "p" in internal.array_names: f_p = internal["p"]
        else: f_p = np.zeros(n_fluid)
        
        # CALCULATE Y_WALL manually using KDTree
        if kdtree:
            f_ywall, _ = kdtree.query(f_pos)
        else:
            f_ywall = np.zeros(n_fluid)
        
        f_flags = np.tile([1, 0, 0, 0], (n_fluid, 1))
        
        fluid_data = np.column_stack((f_pos, f_U, f_p, f_ywall, f_flags))

        # Boundary Data
        boundary_data_list = []
        if "boundary" in data.keys():
            boundaries = data["boundary"]
            for i in range(boundaries.n_blocks):
                name = boundaries.get_block_name(i)
                if name is None or "frontAndBack" in name or "empty" in name.lower(): continue
                patch = boundaries[i]
                if patch.n_cells == 0: continue
                
                n_b = patch.n_cells
                b_pos = patch.cell_centers().points
                
                if "U" in patch.array_names: b_U = patch["U"]
                else: b_U = np.zeros((n_b, 3))
                
                if "p" in patch.array_names: b_p = patch["p"]
                else: b_p = np.zeros(n_b)
                
                # Wall distance at boundary is 0 (approx)
                b_ywall = np.zeros(n_b) 
                
                type_flags = get_patch_one_hot(name)
                b_flags = np.tile([0] + type_flags, (n_b, 1))
                
                b_chunk = np.column_stack((b_pos, b_U, b_p, b_ywall, b_flags))
                boundary_data_list.append(b_chunk)

        if boundary_data_list:
            all_data = np.vstack([fluid_data] + boundary_data_list)
        else:
            all_data = fluid_data

        # CHANGED: Wrap data in a dictionary and use np.save
        save_payload = {
            "data": all_data,
            "shape_name": shape_key,
            "params": case_params
        }
        np.save(output_path, save_payload)
        
        return None

    except subprocess.CalledProcessError as e:
        return f"Err: {case_name} - CMD {e.cmd[0]} failed"
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
    
    tasks = []
    ctr = 0
    base_combos = list(itertools.product(LENGTHS, DIAMETERS, VELOCITIES, REFINEMENTS))
    
    for shape in SHAPE_HANDLERS.keys():
        for _ in range(SAMPLES_PER_SHAPE):
            L, D, U, Ref = random.choice(base_combos)
            tasks.append((shape, L, D, U, Ref, ctr))
            ctr += 1
            
    print(f"Starting {len(tasks)} simulations on {N_CORES} cores.")
    
    with Pool(N_CORES) as pool:
        for i, res in enumerate(pool.imap_unordered(run_case, tasks)):
            if res: print(res)
            pct = ((i+1)/len(tasks))*100
            sys.stdout.write(f"\rProgress: {pct:.1f}%")
            sys.stdout.flush()
            
    print("\nComplete.")