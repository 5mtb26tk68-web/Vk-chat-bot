import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json, time, os, threading
from flask import Flask

# ─── Загрузка БД ───
def load_db():
    if not os.path.exists("db.json"):
        with open("db.json", "w", encoding="utf-8") as f:
            json.dump({"users": {}, "promo": {}, "clans": {}, "settings": {}}, f)
    with open("db.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open("db.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

DB = load_db()

# ─── Конфиг ───
TOKEN = os.getenv("VK_TOKEN", "ТВОЙ_ТОКЕН_СЮДА")
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
DEVELOPERS = [int(x) for x in os.getenv("DEVELOPERS", "0").split(",") if x]
PREFIX = "!"

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

# ─── Flask сервер для Render ───
app = Flask("")

@app.route("/")
def home():
    return "🌟 Astra • Чат-менеджер is alive!"

def run_server():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_server, daemon=True).start()

# ─── Утилиты ───
def get_user(uid):
    if str(uid) not in DB["users"]:
        DB["users"][str(uid)] = {
            "balance": 1000, "bank": 0, "xp": 0, "level": 0,
            "warns": 0, "reputation": 0, "business": None,
            "business_time": 0, "work_time": 0, "bonus_time": 0,
            "deposit": 0, "deposit_time": 0, "car": None,
            "house": None, "yacht": None, "phone": None,
            "pickaxe_level": 1, "rod_level": 1,
            "married_to": 0, "clan_id": 0,
            "inventory": {}, "achievements": [],
            "muted_until": 0, "messages_count": 0,
            "last_msg_time": 0, "nickname": None
        }
        save_db(DB)
    return DB["users"][str(uid)]

def save_user(uid):
    save_db(DB)

def extract_user(text):
    import re
    m = re.search(r"(?:@id|id)(\d+)", text)
    return int(m.group(1)) if m else None

def is_admin(uid):
    return uid in DEVELOPERS

def fmt(n):
    return f"{n:,}".replace(",", " ")

def get_kb():
    kb = VkKeyboard(inline=True)
    kb.add_callback_button("💰 Баланс", {"cmd": "balance"}, color=VkKeyboardColor.PRIMARY)
    kb.add_callback_button("💼 Работа", {"cmd": "work"}, color=VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_callback_button("👤 Профиль", {"cmd": "profile"}, color=VkKeyboardColor.SECONDARY)
    kb.add_callback_button("🎁 Промокод", {"cmd": "promo_menu"}, color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()

# ─── Импорт хендлеров ───
from commands import handle as handle_commands
from fun_en import handle as handle_fun
from mod_en import handle as handle_mod

print("🌟 Astra запущена!")

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
        peer_id = event.peer_id
        user_id = event.user_id
        text = event.text.strip()

        u = get_user(user_id)

        # Проверка мута
        if u["muted_until"] > time.time():
            try:
                vk.messages.delete(peer_id=peer_id, message_ids=event.message_id, delete_for_all=1)
            except: pass
            continue

        # XP за сообщение
        u["xp"] += 5
        u["messages_count"] += 1
        new_lvl = int(u["xp"] ** 0.5)
        if new_lvl > u["level"]:
            u["level"] = new_lvl
            vk.messages.send(peer_id=peer_id,
                message=f"🎉 [id{user_id}|Пользователь] достиг {new_lvl} уровня!",
                random_id=0)

        # Парсинг команды
        if not text.lower().startswith(PREFIX):
            save_user(user_id)
            continue

        parts = text[len(PREFIX):].strip().split(maxsplit=1)
        cmd = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""

        # Роутинг
        if cmd in ("баланс", "balance", "работа", "work", "бонус", "bonus",
                   "бизнесы", "businesses", "купить", "buy", "доход", "income",
                   "банк", "bank", "депозит", "deposit", "снять", "withdraw",
                   "перевод", "transfer", "профиль", "profile", "топ", "top",
                   "инвентарь", "inventory", "кейс", "case", "открыть", "open",
                   "ферма", "farm", "шахта", "mine", "рыбалка", "fish",
                   "свадьба", "marry", "развод", "divorce", "репа", "rep",
                   "клан", "clan", "помощь", "help", "админинфо", "admininfo",
                   "выдатьбаланс", "givebalance", "забратьбаланс", "takebalance",
                   "выдатьуровень", "givelevel", "выдатьварн", "givewarn",
                   "снятьварн", "removewarn", "выдатьмут", "givemute",
                   "снятьмут", "removemute", "кик", "kick", "создатьпромо",
                   "createpromo", "удалитьпромо", "deletepromo", "промокоды",
                   "promos", "выдатьбизнес", "givebusiness", "забратьбизнес",
                   "takebusiness", "выдатьимущество", "giveproperty",
                   "забратьимущество", "takeproperty", "обнулить", "reset",
                   "админы", "admins", "настройки", "settings"):
            handle_commands(vk, peer_id, user_id, cmd, args, DB, get_user, save_user, fmt, extract_user, is_admin, get_kb)

        elif cmd in ("казино", "casino", "слоты", "slots", "монетка", "coin",
                     "кости", "dice", "краш", "crash", "дуэль", "duel",
                     "рулетка", "roulette", "угадай", "guess", "матч", "match",
                     "викторина", "quiz", "анекдот", "joke", "факт", "fact",
                     "цитата", "quote", "погода", "weather", "карта", "card",
                     "тату", "tattoo", "астрология", "astro", "совместимость",
                     "compat", "предсказание", "prediction", "8ball", "шар",
                     "кубик", "cube", "подбросить", "flip"):
            handle_fun(vk, peer_id, user_id, cmd, args, DB, get_user, save_user, fmt, extract_user)

        elif cmd in ("варн", "warn", "мут", "mute", "бан", "ban", "кик", "kick",
                     "снятьварн", "unwarn", "снятьмут", "unmute", "антимат",
                     "antimat", "антиспам", "antispam", "антиссылки", "antlinks",
                     "приветствие", "welcome", "прощание", "goodbye", "правила",
                     "rules", "закреп", "pin", "открепить", "unpin", "очистить",
                     "clear", "медленный", "slowmode", "толькоадмины", "adminonly"):
            handle_mod(vk, peer_id, user_id, cmd, args, DB, get_user, save_user, fmt, extract_user, is_admin)

        save_user(user_id)
