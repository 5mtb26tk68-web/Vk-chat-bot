import os
import json
import time
import threading
import vk_api
from flask import Flask
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from mod_en import handle_mod
from fun_en import handle_fun, send_help_menu

app = Flask(__name__)

@app.route('/')
def home():
    return "Full Chat Manager 24/7 is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.environ.get("VK_TOKEN", "").strip()
GROUP_ID = int(os.environ.get("VK_GROUP_ID", "0").strip())
DB_FILE = "db.json"

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

def load_db():
    data = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
    for k in ["users", "chats", "clans"]:
        if k not in data:
            data[k] = {}
    return data

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

db = load_db()
print("Full Chat Manager запущен!", flush=True)
last_save = time.time()

while True:
    try:
        for event in longpoll.listen():
            if time.time() - last_save > 60:
                save_db(db)
                last_save = time.time()

            if event.type == VkBotEventType.MESSAGE_NEW:
                msg = event.obj.message
                if handle_mod(vk, db, save_db, msg):
                    continue
                handle_fun(vk, db, save_db, msg)

            elif event.type == VkBotEventType.MESSAGE_EVENT:
                ev = event.obj
                payload = ev.get("payload", {})
                if "menu" in payload:
                    send_help_menu(vk, ev["peer_id"], payload["menu"], ev["event_id"], ev["user_id"])
    except Exception as e:
        print(f"Ошибка цикла: {e}", flush=True)
        time.sleep(5)
