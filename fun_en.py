import os, re, json, time, random
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

GROUP_ID = int(os.environ.get("VK_GROUP_ID", "0").strip())

MENUS = {
    "main": "✦ Astra • Чат-менеджер ✦\n━━━━━━━━━━━━━━━━━━\nВыбери нужный раздел кнопками ниже 👇",
    "roles": "🏷 Astra • Роли и приоритеты (1–100)\n━━━━━━━━━━━━━━━━━━\n▸ /createrole [1-99] [Имя] | /delrole [Имя]\n▸ /giverole @юзер [Имя] | /takerole @юзер\n▸ /roles — иерархия | /perms — права | /setperm [ком] [1-100]",
    "mod": "🛡 Astra • Модерация и защита\n━━━━━━━━━━━━━━━━━━\n▸ /mute @юзер [мин] [причина] | /unmute\n▸ /warn @юзер [причина] | /unwarn\n▸ /kick | /ban @юзер [причина] | /cban | /cunban\n▸ /silence | /antilink | /antimat | /all | /inactive | /rules | /welcome",
    "general": "👤 Astra • Основное и статистика\n━━━━━━━━━━━━━━━━━━\n▸ /profile | /stats | /topchat | /chatinfo\n▸ /nick [имя] | /marry @юзер | /divorce | /rep @юзер",
    "economy": "💰 Astra • Экономика и бизнес\n━━━━━━━━━━━━━━━━━━\n▸ /bonus | /work | /farm [buy/collect] | /biz [buy/collect]\n▸ /bank [put/take] [сумма] | /pay @юзер [сумма] | /rob @юзер | /top\n▸ /promo [код] — активировать промокод",
    "games": "🎰 Astra • Игры, VIP и Кланы\n━━━━━━━━━━━━━━━━━━\n▸ /casino [ставка/all] | /roulette [цвет] [ставка] | /dice [1-6] [ставка]\n▸ /case | /duel @юзер [ставка] | /hug | /slap | /kiss | /kill @юзер\n▸ /buyvip | /clan [create/join/deposit/info/leave]\n\n🔰 Разработчикам сообщества:\n▸ /givemoney | /takemoney | /givevip | /takevip\n▸ /createpromo [код] [сумма/vip] [кол-во] | /delpromo | /promos"
}

def is_creator(vk, uid):
    try:
        return any(i["id"] == uid and i.get("role") in ["creator", "administrator"] for i in vk.groups.getMembers(group_id=GROUP_ID, filter="managers")["items"])
    except Exception:
        return False

def get_kb():
    kb = VkKeyboard(inline=True)
    kb.add_callback_button("🏷 Роли (1–100)", color=VkKeyboardColor.PRIMARY, payload={"menu": "roles"})
    kb.add_callback_button("🛡 Модерация", color=VkKeyboardColor.NEGATIVE, payload={"menu": "mod"})
    kb.add_line()
    kb.add_callback_button("👤 Основное", color=VkKeyboardColor.POSITIVE, payload={"menu": "general"})
    kb.add_callback_button("💰 Экономика", color=VkKeyboardColor.SECONDARY, payload={"menu": "economy"})
    kb.add_line()
    kb.add_callback_button("🎰 Игры / VIP / Кланы", color=VkKeyboardColor.SECONDARY, payload={"menu": "games"})
    return kb.get_keyboard()

def send_help_menu(vk, peer_id, cat="main", event_id=None, user_id=None):
    if event_id:
        vk.messages.sendMessageEventAnswer(event_id=event_id, user_id=user_id, peer_id=peer_id, event_data=json.dumps({"type": "show_snackbar", "text": "Раздел открыт ✅"}))
    vk.messages.send(peer_id=peer_id, message=MENUS.get(cat, MENUS["main"]), keyboard=get_kb(), random_id=get_random_id())

def send_msg(vk, peer_id, text):
    vk.messages.send(peer_id=peer_id, message=text, random_id=get_random_id())

def get_user(db, uid):
    s = str(uid)
    if s not in db["users"]:
        db["users"][s] = {"balance": 1000, "bank": 0, "last_bonus": 0, "last_work": 0, "last_rob": 0, "last_farm": 0, "last_biz": 0, "farms": 0, "biz": 0, "partner": None, "clan": None, "rep": 0, "vip": False, "used_promos": []}
    for k, v in [("biz", 0), ("last_biz", 0), ("farms", 0), ("last_farm", 0), ("used_promos", [])]:
        db["users"][s].setdefault(k, v)
    return db["users"][s]

def get_name(vk, uid):
    if uid < 0: return "Astra"
    u = vk.users.get(user_ids=uid).pop(0)
    return f"[id{uid}|{u['first_name']} {u['last_name']}]"

def get_target(msg, args):
    if "reply_message" in msg: return msg["reply_message"]["from_id"]
    m = re.search(r"\[id(\d+)\|", " ".join(args))
    return int(m.group(1)) if m else None

def handle_fun(vk, db, save_db, msg):
    peer_id, from_id, text = msg["peer_id"], msg["from_id"], msg.get("text", "").strip()
    if from_id < 0 or not text.startswith("/"): return
    db.setdefault("promos", {})
    parts = text[1:].split()
    if not parts: return
    cmd, args = parts.pop(0).lower(), parts
    u, now = get_user(db, from_id), time.time()
    mult = 2 if u.get("vip") else 1

    if cmd in ["help", "commands", "menu"]: send_help_menu(vk, peer_id, "main")
    elif cmd in ["profile", "balance", "bal"]:
        v = "👑 VIP" if u.get("vip") else "Обычный"
        p = get_name(vk, u["partner"]) if u.get("partner") else "Нет"
        send_msg(vk, peer_id, f"🪪 ПАСПОРТ ИГРОКА • Astra\n━━━━━━━━━━━━━━━━━━\n👤 {get_name(vk, from_id)} [{v}]\n💵 Наличные: {u['balance']} | 🏦 Банк: {u.get('bank', 0)}\n🖥 Ферм: {u['farms']} шт. | 🏢 Бизнес: {u['biz']} ур.\n🏰 Клан: {u.get('clan') or 'Нет'} | 💍 Брак: {p}\n⭐ Репутация: {u.get('rep', 0)}")
    elif cmd == "bonus":
        if now - u["last_bonus"] < 3600: return send_msg(vk, peer_id, f"⏳ До бонуса: {int((3600 - (now - u['last_bonus'])) // 60) + 1} мин.")
        rew = random.randint(500, 1200) * mult
        u["balance"] += rew; u["last_bonus"] = now; save_db(db)
        send_msg(vk, peer_id, f"🎁 Бонус: +{rew} монет! Баланс: {u['balance']}")
    elif cmd == "work":
        if now - u.get("last_work", 0) < 600: return send_msg(vk, peer_id, f"⏳ Отдохни {int((600 - (now - u['last_work'])) // 60) + 1} мин.")
        pay = random.randint(250, 600) * mult
        u["balance"] += pay; u["last_work"] = now; save_db(db)
        send_msg(vk, peer_id, f"💼 Заработано +{pay} монет! Баланс: {u['balance']}")
    elif cmd == "promo":
        if not args: return send_msg(vk, peer_id, "❌ Пример: /promo ASTRA2026")
        code = args.pop(0).upper()
        if code not in db["promos"] or code in u["used_promos"]: return send_msg(vk, peer_id, "❌ Промокод недействителен или уже использован.")
        pd = db["promos"][code]; u["used_promos"].append(code); pd["uses"] -= 1
        if pd["uses"] <= 0: del db["promos"][code]
        if pd["reward"] == "vip": u["vip"] = True; res_t = "👑 VIP-статус!"
        else: u["balance"] += pd["reward"]; res_t = f"+{pd['reward']} монет!"
        save_db(db); send_msg(vk, peer_id, f"🎉 Промокод «{code}» активирован! Получено: {res_t}")
    elif cmd in ["farm", "biz"]:
        sub = args.pop(0).lower() if args else ""
        is_f = (cmd == "farm")
        lvl, l_key, base_c, rate = (u["farms"], "last_farm", 1500, 250) if is_f else (u["biz"], "last_biz", 4000, 600)
        if sub == "buy":
            if not is_f and lvl >= 5: return send_msg(vk, peer_id, "🏢 Максимальный уровень бизнеса!")
            cost = base_c * (lvl + 1)
            if u["balance"] < cost: return send_msg(vk, peer_id, f"❌ Нужно {cost} монет.")
            u["balance"] -= cost; u["farms" if is_f else "biz"] += 1; save_db(db)
            send_msg(vk, peer_id, f"✅ Куплено! Новый уровень: {lvl + 1} (доход {(lvl + 1) * rate}/час).")
        elif sub == "collect":
            hrs = int((now - u[l_key]) // 3600)
            if lvl == 0 or hrs < 1: return send_msg(vk, peer_id, "⏳ Нечего собирать (доход капает раз в час).")
            prof = min(hrs, 24) * lvl * rate * mult
            u["balance"] += prof; u[l_key] = now; save_db(db)
            send_msg(vk, peer_id, f"⚡ Собрано: +{prof} монет! Баланс: {u['balance']}")
        else: send_msg(vk, peer_id, f"📊 Уровень: {lvl} ({lvl * rate}/час). Команды: /{cmd} buy | /{cmd} collect")
    elif cmd == "bank":
        if len(args) < 2: return send_msg(vk, peer_id, "❌ Пример: /bank put 500 или /bank take 500")
        act, amt_s = args.pop(0).lower(), args.pop(0)
        amt = int(amt_s) if amt_s.isdigit() else 0
        if act == "put" and 0 < amt <= u["balance"]: u["balance"] -= amt; u["bank"] = u.get("bank", 0) + amt; save_db(db); send_msg(vk, peer_id, f"🏦 В банке: {u['bank']}")
        elif act == "take" and 0 < amt <= u.get("bank", 0): u["bank"] -= amt; u["balance"] += amt; save_db(db); send_msg(vk, peer_id, f"💵 Наличные: {u['balance']}")
        else: send_msg(vk, peer_id, "❌ Недостаточно средств.")
    elif cmd == "pay":
        tid, amt = get_target(msg, args), next((int(a) for a in args if a.isdigit()), 0)
        if not tid or tid == from_id or tid < 0 or amt <= 0 or amt > u["balance"]: return send_msg(vk, peer_id, "❌ Пример: /pay @юзер 500")
        get_user(db, tid)["balance"] += amt; u["balance"] -= amt; save_db(db)
        send_msg(vk, peer_id, f"✅ Переведено {amt} монет -> {get_name(vk, tid)}")
    elif cmd == "rob":
        tid = get_target(msg, args)
        if not tid or tid == from_id or tid < 0 or now - u.get("last_rob", 0) < 1800: return send_msg(vk, peer_id, "❌ Укажи цель (/rob @юзер) или жди 30 мин.")
        vic = get_user(db, tid); u["last_rob"] = now
        if vic["balance"] < 100: return send_msg(vk, peer_id, "🤷 У жертвы пусто в карманах.")
        if random.randint(1, 100) <= 40:
            loot = random.randint(50, min(600, vic["balance"] // 2)); vic["balance"] -= loot; u["balance"] += loot
            send_msg(vk, peer_id, f"🥷 Украдено {loot} монет у {get_name(vk, tid)}!")
        else:
            fine = min(250, u["balance"]); u["balance"] -= fine; send_msg(vk, peer_id, f"🚓 Полиция поймала! Штраф {fine} монет.")
        save_db(db)
    elif cmd == "top":
        top_u = sorted(db["users"].items(), key=lambda x: list(x).pop()["balance"] + list(x).pop().get("bank", 0), reverse=True)[:10]
        send_msg(vk, peer_id, "🏆 ТОП-10 МИЛЛИОНЕРОВ • Astra:\n━━━━━━━━━━━━━━━━━━\n" + "\n".join(f"{i}. {get_name(vk, int(uid))} — {ud['balance'] + ud.get('bank', 0)}" for i, (uid, ud) in enumerate(top_u, 1)))
    elif cmd == "casino":
        if not args: return send_msg(vk, peer_id, "❌ Пример: /casino 300 или /casino all")
        b = args.pop(0).lower()
        bet = u["balance"] if b == "all" else (int(b) if b.isdigit() else 0)
        if bet <= 0 or bet > u["balance"]: return send_msg(vk, peer_id, "❌ Недостаточно монет!")
        r = random.randint(1, 100)
        if r <= 45: u["balance"] += bet; send_msg(vk, peer_id, f"🎰 Победа +{bet} (x2)! Баланс: {u['balance']}")
