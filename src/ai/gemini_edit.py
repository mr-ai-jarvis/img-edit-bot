"""Редактирование изображений — Pollinations Kontext (image-to-image).

Принимает оригинальное фото + текстовую инструкцию,
реально редактирует изображение по описанию.
Бесплатно, без ключа.
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)


async def edit_image(
    image_url: str,
    prompt: str,
) -> bytes:
    """Pollinations Kontext — редактирование изображения.

    Передаём URL оригинального фото + промпт, модель меняет фото по описанию.
    """
    import urllib.parse

    encoded_prompt = urllib.parse.quote(prompt)
    encoded_image = urllib.parse.quote(image_url)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?model=kontext"
        f"&image={encoded_image}"
        f"&width=1024&height=1024"
        f"&nologo=true"
    )

    logger.info(f"Kontext: {prompt[:80]}...")
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content
