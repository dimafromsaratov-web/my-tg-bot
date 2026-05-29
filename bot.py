import os
import sys
import json
import asyncio
import shutil
from http.server import BaseHTTPRequestHandler

# Обновление движка в оперативной памяти Vercel
try:
    import pip
    pip.main(['install', '--upgrade', 'yt-dlp'])
except:
    os.system(f"{sys.executable} -m pip install --upgrade yt-dlp")

import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application

TOKEN = "7723448271:AAGhveA6kARIklu21qsKCtNU7uZ0DclMfm8"

async def process_update(update_dict):
    app = Application.builder().token(TOKEN).build()
    await app.initialize()
    
    try:
        update = Update.de_json(update_dict, app.bot)
        if update and update.message and update.message.text:
            url = update.message.text.strip()
            
            if url.startswith("http"):
                status_msg = await app.bot.send_message(
                    chat_id=update.message.chat_id, 
                    text="Секунду, извлекаю видеопоток..."
                )
                
                # Безопасное копирование cookies.txt во временную папку /tmp
                cookies_path = None
                if os.path.exists('cookies.txt'):
                    tmp_cookies = '/tmp/cookies.txt'
                    try:
                        shutil.copyfile('cookies.txt', tmp_cookies)
                        cookies_path = tmp_cookies
                    except:
                        cookies_path = 'cookies.txt'
                
                # ИСПРАВЛЕНО: Полностью всеядный формат для любых сайтов
                ydl_opts = {
                    'format': 'bestvideo+bestaudio/best', 
                    'quiet': True,
                    'no_warnings': True,
                    'nocheckcertificate': True,
                    'cachedir': False,
                    'cookiefile': cookies_path
                }
                
                try:
                    loop = asyncio.get_event_loop()
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = await loop.run_in_executor(
                            None, 
                            lambda: ydl.extract_info(url, download=False)
                        )
                        
                        direct_url = info.get('url') or info.get('formats', [{}])[-1].get('url')
                        title = info.get('title', 'Видео')
                    
                    if direct_url:
                        keyboard = [[InlineKeyboardButton("📥 Скачать видеофайл", url=direct_url)]]
                        markup = InlineKeyboardMarkup(keyboard)
                        
                        await app.bot.delete_message(
                            chat_id=update.message.chat_id, 
                            message_id=status_msg.message_id
                        )
                        await app.bot.send_message(
                            chat_id=update.message.chat_id,
                            text=f"🎬 *{title}*\n\nФайл успешно подготовлен! Нажмите на кнопку ниже, чтобы сохранить его на телефон:",
                            reply_markup=markup,
                            parse_mode="Markdown"
                        )
                    else:
                        await app.bot.edit_message_text(
                            chat_id=update.message.chat_id, 
                            message_id=status_msg.message_id, 
                            text="Не удалось получить прямую ссылку."
                        )
                
                except Exception as e_ydl:
                    error_text = str(e_ydl)[:150]
                    await app.bot.edit_message_text(
                        chat_id=update.message.chat_id, 
                        message_id=status_msg.message_id, 
                        text=f"Ошибка дешифрации: {error_text}"
                    )
    except Exception as e_global:
        print(f"Ошибка: {e_global}")
        
    await app.shutdown()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        update_dict = json.loads(post_data.decode('utf-8'))
        
        asyncio.run(process_update(update_dict))
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
