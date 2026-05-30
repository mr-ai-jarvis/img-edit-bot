# 🖼️ Img Edit Bot — AI Image Editor

Telegram-бот для редактирования изображений с помощью AI. Бесплатно, через Hugging Face InstructPix2Pix.

## Возможности

- 🖼 Отправляешь изображение → бот спрашивает, что изменить
- ✏️ Описываешь изменение текстом → бот редактирует
- 🎨 Получаешь результат

## Бесплатные AI API

### Hugging Face Inference API (основной)
- Бесплатный токен, без кредитной карты
- Модель: `timbrooks/instruct-pix2pix`
- Лимит: ~30 000 запросов/месяц бесплатно

**Как получить:**
1. Регистрируешься на [huggingface.co](https://huggingface.co/join)
2. Идёшь в Settings → Access Tokens → **New token**
3. Выбираешь роль **read**
4. Копируешь токен в `HF_TOKEN`

### Pollinations.ai (резервный, без ключа)
- Полностью бесплатный, не требует API ключа
- Генерирует изображения по текстовому описанию

## Деплой на Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/...)

## Переменные окружения

| Переменная | Описание |
|-----------|----------|
| `BOT_TOKEN` | Токен Telegram бота ([@BotFather](https://t.me/BotFather)) |
| `HF_TOKEN` | Токен Hugging Face ([huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)) |
