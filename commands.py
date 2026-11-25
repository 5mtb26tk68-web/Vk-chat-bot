import re
import time
import random
from vk_api.utils import get_random_id

def get_user(db, user_id):
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {"balance": 1000, "bank": 0, "last_bonus": 0, "last_work": 0, "last_rob": 0, "partner": None, "rep": 0}
    u = db["users"][uid]
    for k, v in [("bank", 0), ("last_work", 0), ("last_rob", 0), ("partner", None), ("rep", 0)]:
        if k not in u:
            u[k] = v
    return u

def get_chat_member(db, peer_id, user_id):
    pid, uid = str(peer_id), str(user_id)
    if pid not in db["chats"]:
        db["chats"][pid] = {}
    if uid not in db["chats"][pid]:
        db["chats"][pid][uid] = {"warns": 0, "mute_until": 0, "msgs": 0}
    if "msgs" not in db["chats"][pid][uid]:
        db["chats"][pid][uid]["msgs"] = 0
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
    u = vk.users.get(user_ids=user_id).pop(0)
    return f"[id{user_id}|{u['first_name']} {u['last_name']}]"

def handle_message(vk, db, save_db, msg_obj):
    peer_id = msg_obj["peer_id"]
    from_id = msg_obj["from_id"]
    text = msg_obj.get("text", "").strip()

    if from_id < 0:
        return

    is_chat = peer_id > 2000000000
    user_data = get_user(db, from_id)

    if is_chat:
        member_data = get_chat_member(db, peer_id, from_id)
        member_data["msgs"] += 1
        if member_data["mute_until"] > time.time():
            if not is_admin(vk, peer_id, from_id):
                try:
                    vk.messages.delete(peer_id=peer_id, cmids=msg_obj["conversation_message_id"], delete_for_all=1)
                except Exception:
                    pass
            return

    # СТРОГО ЧЕРЕЗ СЛЭШ /
    if not text.startswith("/"):
        return

    parts = text[1:].split()
    if not parts:
        return
    cmd = parts.pop(0).lower()
    args = parts

    # --- ПОМОЩЬ ---
    if cmd in ["помощь", "help", "команды"]:
        help_text = (
            "💰 ЭКОНОМИКА И РАБОТА:\n"
            "/профиль — статистика и баланс\n"
            "/бонус — монеты раз в час\n"
            "/работа — подработка раз в 10 мин\n"
            "/банк [положить/снять] [сумма]\n"
            "/перевод [@юзер] [сумма]\n"
            "/ограбить [@юзер] — украсть деньги\n"
            "/топ — топ-10 богачей\n\n"
            "🎰 ИГРЫ И ФАН:\n"
            "/казино [ставка/все] — слоты\n"
            "/рулетка [красное/черное/зеленое] [ставка]\n"
            "/кости [1-6] [ставка]\n"
            "/шар [вопрос] — шар судьбы\n"
            "/брак [@юзер] | /развод — семья\n"
            "/реп [@юзер] — повысить репутацию\n"
            "/обнять | /ударить | /поцеловать [@юзер]\n\n"
            "🛡 ЧАТ-МЕНЕДЖЕР (админам):\n"
            "/кик | /бан [@юзер]\n"
            "/мут [@юзер] [мин] | /размут [@юзер]\n"
            "/варн [@юзер] | /снятьварны [@юзер]\n"
            "/созвать — отметить всех в чате"
        )
        send_msg(vk, peer_id, help_text)

    # --- ПРОФИЛЬ И ЭКОНОМИКА ---
    elif cmd in ["профиль", "баланс", "б"]:
        partner = get_name(vk, user_data["partner"]) if user_data["partner"] else "Нет"
        chat_info = ""
        if is_chat:
            m = get_chat_member(db, peer_id, from_id)
            chat_info = f"\n💬 Сообщений: {m['msgs']} | ⚠️ Варнов: {m['warns']}/3"
        send_msg(vk, peer_id, f"👤 {get_name(vk, from_id)}\n💵 Наличные: {user_data['balance']} монет\n🏦 В банке: {user_data['bank']} монет\n⭐ Репутация: {user_data['rep']}\n💍 Брак: {partner}{chat_info}")

    elif cmd == "бонус":
        now = time.time()
        if now - user_data["last_bonus"] < 3600:
            send_msg(vk, peer_id, f"⏳ Бонус через {int((3600 - (now - user_data['last_bonus'])) // 60) + 1} мин.")
        else:
            rew = random.randint(500, 1500)
            user_data["balance"] += rew
            user_data["last_bonus"] = now
            save_db(db)
            send_msg(vk, peer_id, f"🎁 {get_name(vk, from_id)} забрал бонус +{rew} монет!")

    elif cmd == "работа":
        now = time.time()
        if now - user_data["last_work"] < 600:
            send_msg(vk, peer_id, f"⏳ Вы устали! Отдохните еще {int((600 - (now - user_data['last_work'])) // 60) + 1} мин.")
        else:
            jobs = ["программистом", "курьером", "таксистом", "бариста", "охранником"]
            pay = random.randint(200, 600)
            user_data["balance"] += pay
            user_data["last_work"] = now
            save_db(db)
            send_msg(vk, peer_id, f"💼 {get_name(vk, from_id)} поработал {random.choice(jobs)} и заработал {pay} монет!")

    elif cmd == "банк":
        if len(args) < 2 or not args[1].isdigit():
            send_msg(vk, peer_id, "❌ Пример: /банк положить 500 или /банк снять 500")
            return
        act, amt = args.lower(), int(args[1])
        if act == "положить" and 0 < amt <= user_data["balance"]:
            user_data["balance"] -= amt
            user_data["bank"] += amt
            save_db(db)
            send_msg(vk, peer_id, f"🏦 Внесено в банк: {amt} монет. В банке: {user_data['bank']}")
        elif act == "снять" and 0 < amt <= user_data["bank"]:
            user_data["bank"] -= amt
            user_data["balance"] += amt
            save_db(db)
            send_msg(vk, peer_id, f"💵 Снято с банка: {amt} монет. Наличные: {user_data['balance']}")
        else:
            send_msg(vk, peer_id, "❌ Недостаточно средств для операции.")

    elif cmd == "перевод":
        tid = extract_target(msg_obj, args)
        amt = next((int(a) for a in args if a.isdigit()), None)
        if not tid or not amt or tid == from_id or tid < 0 or amt <= 0 or amt > user_data["balance"]:
            send_msg(vk, peer_id, "❌ Пример: /перевод @юзер 500 (проверьте баланс)")
            return
        get_user(db, tid)["balance"] += amt
        user_data["balance"] -= amt
        save_db(db)
        send_msg(vk, peer_id, f"✅ {get_name(vk, from_id)} перевел {amt} монет -> {get_name(tid)}")

    elif cmd == "ограбить":
        tid = extract_target(msg_obj, args)
        if not tid or tid == from_id or tid < 0:
            send_msg(vk, peer_id, "❌ Укажите цель: /ограбить @юзер")
            return
        now = time.time()
        if now - user_data["last_rob"] < 1800:
            send_msg(vk, peer_id, f"⏳ Полиция начеку! Ждите {int((1800 - (now - user_data['last_rob'])) // 60) + 1} мин.")
            return
        target = get_user(db, tid)
        user_data["last_rob"] = now
        if target["balance"] < 100:
            send_msg(vk, peer_id, "🤷 У жертвы в карманах пусто (деньги в банке грабить нельзя).")
            return
        if random.randint(1, 100) <= 40:
            stolen = random.randint(50, min(500, target["balance"] // 2))
            target["balance"] -= stolen
            user_data["balance"] += stolen
            send_msg(vk, peer_id, f"🥷 Успех! Вы украли {stolen} монет у {get_name(tid)}!")
        else:
            fine = min(200, user_data["balance"])
            user_data["balance"] -= fine
            send_msg(vk, peer_id, f"🚓 Вас поймали! Штраф {fine} монет.")
        save_db(db)

    elif cmd == "топ":
        sorted_u = sorted(db["users"].items(), key=lambda x: x[1]["balance"] + x[1].get("bank", 0), reverse=True)[:10]
        lines = ["🏆 ТОП-10 БОГАЧЕЙ:"]
        for i, (uid, u) in enumerate(sorted_u, 1):
            lines.append(f"{i}. {get_name(vk, int(uid))} — {u['balance'] + u.get('bank', 0)} монет")
        send_msg(vk, peer_id, "\n".join(lines))

    # --- ИГРЫ ---
    elif cmd in ["казино", "каз"]:
        if not args:
            send_msg(vk, peer_id, "❌ Пример: /казино 500 или /казино все")
            return
        b_arg = args.pop(0).lower()
        bet = user_data["balance"] if b_arg in ["все", "всё", "all"] else (int(b_arg) if b_arg.isdigit() else 0)
        if bet <= 0 or bet > user_data["balance"]:
            send_msg(vk, peer_id, f"❌ Неверная ставка. Баланс: {user_data['balance']}")
            return
        ch = random.randint(1, 100)
        if ch <= 45:
            user_data["balance"] += bet
            send_msg(vk, peer_id, f"🎰 Победа +{bet} монет (x2)! Баланс: {user_data['balance']}")
        elif ch <= 50:
            user_data["balance"] += bet * 4
            send_msg(vk, peer_id, f"🔥 ДЖЕКПОТ +{bet*4} монет (x5)! Баланс: {user_data['balance']}")
        else:
            user_data["balance"] -= bet
            send_msg(vk, peer_id, f"📉 Проигрыш -{bet} монет. Баланс: {user_data['balance']}")
        save_db(db)

    elif cmd == "рулетка":
        if len(args) < 2 or not args[1].isdigit():
            send_msg(vk, peer_id, "❌ Пример: /рулетка красное 500 (красное / черное / зеленое)")
            return
        color, bet = args.lower(), int(args[1])
        if color not in ["красное", "черное", "чёрное", "зеленое", "зелёное"] or bet <= 0 or bet > user_data["balance"]:
            send_msg(vk, peer_id, "❌ Проверьте цвет и ставку.")
            return
        color = color.replace("ё", "е")
        roll = random.choices(["красное", "черное", "зеленое"], weights=[48, 48, 4]).pop(0)
        if color == roll:
            mult = 14 if roll == "зеленое" else 2
            win = bet * (mult - 1)
            user_data["balance"] += win
