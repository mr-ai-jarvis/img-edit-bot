"""Обработчик команды /start и /cancel."""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Приветственное сообщение для творческой аудитории."""
    user = update.effective_user
    context.user_data.clear()

    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Отправь мне **фотографию**, напиши, что в ней изменить — "
        "и я всё сделаю 🎨\n\n"
        "Примеры:\n"
        "• *«Сделай фон как пляж»*\n"
        "• *«Преврати в мультяшный стиль»*\n"
        "• *«Убери объект слева»*\n"
        "• *«Сделай ярче и сочнее»*\n\n"
        "Просто отправь фото и напиши, что хочешь поменять 👇",
        parse_mode="Markdown",
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена операции."""
    context.user_data.clear()
    await update.message.reply_text("❌ Отменено. Отправь /start чтобы начать заново.")
    return ConversationHandler.END
