"""
StegoCrypt Steganography Module
-------------------------------
Handles the embedding and extraction of binary data within images using
Least Significant Bit (LSB) manipulation. Optimized for performance with
large resolution images (4K+).

Author: Turkay Yildirim
License: MIT
"""

from PIL import Image


def data_to_bin(data):
    """Converts various data types (int, str, bytes) into binary string representation."""
    if isinstance(data, str):
        return ''.join([format(ord(i), "08b") for i in data])
    elif isinstance(data, bytes):
        return ''.join([format(i, "08b") for i in data])
    elif isinstance(data, int):
        return format(data, "08b")
    else:
        raise TypeError("Unsupported data type.")


def bin_to_bytes(binary_data):
    """Converts a binary string back into a bytearray."""
    all_bytes = [binary_data[i: i + 8] for i in range(0, len(binary_data), 8)]
    return bytearray([int(byte, 2) for byte in all_bytes])


def encode_image(image_path, secret_data, output_path, progress_callback=None):
    """
    Embeds binary data into the LSBs of the provided image.

    Implements an 'Early Exit' optimization: The loop breaks immediately after
    all data bits are embedded, copying the remaining pixels in bulk to save time.

    Args:
        image_path (str): Path to the cover image.
        secret_data (bytes): The encrypted data to hide.
        output_path (str): Where to save the resulting PNG.
        progress_callback (func): Optional function to update UI progress bar.

    Returns:
        bool: True if successful.
    """
    img = Image.open(image_path)
    img = img.convert("RGB")

    # Data Preparation
    data_len = len(secret_data)
    bin_length = format(data_len, '032b')  # First 32 bits = Data Size
    bin_data = data_to_bin(secret_data)
    full_payload = bin_length + bin_data
    payload_len = len(full_payload)

    width, height = img.size
    total_pixels = width * height

    if payload_len > total_pixels * 3:
        raise ValueError("Error: Image is too small to hold this data.")

    pixels = list(img.getdata())
    encoded_pixels = []

    payload_index = 0

    # --- Encoding Loop with Optimization ---
    for i, (r, g, b) in enumerate(pixels):

        # Optimization: If all data is written, copy the rest and break
        if payload_index >= payload_len:
            encoded_pixels.extend(pixels[i:])
            break

        # Modify LSBs of Red, Green, and Blue channels
        if payload_index < payload_len:
            r = (r & 0xFE) | int(full_payload[payload_index])
            payload_index += 1

        if payload_index < payload_len:
            g = (g & 0xFE) | int(full_payload[payload_index])
            payload_index += 1

        if payload_index < payload_len:
            b = (b & 0xFE) | int(full_payload[payload_index])
            payload_index += 1

        encoded_pixels.append((r, g, b))

        # Update progress every 50k pixels to prevent UI lag
        if progress_callback and i % 50000 == 0:
            current_percent = payload_index / payload_len
            progress_callback(current_percent)

    # Save the new image
    if progress_callback: progress_callback(0.99)

    new_img = Image.new(img.mode, img.size)
    new_img.putdata(encoded_pixels)
    new_img.save(output_path, "PNG")

    if progress_callback: progress_callback(1.0)
    return True


def decode_image(image_path, progress_callback=None):
    """
    Extracts hidden data from the LSBs of an image.

    Uses a two-step reading process:
    1. Reads the first 32 bits (Header) to determine data size.
    2. Reads only the required number of pixels to extract the payload.

    Args:
        image_path (str): Path to the encoded image.
        progress_callback (func): Optional function to update UI progress bar.

    Returns:
        bytes: The extracted raw encrypted data.
    """
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = list(img.getdata())

    # Step 1: Read Header (First 32 bits)
    # We need approx 11 pixels (11 * 3 = 33 bits) to get 32 bits
    header_pixels = pixels[:12]

    header_bin_list = []
    for r, g, b in header_pixels:
        header_bin_list.append(str(r & 1))
        header_bin_list.append(str(g & 1))
        header_bin_list.append(str(b & 1))

    header_bin_str = "".join(header_bin_list)[:32]
    data_len = int(header_bin_str, 2)

    # Step 2: Calculate exact bits needed
    total_bits_needed = 32 + (data_len * 8)
    total_pixels_needed = (total_bits_needed + 2) // 3

    if total_pixels_needed > len(pixels):
        return b""  # Header is corrupted or image is too small

    # Step 3: Optimized Reading (Slicing)
    pixels_to_read = pixels[:total_pixels_needed]

    binary_list = []
    total_count = len(pixels_to_read)

    for i, (r, g, b) in enumerate(pixels_to_read):
        binary_list.append(str(r & 1))
        binary_list.append(str(g & 1))
        binary_list.append(str(b & 1))

        if progress_callback and i % 50000 == 0:
            progress_callback(i / total_count)

    full_binary_str = "".join(binary_list)
    extracted_bin = full_binary_str[32: 32 + (data_len * 8)]

    if progress_callback: progress_callback(1.0)

    return bin_to_bytes(extracted_bin)
