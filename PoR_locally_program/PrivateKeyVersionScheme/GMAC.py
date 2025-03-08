# Standard library imports
import os

# Third-party library imports
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


BLOCK_SIZE: int = 1024
NONCE_SIZE: int = 12
GMAC_SIZE: int = 16


def convert_index_to_bytes(index: int, max_bytes_size: int = 32) -> bytes:
    """
    Converts an index into bytes with a specified maximum byte size.

    Args:
    - index (int): The index to convert.
    - max_bytes_size (int, optional): The maximum byte size for the index. Default is 16 bytes.

    Returns:
    - bytes: The index as bytes, fitting within the specified byte size.
    """
    index_in_bytes = index.to_bytes(max_bytes_size, byteorder='big')

    return index_in_bytes


def process_file_with_gmac(file_path: str, block_size: int = 1024) -> (list[tuple[int, bytes, bytes]], bytes):
    """
    Processes a file and generates GMAC (Galois Message Authentication Code) for each block using AES-GCM.

    Args:
    - file_path (str): Path to the file to be processed.
    - block_size (int): Size of each block to read from the file (default 1024 bytes).

    Returns:
    - list[tuple[int, bytes, bytes]]: List of tuples where each tuple contains:
        - block number (int),
        - nonce (bytes),
        - block with appended GMAC (bytes).
    - bytes: The randomly generated 256-bit AES key used for encryption.

    Logs:
    - Information and error logs during file processing.
    """
    # Generate a random 256-bit (32-byte) AES key
    key: bytes = os.urandom(32)

    # Open the file for reading
    with open(file_path, "rb") as f:
        blocks_with_mac: list[tuple[int, bytes, bytes]] = []  # To store blocks with appended GMAC
        block_number: int = 0

        while True:
            # Read the next block
            block = f.read(block_size)
            if not block:  # End of file
                break

            # Generate a random nonce (12 bytes recommended for AES-GCM)
            nonce: bytes = os.urandom(NONCE_SIZE)

            # Initialize AES-GCM
            aesgcm = AESGCM(key)

            block_number_bytes: bytes = convert_index_to_bytes(block_number)
            block_with_number: bytes = block + block_number_bytes

            # Generate GMAC (encrypt empty plaintext with block as AAD)
            gmac_tag: bytes = aesgcm.encrypt(nonce, b"", block_with_number)

            # Append GMAC to the block
            block_with_mac: bytes = block + gmac_tag
            blocks_with_mac.append((block_number, nonce, block_with_mac))

            # Increment block number
            block_number += 1

    return blocks_with_mac, key  # Return processed blocks and the key for verification


def write_blocks_to_file(blocks_with_mac: list[tuple[int, bytes, bytes]], output_file: str) -> None:
    """
    Writes processed blocks with GMAC to a new output file.

    Args:
    - blocks_with_mac (list[tuple[int, bytes, bytes]]): List of blocks, each containing:
        - block number (int),
        - nonce (bytes),
        - block with appended GMAC (bytes).
    - output_file (str): Path to the output file where the processed blocks will be written.
    """
    # Write processed blocks with GMAC to a new file
    with open(output_file, "wb") as out_f:
        for _, nonce, block_with_mac in blocks_with_mac:
            # Write nonce (12 bytes), block, and its GMAC
            out_f.write(nonce + block_with_mac)


def validate_block_with_gmac(block: bytes, block_index: int, key: bytes) -> bool:
    """
    Validates a block using GMAC (Galois/Counter Mode Authentication Code) for integrity and authenticity.

    Args:
    - block (bytes): The block to validate, which includes:
        - nonce (12 bytes),
        - data (the actual data),
        - GMAC tag (last 16 bytes).
    - block_index (int): The index of the block (used as additional authenticated data).
    - key (bytes): The AES key used for the decryption and GMAC verification (256-bit key).

    Returns:
    - bool: True if the GMAC is valid and the block is authentic, False if the GMAC is invalid.
    """
    # block (nonce + data + GMAC)
    # Extract the nonce (first 12 bytes)
    nonce: bytes = block[:12]

    # Extract the data (everything in between)
    data: bytes = block[12:-16]

    # Extract the GMAC (last 16 bytes)
    gmac_tag: bytes = block[-16:]

    index_in_bytes: bytes = convert_index_to_bytes(block_index)
    data_with_index: bytes = data + index_in_bytes

    # Recompute GMAC for the block
    aesgcm = AESGCM(key)
    try:
        # Try to verify the GMAC by decrypting (recompute GMAC)
        aesgcm.decrypt(nonce, gmac_tag, data_with_index)
        return True
    except Exception as e:
        return False


def validate_file_with_gmac(file_path: str, key: bytes, block_size: int = 1024):
    with open(file_path, "rb") as f:
        block_index: int = 0
        while True:
            # Read the next block (nonce + data + GMAC)
            full_block: bytes = f.read(NONCE_SIZE + block_size + GMAC_SIZE)  # 12-byte nonce (IV), up-to 1024-byte data, 16-byte GMAC tag
            if not full_block:
                break  # End of file
            isValid: bool = validate_block_with_gmac(full_block, block_index, key)

            if isValid:
                print(f"Block {block_index} is authenticated.")
            else:
                print(f"Block {block_index} authentication failed")
                break

            block_index += 1


# Example usage
example_file_path = "../PoR.pdf"
example_output_file = "../processed_with_gmac.txt"

example_blocks_with_mac, example_key = process_file_with_gmac(example_file_path, BLOCK_SIZE)
write_blocks_to_file(example_blocks_with_mac, example_output_file)

print(f"Processed file saved to {example_output_file}")
print(f"AES Key (hex): {example_key.hex()}")

# Example usage
validate_file_with_gmac(example_output_file, example_key)
