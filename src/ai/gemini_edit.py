"""Редактирование изображений — Google Gemini 2.0 Flash (бесплатно).

Gemini 2.0 Flash нативно поддерживает редактирование изображений:
- Принимает изображение + текстовую инструкцию
- Редактирует именно переданное изображение (не генерит новое)
- Бесплатно: 1500 запросов/день

Модель: gemini-2.0-flash-preview-image-generation
"""

import os
import io
import logging
import httpx

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{}"


async def _edit_with_gemini(image_bytes: bytes, prompt: str) -> bytes:
    """Редактирование через Gemini 2.0 Flash."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-preview-image-generation")

        response = model.generate_content([
            f"Отредактируй это изображение: {prompt}. "
            f"Верни ТОЛЬКО изображение, без текста.",
            {"mime_type": "image/jpeg", "data": image_bytes},
        ])

        # Gemini может вернуть как изображение, так и текст
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                return part.inline_data.data
            elif hasattr(part, "text") and part.text:
                logger.info(f"Gemini text response: {part.text[:100]}")

        raise ValueError("Gemini не вернул изображение")
    except Exception as e:
        logger.error(f"Gemini edit failed: {e}", exc_info=True)
        raise


async def _generate_pollinations(prompt: str) -> bytes:
    """Резерв: генерация через Pollinations.ai (без ключа)."""
    import urllib.parse
    encoded = urllib.parse.quote(prompt)
    url = f"{POLLINATIONS_URL.format(encoded)}?width=1024&height=1024&nologo=true"

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


async def edit_image(image_bytes: bytes, prompt: str) -> bytes:
    """Отредактировать изображение. Цепочка бесплатных API:

    1. Google Gemini 2.0 Flash (самое качественное редактирование)
    2. Pollinations.ai (резерв, без ключа)
    """
    # Приоритет: Gemini (редактирует по-настоящему)
    if GEMINI_API_KEY:
        try:
            logger.info("Trying Gemini 2.0 Flash image editing...")
            return await _edit_with_gemini(image_bytes, prompt)
        except Exception as e:
            logger.warning(f"Gemini failed, fallback to Pollinations: {e}")

    # Резерв: генерация похожего изображения
    logger.info("Using Pollinations.ai as fallback")
    enhanced = f"реалистичное фото, высокое качество: {prompt}"
    return await _generate_pollinations(enhanced)
