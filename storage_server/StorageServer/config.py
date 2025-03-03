# Standard library imports
import os

# Third-party library imports
import shutil

# Directory to save uploaded files
UPLOAD_FOLDER = 'StorageDirectory'

# Check if the folder already exists
if os.path.exists(UPLOAD_FOLDER):
    print(f"Directory '{UPLOAD_FOLDER}' exists. Removing it...")
    # Remove the existing directory and all its contents
    shutil.rmtree(UPLOAD_FOLDER)
    print(f"Directory '{UPLOAD_FOLDER}' has been removed.")
else:
    print(f"Directory '{UPLOAD_FOLDER}' does not exist. Creating it...")
    # Ensure the directory exists
    os.makedirs(UPLOAD_FOLDER)
    print(f"Directory '{UPLOAD_FOLDER}' has been created.")
