# Standard library imports
import os
from datetime import datetime

# Third-party library imports
from flask import Blueprint, jsonify, request, send_file
import py_ecc.optimized_bls12_381 as bls_opt


# Local imports
from .constants import SELLER_PRIVATE_KEY
from .storage import save_file
from .storage import files_details_dict
from .Common.Providers.solanaApiGatewayProvider import SolanaGatewayClientProvider
from .Common.ReedSolomon.reedSolomon import corrupt_file
from .config import UPLOAD_FOLDER
from .BLS12_381.helpers import p, MAC_SIZE, BLOCK_SIZE, compress_g1_to_hex, MAC_SIZE_3D


# Create a Blueprint for the API in the StorageServer2 app
api_bp = Blueprint('api', __name__)


@api_bp.route('/api/get_files', methods=['GET'])
def get_files_endpoint():
    """
    Endpoint to retrieve the list of stored files with their details.

    This API endpoint iterates through the files stored in the `files_details_dict`
    and retrieves details such as the file name, escrow public key, validation frequency,
    and the last verification date. It returns a JSON response with all the necessary
    file details, including an ID and formatted last verification date.

    Returns:
        JSON: A list of file details with each file's name, escrow public key,
              validation frequency, and last verification date in ISO 8601 format.
    """

    # Create a list to store the result
    result = []

    # Initialize the index for each file
    index: int = 0

    # Iterate over each file's details in the files_details_dict
    for filename, file_details in files_details_dict.items():
        # Extract necessary details from the file's details
        escrow_public_key = file_details.get("escrow_public_key")
        validate_every = file_details.get("validate_every")
        last_verify = file_details.get("last_verify")

        # Ensure `last_verify` is converted to date if it's a datetime object
        last_verify_date = last_verify.date() if isinstance(last_verify, datetime) else last_verify

        # Append the file details to the result list
        result.append({
            "id": index,  # Unique ID for each file in the response
            "file_name": filename,  # Name of the file
            "escrow_public_key": escrow_public_key,  # Public key associated with the escrow
            "validate_every": validate_every,  # Frequency of validation for the file
            "last_verify": last_verify_date.isoformat()  # Convert to ISO format string for consistency
        })

        # Increment the index for the next file
        index += 1

    # Return the list of files in JSON format
    return jsonify({
        "data": {
            "storageFiles": result  # Wrap the list of file details in a 'storageFiles' key
        }
    })


@api_bp.route('/api/delete_file', methods=['GET'])
def delete_file_endpoint():
    """
    Endpoint to delete a specific file from the storage.

    This API endpoint accepts a query parameter `filename` to identify the file to be deleted.
    If the filename is not provided or if the file does not exist in the `files_details_dict`,
    appropriate error messages are returned. If the file is found, it is removed from the dictionary
    and a success message is returned.

    Query Parameters:
        filename (str): The name of the file to be deleted.

    Returns:
        JSON: A message indicating the success or failure of the file deletion.
    """

    # Retrieve the filename from query parameters
    filename = request.args.get("filename")

    # If filename is not provided, return a Bad Request error
    if not filename:
        return jsonify({"error": "Filename not provided"}), 400  # Bad Request if filename is missing

    # Check if the file exists in the dictionary before trying to remove it
    if filename not in files_details_dict:
        return jsonify({"error": f"File {filename} not found"}), 404  # Not Found if the file doesn't exist

    file_details = files_details_dict[filename]

    escrow_pubkey = file_details["escrow_public_key"]
    # Initialize Solana client and get escrow data
    client = SolanaGatewayClientProvider()

    print("Starting request for funds from escrow using the Solana client.")

    # Use the client to request funds by providing the seller's private key and the escrow public key
    client.request_funds(SELLER_PRIVATE_KEY, escrow_pubkey)

    print("Finished requesting funds from escrow using the Solana client.")

    # Remove the file entry from the dictionary
    files_details_dict.pop(filename)

    # Return success message in JSON format
    return jsonify({
        "message": "Deletion succeeded"
    }), 200  # Success with status code 200


@api_bp.route('/api/download', methods=['GET'])
def download_endpoint():
    """
    Handles file download requests.

    This function:
    - Accepts a filename parameter from the request.
    - Validates if the filename is provided.
    - Checks if the file exists in the storage directory.
    - If the file exists, it sends the file as an attachment for download.
    - If the file does not exist, it returns a 404 error with a message.

    Args:
        None

    Returns:
        send_file (file): The file requested for download, sent as an attachment.
        jsonify (dict): A JSON response with error messages (in case of failure).
    """
    filename = request.args.get("filename")
    print(f"Received download request for file: {filename}")

    if not filename:
        print("Error: Filename not provided")
        return jsonify({"error": "Filename not provided"}), 400

    file_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, filename))
    print(f"Constructed file path: {file_path}")

    if not os.path.exists(file_path):
        print(f"Error: File {filename} not found at {file_path}")
        return jsonify({"error": "File not found"}), 404

    print(f"File {filename} found, sending for download...")
    return send_file(file_path, as_attachment=True)


@api_bp.route("/api/upload", methods=["POST"])
def upload_endpoint():
    """
    Handles file uploads and processes associated metadata for an escrow account.

    This function:
    - Accepts a file upload via a POST request.
    - Retrieves the `escrow_public_key` from the request.
    - Fetches escrow data from the Solana Gateway Client.
    - Validates the data and saves the file to the specified directory.
    - Updates the metadata for the uploaded file in the `files_details_dict`.

    Args:
        None

    Returns:
        jsonify (dict): A response object containing success or error message.
    """
    print("Received file upload request")

    # Check if a file is included in the request
    if "file" not in request.files:
        print("Error: No file provided in the request")
        return jsonify({"error": "No file provided"}), 400

    uploaded_file = request.files["file"]

    # Check if the uploaded file has a name
    if uploaded_file.filename == "":
        print("Error: Empty file name")
        return jsonify({"error": "Empty file name"}), 400

    if request.content_type == "application/json":
        params = request.json
        print("Received parameters as JSON")
    else:
        params = request.form
        print("Received parameters as form-data")

    escrow_pubkey = params.get("escrow_public_key", type=str)
    print(f"Escrow public key: {escrow_pubkey}")

    try:
        # Initialize Solana client and get escrow data
        client = SolanaGatewayClientProvider()
        print("Fetching escrow data using the Solana client")
        get_escrow_data_response = client.get_escrow_data(escrow_pubkey)

        # Check if the response from the Solana client is successful
        if 200 <= get_escrow_data_response.status_code < 300:
            print("Successfully retrieved escrow data")
            get_escrow_data_response_json = get_escrow_data_response.json()

            # Extract the 'validate_every' parameter from the response
            validate_every = get_escrow_data_response_json.get("validate_every")
            print(f"Validate every: {validate_every}")
        else:
            print(f"Error: Failed to retrieve escrow data, status code: {get_escrow_data_response.status_code}")
            return jsonify({"error": f"Failed to retrieve escrow data"}), 500

    except Exception as e:
        print(f"Exception while fetching escrow data: {str(e)}")
        return jsonify({"error": f"Failed to fetch escrow data: {str(e)}"}), 500

    # Save the uploaded file
    try:
        print(f"Saving file: {uploaded_file.filename}")
        file_path = save_file(uploaded_file, UPLOAD_FOLDER)
        print(f"File saved at {file_path}")
    except FileExistsError as e:
        print(f"Error: File '{e.args[0]}' already exists in the directory")
        return jsonify({"error": f"File '{e.args[0]}' already exists in the directory."}), 409
    except Exception as e:
        print(f"Exception while saving file: {str(e)}")
        return jsonify({"error": f"Failed to save file: {str(e)}"}), 500

    # Update the details of the uploaded file in the storage dictionary
    files_details_dict[uploaded_file.filename] = {
        "escrow_public_key": escrow_pubkey,
        "validate_every": validate_every,
        "last_verify": datetime.now()
    }
    print(f"Updated file details for {uploaded_file.filename}")

    # Return a success message
    return jsonify({"message": "File received and saved", "filename": uploaded_file.filename})


@api_bp.route("/api/calculate_and_prove", methods=["GET"])
def calculate_and_prove_endpoint():
    """
    Calculates the values of σ (sigma) and μ (mu) for a given file based on its metadata and
    validates the proof of the calculation.

    This function:
    - Retrieves the filename from the request parameters.
    - Looks up the file details in `files_details_dict`.
    - Validates the existence of the file in the specified folder.
    - Calculates the values of σ and μ using the `calculate_sigma_mu_and_prove` function.
    - Returns whether the calculation was successfully proved.

    Args:
        None

    Returns:
        jsonify (dict): A response object containing the result of the calculation and whether it was proved.
        - If successful, returns a JSON object with a "proved" field indicating the validity of the calculation.
        - If an error occurs, returns an error message and a corresponding HTTP status code.
    """
    try:
        # Retrieve filename from request parameters
        filename = request.args.get("filename")
        file_details = files_details_dict[filename]

        # Check if the filename is provided
        if not filename:
            return jsonify({"error": "Filename not provided"}), 400

        # Construct the full file path
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Check if the file exists
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404

        # Calculate the values of σ and μ and check if the proof is valid
        is_proved: bool = calculate_sigma_mu_and_prove(filename, file_details["escrow_public_key"])

        # Return the calculated values and the proof result
        return jsonify({
            "proved": is_proved,
        })

    except Exception as e:
        return jsonify({"error": f"An error occurred during calculation: {str(e)}"}), 500


@api_bp.route("/api/corrupt", methods=["GET"])
def corrupt_file_endpoint():
    """
    Handles file corruption requests.

    This function:
    - Accepts a filename as a request parameter.
    - Checks if the filename is provided and if the file exists.
    - If the file exists, it corrupts the file using the `corrupt_file_with_rs` function.
    - If any errors occur during the process, it returns a 500 error with the exception message.

    Args:
        None

    Returns:
        jsonify (dict): A response object containing success or error message.
    """
    try:
        # Retrieve file_name from request parameters
        file_name = request.args.get("filename")

        # Check if the file_name is provided
        if not file_name:
            return jsonify({"error": "Filename not provided"}), 400

        file_path = os.path.join(UPLOAD_FOLDER, file_name)

        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404

        # corrupt the file by changing bytes
        corrupt_file(file_path, file_path)

        # Return the calculated values and the proof result
        return jsonify({
            "message": f'The file "{file_name}" corrupted.',
        })

    except Exception as e:
        return jsonify({"error": f"An error occurred during calculation: {str(e)}"}), 500


def calculate_sigma_mu_and_prove(filename: str, escrow_public_key: str) -> bool:
    """
    Calculates the values of σ (sigma) and μ (mu) based on the provided file and escrow public key,
    and sends a proof request to the Solana gateway client.

    This function:
    - Retrieves queries from the Solana gateway for a specific escrow account.
    - Processes the file by reading its blocks, extracting the relevant information, and calculating
      the values of σ and μ using cryptographic operations.
    - Sends the proof to the Solana gateway to verify the results.

    Args:
        filename (str): The name of the file containing the data to be processed.
        escrow_public_key (str): The public key associated with the escrow account.

    Returns:
        bool: Returns True if the proof was successfully generated and verified, otherwise False.
    """
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Create client instance to interact with the Solana gateway
    client = SolanaGatewayClientProvider()

    # Fetch queries associated with the given escrow public key
    generate_queries_response = client.generate_queries(SELLER_PRIVATE_KEY, escrow_public_key)

    if 200 <= generate_queries_response.status_code < 300:
        # Assuming generate_queries_response is the response from the GET query
        generate_queries_response_json = generate_queries_response.json()

        # Fetch the 'message' key's value (for logging or debugging purposes)
        message = generate_queries_response_json.get("message")
        print(message)
    else:
        return False

    # Fetch existing queries associated with the escrow public key
    get_queries_by_escrow_pubkey_response = client.get_queries_by_escrow(escrow_public_key)

    if 200 <= get_queries_by_escrow_pubkey_response.status_code < 300:
        # Assuming get_queries_response is the response from the GET query
        get_queries_by_escrow_pubkey_response_json = get_queries_by_escrow_pubkey_response.json()

        # Fetch the 'queries' key's value (list of queries)
        queries = get_queries_by_escrow_pubkey_response_json.get("queries")
    else:
        return False

    # Separate the indices and coefficients from the queries
    indices = [query[0] for query in queries]
    coefficients = [int(query[1], 16) for query in queries]

    # Initialize the variables for σ and μ
    σ = None
    μ: int = 0

    # Process the file to calculate σ and μ
    with open(file_path, "rb") as f:
        block_index: int = 0

        while True:
            # Read the next block (data + authenticator)
            full_block: bytes = f.read(BLOCK_SIZE + MAC_SIZE_3D)  # up-to 1024-byte data, 4-byte * 3 for 3d point authenticator tag
            if not full_block:
                break  # End of file

            # Extract m_i from the block data
            m_i: int = int.from_bytes(full_block[:-MAC_SIZE_3D], byteorder='big') % p

            # Extract 3D MAC (x, y, z coordinates)
            _3d_mac: bytes = full_block[-MAC_SIZE_3D:]
            mac_x_coordinate: bytes = _3d_mac[0:MAC_SIZE]  # Bytes 0 - (MAC_SIZE - 1)
            mac_y_coordinate: bytes = _3d_mac[MAC_SIZE:2 * MAC_SIZE]  # Bytes (MAC_SIZE) - (2 * MAC_SIZE - 1)
            mac_z_coordinate: bytes = _3d_mac[2 * MAC_SIZE:3 * MAC_SIZE]  # Bytes (2 * MAC_SIZE) - (3 * MAC_SIZE - 1)

            # Convert MAC coordinates to integers
            mac_x_coordinate_as_int = int.from_bytes(mac_x_coordinate, byteorder='big')
            mac_y_coordinate_as_int = int.from_bytes(mac_y_coordinate, byteorder='big')
            mac_z_coordinate_as_int = int.from_bytes(mac_z_coordinate, byteorder='big')

            # Create the σ_i tuple for the current block
            σ_i = (bls_opt.FQ(mac_x_coordinate_as_int), bls_opt.FQ(mac_y_coordinate_as_int),
                   bls_opt.FQ(mac_z_coordinate_as_int))

            # If this block's index is part of the queries, calculate the corresponding values
            if block_index in indices:
                v_i: int = coefficients[indices.index(block_index)]
                σ_i_power_v_i = bls_opt.multiply(σ_i, v_i)  # (σ_i)^(v_i)

                # Aggregate the σ_i values
                if σ is None:
                    σ = σ_i_power_v_i
                else:
                    σ = bls_opt.add(σ, σ_i_power_v_i)

                # Update μ with the corresponding value
                v_i_multiply_m_i = (v_i * m_i) % p
                μ = (μ + v_i_multiply_m_i) % p

            block_index += 1

    # Send the proof request to the Solana gateway
    prove_response = client.prove(SELLER_PRIVATE_KEY, escrow_public_key, compress_g1_to_hex(σ), μ.to_bytes(32, 'big').hex())

    if 200 <= prove_response.status_code < 300:
        # Assuming prove_response is the response from the prove request
        prove_response_json = prove_response.json()

        try:
            # Fetch the 'message' from request body
            message = prove_response_json.get("message")
            if message == "Subscription extended successfully":
                return True  # Return True to indicate the proof was successfully generated and verified
        except Exception as e:
            print(f"Exception occurred while parsing prove request: {str(e)}")
            return False

    return False  # Return False if the proof request failed
