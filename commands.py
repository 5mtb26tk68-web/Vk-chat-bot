import re
import time
import random
from vk_api.utils import get_random_id

def get_user(db, user_id):
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {"balance": 1000, "last_bonus": 0}
    return db["users"][uid]

def get_chat_member(db, peer_id, user_id):
    pid, uid = str(peer_id), str(user_id)
    if pid not in db["chats"]:
        db["chats"][pid] = {}
    if uid not in db["chats"][pid]:
        db["chats"][pid][uid] = {"warns": 0, "mute_until": 0}
    return db["chats"][pid][uid]

def send_msg(vk, peer_id, text):
    vk.messages.send(peer_id=peer_id, message=text, random_id=get_random_id())

def is_admin(vk, peer_id, user_id):
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

def get_name(vk, user_id):
    if user_id < 0:
        return "Бот"
    users = vk.users.get(user_ids=user_id)
    u = users.pop(0)
    return f"[id{user_id}|{u['first_name']} {u['last_name']}]"

def handle_message(vk, db, save_db, msg_obj):
    peer_id = msg_obj["peer_id"]
    from_id = msg_obj["from_id"]
    text = msg_obj.get("text", "").strip()

    if from_id < 0:
        return

    is_chat = peer_id > 2000000000

    if is_chat:
        member_data = get_chat_member(db, peer_id, from_id)
        if member_data["mute_until"] > time.time():
            if not is_admin(vk, peer_id, from_id):
                try:
                    vk.messages.delete(
                        peer_id=peer_id,
                        cmids=msg_obj["conversation_message_id"],
                        delete_for_all=1
                    )
                except Exception:
                    pass
            return

    if not text:
        return

    parts = text.split()
    cmd = parts.pop(0).lower().lstrip("/!.")
    args = parts
    user_data = get_user(db, from_id)

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
        send_msg(vk, peer_id, help_text)

    elif cmd in ["баланс", "б", "профиль"]:
        warns_info = ""
        if is_chat:
            w = get_chat_member(db, peer_id, from_id)["warns"]
            warns_info = f"\n⚠️ Варнов в чате: {w}/3"
        send_msg(vk, peer_id, f"👤 {get_name(vk, from_id)}\n💰 Баланс: {user_data['balance']} монет{warns_info}")

    elif cmd == "бонус":
        now = time.time()
        if now - user_data["last_bonus"] < 3600:
            left = int((3600 - (now - user_data["last_bonus"])) // 60) + 1
            send_msg(vk, peer_id, f"⏳ Бонус можно забрать через {left} мин.")
        else:
            reward = random.randint(250, 750)
            user_data["balance"] += reward
            user_data["last_bonus"] = now
            save_db(db)
            send_msg(vk, peer_id, f"🎁 {get_name(vk, from_id)}, вы получили {reward} монет! Баланс: {user_data['balance']}")

    elif cmd in ["казино", "каз"]:
        if not args:
            send_msg(vk, peer_id, "❌ Укажите ставку. Пример: Казино 500 или Казино все")
            return
        bet_arg = args.pop(0)
        if bet_arg.lower() in ["все", "всё", "all"]:
            bet = user_data["balance"]
        elif bet_arg.isdigit():
            bet = int(bet_arg)
        else:
            send_msg(vk, peer_id, "❌ Неверная сумма ставки.")
            return

        if bet <= 0 or bet > user_data["balance"]:
            send_msg(vk, peer_id, f"❌ Недостаточно средств! Ваш баланс: {user_data['balance']}")
            return

        chance = random.randint(1, 100)
        if chance <= 45:
            user_data["balance"] += bet
            send_msg(vk, peer_id, f"🎰 {get_name(vk, from_id)} выиграл {bet} монет! (x2)\n💰 Баланс: {user_data['balance']}")
        elif chance <= 50:
            win = bet * 4
            user_data["balance"] += win
            send_msg(vk, peer_id, f"🔥 ДЖЕКПОТ! {get_name(vk, from_id)} сорвал куш +{win} монет! (x5)\n💰 Баланс: {user_data['balance']}")
        else:
            user_data["balance"] -= bet
            send_msg(vk, peer_id, f"📉 {get_name(vk, from_id)} проиграл {bet} монет...\n💰 Баланс: {user_data['balance']}")
        save_db(db)

    elif cmd in ["перевод", "перевести", "дать"]:
        target_id = extract_target(msg_obj, args)
        amount = next((int(a) for a in args if a.isdigit()), None)
        if not target_id or not amount:
            send_msg(vk, peer_id, "❌ Пример: Перевод @пользователь 500")
            return
        if target_id == from_id or target_id < 0:
            send_msg(vk, peer_id, "❌ Нельзя переводить самому себе или боту.")
            return
        if amount <= 0 or amount > user_data["balance"]:
            send_msg(vk, peer_id, f"❌ Недостаточно монет. Ваш баланс: {user_data['balance']}")
            return

        target_data = get_user(db, target_id)
        user_data["balance"] -= amount
        target_data["balance"] += amount
        save_db(db)
        send_msg(vk, peer_id, f"✅ {get_name(vk, from_id)} перевел {amount} монет пользователю {get_name(target_id)}!")

    elif cmd in ["кик", "бан", "мут", "размут", "варн", "снятьварны"]:
        if not is_chat:
            send_msg(vk, peer_id, "❌ Команда работает только в беседах.")
            return
        if not is_admin(vk, peer_id, from_id):
            send_msg(vk, peer_id, "⛔ У вас нет прав администратора беседы.")
            return
        target_id = extract_target(msg_obj, args)
        if not target_id or target_id == from_id or is_admin(vk, peer_id, target_id):
            send_msg(vk, peer_id, "❌ Укажите обычного участника через @ или ответ на сообщение.")
            return

        chat_id = peer_id - 2000000000
        target_member = get_chat_member(db, peer_id, target_id)

        if cmd in ["кик", "бан"]:
            try:
                vk.messages.removeChatUser(chat_id=chat_id, member_id=target_id)
                send_msg(vk, peer_id, f"🔨 {get_name(vk, from_id)} исключил {get_name(vk, target_id)} из беседы.")
            except Exception as e:
                send_msg(vk, peer_id, f"❌ Ошибка (проверьте права админа у бота): {e}")
        elif cmd == "мут":
            minutes = next((int(a) for a in args if a.isdigit()), 10)
            target_member["mute_until"] = time.time() + (minutes * 60)
            save_db(db)
            send_msg(vk, peer_id, f"🔇 {get_name(vk, target_id)} получил мут на {minutes} мин.")
        elif cmd == "размут":
            target_member["mute_until"] = 0
            save_db(db)
            send_msg(vk, peer_id, f"🔊 С {get_name(vk, target_id)} снят мут.")
        elif cmd == "варн":
            target_member["warns"] += 1
            w = target_member["warns"]
            if w >= 3:
                target_member["warns"] = 0
                save_db(db)
                try:
                    vk.messages.removeChatUser(chat_id=chat_id, member_id=target_id)
                    send_msg(vk, peer_id, f"🚨 {get_name(vk, target_id)} получил 3/3 варнов и исключен!")
                except Exception:
                    send_msg(vk, peer_id, f"🚨 {get_name(vk, target_id)} набрал 3/3 варнов, но у бота нет прав на кик!")
            else:
                save_db(db)
                send_msg(vk, peer_id, f"⚠️ {get_name(vk, target_id)} получил предупреждение ({w}/3).")
        elif cmd == "снятьварны":
            target_member["warns"] = 0
            save_db(db)
            send_msg(vk, peer_id, f"🛡 Варны пользователя {get_name(vk, target_id)} обнулены.")
