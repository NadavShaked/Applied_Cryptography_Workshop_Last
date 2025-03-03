import reedsolo


def encode_file_with_rs(filepath: str, output_filepath: str, chunk_size: int = 245):
    """
    Reads a file, applies Reed-Solomon encoding in chunks, and saves the encoded file.

    Args:
        filepath (str): Path to the input file to be encoded.
        output_filepath (str): Path where the encoded file will be saved.
        chunk_size (int): Size of each chunk to be encoded. Default is 245 bytes.

    Returns:
        str: Path to the encoded file.
    """
    # Initialize Reed-Solomon codec with 10 error correction bytes and 255 total bytes per block
    rs = reedsolo.RSCodec(10, nsize=255)

    print(f"Starting file encoding for {filepath}...")

    with open(filepath, "rb") as file, open(output_filepath, "wb") as encoded_file:
        while chunk := file.read(chunk_size):
            # Apply Reed-Solomon encoding to the chunk
            encoded_chunk = rs.encode(chunk)
            encoded_file.write(encoded_chunk)

    print(f"File encoding completed. Encoded file saved at {output_filepath}")
    return output_filepath


def corrupt_file(input_filepath: str, output_filepath: str, block_size: int = 1024):
    """
    Corrupts the file by flipping the first byte of every 1024-byte block.

    Args:
        input_filepath (str): Path to the file to be corrupted.
        output_filepath (str): Path where the corrupted file will be saved.
        block_size (int): Size of each block to corrupt. Default is 1024 bytes.

    Returns:
        str: Path to the corrupted file.
    """
    print(f"Starting file corruption for {input_filepath}...")

    with open(input_filepath, "rb") as file:
        data = bytearray(file.read())

    # Flip the first byte of each block of data
    for i in range(0, len(data), block_size):
        data[i] ^= 0x80  # Flip the first byte (XOR with 0x80)

    with open(output_filepath, "wb") as corrupted_file:
        corrupted_file.write(data)

    print(f"File corruption completed. Corrupted file saved at {output_filepath}")
    return output_filepath


def decode_file_with_rs(encoded_filepath: str, output_filepath: str, chunk_size: int = 255):
    """
    Reads a Reed-Solomon encoded file, decodes it in chunks, and saves the original file.

    Args:
        encoded_filepath (str): Path to the encoded file.
        output_filepath (str): Path where the decoded file will be saved.
        chunk_size (int): Size of each chunk to decode. Default is 255 bytes.

    Returns:
        str: Path to the decoded file.
    """
    # Initialize Reed-Solomon codec with 10 error correction bytes and 255 total bytes per block
    rs = reedsolo.RSCodec(10, nsize=255)

    print(f"Starting file decoding for {encoded_filepath}...")

    with open(encoded_filepath, "rb") as encoded_file, open(output_filepath, "wb") as decoded_file:
        while chunk := encoded_file.read(chunk_size):
            # Decode the Reed-Solomon encoded chunk
            decoded_chunk = rs.decode(chunk)
            decoded_file.write(decoded_chunk[0])  # Write the decoded content (first element of the tuple)

    print(f"File decoding completed. Decoded file saved at {output_filepath}")
    return output_filepath
