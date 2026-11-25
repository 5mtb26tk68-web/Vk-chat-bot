import os
import json
import time
import threading
import vk_api
from flask import Flask
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from commands import handle_message

app = Flask(__name__)

@app.route('/')
def home():
    return "VK Bot is running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.environ.get("VK_TOKEN")
GROUP_ID = int(os.environ.get("VK_GROUP_ID"))
DB_FILE = "db.json"

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "chats": {}}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

db = load_db()
print("Бот успешно запущен на Render!")
last_save = time.time()

while True:
    try:
        for event in longpoll.listen():
            if time.time() - last_save > 60:
                save_db(db)
                last_save = time.time()

            if event.type == VkBotEventType.MESSAGE_NEW:
                handle_message(vk, db, save_db, event.obj.message)
    except Exception as e:
        print("Ошибка сети:", e)
        time.sleep(5)
