# Deep Learning CFD Dataset Generator (Raw Point Cloud Version)

## Project Overview
This framework automates the generation of a large-scale CFD dataset for Geometric Deep Learning (Graph Neural Networks, PointNet, etc.).

Unlike standard CNN datasets which interpolate physics onto a fixed grid, this generator captures the **Exact Raw Mesh** (cell centers) from OpenFOAM. This preserves:
1.  **Variable Resolution:** Each case has a different number of points ($N$) depending on geometry size and refinement level.
2.  **Boundary Layer Topology:** Preserves the high-density cell clustering near walls defined by the `blockMesh` grading.
3.  **Boundary Conditions:** Explicitly captures inlet, outlet, and wall patch data alongside the fluid domain.

**Simulation Specs:**
*   **Physics:** Steady-State RANS ($k-\epsilon$), Incompressible Flow.
*   **Solver:** OpenFOAM v13 (`simpleFoam`).
*   **Output:** Compressed `.npz` files containing spatial coordinates ($x,y,z$) and physical fields ($U, p, k, \epsilon$, wall distance).

---

## 1. Prerequisites

### Software
*   **OS:** Ubuntu 22.04 / 24.04 (Linux).
*   **CFD Solver:** OpenFOAM v13 (Foundation Release).
    *   *Critical:* Must support the `yPlus` function object with `meshWave` integration.
*   **Python:** 3.12 (via Miniconda/Anaconda).
*   **Visualization:** Paraview 5.10+.

### Hardware
*   Recommended: Multi-core CPU (e.g., Ryzen 9 5900x or better).
*   Storage: ~50GB free space (for 78k cases in compressed format).

---

## 2. Installation & Setup

### 2.1 Create Conda Environment
```bash
# Create environment
conda create -n AICFD python=3.12 -y

# Activate
conda activate AICFD
```

### 2.2 Install Dependencies
```bash
pip install numpy pyvista scipy
```

### 2.3 Configure OpenFOAM
Ensure OpenFOAM is available in your terminal. Add this to your `.bashrc` if not present:
```bash
source /opt/openfoam13/etc/bashrc
```
*Verify by running `simpleFoam -help`.*

---

## 3. Project Structure

| File | Description |
| :--- | :--- |
| `generate_dataset_raw.py` | **Main Generator.** Runs 22-core parallel simulations and saves `.npz`. |
| `one_case.py` | **Verification.** Runs a single case to test solver/license health. |
| `check_raw_results.py` | **Visualization.** Converts random `.npz` samples to `.vtp` for Paraview. |
| `CLEAN_ALL.py` | **Master Cleanup.** Deletes all data and temp files (Safety locked). |
| `clean_temp_runs.py` | Deletes only intermediate OpenFOAM folders. |
| `clean_data_output.py` | Deletes only the dataset. |
| `base_template/` | (Auto-generated) OpenFOAM configuration templates. |
| `data_output/` | (Auto-generated) Stores the final 78,125 `.npz` files. |

---

## 4. How to Run

### Step 1: Verification
Before launching the massive batch, ensure your OpenFOAM environment works.
```bash
python one_case.py
```
*   **Expected Output:** `VERIFICATION SUCCESSFUL`.
*   *Note:* This confirms that `blockMesh`, `simpleFoam`, and the `yPlus` wall distance calculation are functioning.

### Step 2: Generate Dataset
Launch the parallel production script.
```bash
python generate_dataset_raw.py
```
*   **Performance:** Uses 22 cores. Expect ~10-15 cases/second.
*   **Output:** Files are saved to `data_output/sim_L{L}_D{D}_U{U}_Ref{R}.npz`.
*   The script automatically cleans up individual OpenFOAM temp folders after extraction to save inodes.

### Step 3: Visualize Results
To inspect the quality of the generated point clouds:
```bash
python check_raw_results.py
```
1.  This creates a folder `sample_raw_viz` containing 10 random `.vtp` files.
2.  Open **Paraview**.
3.  Drag and drop the `.vtp` files.
4.  Change "Coloring" to `U` (Velocity) or `type` (Boundary ID).

### Step 4: Cleanup (Optional)
To delete all data and reset the project:
```bash
python CLEAN_ALL.py
```
*   **Safety:** You must type exactly `YES IM SURE` to proceed.

---

## 5. Data Format (`.npz`)

Each `.npz` file contains the following NumPy arrays. Use `np.load('filename.npz')` to access them.

| Key | Shape | Description |
| :--- | :--- | :--- |
| `pos` | $(N, 3)$ | $(x, y, z)$ coordinates of cell centers. |
| `U` | $(N, 3)$ | Velocity vector $(U_x, U_y, U_z)$. |
| `p` | $(N,)$ | Pressure scalar (Kinematic pressure). |
| `k` | $(N,)$ | Turbulent Kinetic Energy. |
| `epsilon`| $(N,)$ | Turbulent Dissipation Rate. |
| `y` | $(N,)$ | Wall Distance (Distance to nearest wall). |
| `type` | $(N, 4)$ | One-Hot Encoding: `[Is_Fluid, Is_Wall, Is_Inlet, Is_Outlet]` |
| `L` | Scalar | Geometric Parameter: Pipe Length. |
| `D` | Scalar | Geometric Parameter: Pipe Diameter. |

*$N$ varies per file depending on the geometry and refinement level.*

### Python Loading Example
```python
import numpy as np

data = np.load("data_output/sim_L10.00_D0.50_U1.00_Ref0.npz")

# Access Point Cloud Positions
points = data['pos'] 

# Access Velocity
velocity = data['U']

# Filter only Fluid nodes
is_fluid = data['type'][:, 0] == 1
fluid_points = points[is_fluid]
```