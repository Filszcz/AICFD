"""
clean_dataset.py - CFD Data Sanitizer

PURPOSE:
    Scans the .npy dataset for "exploded" CFD simulations (NaNs, Infs, or massive values).
    - If a file has a few bad points: It clips them to reasonable physical limits.
    - If a file is completely broken (>50% bad): It moves it to a 'quarantine' folder.
"""

import numpy as np
import glob
import os
import shutil
import sys

# ==========================================
# CONFIGURATION
# ==========================================
DATA_DIR = "./data_output"
QUARANTINE_DIR = "./data_quarantine"

# Physical Limits (Adjust based on your fluid/scale)
# For standard water/air pipe flow, 200m/s is already very high.
MAX_VELOCITY = 20     # m/s
MAX_PRESSURE = 5e6       # Pa (50 bar)

# If more than this % of points are bad, discard the file entirely
DESTRUCTION_THRESHOLD = 0.50 # 50%

# ==========================================
# UTILS
# ==========================================

def load_file_content(file_path):
    """Robust loader that handles the 0-D dictionary issue."""
    try:
        raw = np.load(file_path, allow_pickle=True)
        
        # Unpack 0-D array wrapping a dict
        if raw.ndim == 0:
            content = raw.item()
            if isinstance(content, dict) and 'data' in content:
                return content, content['data']
        
        # Handle direct array (legacy)
        if isinstance(raw, np.ndarray) and raw.ndim == 2:
            return {"data": raw}, raw
            
        return None, None
    except Exception as e:
        print(f"❌ Read Error {file_path}: {e}")
        return None, None

def check_and_fix(file_path):
    full_content, data = load_file_content(file_path)
    
    if data is None:
        return "READ_ERR"

    # Data shape: [N, 12]
    # Cols: 3,4,5 (u,v,w), 6 (p)
    
    # 1. Check NaNs / Infs
    mask_nan = ~np.isfinite(data)
    nan_count = np.sum(mask_nan)
    
    if nan_count > 0:
        data[mask_nan] = 0.0 # Replace NaNs with 0
        
    # 2. Check Physical Limits
    # Velocity (Cols 3,4,5)
    vels = data[:, 3:6]
    mask_v = np.abs(vels) > MAX_VELOCITY
    
    # Pressure (Col 6)
    press = data[:, 6]
    mask_p = np.abs(press) > MAX_PRESSURE
    
    # Total bad points (logical OR of all conditions)
    # We count rows where ANY column is bad
    row_is_bad = np.any(mask_v, axis=1) | mask_p | np.any(mask_nan, axis=1)
    bad_row_count = np.sum(row_is_bad)
    total_rows = data.shape[0]
    
    damage_ratio = bad_row_count / total_rows

    # DECISION TIME
    if bad_row_count == 0:
        return "OK"

    print(f"⚠️  {os.path.basename(file_path)}: {bad_row_count}/{total_rows} points ({damage_ratio:.1%}) out of bounds.")

    if damage_ratio > DESTRUCTION_THRESHOLD:
        return "QUARANTINE"
    
    # FIX: Clip values
    # Clip Velocity
    data[:, 3:6] = np.clip(data[:, 3:6], -MAX_VELOCITY, MAX_VELOCITY)
    
    # Clip Pressure
    data[:, 6] = np.clip(data[:, 6], -MAX_PRESSURE, MAX_PRESSURE)
    
    # Save back
    # We must update the array inside the dictionary to preserve metadata
    full_content['data'] = data
    
    try:
        np.save(file_path, full_content)
        return "FIXED"
    except Exception as e:
        print(f"Failed to save {file_path}: {e}")
        return "SAVE_ERR"

# ==========================================
# MAIN
# ==========================================

def main():
    if not os.path.exists(DATA_DIR):
        print(f"Directory {DATA_DIR} not found.")
        return

    os.makedirs(QUARANTINE_DIR, exist_ok=True)
    
    files = glob.glob(os.path.join(DATA_DIR, "*.npy"))
    print(f"🔍 Scanning {len(files)} files in {DATA_DIR}...")
    print(f"   Limits: Vel > {MAX_VELOCITY} m/s, Press > {MAX_PRESSURE} Pa")

    stats = {"OK": 0, "FIXED": 0, "QUARANTINE": 0, "ERR": 0}

    for f in files:
        result = check_and_fix(f)
        
        if result == "OK":
            stats["OK"] += 1
        elif result == "FIXED":
            stats["FIXED"] += 1
            print(f"   ✅ Clipped and Saved.")
        elif result == "QUARANTINE":
            stats["QUARANTINE"] += 1
            dst = os.path.join(QUARANTINE_DIR, os.path.basename(f))
            shutil.move(f, dst)
            print(f"   ⛔ Moved to Quarantine (Too damaged).")
        else:
            stats["ERR"] += 1

    print("\n" + "="*30)
    print("SUMMARY")
    print("="*30)
    print(f"🟢 Good Files:      {stats['OK']}")
    print(f"🟡 Fixed (Clipped): {stats['FIXED']}")
    print(f"🔴 Quarantined:     {stats['QUARANTINE']}")
    print(f"❌ Errors:          {stats['ERR']}")
    print("="*30)

if __name__ == "__main__":
    main()