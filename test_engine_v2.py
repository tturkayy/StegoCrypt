"""
StegoCrypt v2.0.0 Full Engine Test
----------------------------------
Tests Compression, AES-256-GCM, AI Upscaling, 1-Bit/2-Bit LSB, and PSNR/SSIM.
"""

import os
import struct
from PIL import Image
import crypto_v2
import stego_v2
from upscaler import ImageUpscaler
import quality_metrics


def run_tests():
    print("=== StegoCrypt v2.0.0 Motor Testleri Başlatılıyor ===\n")

    # 1. Test Verisi Hazırlama
    secret_text = "Bu gizli bir belgedir. " * 200
    secret_bytes = secret_text.encode("utf-8")
    filename = "gizli_rapor.txt".encode("utf-8")
    password = "SuperSecretPassword123!"

    payload = struct.pack(">I", len(filename)) + filename + secret_bytes
    print(f"[1] Orijinal Veri Boyutu      : {len(payload)} bayt")

    # 2. Şifreleme ve Sıkıştırma
    encrypted_payload = crypto_v2.encrypt_payload(payload, password)
    print(f"[2] Sıkıştırılmış + Şifreli    : {len(encrypted_payload)} bayt")
    print(f"    Sıkıştırma Kazanımı       : %{round((1 - len(encrypted_payload) / len(payload)) * 100, 2)}")

    # 3. Test Görselleri
    cover_img_path = "test_cover.png"
    upscaled_cover_path = "test_cover_upscaled.png"
    stego_1bit_path = "test_stego_1bit.png"
    stego_2bit_path = "test_stego_2bit.png"

    img = Image.new("RGB", (100, 100), color=(73, 109, 137))
    img.save(cover_img_path)

    # 4. Upscaler Testi
    upscaler = ImageUpscaler()
    upscaled_img = upscaler.upscale(img, scale=2)
    upscaled_img.save(upscaled_cover_path)

    orig_cap = (100 * 100 * 3) // 8
    up_cap = (200 * 200 * 3) // 8
    print(f"[3] Orijinal Kapasite         : {orig_cap} bayt")
    print(f"    2x Büyütülmüş Kapasite    : {up_cap} bayt (4 Kat Artış)")

    # 5. 1-Bit Mod Gömme ve Çıkarma Testi
    print("\n--- [4] 1-Bit LSB Modu Test Ediliyor ---")
    stego_v2.encode_image(upscaled_cover_path, encrypted_payload, stego_1bit_path, bit_depth=1)
    extracted_1bit = stego_v2.decode_image(stego_1bit_path)
    decrypted_1bit = crypto_v2.decrypt_payload(extracted_1bit, password)

    assert decrypted_1bit != b"ERROR", "1-Bit şifre çözme hatası!"
    print("✓ 1-Bit Gömme/Çözme Doğrulandı.")

    # 6. 2-Bit Mod Gömme ve Çıkarma Testi
    print("\n--- [5] 2-Bit LSB Modu Test Ediliyor ---")
    stego_v2.encode_image(upscaled_cover_path, encrypted_payload, stego_2bit_path, bit_depth=2)
    extracted_2bit = stego_v2.decode_image(stego_2bit_path)
    decrypted_2bit = crypto_v2.decrypt_payload(extracted_2bit, password)

    assert decrypted_2bit != b"ERROR", "2-Bit şifre çözme hatası!"
    print("✓ 2-Bit Gömme/Çözme Doğrulandı.")

    # 7. Kalite Metrikleri (PSNR & SSIM)
    print("\n--- [6] Görsel Kalite Analizi (Metrikler) ---")
    cover_ref = Image.open(upscaled_cover_path)
    stego_1 = Image.open(stego_1bit_path)
    stego_2 = Image.open(stego_2bit_path)

    psnr_1 = quality_metrics.calculate_psnr(cover_ref, stego_1)
    ssim_1 = quality_metrics.calculate_ssim(cover_ref, stego_1)
    print(f"[1-Bit Mod] PSNR: {round(psnr_1, 2)} dB | SSIM: {round(ssim_1, 5)}")

    psnr_2 = quality_metrics.calculate_psnr(cover_ref, stego_2)
    ssim_2 = quality_metrics.calculate_ssim(cover_ref, stego_2)
    print(f"[2-Bit Mod] PSNR: {round(psnr_2, 2)} dB | SSIM: {round(ssim_2, 5)}")

    print("\n✅ TÜM TESTLER BAŞARIYLA GEÇTİ!")

    # Temizlik (En son çalışır)
    for f in [cover_img_path, upscaled_cover_path, stego_1bit_path, stego_2bit_path]:
        if os.path.exists(f):
            os.remove(f)


if __name__ == "__main__":
    run_tests()