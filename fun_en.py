import os
import re
import json
import time
import random
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

GROUP_ID = int(os.environ.get("VK_GROUP_ID", "0").strip())

MENUS = {
    "main": "⚡ ПАНЕЛЬ УПРАВЛЕНИЯ ЧАТ-МЕНЕДЖЕРОМ\n━━━━━━━━━━━━━━━━━━\nВыбери нужный раздел кнопками ниже, чтобы увидеть полный список команд 👇",
    "roles": "🏷 РОЛИ И ПРИОРИТЕТЫ (1–100)\n━━━━━━━━━━━━━━━━━━\n▸ /createrole [1-99] [Имя] — создать роль\n▸ /delrole [Имя] — удалить роль\n▸ /giverole @юзер [Имя] — выдать роль\n▸ /takerole @юзер — снять роль\n▸ /roles — иерархия ролей беседы\n▸ /perms — права доступа к командам\n▸ /setperm [команда] [1-100] — настроить доступ",
    "mod": "🛡 МОДЕРАЦИЯ И ЗАЩИТА ЧАТА\n━━━━━━━━━━━━━━━━━━\n▸ /mute @юзер [мин] [причина] | /unmute\n▸ /warn @юзер [причина] | /unwarn\n▸ /kick | /ban @юзер [причина]\n▸ /cban | /cunban @юзер — ЧС беседы\n▸ /silence | /antilink | /antimat — защита\n▸ /all | /inactive | /rules | /welcome",
    "general": "👤 ОСНОВНОЕ И СТАТИСТИКА\n━━━━━━━━━━━━━━━━━━\n▸ /profile — паспорт, баланс, бизнес\n▸ /stats — карточка, роль и опыт в чате\n▸ /topchat — топ-10 активных болтунов\n▸ /chatinfo — настройки защиты чата\n▸ /nick [имя] — сменить ник в беседе\n▸ /marry @юзер | /divorce | /rep @юзер",
    "economy": "💰 ЭКОНОМИКА, ФЕРМЫ И БИЗНЕС\n━━━━━━━━━━━━━━━━━━\n▸ /bonus (1 час) | /work (10 мин)\n▸ /farm [buy / collect] — майнинг-фермы\n▸ /biz [buy / collect] — бизнес-империя\n▸ /bank [put / take] [сумма] — сейф\n▸ /pay @юзер [сумма] | /rob @юзер | /top",
    "games": "🎰 ИГРЫ, VIP И КЛАНЫ\n━━━━━━━━━━━━━━━━━━\n▸ /casino [ставка/all] | /roulette [цвет] [ставка]\n▸ /dice [1-6] [ставка] | /case | /duel @юзер [ставка]\n▸ /hug | /slap | /kiss | /kill @юзер\n▸ /buyvip (10,000) | /clan [create/join/deposit/info/leave]\n\n🔰 СОЗДАТЕЛЯМ СООБЩЕСТВА:\n▸ /givemoney | /takemoney | /givevip | /takevip"
}

def is_group_creator(vk, user_id):
    try:
        res = vk.groups.getMembers(group_id=GROUP_ID, filter="managers")
        for item in res["items"]:
            if item["id"] == user_id and item.get("role") in ["creator", "administrator"]:
                return True
    except Exception:
        return False
    return False

def get_menu_kb():
    kb = VkKeyboard(inline=True)
    kb.add_callback_button("🏷 Роли (1–100)", color=VkKeyboardColor.PRIMARY, payload={"menu": "roles"})
    kb.add_callback_button("🛡 Модерация", color=VkKeyboardColor.NEGATIVE, payload={"menu": "mod"})
    kb.add_line()
    kb.add_callback_button("👤 Основное", color=VkKeyboardColor.POSITIVE, payload={"menu": "general"})
    kb.add_callback_button("💰 Экономика", color=VkKeyboardColor.SECONDARY, payload={"menu": "economy"})
    kb.add_line()
    kb.add_callback_button("🎰 Игры / VIP / Кланы", color=VkKeyboardColor.SECONDARY, payload={"menu": "games"})
    return kb.get_keyboard()

def send_help_menu(vk, peer_id, category="main", event_id=None, user_id=None):
    text = MENUS.get(category, MENUS["main"])
    if event_id:
        vk.messages.sendMessageEventAnswer(event_id=event_id, user_id=user_id, peer_id=peer_id, event_data=json.dumps({"type": "show_snackbar", "text": "Раздел открыт ✅"}))
    vk.messages.send(peer_id=peer_id, message=text, keyboard=get_menu_kb(), random_id=get_random_id())

def send_msg(vk, peer_id, text):
    vk.messages.send(peer_id=peer_id, message=text, random_id=get_random_id())

def get_user(db, user_id):
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {"balance": 1000, "bank": 0, "last_bonus": 0, "last_work": 0, "last_rob": 0, "last_farm": 0, "last_biz": 0, "farms": 0, "biz": 0, "partner": None, "clan": None, "rep": 0, "vip": False}
    u = db["users"][uid]
    for k, v in [("biz", 0), ("last_biz", 0), ("farms", 0), ("last_farm", 0)]:
        if k not in u:
            u[k] = v
    return u

def get_name(vk, user_id):
    if user_id < 0:
        return "Бот"
    u = vk.users.get(user_ids=user_id).pop(0)
    return f"[id{user_id}|{u['first_name']} {u['last_name']}]"

def extract_target(msg_obj, args):
    if "reply_message" in msg_obj:
        return msg_obj["reply_message"]["from_id"]
    if args:
        match = re.search(r"\[id(\d+)\|", " ".join(args))
        if match:
            return int(match.group(1))
    return None

def handle_fun(vk, db, save_db, msg_obj):
    peer_id = msg_obj["peer_id"]
    from_id = msg_obj["from_id"]
    text = msg_obj.get("text", "").strip()
    if from_id < 0 or not text.startswith("/"):
        return
    parts = text[1:].split()
    if not parts:
        return
    cmd = parts.pop(0).lower()
    args = parts
    user = get_user(db, from_id)
    now = time.time()
    mult = 2 if user.get("vip") else 1

    if cmd in ["help", "commands", "menu"]:
        send_help_menu(vk, peer_id, "main")
    elif cmd in ["profile", "balance", "bal"]:
        vip_tag = "👑 VIP" if user.get("vip") else "Обычный"
        partner = get_name(vk, user["partner"]) if user.get("partner") else "Нет"
        clan = user.get("clan") or "Нет"
        send_msg(vk, peer_id, f"🪪 ПАСПОРТ ИГРОКА\n━━━━━━━━━━━━━━━━━━\n👤 {get_name(vk, from_id)} [{vip_tag}]\n💵 Наличные: {user['balance']} | 🏦 Банк: {user.get('bank', 0)}\n🖥 Ферм: {user['farms']} шт. | 🏢 Бизнес: {user['biz']} ур.\n🏰 Клан: {clan} | 💍 Брак: {partner}\n⭐ Репутация: {user.get('rep', 0)}")
    elif cmd == "bonus":
        if now - user["last_bonus"] < 3600:
            send_msg(vk, peer_id, f"⏳ До бонуса: {int((3600 - (now - user['last_bonus'])) // 60) + 1} мин.")
        else:
            rew = random.randint(500, 1200) * mult
            user["balance"] += rew
            user["last_bonus"] = now
            save_db(db)
            send_msg(vk, peer_id, f"🎁 Бонус: +{rew} монет! Баланс: {user['balance']}")
    elif cmd == "work":
        if now - user.get("last_work", 0) < 600:
            send_msg(vk, peer_id, f"⏳ Отдохни ещё {int((600 - (now - user['last_work'])) // 60) + 1} мин.")
        else:
            pay = random.randint(250, 600) * mult
            user["balance"] += pay
            user["last_work"] = now
            save_db(db)
            send_msg(vk, peer_id, f"💼 Заработано +{pay} монет! Баланс: {user['balance']}")
    elif cmd == "farm":
        sub = args.pop(0).lower() if args else ""
        farms = user["farms"]
        if sub == "buy":
            cost = 1500 * (farms + 1)
            if user["balance"] < cost:
                return send_msg(vk, peer_id, f"❌ Ферма №{farms+1} стоит {cost} монет.")
            user["balance"] -= cost
            user["farms"] += 1
            save_db(db)
            send_msg(vk, peer_id, f"🖥 Куплена ферма №{user['farms']}! Доход: {user['farms']*250} монет/час.")
        elif sub == "collect":
            if farms == 0:
                return send_msg(vk, peer_id, "❌ Нет ферм (/farm buy).")
            hrs = int((now - user["last_farm"]) // 3600)
            if hrs < 1:
                return send_msg(vk, peer_id, "⏳ Майнинг идёт, приходи через час!")
            profit = min(hrs, 24) * farms * 250 * mult
            user["balance"] += profit
            user["last_farm"] = now
            save_db(db)
            send_msg(vk, peer_id, f"⚡ Собрано: +{profit} монет! Баланс: {user['balance']}")
        else:
            send_msg(vk, peer_id, f"🖥 Ферм: {farms} шт. ({farms*250}/час)\nКоманды: /farm buy | /farm collect")
    elif cmd == "biz":
        sub = args.pop(0).lower() if args else ""
        b = user["biz"]
        names = ["Нет", "Ларёк с шаурмой", "Автомойка", "Ночной клуб", "IT-корпорация", "Нефтяная вышка"]
        if sub == "buy":
            if b >= 5:
                return send_msg(vk, peer_id, "🏢 У тебя максимальный уровень бизнеса!")
            cost = 4000 * (b + 1)
            if user["balance"] < cost:
                return send_msg(vk, peer_id, f"❌ Улучшение до «{names[b+1]}» стоит {cost} монет.")
            user["balance"] -= cost
            user["biz"] += 1
            save_db(db)
            send_msg(vk, peer_id, f"🏢 Куплен бизнес: «{names[user['biz']]}» (доход {user['biz']*600}/час)!")
        elif sub == "collect":
            if b == 0:
                return send_msg(vk, peer_id, "❌ Нет бизнеса (/biz buy).")
            hrs = int((now - user["last_biz"]) // 3600)
            if hrs < 1:
                return send_msg(vk, peer_id, "⏳ Выручка собирается раз в час!")
            profit = min(hrs, 24) * b * 600 * mult
            user["balance"] += profit
            user["last_biz"] = now
            save_db(db)
            send_msg(vk, peer_id, f"💵 Выручка с «{names[b]}»: +{profit} монет!")
        else:
            send_msg(vk, peer_id, f"🏢 Бизнес: {names[b]} ({b*600}/час)\nКоманды: /biz buy | /biz collect")
    elif cmd == "bank":
        if len(args) < 2:
            return send_msg(vk, peer_id, "❌ Пример: /bank put 500 или /bank take 500")
        act, amt_s = args.pop(0).lower(), args.pop(0)
        if not amt_s.isdigit():
            return send_msg(vk, peer_id, "❌ Укажи сумму числом.")
        amt = int(amt_s)
        if act == "put" and 0 < amt <= user["balance"]:
            user["balance"] -= amt
            user["bank"] = user.get("bank", 0) + amt
            save_db(db)
            send_msg(vk, peer_id, f"🏦 В банке: {user['bank']} монет.")
        elif act == "take" and 0 < amt <= user.get("bank", 0):
            user["bank"] -= amt
            user["balance"] += amt
            save_db(db)
            send_msg(vk, peer_id, f"💵 Наличные: {user['balance']} монет.")
        else:
            send_msg(vk, peer_id, "❌ Недостаточно средств.")
    elif cmd == "pay":
        tid = extract_target(msg_obj, args)
        amt = next((int(a) for a in args if a.isdigit()), None)
        if not tid or not amt or tid == from_id or tid < 0 or amt <= 0 or amt > user["balance"]:
            return send_msg(vk, peer_id, "❌ Пример: /pay @юзер 500")
        get_user(db, tid)["balance"] += amt
        user["balance"] -= amt
        save_db(db)
