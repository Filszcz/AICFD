# import os
# import shutil
# import numpy as np
# import subprocess
# import itertools
# from multiprocessing import Pool
# import pyvista as pv
# import time
# import textwrap

# # --- Configuration ---
# TEMPLATE_DIR = "base_template"
# OUTPUT_DIR = "data_output"
# N_CORES = 22
# DL_RESOLUTION = (128, 32, 1)

# # Parameter Ranges
# lengths = np.linspace(3, 50, 25)
# diameters = np.linspace(0.25, 2, 25)
# velocities = np.linspace(0.25, 5, 25)
# refinements = [0, 1, 2, 3, 4] 

# TURB_INTENSITY = 0.05
# C_MU = 0.09

# def write_foam_file(path, content):
#     with open(path, "w") as f:
#         f.write(textwrap.dedent(content))

# def generate_case_files(run_dir, L, D, ref_level, Ux):
#     # 1. fvSchemes (Enforces meshWave)
#     write_foam_file(os.path.join(run_dir, "system", "fvSchemes"), """\
#         FoamFile
#         {
#             version     2.0;
#             format      ascii;
#             class       dictionary;
#             object      fvSchemes;
#         }
        
#         ddtSchemes { default steadyState; }
#         gradSchemes { default Gauss linear; }
#         divSchemes
#         {
#             default         none;
#             div(phi,U)      bounded Gauss linearUpwind grad(U);
#             div(phi,k)      bounded Gauss upwind;
#             div(phi,epsilon) bounded Gauss upwind;
#             div(phi,omega)  bounded Gauss upwind;
#             div((nuEff*dev2(T(grad(U))))) Gauss linear;
#         }
#         laplacianSchemes { default Gauss linear corrected; }
#         interpolationSchemes { default linear; }
#         snGradSchemes { default corrected; }
        
#         wallDist
#         {
#             method          meshWave;
#             correctWalls    true;
#         }
#     """)

#     # 2. BlockMesh
#     dens_mult = [1.0, 1.25, 1.5, 1.75, 2.0][ref_level]
#     r, z = D / 2.0, 0.05
#     y_cells = int(20 * dens_mult)
#     x_cells = int((L / D * 20) * dens_mult)
#     if y_cells % 2 != 0: y_cells += 1
    
#     write_foam_file(os.path.join(run_dir, "system", "blockMeshDict"), f"""\
#         FoamFile
#         {{
#             version     2.0;
#             format      ascii;
#             class       dictionary;
#             object      blockMeshDict;
#         }}
        
#         convertToMeters 1;
#         vertices
#         (
#             (0 {-r} {-z}) ({L} {-r} {-z}) ({L} {r} {-z}) (0 {r} {-z})
#             (0 {-r} {z}) ({L} {-r} {z}) ({L} {r} {z}) (0 {r} {z})
#         );
#         blocks ( hex (0 1 2 3 4 5 6 7) ({x_cells} {y_cells} 1) simpleGrading (1 1 1) );
#         edges ();
#         boundary
#         (
#             inlet  {{ type patch; faces ((0 4 7 3)); }}
#             outlet {{ type patch; faces ((1 2 6 5)); }}
#             walls  {{ type wall;  faces ((0 1 5 4) (3 7 6 2)); }}
#             frontAndBack {{ type empty; faces ((0 3 2 1) (4 5 6 7)); }}
#         );
#         mergePatchPairs ();
#     """)

#     # 3. ControlDict
#     write_foam_file(os.path.join(run_dir, "system", "controlDict"), """\
#         FoamFile
#         {
#             version     2.0;
#             format      ascii;
#             class       dictionary;
#             object      controlDict;
#         }
        
#         application     simpleFoam;
#         startFrom       latestTime;
#         startTime       0;
#         stopAt          endTime;
#         endTime         2000;
#         deltaT          1;
#         writeControl    runTime;
#         writeInterval   2000;
#         purgeWrite      1;
#         writeFormat     binary;
#         writePrecision  6;
#         writeCompression off;
#         timeFormat      general;
#         timePrecision   6;
#         runTimeModifiable true;
        
#         functions {}
#     """)
    
#     # 4. Physics
#     k_val = max(1.5 * (Ux * TURB_INTENSITY)**2, 1e-8)
#     l_mix = 0.07 * D
#     eps_val = max((C_MU**0.75 * k_val**1.5) / l_mix, 1e-8)

#     write_foam_file(os.path.join(run_dir, "0", "p"), """\
#         FoamFile { version 2.0; format ascii; class volScalarField; object p; }
#         dimensions [0 2 -2 0 0 0 0]; internalField uniform 0;
#         boundaryField { inlet { type zeroGradient; } outlet { type fixedValue; value uniform 0; } walls { type zeroGradient; } frontAndBack { type empty; } }
#     """)
#     write_foam_file(os.path.join(run_dir, "0", "nut"), """\
#         FoamFile { version 2.0; format ascii; class volScalarField; object nut; }
#         dimensions [0 2 -1 0 0 0 0]; internalField uniform 0;
#         boundaryField { inlet { type calculated; value uniform 0; } outlet { type calculated; value uniform 0; } walls { type nutkWallFunction; value uniform 0; } frontAndBack { type empty; } }
#     """)
    
#     write_foam_file(os.path.join(run_dir, "0", "U"), f"""\
#         FoamFile {{ version 2.0; format ascii; class volVectorField; object U; }}
#         dimensions [0 1 -1 0 0 0 0]; internalField uniform ({Ux} 0 0);
#         boundaryField {{ inlet {{ type fixedValue; value uniform ({Ux} 0 0); }} outlet {{ type zeroGradient; }} walls {{ type noSlip; }} frontAndBack {{ type empty; }} }}
#     """)
#     write_foam_file(os.path.join(run_dir, "0", "k"), f"""\
#         FoamFile {{ version 2.0; format ascii; class volScalarField; object k; }}
#         dimensions [0 2 -2 0 0 0 0]; internalField uniform {k_val};
#         boundaryField {{ inlet {{ type fixedValue; value uniform {k_val}; }} outlet {{ type zeroGradient; }} walls {{ type kqRWallFunction; value uniform {k_val}; }} frontAndBack {{ type empty; }} }}
#     """)
#     write_foam_file(os.path.join(run_dir, "0", "epsilon"), f"""\
#         FoamFile {{ version 2.0; format ascii; class volScalarField; object epsilon; }}
#         dimensions [0 2 -3 0 0 0 0]; internalField uniform {eps_val};
#         boundaryField {{ inlet {{ type fixedValue; value uniform {eps_val}; }} outlet {{ type zeroGradient; }} walls {{ type epsilonWallFunction; value uniform {eps_val}; }} frontAndBack {{ type empty; }} }}
#     """)

# def run_case(params):
#     L, D, Ux, ref, case_id = params
#     case_name = f"case_{case_id}"
#     run_dir = os.path.join(os.getcwd(), "temp_runs", case_name)
#     output_path = os.path.join(OUTPUT_DIR, f"sim_L{L:.2f}_D{D:.2f}_U{Ux:.2f}_Ref{ref}.npz")

#     if os.path.exists(output_path): return None

#     try:
#         if os.path.exists(run_dir): shutil.rmtree(run_dir)
#         shutil.copytree(TEMPLATE_DIR, run_dir)
        
#         generate_case_files(run_dir, L, D, ref, Ux)
        
#         # 1. Mesh
#         subprocess.run(["blockMesh"], cwd=run_dir, check=True, capture_output=True, text=True)
        
#         # 2. Append yPlus function
#         with open(os.path.join(run_dir, "system", "controlDict"), "r+") as f:
#             content = f.read()
#             f.seek(0)
#             f.write(content.replace("functions {}", """
#             functions
#             {
#                 yPlus1
#                 {
#                     type            yPlus;
#                     libs            ("libfieldFunctionObjects.so");
#                     executeControl  writeTime;
#                     writeControl    writeTime;
#                 }
#             }
#             """))

#         # 3. Solver
#         subprocess.run(["simpleFoam"], cwd=run_dir, check=True, capture_output=True, text=True)
        
#         # 4. Extract
#         touch_file = os.path.join(run_dir, "case.foam")
#         open(touch_file, 'a').close()
#         reader = pv.POpenFOAMReader(touch_file)
#         reader.set_active_time_value(reader.time_values[-1])
#         mesh = reader.read()["internalMesh"]
        
#         x_r = np.linspace(0, L, DL_RESOLUTION[0])
#         y_r = np.linspace(-D/2, D/2, DL_RESOLUTION[1])
#         z_r = np.array([0])
#         grid = pv.StructuredGrid(*np.meshgrid(x_r, y_r, z_r, indexing='ij'))
#         sampled = grid.sample(mesh)
        
#         # Extract y (Standard OpenFOAM writes 'y' when running yPlus)
#         # If 'y' is missing, fallback to geometric calculation
#         if "y" in sampled.array_names:
#             y_arr = sampled["y"]
#         elif "yPlus" in sampled.array_names:
#              # Fallback: Approximate wall distance geometrically if meshWave data isn't exposed
#              # (This ensures the dataset isn't empty on version mismatches)
#              points = sampled.points
#              y_coords = points[:, 1]
#              y_arr = (D/2.0) - np.abs(y_coords)
#         else:
#              y_arr = np.zeros(mesh.n_points)

#         np.savez_compressed(
#             output_path, L=L, D=D, Ux_in=Ux, Ref=ref,
#             U=sampled["U"].reshape(*DL_RESOLUTION[:2], 3),
#             p=sampled["p"].reshape(*DL_RESOLUTION),
#             k=sampled["k"].reshape(*DL_RESOLUTION),
#             epsilon=sampled["epsilon"].reshape(*DL_RESOLUTION),
#             y=y_arr.reshape(*DL_RESOLUTION)
#         )
#         return f"Done: {case_name}"

#     except subprocess.CalledProcessError as e:
#         return f"Fail: {case_name} [CMD: {e.cmd[0]}]"
#     except Exception as e:
#         return f"Fail: {case_name} [PY: {str(e)}]"
#     finally:
#         if os.path.exists(run_dir): shutil.rmtree(run_dir)

# if __name__ == "__main__":
#     os.makedirs(OUTPUT_DIR, exist_ok=True)
#     os.makedirs("temp_runs", exist_ok=True)
    
#     case_params = list(itertools.product(lengths, diameters, velocities, refinements))
#     tasks = [(*p, i) for i, p in enumerate(case_params)]
    
#     print(f"Starting {len(tasks)} cases on {N_CORES} cores...")
#     start_time = time.time()
    
#     with Pool(processes=N_CORES) as pool:
#         for i, res in enumerate(pool.imap_unordered(run_case, tasks)):
#             if res and "Fail" in res: print(res)
#             if i % 100 == 0:
#                 elapsed = time.time() - start_time
#                 rate = (i+1) / max(elapsed, 1e-3)
#                 print(f"[{i}/{len(tasks)}] Rate: {rate:.2f} cases/s")




import os
import shutil
import numpy as np
import subprocess
import itertools
from multiprocessing import Pool
import pyvista as pv
import time
import textwrap

# --- Configuration ---
TEMPLATE_DIR = "base_template"
OUTPUT_DIR = "data_output"
N_CORES = 22
# INCREASED RESOLUTION: 256x64
DL_RESOLUTION = (256, 64, 1)

# Parameter Ranges
lengths = np.linspace(3, 50, 25)
diameters = np.linspace(0.25, 2, 25)
velocities = np.linspace(0.25, 5, 25)
refinements = [0, 1, 2, 3, 4] 

TURB_INTENSITY = 0.05
C_MU = 0.09

def write_foam_file(path, content):
    with open(path, "w") as f:
        f.write(textwrap.dedent(content))

def generate_case_files(run_dir, L, D, ref_level, Ux):
    # 1. fvSchemes
    write_foam_file(os.path.join(run_dir, "system", "fvSchemes"), """\
        FoamFile
        {
            version     2.0;
            format      ascii;
            class       dictionary;
            object      fvSchemes;
        }
        
        ddtSchemes { default steadyState; }
        gradSchemes { default Gauss linear; }
        divSchemes
        {
            default         none;
            div(phi,U)      bounded Gauss linearUpwind grad(U);
            div(phi,k)      bounded Gauss upwind;
            div(phi,epsilon) bounded Gauss upwind;
            div(phi,omega)  bounded Gauss upwind;
            div((nuEff*dev2(T(grad(U))))) Gauss linear;
        }
        laplacianSchemes { default Gauss linear corrected; }
        interpolationSchemes { default linear; }
        snGradSchemes { default corrected; }
        
        wallDist
        {
            method          meshWave;
            correctWalls    true;
        }
    """)

    # 2. BlockMesh with Boundary Layer Grading
    # Dens Mult: 1.0 -> 2.0
    dens_mult = [1.0, 1.25, 1.5, 1.75, 2.0][ref_level]
    
    r, z = D / 2.0, 0.05
    
    # Base Resolution adjusted for higher fidelity
    # Y: 40 cells base (was 20) -> goes up to 80
    y_cells = int(40 * dens_mult) 
    x_cells = int((L / D * 20) * dens_mult)
    if y_cells % 2 != 0: y_cells += 1
    
    # Grading Logic:
    # We want cells near walls to be smaller.
    # In Y-direction: ((0.5 0.5 10) (0.5 0.5 0.1))
    # Explanation: 
    #   First 50% of length (0.5), contains 50% of cells (0.5), expansion ratio 10 (Start small, end big)
    #   Second 50% of length (0.5), contains 50% of cells (0.5), expansion ratio 0.1 (Start big, end small)
    # This creates a symmetric grading: Fine -> Coarse -> Fine
    grading_y = "((0.5 0.5 10) (0.5 0.5 0.1))"
    
    write_foam_file(os.path.join(run_dir, "system", "blockMeshDict"), f"""\
        FoamFile
        {{
            version     2.0;
            format      ascii;
            class       dictionary;
            object      blockMeshDict;
        }}
        
        convertToMeters 1;
        vertices
        (
            (0 {-r} {-z}) ({L} {-r} {-z}) ({L} {r} {-z}) (0 {r} {-z})
            (0 {-r} {z}) ({L} {-r} {z}) ({L} {r} {z}) (0 {r} {z})
        );
        blocks
        (
            // hex (pts) (cells) simpleGrading (x y z)
            hex (0 1 2 3 4 5 6 7) ({x_cells} {y_cells} 1) simpleGrading (1 {grading_y} 1)
        );
        edges ();
        boundary
        (
            inlet  {{ type patch; faces ((0 4 7 3)); }}
            outlet {{ type patch; faces ((1 2 6 5)); }}
            walls  {{ type wall;  faces ((0 1 5 4) (3 7 6 2)); }}
            frontAndBack {{ type empty; faces ((0 3 2 1) (4 5 6 7)); }}
        );
        mergePatchPairs ();
    """)

    # 3. ControlDict
    write_foam_file(os.path.join(run_dir, "system", "controlDict"), """\
        FoamFile
        {
            version     2.0;
            format      ascii;
            class       dictionary;
            object      controlDict;
        }
        
        application     simpleFoam;
        startFrom       latestTime;
        startTime       0;
        stopAt          endTime;
        endTime         2000;
        deltaT          1;
        writeControl    runTime;
        writeInterval   2000;
        purgeWrite      1;
        writeFormat     binary;
        writePrecision  6;
        writeCompression off;
        timeFormat      general;
        timePrecision   6;
        runTimeModifiable true;
        
        functions {}
    """)
    
    # 4. Physics
    k_val = max(1.5 * (Ux * TURB_INTENSITY)**2, 1e-8)
    l_mix = 0.07 * D
    eps_val = max((C_MU**0.75 * k_val**1.5) / l_mix, 1e-8)

    write_foam_file(os.path.join(run_dir, "0", "p"), """\
        FoamFile { version 2.0; format ascii; class volScalarField; object p; }
        dimensions [0 2 -2 0 0 0 0]; internalField uniform 0;
        boundaryField { inlet { type zeroGradient; } outlet { type fixedValue; value uniform 0; } walls { type zeroGradient; } frontAndBack { type empty; } }
    """)
    write_foam_file(os.path.join(run_dir, "0", "nut"), """\
        FoamFile { version 2.0; format ascii; class volScalarField; object nut; }
        dimensions [0 2 -1 0 0 0 0]; internalField uniform 0;
        boundaryField { inlet { type calculated; value uniform 0; } outlet { type calculated; value uniform 0; } walls { type nutkWallFunction; value uniform 0; } frontAndBack { type empty; } }
    """)
    
    write_foam_file(os.path.join(run_dir, "0", "U"), f"""\
        FoamFile {{ version 2.0; format ascii; class volVectorField; object U; }}
        dimensions [0 1 -1 0 0 0 0]; internalField uniform ({Ux} 0 0);
        boundaryField {{ inlet {{ type fixedValue; value uniform ({Ux} 0 0); }} outlet {{ type zeroGradient; }} walls {{ type noSlip; }} frontAndBack {{ type empty; }} }}
    """)
    write_foam_file(os.path.join(run_dir, "0", "k"), f"""\
        FoamFile {{ version 2.0; format ascii; class volScalarField; object k; }}
        dimensions [0 2 -2 0 0 0 0]; internalField uniform {k_val};
        boundaryField {{ inlet {{ type fixedValue; value uniform {k_val}; }} outlet {{ type zeroGradient; }} walls {{ type kqRWallFunction; value uniform {k_val}; }} frontAndBack {{ type empty; }} }}
    """)
    write_foam_file(os.path.join(run_dir, "0", "epsilon"), f"""\
        FoamFile {{ version 2.0; format ascii; class volScalarField; object epsilon; }}
        dimensions [0 2 -3 0 0 0 0]; internalField uniform {eps_val};
        boundaryField {{ inlet {{ type fixedValue; value uniform {eps_val}; }} outlet {{ type zeroGradient; }} walls {{ type epsilonWallFunction; value uniform {eps_val}; }} frontAndBack {{ type empty; }} }}
    """)

def run_case(params):
    L, D, Ux, ref, case_id = params
    case_name = f"case_{case_id}"
    run_dir = os.path.join(os.getcwd(), "temp_runs", case_name)
    output_path = os.path.join(OUTPUT_DIR, f"sim_L{L:.2f}_D{D:.2f}_U{Ux:.2f}_Ref{ref}.npz")

    if os.path.exists(output_path): return None

    try:
        if os.path.exists(run_dir): shutil.rmtree(run_dir)
        shutil.copytree(TEMPLATE_DIR, run_dir)
        
        generate_case_files(run_dir, L, D, ref, Ux)
        
        # 1. Mesh
        subprocess.run(["blockMesh"], cwd=run_dir, check=True, capture_output=True, text=True)
        
        # 2. Append yPlus function
        with open(os.path.join(run_dir, "system", "controlDict"), "r+") as f:
            content = f.read()
            f.seek(0)
            f.write(content.replace("functions {}", """
            functions
            {
                yPlus1
                {
                    type            yPlus;
                    libs            ("libfieldFunctionObjects.so");
                    executeControl  writeTime;
                    writeControl    writeTime;
                }
            }
            """))

        # 3. Solver
        subprocess.run(["simpleFoam"], cwd=run_dir, check=True, capture_output=True, text=True)
        
        # 4. Extract
        touch_file = os.path.join(run_dir, "case.foam")
        open(touch_file, 'a').close()
        reader = pv.POpenFOAMReader(touch_file)
        reader.set_active_time_value(reader.time_values[-1])
        mesh = reader.read()["internalMesh"]
        
        x_r = np.linspace(0, L, DL_RESOLUTION[0])
        y_r = np.linspace(-D/2, D/2, DL_RESOLUTION[1])
        z_r = np.array([0])
        grid = pv.StructuredGrid(*np.meshgrid(x_r, y_r, z_r, indexing='ij'))
        sampled = grid.sample(mesh)
        
        # Check field names
        if "y" in sampled.array_names:
            y_arr = sampled["y"]
        elif "yPlus" in sampled.array_names:
             points = sampled.points
             y_coords = points[:, 1]
             y_arr = (D/2.0) - np.abs(y_coords)
        else:
             y_arr = np.zeros(mesh.n_points)

        np.savez_compressed(
            output_path, L=L, D=D, Ux_in=Ux, Ref=ref,
            U=sampled["U"].reshape(*DL_RESOLUTION[:2], 3),
            p=sampled["p"].reshape(*DL_RESOLUTION),
            k=sampled["k"].reshape(*DL_RESOLUTION),
            epsilon=sampled["epsilon"].reshape(*DL_RESOLUTION),
            y=y_arr.reshape(*DL_RESOLUTION)
        )
        return f"Done: {case_name}"

    except subprocess.CalledProcessError as e:
        return f"Fail: {case_name} [CMD: {e.cmd[0]}]"
    except Exception as e:
        return f"Fail: {case_name} [PY: {str(e)}]"
    finally:
        if os.path.exists(run_dir): shutil.rmtree(run_dir)

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("temp_runs", exist_ok=True)
    
    case_params = list(itertools.product(lengths, diameters, velocities, refinements))
    tasks = [(*p, i) for i, p in enumerate(case_params)]
    
    print(f"Starting {len(tasks)} cases on {N_CORES} cores...")
    print(f"High-Res Mode: {DL_RESOLUTION} | Wall Grading Active")
    start_time = time.time()
    
    with Pool(processes=N_CORES) as pool:
        for i, res in enumerate(pool.imap_unordered(run_case, tasks)):
            if res and "Fail" in res: print(res)
            if i % 100 == 0:
                elapsed = time.time() - start_time
                rate = (i+1) / max(elapsed, 1e-3)
                print(f"[{i}/{len(tasks)}] Rate: {rate:.2f} cases/s")