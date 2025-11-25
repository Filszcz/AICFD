import os
import shutil
import sys

# TARGET FOLDERS
TARGETS = ["extracted_data"]

def clean_vis():
    print(f"WARNING: You are about to DELETE the directories: {TARGETS}")
    
    confirm = input("Are you sure you want to delete it? (yes/no): ").strip().lower()
    
    if confirm == "yes":
        for target in TARGETS:
            if os.path.exists(target):
                print(f"Deleting '{target}'...")
                try:
                    shutil.rmtree(target)
                except Exception as e:
                    print(f"Error deleting {target}: {e}")
            else:
                print(f"'{target}' not found, skipping.")
        print("Cleanup complete.")
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    clean_vis()