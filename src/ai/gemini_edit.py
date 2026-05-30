"""Редактирование изображений — Google Gemini API (бесплатно).

Использует новую библиотеку google.genai (не deprecated google-generativeai).
Модель: gemini-2.5-flash-image

Как работает:
1. Загружаем изображение пользователя через client.files.upload()
2. Отправляем изображение + инструкцию в Gemini
3. Gemini возвращает отредактированное изображение

Бесплатно: 1500 запросов/день на Gemini API.
"""

import os
import io
import logging
import httpx

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


async def _edit_with_gemini_genai(image_bytes: bytes, prompt: str) -> bytes:
    """Редактирование через новую google.genai библиотеку."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)

        # Загружаем изображение пользователя
        image_file = client.files.upload(
            file=io.BytesIO(image_bytes),
            config=dict(
                mime_type="image/jpeg",
            ),
        )

        # Отправляем изображение + инструкцию
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[
                f"Отредактируй это изображение: {prompt}. "
                f"Сохрани оригинальную композицию, но примени изменения.",
                image_file,
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Извлекаем изображение из ответа
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                return part.inline_data.data
            elif hasattr(part, "as_image"):
                img = part.as_image()
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                return buf.getvalue()

        raise ValueError("Gemini не вернул изображение")

    except Exception as e:
        logger.error(f"Gemini genai edit failed: {e}", exc_info=True)
        raise


async def _generate_pollinations(prompt: str, seed: int = None) -> bytes:
    """Резерв: генерация через Pollinations.ai (без ключа)."""
    import urllib.parse
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"
    if seed is not None:
        url += f"&seed={seed}"

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


async def edit_image(image_bytes: bytes, prompt: str) -> bytes:
    """Отредактировать изображение через цепочку бесплатных API.

    1. Google Gemini 2.5 Flash Image (редактирует твоё изображение)
    2. Pollinations.ai (резерв: генерирует новое по описанию)
    """
    if GEMINI_API_KEY:
        try:
            logger.info("Trying Gemini 2.5 Flash Image editing...")
            return await _edit_with_gemini_genai(image_bytes, prompt)
        except Exception as e:
            logger.warning(f"Gemini failed, using Pollinations: {e}")

    logger.info("Using Pollinations.ai as fallback")
    enhanced = f"реалистичное фото, профессиональное качество: {prompt}"
    return await _generate_pollinations(enhanced)
