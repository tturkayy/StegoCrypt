"""
StegoCrypt Visual Quality Analysis Module
----------------------------------------
Calculates Peak Signal-to-Noise Ratio (PSNR) and Structural Similarity Index (SSIM)
to evaluate the imperceptibility of embedded payload.
"""

import math
import numpy as np
from PIL import Image


def calculate_psnr(img1: Image.Image, img2: Image.Image) -> float:
    """
    Calculates Peak Signal-to-Noise Ratio (PSNR) in decibels (dB).
    Formula: PSNR = 20 * log10(MAX_I) - 10 * log10(MSE)
    """
    arr1 = np.array(img1.convert("RGB"), dtype=np.float64)
    arr2 = np.array(img2.convert("RGB"), dtype=np.float64)

    mse = np.mean((arr1 - arr2) ** 2)
    if mse == 0:
        return float("inf")  # Görseller tamamen özdeş

    max_pixel = 255.0
    return 20 * math.log10(max_pixel / math.sqrt(mse))


def calculate_ssim(img1: Image.Image, img2: Image.Image) -> float:
    """
    Calculates Structural Similarity Index Measure (SSIM).
    Returns a score between -1.0 and 1.0 (1.0 = identical images).
    """
    arr1 = np.array(img1.convert("RGB"), dtype=np.float64)
    arr2 = np.array(img2.convert("RGB"), dtype=np.float64)

    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2

    mu1 = np.mean(arr1)
    mu2 = np.mean(arr2)
    sigma1_sq = np.var(arr1)
    sigma2_sq = np.var(arr2)
    sigma12 = np.mean((arr1 - mu1) * (arr2 - mu2))

    numerator = (2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)
    denominator = (mu1**2 + mu2**2 + c1) * (sigma1_sq + sigma2_sq + c2)

    return float(numerator / denominator)