import json
import asyncio
import urllib.request
from http.server import BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application

TOKEN = "7723448271:AAGhveA6kARIklu21qsKCtNU7uZ0DclMfm8"

# Список стабильных мировых открытых инстансов Invidious (альтернативный плеер YouTube)
INVIDIOUS_INSTANCES = [
    "https://io.lol",
    "https://yewtu.be",
    "https://puffyan.us",
    "https://tux.digital",
    "https://nerdvpn.de"
]

async def get_youtube_stream(url):
    """Извлекает ID видео и ищет прямую ссылку через распределенную сеть Invidious"""
    video_id = None
    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    elif "be/" in url:
        video_id = url.split("be/")[1].split("?")[0]
        
    if not video_id:
        return None, "Не удалось распознать ID видео. Проверьте ссылку."

    loop = asyncio.get_event_loop()
    
    for instance in INVIDIOUS_INSTANCES:
        try:
            # Делаем официальный сверхлегкий текстовый запрос к API видеоплеера
            api_url = f"{instance}/api/v1/videos/{video_id}"
            req = urllib.request.Request(api_url, method="GET")
            
            response = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=5).read())
            res_json = json.loads(response.decode("utf-8"))
            
            format_streams = res_json.get("formatStreams", [])
            if format_streams:
                # Берем самый первый доступный готовый MP4 поток со звуком
                direct_url = format_streams[0].get("url")
                title = res_json.get("title", "Видео")
                if direct_url:
                    return {"url": direct_url, "title": title}, None
        except:
            continue
            
    return None, "Все линии загрузки YouTube сейчас заняты. Попробуйте еще раз через минуту."

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
                    text="Секунду, подключаюсь к выделенной линии скачивания..."
                )
                
                # Запускаем извлечение через чистый медиа-поток
                result, error = await get_youtube_stream(url)
                
                if result and result.get("url"):
                    keyboard = [[InlineKeyboardButton("📥 Скачать видеофайл", url=result["url"])]]
                    markup = InlineKeyboardMarkup(keyboard)
                    
                    await app.bot.delete_message(chat_id=update.message.chat_id, message_id=status_msg.message_id)
                    await app.bot.send_message(
                        chat_id=update.message.chat_id,
                        text=f"🎬 *{result['title']}*\n\nСсылка полностью готова! Нажмите на кнопку ниже, чтобы сохранить файл:",
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                else:
                    await app.bot.edit_message_text(
                        chat_id=update.message.chat_id, 
                        message_id=status_msg.message_id, 
                        text=error if error else "Ошибка обработки ссылки."
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
