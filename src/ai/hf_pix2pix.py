"""Hugging Face Inference API — InstructPix2Pix.

Бесплатно: нужен HF_TOKEN (получить на huggingface.co/settings/tokens).
Лимит: ~30k запросов/месяц.
"""

import os
import io
import logging
import httpx

logger = logging.getLogger(__name__)

HF_TOKEN = os.environ.get("HF_TOKEN", "")
HF_API_URL = "https://api-inference.huggingface.co/models/timbrooks/instruct-pix2pix"


async def edit_image_hf(image_bytes: bytes, prompt: str) -> bytes:
    """Отправить изображение в InstructPix2Pix и получить отредактированное."""
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN не задан! Получи на huggingface.co/settings/tokens")

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    # Send image + prompt to Hugging Face
    async with httpx.AsyncClient(timeout=60) as client:
        # InstructPix2Pix expects image + text prompt
        response = await client.post(
            HF_API_URL,
            headers=headers,
            data={"inputs": prompt},
            files={"data": ("image.jpg", image_bytes, "image/jpeg")},
        )

        if response.status_code != 200:
            logger.error(f"HF API error {response.status_code}: {response.text[:200]}")
            raise Exception(f"HF API вернул {response.status_code}")

        # Response is the edited image bytes
        return response.content
