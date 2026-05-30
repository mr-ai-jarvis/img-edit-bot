"""AI обработка изображений — несколько бесплатных API.

Цепочка попыток:
1. Hugging Face InstructPix2Pix (если доступен)
2. Hugging Face через альтернативные эндпоинты
3. Pollinations.ai — генерация по промпту (всегда работает)
"""

import os
import base64
import json
import logging
import httpx

logger = logging.getLogger(__name__)

HF_TOKEN = os.environ.get("HF_TOKEN", "")

# Несколько эндпоинтов HF на случай, если какой-то не работает из Railway
HF_ENDPOINTS = [
    "https://api-inference.huggingface.co/models/{}",
    "https://router.huggingface.co/hf-inference/models/{}",
]

# Модели для редактирования по порядку
HF_MODELS = [
    "timbrooks/instruct-pix2pix",
    "black-forest-labs/FLUX.1-Kontext-dev",
]


async def _try_hf_endpoint(image_b64: str, prompt: str) -> bytes:
    """Пробует все HF эндпоинты и модели."""
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN не задан")

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": image_b64,
        "parameters": {
            "prompt": prompt,
            "guidance_scale": 7.5,
            "image_guidance_scale": 1.5,
        },
    }

    for model in HF_MODELS:
        for endpoint_template in HF_ENDPOINTS:
            url = endpoint_template.format(model)
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(
                        url, headers=headers, content=json.dumps(payload)
                    )
                    if response.status_code == 200:
                        logger.info(f"✅ HF success: {url}")
                        return response.content
                    logger.warning(f"⚠️ HF {url}: {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ HF {url}: {e}")
                continue

    raise Exception("Все HF эндпоинты не сработали")


async def _try_pollinations_generate(prompt: str) -> bytes:
    """Генерация через Pollinations.ai (без ключа)."""
    import urllib.parse
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


async def edit_image(image_bytes: bytes, prompt: str) -> bytes:
    """Отредактировать изображение — цепочка бесплатных API."""
    # Пытаемся через HF InstructPix2Pix (редактирует по-настоящему)
    if HF_TOKEN:
        img_b64 = base64.b64encode(image_bytes).decode("utf-8")
        try:
            return await _try_hf_endpoint(img_b64, prompt)
        except Exception as e:
            logger.warning(f"HF API all failed, fallback to Pollinations: {e}")

    # Резерв: генерация на основе описания
    logger.info("Using Pollinations.ai as fallback")
    enhanced_prompt = f"реалистичное фото: {prompt}, профессиональное качество, детализированное"
    return await _try_pollinations_generate(enhanced_prompt)
