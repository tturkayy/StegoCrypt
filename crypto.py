"""
StegoCrypt Cryptography Module
------------------------------
Handles AES-256 encryption and decryption processes using PyCryptodome.
Implements SHA-256 for key derivation and CBC mode for secure block cipher operations.

Author: Turkay Yildirim
License: MIT
"""

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes


def get_key(password):
    """
    Derives a 32-byte (256-bit) cryptographic key from the user password.

    Uses SHA-256 hashing to transform an arbitrary length string into
    a fixed-length secure key suitable for AES-256.

    Args:
        password (str): The user-provided password.

    Returns:
        bytes: A 32-byte digest of the password.
    """
    hasher = SHA256.new(data=password.encode('utf-8'))
    return hasher.digest()


def encrypt_message(data, password):
    """
    Encrypts binary data using AES-256 in CBC (Cipher Block Chaining) mode.

    Generates a random Initialization Vector (IV) for each encryption operation
    to ensure that identical plaintexts produce different ciphertexts.

    Args:
        data (bytes): The raw file data (including header) to be encrypted.
        password (str): The password used to derive the encryption key.

    Returns:
        bytes: A byte sequence containing the IV (first 16 bytes) followed by the ciphertext.
    """
    if isinstance(data, str):
        data = data.encode('utf-8')

    key = get_key(password)
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # Pad the data to be a multiple of the block size (16 bytes)
    encrypted_data = cipher.encrypt(pad(data, AES.block_size))

    return iv + encrypted_data


def decrypt_message(encrypted_data, password):
    """
    Decrypts AES-256 encrypted data.

    Extracts the IV from the beginning of the data stream and uses it
    to decrypt the remaining ciphertext.

    Args:
        encrypted_data (bytes): The byte sequence containing IV + Ciphertext.
        password (str): The password used for decryption.

    Returns:
        bytes: The raw decrypted data (original file bytes).
        bytes: Returns b"ERROR" if decryption fails (wrong password or padding error).
    """
    try:
        key = get_key(password)
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]

        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted_data
    except (ValueError, KeyError):
        return b"ERROR"
