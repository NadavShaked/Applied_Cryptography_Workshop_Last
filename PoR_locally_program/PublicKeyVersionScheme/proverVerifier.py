# Standard library imports
import secrets
from hashlib import sha256

# Third-party library imports
import py_ecc.bls.hash_to_curve as bls_hash
import py_ecc.optimized_bls12_381 as bls_opt

# Local imports
from Common.helpers import secure_random_sample, write_file_by_blocks_with_authenticators
from helpers import get_blocks_authenticators_by_file_path, DST, HASH_INDEX_BYTES, p, MAC_SIZE, BLOCK_SIZE, generate_x, \
    generate_g, generate_v, generate_u, MAC_SIZE_3D


file_name: str = "PoR.pdf"
file_path: str = "../Files/" + file_name

x: int = generate_x()    # private key

g = generate_g()
v = generate_v(g, x)  # v = g^x in G2

u = generate_u()  # u in G1

# To store blocks with appended authenticator
blocks_with_authenticators: list[tuple[bytes, bytes]] = get_blocks_authenticators_by_file_path(file_path,
                                                                                               BLOCK_SIZE,
                                                                                               p,
                                                                                               x,
                                                                                               u,
                                                                                               MAC_SIZE)

output_file: str = "./EncodedFiles/" + file_name + ".encoded.txt"

write_file_by_blocks_with_authenticators(output_file, blocks_with_authenticators)

n: int = len(blocks_with_authenticators)
l: int = secrets.randbelow(n)

# Select random indices
indices: list[int] = secure_random_sample(n, l)
coefficients: list[int] = [secrets.randbelow(p) for _ in range(l)]

σ = None
μ: int = 0

# Calculate the σ and μ
with open(output_file, "rb") as f:
    block_index: int = 0

    while True:
        # Read the next block (data + authenticator)
        full_block: bytes = f.read(BLOCK_SIZE + MAC_SIZE_3D)  # up-to 1024-byte data, 4-byte * 3 for 3d point authenticator tag
        if not full_block:
            break  # End of file

        m_i: int = int.from_bytes(full_block[:-MAC_SIZE_3D], byteorder='big') % p

        _3d_mac: bytes = full_block[-MAC_SIZE_3D:]
        mac_x_coordinate: bytes = _3d_mac[0:MAC_SIZE]  # Bytes 0 - (MAC_SIZE - 1)
        mac_y_coordinate: bytes = _3d_mac[MAC_SIZE:2*MAC_SIZE]  # Bytes (MAC_SIZE) - (2 * MAC_SIZE - 1)
        mac_z_coordinate: bytes = _3d_mac[2*MAC_SIZE:3*MAC_SIZE]  # Bytes (2 * MAC_SIZE) - (3 * MAC_SIZE - 1)

        mac_x_coordinate_as_int = int.from_bytes(mac_x_coordinate, byteorder='big')
        mac_y_coordinate_as_int = int.from_bytes(mac_y_coordinate, byteorder='big')
        mac_z_coordinate_as_int = int.from_bytes(mac_z_coordinate, byteorder='big')

        σ_i = (bls_opt.FQ(mac_x_coordinate_as_int),
               bls_opt.FQ(mac_y_coordinate_as_int),
               bls_opt.FQ(mac_z_coordinate_as_int))

        if block_index in indices:
            v_i: int = coefficients[indices.index(block_index)]
            σ_i_power_v_i = bls_opt.multiply(σ_i, v_i)   # (σ_i)^(v_i)

            if σ is None:
                σ = σ_i_power_v_i
            else:
                σ = bls_opt.add(σ, σ_i_power_v_i)

            v_i_multiply_m_i = (v_i * m_i) % p
            μ = (μ + v_i_multiply_m_i) % p

        block_index += 1


# Verify pairing
left_pairing = bls_opt.pairing(g, σ)   # e(σ, g)

Π_H_i_multiply_v_i = None
for i, coefficient in zip(indices, coefficients):
    v_i: int = coefficient

    H_i = bls_hash.hash_to_G1(i.to_bytes(HASH_INDEX_BYTES, byteorder='big'), DST, sha256)  # H(i)

    H_i_multiply_v_i = bls_opt.multiply(H_i, v_i)  # H(i)^(v_i)

    if Π_H_i_multiply_v_i is None:
        Π_H_i_multiply_v_i = H_i_multiply_v_i
    else:
        Π_H_i_multiply_v_i = bls_opt.add(Π_H_i_multiply_v_i, H_i_multiply_v_i)

u_μ = bls_opt.multiply(u, μ)  # u^μ

multiplication_sum = bls_opt.add(Π_H_i_multiply_v_i, u_μ)

right_pairing = bls_opt.pairing(v, multiplication_sum)   # e(Π(H(i)^(v_i)) * u^μ, v)

print(left_pairing.coeffs[0] == right_pairing.coeffs[0] and left_pairing.coeffs[1] == right_pairing.coeffs[1] and left_pairing.coeffs[2] == right_pairing.coeffs[2])
