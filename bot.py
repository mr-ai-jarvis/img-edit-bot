"""
Img Edit Bot — главный entry point.
Telegram-бот для обработки изображений.
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    ConversationHandler, filters,
)

from src.handlers.start import start_command, cancel
from src.handlers.edit import receive_image, receive_prompt, PHOTO, PROMPT
from src.web.health import start_health_server

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Запуск бота."""
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        logger.error("❌ BOT_TOKEN не задан!")
        return

    app = Application.builder().token(bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.PHOTO, receive_image)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, receive_image)],
            PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_prompt)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(conv_handler)

    start_health_server()
    logger.info("🖼️ Img Edit Bot запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
