"""Обработчик редактирования изображений — ConversationHandler."""

import io
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.ai.gemini_edit import edit_image
from src.web.health import save_temp_image, get_temp_url

logger = logging.getLogger(__name__)

PHOTO, PROMPT = range(2)


async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем фото от пользователя."""
    if not update.message or not update.message.photo:
        return PHOTO

    photo = update.message.photo[-1]
    context.user_data["photo_file_id"] = photo.file_id

    await update.message.reply_text(
        "✅ Фото получил!\n\n"
        "Теперь напиши, что хочешь изменить ✏️\n\n"
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
        await update.message.reply_text("❌ Что-то пошло не так. Отправь /start и попробуй снова.")
        return ConversationHandler.END

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="upload_photo",
    )

    msg = await update.message.reply_text(
        "🎨 *Обрабатываю...* ⏳",
        parse_mode="Markdown",
    )

    try:
        file = await context.bot.get_file(file_id)
        image_bytes = io.BytesIO()
        await file.download_to_memory(image_bytes)
        image_bytes.seek(0)
        raw_image = image_bytes.read()

        # Сохраняем во временное хранилище для Pollinations Kontext
        file_id = save_temp_image(raw_image)
        image_url = get_temp_url(file_id)

        result_bytes = await edit_image(raw_image, prompt, image_url=image_url)

        await msg.delete()
        await update.message.reply_photo(
            photo=result_bytes,
            caption=f"✅ *Готово!*",
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Edit failed: {e}", exc_info=True)
        await msg.edit_text(
            "😔 Что-то пошло не так. Попробуй другой запрос или другое фото.\n"
            "Отправь /start чтобы начать заново."
        )

    context.user_data.clear()
    return ConversationHandler.END
