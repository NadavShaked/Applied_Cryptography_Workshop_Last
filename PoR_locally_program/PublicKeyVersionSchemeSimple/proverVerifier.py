# Standard library imports
import secrets

# Local imports
from Common.Constants.primes import LOW_PRIME
from Common.helpers import secure_random_sample, write_file_by_blocks_with_authenticators
from PublicKeyVersionScheme.helpers import MAC_SIZE, MAC_SIZE_3D
from helpers import get_blocks_authenticators_by_file_path, add, multiply, hash, pairing


p: int = LOW_PRIME

file_name: str = "PoR.pdf"
file_path: str = "../Files/" + file_name
BLOCK_SIZE: int = 1024

x: int = secrets.randbelow(p)    # private key

G1: int = 13
G2: int = 7

rand_value_1: int = secrets.randbelow(p)
g = multiply(G2, rand_value_1)
v = multiply(g, x)  # v = g^x in Z_p

rand_value_2: int = secrets.randbelow(p)
u = multiply(G1, rand_value_2)  # u in Z_p

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
        mac_b_coordinate: bytes = _3d_mac[2*MAC_SIZE:3*MAC_SIZE]  # Bytes (2 * MAC_SIZE) - (3 * MAC_SIZE - 1)

        mac_x_coordinate_as_int = int.from_bytes(mac_x_coordinate, byteorder='big')
        mac_y_coordinate_as_int = int.from_bytes(mac_y_coordinate, byteorder='big')
        mac_b_coordinate_as_int = int.from_bytes(mac_b_coordinate, byteorder='big')

        σ_i = mac_x_coordinate_as_int

        if block_index in indices:
            v_i: int = coefficients[indices.index(block_index)]
            σ_i_power_v_i = multiply(σ_i, v_i)   # (σ_i)^(v_i)

            if σ is None:
                σ = σ_i_power_v_i
            else:
                σ = add(σ, σ_i_power_v_i)

            v_i_multiply_m_i = (v_i * m_i) % p
            μ = (μ + v_i_multiply_m_i) % p

        block_index += 1


# Verify pairing
left_pairing = pairing(g, σ)   # e(σ, g)

Π_H_i_multiply_v_i = None
for i, coefficient in zip(indices, coefficients):
    v_i: int = coefficient

    H_i = hash(i)  # H(i)

    H_i_multiply_v_i = multiply(H_i, v_i)  # H(i)^(v_i)

    if Π_H_i_multiply_v_i is None:
        Π_H_i_multiply_v_i = H_i_multiply_v_i
    else:
        Π_H_i_multiply_v_i = add(Π_H_i_multiply_v_i, H_i_multiply_v_i)

u_μ = multiply(u, μ)  # u^μ

all = add(Π_H_i_multiply_v_i, u_μ)

right_pairing = pairing(v, all)   # e(Π(H(i)^(v_i)) * u^μ, v)

print(left_pairing == right_pairing)
