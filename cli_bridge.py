import os
import sys
import json
import argparse
from PIL import Image

import crypto_v2
import stego_v2
import quality_metrics
import upscaler


def analyze(args):
    try:
        with Image.open(args.cover) as img:
            w, h = img.size
            total_slots = (w * h * 3) - 40
            cap_1bit = max(0, total_slots // 8)
            cap_2bit = max(0, (total_slots * 2) // 8)

        secret_sz = 0
        if args.secret and os.path.exists(args.secret):
            raw_sz = os.path.getsize(args.secret)
            filename_len = len(os.path.basename(args.secret).encode("utf-8"))
            secret_sz = raw_sz + filename_len + 46

        res = {
            "success": True,
            "data": {
                "capacity_1bit": cap_1bit,
                "capacity_2bit": cap_2bit,
                "secret_size": secret_sz,
            },
        }
        print(json.dumps(res))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


def embed(args):
    try:
        # 1. Taşıyıcı Görseli Aç ve Gerekiyorsa 2x Büyüt
        with Image.open(args.cover) as img:
            cover_img = img.convert("RGB")

        if args.upscale:
            scaler = upscaler.ImageUpscaler()
            cover_img = scaler.upscale(cover_img, scale=2)
            # Büyütülmüş geçici görseli kaydet
            temp_cover_path = os.path.splitext(args.output)[0] + "_upscaled_temp.png"
            cover_img.save(temp_cover_path, "PNG")
            active_cover_path = temp_cover_path
        else:
            active_cover_path = args.cover

        # 2. Gizlenecek Dosyayı Paketle
        with open(args.secret, "rb") as f:
            secret_bytes = f.read()

        filename = os.path.basename(args.secret).encode("utf-8")
        filename_len = len(filename).to_bytes(2, byteorder="big")
        raw_package = filename_len + filename + secret_bytes

        # 3. Şifrele & Sıkıştır
        encrypted_payload = crypto_v2.encrypt_payload(raw_package, args.password)

        # 4. LSB Katmanına Göm
        stego_v2.encode_image(
            image_path=active_cover_path,
            payload=encrypted_payload,
            output_path=args.output,
            bit_depth=args.bit_depth,
        )

        # 5. Kalite Analizi
        with Image.open(active_cover_path) as orig_img, Image.open(args.output) as stego_img:
            psnr_calc = quality_metrics.calculate_psnr(orig_img, stego_img)
            ssim_calc = quality_metrics.calculate_ssim(orig_img, stego_img)
            psnr_val = 99.99 if psnr_calc == float("inf") else psnr_calc
            ssim_val = ssim_calc

        # Geçici büyütülmüş dosyayı temizle
        if args.upscale and os.path.exists(temp_cover_path):
            try:
                os.remove(temp_cover_path)
            except Exception:
                pass

        res = {
            "success": True,
            "data": {
                "output_path": args.output,
                "payload_size": len(encrypted_payload),
                "psnr": round(float(psnr_val), 2),
                "ssim": round(float(ssim_val), 4),
            },
        }
        print(json.dumps(res))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


def extract(args):
    try:
        # LSB Çıkart
        extracted_payload = stego_v2.decode_image(args.stego)

        # Deşifre Et
        decrypted_package = crypto_v2.decrypt_payload(extracted_payload, args.password)
        if decrypted_package == b"ERROR":
            print(json.dumps({"success": False, "error": "Hatalı parola veya bozulmuş veri."}))
            return

        # Paketi Ayrıştır
        name_len = int.from_bytes(decrypted_package[:2], byteorder="big")
        filename = decrypted_package[2 : 2 + name_len].decode("utf-8")
        file_data = decrypted_package[2 + name_len :]

        os.makedirs(args.outdir, exist_ok=True)
        out_path = os.path.join(args.outdir, filename)
        with open(out_path, "wb") as f:
            f.write(file_data)

        res = {
            "success": True,
            "data": {
                "filename": filename,
                "output_path": out_path,
                "size": len(file_data),
            },
        }
        print(json.dumps(res))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


def main():
    parser = argparse.ArgumentParser(description="StegoCrypt CLI Bridge")
    subparsers = parser.add_subparsers(dest="command")

    # Analyze
    p_analyze = subparsers.add_parser("analyze")
    p_analyze.add_argument("--cover", required=True)
    p_analyze.add_argument("--secret", default="")

    # Embed
    p_embed = subparsers.add_parser("embed")
    p_embed.add_argument("--cover", required=True)
    p_embed.add_argument("--secret", required=True)
    p_embed.add_argument("--output", required=True)
    p_embed.add_argument("--password", required=True)
    p_embed.add_argument("--bit-depth", type=int, default=1)
    p_embed.add_argument("--upscale", action="store_true")

    # Extract
    p_extract = subparsers.add_parser("extract")
    p_extract.add_argument("--stego", required=True)
    p_extract.add_argument("--outdir", required=True)
    p_extract.add_argument("--password", required=True)

    args = parser.parse_args()

    if args.command == "analyze":
        analyze(args)
    elif args.command == "embed":
        embed(args)
    elif args.command == "extract":
        extract(args)
    else:
        print(json.dumps({"success": False, "error": "Geçersiz komut"}))


if __name__ == "__main__":
    main()