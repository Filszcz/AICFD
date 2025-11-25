Here is the updated `README.md` reflecting the **2.0 Exponential Mesh Refinement** and the specific optimizations for your 12-core setup.

***

# Deep Learning CFD Dataset Generator (Raw Point Cloud Edition)

## Project Overview
This framework automates the generation of a massive Computational Fluid Dynamics (CFD) dataset (78,125 cases) designed for **Geometric Deep Learning**.

Unlike traditional datasets that interpolate results onto a fixed image grid, this generator extracts the **Exact Raw Mesh Centers** from OpenFOAM. This ensures:
1.  **Physics Fidelity:** No interpolation loss; data represents the exact solver output.
2.  **Variable Resolution:** Point clouds vary in size ($N$) based on geometry and refinement level.
3.  **True 2D Topology:** Explicitly excludes simulation thickness layers, providing a clean 2D plane ($z=0$).
4.  **Boundary Awareness:** Includes inlet, outlet, and wall nodes with one-hot encoded tags.

## Simulation Specifications
*   **Physics:** Steady-State Incompressible Flow (RANS $k-\epsilon$).
*   **Solver:** OpenFOAM v13 (`simpleFoam`).
*   **Geometry:** 2D Pipe with parametric Length ($L$) and Diameter ($D$).
*   **Meshing:** `blockMesh` with **Boundary Layer Grading** (High density near walls).
*   **Refinement Strategy:** **Exponential ($2.0^N$)**.
    *   Level 0: 1x Base Density.
    *   Level 4: 16x Base Density (Ultra-fine).

---

## 1. Prerequisites

### Software
*   **OS:** Ubuntu 22.04 / 24.04.
*   **CFD Solver:** OpenFOAM v13 (Foundation Release).
    *   *Must support `yPlus` with `meshWave` method.*
*   **Python:** 3.12 (via Miniconda/Anaconda).
*   **Visualization:** Paraview 5.10+.

### Hardware
*   **CPU:** Configured for **12 Physical Cores**, `N_CORES` variable.

---

## 2. Installation

1.  **Create Environment:**
    ```bash
    conda create -n AICFD python=3.12 -y
    conda activate AICFD
    ```

2.  **Install Dependencies:**
    ```bash
    pip install numpy pyvista scipy
    ```

3.  **Source OpenFOAM:**
    (Add to `~/.bashrc` if not already present)
    ```bash
    source /opt/openfoam13/etc/bashrc
    ```

---

## 3. Project Files

| Script | Function |
| :--- | :--- |
| `generate_dataset_raw.py` | **Main Generator.** Runs parallel simulations and saves `.npz`. |
| `one_case.py` | **Verification.** Tests the solver/license on a single case. |
| `check_raw_results.py` | **Visualization.** Converts `.npz` samples to `.vtp` for Paraview. |
| `CLEAN_ALL.py` | **Master Cleanup.** Deletes data/temp files (Safety locked). |
| `data_output/` | Directory where final `.npz` files are saved. |

---

## 4. How to Run

### Step 1: Verification
Ensure OpenFOAM is correctly linked and the `yPlus` function object works.
```bash
python one_case.py
```
*   **Success:** Prints `VERIFICATION SUCCESSFUL`.

### Step 2: Generate Dataset
Launch the production run.
```bash
python generate_dataset_raw.py
```
*   **Configuration:** Runs on 12 Cores.
*   **Progress:** Displays cases per second and status.
*   **Output:** Files saved as `data_output/sim_L{L}_D{D}_U{U}_Ref{R}.npz`.

### Step 3: Visualize Results
Inspect random samples to ensure mesh quality and physics convergence.
```bash
python check_raw_results.py
```
1.  Generates `.vtp` files in `sample_raw_viz/`.
2.  Open these in **Paraview**.
3.  Visualize `U` (Velocity) or `type` (Boundary tags). You will see the mesh density increase dramatically between Refinement levels.

### Step 4: Cleanup
To delete all generated data and temp files:
```bash
python CLEAN_ALL.py
```
*(Requires confirmation input: "YES IM SURE")*

---

## 5. Data Format (`.npz`)

The data is stored as compressed NumPy arrays.

**Loading Data:**
```python
import numpy as np
data = np.load("data_output/sim_case_0.npz")
points = data['pos']  # (N, 3)
velocity = data['U']  # (N, 3)
```

**Array Dictionary:**

| Key | Shape | Description |
| :--- | :--- | :--- |
| `pos` | $(N, 3)$ | Cell center coordinates $(x, y, 0)$. |
| `U` | $(N, 3)$ | Velocity vector. |
| `p` | $(N,)$ | Pressure field. |
| `k` | $(N,)$ | Turbulent Kinetic Energy. |
| `epsilon`| $(N,)$ | Turbulent Dissipation Rate. |
| `y` | $(N,)$ | Wall Distance (computed via `meshWave`). |
| `type` | $(N, 4)$ | Node Type One-Hot: `[Fluid, Wall, Inlet, Outlet]`. |
| `L`, `D` | Scalar | Geometry parameters. |
| `Ref` | Scalar | Refinement Level (0-4). |

---

## 6. Configuration

You can modify parameters in `generate_dataset_raw.py`:

*   **`N_CORES = 12`**: Set to your CPU's physical core count.
*   **`dens_mult = 2.0 ** ref_level`**: Controls mesh density scaling.
*   **`base_y = 25`**: Base number of cells across the pipe diameter (Level 0).
