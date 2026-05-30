"""Обработчик команды /start и /cancel."""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Приветственное сообщение."""
    user = update.effective_user
    context.user_data.clear()

    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я — **AI-редактор изображений** 🖼️\n\n"
        "Как это работает:\n"
        "1️⃣ Отправь мне **фотографию**\n"
        "2️⃣ Напиши, **что хочешь изменить**\n"
        "3️⃣ Я отредактирую и пришлю результат\n\n"
        "Примеры запросов:\n"
        "• *«Сделай фон как пляж»*\n"
        "• *«Преврати в мультяшный стиль»*\n"
        "• *«Убери объект слева»*\n"
        "• *«Сделай изображение более ярким»*\n\n"
        "Просто отправь фото и начнём! 👇\n\n"
        "_(Бесплатно через Hugging Face InstructPix2Pix)_",
        parse_mode="Markdown",
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена операции."""
    context.user_data.clear()
    await update.message.reply_text("❌ Отменено. Отправь /start чтобы начать заново.")
    return ConversationHandler.END
