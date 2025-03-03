# Standard library imports
import secrets
from hashlib import sha256

# Third-party library imports
import py_ecc.bls.hash_to_curve as bls_hash
from py_ecc.bls.typing import G1Compressed, G2Compressed
from py_ecc.fields import optimized_bls12_381_FQ
import py_ecc.optimized_bls12_381 as bls_opt
import py_ecc.bls.point_compression as bls_comp

MAC_SIZE: int = 128
MAC_SIZE_3D: int = 3 * MAC_SIZE    # 3d point authenticator tag
BLOCK_SIZE: int = 1024

p: int = bls_opt.curve_order    # The curve order is 52435875175126190479447740508185965837690552500527637822603658699938581184513

HASH_INDEX_BYTES = 32
DST = b"BLS_SIG_BLS12381G1_XMD:SHA-256_SSWU_RO_"


def generate_x() -> int:
    """
    Generate a secure random integer x as a private key.

    :return: A randomly generated integer x within the range [0, p).
    """
    x: int = secrets.randbelow(p)  # private key
    return x


def generate_g():
    """
    Generate a point on the elliptic curve G2 by multiplying the generator G2
    by a securely generated random value.

    :return: The resulting elliptic curve point g in the G2 group.
    """
    rand_value: int = secrets.randbelow(p)
    g = bls_opt.multiply(bls_opt.G2, rand_value)
    return g


def generate_v(g, x: int):
    """
    Generate a point v on the elliptic curve G2 by multiplying a point g by
    the private key x.

    :param g: The elliptic curve point to be multiplied (typically generated from G2).
    :param x: The private key (an integer) used for the multiplication.
    :return: The resulting elliptic curve point v in the G2 group.
    """
    v = bls_opt.multiply(g, x)  # v = g^x in G2
    return v


def generate_u():
    """
    Generate a point u on the elliptic curve G1 by multiplying the generator G1
    by a securely generated random value.

    :return: The resulting elliptic curve point u in the G1 group.
    """
    rand_value: int = secrets.randbelow(p)
    u = bls_opt.multiply(bls_opt.G1, rand_value)  # u in G1
    return u


def curve_field_element_to_bytes(
    point: tuple[optimized_bls12_381_FQ, optimized_bls12_381_FQ, optimized_bls12_381_FQ],
    num_bytes: int
) -> bytes:
    """
    Convert a tuple representing a BLS 12_381 Curve point element on an elliptic curve to its byte representation.

    The curve satisfies the equation: y^2 = x^3 + 4.

    :param point: A tuple containing three elements (x, y, z) representing a point on the elliptic curve.
    :param num_bytes: The desired length of the byte representation for each coordinate.
    :return: A concatenated byte representation of (x, y, z) in big-endian order.
    """
    x_as_int: int = int(point[0])
    y_as_int: int = int(point[1])
    z_as_int: int = int(point[2])

    # Convert each integer to a byte array
    return (
        x_as_int.to_bytes(num_bytes, byteorder='big') +
        y_as_int.to_bytes(num_bytes, byteorder='big') +
        z_as_int.to_bytes(num_bytes, byteorder='big')
    )


def get_blocks_authenticators_by_file_path(
        file_path: str,
        block_size: int,
        p: int,
        x: int,
        u: tuple[optimized_bls12_381_FQ, optimized_bls12_381_FQ, optimized_bls12_381_FQ],
        mac_size: int
) -> list[tuple[bytes, bytes]]:
    """
    Process a file into blocks with their corresponding cryptographic authenticators.

    :param file_path: Path to the input file.
    :param block_size: Size of each block in bytes.
    :param p: A prime modulus used in some field arithmetic operations.
    :param x: A scalar value used in multiplication operations.
    :param u: A tuple representing an elliptic curve point (u) used in cryptographic computations.
    :param mac_size: Size of the message authentication code (MAC) in bytes.
    :return: A list of tuples, where each tuple contains a block of bytes and its corresponding authenticator.
    """
    blocks_with_authenticators: list[tuple[bytes, bytes]] = []

    # Open the file for reading
    with open(file_path, "rb") as f:
        block_index: int = 0

        while True:
            # Read the next block
            block: bytes = f.read(block_size)
            if not block:  # End of file
                break

            block_in_z_p: int = int.from_bytes(block, byteorder='big') % p  # m_i

            # Compute u^(m_i)
            u_m_i = bls_opt.multiply(u, block_in_z_p)

            # Compute H(i) where i is the block index
            H_i = bls_hash.hash_to_G1(block_index.to_bytes(HASH_INDEX_BYTES, byteorder='big'), DST, sha256)

            # Compute H(i) * u^(m_i)
            H_i_add_u_m_i = bls_opt.add(H_i, u_m_i)

            # Compute σ_i = [H(i) * u^(m_i)]^x
            σ_i = bls_opt.multiply(H_i_add_u_m_i, x)

            # Convert σ_i to bytes
            σ_i_in_bytes: bytes = curve_field_element_to_bytes(σ_i, mac_size)

            # Append the block and its corresponding authenticator
            blocks_with_authenticators.append((block, σ_i_in_bytes))

            block_index += 1

    return blocks_with_authenticators


def compress_g1_to_hex(g1_point) -> str:
    """
    Compress a G1 point to a hexadecimal string representation.

    :param g1_point: The G1 point (typically an elliptic curve point) to compress.
    :return: A hexadecimal string representing the compressed G1 point.
    """
    g1_comp: G1Compressed = bls_comp.compress_G1(g1_point)
    g1_comp_as_bytes: bytes = g1_comp.to_bytes(48, 'big')
    return g1_comp_as_bytes.hex()


def compress_g2_to_hex(g2_point) -> str:
    """
    Compress a G2 point to a hexadecimal string representation.

    :param g2_point: The G2 point (typically an elliptic curve point) to compress.
    :return: A hexadecimal string representing the compressed G2 point.
    """
    g2_comp: G2Compressed = bls_comp.compress_G2(g2_point)
    g2_comp_as_bytes: bytes = g2_comp[0].to_bytes(48, 'big') + g2_comp[1].to_bytes(48, 'big')
    return g2_comp_as_bytes.hex()
