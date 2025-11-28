import os
import shutil
import sys

# TARGET FOLDER
TARGET_DIR = "base_template"

def clean_data():
    if not os.path.exists(TARGET_DIR):
        print(f"Directory '{TARGET_DIR}' does not exist. Nothing to do.")
        return

    print(f"WARNING: You are about to DELETE the directory: '{TARGET_DIR}'")
    print(f"This contains all your base template files.")
    
    confirm = input("Are you sure you want to delete it? (yes/no): ").strip().lower()
    
    if confirm == "yes":
        print(f"Deleting '{TARGET_DIR}'...")
        try:
            shutil.rmtree(TARGET_DIR)
            print("Cleanup complete.")
        except Exception as e:
            print(f"Error during deletion: {e}")
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    clean_data()