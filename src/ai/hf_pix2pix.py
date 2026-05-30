"""Hugging Face Inference API — InstructPix2Pix / image-to-image.

Бесплатно: нужен HF_TOKEN (получить на huggingface.co/settings/tokens).

Правильный формат API:
POST /model
{
  "inputs": "<base64_image>",
  "parameters": { "prompt": "edit instruction" }
}
"""

import os
import base64
import io
import logging
import httpx
import json

logger = logging.getLogger(__name__)

HF_TOKEN = os.environ.get("HF_TOKEN", "")

# Пробуем модели по порядку:
# 1. instruct-pix2pix (лучший для редактирования по инструкции)
# 2. FLUX.1-Kontext-dev (мощная модель редактирования, если доступна)
MODELS = [
    "timbrooks/instruct-pix2pix",
    "black-forest-labs/FLUX.1-Kontext-dev",
    "stabilityai/stable-diffusion-xl-refiner-1.0",
]


async def edit_image_hf(image_bytes: bytes, prompt: str) -> bytes:
    """Отправить изображение + инструкцию на HF API и получить результат."""
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN не задан!")

    # Конвертируем изображение в base64
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": img_b64,
        "parameters": {
            "prompt": prompt,
            "guidance_scale": 7.5,
            "image_guidance_scale": 1.5,
        },
    }

    # Пробуем каждую модель по порядку
    last_error = None
    for model in MODELS:
        url = f"https://api-inference.huggingface.co/models/{model}"
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    url, headers=headers, content=json.dumps(payload)
                )

                if response.status_code == 200:
                    return response.content

                error_text = response.text[:200]
                logger.warning(f"HF model {model} error {response.status_code}: {error_text}")
                last_error = f"{model}: {response.status_code}"

        except Exception as e:
            logger.warning(f"HF model {model} failed: {e}")
            last_error = str(e)
            continue

    raise Exception(f"Все HF модели не сработали: {last_error}")
