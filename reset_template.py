"""
reset_template.py - OpenFOAM Template Generator

PURPOSE:
    Creates a clean OpenFOAM case template directory structure used as the base
    for all CFD simulations. This script initializes the required OpenFOAM system
    files with configurations optimized for simpleFoam solver with k-epsilon turbulence.

USAGE:
    python reset_template.py

OUTPUT:
    Creates 'base_template/' directory with:
    - base_template/0/          : Initial conditions directory (empty)
    - base_template/constant/   : Turbulence and transport properties
    - base_template/system/     : Solver control, schemes, and solution settings

CONFIGURATION:
    - Solver: simpleFoam (steady-state RANS)
    - Turbulence: k-epsilon model
    - Mesh: Uses meshWave method for wall distance calculation (OpenFOAM 13+)
    - Convergence: Residuals set to 1e-4

NOTES:
    - Run this before generate_dataset.py to ensure clean template
    - Compatible with OpenFOAM v13+ (uses updated wallDist method)
    - Removes existing base_template/ directory if present
"""

import os
import shutil

BASE_DIR = "base_template"

# ==========================================
# Step 1: Clean Previous Template
# ==========================================
# Remove existing template to ensure clean state
if os.path.exists(BASE_DIR):
    shutil.rmtree(BASE_DIR)

# ==========================================
# Step 2: Create OpenFOAM Directory Structure
# ==========================================
# Creates standard OpenFOAM case structure
os.makedirs(os.path.join(BASE_DIR, "0"))
os.makedirs(os.path.join(BASE_DIR, "constant"))
os.makedirs(os.path.join(BASE_DIR, "system"))

# ==========================================
# Step 3: Define System Configuration Files
# ==========================================

# --- Control Dictionary ---
# Defines solver settings, time control, and function objects
control_dict = """FoamFile
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
    // yPlus is supported in OpenFOAM 13
    yPlus1
    {
        type            yPlus;
        libs            ("libfieldFunctionObjects.so"); // Try generic lib, if fails it's often autoloaded
        executeControl  writeTime;
        writeControl    writeTime;
    }
}
"""

# --- Finite Volume Schemes ---
# Discretization schemes for gradients, divergence, Laplacian operators
fv_schemes = """FoamFile
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

// Internal calculation method for turbulence models
wallDist { method meshWave; correctWalls true; }
"""

# fvSolution
fv_solution = """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      fvSolution;
}
solvers
{
    p
    {
        solver          GAMG;
        tolerance       1e-6;
        relTol          0.1;
        smoother        GaussSeidel;
    }
    "(U|k|epsilon|omega)"
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-6;
        relTol          0.1;
    }
}
SIMPLE
{
    nNonOrthogonalCorrectors 0;
    consistent      yes;
    pRefCell        0;
    pRefValue       0;
    residualControl
    {
        p               1e-4;
        U               1e-4;
        "(k|epsilon|omega)" 1e-4;
    }
}
relaxationFactors
{
    equations
    {
        U               0.9;
        k               0.7;
        epsilon         0.7;
    }
}
"""

# ==========================================
# Step 4: Define Physical Properties
# ==========================================

# turbulenceProperties
turb_props = """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      turbulenceProperties;
}
simulationType  RAS;
RAS
{
    model           kEpsilon;
    turbulence      on;
    printCoeffs     on;
}
"""

# transportProperties
trans_props = """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      transportProperties;
}
transportModel  Newtonian;
nu              [0 2 -1 0 0 0 0] 1.5e-05;
"""

# --- WRITE FILES TO DISK ---
def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)
    print(f"Created: {path}")

write_file(os.path.join(BASE_DIR, "system", "controlDict"), control_dict)
write_file(os.path.join(BASE_DIR, "system", "fvSchemes"), fv_schemes)
write_file(os.path.join(BASE_DIR, "system", "fvSolution"), fv_solution)
write_file(os.path.join(BASE_DIR, "constant", "turbulenceProperties"), turb_props)
write_file(os.path.join(BASE_DIR, "constant", "transportProperties"), trans_props)

print("\nTemplate Reset Complete (Safe configuration).")