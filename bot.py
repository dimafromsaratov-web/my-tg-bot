import json
import asyncio
import urllib.request
from http.server import BaseHTTPRequestHandler
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
                    text="Секунду, извлекаю видеопоток через резервный шлюз..."
                )
                
                try:
                    # ИСПРАВЛЕНО: Переключено на стабильный, открытый и рабочий сервер-зеркало Cobalt API
                    api_url = "https://sweeux.org"
                    headers = {
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    }
                    data = json.dumps({
                        "url": url,
                        "videoQuality": "1080",
                        "downloadMode": "video"
                    }).encode("utf-8")
                    
                    req = urllib.request.Request(api_url, data=data, headers=headers, method="POST")
                    
                    # Безопасное извлечение ссылки в фоновом режиме
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req).read())
                    res_json = json.loads(response.decode("utf-8"))
                    
                    direct_url = res_json.get("url")
                    
                    if direct_url:
                        keyboard = [[InlineKeyboardButton("📥 Скачать видеофайл", url=direct_url)]]
                        markup = InlineKeyboardMarkup(keyboard)
                        
                        await app.bot.delete_message(
                            chat_id=update.message.chat_id, 
                            message_id=status_msg.message_id
                        )
                        await app.bot.send_message(
                            chat_id=update.message.chat_id,
                            text="🎬 *Файл успешно подготовлен!*\n\nНажмите на кнопку ниже, чтобы сохранить его на телефон в максимальном качестве:",
                            reply_markup=markup,
                            parse_mode="Markdown"
                        )
                    else:
                        error_msg = res_json.get("text", "Не удалось извлечь ссылку.")
                        await app.bot.edit_message_text(
                            chat_id=update.message.chat_id, 
                            message_id=status_msg.message_id, 
                            text=f"Сервер отклонил запрос: {error_msg}"
                        )
                
                except Exception as e_api:
                    await app.bot.edit_message_text(
                        chat_id=update.message.chat_id, 
                        message_id=status_msg.message_id, 
                        text="Резервный сервер временно перегружен. Попробуйте еще раз через 10 секунд."
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
