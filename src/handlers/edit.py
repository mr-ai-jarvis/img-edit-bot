"""Обработчик редактирования изображений — ConversationHandler."""

import io
import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from telegram.ext import ConversationHandler

from src.ai.hf_pix2pix import edit_image_hf
from src.ai.pollinations import edit_image_pollinations

logger = logging.getLogger(__name__)

PHOTO, PROMPT = range(2)


async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем фото от пользователя."""
    if not update.message or not update.message.photo:
        return PHOTO

    # Берём самое большое фото
    photo = update.message.photo[-1]
    context.user_data["photo_file_id"] = photo.file_id

    await update.message.reply_text(
        "✅ Фото получил!\n\n"
        "Теперь напиши, **что хочешь изменить** ✏️\n\n"
        "Например: *«сделай фон чёрно-белым»*, *«добавь неоновый эффект»*",
        parse_mode="Markdown",
    )
    return PROMPT


async def receive_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем описание изменений и обрабатываем."""
    prompt = update.message.text.strip()
    if not prompt:
        await update.message.reply_text("Напиши, что хочешь изменить!")
        return PROMPT

    context.user_data["prompt"] = prompt
    file_id = context.user_data.get("photo_file_id")

    if not file_id:
        await update.message.reply_text("❌ Не нашёл фото. Отправь /start и попробуй снова.")
        return ConversationHandler.END

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="upload_photo",
    )

    msg = await update.message.reply_text(
        f"🎨 *Редактирую...*\n\n"
        f"Запрос: _{prompt}_\n\n"
        f"Это может занять до 30 секунд. Жди! ⏳",
        parse_mode="Markdown",
    )

    try:
        # Скачиваем фото
        file = await context.bot.get_file(file_id)
        image_bytes = io.BytesIO()
        await file.download_to_memory(image_bytes)
        image_bytes.seek(0)
        raw_image = image_bytes.read()

        # Пробуем InstructPix2Pix через Hugging Face (бесплатно)
        try:
            result_bytes = await edit_image_hf(raw_image, prompt)
        except Exception as e:
            logger.warning(f"Hugging Face failed, fallback to Pollinations: {e}")
            # Резерв: генерация через Pollinations
            result_bytes = await edit_image_pollinations(prompt)

        # Отправляем результат
        await msg.delete()
        await update.message.reply_photo(
            photo=result_bytes,
            caption=f"✅ *Готово!*\n\n_{prompt}_",
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Edit failed: {e}", exc_info=True)
        await msg.edit_text(
            "😔 Не удалось отредактировать изображение. "
            "Попробуй другой запрос или другое фото.\n"
            "Отправь /start чтобы начать заново."
        )

    context.user_data.clear()
    return ConversationHandler.END
