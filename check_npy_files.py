import numpy as np
import glob
import os
import random

def check_encoding():
    # Define directory based on your example
    folder_path = "extracted_data"
    file_pattern = os.path.join(folder_path, "*.npy")
    
    # Get list of all .npy files
    all_files = glob.glob(file_pattern)
    
    if not all_files:
        print(f"No .npy files found in '{folder_path}'")
        return

    # Select 5 random files (or fewer if less than 5 exist)
    num_to_check = min(5, len(all_files))
    selected_files = random.sample(all_files, num_to_check)

    print(f"Found {len(all_files)} files. Checking {num_to_check} random files...\n")

    for file_path in selected_files:
        filename = os.path.basename(file_path)
        print(f"Checking: {filename}")
        
        try:
            # Load the array
            arr = np.load(file_path)
            
            # Verify shape (Ensure there are at least 12 columns)
            if arr.shape[1] < 12:
                print(f"  [ERROR] File has incorrect shape {arr.shape}. Expected 12 columns.")
                continue

            # Extract the 4 category columns:
            # Indices: 8 (is_fluid), 9 (is_wall), 10 (is_inlet), 11 (is_outlet)
            category_cols = arr[:, 8:12]
            
            # Sum across the rows (axis=1)
            # This results in an array of shape (N,)
            row_sums = np.sum(category_cols, axis=1)
            
            # Compare to 1. 
            # We use np.isclose because .npy data is often float, 
            # handling potential floating point minor deviations.
            is_valid = np.isclose(row_sums, 1.0)
            
            if np.all(is_valid):
                print("  [PASS] Encoding correct. All rows sum to 1.")
            else:
                # Count failures
                fail_count = np.sum(~is_valid)
                total_rows = arr.shape[0]
                print(f"  [FAIL] {fail_count}/{total_rows} rows have incorrect encoding.")
                
                # Optional: Show the first failed row for debugging
                bad_idx = np.where(~is_valid)[0][0]
                print(f"    -> Example failure at row {bad_idx}: {category_cols[bad_idx]} (Sum: {row_sums[bad_idx]})")
                
        except Exception as e:
            print(f"  [ERROR] Could not read file: {e}")
            
        print("-" * 50)

if __name__ == "__main__":
    check_encoding()