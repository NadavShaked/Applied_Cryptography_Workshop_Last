# Standard library imports
import os

# Local imports
from .Common.Providers.solanaApiGatewayProvider import SolanaGatewayClientProvider
from .config import UPLOAD_FOLDER
from .constants import SELLER_PRIVATE_KEY


def get_escrow_data(escrow_public_key: str):
    """
    Fetches escrow data for the provided public key from the Solana gateway client.

    This function:
    - Initializes the Solana client.
    - Sends a request to get escrow data associated with the provided public key.
    - Returns the JSON response from the Solana gateway if the request is successful.

    Args:
        escrow_public_key (str): The public key of the escrow account.

    Returns:
        dict: The JSON response from the Solana gateway containing the escrow data.
    """
    try:
        # Initialize Solana client and get escrow data
        client = SolanaGatewayClientProvider()
        print(f"Fetching escrow data for escrow public key: {escrow_public_key} using the Solana client")

        # Send the request to fetch escrow data
        get_escrow_data_response = client.get_escrow_data(escrow_public_key)

        # Check if the response from the Solana client is successful
        if 200 <= get_escrow_data_response.status_code < 300:
            print("Successfully fetched escrow data.")
            return get_escrow_data_response.json()
        else:
            print(f"Failed to fetch escrow data, status code: {get_escrow_data_response.status_code}")
            return None

    except Exception as e:
        print(f"Exception occurred while fetching escrow data: {str(e)}")
        return None


def request_funds(escrow_public_key: str) -> bool:
    """
    Requests funds from the Solana gateway for a specified escrow public key.

    This function:
    - Sends a request to the Solana gateway to request funds from the escrow account.
    - Logs the response message for debugging purposes.
    - Returns True if the request is successful, or False if it fails.

    Args:
        escrow_public_key (str): The public key of the escrow account to request funds from.

    Returns:
        bool: True if the fund request was successful, False otherwise.
    """
    try:
        # Initialize Solana client and send request for funds
        client = SolanaGatewayClientProvider()
        print(f"Requesting funds from escrow public key: {escrow_public_key} using the Solana client")

        # Send the request to the Solana client for funds
        request_funds_response = client.request_funds(SELLER_PRIVATE_KEY, escrow_public_key)

        # Check if the response from the Solana client is successful (status code 2xx)
        if 200 <= request_funds_response.status_code < 300:
            request_funds_response_json = request_funds_response.json()
            message = request_funds_response_json.get("message")
            print(f"Fund request successful. Message: {message}")
            return True
        else:
            print(f"Request Fund Failed. Status Code: {request_funds_response.status_code}")
            return False

    except Exception as e:
        print(f"Exception occurred while requesting funds: {str(e)}")
        return False


def end_subscription_by_seller(escrow_public_key: str) -> bool:
    """
    Ends a subscription by the seller for the specified escrow public key.

    This function:
    - Sends a request to the Solana gateway to end the subscription for the escrow account.
    - Logs the response message for debugging purposes.
    - Returns True if the request is successful, or False if it fails.

    Args:
        escrow_public_key (str): The public key of the escrow account for which to end the subscription.

    Returns:
        bool: True if the subscription was successfully ended, False otherwise.
    """
    try:
        # Initialize Solana client and send request to end subscription
        client = SolanaGatewayClientProvider()
        print(f"Ending subscription for escrow public key: {escrow_public_key} using the Solana client")

        # Send the request to the Solana client to end the subscription
        request_funds_response = client.end_subscription_by_seller(SELLER_PRIVATE_KEY, escrow_public_key)

        # Check if the response from the Solana client is successful (status code 2xx)
        if 200 <= request_funds_response.status_code < 300:
            request_funds_response_json = request_funds_response.json()
            message = request_funds_response_json.get("message")
            print(f"Subscription ended successfully. Message: {message}")
            return True
        else:
            print(f"End Subscription Failed. Status Code: {request_funds_response.status_code}")
            return False

    except Exception as e:
        print(f"Exception occurred while ending subscription: {str(e)}")
        return False


def delete_file_from_storage_server(file_name: str):
    """
    Deletes a file from the storage server.

    This function:
    - Constructs the full file path based on the provided filename.
    - Checks if the file exists in the storage directory.
    - Deletes the file if it exists and logs the success message.
    - Logs an error message if the file does not exist.

    Args:
        file_name (str): The name of the file to be deleted.

    Returns:
        None
    """
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    print(f"Attempting to delete file: {file_path}")

    # Check if the file exists at the specified path
    if os.path.exists(file_path):
        try:
            # Remove the file
            os.remove(file_path)
            print(f"File {file_path} deleted successfully.")
        except Exception as e:
            print(f"Error deleting file {file_path}: {str(e)}")
    else:
        print(f"The file {file_path} does not exist.")
