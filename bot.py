import json
import asyncio
import urllib.request
from http.server import BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application

TOKEN = "7723448271:AAGhveA6kARIklu21qsKCtNU7uZ0DclMfm8"

# Список из 5 независимых рабочих серверов-зеркал Cobalt API
SERVERS = [
    "https://api.cobalt.tools/",
    "https://hyper.lol",
    "https://cgm.rs",
    "https://oak.li",
    "https://rooot.gay"
]

async def get_direct_link(url):
    """Функция перебирает сервера по очереди, пока один не сработает"""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "url": url,
        "videoQuality": "1080",
        "downloadMode": "video"
    }).encode("utf-8")
    
    loop = asyncio.get_event_loop()
    
    for server in SERVERS:
        try:
            req = urllib.request.Request(server, data=data, headers=headers, method="POST")
            # Ограничиваем время ожидания сервера 6 секундами, чтобы не ждать долго
            response = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=6).read())
            res_json = json.loads(response.decode("utf-8"))
            
            if res_json.get("url"):
                return res_json.get("url"), None
        except Exception as e:
            # Если этот сервер выдал ошибку, цикл просто идет к следующему
            continue
            
    return None, "Все резервные сервера сейчас перегружены. Попробуйте еще раз через минуту."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Код оставлен для совместимости, основная логика ниже в process_update
    pass

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
                    text="Секунду, подбираю свободный сервер дешифрации..."
                )
                
                # Запускаем умный поиск ссылки
                direct_url, error = await get_direct_link(url)
                
                if direct_url:
                    keyboard = [[InlineKeyboardButton("📥 Скачать видеофайл", url=direct_url)]]
                    markup = InlineKeyboardMarkup(keyboard)
                    
                    await app.bot.delete_message(chat_id=update.message.chat_id, message_id=status_msg.message_id)
                    await app.bot.send_message(
                        chat_id=update.message.chat_id,
                        text="🎬 *Файл успешно подготовлен!*\n\nНажмите на кнопку ниже, чтобы сохранить его на телефон в максимальном качестве:",
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                else:
                    await app.bot.edit_message_text(
                        chat_id=update.message.chat_id, 
                        message_id=status_msg.message_id, 
                        text=error if error else "Не удалось извлечь ссылку."
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
