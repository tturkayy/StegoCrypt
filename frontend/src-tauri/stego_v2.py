"""
StegoCrypt v2.0.0 Configurable LSB Engine
----------------------------------------
Supports dynamic bit depth:
- 1-Bit Mode: 1 bit per RGB channel (3 bits/pixel) -> Max stealth
- 2-Bit Mode: 2 bits per RGB channel (6 bits/pixel) -> Double capacity
"""

from PIL import Image
import numpy as np


def encode_image(image_path: str, payload: bytes, output_path: str, bit_depth: int = 1) -> None:
    """
    Embeds binary payload into the LSBs of the cover image.
    Header Format (Fixed at 1-bit mode for compatibility):
    [4 Bytes Payload Length] + [1 Byte Bit Depth Mode (1 or 2)]
    """
    if bit_depth not in (1, 2):
        raise ValueError("Bit derinliği 1 veya 2 olmalıdır.")

    img = Image.open(image_path).convert("RGB")
    arr = np.array(img, dtype=np.uint8)
    flat = arr.reshape(-1)

    # 1. Başlık: 4 bayt uzunluk + 1 bayt mod (Toplam 5 Bayt = 40 Bit, her zaman 1-bit LSB ile yazılır)
    header = len(payload).to_bytes(4, byteorder="big") + bit_depth.to_bytes(1, byteorder="big")
    header_bits = np.unpackbits(np.frombuffer(header, dtype=np.uint8))

    flat[:40] = (flat[:40] & 0xFE) | header_bits

    # 2. Gövde Verisi
    payload_raw = np.frombuffer(payload, dtype=np.uint8)

    if bit_depth == 1:
        payload_bits = np.unpackbits(payload_raw)
        total_slots = 40 + len(payload_bits)
        if total_slots > flat.size:
            raise ValueError("Hata: Veri 1-bit modda bu görsele sığmıyor.")
        flat[40:total_slots] = (flat[40:total_slots] & 0xFE) | payload_bits

    elif bit_depth == 2:
        # 1 Bayt = 4 adet 2-bitlik parça
        b0 = (payload_raw >> 6) & 0x03
        b1 = (payload_raw >> 4) & 0x03
        b2 = (payload_raw >> 2) & 0x03
        b3 = payload_raw & 0x03
        payload_2bit = np.column_stack((b0, b1, b2, b3)).reshape(-1)

        total_slots = 40 + len(payload_2bit)
        if total_slots > flat.size:
            raise ValueError("Hata: Veri 2-bit modda bu görsele sığmıyor.")
        flat[40:total_slots] = (flat[40:total_slots] & 0xFC) | payload_2bit

    result_img = Image.fromarray(arr)
    result_img.save(output_path, "PNG", compress_level=1)


def decode_image(image_path: str) -> bytes:
    """
    Extracts embedded payload by reading the dynamic header first.
    """
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img, dtype=np.uint8)
    flat = arr.reshape(-1)

    # 1. Başlığı Oku (İlk 40 bit)
    header_bits = flat[:40] & 1
    header_bytes = np.packbits(header_bits).tobytes()

    data_len = int.from_bytes(header_bytes[:4], byteorder="big")
    bit_depth = int(header_bytes[4])

    if bit_depth not in (1, 2):
        raise ValueError("Bozulmuş başlık veya geçersiz bit modu.")

    # 2. Gövde Verisini Oku
    if bit_depth == 1:
        total_bits = 40 + (data_len * 8)
        if total_bits > flat.size:
            raise ValueError("Görsel hasarlı veya eksik.")
        payload_bits = flat[40:total_bits] & 1
        return np.packbits(payload_bits).tobytes()

    elif bit_depth == 2:
        total_slots = 40 + (data_len * 4)
        if total_slots > flat.size:
            raise ValueError("Görsel hasarlı veya eksik.")
        payload_2bit = flat[40:total_slots] & 0x03
        grouped = payload_2bit.reshape(-1, 4)
        reconstructed_bytes = (
            (grouped[:, 0] << 6)
            | (grouped[:, 1] << 4)
            | (grouped[:, 2] << 2)
            | grouped[:, 3]
        ).astype(np.uint8)
        return reconstructed_bytes.tobytes()