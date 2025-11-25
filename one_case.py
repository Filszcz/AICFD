import os
import shutil
import subprocess
import numpy as np
import textwrap

# --- Setup ---
TEST_DIR = "verify_case"
TEMPLATE_DIR = "base_template"
L, D, Ux = 10.0, 0.5, 1.0

def write_file(path, content):
    with open(path, "w") as f:
        f.write(textwrap.dedent(content))

def generate_files(run_dir):
    # 1. fvSchemes: We strictly set wallDist method to meshWave here.
    # The solver will respect this setting when yPlus asks for distance.
    write_file(os.path.join(run_dir, "system", "fvSchemes"), """\
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

    # 2. blockMeshDict
    dens_mult = 1.0
    r, z = D / 2.0, 0.05
    x_cells, y_cells = 40, 20
    
    write_file(os.path.join(run_dir, "system", "blockMeshDict"), f"""\
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
    """)

    # 3. controlDict
    write_file(os.path.join(run_dir, "system", "controlDict"), """\
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
        endTime         100;
        deltaT          1;
        writeControl    runTime;
        writeInterval   100;
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
    write_file(os.path.join(run_dir, "0", "p"), """\
        FoamFile { version 2.0; format ascii; class volScalarField; object p; }
        dimensions [0 2 -2 0 0 0 0]; internalField uniform 0;
        boundaryField { inlet { type zeroGradient; } outlet { type fixedValue; value uniform 0; } walls { type zeroGradient; } frontAndBack { type empty; } }
    """)
    write_file(os.path.join(run_dir, "0", "U"), f"""\
        FoamFile {{ version 2.0; format ascii; class volVectorField; object U; }}
        dimensions [0 1 -1 0 0 0 0]; internalField uniform ({Ux} 0 0);
        boundaryField {{ inlet {{ type fixedValue; value uniform ({Ux} 0 0); }} outlet {{ type zeroGradient; }} walls {{ type noSlip; }} frontAndBack {{ type empty; }} }}
    """)
    write_file(os.path.join(run_dir, "0", "k"), """\
        FoamFile { version 2.0; format ascii; class volScalarField; object k; }
        dimensions [0 2 -2 0 0 0 0]; internalField uniform 0.1;
        boundaryField { inlet { type fixedValue; value uniform 0.1; } outlet { type zeroGradient; } walls { type kqRWallFunction; value uniform 0.1; } frontAndBack { type empty; } }
    """)
    write_file(os.path.join(run_dir, "0", "epsilon"), """\
        FoamFile { version 2.0; format ascii; class volScalarField; object epsilon; }
        dimensions [0 2 -3 0 0 0 0]; internalField uniform 0.1;
        boundaryField { inlet { type fixedValue; value uniform 0.1; } outlet { type zeroGradient; } walls { type epsilonWallFunction; value uniform 0.1; } frontAndBack { type empty; } }
    """)
    write_file(os.path.join(run_dir, "0", "nut"), """\
        FoamFile { version 2.0; format ascii; class volScalarField; object nut; }
        dimensions [0 2 -1 0 0 0 0]; internalField uniform 0;
        boundaryField { inlet { type calculated; value uniform 0; } outlet { type calculated; value uniform 0; } walls { type nutkWallFunction; value uniform 0; } frontAndBack { type empty; } }
    """)

def run_test():
    if os.path.exists(TEST_DIR): shutil.rmtree(TEST_DIR)
    shutil.copytree(TEMPLATE_DIR, TEST_DIR)
    generate_files(TEST_DIR)
    
    print("1. Running blockMesh...")
    subprocess.run(["blockMesh"], cwd=TEST_DIR, check=True, capture_output=True, text=True)
    print("   [OK]")

    # Append yPlus function to controlDict
    # This function is valid in v13 and will trigger the wall distance calculation
    with open(os.path.join(TEST_DIR, "system", "controlDict"), "r+") as f:
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

    print("2. Running simpleFoam...")
    subprocess.run(["simpleFoam"], cwd=TEST_DIR, check=True, capture_output=True, text=True)
    print("   [OK]")
    
    print("\nVERIFICATION SUCCESSFUL.")

if __name__ == "__main__":
    try:
        run_test()
    except subprocess.CalledProcessError as e:
        print("\n!!! ERROR !!!")
        print(f"Command: {e.cmd}")
        print("STDERR:", e.stderr)