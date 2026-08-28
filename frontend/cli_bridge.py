"""
StegoCrypt v2.0.0 CLI Bridge for Tauri / Web IPC
Outputs structured JSON responses.
"""

import sys
import os
import json
import struct
from PIL import Image
import crypto_v2
import stego_v2
from upscaler import ImageUpscaler
import quality_metrics


def respond_json(success: bool, data: dict = None, error: str = ""):
    print(json.dumps({"success": success, "data": data or {}, "error": error}))
    sys.exit(0 if success else 1)


def handle_analyze(cover_path: str, secret_path: str = ""):
    try:
        img = Image.open(cover_path).convert("RGB")
        w, h = img.size
        cap_1bit = (w * h * 3) // 8
        cap_2bit = (w * h * 6) // 8

        secret_size = os.path.getsize(secret_path) if secret_path and os.path.exists(secret_path) else 0

        respond_json(True, {
            "width": w,
            "height": h,
            "capacity_1bit": cap_1bit,
            "capacity_2bit": cap_2bit,
            "secret_size": secret_size
        })
    except Exception as e:
        respond_json(False, error=str(e))


def handle_embed(cover_path, secret_path, output_path, password, use_upscale, bit_depth):
    try:
        bit_depth = int(bit_depth)
        with open(secret_path, "rb") as f:
            secret_bytes = f.read()

        filename = os.path.basename(secret_path).encode("utf-8")
        payload = struct.pack(">I", len(filename)) + filename + secret_bytes
        encrypted_payload = crypto_v2.encrypt_payload(payload, password)

        img = Image.open(cover_path).convert("RGB")
        if use_upscale in ("--upscale", "true", True):
            upscaler = ImageUpscaler()
            img = upscaler.upscale(img, scale=2)

        temp_cover = "temp_work_cover.png"
        img.save(temp_cover)

        stego_v2.encode_image(temp_cover, encrypted_payload, output_path, bit_depth=bit_depth)

        # Kalite Analizi Hesaplama
        stego_img = Image.open(output_path).convert("RGB")
        psnr_val = quality_metrics.calculate_psnr(img, stego_img)
        ssim_val = quality_metrics.calculate_ssim(img, stego_img)

        if os.path.exists(temp_cover):
            os.remove(temp_cover)

        respond_json(True, {
            "output_path": output_path,
            "payload_size": len(encrypted_payload),
            "original_size": len(payload),
            "psnr": round(psnr_val, 2) if psnr_val != float("inf") else 99.9,
            "ssim": round(ssim_val, 4)
        })
    except Exception as e:
        respond_json(False, error=str(e))


def handle_extract(stego_path, output_dir, password):
    try:
        extracted_encrypted = stego_v2.decode_image(stego_path)
        decrypted_payload = crypto_v2.decrypt_payload(extracted_encrypted, password)

        if decrypted_payload == b"ERROR":
            respond_json(False, error="Geçersiz şifre veya bozuk görsel verisi.")

        fn_len = struct.unpack(">I", decrypted_payload[:4])[0]
        filename = decrypted_payload[4:4 + fn_len].decode("utf-8")
        file_data = decrypted_payload[4 + fn_len:]

        save_path = os.path.join(output_dir, filename)
        with open(save_path, "wb") as f:
            f.write(file_data)

        respond_json(True, {
            "filename": filename,
            "size": len(file_data),
            "saved_to": save_path
        })
    except Exception as e:
        respond_json(False, error=str(e))


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "analyze":
        handle_analyze(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    elif action == "embed":
        handle_embed(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
    elif action == "extract":
        handle_extract(sys.argv[2], sys.argv[3], sys.argv[4])