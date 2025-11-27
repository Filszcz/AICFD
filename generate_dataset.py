import os
import shutil
import numpy as np
import subprocess
import itertools
from multiprocessing import Pool
import pyvista as pv
import time
import textwrap
import math
import sys

# THE T INLETS AND OUTLETS ARE IN THE WRONG PLACES, WILL FIX LATER!!!!

# --- Configuration ---
TEMPLATE_DIR = "base_template"
OUTPUT_DIR = "data_output"
N_CORES = 10

# Parameter Ranges
lengths = np.linspace(5, 10, 2) 
diameters = np.linspace(0.5, 2.0, 2)
velocities = np.linspace(1, 3, 2)
refinements = [0, 2] 

# Shapes:
# straight:   Pipe
# bend:       90 deg turn (Down)
# bend45:     45 deg turn (Down-Right)
# tee_split:  Inlet Left -> Outlet Right & Top
# tee_opposed: Inlet Left & Right -> Outlet Top
# taper_in:   Constriction
# taper_out:  Expansion
SHAPES = ["straight", "bend", "bend45", "tee_split", "tee_opposed", "taper_in", "taper_out"]


TURB_INTENSITY = 0.05
C_MU = 0.09

def write_foam_file(path, content):
    with open(path, "w") as f:
        f.write(textwrap.dedent(content))

def get_patch_type_encoding(name):
    name = name.lower()
    if "inlet" in name: return [0, 0, 1, 0]
    if "outlet" in name: return [0, 0, 0, 1]
    return [0, 1, 0, 0]

# --- GEOMETRY GENERATORS ---

def get_blockmesh_straight(L, D, dens_mult):
    r, z = D / 2.0, 0.05
    base_y = int(20 * dens_mult)
    if base_y % 2 != 0: base_y += 1
    # Maintain aspect ratio of cell ~ 1:1
    # Cell size = D / base_y
    # x_cells = L / (D/base_y) = (L/D) * base_y
    x_cells = int((L / D) * base_y)
    
    return f"""
        vertices
        (
            (0 {-r} {-z}) ({L} {-r} {-z}) ({L} {r} {-z}) (0 {r} {-z})
            (0 {-r} {z}) ({L} {-r} {z}) ({L} {r} {z}) (0 {r} {z})
        );
        blocks ( hex (0 1 2 3 4 5 6 7) ({x_cells} {base_y} 1) simpleGrading (1 1 1) );
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

def get_blockmesh_bend(L, D, dens_mult):
    # 90 Degree Bend (Downwards -Y)
    r, z = D / 2.0, 0.05
    R_inner, R_outer = D, 2.0*D
    R_mid = 1.5 * D
    
    base_cells = int(20 * dens_mult)
    if base_cells % 2 != 0: base_cells += 1
    
    # Linear sections
    l_cells = int((L / D) * base_cells)
    
    # Arc Section density
    # Arc Length = R_mid * pi/2
    # Cell size target = D / base_cells
    # Arc Cells = (R_mid * pi/2) / (D/base_cells) = 1.5 * 1.57 * base_cells ~ 2.35 * base_cells
    arc_cells = int(2.4 * base_cells)

    cx, cy = L, -r - R_inner
    
    # Plane 2 (End of Turn) - Horizontal line at y = cy
    p2_in_x, p2_in_y = cx + R_inner, cy
    p2_out_x, p2_out_y = cx + R_outer, cy
    
    # Plane 3 (End of Leg)
    p3_in_x, p3_in_y = p2_in_x, p2_in_y - L
    p3_out_x, p3_out_y = p2_out_x, p2_out_y - L
    
    # Arc Midpoints
    theta = math.radians(45)
    m_in_x = cx + R_inner * math.sin(theta)
    m_in_y = cy + R_inner * math.cos(theta)
    m_out_x = cx + R_outer * math.sin(theta)
    m_out_y = cy + R_outer * math.cos(theta)

    return f"""
        vertices
        (
            (0 {-r} {-z}) ({L} {-r} {-z}) ({L} {r} {-z}) (0 {r} {-z})
            (0 {-r} {z})  ({L} {-r} {z})  ({L} {r} {z})  (0 {r} {z})
            ({p2_in_x} {p2_in_y} {-z}) ({p2_out_x} {p2_out_y} {-z})
            ({p2_in_x} {p2_in_y} {z})  ({p2_out_x} {p2_out_y} {z})
            ({p3_in_x} {p3_in_y} {-z}) ({p3_out_x} {p3_out_y} {-z})
            ({p3_in_x} {p3_in_y} {z})  ({p3_out_x} {p3_out_y} {z})
        );
        blocks
        (
            hex (0 1 2 3 4 5 6 7) ({l_cells} {base_cells} 1) simpleGrading (1 1 1)
            hex (1 8 9 2 5 10 11 6) ({arc_cells} {base_cells} 1) simpleGrading (1 1 1)
            hex (8 12 13 9 10 14 15 11) ({l_cells} {base_cells} 1) simpleGrading (1 1 1)
        );
        edges
        (
            arc 1 8 ({m_in_x} {m_in_y} {-z})
            arc 5 10 ({m_in_x} {m_in_y} {z})
            arc 2 9 ({m_out_x} {m_out_y} {-z})
            arc 6 11 ({m_out_x} {m_out_y} {z})
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 4 7 3)); }}
            outlet {{ type patch; faces ((12 13 15 14)); }}
            walls  {{ type wall;  faces ((0 1 5 4) (3 7 6 2) (1 8 10 5) (9 2 6 11) (8 12 14 10) (13 9 11 15)); }}
            frontAndBack {{ type empty; faces ((0 3 2 1) (4 5 6 7) (1 2 9 8) (5 10 11 6) (8 9 13 12) (10 14 15 11)); }}
        );
        mergePatchPairs ();
    """

def get_blockmesh_bend45(L, D, dens_mult):
    r, z = D / 2.0, 0.05
    R_inner, R_outer = D, 2.0*D
    
    base_cells = int(20 * dens_mult)
    if base_cells % 2 != 0: base_cells += 1
    
    l_cells = int((L / D) * base_cells)
    
    # 45 deg arc = 0.5 * 90 deg arc
    arc_cells = int(1.2 * base_cells)
    
    sin45, cos45 = math.sin(math.radians(45)), math.cos(math.radians(45))
    cx, cy = L, -r - R_inner
    
    p2_in_x, p2_in_y = cx + R_inner * sin45, cy + R_inner * cos45
    p2_out_x, p2_out_y = cx + R_outer * sin45, cy + R_outer * cos45
    
    # Extrude downwards-right
    p3_in_x, p3_in_y = p2_in_x + L*cos45, p2_in_y - L*sin45
    p3_out_x, p3_out_y = p2_out_x + L*cos45, p2_out_y - L*sin45

    m_in_x = cx + R_inner * math.sin(math.radians(22.5))
    m_in_y = cy + R_inner * math.cos(math.radians(22.5))
    m_out_x = cx + R_outer * math.sin(math.radians(22.5))
    m_out_y = cy + R_outer * math.cos(math.radians(22.5))

    return f"""
        vertices
        (
            (0 {-r} {-z}) ({L} {-r} {-z}) ({L} {r} {-z}) (0 {r} {-z})
            (0 {-r} {z})  ({L} {-r} {z})  ({L} {r} {z})  (0 {r} {z})
            ({p2_in_x} {p2_in_y} {-z}) ({p2_out_x} {p2_out_y} {-z})
            ({p2_in_x} {p2_in_y} {z})  ({p2_out_x} {p2_out_y} {z})
            ({p3_in_x} {p3_in_y} {-z}) ({p3_out_x} {p3_out_y} {-z})
            ({p3_in_x} {p3_in_y} {z})  ({p3_out_x} {p3_out_y} {z})
        );
        blocks
        (
            hex (0 1 2 3 4 5 6 7) ({l_cells} {base_cells} 1) simpleGrading (1 1 1)
            hex (1 8 9 2 5 10 11 6) ({arc_cells} {base_cells} 1) simpleGrading (1 1 1)
            hex (8 12 13 9 10 14 15 11) ({l_cells} {base_cells} 1) simpleGrading (1 1 1)
        );
        edges
        (
            arc 1 8 ({m_in_x} {m_in_y} {-z})
            arc 5 10 ({m_in_x} {m_in_y} {z})
            arc 2 9 ({m_out_x} {m_out_y} {-z})
            arc 6 11 ({m_out_x} {m_out_y} {z})
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 4 7 3)); }}
            outlet {{ type patch; faces ((12 13 15 14)); }}
            walls  {{ type wall;  faces ((0 1 5 4) (3 7 6 2) (1 8 10 5) (9 2 6 11) (8 12 14 10) (13 9 11 15)); }}
            frontAndBack {{ type empty; faces ((0 3 2 1) (4 5 6 7) (1 2 9 8) (5 10 11 6) (8 9 13 12) (10 14 15 11)); }}
        );
        mergePatchPairs ();
    """

def get_blockmesh_tee(L, D, dens_mult, mode="split"):
    # mode="split": Inlet Left -> Right + Top
    # mode="opposed": Inlet Left + Right -> Top
    r, z = D / 2.0, 0.05
    n_D = int(20 * dens_mult)
    if n_D % 2 != 0: n_D += 1
    n_L = int((L/D) * n_D)

    p_left = "inlet_left" if mode == "opposed" else "inlet"
    p_right = "inlet_right" if mode == "opposed" else "outlet_right"
    p_top = "outlet_top" if mode == "opposed" else "outlet_top"

    return f"""
        vertices
        (
            (0 {-r} {-z})   ({L} {-r} {-z})    ({L} {r} {-z})    (0 {r} {-z})
            (0 {-r} {z})    ({L} {-r} {z})     ({L} {r} {z})     (0 {r} {z})
            ({L+D} {-r} {-z}) ({L+2*L} {-r} {-z}) ({L+2*L} {r} {-z}) ({L+D} {r} {-z})
            ({L+D} {-r} {z})  ({L+2*L} {-r} {z})  ({L+2*L} {r} {z})  ({L+D} {r} {z})
            ({L} {r+L} {-z}) ({L+D} {r+L} {-z})
            ({L} {r+L} {z})  ({L+D} {r+L} {z})
        );
        blocks
        (
            hex (0 1 2 3 4 5 6 7) ({n_L} {n_D} 1) simpleGrading (1 1 1)
            hex (1 8 11 2 5 12 15 6) ({n_D} {n_D} 1) simpleGrading (1 1 1)
            hex (8 9 10 11 12 13 14 15) ({n_L} {n_D} 1) simpleGrading (1 1 1)
            hex (2 11 17 16 6 15 19 18) ({n_D} {n_L} 1) simpleGrading (1 1 1)
        );
        edges ();
        boundary
        (
            {p_left}  {{ type patch; faces ((0 4 7 3)); }}
            {p_right} {{ type patch; faces ((9 10 14 13)); }}
            {p_top}   {{ type patch; faces ((17 16 18 19)); }}
            walls  {{ type wall;  faces (
                (0 1 5 4) (3 7 6 2)
                (1 8 12 5)
                (8 9 13 12) (10 11 15 14)
                (11 17 19 15) (16 2 6 18)
            ); }}
            frontAndBack {{ type empty; faces (
                (0 3 2 1) (4 5 6 7) 
                (1 2 11 8) (5 6 15 12)
                (8 11 10 9) (12 15 14 13)
                (2 16 17 11) (6 18 19 15)
            ); }}
        );
        mergePatchPairs ();
    """

def get_blockmesh_taper(L, D, dens_mult, mode):
    ratio = 0.5
    if mode == "taper_in": d1, d2 = D, D * ratio
    else: d1, d2 = D * ratio, D
    r1, r2 = d1/2.0, d2/2.0
    z = 0.05
    n_y = int(20 * dens_mult)
    if n_y % 2 != 0: n_y += 1
    
    # 3 sections, each L/3
    n_x = int((L/3.0 / D) * n_y)
    
    x0, x1, x2, x3 = 0, L/3.0, 2*L/3.0, L
    
    return f"""
        vertices
        (
            ({x0} {-r1} {-z}) ({x1} {-r1} {-z}) ({x1} {r1} {-z}) ({x0} {r1} {-z})
            ({x0} {-r1} {z})  ({x1} {-r1} {z})  ({x1} {r1} {z})  ({x0} {r1} {z})
            ({x2} {-r2} {-z}) ({x2} {r2} {-z})
            ({x2} {-r2} {z})  ({x2} {r2} {z})
            ({x3} {-r2} {-z}) ({x3} {r2} {-z})
            ({x3} {-r2} {z})  ({x3} {r2} {z})
        );
        blocks
        (
            hex (0 1 2 3 4 5 6 7) ({n_x} {n_y} 1) simpleGrading (1 1 1)
            hex (1 8 9 2 5 10 11 6) ({n_x} {n_y} 1) simpleGrading (1 1 1)
            hex (8 12 13 9 10 14 15 11) ({n_x} {n_y} 1) simpleGrading (1 1 1)
        );
        edges ();
        boundary
        (
            inlet  {{ type patch; faces ((0 4 7 3)); }}
            outlet {{ type patch; faces ((12 13 15 14)); }}
            walls  {{ type wall;  faces ((0 1 5 4) (3 7 6 2) (1 8 10 5) (2 6 11 9) (8 12 14 10) (9 11 15 13)); }}
            frontAndBack {{ type empty; faces ((0 3 2 1) (4 5 6 7) (1 2 9 8) (5 6 11 10) (8 9 13 12) (10 11 15 14)); }}
        );
        mergePatchPairs ();
    """

def generate_case_files(run_dir, shape, L, D, ref_level, Ux):
    os.makedirs(os.path.join(run_dir, "0"), exist_ok=True)
    
    # BlockMesh
    dens_mult = 1.4 ** ref_level
    bm_content = ""
    if shape == "straight":     bm_content = get_blockmesh_straight(L, D, dens_mult)
    elif shape == "bend":       bm_content = get_blockmesh_bend(L, D, dens_mult)
    elif shape == "bend45":     bm_content = get_blockmesh_bend45(L, D, dens_mult)
    elif shape == "tee_split":  bm_content = get_blockmesh_tee(L, D, dens_mult, mode="split")
    elif shape == "tee_opposed":bm_content = get_blockmesh_tee(L, D, dens_mult, mode="opposed")
    elif "taper" in shape:      bm_content = get_blockmesh_taper(L, D, dens_mult, shape)
        
    write_foam_file(os.path.join(run_dir, "system", "blockMeshDict"), f"""\
        FoamFile {{ version 2.0; format ascii; class dictionary; object blockMeshDict; }}
        convertToMeters 1;
        {bm_content}
    """)
    
    # fvSchemes
    write_foam_file(os.path.join(run_dir, "system", "fvSchemes"), """\
        FoamFile { version 2.0; format ascii; class dictionary; object fvSchemes; }
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
        wallDist { method meshWave; correctWalls true; }
    """)

    # fvSolution
    write_foam_file(os.path.join(run_dir, "system", "fvSolution"), """\
        FoamFile { version 2.0; format ascii; class dictionary; object fvSolution; }
        solvers
        {
            p { solver GAMG; tolerance 1e-6; relTol 0.1; smoother GaussSeidel; }
            "(U|k|epsilon|omega)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0.1; }
        }
        SIMPLE
        {
            nNonOrthogonalCorrectors 1;
            consistent      yes;
            residualControl { p 1e-3; U 1e-3; "(k|epsilon)" 1e-3; }
        }
        relaxationFactors { equations { U 0.5; k 0.5; epsilon 0.5; } fields { p 0.3; } }
    """)

    # ControlDict
    write_foam_file(os.path.join(run_dir, "system", "controlDict"), """\
        FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }
        application     simpleFoam;
        startFrom       latestTime;
        startTime       0;
        stopAt          endTime;
        endTime         1000;
        deltaT          1;
        writeControl    runTime;
        writeInterval   1000;
        purgeWrite      1;
        writeFormat     binary;
        writePrecision  6;
        writeCompression off;
        timeFormat      general;
        timePrecision   6;
        runTimeModifiable true;
        functions
        {
            yPlus1 { type yPlus; libs ("libfieldFunctionObjects.so"); executeControl writeTime; writeControl writeTime; }
        }
    """)
    
    # Physics
    k_val = max(1.5 * (Ux * TURB_INTENSITY)**2, 1e-8)
    l_mix = 0.07 * D
    eps_val = max((C_MU**0.75 * k_val**1.5) / l_mix, 1e-8)

    # U Boundary Logic
    u_boundary_content = ""
    if shape == "tee_opposed":
        # Left In, Right In, Top Out
        u_boundary_content = f"""
            inlet_left  {{ type fixedValue; value uniform ({Ux} 0 0); }}
            inlet_right {{ type fixedValue; value uniform ({-Ux} 0 0); }}
            outlet_top  {{ type zeroGradient; }}
            walls       {{ type noSlip; }}
            frontAndBack {{ type empty; }}
        """
    else:
        # Standard Generic (Matches inlet*, outlet*)
        u_boundary_content = f"""
            ".*inlet.*"  {{ type fixedValue; value uniform ({Ux} 0 0); }}
            ".*outlet.*" {{ type zeroGradient; }}
            walls        {{ type noSlip; }}
            frontAndBack {{ type empty; }}
        """

    write_foam_file(os.path.join(run_dir, "0", "U"), f"""\
        FoamFile {{ version 2.0; format ascii; class volVectorField; object U; }}
        dimensions [0 1 -1 0 0 0 0]; internalField uniform ({Ux} 0 0);
        boundaryField {{ {u_boundary_content} }}
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

def run_case(params):
    shape, L, D, Ux, ref, case_id = params
    case_name = f"case_{case_id}"
    run_dir = os.path.join(os.getcwd(), "temp_runs", case_name)
    output_path = os.path.join(OUTPUT_DIR, f"sim_{shape}_L{L:.2f}_D{D:.2f}_U{Ux:.2f}_Ref{ref}.npz")

    if os.path.exists(output_path): return None

    try:
        if os.path.exists(run_dir): shutil.rmtree(run_dir)
        shutil.copytree(TEMPLATE_DIR, run_dir)
        
        generate_case_files(run_dir, shape, L, D, ref, Ux)
        
        # Run BlockMesh
        res = subprocess.run(["blockMesh"], cwd=run_dir, capture_output=True, text=True)
        if res.returncode != 0: return f"Fail: {case_name} [CMD: blockMesh] {res.stderr[-100:]}"
        
        # Run Solver
        res = subprocess.run(["simpleFoam"], cwd=run_dir, capture_output=True, text=True)
        if res.returncode != 0: return f"Fail: {case_name} [CMD: simpleFoam]"
        
        # Extract
        touch_file = os.path.join(run_dir, "case.foam")
        open(touch_file, 'a').close()
        reader = pv.POpenFOAMReader(touch_file)
        reader.set_active_time_value(reader.time_values[-1])
        data = reader.read()
        
        internal = data["internalMesh"]
        fluid_pos = internal.cell_centers().points
        n_fluid = len(fluid_pos)
        
        def get_field(mesh, name, shape_suffix):
            if name in mesh.array_names: return mesh[name]
            return np.zeros((mesh.n_cells,) + shape_suffix)

        fluid_U = get_field(internal, "U", (3,))
        fluid_p = get_field(internal, "p", ())
        fluid_k = get_field(internal, "k", ())
        fluid_eps = get_field(internal, "epsilon", ())
        
        fluid_y = internal["y"] if "y" in internal.array_names else np.zeros(n_fluid)
        fluid_type = np.tile([1, 0, 0, 0], (n_fluid, 1))
        
        b_pos_list, b_U_list, b_p_list, b_k_list, b_eps_list, b_y_list, b_type_list = [],[],[],[],[],[],[]
        
        if "boundary" in data.keys():
            boundaries = data["boundary"]
            for name in boundaries.keys():
                if "frontAndBack" in name or "empty" in name.lower(): continue
                patch = boundaries[name]
                if patch.n_cells == 0: continue
                
                n = patch.n_cells
                b_pos_list.append(patch.cell_centers().points)
                b_U_list.append(get_field(patch, "U", (3,)))
                b_p_list.append(get_field(patch, "p", ()))
                b_k_list.append(get_field(patch, "k", ()))
                b_eps_list.append(get_field(patch, "epsilon", ()))
                b_y_list.append(np.zeros(n))
                b_type_list.append(np.tile(get_patch_type_encoding(name), (n, 1)))

        if b_pos_list:
            all_pos = np.vstack([fluid_pos] + b_pos_list)
            all_U = np.vstack([fluid_U] + b_U_list)
            all_p = np.concatenate([fluid_p] + b_p_list)
            all_k = np.concatenate([fluid_k] + b_k_list)
            all_eps = np.concatenate([fluid_eps] + b_eps_list)
            all_y = np.concatenate([fluid_y] + b_y_list)
            all_type = np.vstack([fluid_type] + b_type_list)
        else:
            all_pos, all_U, all_p, all_k, all_eps, all_y, all_type = \
            fluid_pos, fluid_U, fluid_p, fluid_k, fluid_eps, fluid_y, fluid_type

        shape_id = SHAPES.index(shape)
        np.savez_compressed(
            output_path, 
            shape_name=shape, shape_id=shape_id,
            L=L, D=D, Ux_in=Ux, Ref=ref,
            pos=all_pos, U=all_U, p=all_p, k=all_k, epsilon=all_eps, y=all_y, type=all_type
        )
        return None 

    except subprocess.CalledProcessError as e:
        return f"Fail: {case_name} [CMD: {e.cmd[0]}]"
    except Exception as e:
        return f"Fail: {case_name} [PY: {str(e)}]"
    finally:
        if os.path.exists(run_dir): shutil.rmtree(run_dir)

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("temp_runs", exist_ok=True)
    
    case_params = []
    id_ctr = 0
    for shape in SHAPES:
        for L in lengths:
            for D in diameters:
                for Ux in velocities:
                    for ref in refinements:
                        case_params.append((shape, L, D, Ux, ref, id_ctr))
                        id_ctr += 1
    
    total = len(case_params)
    print(f"Starting {total} cases on {N_CORES} cores...")
    
    with Pool(processes=N_CORES) as pool:
        for i, res in enumerate(pool.imap_unordered(run_case, case_params)):
            if res: print("\n" + res)
            
            # Progress Bar
            percent = (i + 1) * 100 // total
            bar_len = 30
            filled = int(bar_len * percent / 100)
            bar = "=" * filled + "-" * (bar_len - filled)
            sys.stdout.write(f"\r[{bar}] {percent}% ({i+1}/{total})")
            sys.stdout.flush()
    print("\nDone.")