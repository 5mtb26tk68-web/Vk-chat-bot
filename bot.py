import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json, time, os, re, random, threading, traceback
from datetime import datetime

# ═══════════ КОНФИГ ═══════════
TOKEN = os.environ.get("VK_TOKEN", "")
DEVELOPERS = [int(x) for x in os.environ.get("DEVELOPERS", "734176092").split(",") if x]
PREFIX = "!"

if not TOKEN:
    print("❌ VK_TOKEN не установлен в Render Environment!")
    raise SystemExit(1)

print(f"✅ Токен загружен | Админы: {DEVELOPERS}")

# ═══════════ БД ═══════════
DB_FILE = "db.json"
def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "promo": {}, "clans": {}}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(DB, f, ensure_ascii=False, indent=2)

DB = load_db()

def get_user(uid):
    s = str(uid)
    if s not in DB["users"]:
        DB["users"][s] = {
            "balance": 1000, "bank": 0, "xp": 0, "level": 0,
            "warns": 0, "reputation": 0, "business": None,
            "business_time": 0, "work_time": 0, "bonus_time": 0,
            "deposit": 0, "deposit_time": 0,
            "car": None, "house": None, "yacht": None, "phone": None,
            "pet": None, "pet_hunger": 100, "pet_happiness": 100,
            "farm": None, "farm_time": 0,
            "married_to": 0, "clan_id": 0,
            "inventory": {}, "achievements": [],
            "muted_until": 0, "messages_count": 0,
            "games_won": 0, "games_lost": 0,
            "title": None, "daily_time": 0, "spin_time": 0,
            "friends": [], "nickname": None, "bio": None,
            "last_seen": 0, "register_time": int(time.time())
        }
        save_db()
    return DB["users"][s]

def extract_user(text):
    m = re.search(r"(?:@id|id|vk\.com/)(\d+)", str(text))
    return int(m.group(1)) if m else None

def is_admin(uid):
    return uid in DEVELOPERS

def fmt(n):
    try: return f"{int(n):,}".replace(",", " ")
    except: return str(n)

def get_name(uid):
    try:
        r = vk.users.get(user_ids=uid)[0]
        return f"{r['first_name']} {r['last_name']}"
    except: return "Пользователь"

# ═══════════ ДАННЫЕ ═══════════
BUSINESSES = {
    "ларёк": {"price": 10000, "income": 800},
    "кафе": {"price": 50000, "income": 4500},
    "магазин": {"price": 200000, "income": 20000},
    "ресторан": {"price": 750000, "income": 80000},
    "завод": {"price": 2500000, "income": 280000},
    "банк": {"price": 10000000, "income": 1200000},
    "нефтянка": {"price": 50000000, "income": 6500000},
    "космодром": {"price": 200000000, "income": 30000000},
}
CARS = {"велик": 5000, "самокат": 15000, "жигуль": 80000, "тойота": 500000,
        "бмв": 2000000, "мерседес": 5000000, "ламборгини": 25000000, "бугатти": 100000000}
HOUSES = {"палатка": 10000, "квартира": 250000, "дом": 1500000,
          "особняк": 15000000, "замок": 100000000, "остров": 500000000}
YACHTS = {"лодка": 50000, "катер": 500000, "яхта": 10000000, "мега-яхта": 100000000}
PHONES = {"нокия": 5000, "xiaomi": 25000, "iphone": 150000, "samsung": 300000}
PETS = {"кот": 50000, "собака": 75000, "попугай": 30000, "дракон": 5000000}
FARMS = {"огород": 100000, "теплица": 500000, "ранчо": 2000000}
CASES = {
    "деревянный": {"price": 1000, "min": 500, "max": 5000},
    "железный": {"price": 10000, "min": 5000, "max": 50000},
    "золотой": {"price": 100000, "min": 50000, "max": 500000},
    "платиновый": {"price": 1000000, "min": 500000, "max": 5000000},
    "алмазный": {"price": 10000000, "min": 5000000, "max": 50000000},
}
MINE_ITEMS = {"камень": (10, 100), "уголь": (50, 300), "железо": (200, 1000),
              "серебро": (1000, 5000), "золото": (5000, 25000), "алмаз": (25000, 150000)}
FISH_ITEMS = {"карась": (5, 50), "окунь": (20, 150), "щука": (100, 800),
              "сом": (500, 3000), "осётр": (3000, 20000), "золотая рыбка": (50000, 250000)}
HUNT_ITEMS = {"заяц": (100, 500), "лиса": (500, 2000), "волк": (2000, 8000),
              "медведь": (10000, 50000), "тигр": (50000, 250000)}
TITLES = {"новичок": 0, "работяга": 100000, "бизнесмен": 1000000,
          "олигарх": 10000000, "магнат": 100000000, "легенда": 1000000000}

# ═══════════ FLASK ═══════════
try:
    from flask import Flask
    app = Flask("")
    @app.route("/")
    def home(): return "🌟 Astra alive!"
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080), daemon=True).start()
    print("🌐 Flask :8080")
except: pass

# ═══════════ VK ═══════════
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

# ═══════════ КЛАВИАТУРЫ ═══════════
def get_kb():
    kb = VkKeyboard(one_time=False)
    kb.add_button("💰 Баланс", color=VkKeyboardColor.PRIMARY)
    kb.add_button("💼 Работа", color=VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_button("🏢 Бизнесы", color=VkKeyboardColor.POSITIVE)
    kb.add_button("🎮 Игры", color=VkKeyboardColor.SECONDARY)
    kb.add_line()
    kb.add_button("👤 Профиль", color=VkKeyboardColor.SECONDARY)
    kb.add_button("📋 Помощь", color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()

def get_games_kb():
    kb = VkKeyboard(one_time=False)
    kb.add_button("🎰 Казино 100", color=VkKeyboardColor.PRIMARY)
    kb.add_button("🪙 Монетка 100", color=VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_button("🎲 Кости 100", color=VkKeyboardColor.POSITIVE)
    kb.add_button("🎡 Колесо", color=VkKeyboardColor.SECONDARY)
    kb.add_line()
    kb.add_button("⛏️ Шахта", color=VkKeyboardColor.SECONDARY)
    kb.add_button("🎣 Рыбалка", color=VkKeyboardColor.SECONDARY)
    kb.add_line()
    kb.add_button("◀️ Назад", color=VkKeyboardColor.NEGATIVE)
    return kb.get_keyboard()

BUTTON_CMDS = {
    "💰 Баланс": "баланс", "💼 Работа": "работа", "🏢 Бизнесы": "бизнесы",
    "🎮 Игры": "игры", "👤 Профиль": "профиль", "📋 Помощь": "помощь",
    "🎰 Казино 100": "казино", "🪙 Монетка 100": "монетка",
    "🎲 Кости 100": "кости", "🎡 Колесо": "колесо",
    "⛏️ Шахта": "шахта", "🎣 Рыбалка": "рыбалка",
    "◀️ Назад": "назад",
}

# ═══════════ ОТПРАВКА ═══════════
def send(peer_id, msg, kb=None):
    kw = {"peer_id": peer_id, "message": str(msg), "random_id": 0}
    if kb is None:
        kb = get_kb()
    kw["keyboard"] = kb
    try: vk.messages.send(**kw)
    except Exception as e: print("Send err:", e)

# ═══════════ ОБРАБОТКА ═══════════
def handle(peer_id, user_id, cmd, args):
    u = get_user(user_id)
    target_id = extract_user(args) or user_id
    t = get_user(target_id)

    # КНОПКИ
    if cmd in ("игры", "games"):
        return send(peer_id, "🎮 Выбери игру:", get_games_kb())
    if cmd == "назад":
        return send(peer_id, "📋 Главное меню:", get_kb())

    # ПОМОЩЬ
    if cmd in ("помощь", "help", "команды"):
        return send(peer_id,
            "🌟 𝗔𝘀𝘁𝗿𝗮 • Чат-менеджер\n\n"
            "💰 Экономика:\n  !баланс !работа !бонус !ежедневка\n"
            "  !бизнесы !купить !доход !продать\n"
            "  !банк !положить !снять !депозит !забрать !перевод\n\n"
            "🏪 Магазин:\n  !машины !дома !яхты !телефоны\n"
            "  !питомцы !фермы !кейсы\n\n"
            "🎮 Игры:\n  !казино [ставка] !монетка [ставка]\n"
            "  !кости [ставка] !рулетка [ставка] !краш [ставка]\n"
            "  !угадай <1-10> [ставка] !кнб <камень/ножницы/бумага>\n"
            "  !дуэль @id !лотерея !колесо\n\n"
            "⛏️ Активности:\n  !шахта !рыбалка !охота !ферма\n"
            "  !покормить !поиграть\n\n"
            "💍 Социал:\n  !репа @id !брак @id !развод\n"
            "  !друзья !подарить @id сумма\n"
            "  !клан !создатьклан <название>\n\n"
            "👤 Профиль:\n  !профиль !топ !стата !титул <название>\n"
            "  !инвентарь !достижения\n\n"
            "🎁 Промо:\n  !активировать <код> !списокпромо\n\n"
            "🛡️ Админ:\n  !варн !мут !снятьмут !снятьварн !кик !бан\n"
            "  !выдатьбаланс !забратьбаланс !выдатьуровень\n"
            "  !выдатьбизнес !выдатьимущество !обнулить\n"
            "  !создатьпромо !админинфо",
            get_kb())

    if cmd in ("о боте", "about", "инфо"):
        return send(peer_id,
            f"🌟 𝗔𝘀𝘁𝗿𝗮 v2.0\n👥 Пользователей: {fmt(len(DB['users']))}\n"
            f"🎁 Промо: {len(DB['promo'])}\n🏰 Кланов: {len(DB.get('clans', {}))}")

    # ЭКОНОМИКА
    if cmd in ("баланс", "balance", "счет"):
        warns_bar = "⚠️" * t["warns"] + "⚪" * max(0, 3 - t["warns"])
        title = ""
        for tn, tv in sorted(TITLES.items(), key=lambda x: x[1], reverse=True):
            if t["balance"] >= tv: title = tn.capitalize(); break
        return send(peer_id,
            f"💰 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 • [id{target_id}|{get_name(target_id)}]\n\n"
            f"💵 {fmt(t['balance'])} ₽\n🏦 {fmt(t['bank'])} ₽\n"
            f"📊 Уровень {t['level']} ({t['xp']} XP)\n⭐ Реп: {t['reputation']}\n"
            f"🏆 {title or 'Новичок'}\n🏢 {t['business'] or '—'}\n"
            f"🚗 {t['car'] or '—'} | 🏠 {t['house'] or '—'}\n"
            f"⚠️ {warns_bar} ({t['warns']}/3)\n💬 {t['messages_count']}",
            get_kb())

    if cmd in ("работа", "work"):
        if time.time() - u["work_time"] < 1800:
            return send(peer_id, f"⏳ Отдыхай ещё {int((1800-(time.time()-u['work_time']))//60)} мин.")
        jobs = ["программистом", "строителем", "врачом", "таксистом", "поваром", "дизайнером"]
        job = random.choice(jobs)
        earn = 200 + u["level"] * 20 + random.randint(0, 100)
        u["balance"] += earn; u["work_time"] = int(time.time()); save_db()
        return send(peer_id, f"💼 Поработал {job}. Заработал {fmt(earn)} ₽")

    if cmd in ("бонус", "bonus", "ежедневка", "daily"):
        if time.time() - u["daily_time"] < 86400:
            return send(peer_id, f"⏳ Через {int((86400-(time.time()-u['daily_time']))//3600)} ч.")
        b = 500 + u["level"] * 100
        u["balance"] += b; u["daily_time"] = int(time.time()); save_db()
        return send(peer_id, f"🎁 Ежедневка: {fmt(b)} ₽")

    if cmd in ("бизнесы", "businesses"):
        txt = "🏢 𝗕𝗶𝘇𝗻𝗲𝘀𝘀\n\n"
        for n, b in BUSINESSES.items():
            txt += f"• {n} — {fmt(b['price'])} ₽ ({fmt(b['income'])}/ч)"
            if u["business"] == n: txt += " ✅"
            txt += "\n"
        return send(peer_id, txt + "\n!купить <название>")

    if cmd in ("купить", "buy"):
        n = args.lower().strip()
        if n in BUSINESSES:
            b = BUSINESSES[n]
            if u["balance"] < b["price"]: return send(peer_id, "💸")
            if u["business"]: return send(peer_id, "Уже есть бизнес")
            u["balance"] -= b["price"]; u["business"] = n; u["business_time"] = int(time.time())
            save_db(); return send(peer_id, f"🎉 Куплен бизнес «{n}»!")
        elif n in CARS:
            if u["balance"] < CARS[n]: return send(peer_id, "💸")
            u["balance"] -= CARS[n]; u["car"] = n; save_db()
            return send(peer_id, f"🚗 Куплено: {n}")
        elif n in HOUSES:
            if u["balance"] < HOUSES[n]: return send(peer_id, "💸")
            u["balance"] -= HOUSES[n]; u["house"] = n; save_db()
            return send(peer_id, f"🏠 Куплено: {n}")
        elif n in YACHTS:
            if u["balance"] < YACHTS[n]: return send(peer_id, "💸")
            u["balance"] -= YACHTS[n]; u["yacht"] = n; save_db()
            return send(peer_id, f"🚢 Куплено: {n}")
        elif n in PHONES:
            if u["balance"] < PHONES[n]: return send(peer_id, "💸")
            u["balance"] -= PHONES[n]; u["phone"] = n; save_db()
            return send(peer_id, f"📱 Куплено: {n}")
        elif n in PETS:
            if u["balance"] < PETS[n]: return send(peer_id, "💸")
            u["balance"] -= PETS[n]; u["pet"] = n; save_db()
            return send(peer_id, f"🐾 Питомец: {n}")
        elif n in FARMS:
            if u["balance"] < FARMS[n]: return send(peer_id, "💸")
            u["balance"] -= FARMS[n]; u["farm"] = n; save_db()
            return send(peer_id, f"🌾 Ферма: {n}")
        return send(peer_id, "❌ !машины !дома !яхты !телефоны !питомцы !фермы")

    if cmd in ("продать", "sell"):
        n = args.lower().strip()
        if n == "бизнес" and u["business"]:
            p = BUSINESSES[u["business"]]["price"] // 2
            u["balance"] += p; u["business"] = None; save_db()
            return send(peer_id, f"💰 Бизнес продан за {fmt(p)} ₽")
        if n == "машина" and u["car"]:
            p = CARS[u["car"]] // 2
            u["balance"] += p; u["car"] = None; save_db()
            return send(peer_id, f"💰 Машина продана за {fmt(p)} ₽")
        if n == "дом" and u["house"]:
            p = HOUSES[u["house"]] // 2
            u["balance"] += p; u["house"] = None; save_db()
            return send(peer_id, f"💰 Дом продан за {fmt(p)} ₽")
        return send(peer_id, "❌ Нечего продавать")

    if cmd in ("доход", "income"):
        if not u["business"]: return send(peer_id, "Нет бизнеса")
        h = int((time.time() - u["business_time"]) // 3600)
        if h < 1: return send(peer_id, "Рано")
        e = BUSINESSES[u["business"]]["income"] * h
        u["balance"] += e; u["business_time"] = int(time.time()); save_db()
        return send(peer_id, f"💵 Доход: {fmt(e)} ₽")

    if cmd in ("банк", "bank"):
        return send(peer_id,
            f"🏦 𝗕𝗮𝗻𝗸\n💵 {fmt(u['balance'])} ₽\n🏦 {fmt(u['bank'])} ₽\n"
            f"📈 Депозит: {fmt(u['deposit'])} ₽ (5%/ч)\n\n"
            f"!положить <сумма>\n!снять <сумма>\n!депозит <сумма>\n!забрать")

    if cmd in ("положить", "put"):
        try: amt = int(args)
        except: return send(peer_id, "❌ Сумма")
        if amt > u["balance"]: return send(peer_id, "💸")
        u["balance"] -= amt; u["bank"] += amt; save_db()
        return send(peer_id, f"🏦 Положено {fmt(amt)} ₽")

    if cmd in ("снять", "withdraw"):
        try: amt = int(args)
        except: return send(peer_id, "❌ Сумма")
        if amt > u["bank"]: return send(peer_id, "💸")
        u["bank"] -= amt; u["balance"] += amt; save_db()
        return send(peer_id, f"🏦 Снято {fmt(amt)} ₽")

    if cmd in ("депозит", "deposit"):
        try: amt = int(args)
        except: return send(peer_id, "❌ Сумма")
        if amt < 1000: return send(peer_id, "Мин. 1000 ₽")
        if u["balance"] < amt: return send(peer_id, "💸")
        u["balance"] -= amt; u["deposit"] += amt; u["deposit_time"] = int(time.time())
        save_db(); return send(peer_id, f"📈 Депозит {fmt(amt)} ₽ (5%/ч)")

    if cmd in ("забрать", "claim"):
        h = int((time.time() - u["deposit_time"]) // 3600)
        interest = int(u["deposit"] * 0.05 * h)
        total = u["deposit"] + interest
        u["balance"] += total; u["deposit"] = 0; save_db()
        return send(peer_id, f"💰 Забрано {fmt(total)} ₽ (+{fmt(interest)} %)")

    if cmd in ("перевод", "transfer", "перевести"):
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌ !перевод @id123 сумма")
        tg = extract_user(p[0])
        try: amt = int(p[1])
        except: return send(peer_id, "❌ Сумма")
        if amt < 100 or u["balance"] < amt: return send(peer_id, "💸")
        tax = int(amt * 0.05)
        u["balance"] -= amt; tt = get_user(tg); tt["balance"] += amt - tax
        save_db(); return send(peer_id, f"✅ Переведено {fmt(amt-tax)} ₽ (комиссия {fmt(tax)})")

    # МАГАЗИН
    if cmd in ("машины", "cars"):
        txt = "🚗 𝗠𝗮𝗰𝗵𝗶𝗻𝘆\n" + "\n".join(f"• {n} — {fmt(p)} ₽" for n,p in CARS.items())
        return send(peer_id, txt + "\n!купить <название>")
    if cmd in ("дома", "houses"):
        txt = "🏠 𝗗𝗼𝗺𝗮\n" + "\n".join(f"• {n} — {fmt(p)} ₽" for n,p in HOUSES.items())
        return send(peer_id, txt)
    if cmd in ("яхты", "yachts"):
        txt = "🚢 𝗬𝗮𝗵𝘁𝘆\n" + "\n".join(f"• {n} — {fmt(p)} ₽" for n,p in YACHTS.items())
        return send(peer_id, txt)
    if cmd in ("телефоны", "phones"):
        txt = "📱 𝗧𝗲𝗹𝗲𝗳𝗼𝗻𝘆\n" + "\n".join(f"• {n} — {fmt(p)} ₽" for n,p in PHONES.items())
        return send(peer_id, txt)
    if cmd in ("питомцы", "pets"):
        txt = "🐾 𝗣𝗶𝘁𝗼𝗺𝗰𝘆\n" + "\n".join(f"• {n} — {fmt(p)} ₽" for n,p in PETS.items())
        return send(peer_id, txt + "\n!покормить !поиграть")
    if cmd in ("фермы", "farms"):
        txt = "🌾 𝗙𝗲𝗿𝗺𝘆\n" + "\n".join(f"• {n} — {fmt(p)} ₽" for n,p in FARMS.items())
        return send(peer_id, txt)
    if cmd in ("кейсы", "cases"):
        txt = "🎁 𝗞𝗲𝗶𝘀𝘆\n" + "\n".join(f"• {n} — {fmt(c['price'])} ₽ ({fmt(c['min'])}-{fmt(c['max'])})" for n,c in CASES.items())
        return send(peer_id, txt + "\n!кейс <название>")

    # КЕЙС / ИНВЕНТАРЬ
    if cmd in ("кейс", "case", "открыть"):
        n = args.lower().strip()
        if n not in CASES: return send(peer_id, "❌ " + ", ".join(CASES.keys()))
        c = CASES[n]
        if u["balance"] < c["price"]: return send(peer_id, "💸")
        u["balance"] -= c["price"]
        win = random.randint(c["min"], c["max"])
        u["balance"] += win
        item = random.choice(list(MINE_ITEMS.keys()) + list(FISH_ITEMS.keys()))
        u["inventory"][item] = u["inventory"].get(item, 0) + 1
        save_db(); return send(peer_id, f"🎁 Кейс «{n}»\n💰 {fmt(win)} ₽\n📦 {item}")

    if cmd in ("инвентарь", "inventory", "вещи"):
        if not u["inventory"]: return send(peer_id, "📦 Пусто")
        txt = "📦 𝗜𝗻𝘃𝗲𝗻𝘁𝗼𝗿𝘆\n" + "\n".join(f"• {i} × {c}" for i,c in u["inventory"].items())
        return send(peer_id, txt)

    if cmd == "продать":
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌ !продать <предмет> <кол-во>")
        item, count = p[0], int(p[1])
        if item not in u["inventory"] or u["inventory"][item] < count:
            return send(peer_id, "❌ Нет")
        price = 0
        for d in [MINE_ITEMS, FISH_ITEMS, HUNT_ITEMS]:
            if item in d: price = d[item][1]
        if price == 0: return send(peer_id, "❌")
        earn = price * count
        u["inventory"][item] -= count
        if u["inventory"][item] <= 0: del u["inventory"][item]
        u["balance"] += earn; save_db()
        return send(peer_id, f"💰 Продано за {fmt(earn)} ₽")

    # АКТИВНОСТИ
    if cmd in ("шахта", "mine", "копать"):
        item, (mn, mx) = random.choice(list(MINE_ITEMS.items()))
        earn = random.randint(mn, mx)
        u["balance"] += earn; u["inventory"][item] = u["inventory"].get(item, 0) + 1
        save_db(); return send(peer_id, f"⛏️ {item} → {fmt(earn)} ₽")
    if cmd in ("рыбалка", "fish"):
        item, (mn, mx) = random.choice(list(FISH_ITEMS.items()))
        earn = random.randint(mn, mx)
        u["balance"] += earn; u["inventory"][item] = u["inventory"].get(item, 0) + 1
        save_db(); return send(peer_id, f"🎣 {item} → {fmt(earn)} ₽")
    if cmd in ("охота", "hunt"):
        item, (mn, mx) = random.choice(list(HUNT_ITEMS.items()))
        earn = random.randint(mn, mx)
        u["balance"] += earn; u["inventory"][item] = u["inventory"].get(item, 0) + 1
        save_db(); return send(peer_id, f"🏹 {item} → {fmt(earn)} ₽")
    if cmd in ("ферма", "farm", "собрать"):
        if not u["farm"]: return send(peer_id, "Купи ферму: !фермы")
        h = int((time.time() - u["farm_time"]) // 3600)
        if h < 1: return send(peer_id, "Рано")
        earn = {"огород": 5000, "теплица": 25000, "ранчо": 100000}[u["farm"]] * h
        u["balance"] += earn; u["farm_time"] = int(time.time()); save_db()
        return send(peer_id, f"🌾 Собрано: {fmt(earn)} ₽")
    if cmd in ("покормить", "feed"):
        if not u["pet"]: return send(peer_id, "Нет питомца")
        if u["balance"] < 500: return send(peer_id, "💸 500 ₽")
        u["balance"] -= 500; u["pet_hunger"] = min(100, u["pet_hunger"] + 30); save_db()
        return send(peer_id, f"🍖 {u['pet']} сытость: {u['pet_hunger']}%")
    if cmd in ("поиграть", "play_pet"):
        if not u["pet"]: return send(peer_id, "Нет питомца")
        u["pet_happiness"] = min(100, u["pet_happiness"] + 30); save_db()
        return send(peer_id, f"🎾 {u['pet']} счастье: {u['pet_happiness']}%")

    # ИГРЫ
    if cmd in ("монетка", "coin", "flip"):
        bet = int(args) if args else 100
        if bet < 50 or u["balance"] < bet: return send(peer_id, "💸")
        if random.choice([True, False]):
            u["balance"] += bet; u["games_won"] += 1
            send(peer_id, f"🪙 Орёл! +{fmt(bet)} ₽")
        else:
            u["balance"] -= bet; u["games_lost"] += 1
            send(peer_id, f"🪙 Решка! -{fmt(bet)} ₽")
        save_db(); return
    if cmd in ("казино", "slots", "casino", "слоты"):
        bet = int(args) if args else 100
        if bet < 100 or u["balance"] < bet: return send(peer_id, "💸")
        s = [random.choice(["🍒","🍋","🔔","⭐","7️⃣"]) for _ in range(3)]
        if s[0]==s[1]==s[2]:
            mult = 10 if s[0]=="7️⃣" else 5
            u["balance"] += bet*mult; u["games_won"] += 1
            send(peer_id, f"{''.join(s)} ДЖЕКПОТ ×{mult}! +{fmt(bet*mult)} ₽")
        elif s[0]==s[1] or s[1]==s[2] or s[0]==s[2]:
            u["balance"] += bet; u["games_won"] += 1
            send(peer_id, f"{''.join(s)} +{fmt(bet)} ₽")
        else:
            u["balance"] -= bet; u["games_lost"] += 1
            send(peer_id, f"{''.join(s)} -{fmt(bet)} ₽")
        save_db(); return
    if cmd in ("кости", "dice"):
        bet = int(args) if args else 100
        if bet < 100 or u["balance"] < bet: return send(peer_id, "💸")
        d = random.randint(1, 6)
        if d >= 4:
            u["balance"] += bet; u["games_won"] += 1
            send(peer_id, f"🎲 {d} +{fmt(bet)} ₽")
        else:
            u["balance"] -= bet; u["games_lost"] += 1
            send(peer_id, f"🎲 {d} -{fmt(bet)} ₽")
        save_db(); return
    if cmd in ("рулетка", "roulette"):
        bet = int(args) if args else 100
        if bet < 100 or u["balance"] < bet: return send(peer_id, "💸")
        n = random.randint(0, 36)
        if n == 0:
            u["balance"] -= bet; u["games_lost"] += 1
            send(peer_id, f"🎰 {n} зеро -{fmt(bet)} ₽")
        elif n % 2 == 0:
            u["balance"] += bet; u["games_won"] += 1
            send(peer_id, f"🎰 {n} красное +{fmt(bet)} ₽")
        else:
            u["balance"] -= bet; u["games_lost"] += 1
            send(peer_id, f"🎰 {n} чёрное -{fmt(bet)} ₽")
        save_db(); return
    if cmd in ("краш", "crash"):
        bet = int(args) if args else 100
        if bet < 100 or u["balance"] < bet: return send(peer_id, "💸")
        crash = round(random.uniform(1.0, 10.0), 2)
        if crash >= 2.0:
            win = int(bet * crash); u["balance"] += win; u["games_won"] += 1
            send(peer_id, f"📈 {crash}× +{fmt(win)} ₽")
        else:
            u["balance"] -= bet; u["games_lost"] += 1
            send(peer_id, f"📉 {crash}× -{fmt(bet)} ₽")
        save_db(); return
    if cmd in ("угадай", "guess"):
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌ !угадай <1-10> <ставка>")
        try: guess, bet = int(p[0]), int(p[1])
        except: return send(peer_id, "❌")
        if bet < 100 or u["balance"] < bet: return send(peer_id, "💸")
        num = random.randint(1, 10)
        if guess == num:
            win = bet*5; u["balance"] += win; u["games_won"] += 1
            send(peer_id, f"🎯 Было {num}. +{fmt(win)} ₽")
        else:
            u["balance"] -= bet; u["games_lost"] += 1
            send(peer_id, f"🎯 Было {num}. -{fmt(bet)} ₽")
        save_db(); return
    if cmd in ("кнб", "rps"):
        if args.lower() not in ("камень","ножницы","бумага"):
            return send(peer_id, "❌ !кнб <камень/ножницы/бумага>")
        bot_c = random.choice(["камень","ножницы","бумага"])
        wins = {"камень":"ножницы","ножницы":"бумага","бумага":"камень"}
        if args.lower() == bot_c:
            return send(peer_id, f"🤝 Ничья. Бот: {bot_c}")
        elif wins[args.lower()] == bot_c:
            u["balance"] += 100; u["games_won"] += 1; save_db()
            return send(peer_id, f"✅ Бот: {bot_c}. +100 ₽")
        else:
            u["balance"] -= 100; u["games_lost"] += 1; save_db()
            return send(peer_id, f"❌ Бот: {bot_c}. -100 ₽")
    if cmd in ("дуэль", "duel"):
        tg = extract_user(args)
        if not tg or tg == user_id: return send(peer_id, "❌ !дуэль @id123")
        tt = get_user(tg); bet = 500
        if u["balance"] < bet or tt["balance"] < bet: return send(peer_id, f"💸 Нужно {fmt(bet)}")
        u["balance"] -= bet; tt["balance"] -= bet
        if random.choice([True, False]):
            u["balance"] += bet*2; u["games_won"] += 1
            send(peer_id, f"⚔️ Победил [id{tg}]! +{fmt(bet*2)} ₽")
        else:
            tt["balance"] += bet*2; u["games_lost"] += 1
            send(peer_id, f"⚔️ [id{tg}] победил!")
        save_db(); return
    if cmd in ("лотерея", "lottery"):
        if u["balance"] < 100: return send(peer_id, "💸 100 ₽")
        u["balance"] -= 100
        ticket = random.randint(100000, 999999)
        if random.randint(1, 100) <= 5:
            prize = random.randint(10000, 100000)
            u["balance"] += prize; save_db()
            return send(peer_id, f"🎟️ #{ticket}\n🎉 {fmt(prize)} ₽!")
        save_db(); return send(peer_id, f"🎟️ #{ticket}\n😔 Мимо")
    if cmd in ("колесо", "wheel", "spin"):
        if time.time() - u["spin_time"] < 3600:
            return send(peer_id, f"⏳ Через {int((3600-(time.time()-u['spin_time']))//60)} мин.")
        prizes = [100, 500, 1000, 5000, 10000, 50000, 100000, 0]
        win = random.choice(prizes)
        u["balance"] += win; u["spin_time"] = int(time.time()); save_db()
        return send(peer_id, f"🎡 Выпало: {fmt(win)} ₽!")

    # СОЦИАЛ
    if cmd in ("репа", "rep", "репутация"):
        tg = extract_user(args)
        if not tg or tg == user_id: return send(peer_id, "❌ !репа @id123")
        tt = get_user(tg); tt["reputation"] += 1; save_db()
        return send(peer_id, f"⭐ +1 репы [id{tg}] (всего {tt['reputation']})")
    if cmd in ("брак", "marry", "свадьба"):
        tg = extract_user(args)
        if not tg or tg == user_id: return send(peer_id, "❌ !брак @id123")
        if u["married_to"] or get_user(tg)["married_to"]: return send(peer_id, "💔 Кто-то женат")
        if u["balance"] < 50000: return send(peer_id, "💸 50000 ₽")
        u["balance"] -= 50000; u["married_to"] = tg; get_user(tg)["married_to"] = user_id
        save_db(); return send(peer_id, f"💍 [id{user_id}] + [id{tg}] семья!")
    if cmd in ("развод", "divorce"):
        if not u["married_to"]: return send(peer_id, "Не женат")
        get_user(u["married_to"])["married_to"] = 0; u["married_to"] = 0; save_db()
        return send(peer_id, "💔 Развод")
    if cmd in ("друзья", "friends"):
        if not u["friends"]: return send(peer_id, "👥 Пусто")
        return send(peer_id, "👥 Друзья:\n" + "\n".join(f"• [id{f}]" for f in u["friends"]))
    if cmd in ("добавитьдруга", "addfriend"):
        tg = extract_user(args)
        if tg and tg not in u["friends"]:
            u["friends"].append(tg); save_db()
            return send(peer_id, f"✅ [id{tg}] в друзьях")
    if cmd in ("подарить", "gift"):
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌ !подарить @id123 сумма")
        tg = extract_user(p[0])
        try: amt = int(p[1])
        except: return send(peer_id, "❌")
        if amt < 100 or u["balance"] < amt: return send(peer_id, "💸")
        u["balance"] -= amt; get_user(tg)["balance"] += amt; save_db()
        return send(peer_id, f"🎁 {fmt(amt)} ₽ → [id{tg}]")
    if cmd in ("клан", "clan"):
        if u["clan_id"] == 0: return send(peer_id, "Ты не в клане. !создатьклан <название>")
        clan = DB["clans"].get(str(u["clan_id"]), {})
        return send(peer_id, f"🏰 {clan.get('name','?')}\n💰 {fmt(clan.get('balance',0))} ₽")
    if cmd in ("создатьклан", "createclan"):
        name = args.strip()
        if not name: return send(peer_id, "❌ !создатьклан <название>")
        if u["balance"] < 100000: return send(peer_id, "💸 100000 ₽")
        if u["clan_id"] != 0: return send(peer_id, "Уже в клане")
        u["balance"] -= 100000
        cid = len(DB["clans"]) + 1
        DB["clans"][str(cid)] = {"name": name, "owner": user_id, "balance": 0, "members": [user_id]}
        u["clan_id"] = cid; save_db()
        return send(peer_id, f"🏰 Клан «{name}» создан!")

    # ПРОФИЛЬ
    if cmd in ("профиль", "profile", "я"):
        warns_bar = "⚠️"*t["warns"] + "⚪"*max(0, 3-t["warns"])
        title = ""
        for tn, tv in sorted(TITLES.items(), key=lambda x: x[1], reverse=True):
            if t["balance"] >= tv: title = tn.capitalize(); break
        return send(peer_id,
            f"👤 [id{target_id}|{get_name(target_id)}]\n\n"
            f"💰 {fmt(t['balance'])} ₽\n🏦 {fmt(t['bank'])} ₽\n"
            f"📊 Ур. {t['level']} ({t['xp']} XP)\n⭐ {t['reputation']}\n"
            f"🏆 {title or 'Новичок'}\n🏢 {t['business'] or '—'}\n"
            f"🚗 {t['car'] or '—'} | 🏠 {t['house'] or '—'}\n"
            f"🐾 {t['pet'] or '—'}\n⚔️ {t['games_won']}W/{t['games_lost']}L\n"
            f"⚠️ {warns_bar} ({t['warns']}/3)\n💬 {t['messages_count']}",
            get_kb())
    if cmd in ("топ", "top"):
        rows = sorted(DB["users"].items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
        medals = ["🥇","🥈","🥉"]
        txt = "🏆 𝗧𝗼𝗽-10\n\n"
        for i,(uid,d) in enumerate(rows, 1):
            m = medals[i-1] if i<=3 else f"{i}."
            txt += f"{m} [id{uid}|{get_name(int(uid))}] — {fmt(d['balance'])} ₽\n"
        return send(peer_id, txt)
    if cmd in ("топ уровень", "toplevel"):
        rows = sorted(DB["users"].items(), key=lambda x: x[1]["level"], reverse=True)[:10]
        txt = "📊 𝗧𝗼𝗽 𝗽𝗼 𝘂𝗿𝗼𝘃𝗻𝘆\n\n"
        for i,(uid,d) in enumerate(rows, 1):
            txt += f"{i}. [id{uid}] — ур. {d['level']}\n"
        return send(peer_id, txt)
    if cmd in ("стата", "stats", "статистика"):
        tb = sum(d["balance"] for d in DB["users"].values())
        tm = sum(d["messages_count"] for d in DB["users"].values())
        return send(peer_id,
            f"📊 𝗦𝘁𝗮𝘁𝘀\n👥 {fmt(len(DB['users']))}\n💰 {fmt(tb)} ₽\n"
            f"💬 {fmt(tm)}\n🎁 {len(DB['promo'])}\n🏰 {len(DB.get('clans',{}))}")
    if cmd in ("титул", "title"):
        n = args.lower().strip()
        if n not in TITLES: return send(peer_id, "❌ " + ", ".join(TITLES.keys()))
        if u["balance"] < TITLES[n]: return send(peer_id, f"💸 {fmt(TITLES[n])} ₽")
        u["balance"] -= TITLES[n]; u["title"] = n; save_db()
        return send(peer_id, f"🏆 Титул «{n}»!")
    if cmd in ("достижения", "achievements", "ачивки"):
        if not u["achievements"]: return send(peer_id, "🏅 Пусто")
        return send(peer_id, "🏅 " + "\n".join(f"• {a}" for a in u["achievements"]))

    # ПРОМО
    if cmd in ("активировать", "промо", "promo", "promocode"):
        code = args.upper().strip()
        if not code: return send(peer_id, "❌ !активировать <код>")
        if code not in DB["promo"]: return send(peer_id, "❌ Не найден")
        p = DB["promo"][code]
        if p["uses_left"] <= 0: return send(peer_id, "❌ Исчерпан")
        if p["reward_type"] == "balance":
            u["balance"] += int(p["reward_value"]); msg = f"💰 +{fmt(p['reward_value'])} ₽"
        elif p["reward_type"] == "business":
            u["business"] = p["reward_value"]; msg = f"🏢 {p['reward_value']}"
        elif p["reward_type"] == "level":
            u["level"] = int(p["reward_value"]); u["xp"] = u["level"]**2
            msg = f"📊 Уровень {p['reward_value']}"
        p["uses_left"] -= 1; save_db()
        return send(peer_id, f"🎁 {msg}")
    if cmd in ("списокпромо", "promos"):
        if not DB["promo"]: return send(peer_id, "🎁 Пусто")
        txt = "🎁 𝗣𝗿𝗼𝗺𝗼\n" + "\n".join(f"• {c} — {p['reward_type']} {p['reward_value']} ({p['uses_left']} ост.)" for c,p in DB["promo"].items())
        return send(peer_id, txt)

    # РАЗВЛЕЧЕНИЯ
    if cmd in ("анекдот", "joke"):
        jokes = [
            "— Почему программисты путают Хэллоуин и Рождество?\n— Oct 31 == Dec 25",
            "Заходит улитка в бар, бармен её выгоняет. Через год: 'Зачем ты так?'",
            "— Сири, почему я одинок?\n— *открывает фронталку*",
            "Жена: 'Купи батон. Если будут яйца — десяток.'\nВернулся с 10 батонами."
        ]
        return send(peer_id, "😄 " + random.choice(jokes))
    if cmd in ("факт", "fact"):
        facts = [
            "Мёд не портится. Находили съедобный в гробницах фараонов.",
            "Осьминоги имеют 3 сердца и голубую кровь.",
            "Бананы — ягоды, клубника — нет.",
            "Человек проводит 6 месяцев жизни, ожидая зелёный свет.",
            "Сердце креветки в голове."
        ]
        return send(peer_id, "🧠 " + random.choice(facts))
    if cmd in ("цитата", "quote"):
        quotes = [
            "«Будь собой; прочие роли заняты.» — Уайльд",
            "«Делай великие дела — люби что делаешь.» — Джобс",
            "«Будущее за теми, кто верит в мечты.» — Рузвельт"
        ]
        return send(peer_id, random.choice(quotes))
    if cmd in ("8ball", "шар", "предсказание"):
        return send(peer_id, f"🎱 {random.choice(['Да','Нет','Возможно','Точно да','Точно нет','Спроси позже','100%'])}")
    if cmd in ("погода", "weather"):
        return send(peer_id, f"🌤️ {random.choice(['☀️ Ясно','⛅ Облачно','🌧️ Дождь','❄️ Снег'])}, {random.randint(-10,30)}°C")
    if cmd in ("совместимость", "compat"):
        tg = extract_user(args)
        if not tg: return send(peer_id, "❌ !совместимость @id123")
        return send(peer_id, f"💕 [id{user_id}] + [id{tg}]: {random.randint(0,100)}%")

    # МОДЕРАЦИЯ
    if cmd in ("варн", "warn"):
        if not is_admin(user_id): return send(peer_id, "🚫 Только админ")
        tg = extract_user(args)
        if not tg: return send(peer_id, "❌ !варн @id123")
        tt = get_user(tg); tt["warns"] += 1; save_db()
        send(peer_id, f"⚠️ [id{tg}] варн ({tt['warns']}/3)")
        if tt["warns"] >= 3:
            tt["muted_until"] = int(time.time()) + 3600; tt["warns"] = 0; save_db()
            send(peer_id, f"🚫 [id{tg}] мут 1ч за 3 варна")
        return
    if cmd in ("мут", "mute"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split(); tg = extract_user(p[0]) if p else None
        if not tg: return send(peer_id, "❌ !мут @id123 [мин]")
        mins = int(p[1]) if len(p)>1 else 60
        get_user(tg)["muted_until"] = int(time.time()) + mins*60; save_db()
        return send(peer_id, f"🔇 [id{tg}] мут {mins} мин")
    if cmd in ("снятьмут", "unmute"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if tg: get_user(tg)["muted_until"] = 0; save_db(); send(peer_id, f"✅ Мут снят [id{tg}]")
        return
    if cmd in ("снятьварн", "unwarn"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if tg:
            tt = get_user(tg); tt["warns"] = max(0, tt["warns"]-1); save_db()
            send(peer_id, f"✅ Варн снят [id{tg}] ({tt['warns']} ост.)")
        return
    if cmd in ("кик", "kick", "бан", "ban"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if not tg: return send(peer_id, "❌ !кик @id123")
        try:
            vk.messages.removeChatUser(chat_id=peer_id-2000000000, user_id=tg)
            send(peer_id, f"🔨 [id{tg}] удалён")
        except Exception as e: send(peer_id, f"❌ {e}")
        return

    # АДМИН
    if cmd in ("выдатьбаланс", "givebalance"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split()
        if len(p)<2: return send(peer_id, "❌ !выдатьбаланс @id123 сумма")
        tg = extract_user(p[0]); amt = int(p[1])
        get_user(tg)["balance"] += amt; save_db()
        return send(peer_id, f"✅ +{fmt(amt)} ₽ [id{tg}]")
    if cmd in ("забратьбаланс", "takebalance"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split()
        if len(p)<2: return send(peer_id, "❌ !забратьбаланс @id123 сумма")
        tg = extract_user(p[0]); amt = int(p[1])
        tt = get_user(tg); tt["balance"] = max(0, tt["balance"]-amt); save_db()
        return send(peer_id, f"✅ -{fmt(amt)} ₽ у [id{tg}]")
    if cmd in ("выдатьуровень", "givelevel"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split()
        if len(p)<2: return send(peer_id, "❌ !выдатьуровень @id123 уровень")
        tg = extract_user(p[0]); lv = int(p[1])
        tt = get_user(tg); tt["level"] = lv; tt["xp"] = lv*lv; save_db()
        return send(peer_id, f"✅ Уровень {lv} [id{tg}]")
    if cmd in ("выдатьрепу", "giverep"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split()
        if len(p)<2: return send(peer_id, "❌ !выдатьрепу @id123 кол-во")
        tg = extract_user(p[0]); amt = int(p[1])
        get_user(tg)["reputation"] += amt; save_db()
        return send(peer_id, f"✅ +{amt} репы [id{tg}]")
    if cmd in ("выдатьбизнес", "givebusiness"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split()
        if len(p)<2: return send(peer_id, "❌ !выдатьбизнес @id123 название")
        tg = extract_user(p[0]); biz = p[1].lower()
        if biz in BUSINESSES:
            tt = get_user(tg); tt["business"] = biz; tt["business_time"] = int(time.time()); save_db()
            return send(peer_id, f"✅ {biz} → [id{tg}]")
        return send(peer_id, "❌ !бизнесы")
    if cmd in ("забратьбизнес", "takebusiness"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if tg: get_user(tg)["business"] = None; save_db(); send(peer_id, f"✅ Бизнес забран [id{tg}]")
        return
    if cmd in ("выдатьимущество", "giveproperty"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split()
        if len(p)<3: return send(peer_id, "❌ !выдатьимущество @id123 тип название\n(car/house/yacht/phone/pet)")
        tg = extract_user(p[0]); typ = p[1].lower(); nm = p[2].lower()
        tt = get_user(tg)
        maps = {"car": ("car", CARS), "house": ("house", HOUSES), "yacht": ("yacht", YACHTS),
                "phone": ("phone", PHONES), "pet": ("pet", PETS)}
        if typ in maps:
            key, d = maps[typ]
            if nm in d:
                tt[key] = nm; save_db(); return send(peer_id, f"✅ {nm} → [id{tg}]")
        return send(peer_id, "❌")
    if cmd in ("обнулить", "reset"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if not tg: return send(peer_id, "❌ !обнулить @id123")
        DB["users"][str(tg)] = {
            "balance":1000,"bank":0,"xp":0,"level":0,"warns":0,"reputation":0,
            "business":None,"business_time":0,"work_time":0,"bonus_time":0,
            "deposit":0,"deposit_time":0,"car":None,"house":None,"yacht":None,
            "phone":None,"pet":None,"pet_hunger":100,"pet_happiness":100,
            "farm":None,"farm_time":0,"married_to":0,"clan_id":0,"inventory":{},
            "achievements":[],"muted_until":0,"messages_count":0,"games_won":0,
            "games_lost":0,"title":None,"daily_time":0,"spin_time":0,"friends":[],
            "nickname":None,"bio":None,"last_seen":0,"register_time":int(time.time())
        }
        save_db(); return send(peer_id, f"✅ [id{tg}] обнулён")
    if cmd in ("админинфо", "admininfo"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if not tg: return send(peer_id, "❌ !админинфо @id123")
        tt = get_user(tg)
        return send(peer_id,
            f"👤 [id{tg}|{get_name(tg)}]\n\n"
            f"💰 {fmt(tt['balance'])} ₽\n🏦 {fmt(tt['bank'])} ₽\n"
            f"📊 Ур. {tt['level']} ({tt['xp']} XP)\n⚠️ {tt['warns']}/3\n"
            f"⭐ {tt['reputation']}\n🏢 {tt['business'] or '—'}\n"
            f"🚗 {tt['car'] or '—'} | 🏠 {tt['house'] or '—'}\n"
            f"🚢 {tt['yacht'] or '—'} | 📱 {tt['phone'] or '—'}\n"
            f"🐾 {tt['pet'] or '—'} | 🌾 {tt['farm'] or '—'}\n"
            f"💍 {tt['married_to'] or '—'} | 🏰 {tt['clan_id'] or '—'}\n"
            f"📦 {len(tt['inventory'])} предметов\n⚔️ {tt['games_won']}W/{tt['games_lost']}L\n"
            f"💬 {tt['messages_count']}\n🔇 {'да' if tt['muted_until']>time.time() else 'нет'}\n"
            f"📅 {datetime.fromtimestamp(tt['register_time']).strftime('%d.%m.%Y')}")
    if cmd in ("создатьпромо", "createpromo"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split()
        if len(p)<4:
            return send(peer_id, "❌ !создатьпромо КОД balance|business|level ЗНАЧЕНИЕ КОЛ-ВО\nПример: !создатьпромо VIP2026 balance 10000 50")
        code, rtype, rval, uses = p[0].upper(), p[1], p[2], int(p[3])
        if rtype not in ("balance","business","level"):
            return send(peer_id, "❌ Тип: balance / business / level")
        DB["promo"][code] = {"reward_type":rtype,"reward_value":rval,"uses_left":uses,"creator":user_id,"created":int(time.time())}
        save_db()
        return send(peer_id, f"✅ Промо `{code}`\nТип: {rtype}\nЗначение: {rval}\nАктиваций: {uses}")
    if cmd in ("удалитьпромо", "deletepromo"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        code = args.upper().strip()
        if code in DB["promo"]:
            del DB["promo"][code]; save_db(); return send(peer_id, f"✅ {code} удалён")
        return send(peer_id, "❌")
    if cmd in ("добавитьадмина", "addadmin"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if tg and tg not in DEVELOPERS:
            DEVELOPERS.append(tg)
            os.environ["DEVELOPERS"] = ",".join(map(str, DEVELOPERS))
            return send(peer_id, f"✅ [id{tg}] теперь админ")
        return send(peer_id, "❌")
    if cmd in ("списокадминов", "admins"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        return send(peer_id, "👑 Админы:\n" + "\n".join(f"• [id{a}]" for a in DEVELOPERS))


# ═══════════ ГЛАВНЫЙ ЦИКЛ ═══════════
print("="*50)
print("🌟 Astra запущена и слушает события...")
print("="*50)

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        print(f"📨 MSG | user={event.from_user} chat={event.from_chat} peer={event.peer_id} text='{event.text}'")

        if not (event.from_user or event.from_chat):
            print("   ⚠️ Пропуск")
            continue

        peer_id = event.peer_id
        user_id = event.user_id
        text = event.text.strip() if event.text else ""

        u = get_user(user_id)
        if u["muted_until"] > time.time():
            try: vk.messages.delete(peer_id=peer_id, message_ids=event.message_id, delete_for_all=1)
            except: pass
            continue

        u["xp"] += 5
        u["messages_count"] += 1
        u["last_seen"] = int(time.time())
        nl = int(u["xp"] ** 0.5)
        if nl > u["level"]:
            u["level"] = nl
            if event.from_user:
                send(peer_id, f"🎉 Уровень {nl}!", get_kb())
        save_db()

        if not text:
            continue

        # Кнопка?
        if text in BUTTON_CMDS:
            cmd = BUTTON_CMDS[text]
            print(f"   🎯 Кнопка: '{text}' → '{cmd}'")
            try: handle(peer_id, user_id, cmd, "")
            except Exception as e:
                print(f"   ❌ {e}"); traceback.print_exc()
            continue

        # Команда?
        if text.lower().startswith(PREFIX):
            rest = text[1:].strip()
            parts = rest.split(maxsplit=1)
            cmd = parts[0].lower() if parts else ""
            args = parts[1] if len(parts)>1 else ""
            print(f"   ✅ Команда: '{cmd}' args='{args}'")
            try: handle(peer_id, user_id, cmd, args)
            except Exception as e:
                print(f"   ❌ {e}"); traceback.print_exc()
                send(peer_id, f"❌ Ошибка: {e}")

    elif event.type == VkEventType.MESSAGE_EVENT:
        print(f"🔘 EVENT | {event.object}")
        try:
            payload = json.loads(event.object.payload) if event.object.payload else {}
            cmd = payload.get("cmd", "")
            if cmd: handle(event.peer_id, event.user_id, cmd, "")
            vk.messages.sendMessageEventAnswer(
                event_id=event.object.event_id,
                user_id=event.user_id,
                peer_id=event.peer_id
            )
        except Exception as e:
            print(f"   ❌ Event err: {e}")
