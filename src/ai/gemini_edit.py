"""Редактирование изображений — гибридный подход (бесплатно).

Gemini 2.5 Flash (бесплатный тариф) анализирует твоё фото + твою правку
и пишет детальный промпт. Pollinations рисует по нему.

Цепочка:
1. 🔥 Gemini (анализ фото + твоя правка → детальный промпт) — бесплатно, 1500/день
2. 🎨 Pollinations (рисует по промпту) — бесплатно, без ключа

Не идеальное редактирование, но намного точнее, чем просто "сгенерировать заново".
"""

import os
import io
import logging
import httpx

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


async def _generate_image_via_gemini_prompt_pollinations(
    image_bytes: bytes, user_prompt: str
) -> bytes:
    """Gemini смотрит на фото + правку, пишет детальный промпт для Pollinations,
    который максимально сохраняет композицию, но применяет изменения."""
    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)

        # Загружаем изображение пользователя
        image_file = client.files.upload(
            file=io.BytesIO(image_bytes),
            config={"mime_type": "image/jpeg"},
        )

        # Gemini анализирует фото и пишет промпт для Pollinations
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

        # Генерируем через Pollinations по enhanced промпту
        return await _generate_pollinations(enhanced_prompt)

    except Exception as e:
        logger.error(f"Gemini prompt enhancement failed: {e}", exc_info=True)
        raise


async def _generate_pollinations(prompt: str) -> bytes:
    """Генерация через Pollinations.ai (без ключа)."""
    import urllib.parse
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={abs(hash(prompt)) % 100000}"

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


async def edit_image(image_bytes: bytes, prompt: str) -> bytes:
    """Отредактировать изображение через гибридный подход.

    1. 🔥 Gemini 2.5 Flash → анализирует фото + правку → пишет детальный промпт
    2. 🎨 Pollinations → рисует по промпту (бесплатно, без ключа)
    3. ⚠️ Если Gemini недоступен — Pollinations с простым промптом
    """
    if GEMINI_API_KEY:
        try:
            logger.info("Gemini analyzing image for prompt engineering...")
            return await _generate_image_via_gemini_prompt_pollinations(
                image_bytes, prompt
            )
        except Exception as e:
            logger.warning(f"Gemini prompt enhancement failed, using raw Pollinations: {e}")

    logger.info("Using Pollinations.ai directly (no Gemini)")
    enhanced = f"реалистичное фото, профессиональное качество, 4K: {prompt}"
    return await _generate_pollinations(enhanced)
