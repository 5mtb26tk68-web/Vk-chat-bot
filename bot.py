import os
import re
import json
import time
import random
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

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

def get_user(user_id):
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {"balance": 1000, "last_bonus": 0}
    return db["users"][uid]

def get_chat_member(peer_id, user_id):
    pid, uid = str(peer_id), str(user_id)
    if pid not in db["chats"]:
        db["chats"][pid] = {}
    if uid not in db["chats"][pid]:
        db["chats"][pid][uid] = {"warns": 0, "mute_until": 0}
    return db["chats"][pid][uid]

def send_msg(peer_id, text):
    vk.messages.send(peer_id=peer_id, message=text, random_id=get_random_id())

def is_admin(peer_id, user_id):
    try:
        members = vk.messages.getConversationMembers(peer_id=peer_id)
        for item in members["items"]:
            if item["member_id"] == user_id:
                return item.get("is_admin", False) or item.get("is_owner", False)
    except Exception:
        return False
    return False

def extract_target(msg_obj, args):
    if "reply_message" in msg_obj:
        return msg_obj["reply_message"]["from_id"]
    if args:
        match = re.search(r"\[id(\d+)\|", " ".join(args))
        if match:
            return int(match.group(1))
    return None

def get_name(user_id):
    if user_id < 0:
        return "Бот"
    user = vk.users.get(user_ids=user_id)[0]
    return f"[id{user_id}|{user['first_name']} {user['last_name']}]"

print("Чат-менеджер и казино запущены!")
start_time = time.time()
MAX_RUNTIME = 5 * 3600 + 40 * 60
last_save = time.time()

for event in longpoll.listen():
    if time.time() - last_save > 300:
        save_db(db)
        last_save = time.time()

    if time.time() - start_time > MAX_RUNTIME:
        save_db(db)
        break

    if event.type == VkBotEventType.MESSAGE_NEW:
        msg_obj = event.obj.message
        peer_id = msg_obj["peer_id"]
        from_id = msg_obj["from_id"]
        text = msg_obj.get("text", "").strip()

        if from_id < 0:
            continue

        is_chat = peer_id > 2000000000

        if is_chat:
            member_data = get_chat_member(peer_id, from_id)
            if member_data["mute_until"] > time.time():
                if not is_admin(peer_id, from_id):
                    try:
                        vk.messages.delete(
                            peer_id=peer_id,
                            cmids=msg_obj["conversation_message_id"],
                            delete_for_all=1
                        )
                    except Exception:
                        pass
                continue

        if not text:
            continue

        parts = text.split()
        cmd = parts[0].lower().lstrip("/!.")
        args = parts[1:]

        user_data = get_user(from_id)

        if cmd in ["помощь", "команды", "help"]:
            help_text = (
                "🎮 ЭКОНОМИКА И ИГРЫ:\n"
                "• Баланс — проверить счет\n"
                "• Бонус — получить монеты (раз в час)\n"
                "• Казино [ставка / все] — испытать удачу\n"
                "• Перевод [@юзер или ответ] [сумма] — перевести монеты\n\n"
                "🛡 МОДЕРАЦИЯ (для админов беседы):\n"
                "• Кик / Бан [@юзер или ответ] — исключить из чата\n"
                "• Мут [@юзер или ответ] [минуты] — запретить писать\n"
                "• Размут [@юзер или ответ] — снять мут\n"
                "• Варн [@юзер или ответ] — выдать предупреждение (3 = кик)\n"
                "• Снятьварны [@юзер или ответ] — обнулить варны"
            )
            send_msg(peer_id, help_text)

        elif cmd in ["баланс", "б", "профиль"]:
            warns_info = ""
            if is_chat:
                w = get_chat_member(peer_id, from_id)["warns"]
                warns_info = f"\n⚠️ Варнов в чате: {w}/3"
            send_msg(peer_id, f"👤 {get_name(from_id)}\n💰 Баланс: {user_data['balance']} монет{warns_info}")

        elif cmd == "бонус":
            now = time.time()
            if now - user_data["last_bonus"] < 3600:
                left = int((3600 - (now - user_data["last_bonus"])) // 60) + 1
                send_msg(peer_id, f"⏳ Бонус можно забрать через {left} мин.")
            else:
                reward = random.randint(250, 750)
                user_data["balance"] += reward
                user_data["last_bonus"] = now
                send_msg(peer_id, f"🎁 {get_name(from_id)}, вы получили {reward} монет! Баланс: {user_data['balance']}")

        elif cmd in ["казино", "каз"]:
            if not args:
                send_msg(peer_id, "❌ Укажите ставку. Пример: Казино 500 или Казино все")
                continue

            if args[0].lower() in ["все", "всё", "all"]:
                bet = user_data["balance"]
            elif args[0].isdigit():
                bet = int(args[0])
            else:
                send_msg(peer_id, "❌ Неверная сумма ставки.")
                continue

            if bet <= 0 or bet > user_data["balance"]:
                send_msg(peer_id, f"❌ Недостаточно средств! Ваш баланс: {user_data['balance']}")
                continue

            chance = random.randint(1, 100)
            if chance <= 45:
                win = bet
                user_data["balance"] += win
                send_msg(peer_id, f"🎰 {get_name(from_id)} выиграл {win} монет! (x2)\n💰 Баланс: {user_data['balance']}")
            elif chance <= 50:
                win = bet * 4
                user_data["balance"] += win
                send_msg(peer_id, f"🔥 ДЖЕКПОТ! {get_name(from_id)} сорвал куш +{win} монет! (x5)\n💰 Баланс: {user_data['balance']}")
            else:
                user_data["balance"] -= bet
                send_msg(peer_id, f"📉 {get_name(from_id)} проиграл {bet} монет...\n💰 Баланс: {user_data['balance']}")

        elif cmd in ["перевод", "перевести", "дать"]:
            target_id = extract_target(msg_obj, args)
            amount = None
            for a in args:
                if a.isdigit():
                    amount = int(a)
                    break

            if not target_id or not amount:
                send_msg(peer_id, "❌ Пример: Перевод @пользователь 500 (или ответом на сообщение: Перевод 500)")
                continue

            if target_id == from_id or target_id < 0:
                send_msg(peer_id, "❌ Нельзя переводить самому себе или боту.")
                continue

            if amount <= 0 or amount > user_data["balance"]:
                send_msg(peer_id, f"❌ Недостаточно монет. Ваш баланс: {user_data['balance']}")
                continue

            target_data = get_user(target_id)
            user_data["balance"] -= amount
            target_data["balance"] += amount
            send_msg(peer_id, f"✅ {get_name(from_id)} перевел {amount} монет пользователю {get_name(target_id)}!")

        elif cmd in ["кик", "бан", "мут", "размут", "варн", "снятьварны"]:
            if not is_chat:
                send_msg(peer_id, "❌ Эта команда работает только в беседах.")
                continue

            if not is_admin(peer_id, from_id):
                send_msg(peer_id, "⛔ У вас нет прав администратора беседы.")
                continue

            target_id = extract_target(msg_obj, args)
            if not target_id:
                send_msg(peer_id, "❌ Укажите пользователя через @упоминание или ответьте на его сообщение.")
                continue

            if target_id == from_id or is_admin(peer_id, target_id):
                send_msg(peer_id, "❌ Нельзя применить команду к себе или другому администратору.")
                continue

            chat_id = peer_id - 2000000000
            target_member = get_chat_member(peer_id, target_id)

            if cmd in ["кик", "бан"]:
                try:
                    vk.messages.removeChatUser(chat_id=chat_id, member_id=target_id)
                    send_msg(peer_id, f"🔨 Администратор {get_name(from_id)} исключил {get_name(target_id)} из беседы.")
                except Exception as e:
                    send_msg(peer_id, f"❌ Не удалось кикнуть. Проверьте, выданы ли боту права админа. ({e})")

            elif cmd == "мут":
                minutes = 10
                for a in args:
                    if a.isdigit():
                        minutes = int(a)
                        break
                target_member["mute_until"] = time.time() + (minutes * 60)
                send_msg(peer_id, f"🔇 {get_name(target_id)} получил мут на {minutes} мин. Его сообщения будут удаляться.")

            elif cmd == "размут":
                target_member["mute_until"] = 0
                send_msg(peer_id, f"🔊 С пользователя {get_name(target_id)} снят мут.")

            elif cmd == "варн":
                target_member["warns"] += 1
                w = target_member["warns"]
                if w >= 3:
                    target_member["warns"] = 0
                    try:
                        vk.messages.removeChatUser(chat_id=chat_id, member_id=target_id)
                        send_msg(peer_id, f"🚨 {get_name(target_id)} получил 3/3 предупреждений и был автоматически исключен!")
                    except Exception:
                        send_msg(peer_id, f"🚨 {get_name(target_id)} набрал 3/3 варнов, но у бота нет прав на кик!")
                else:
