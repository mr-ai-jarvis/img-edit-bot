"""Редактирование изображений — многоуровневый подход (всё бесплатно).

Цепочка (от лучшего к простому):
1. 🎨 Pollinations Kontext — image-to-image, редактирует реально (без ключа, через temp URL)
2. 🔥 Gemini 2.5 Flash → пишет детальный промпт → Pollinations рисует (1500/день)
3. 🎨 Pollinations напрямую (всегда работает)
"""

import os
import io
import logging
import httpx

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


async def _edit_with_kontext(image_url: str, prompt: str) -> bytes:
    """Pollinations Kontext — реальное редактирование изображения (image-to-image).

    Передаём URL оригинального фото + промпт, модель меняет фото по описанию.
    Без ключа, бесплатно.
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

    logger.info(f"Kontext: {prompt[:60]}...")
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


async def _generate_image_via_gemini_prompt_pollinations(
    image_bytes: bytes, user_prompt: str
) -> bytes:
    """Gemini смотрит на фото + правку, пишет детальный промпт для Pollinations."""
    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)

        image_file = client.files.upload(
            file=io.BytesIO(image_bytes),
            config={"mime_type": "image/jpeg"},
        )

        system_instruction = (
            "Ты — профессиональный промпт-инженер. "
            "Я покажу тебе фотографию и напишу, что на ней нужно изменить. "
            "Твоя задача — написать максимально детальный промпт НА РУССКОМ ЯЗЫКЕ "
            "для нейросети-генератора изображений, который опишет ИСХОДНУЮ фотографию "
            "с УЖЕ ВНЕСЁННЫМИ изменениями.\n\n"
            "Правила:\n"
            "- Опиши всё, что есть на фото: объекты, фон, освещение, цвета, композицию\n"
            "- Примени указанные изменения (например, если просят покрасить слона — опиши слона жёлтым)\n"
            "- Сохрани стиль и композицию оригинала максимально близко\n"
            "- Добавь в конце: 'реалистичное фото, высокое качество, 4K'\n"
            "- НЕ пиши 'нравится', 'отлично', 'вот' — только чистый промпт\n"
            "- Весь промпт на русском языке\n"
            "- Максимум 300 символов, одним абзацем"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                system_instruction,
                image_file,
                user_prompt,
            ],
        )

        enhanced_prompt = response.text.strip()
        logger.info(f"Gemini enhanced prompt: {enhanced_prompt[:100]}...")

        return await _generate_pollinations(enhanced_prompt)

    except Exception as e:
        logger.error(f"Gemini prompt enhancement failed: {e}", exc_info=True)
        raise


async def _generate_pollinations(prompt: str) -> bytes:
    """Обычная генерация через Pollinations.ai (без ключа)."""
    import urllib.parse
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={abs(hash(prompt)) % 100000}"

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


async def edit_image(
    image_bytes: bytes,
    prompt: str,
    image_url: str | None = None,
) -> bytes:
    """Отредактировать изображение — многоуровневая цепочка бесплатных API.

    Приоритет:
    1. 🎨 Pollinations Kontext — image-to-image, редактирует реально
       (нужен image_url — публичная ссылка на оригинал)
    2. 🔥 Gemini анализирует → Pollinations рисует по детальному промпту
       (нужен GEMINI_API_KEY, 1500 запросов/день бесплатно)
    3. 🎨 Pollinations напрямую — всегда работает, но генерирует с нуля
    """
    # Уровень 1: Pollinations Kontext (реальное редактирование)
    if image_url:
        try:
            logger.info("Level 1: Trying Pollinations Kontext (image-to-image)...")
            return await _edit_with_kontext(image_url, prompt)
        except Exception as e:
            logger.warning(f"Kontext failed: {e}")

    # Уровень 2: Gemini + Pollinations (умный промпт)
    if GEMINI_API_KEY:
        try:
            logger.info("Level 2: Gemini analyzes + Pollinations draws...")
            return await _generate_image_via_gemini_prompt_pollinations(
                image_bytes, prompt
            )
        except Exception as e:
            logger.warning(f"Gemini hybrid failed: {e}")

    # Уровень 3: Pollinations напрямую (всегда работает)
    logger.info("Level 3: Pollinations directly")
    enhanced = f"реалистичное фото, профессиональное качество, 4K: {prompt}"
    return await _generate_pollinations(enhanced)
