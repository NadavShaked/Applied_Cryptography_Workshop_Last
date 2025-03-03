# Standard library imports
import os


files_details_dict = {}


# Function to save uploaded files to the specified directory
def save_file(file, upload_folder):
    # Ensure the directory exists
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    file_path = os.path.join(upload_folder, file.filename)

    # Check if the file already exists
    if os.path.exists(file_path):
        print("FileExistsError")
        raise FileExistsError(f"File '{file.filename}' already exists in the directory.")

    try:
        file.save(file_path)
    except Exception as e:
        raise Exception(f"Failed to save file: {str(e)}")

    return file_path
