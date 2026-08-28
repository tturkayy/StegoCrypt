"""
StegoCrypt v2.0.0 Cryptography & Compression Engine
--------------------------------------------------
- Compression: Smart Zstandard (Negative compression prevention)
- Key Derivation: PBKDF2-HMAC-SHA256 with dynamic Salt
- Encryption: AES-256-GCM (Authenticated Encryption)
"""

import os
import zstandard as zstd
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes


def compress_data(data: bytes, level: int = 3) -> bytes:
    """
    Compresses binary data using Zstandard.
    Prepends 1-byte flag:
    - 0x00: Raw data (used when compression enlarges payload)
    - 0x01: Compressed data
    """
    cctx = zstd.ZstdCompressor(level=level)
    compressed = cctx.compress(data)

    if len(compressed) >= len(data):
        return b"\x00" + data
    return b"\x01" + compressed


def decompress_data(data: bytes) -> bytes:
    """Decompresses Zstandard binary data based on the 1-byte prefix flag."""
    if not data:
        return b""

    is_compressed = data[0]
    payload = data[1:]

    if is_compressed == 1:
        dctx = zstd.ZstdDecompressor()
        return dctx.decompress(payload)
    return payload


def derive_key(password: str, salt: bytes) -> bytes:
    """Derives a 32-byte key using PBKDF2-HMAC-SHA256."""
    return PBKDF2(password.encode("utf-8"), salt, dkLen=32, count=100_000)


def encrypt_payload(data: bytes, password: str) -> bytes:
    """
    Compresses and encrypts data using AES-256-GCM.
    Binary Format: [16B Salt] + [12B Nonce] + [16B Auth Tag] + [Ciphertext]
    """
    # 1. Akıllı Sıkıştırma
    compressed = compress_data(data)

    # 2. Anahtar ve Şifreleme Parametreleri
    salt = get_random_bytes(16)
    nonce = get_random_bytes(12)
    key = derive_key(password, salt)

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(compressed)

    # 3. Paketleme
    return salt + nonce + tag + ciphertext


def decrypt_payload(encrypted_data: bytes, password: str) -> bytes:
    """
    Decrypts AES-256-GCM payload, verifies authenticity, and decompresses.
    Returns b"ERROR" if verification or decompression fails.
    """
    try:
        salt = encrypted_data[:16]
        nonce = encrypted_data[16:28]
        tag = encrypted_data[28:44]
        ciphertext = encrypted_data[44:]

        key = derive_key(password, salt)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

        # Şifre çözme ve veri bütünlüğü doğrulama
        compressed = cipher.decrypt_and_verify(ciphertext, tag)

        # Açma / Dekompresyon
        return decompress_data(compressed)
    except Exception:
        return b"ERROR"