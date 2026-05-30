"""Pollinations.ai — бесплатная генерация/редактирование изображений.

Не требует API ключа! Работает через HTTP GET.
Используется как резервный вариант.
"""

import logging
import httpx

logger = logging.getLogger(__name__)

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{}"


async def edit_image_pollinations(prompt: str, width: int = 1024, height: int = 1024) -> bytes:
    """Сгенерировать изображение по текстовому описанию."""
    url = POLLINATIONS_URL.format(prompt) + f"?width={width}&height={height}&nologo=true"

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content
