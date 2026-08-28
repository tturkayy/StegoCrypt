"""
StegoCrypt AI Super-Resolution Engine
------------------------------------
Upscales low-resolution cover images using lightweight ONNX models
to drastically increase steganographic byte capacity.
"""

import numpy as np
from PIL import Image
import onnxruntime as ort


class ImageUpscaler:
    def __init__(self, model_path: str = None):
        self.session = None
        if model_path:
            self.session = ort.InferenceSession(
                model_path,
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
            )

    def simple_fallback_upscale(self, img: Image.Image, scale: int = 2) -> Image.Image:
        """Fallback high-quality Lanczos upscale when model is not provided."""
        new_size = (img.width * scale, img.height * scale)
        return img.resize(new_size, Image.Resampling.LANCZOS)

    def upscale(self, img: Image.Image, scale: int = 2) -> Image.Image:
        """Upscales PIL Image using ONNX model or falls back to Lanczos."""
        if not self.session:
            return self.simple_fallback_upscale(img, scale)

        img_rgb = img.convert("RGB")
        img_np = np.array(img_rgb).astype(np.float32) / 255.0
        img_np = np.transpose(img_np, (2, 0, 1))  # HWC -> CHW
        img_np = np.expand_dims(img_np, axis=0)    # NCHW

        input_name = self.session.get_inputs()[0].name
        output_name = self.session.get_outputs()[0].name

        preds = self.session.run([output_name], {input_name: img_np})[0]
        output = np.squeeze(preds, axis=0)
        output = np.clip(output * 255.0, 0, 255).astype(np.uint8)
        output = np.transpose(output, (1, 2, 0))   # CHW -> HWC

        return Image.fromarray(output)