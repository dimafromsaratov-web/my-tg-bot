import os
import json
import asyncio
from http.server import BaseHTTPRequestHandler
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application

TOKEN = "7723448271:AAGhveA6kARIklu21qsKCtNU7uZ0DclMfm8"

async def process_update(update_dict):
    app = Application.builder().token(TOKEN).build()
    await app.initialize()
    
    update = Update.de_json(update_dict, app.bot)
    if update and update.message and update.message.text:
        url = update.message.text
        if url.startswith("http"):
            # Быстро извлекаем прямую ссылку через yt-dlp
            ydl_opts = {'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 'quiet': True}
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    direct_url = info.get('url') or info.get('formats', [{}])[-1].get('url')
                    title = info.get('title', 'Видео')
                
                if direct_url:
                    keyboard = [[InlineKeyboardButton("📥 Скачать видеофайл", url=direct_url)]]
                    markup = InlineKeyboardMarkup(keyboard)
                    await app.bot.send_message(
                        chat_id=update.message.chat_id,
                        text=f"🎬 *{title}*\n\nСсылка готова! Нажмите кнопку ниже для скачивания:",
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                await app.bot.send_message(chat_id=update.message.chat_id, text="Ошибка обработки ссылки.")
    await app.shutdown()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        update_dict = json.loads(post_data.decode('utf-8'))
        
        # Запускаем асинхронную обработку сообщения от Telegram
        asyncio.run(process_update(update_dict))
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
