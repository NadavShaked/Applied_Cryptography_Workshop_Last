# Standard library imports
import hashlib
import hmac


SHA_256_BYTES_SIZE: int = 32


def hmac_prf(k: int, index: int) -> int:
    """
    Pseudo-Random Function using HMAC.
    :param k: Random key (int)
    :param index: Input value (int)
    :return: Pseudo-random output (int)
    """
    # Convert k to bytes (e.g., 32-byte big-endian format)
    k_in_bytes: bytes = k.to_bytes(SHA_256_BYTES_SIZE, byteorder='big')
    # Convert index to bytes (e.g., 32-byte big-endian format)
    index_in_bytes: bytes = index.to_bytes(SHA_256_BYTES_SIZE, byteorder='big')

    # Compute HMAC-based PRF
    output: bytes = hmac.new(k_in_bytes, index_in_bytes, hashlib.sha256).digest()

    # Convert the hex string to an integer
    return int.from_bytes(output, byteorder='big')  # Convert from bytes to integer
