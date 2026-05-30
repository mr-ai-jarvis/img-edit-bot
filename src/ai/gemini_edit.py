"""Редактирование изображений через Polza.ai (Media API).

Использует модель google/gemini-2.5-flash-image для редактирования фото.

API: POST https://polza.ai/api/v1/media
Документация: https://polza.ai/docs/api-reference/media/create
"""

import os
import json
import logging
import asyncio
import httpx

logger = logging.getLogger(__name__)

POLZA_AI_API_KEY = os.environ.get("POLZA_AI_API_KEY", "")
POLZA_AI_BASE_URL = "https://polza.ai/api/v1"


async def edit_image(image_url: str, prompt: str) -> bytes:
    """Отредактировать изображение через Polza.ai Media API.

    Args:
        image_url: Публичный URL исходного изображения
        prompt: Описание изменений

    Returns:
        Байты отредактированного изображения
    """
    if not POLZA_AI_API_KEY:
        raise ValueError("POLZA_AI_API_KEY не задан")

    headers = {
        "Authorization": f"Bearer {POLZA_AI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "google/gemini-2.5-flash-image",
        "input": {
            "prompt": prompt,
            "images": [image_url],
            "aspect_ratio": "1:1",
            "image_resolution": "2K",
            "output_format": "png",
        },
    }

    logger.info(f"Polza.ai: sending to gemini-2.5-flash-image...")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{POLZA_AI_BASE_URL}/media",
            headers=headers,
            json=payload,
        )

        # Логируем ошибку если что-то пошло не так
        if response.status_code != 200:
            try:
                error_body = response.json()
                logger.error(f"Polza.ai error {response.status_code}: {error_body}")
            except Exception:
                logger.error(f"Polza.ai error {response.status_code}: {response.text[:500]}")

        response.raise_for_status()
        result = response.json()

        media_id = result.get("id")
        status = result.get("status")

        logger.info(f"Polza.ai: generation {media_id}, status={status}")

        if status == "completed":
            return await _get_media_result(client, headers, media_id)

        if status == "pending":
            return await _poll_media_result(client, headers, media_id)

        raise ValueError(f"Неожиданный статус: {status}")


async def _get_media_result(
    client: httpx.AsyncClient,
    headers: dict,
    media_id: str,
) -> bytes:
    """Получить результат генерации по ID."""
    response = await client.get(
        f"{POLZA_AI_BASE_URL}/media/{media_id}",
        headers=headers,
    )
    response.raise_for_status()
    result = response.json()

    # Извлекаем URL изображения из ответа
    image_url = _extract_image_url(result)
    if not image_url:
        raise ValueError(f"Не удалось найти URL изображения в ответе: {result}")

    logger.info(f"Polza.ai: downloading result from {image_url[:60]}...")

    # Скачиваем изображение
    img_response = await client.get(image_url)
    img_response.raise_for_status()
    return img_response.content


async def _poll_media_result(
    client: httpx.AsyncClient,
    headers: dict,
    media_id: str,
    timeout: int = 120,
    poll_interval: float = 2.0,
) -> bytes:
    """Поллинг статуса генерации до завершения."""
    start = asyncio.get_event_loop().time()
    while True:
        elapsed = asyncio.get_event_loop().time() - start
        if elapsed > timeout:
            raise TimeoutError(f"Таймаут {timeout}с при ожидании генерации {media_id}")

        await asyncio.sleep(poll_interval)

        response = await client.get(
            f"{POLZA_AI_BASE_URL}/media/{media_id}",
            headers=headers,
        )
        response.raise_for_status()
        result = response.json()

        status = result.get("status")
        logger.debug(f"Polza.ai: poll {media_id} status={status}")

        if status == "completed":
            return await _get_media_result(client, headers, media_id)
        elif status == "failed":
            error = result.get("error", "Неизвестная ошибка")
            raise RuntimeError(f"Генерация не удалась: {error}")
        # "pending" — продолжаем ждать


def _extract_image_url(result: dict) -> str | None:
    """Извлечь URL изображения из ответа Media API."""
    # Пробуем разные пути в ответе
    output = result.get("output")
    if isinstance(output, dict):
        url = output.get("url")
        if url:
            return url

    # Прямой путь
    url = result.get("url")
    if url:
        return url

    # Массив output
    if isinstance(output, list) and len(output) > 0:
        if isinstance(output[0], dict):
            return output[0].get("url")

    # data массив
    data = result.get("data")
    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], dict):
            return data[0].get("url")

    return None
