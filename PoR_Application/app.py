# Standard library imports
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

# Third-party library imports
from enum import Enum
from PIL import ImageTk, Image

# Local imports
from BLS_12_381.helpers import get_blocks_authenticators_by_file_path, p, MAC_SIZE, BLOCK_SIZE, generate_x, \
    generate_g, generate_v, generate_u, compress_g2_to_hex, compress_g1_to_hex, MAC_SIZE_3D
from Common.helpers import write_file_by_blocks_with_authenticators, write_file_by_blocks
from Common.ReedSolomon.reedSolomon import encode_file_with_rs, decode_file_with_rs
from Common.Constants.BLS12_381Constants import G1_COMPRESS_POINT_HEX_STRING_LENGTH, G2_COMPRESS_POINT_HEX_STRING_LENGTH
from Common.Providers.solanaApiGatewayProvider import SolanaGatewayClientProvider
from Common.Constants.SolanaConstants import SOLANA_PRIVATE_KEY_BASE58_CHARACTERS_LEN, \
    SOLANA_PUBLIC_KEY_BASE58_CHARACTERS_LEN

INCLUDES_REED_SOLOMON: bool = True


class Page(Enum):
    ENCODING = "Encoding"
    DECODING = "Decoding"
    SOLANA = "Solana"


class Solana_Page(Enum):
    START_SUBSCRIPTION = "Start Subscription"
    ADD_FUNDS_TO_SUBSCRIPTION = "Add Funds to Subscription"
    END_SUBSCRIPTION = "End Subscription"
    REQUEST_FUNDS = "Request Funds"


solana_start_subscription_output_text_value: str = ""
solana_add_funds_to_subscription_output_text_value: str = ""
solana_end_subscription_output_text_value: str = ""
solana_request_funds_output_text_value: str = ""


def is_number(s: any) -> bool:
    """
    Checks if the given input can be converted to an integer.

    Args:
        s (any): The input value to check.

    Returns:
        bool: True if the input can be converted to an integer, False otherwise.
    """
    try:
        int(s)  # Try converting to an integer
        return True
    except ValueError:
        print(f"Error: '{s}' is not a valid number.")  # Debugging message
        return False


def encoding_select_file() -> None:
    """
    Opens a file dialog to select a file for encoding and stores the selected file path.

    Returns:
        None
    """
    file_path: str = filedialog.askopenfilename(title="Select a File")

    if file_path:
        file_path_to_encode_var.set(file_path)
        print(f"Selected file for encoding: {file_path}")  # Debugging message
    else:
        print("No file selected for encoding.")  # Debugging message


def decoding_select_file() -> None:
    """
    Opens a file dialog to select a file for decoding and stores the selected file path.

    Returns:
        None
    """
    file_path: str = filedialog.askopenfilename(title="Select a File")

    if file_path:
        file_path_to_decode_var.set(file_path)
        print(f"Selected file for decoding: {file_path}")  # Debugging message
    else:
        print("No file selected for decoding.")  # Debugging message


def generate_ecc_file() -> None:
    """
    Generates an ECC-encoded file by:
    - Checking if a file has been selected.
    - Asking the user to choose a destination folder.
    - Optionally applying Reed-Solomon encoding.
    - Generating cryptographic keys and authenticators.
    - Processing the file into cryptographic blocks.
    - Saving the encoded file and displaying key values.

    Returns:
        None
    """

    # Check if a file has been selected
    if not file_path_to_encode_var.get():
        messagebox.showwarning("Warning", "Please Select a File First.")
        print("Warning: No file selected for encoding.")
        return

    # Ask user to select a destination folder
    save_path: str = filedialog.askdirectory(title="Select Destination Folder")

    if save_path:
        file_name: str = os.path.basename(file_path_to_encode_var.get())
        encoded_file_name: str = file_name + ".encoded"

        file_path: str = file_path_to_encode_var.get()
        encoded_file_path: str = os.path.join(save_path, encoded_file_name)

        print(f"Selected file: {file_name}")
        print(f"Destination folder: {save_path}")
        print(f"Encoded file path: {encoded_file_path}")

        # Apply Reed-Solomon encoding if enabled
        if INCLUDES_REED_SOLOMON:
            print("Reed-Solomon encoding enabled. Starting RS encoding...")
            encoded_file_path: str = encode_file_with_rs(file_path, encoded_file_path)
            print("Reed-Solomon encoding completed.")

        try:
            # Generate cryptographic values
            x: int = generate_x()   # Private key x
            g = generate_g()        # g in G2
            v = generate_v(g, x)    # v = g^x in G2
            u = generate_u()        # u in G1

            print(f"Generated x (private key): {x}")
            print(f"Generated g (G2 point): {compress_g2_to_hex(g)}")
            print(f"Generated v (g^x in G2): {compress_g2_to_hex(v)}")
            print(f"Generated u (G1 point): {compress_g1_to_hex(u)}")

            # Process the file into blocks with cryptographic authenticators
            blocks_with_authenticators: list[tuple[bytes, bytes]] = get_blocks_authenticators_by_file_path(encoded_file_path,
                                                                                                           BLOCK_SIZE,
                                                                                                           p,
                                                                                                           x,
                                                                                                           u,
                                                                                                           MAC_SIZE)
            print(f"Total blocks with authenticators generated: {len(blocks_with_authenticators)}")

            # Write the processed blocks to the encoded file
            write_file_by_blocks_with_authenticators(encoded_file_path, blocks_with_authenticators)
            print(f"Encoded file successfully written to {encoded_file_path}")

            # Display values in the UI
            encoding_output_text.config(state=tk.NORMAL)
            encoding_output_text.delete("1.0", tk.END)
            encoding_output_text.insert(tk.END, f"g (in G2): {compress_g2_to_hex(g)}\n")
            encoding_output_text.insert(tk.END, f"v (g^x in G2): {compress_g2_to_hex(v)}\n")
            encoding_output_text.insert(tk.END, f"u (in G1): {compress_g1_to_hex(u)}\n")
            encoding_output_text.insert(tk.END, f"x (private key): {x}\n")
            encoding_output_text.config(state=tk.DISABLED)

            messagebox.showinfo("Success", f"ECC File Copied to {encoded_file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to Encode File: {e}")
            print(f"Error: Failed to encode file: {e}")


def decode_ecc_file() -> None:
    """
    Decodes an ECC-encoded file by:
    - Checking if a file has been selected.
    - Asking the user to choose a destination folder.
    - Validating the selected file's extension.
    - Removing ECC authentication data and optionally decoding Reed-Solomon encoded data.
    - Saving the decoded file to the selected destination.

    Returns:
        None
    """

    # Check if a file has been selected
    if not file_path_to_decode_var.get():
        messagebox.showwarning("Warning", "Please Select a File First.")
        print("Warning: No file selected for decoding.")
        return

    # Ask user to select a destination folder
    save_path: str = filedialog.askdirectory(title="Select Destination Folder")

    if save_path:
        file_name: str = os.path.basename(file_path_to_decode_var.get())
        print(f"Selected file: {file_name}")
        print(f"Destination folder: {save_path}")

        # Validate file extension
        if not file_name.endswith(".encoded"):
            messagebox.showwarning("Warning", "Selected File Must Have a \".encoded\" Extension.")
            print("Warning: Selected file does not have the \".encoded\" extension.")
            return

        # Generate decoded file name by removing ".encoded" suffix
        decoded_file_name: str = file_name.removesuffix(".encoded")
        file_path: str = file_path_to_decode_var.get()
        decoded_file_path: str = os.path.join(save_path, decoded_file_name)

        print(f"Decoding file: {file_path}")
        print(f"Decoded file path: {decoded_file_path}")

        try:
            blocks: list[bytes] = []

            # Read the encoded file and extract blocks
            with open(file_path, "rb") as f:
                while True:
                    # Read the next block (data + authenticator)
                    full_block: bytes = f.read(
                        BLOCK_SIZE + MAC_SIZE_3D
                    )  # Up to 1024-byte data, 4-byte * 3 for 3D point authenticator tag
                    if not full_block:
                        break  # End of file reached

                    # Remove the MAC authenticator from the block
                    blocks.append(full_block[:-MAC_SIZE_3D])

            print(f"Total blocks read: {len(blocks)}")

            # Write processed blocks of data to a new file
            write_file_by_blocks(file_path, blocks)
            print(f"File successfully written to {file_path}")

            # Decode using Reed-Solomon if applicable
            if INCLUDES_REED_SOLOMON:
                print("Reed-Solomon decoding enabled. Starting RS decoding...")
                decode_file_with_rs(file_path, decoded_file_path)
                print("Reed-Solomon decoding completed.")

            messagebox.showinfo("Success", f"Decoded File Saved to {decoded_file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to Decode File: {e}")
            print(f"Error: Failed to decode file: {e}")


def start_subscription() -> None:
    """
    Starts the subscription process by validating user inputs and sending the request to
    the Solana gateway. Displays the result in the output text widget.

    This function:
    - Validates user inputs such as private/public keys, G1/G2 points, and numerical values.
    - Sends the subscription request to the Solana gateway if inputs are valid.
    - Displays results or error messages in the output text widget.

    Returns:
        None
    """
    global solana_start_subscription_output_text_value

    # Retrieve user inputs from the subscription frame
    buyer_private_key: str = start_subscription_frame_buyer_private_key_var.get().strip()
    seller_public_key: str = start_subscription_frame_seller_public_key_var.get().strip()
    u: str = start_subscription_frame_u_var.get().strip()
    g: str = start_subscription_frame_g_var.get().strip()
    v: str = start_subscription_frame_v_var.get().strip()
    query_size: str = start_subscription_frame_query_size_var.get().strip()
    blocks_number: str = start_subscription_frame_blocks_number_var.get().strip()
    validate_every: str = start_subscription_frame_validate_every_var.get().strip()

    # Enable text area and clear any previous output
    solana_start_subscription_output_text.config(state=tk.NORMAL)
    solana_start_subscription_output_text.delete("1.0", tk.END)

    # Validate inputs, setting is_valid_input to False if any validation fails
    is_valid_input: bool = True

    # Validate buyer private key
    if not buyer_private_key:
        solana_start_subscription_output_text.insert(tk.END, "Buyer private key is required\n")
        is_valid_input = False
    elif len(buyer_private_key) != SOLANA_PRIVATE_KEY_BASE58_CHARACTERS_LEN:
        solana_start_subscription_output_text.insert(tk.END, f"Buyer private key is invalid - must be of {SOLANA_PRIVATE_KEY_BASE58_CHARACTERS_LEN} length\n")
        is_valid_input = False

    # Validate seller public key
    if not seller_public_key:
        solana_start_subscription_output_text.insert(tk.END, "Seller public key is required\n")
        is_valid_input = False
    elif len(seller_public_key) != SOLANA_PUBLIC_KEY_BASE58_CHARACTERS_LEN:
        solana_start_subscription_output_text.insert(tk.END, f"Seller public key is invalid - must be of {SOLANA_PUBLIC_KEY_BASE58_CHARACTERS_LEN} length\n")
        is_valid_input = False

    # Validate u - G1 point
    if not u:
        solana_start_subscription_output_text.insert(tk.END, "u - G1 point is required\n")
        is_valid_input = False
    elif len(u) != G1_COMPRESS_POINT_HEX_STRING_LENGTH:
        solana_start_subscription_output_text.insert(tk.END, f"u - G1 point is invalid - must be of {G1_COMPRESS_POINT_HEX_STRING_LENGTH} length\n")
        is_valid_input = False

    # Validate g - G2 point
    if not g:
        solana_start_subscription_output_text.insert(tk.END, "g - G2 point is required\n")
        is_valid_input = False
    elif len(g) != G2_COMPRESS_POINT_HEX_STRING_LENGTH:
        solana_start_subscription_output_text.insert(tk.END, f"g - G2 point is invalid - must be of {G2_COMPRESS_POINT_HEX_STRING_LENGTH} length\n")
        is_valid_input = False

    # Validate v - G2 point
    if not v:
        solana_start_subscription_output_text.insert(tk.END, "v - G2 point is required\n")
        is_valid_input = False
    elif len(v) != G2_COMPRESS_POINT_HEX_STRING_LENGTH:
        solana_start_subscription_output_text.insert(tk.END, f"v - G2 point is invalid - must be of {G2_COMPRESS_POINT_HEX_STRING_LENGTH} length\n")
        is_valid_input = False

    # Validate query size
    if not query_size:
        solana_start_subscription_output_text.insert(tk.END, "Query size is required\n")
        is_valid_input = False
    elif not is_number(query_size):
        solana_start_subscription_output_text.insert(tk.END, "Query size is invalid - must be number\n")
        is_valid_input = False

    # Validate blocks number
    if not blocks_number:
        solana_start_subscription_output_text.insert(tk.END, "Block number is required\n")
        is_valid_input = False
    elif not is_number(blocks_number):
        solana_start_subscription_output_text.insert(tk.END, "Block number is invalid - must be number\n")
        is_valid_input = False

    # Validate validate every
    if not validate_every:
        solana_start_subscription_output_text.insert(tk.END, "Validate every is required\n")
        is_valid_input = False
    elif not is_number(validate_every):
        solana_start_subscription_output_text.insert(tk.END, "Validate every is invalid - must be number\n")
        is_valid_input = False

    # If all inputs are valid, proceed with the subscription request
    if is_valid_input:
        print("Inputs are valid, proceeding with subscription request.")
        client: SolanaGatewayClientProvider = SolanaGatewayClientProvider()

        # Send the request to start the subscription
        response = client.start_subscription(
            buyer_private_key, seller_public_key, u, g, v,
            int(query_size), int(blocks_number), int(validate_every)
        )

        # Check the response status code
        if 200 <= response.status_code < 300:
            print(f"Subscription started successfully. Status code: {response.status_code}")
            response_json = response.json()

            # Extract the escrow public key from the response
            escrow_public_key: str = response_json.get("escrow_pubkey")
            print(f"Escrow public key: {escrow_public_key}")

            # Display the escrow public key in the output
            solana_start_subscription_output_text.insert(tk.END, f"Escrow public key: {escrow_public_key}\n")
        else:
            print(f"Error: Request failed with status code {response.status_code}. Response text: {response.text}")
            solana_start_subscription_output_text.insert(tk.END, f"Request {response.status_code} error: {response.text}\n")

    # Capture the output text after processing and disable editing
    solana_start_subscription_output_text_value = solana_start_subscription_output_text.get("1.0", tk.END)
    solana_start_subscription_output_text.config(state=tk.DISABLED)


def add_funds_to_subscription() -> None:
    """
    Handles adding funds to a Solana subscription by validating user inputs and sending a request.

    Retrieves the buyer's private key, escrow public key, and the amount of lamports from the UI,
    validates them, and then interacts with the Solana gateway client to add funds.
    """
    global solana_add_funds_to_subscription_output_text_value

    # Retrieve input values from UI
    buyer_private_key: str = add_funds_to_subscription_frame_buyer_private_key_var.get().strip()
    escrow_public_key: str = add_funds_to_subscription_frame_escrow_public_key_var.get().strip()
    lamports_amount: str = add_funds_to_subscription_frame_lamports_amount_var.get().strip()

    # Reset output text field
    solana_add_funds_to_subscription_output_text.config(state=tk.NORMAL)
    solana_add_funds_to_subscription_output_text.delete("1.0", tk.END)

    # Input validation
    is_valid_input: bool = True

    if not buyer_private_key:
        solana_add_funds_to_subscription_output_text.insert(tk.END, "Buyer private key is required\n")
        print("Validation error: Buyer private key is missing")
        is_valid_input = False
    elif len(buyer_private_key) != SOLANA_PRIVATE_KEY_BASE58_CHARACTERS_LEN:
        solana_add_funds_to_subscription_output_text.insert(
            tk.END,
            f"Buyer private key is invalid - must be {SOLANA_PRIVATE_KEY_BASE58_CHARACTERS_LEN} characters long\n"
        )
        print(f"Validation error: Buyer private key length is incorrect ({len(buyer_private_key)} characters)")
        is_valid_input = False

    if not escrow_public_key:
        solana_add_funds_to_subscription_output_text.insert(tk.END, "Escrow public key is required\n")
        print("Validation error: Escrow public key is missing")
        is_valid_input = False
    elif len(escrow_public_key) != SOLANA_PUBLIC_KEY_BASE58_CHARACTERS_LEN:
        solana_add_funds_to_subscription_output_text.insert(
            tk.END,
            f"Escrow public key is invalid - must be {SOLANA_PUBLIC_KEY_BASE58_CHARACTERS_LEN} characters long\n"
        )
        print(f"Validation error: Escrow public key length is incorrect ({len(escrow_public_key)} characters)")
        is_valid_input = False

    if not lamports_amount:
        solana_add_funds_to_subscription_output_text.insert(tk.END, "Lamports amount is required\n")
        print("Validation error: Lamports amount is missing")
        is_valid_input = False
    elif not is_number(lamports_amount):
        solana_add_funds_to_subscription_output_text.insert(tk.END, "Lamports amount is invalid - must be a number\n")
        print(f"Validation error: Lamports amount is not a valid number ({lamports_amount})")
        is_valid_input = False

    # If all inputs are valid, proceed with API request
    if is_valid_input:
        print(f"Sending request to add {lamports_amount} lamports to subscription")
        client: SolanaGatewayClientProvider = SolanaGatewayClientProvider()
        response = client.add_funds_to_subscription(buyer_private_key, escrow_public_key, int(lamports_amount))

        # Process response
        if 200 <= response.status_code < 300:
            response_json = response.json()
            message: str = response_json.get("message", "No message returned")

            solana_add_funds_to_subscription_output_text.insert(tk.END, f"{message}\n")
            print(f"Success: {message}")
        else:
            solana_add_funds_to_subscription_output_text.insert(
                tk.END, f"Request {response.status_code} error: {response.text}\n"
            )
            print(f"Error: Request failed with status {response.status_code} - {response.text}")

    # Store and disable output text field
    solana_add_funds_to_subscription_output_text_value = solana_add_funds_to_subscription_output_text.get("1.0", tk.END)
    solana_add_funds_to_subscription_output_text.config(state=tk.DISABLED)


def end_subscription() -> None:
    """
    Handles the termination of a Solana subscription by validating user inputs and sending a request.

    Retrieves the buyer's private key and escrow public key from the UI, validates them, and then
    interacts with the Solana gateway client to end the subscription.
    """
    global solana_end_subscription_output_text_value

    # Retrieve input values from UI
    buyer_private_key: str = end_subscription_frame_buyer_private_key_var.get().strip()
    escrow_public_key: str = end_subscription_frame_escrow_public_key_var.get().strip()

    # Reset output text field
    solana_end_subscription_output_text.config(state=tk.NORMAL)
    solana_end_subscription_output_text.delete("1.0", tk.END)

    # Input validation
    is_valid_input: bool = True

    if not buyer_private_key:
        solana_end_subscription_output_text.insert(tk.END, "Buyer private key is required\n")
        print("Validation error: Buyer private key is missing")
        is_valid_input = False
    elif len(buyer_private_key) != SOLANA_PRIVATE_KEY_BASE58_CHARACTERS_LEN:
        solana_end_subscription_output_text.insert(
            tk.END, f"Buyer private key is invalid - must be {SOLANA_PRIVATE_KEY_BASE58_CHARACTERS_LEN} characters long\n"
        )
        print(f"Validation error: Buyer private key length is incorrect ({len(buyer_private_key)} characters)")
        is_valid_input = False

    if not escrow_public_key:
        solana_end_subscription_output_text.insert(tk.END, "Escrow public key is required\n")
        print("Validation error: Escrow public key is missing")
        is_valid_input = False
    elif len(escrow_public_key) != SOLANA_PUBLIC_KEY_BASE58_CHARACTERS_LEN:
        solana_end_subscription_output_text.insert(
            tk.END, f"Escrow public key is invalid - must be {SOLANA_PUBLIC_KEY_BASE58_CHARACTERS_LEN} characters long\n"
        )
        print(f"Validation error: Escrow public key length is incorrect ({len(escrow_public_key)} characters)")
        is_valid_input = False

    # If inputs are valid, proceed with API request
    if is_valid_input:
        print(f"Attempting to end subscription for escrow account: {escrow_public_key}")
        client: SolanaGatewayClientProvider = SolanaGatewayClientProvider()
        response = client.end_subscription_by_buyer(buyer_private_key, escrow_public_key)

        # Process response
        if 200 <= response.status_code < 300:
            response_json = response.json()
            message: str = response_json.get("message", "Subscription successfully ended")

            solana_end_subscription_output_text.insert(tk.END, f"{message}\n")
            print(f"Success: {message}")
        else:
            error_message: str = f"Request {response.status_code} error: {response.text}"
            solana_end_subscription_output_text.insert(tk.END, f"{error_message}\n")
            print(error_message)

    # Store and disable output text field
    solana_end_subscription_output_text_value = solana_end_subscription_output_text.get("1.0", tk.END)
    solana_end_subscription_output_text.config(state=tk.DISABLED)


def request_funds() -> None:
    """
    Handles a request for funds withdrawal from an escrow account on Solana.

    Retrieves the buyer's private key and escrow public key from the UI, validates them,
    and then interacts with the Solana gateway client to request funds.
    """
    global solana_request_funds_output_text_value

    # Retrieve input values from UI
    buyer_private_key: str = request_funds_frame_buyer_private_key_var.get().strip()
    escrow_public_key: str = request_funds_frame_escrow_public_key_var.get().strip()

    # Reset output text field
    solana_request_funds_output_text.config(state=tk.NORMAL)
    solana_request_funds_output_text.delete("1.0", tk.END)

    # Input validation
    is_valid_input: bool = True

    if not buyer_private_key:
        solana_request_funds_output_text.insert(tk.END, "Buyer private key is required\n")
        print("Validation error: Buyer private key is missing")
        is_valid_input = False
    elif len(buyer_private_key) != SOLANA_PRIVATE_KEY_BASE58_CHARACTERS_LEN:
        solana_request_funds_output_text.insert(
            tk.END, f"Buyer private key is invalid - must be {SOLANA_PRIVATE_KEY_BASE58_CHARACTERS_LEN} characters long\n"
        )
        print(f"Validation error: Buyer private key length is incorrect ({len(buyer_private_key)} characters)")
        is_valid_input = False

    if not escrow_public_key:
        solana_request_funds_output_text.insert(tk.END, "Escrow public key is required\n")
        print("Validation error: Escrow public key is missing")
        is_valid_input = False
    elif len(escrow_public_key) != SOLANA_PUBLIC_KEY_BASE58_CHARACTERS_LEN:
        solana_request_funds_output_text.insert(
            tk.END, f"Escrow public key is invalid - must be {SOLANA_PUBLIC_KEY_BASE58_CHARACTERS_LEN} characters long\n"
        )
        print(f"Validation error: Escrow public key length is incorrect ({len(escrow_public_key)} characters)")
        is_valid_input = False

    # If inputs are valid, proceed with API request
    if is_valid_input:
        print(f"Attempting to request funds from escrow account: {escrow_public_key}")
        client = SolanaGatewayClientProvider()
        response = client.request_funds(buyer_private_key, escrow_public_key)

        # Process response
        if 200 <= response.status_code < 300:
            response_json = response.json()
            message: str = response_json.get("message", "Funds request successfully processed")

            solana_request_funds_output_text.insert(tk.END, f"{message}\n")
            print(f"Success: {message}")
        else:
            error_message = f"Request {response.status_code} error: {response.text}"
            solana_request_funds_output_text.insert(tk.END, f"{error_message}\n")
            print(error_message)

    # Store and disable output text field
    solana_request_funds_output_text_value = solana_request_funds_output_text.get("1.0", tk.END)
    solana_request_funds_output_text.config(state=tk.DISABLED)


def update_solana_content(button_frame, selected_solana_page_option) -> None:
    """
    Updates the Solana content frame based on the selected option.
    Clears the frame, updates button styles, and dynamically creates UI elements.
    """

    # Clear the current content in the solana_content_frame
    for widget in solana_content_frame.winfo_children():
        widget.destroy()

    # Update button colors based on the selected option
    for child in button_frame.winfo_children():
        if isinstance(child, ttk.Button):
            if child.cget("text") == selected_solana_page_option.value:
                child.configure(style="Selected.TButton")
            else:
                child.configure(style="Rounded.TButton")

    if selected_solana_page_option == Solana_Page.START_SUBSCRIPTION:
        # Add content for "Start Subscription"
        tk.Label(solana_content_frame, text="Buyer Private Key:", bg=content_background_color, fg="#000000").pack()
        ttk.Entry(solana_content_frame, textvariable=start_subscription_frame_buyer_private_key_var, width=50).pack(pady=5)

        tk.Label(solana_content_frame, text="Seller Public Key:", bg=content_background_color, fg="#000000").pack()
        ttk.Entry(solana_content_frame, textvariable=start_subscription_frame_seller_public_key_var, width=50).pack(pady=5)

        # Create a frame for aligned inputs
        param_frame = tk.Frame(solana_content_frame, bg=content_background_color)
        param_frame.pack(pady=5)

        # First row: u, g, v
        tk.Label(param_frame, text="u:", bg=content_background_color, fg="#000000").grid(row=0, column=0, padx=5)
        ttk.Entry(param_frame, textvariable=start_subscription_frame_u_var, width=15).grid(row=0, column=1, padx=5)

        tk.Label(param_frame, text="g:", bg=content_background_color, fg="#000000").grid(row=1, column=0, padx=5)
        ttk.Entry(param_frame, textvariable=start_subscription_frame_g_var, width=15).grid(row=1, column=1, padx=5)

        tk.Label(param_frame, text="v:", bg=content_background_color, fg="#000000").grid(row=2, column=0, padx=5)
        ttk.Entry(param_frame, textvariable=start_subscription_frame_v_var, width=15).grid(row=2, column=1, padx=5)

        # Second row: query_size, blocks_number, validate_every
        tk.Label(param_frame, text="Query Size:", bg=content_background_color, fg="#000000").grid(row=0, column=2,
                                                                                                  padx=5)
        ttk.Entry(param_frame, textvariable=start_subscription_frame_query_size_var, width=15).grid(row=0, column=3,
                                                                                                    padx=5)

        tk.Label(param_frame, text="Blocks Number:", bg=content_background_color, fg="#000000").grid(row=1, column=2,
                                                                                                     padx=5)
        ttk.Entry(param_frame, textvariable=start_subscription_frame_blocks_number_var, width=15).grid(row=1, column=3,
                                                                                                       padx=5)

        tk.Label(param_frame, text="Validate Every:", bg=content_background_color, fg="#000000").grid(row=2, column=2,
                                                                                                      padx=5)
        ttk.Entry(param_frame, textvariable=start_subscription_frame_validate_every_var, width=15).grid(row=2, column=3,
                                                                                                        padx=5)

        # Button to start the subscription
        ttk.Button(solana_content_frame, text="Send Request to Solana", command=start_subscription,
                   style="Rounded.TButton").pack(pady=5)

        global solana_start_subscription_output_text
        solana_start_subscription_output_text = tk.Text(solana_content_frame, height=15, width=80, wrap=tk.WORD)
        solana_start_subscription_output_text.pack(pady=10)
        solana_start_subscription_output_text.config(state=tk.DISABLED)

        if solana_start_subscription_output_text_value:
            solana_start_subscription_output_text.config(state=tk.NORMAL)
            solana_start_subscription_output_text.insert(tk.END, solana_start_subscription_output_text_value)
            solana_start_subscription_output_text.config(state=tk.DISABLED)

    elif selected_solana_page_option == Solana_Page.ADD_FUNDS_TO_SUBSCRIPTION:
        # Add content for "Add Funds to Subscription"
        tk.Label(solana_content_frame, text="Buyer Private Key:", bg=content_background_color, fg="#000000").pack()
        ttk.Entry(solana_content_frame, textvariable=add_funds_to_subscription_frame_buyer_private_key_var, width=50).pack(pady=5)

        tk.Label(solana_content_frame, text="Escrow Public Key:", bg=content_background_color, fg="#000000").pack()
        ttk.Entry(solana_content_frame, textvariable=add_funds_to_subscription_frame_escrow_public_key_var, width=50).pack(pady=5)

        tk.Label(solana_content_frame, text="Lamports Amount to Add:", bg=content_background_color, fg="#000000").pack()
        ttk.Entry(solana_content_frame, textvariable=add_funds_to_subscription_frame_lamports_amount_var, width=50).pack(pady=5)

        # Button to add funds to the subscription
        ttk.Button(solana_content_frame, text="Send Request to Solana", command=add_funds_to_subscription, style="Rounded.TButton").pack(pady=5)

        global solana_add_funds_to_subscription_output_text
        solana_add_funds_to_subscription_output_text = tk.Text(solana_content_frame, height=15, width=80, wrap=tk.WORD)
        solana_add_funds_to_subscription_output_text.pack(pady=10)
        solana_add_funds_to_subscription_output_text.config(state=tk.DISABLED)

        if solana_add_funds_to_subscription_output_text_value:
            solana_add_funds_to_subscription_output_text.config(state=tk.NORMAL)
            solana_add_funds_to_subscription_output_text.insert(tk.END, solana_add_funds_to_subscription_output_text_value)
            solana_add_funds_to_subscription_output_text.config(state=tk.DISABLED)

    elif selected_solana_page_option == Solana_Page.END_SUBSCRIPTION:
        tk.Label(solana_content_frame, text="Buyer Private Key:", bg=content_background_color, fg="#000000").pack()
        ttk.Entry(solana_content_frame, textvariable=end_subscription_frame_buyer_private_key_var, width=50).pack(pady=5)

        tk.Label(solana_content_frame, text="Escrow Public Key:", bg=content_background_color, fg="#000000").pack()
        ttk.Entry(solana_content_frame, textvariable=end_subscription_frame_escrow_public_key_var, width=50).pack(
            pady=5)

        # Button to end the subscription
        ttk.Button(solana_content_frame, text="Send Request to Solana", command=end_subscription,
                   style="Rounded.TButton").pack(pady=5)

        global solana_end_subscription_output_text

        solana_end_subscription_output_text = tk.Text(solana_content_frame, height=15, width=80, wrap=tk.WORD)
        solana_end_subscription_output_text.pack(pady=10)
        solana_end_subscription_output_text.config(state=tk.DISABLED)

        if solana_end_subscription_output_text_value:
            solana_end_subscription_output_text.config(state=tk.NORMAL)
            solana_end_subscription_output_text.insert(tk.END, solana_end_subscription_output_text_value)
            solana_end_subscription_output_text.config(state=tk.DISABLED)

    elif selected_solana_page_option == Solana_Page.REQUEST_FUNDS:
        tk.Label(solana_content_frame, text="Buyer Private Key:", bg=content_background_color, fg="#000000").pack()
        ttk.Entry(solana_content_frame, textvariable=request_funds_frame_buyer_private_key_var, width=50).pack(pady=5)

        tk.Label(solana_content_frame, text="Escrow Public Key:", bg=content_background_color, fg="#000000").pack()
        ttk.Entry(solana_content_frame, textvariable=request_funds_frame_escrow_public_key_var, width=50).pack(pady=5)

        # Button to end the subscription
        ttk.Button(solana_content_frame, text="Send Request to Solana", command=request_funds, style="Rounded.TButton").pack(pady=5)

        global solana_request_funds_output_text
        solana_request_funds_output_text = tk.Text(solana_content_frame, height=15, width=80, wrap=tk.WORD)
        solana_request_funds_output_text.pack(pady=10)
        solana_request_funds_output_text.config(state=tk.DISABLED)

        if solana_request_funds_output_text_value:
            solana_request_funds_output_text.config(state=tk.NORMAL)
            solana_request_funds_output_text.insert(tk.END, solana_request_funds_output_text_value)
            solana_request_funds_output_text.config(state=tk.DISABLED)


def update_content(option: Page) -> None:
    """
    This function updates the content displayed in the center panel of the UI based on the selected option.

    It handles different pages (e.g., Encoding, Decoding, Solana) and updates the displayed widgets accordingly.
    - It clears the current content before adding the new content for the selected option.
    - It updates the button colors in the navigation frame to indicate the selected option.
    - Depending on the selected page, it adds relevant labels, buttons, and input fields for user interaction.

    Args:
        option (Page): The selected page option (e.g., Encoding, Decoding, Solana).
    """

    # Clear the current content in the center panel
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Update button colors based on the selected option
    for child in nav_frame.winfo_children():
        if isinstance(child, ttk.Button):
            if child.cget("text") == option.value:
                child.configure(style="Selected.TButton")
            else:
                child.configure(style="Rounded.TButton")

    if option == Page.ENCODING:
        content_title = tk.Label(content_frame, text=Page.ENCODING.value, font=("Helvetica", 18, "bold"), bg=content_background_color, fg="#000000")
        content_title.pack(pady=10)

        content_description = tk.Label(
            content_frame,
            text="Perform a full encoding and authentication.",
            wraplength=400,
            justify="center",
            bg=content_background_color,
            fg="#000000"
        )
        content_description.pack(pady=10)

        action_button = ttk.Button(content_frame, text="Select File To Encode", command=encoding_select_file, style="Rounded.TButton")
        action_button.pack(pady=20)

        file_path_label = tk.Label(content_frame, text="Selected File:", bg=content_background_color, fg="#000000")
        file_path_label.pack(pady=(10, 0))

        file_path_entry = ttk.Entry(content_frame, textvariable=file_path_to_encode_var, state="readonly", width=50)
        file_path_entry.pack(pady=5)

        save_copy_button = ttk.Button(content_frame, text="Generate ECC File", command=generate_ecc_file, style="Rounded.TButton")
        save_copy_button.pack(pady=10)

        global encoding_output_text
        encoding_output_text = tk.Text(content_frame, height=15, width=80, wrap=tk.WORD)
        encoding_output_text.pack(pady=10)
        encoding_output_text.config(state=tk.DISABLED)

    elif option == Page.DECODING:
        content_title = tk.Label(content_frame, text=Page.DECODING.value, font=("Helvetica", 18, "bold"), bg=content_background_color, fg="#000000")
        content_title.pack(pady=10)

        content_description = tk.Label(
            content_frame,
            text="Perform a full decoding.",
            wraplength=400,
            justify="center",
            bg=content_background_color,
            fg="#000000"
        )
        content_description.pack(pady=10)

        action_button = ttk.Button(content_frame, text="Select File To Decode", command=decoding_select_file, style="Rounded.TButton")
        action_button.pack(pady=20)

        file_path_label = tk.Label(content_frame, text="Selected ECC File:", bg=content_background_color, fg="#000000")
        file_path_label.pack(pady=(10, 0))

        file_path_entry = ttk.Entry(content_frame, textvariable=file_path_to_decode_var, state="readonly", width=50)
        file_path_entry.pack(pady=5)

        save_copy_button = ttk.Button(content_frame, text="Generate Decoded File", command=decode_ecc_file, style="Rounded.TButton")
        save_copy_button.pack(pady=10)

    # In the Solana page, create the frame that will change its content
    if option == Page.SOLANA:
        content_title = tk.Label(content_frame, text=Page.SOLANA.value, font=("Helvetica", 18, "bold"),
                                 bg=content_background_color, fg="#000000")
        content_title.pack(pady=10)

        # Button frame for the buttons (Start Subscription, Add Funds, End Subscription)
        button_frame = tk.Frame(content_frame, bg=content_background_color)
        button_frame.pack(pady=5)

        solana_page_options = [Solana_Page.START_SUBSCRIPTION, Solana_Page.ADD_FUNDS_TO_SUBSCRIPTION, Solana_Page.END_SUBSCRIPTION, Solana_Page.REQUEST_FUNDS]
        for solana_page_option in solana_page_options:
            ttk.Button(button_frame, text=solana_page_option.value,
                       command=lambda opt=solana_page_option: update_solana_content(button_frame, opt),
                       style="Rounded.TButton").pack(side=tk.LEFT, padx=5)

        global solana_content_frame
        # Create a new frame below the buttons for dynamic content
        solana_content_frame = tk.Frame(content_frame, bg=content_background_color)
        solana_content_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # Set initial content for "Start Subscription"
        update_solana_content(button_frame, Solana_Page.START_SUBSCRIPTION)


# Create main window
root = tk.Tk()
root.title("PoR - Crypto Course")
root.geometry("800x500")
root.resizable(False, False)
icon_image = Image.open(
    './solana-sol-logo.ico')
icon = ImageTk.PhotoImage(icon_image)
root.iconphoto(True, icon)

# Styling
nav_color = "#1c2c3c"
content_background_color = "#F5F5F5"
button_color = "#3475df"
text_color = "#FFFFFF"
default_font = ("Helvetica", 12)

# Remove button border and flat style
style = ttk.Style()
style.theme_use("clam")
style.configure("TFrame", background=content_background_color)
style.configure("TLabel", font=default_font, background=content_background_color, foreground=text_color)
style.configure("TButton", font=default_font, padding=6, background=button_color, foreground=text_color, borderwidth=0, relief="flat")
style.map("TButton",
          background=[("active", nav_color), ("!disabled", nav_color)],
          foreground=[("active", text_color), ("!disabled", text_color)])
style.configure("Rounded.TButton", font=default_font, padding=10, background=button_color, foreground=text_color, borderwidth=0, relief="flat", border=10)
style.configure("Selected.TButton", font=default_font, padding=10, background=nav_color, foreground=text_color, borderwidth=0, relief="flat", border=10)
style.map("Selected.TButton",
          background=[("active", button_color), ("!disabled", button_color)],
          foreground=[("active", text_color), ("!disabled", text_color)])

# Variable to store selected file path to encode
file_path_to_encode_var = tk.StringVar()

# Variable to store selected file path to decode
file_path_to_decode_var = tk.StringVar()

# Solana - Start subscription frame
# Variable to track private key in start subscription frame
start_subscription_frame_buyer_private_key_var = tk.StringVar()
# Variable to track seller public key in start subscription frame
start_subscription_frame_seller_public_key_var = tk.StringVar()
# Variable to track u - G2 point value in start subscription frame
start_subscription_frame_u_var = tk.StringVar()
# Variable to track g - G2 point value in start subscription frame
start_subscription_frame_g_var = tk.StringVar()
# Variable to track v - G2 point value in start subscription frame
start_subscription_frame_v_var = tk.StringVar()
# Variable to track query size in start subscription frame
start_subscription_frame_query_size_var = tk.StringVar()
# Variable to track block number in start subscription frame
start_subscription_frame_blocks_number_var = tk.StringVar()
# Variable to track validate every in start subscription frame
start_subscription_frame_validate_every_var = tk.StringVar()

# Solana - Add fund to subscription frame
# Variable to track buyer private in add fund to subscription frame
add_funds_to_subscription_frame_buyer_private_key_var = tk.StringVar()
# Variable to track escrow public in add fund to subscription frame
add_funds_to_subscription_frame_escrow_public_key_var = tk.StringVar()
# Variable to track lamports amount
add_funds_to_subscription_frame_lamports_amount_var = tk.StringVar()

# Solana - End subscription frame
# Variable to track buyer private key in end subscription frame
end_subscription_frame_buyer_private_key_var = tk.StringVar()
# Variable to track escrow public key in end subscription frame
end_subscription_frame_escrow_public_key_var = tk.StringVar()

# Solana - Request funds frame
# Variable to track buyer private key in request funds frame
request_funds_frame_buyer_private_key_var = tk.StringVar()
# Variable to track escrow public key in request funds frame
request_funds_frame_escrow_public_key_var = tk.StringVar()

# Main layout
main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

# Left navigation panel
nav_frame = tk.Frame(main_frame, width=200, bg=nav_color)
nav_frame.pack(side=tk.LEFT, fill=tk.Y)

nav_label = tk.Label(nav_frame, text="PoR - Crypto Course", font=("Helvetica", 16, "bold"), bg=nav_color, fg=text_color, anchor="center")
nav_label.pack(pady=20)

# Menu options
menu_options = [Page.ENCODING, Page.DECODING, Page.SOLANA]
for option in menu_options:
    btn = ttk.Button(nav_frame, text=option.value, command=lambda opt=option: update_content(opt))
    btn.pack(fill=tk.X, pady=5, ipadx=10)  # Fill horizontally across the nav_frame

# Right content panel
content_frame = tk.Frame(main_frame, bg=content_background_color)
content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)

# Initially load Encryption content
update_content(Page.ENCODING)

# Start GUI main loop
root.mainloop()
