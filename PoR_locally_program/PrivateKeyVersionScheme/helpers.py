# Standard library imports
from typing import Type

# Third-party library imports
import galois
from galois import FieldArray

# Local imports
from PRFs import hmac_prf


def galois_field_element_to_bytes(element: FieldArray, num_bytes: int) -> bytes:
    """
    Convert a Galois Field (GF) element to its byte representation.

    :param element: The Galois Field element to convert.
    :param num_bytes: The desired length of the byte representation.
    :return: A byte representation of the element in big-endian order.
    """
    # Ensure the element is an integer
    element_as_int: int = int(element)

    # Convert the integer to a byte array
    return element_as_int.to_bytes(num_bytes, byteorder='big')


def get_blocks_authenticators_by_file_path(
        file_path: str,
        α: FieldArray,
        block_size: int,
        k: int,
        p: int,
        mac_size: int
) -> list[tuple[bytes, bytes]]:
    """
    Reads a file and generates authenticators for each block using a combination of
    HMAC and finite field arithmetic.

    Args:
    - file_path (str): Path to the file to be processed.
    - α (FieldArray): A constant multiplier used in the authenticator generation.
    - block_size (int): The size of each block (in bytes) to be read from the file.
    - k (int): A key used in the HMAC function for block-specific authentication.
    - p (int): The prime number used to define the finite field.
    - mac_size (int): The desired size of the MAC (Authenticator) in bytes.

    Returns:
    - list[tuple[bytes, bytes]]: A list of tuples where each tuple contains:
        - The block of data (bytes).
        - The authenticator (MAC) for the block (bytes).
    """
    blocks_with_authenticators: list[tuple[bytes, bytes]] = []

    # Open the file for reading
    with open(file_path, "rb") as f:
        GF: Type[FieldArray] = galois.GF(p)  # Define the finite field GF(p)
        block_index: int = 0

        while True:
            # Read the next block of data from the file
            block: bytes = f.read(block_size)
            if not block:  # End of file
                break

            # Generate the block-specific value for HMAC
            f_k_i: FieldArray = GF(hmac_prf(k, block_index) % p)
            block_in_z_p: FieldArray = GF(int.from_bytes(block, byteorder='big') % p)

            # Calculate the authenticator for the block using finite field arithmetic
            σ_i: FieldArray = f_k_i + α * block_in_z_p

            # Convert the authenticator to bytes
            σ_i_in_bytes: bytes = galois_field_element_to_bytes(σ_i, mac_size)

            # Append the block and its authenticator to the result list
            blocks_with_authenticators.append((block, σ_i_in_bytes))

            block_index += 1

    return blocks_with_authenticators


def is_prime(n: int) -> bool:
    """Check if a number is prime."""
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
