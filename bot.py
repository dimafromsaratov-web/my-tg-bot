import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import yt_dlp

# Вставьте сюда ваш токен от BotFather внутри кавычек
TOKEN = "7723448271:AAGhveA6kARIklu21qsKCtNU7uZ0DclMfm8"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        await update.message.reply_text("Пожалуйста, отправьте корректную ссылку.")
        return

    status = await update.message.reply_text("Генерирую прямую ссылку на видео...")

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            direct_url = info.get('url') or info.get('formats', [{}])[-1].get('url')
            title = info.get('title', 'Видео')

        if direct_url:
            keyboard = [[InlineKeyboardButton("📥 Скачать видеофайл", url=direct_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"🎬 *{title}*\n\nСсылка готова! Нажмите на кнопку ниже, чтобы скачать видео на телефон в максимальном качестве.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            await status.delete()
        else:
            await status.edit_text("Не удалось получить прямую ссылку для этого сайта.")

    except Exception as e:
        await status.edit_text(f"Произошла ошибка: {str(e)[:100]}...")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот успешно запущен в облаке Render!")
    app.run_polling()

if __name__ == '__main__':
    main()
