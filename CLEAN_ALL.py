import os
import glob
import subprocess
import sys

def main():
    # 1. Identify the script itself to prevent recursion
    current_script = os.path.basename(__file__)

    # 2. Find all scripts starting with 'clean_' (case insensitive matching pattern)
    # This covers clean_temp_runs.py, clean_visuals.py, etc.
    scripts = [f for f in glob.glob("clean_*.py") if f != current_script]
    
    if not scripts:
        print("No cleanup scripts (starting with 'clean_') found in this directory.")
        return

    # 3. Warning Message
    print("!" * 60)
    print("CRITICAL WARNING: MASTER CLEANUP INITIATED")
    print("!" * 60)
    print("The following scripts will be executed sequentially:")
    for script in scripts:
        print(f"  - {script}")
    print("-" * 60)
    print("This may PERMANENTLY DELETE datasets, temp runs, and visualizations.")
    
    # 4. Strict Confirmation
    confirmation = input("To proceed, type exactly 'YES IM SURE': ")

    if confirmation != "YES IM SURE":
        print("\nIncorrect confirmation. Operation ABORTED.")
        return

    print("\nStarting cleanup sequence...\n")

    # 5. Execute Scripts
    for script in scripts:
        print(f">>> Executing: {script}")
        try:
            # We pass sys.executable to ensure we use the same python interpreter (conda env)
            subprocess.run([sys.executable, script], check=True)
            print(f">>> Finished: {script}\n")
        except subprocess.CalledProcessError as e:
            print(f"!!! Error running {script}. Exit code: {e.returncode}\n")
        except Exception as e:
            print(f"!!! Unexpected error running {script}: {e}\n")

    print("Master cleanup sequence finished.")

if __name__ == "__main__":
    main()