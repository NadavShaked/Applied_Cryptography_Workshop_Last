# Standard library imports
import math
import secrets


def bytes_needed(number: int) -> int:
    """
    Calculate the smallest number of bytes needed to represent the integer
    where the byte size is a power of two.

    :param number: The integer to analyze.
    :return: The smallest number of bytes (power of 2) needed.
    """
    if number < 0:
        raise ValueError("Number must be non-negative.")
    if number == 0:
        return 1  # Special case: 0 fits in 1 byte

    # Determine the bit length of the number
    bit_length: int = number.bit_length()

    # Find the smallest power of 2 greater than or equal to the bit length
    # Divide by 8 to get bytes, then round up to the next power of 2
    byte_count: int = math.ceil(bit_length / 8)
    power_of_two_bytes: int = 2**math.ceil(math.log2(byte_count))

    return power_of_two_bytes


def secure_random_sample(maxIndex: int, number_of_indices: int) -> list[int]:
    """
    Generate a secure random sample of indices from a range.

    :param maxIndex: The upper limit (exclusive) of the range of indices.
    :param number_of_indices: The number of random indices to select.
    :return: A list of randomly selected indices.
    :raises ValueError: If the sample size is larger than the range.
    """
    # Check if the number of indices is greater than the available range
    if number_of_indices > maxIndex:
        raise ValueError("Sample size l cannot be larger than the range n.")

    # Create a list of indices from 0 to maxIndex - 1
    indices: list[int] = list(range(maxIndex))

    # Shuffle the list using cryptographically secure randomness
    for i in range(len(indices) - 1, 0, -1):
        # Get a secure random index to swap with
        j: int = secrets.randbelow(i + 1)
        # Swap the elements at positions i and j
        indices[i], indices[j] = indices[j], indices[i]

    # Return the first `number_of_indices` - `l` items as the sample
    return indices[:number_of_indices]


def write_file_by_blocks_with_authenticators(output_file: str, blocks_with_authenticators: list[tuple[bytes, bytes]]) -> None:
    """
    Write processed blocks along with their authenticators to a new file.

    :param output_file: The path to the output file where the blocks will be written.
    :param blocks_with_authenticators: A list of tuples, where each tuple contains
                                        (data_block, authenticator).
    :return: None
    """
    # Open the output file in write-binary mode
    with open(output_file, "wb") as out_f:
        for block_with_authenticator in blocks_with_authenticators:
            # Write data
            out_f.write(block_with_authenticator[0])
            # Write authenticator
            out_f.write(block_with_authenticator[1])


def write_file_by_blocks(output_file: str, blocks: list[bytes]) -> None:
    """
    Write processed blocks of data to a new file.

    :param output_file: The path to the output file where the blocks will be written.
    :param blocks: A list of data blocks (bytes) to be written to the file.
    :return: None
    """
    # Open the output file in write-binary mode
    with open(output_file, "wb") as out_f:
        for block in blocks:
            # Write the current data block to the file
            out_f.write(block)
