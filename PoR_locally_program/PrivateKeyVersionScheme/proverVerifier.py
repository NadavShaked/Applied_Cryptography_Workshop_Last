# Standard library imports
import secrets

# Third-party library imports
import galois
from galois import FieldArray

# Local imports
from Common.helpers import (
    bytes_needed,
    secure_random_sample,
    write_file_by_blocks_with_authenticators
)
from Common.Constants.primes import PRIME_NUMBER_16_BYTES
from PRFs import hmac_prf
from helpers import get_blocks_authenticators_by_file_path

p: int = PRIME_NUMBER_16_BYTES
MAC_SIZE: int = bytes_needed(p)

# Create a finite field GF(p)
GF = galois.GF(p)

file_name: str = "PoR.pdf"
file_path: str = "../Files/" + file_name
BLOCK_SIZE: int = 1024

k: int = secrets.randbelow(100)
α: FieldArray = GF(secrets.randbelow(p))

# To store blocks with appended authenticator
blocks_with_authenticators: list[tuple[bytes, bytes]] = get_blocks_authenticators_by_file_path(file_path,
                                                                                               α,
                                                                                               BLOCK_SIZE,
                                                                                               k,
                                                                                               p,
                                                                                               MAC_SIZE)

output_file: str = "./EncodedFiles/" + file_name + ".encoded.txt"

write_file_by_blocks_with_authenticators(output_file, blocks_with_authenticators)

n: int = len(blocks_with_authenticators)
l: int = secrets.randbelow(n)

# Select random indices
indices: list[int] = secure_random_sample(n, l)
coefficients: list[int] = [secrets.randbelow(p) for _ in range(l)]

σ: FieldArray = GF(0)
μ: FieldArray = GF(0)

# Calculate the σ and μ
with open(output_file, "rb") as f:
    block_index: int = 0
    while True:
        # Read the next block (data + authenticator)
        full_block: bytes = f.read(BLOCK_SIZE + MAC_SIZE)  # up-to 1024-byte data, 4-byte authenticator tag
        if not full_block:
            break  # End of file

        m_i: FieldArray = GF(int.from_bytes(full_block[:-MAC_SIZE], byteorder='big') % p)
        σ_i: FieldArray = GF(int.from_bytes(full_block[-MAC_SIZE:], byteorder='big') % p)

        if block_index in indices:
            v_i: FieldArray = GF(coefficients[indices.index(block_index)] % p)
            σ += v_i * σ_i
            μ += v_i * m_i

        block_index += 1

# Verify σ
Σ: FieldArray = GF(0)
for i, coefficient in zip(indices, coefficients):
    v_i: FieldArray = GF(coefficient % p)
    f_k_i: FieldArray = GF(hmac_prf(k, i) % p)
    Σ += v_i * f_k_i

calculated_σ_to_verify: FieldArray = α * μ + Σ

print(σ == calculated_σ_to_verify)
