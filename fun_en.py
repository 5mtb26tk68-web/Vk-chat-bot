import os
import re
import json
import time
import random
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

GROUP_ID = int(os.environ.get("VK_GROUP_ID", "0").strip())

MENUS = {
    "main": "⚡ ПАНЕЛЬ УПРАВЛЕНИЯ БОТОМ\n━━━━━━━━━━━━━━━━━━\nВыбери нужный раздел кнопками ниже, чтобы посмотреть список команд 👇",
    "general": "👤 ОСНОВНОЕ И ПРОФИЛЬ\n━━━━━━━━━━━━━━━━━━\n▸ /profile — твой паспорт и баланс\n▸ /stats — ранг и активность в чате\n▸ /nick [имя] — сменить ник в беседе\n▸ /rules — правила текущего чата\n▸ /staff — список модераторов\n▸ /rep @юзер — повысить репутацию",
    "economy": "💰 ЭКОНОМИКА И МАЙНИНГ\n━━━━━━━━━━━━━━━━━━\n▸ /bonus — награда раз в час\n▸ /work — подработка раз в 10 мин\n▸ /farm [buy / collect] — майнинг-фермы\n▸ /bank [put / take] [сумма] — сейф\n▸ /pay @юзер [сумма] — перевод монет\n▸ /rob @юзер — ограбить игрока\n▸ /top — топ-10 миллионеров",
    "games": "🎰 ИГРЫ, БРАКИ И РП\n━━━━━━━━━━━━━━━━━━\n▸ /casino [ставка / all] — слоты (x2 / x5)\n▸ /roulette [red/black/green] [ставка]\n▸ /dice [1-6] [ставка] — кубик (x5)\n▸ /case — открыть лутбокс (500 монет)\n▸ /duel @юзер [ставка] — дуэль на монеты\n▸ /marry @юзер | /divorce — свадьба\n▸ /hug | /slap | /kiss @юзер — РП-действия",
    "mod": "🛡 МОДЕРАЦИЯ (Ранги 1–7)\n━━━━━━━━━━━━━━━━━━\n▸ /mute @юзер [мин] | /unmute\n▸ /warn @юзер | /unwarn (2+ ранг)\n▸ /kick | /ban @юзер (3+ ранг)\n▸ /silence | /unsilence (4+ ранг)\n▸ /antilink | /all | /rules | /welcome\n▸ /setlvl @юзер [0-6] (6+ ранг)",
    "vip": "👑 VIP, КЛАНЫ И СОЗДАТЕЛИ\n━━━━━━━━━━━━━━━━━━\n▸ /buyvip — купить VIP (10,000 монет, x2 доход)\n▸ /clan create [имя] | /clan join [имя]\n▸ /clan leave | /clan info\n\n🔰 ТОЛЬКО СОЗДАТЕЛЯМ ГРУППЫ:\n▸ /givemoney @юзер [сумма] — выдать монеты\n▸ /takemoney @юзер [сумма] — забрать монеты\n▸ /givevip @юзер | /takevip @юзер — выдать/снять VIP"
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
    kb.add_callback_button("👤 Основное", color=VkKeyboardColor.POSITIVE, payload={"menu": "general"})
    kb.add_callback_button("💰 Экономика", color=VkKeyboardColor.PRIMARY, payload={"menu": "economy"})
    kb.add_line()
    kb.add_callback_button("🎰 Игры и РП", color=VkKeyboardColor.SECONDARY, payload={"menu": "games"})
    kb.add_callback_button("🛡 Модерация", color=VkKeyboardColor.SECONDARY, payload={"menu": "mod"})
    kb.add_line()
    kb.add_callback_button("👑 VIP и Кланы", color=VkKeyboardColor.NEGATIVE, payload={"menu": "vip"})
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
        db["users"][uid] = {"balance": 1000, "bank": 0, "last_bonus": 0, "last_work": 0, "last_rob": 0, "last_farm": 0, "farms": 0, "partner": None, "clan": None, "rep": 0, "vip": False}
    return db["users"][uid]

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
        send_msg(vk, peer_id, f"🪪 ПРОФИЛЬ ИГРОКА\n━━━━━━━━━━━━━━\n👤 {get_name(vk, from_id)} [{vip_tag}]\n💵 Наличные: {user['balance']} | 🏦 Банк: {user.get('bank', 0)}\n🖥 Майнинг-ферм: {user.get('farms', 0)} шт.\n🏰 Клан: {clan} | 💍 Брак: {partner}\n⭐ Репутация: {user.get('rep', 0)}")
    elif cmd == "bonus":
        if now - user["last_bonus"] < 3600:
            send_msg(vk, peer_id, f"⏳ Следующий бонус через {int((3600 - (now - user['last_bonus'])) // 60) + 1} мин.")
        else:
            rew = random.randint(500, 1200) * mult
            user["balance"] += rew
            user["last_bonus"] = now
            save_db(db)
            send_msg(vk, peer_id, f"🎁 Ты забрал бонус: +{rew} монет!\n💰 Баланс: {user['balance']}")
    elif cmd == "work":
        if now - user.get("last_work", 0) < 600:
            send_msg(vk, peer_id, f"⏳ Ты устал! Отдохни ещё {int((600 - (now - user['last_work'])) // 60) + 1} мин.")
        else:
            pay = random.randint(250, 600) * mult
            user["balance"] += pay
            user["last_work"] = now
            save_db(db)
            send_msg(vk, peer_id, f"💼 Отличная смена! Заработано +{pay} монет.\n💰 Баланс: {user['balance']}")
    elif cmd == "farm":
        sub = args.pop(0).lower() if args else ""
        farms = user.get("farms", 0)
        if sub == "buy":
            cost = 1500 * (farms + 1)
            if user["balance"] < cost:
                return send_msg(vk, peer_id, f"❌ Покупка фермы №{farms+1} стоит {cost} монет.")
            user["balance"] -= cost
            user["farms"] = farms + 1
            save_db(db)
            send_msg(vk, peer_id, f"🖥 Куплена майнинг-ферма №{user['farms']}! Доход: {user['farms']*250} монет/час.")
        elif sub == "collect":
            if farms == 0:
                return send_msg(vk, peer_id, "❌ У тебя нет ферм (/farm buy).")
            hrs = int((now - user.get("last_farm", 0)) // 3600)
            if hrs < 1:
                return send_msg(vk, peer_id, "⏳ Майнинг ещё идёт, приходи через час после прошлой сборки!")
            profit = min(hrs, 24) * farms * 250 * mult
            user["balance"] += profit
            user["last_farm"] = now
            save_db(db)
            send_msg(vk, peer_id, f"⚡ Собрано с ферм: +{profit} монет! Баланс: {user['balance']}")
        else:
            send_msg(vk, peer_id, f"🖥 Твои фермы: {farms} шт. ({farms*250} монет/час)\nКоманды: /farm buy | /farm collect")
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
            send_msg(vk, peer_id, f"🏦 В банке теперь: {user['bank']} монет.")
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
        send_msg(vk, peer_id, f"✅ Переведено {amt} монет -> {get_name(vk, tid)}")
    elif cmd == "rob":
        tid = extract_target(msg_obj, args)
        if not tid or tid == from_id or tid < 0 or now - user.get("last_rob", 0) < 1800:
            return send_msg(vk, peer_id, "❌ Укажи цель (/rob @юзер) или подожди откат 30 мин.")
        victim = get_user(db, tid)
        user["last_rob"] = now
        if victim["balance"] < 100:
            return send_msg(vk, peer_id, "🤷 У жертвы пусто в карманах (деньги в банке защищены).")
        if random.randint(1, 100) <= 40:
            loot = random.randint(50, min(600, victim["balance"] // 2))
            victim["balance"] -= loot
            user["balance"] += loot
            send_msg(vk, peer_id, f"🥷 Ограбление века! Украдено {loot} монет у {get_name(vk, tid)}!")
        else:
            fine = min(250, user["balance"])
            user["balance"] -= fine
            send_msg(vk, peer_id, f"🚓 Тебя поймала полиция! Штраф {fine} монет.")
        save_db(db)
    elif cmd == "top":
        top_u = sorted(db["users"].items(), key=lambda x: x["balance"] + x.get("bank", 0), reverse=True)[:10]
        lines = ["🏆 ТОП-10 МИЛЛИОНЕРОВ:", "━━━━━━━━━━━━━━"] + [f"{i}. {get_name(vk, int(uid))} — {u['balance'] + u.get('bank', 0)} монет" for i, (uid, u) in enumerate(top_u, 1)]
