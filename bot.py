import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json, time, os, re, random, threading, traceback, math
from datetime import datetime

# ═══════════════════════════════════════
#  КОНФИГ
# ═══════════════════════════════════════
TOKEN = os.environ.get("VK_TOKEN", "")
DEVELOPERS = [int(x) for x in os.environ.get("DEVELOPERS", "0").split(",") if x]
PREFIX = "!"

if not TOKEN:
    print("❌ VK_TOKEN не установлен!")
    raise SystemExit(1)

print(f"✅ Токен загружен | Админы: {DEVELOPERS}")

# ═══════════════════════════════════════
#  БД JSON
# ═══════════════════════════════════════
DB_FILE = "db.json"
def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "promo": {}, "clans": {}, "chat": {}, "achievements": {}}
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
            "title": None, "skin": None,
            "daily_time": 0, "spin_time": 0,
            "friends": [], "banned": False,
            "nickname": None, "bio": None,
            "last_seen": 0, "register_time": int(time.time())
        }
        save_db()
    return DB["users"][s]

def extract_user(text):
    m = re.search(r"(?:@id|id|vk\.com/)(\d+)", text)
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

# ═══════════════════════════════════════
#  ДАННЫЕ
# ═══════════════════════════════════════
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

PHONES = {"нокия": 5000, "xiaomi": 25000, "iphone": 150000, "samsung": 300000, "huawei": 80000}

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

TITLES = {
    "новичок": 0, "работяга": 100000, "бизнесмен": 1000000,
    "олигарх": 10000000, "магнат": 100000000, "легенда": 1000000000
}

BAD_WORDS = ["плохое_слово1", "плохое_слово2"]  # добавь свои

# ═══════════════════════════════════════
#  FLASK
# ═══════════════════════════════════════
try:
    from flask import Flask
    app = Flask("")
    @app.route("/")
    def home(): return "🌟 Astra alive!"
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080), daemon=True).start()
    print("🌐 Flask :8080")
except: pass

# ═══════════════════════════════════════
#  VK
# ═══════════════════════════════════════
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)
print("🌟 Astra запущена!")

def send(peer_id, msg, kb=None):
    kw = {"peer_id": peer_id, "message": msg, "random_id": 0}
    if kb: kw["keyboard"] = kb
    try: vk.messages.send(**kw)
    except Exception as e: print("Send error:", e)

def get_kb():
    kb = VkKeyboard(inline=True)
    kb.add_button("💰 Баланс", VkKeyboardColor.PRIMARY)
    kb.add_button("💼 Работа", VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_button("👤 Профиль", VkKeyboardColor.SECONDARY)
    kb.add_button("🎮 Игры", VkKeyboardColor.SECONDARY)
    kb.add_line()
    kb.add_button("🏪 Магазин", VkKeyboardColor.PRIMARY)
    kb.add_button("📋 Помощь", VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()

# ═══════════════════════════════════════
#  ОБРАБОТКА КОМАНД
# ═══════════════════════════════════════
def handle(peer_id, user_id, cmd, args):
    u = get_user(user_id)
    target_id = extract_user(args) or user_id
    t = get_user(target_id)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  ПОМОЩЬ / ИНФО
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if cmd in ("помощь", "help", "команды"):
        send(peer_id,
            "🌟 𝗔𝘀𝘁𝗿𝗮 • Чат-менеджер\n\n"
            "💰 𝗘𝗸𝗼𝗻𝗼𝗺𝗶𝗸𝗮:\n"
            "  !баланс !работа !бонус !ежедневка\n"
            "  !бизнесы !купить !доход\n"
            "  !банк !депозит !снять !перевод\n\n"
            "🏪 𝗠𝗮𝗴𝗮𝘇𝗶𝗻:\n"
            "  !машины !дома !яхты !телефоны\n"
            "  !питомцы !фермы !кейсы\n\n"
            "🎮 𝗜𝗴𝗿𝘆:\n"
            "  !казино !слоты !монетка !кости\n"
            "  !рулетка !краш !дуэль !угадай\n"
            "  !кнб !лотерея !колесо !коины\n\n"
            "⛏️ 𝗔𝗸𝘁𝗶𝘃𝗻𝗼𝘀𝘁𝗶:\n"
            "  !шахта !рыбалка !охота !ферма\n\n"
            "💍 𝗦𝗼𝗰𝗶𝗮𝗹:\n"
            "  !репа !брак !развод !друзья\n"
            "  !подарить !клан !создатьклан\n\n"
            "👤 𝗣𝗿𝗼𝗳𝗶𝗹𝗲:\n"
            "  !профиль !топ !инвентарь\n"
            "  !титул !стата !достижения\n\n"
            "🎁 𝗣𝗿𝗼𝗺𝗼:\n"
            "  !активировать <код>\n\n"
            "🛡️ 𝗔𝗱𝗺𝗶𝗻:\n"
            "  !варн !мут !кик !бан\n"
            "  !выдатьбаланс !обнулить\n"
            "  !создатьпромо !админинфо",
            get_kb())

    elif cmd in ("о боте", "about", "инфо"):
        send(peer_id,
            "🌟 𝗔𝘀𝘁𝗿𝗮 • Чат-менеджер v2.0\n\n"
            "👥 Пользователей: " + fmt(len(DB["users"])) + "\n"
            "🎁 Промокодов: " + str(len(DB["promo"])) + "\n"
            "🏰 Кланов: " + str(len(DB.get("clans", {}))) + "\n\n"
            "Создано с ❤️ для твоих бесед")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  ЭКОНОМИКА
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif cmd in ("баланс", "balance", "счет"):
        warns_bar = "⚠️" * t["warns"] + "⚪" * max(0, 3 - t["warns"])
        title = ""
        for tn, tv in sorted(TITLES.items(), key=lambda x: x[1], reverse=True):
            if t["balance"] >= tv:
                title = tn.capitalize()
                break
        send(peer_id,
            f"💰 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 • [id{target_id}|{get_name(target_id)}]\n\n"
            f"💵 Наличные: {fmt(t['balance'])} ₽\n"
            f"🏦 В банке: {fmt(t['bank'])} ₽\n"
            f"📊 Уровень: {t['level']} ({t['xp']} XP)\n"
            f"⭐ Репутация: {t['reputation']}\n"
            f"🏆 Титул: {title or 'Новичок'}\n"
            f"🏢 Бизнес: {t['business'] or '—'}\n"
            f"🚗 Машина: {t['car'] or '—'}\n"
            f"🏠 Дом: {t['house'] or '—'}\n"
            f"⚠️ Варны: {warns_bar} ({t['warns']}/3)\n"
            f"💬 Сообщений: {t['messages_count']}",
            get_kb())

    elif cmd in ("работа", "work"):
        if time.time() - u["work_time"] < 1800:
            mins = int((1800 - (time.time() - u["work_time"])) // 60)
            return send(peer_id, f"⏳ Отдыхай ещё {mins} мин.")
        jobs = ["программистом", "строителем", "врачом", "таксистом", "поваром", "дизайнером", "блогером"]
        job = random.choice(jobs)
        earn = 200 + u["level"] * 20 + random.randint(0, 100)
        u["balance"] += earn
        u["work_time"] = int(time.time())
        save_db()
        send(peer_id, f"💼 Ты поработал {job} и заработал {fmt(earn)} ₽")

    elif cmd in ("бонус", "bonus", "ежедневка", "daily"):
        if time.time() - u["daily_time"] < 86400:
            hours = int((86400 - (time.time() - u["daily_time"])) // 3600)
            return send(peer_id, f"⏳ Ежедневка через {hours} ч.")
        bonus = 500 + u["level"] * 100
        u["balance"] += bonus
        u["daily_time"] = int(time.time())
        save_db()
        send(peer_id, f"🎁 Ежедневный бонус: {fmt(bonus)} ₽\nПриходи завтра!")

    elif cmd in ("бизнесы", "businesses"):
        txt = "🏢 𝗕𝗶𝘇𝗻𝗲𝘀𝘀\n\n"
        for n, b in BUSINESSES.items():
            owned = " ✅" if u["business"] == n else ""
            txt += f"• {n} — {fmt(b['price'])} ₽ ({fmt(b['income'])}/ч){owned}\n"
        txt += "\n✏️ !купить <название>"
        send(peer_id, txt)

    elif cmd in ("купить", "buy"):
        n = args.lower().strip()
        if n in BUSINESSES:
            b = BUSINESSES[n]
            if u["balance"] < b["price"]: return send(peer_id, "💸 Не хватает денег")
            if u["business"]: return send(peer_id, "У тебя уже есть бизнес. Сначала продай.")
            u["balance"] -= b["price"]; u["business"] = n; u["business_time"] = int(time.time())
            save_db(); send(peer_id, f"🎉 Куплен бизнес «{n}»!")
        elif n in CARS:
            if u["balance"] < CARS[n]: return send(peer_id, "💸")
            u["balance"] -= CARS[n]; u["car"] = n; save_db(); send(peer_id, f"🚗 Куплено: {n}")
        elif n in HOUSES:
            if u["balance"] < HOUSES[n]: return send(peer_id, "💸")
            u["balance"] -= HOUSES[n]; u["house"] = n; save_db(); send(peer_id, f"🏠 Куплено: {n}")
        elif n in YACHTS:
            if u["balance"] < YACHTS[n]: return send(peer_id, "💸")
            u["balance"] -= YACHTS[n]; u["yacht"] = n; save_db(); send(peer_id, f"🚢 Куплено: {n}")
        elif n in PHONES:
            if u["balance"] < PHONES[n]: return send(peer_id, "💸")
            u["balance"] -= PHONES[n]; u["phone"] = n; save_db(); send(peer_id, f"📱 Куплено: {n}")
        elif n in PETS:
            if u["balance"] < PETS[n]: return send(peer_id, "💸")
            u["balance"] -= PETS[n]; u["pet"] = n; save_db(); send(peer_id, f"🐾 Питомец: {n}")
        elif n in FARMS:
            if u["balance"] < FARMS[n]: return send(peer_id, "💸")
            u["balance"] -= FARMS[n]; u["farm"] = n; save_db(); send(peer_id, f"🌾 Ферма: {n}")
        else:
            send(peer_id, "❌ Не найдено. Смотри: !машины !дома !яхты !питомцы !фермы")

    elif cmd in ("продать", "sell"):
        n = args.lower().strip()
        if n == "бизнес" and u["business"]:
            price = BUSINESSES[u["business"]]["price"] // 2
            u["balance"] += price; u["business"] = None
            save_db(); send(peer_id, f"💰 Бизнес продан за {fmt(price)} ₽")
        elif n == "машина" and u["car"]:
            price = CARS[u["car"]] // 2
            u["balance"] += price; u["car"] = None
            save_db(); send(peer_id, f"💰 Машина продана за {fmt(price)} ₽")
        elif n == "дом" and u["house"]:
            price = HOUSES[u["house"]] // 2
            u["balance"] += price; u["house"] = None
            save_db(); send(peer_id, f"💰 Дом продан за {fmt(price)} ₽")
        else: send(peer_id, "❌ Нечего продавать")

    elif cmd in ("доход", "income"):
        if not u["business"]: return send(peer_id, "Нет бизнеса")
        h = int((time.time() - u["business_time"]) // 3600)
        if h < 1: return send(peer_id, "Рано собирать")
        e = BUSINESSES[u["business"]]["income"] * h
        u["balance"] += e; u["business_time"] = int(time.time())
        save_db(); send(peer_id, f"💵 Доход: {fmt(e)} ₽")

    elif cmd in ("банк", "bank"):
        send(peer_id,
            f"🏦 𝗕𝗮𝗻𝗸\n\n"
            f"💵 Наличные: {fmt(u['balance'])} ₽\n"
            f"🏦 В банке: {fmt(u['bank'])} ₽\n"
            f"📈 Депозит: {fmt(u['deposit'])} ₽ (5%/ч)\n\n"
            f"!положить <сумма> — в банк\n"
            f"!снять <сумма> — из банка\n"
            f"!депозит <сумма> — на вклад\n"
            f"!забрать — с депозита")

    elif cmd in ("положить", "put"):
        try: amt = int(args)
        except: return send(peer_id, "❌ Сумма")
        if amt > u["balance"]: return send(peer_id, "💸")
        u["balance"] -= amt; u["bank"] += amt; save_db()
        send(peer_id, f"🏦 Положено {fmt(amt)} ₽")

    elif cmd in ("снять", "withdraw"):
        try: amt = int(args)
        except: return send(peer_id, "❌ Сумма")
        if amt > u["bank"]: return send(peer_id, "💸")
        u["bank"] -= amt; u["balance"] += amt; save_db()
        send(peer_id, f"🏦 Снято {fmt(amt)} ₽")

    elif cmd in ("депозит", "deposit"):
        try: amt = int(args)
        except: return send(peer_id, "❌ Сумма")
        if amt < 1000: return send(peer_id, "Мин. 1000 ₽")
        if u["balance"] < amt: return send(peer_id, "💸")
        u["balance"] -= amt; u["deposit"] += amt; u["deposit_time"] = int(time.time())
        save_db(); send(peer_id, f"📈 Депозит {fmt(amt)} ₽ (5%/ч)")

    elif cmd in ("забрать", "claim"):
        hours = int((time.time() - u["deposit_time"]) // 3600)
        interest = int(u["deposit"] * 0.05 * hours)
        total = u["deposit"] + interest
        u["balance"] += total; u["deposit"] = 0; u["deposit_time"] = int(time.time())
        save_db()
        send(peer_id, f"💰 Забрано {fmt(total)} ₽ (проценты: {fmt(interest)} ₽)")

    elif cmd in ("перевод", "transfer", "перевести"):
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌ !перевод @id123 сумма")
        tg = extract_user(p[0])
        try: amt = int(p[1])
        except: return send(peer_id, "❌ Сумма")
        if amt < 100: return send(peer_id, "Мин. 100 ₽")
        if u["balance"] < amt: return send(peer_id, "💸")
        tax = int(amt * 0.05)
        u["balance"] -= amt
        tt = get_user(tg); tt["balance"] += amt - tax
        save_db()
        send(peer_id, f"✅ Переведено {fmt(amt - tax)} ₽ (комиссия 5%: {fmt(tax)} ₽)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  МАГАЗИН / СПИСКИ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif cmd in ("машины", "cars"):
        txt = "🚗 𝗠𝗮𝗰𝗵𝗶𝗻𝘆\n\n"
        for n, p in CARS.items():
            txt += f"• {n} — {fmt(p)} ₽\n"
        send(peer_id, txt + "\n!купить <название>")

    elif cmd in ("дома", "houses"):
        txt = "🏠 𝗗𝗼𝗺𝗮\n\n"
        for n, p in HOUSES.items(): txt += f"• {n} — {fmt(p)} ₽\n"
        send(peer_id, txt + "\n!купить <название>")

    elif cmd in ("яхты", "yachts"):
        txt = "🚢 𝗬𝗮𝗵𝘁𝘆\n\n"
        for n, p in YACHTS.items(): txt += f"• {n} — {fmt(p)} ₽\n"
        send(peer_id, txt)

    elif cmd in ("телефоны", "phones"):
        txt = "📱 𝗧𝗲𝗹𝗲𝗳𝗼𝗻𝘆\n\n"
        for n, p in PHONES.items(): txt += f"• {n} — {fmt(p)} ₽\n"
        send(peer_id, txt)

    elif cmd in ("питомцы", "pets"):
        txt = "🐾 𝗣𝗶𝘁𝗼𝗺𝗰𝘆\n\n"
        for n, p in PETS.items(): txt += f"• {n} — {fmt(p)} ₽\n"
        send(peer_id, txt + "\n!купить <питомец>\n!покормить — сытость\n!поиграть — счастье")

    elif cmd in ("фермы", "farms"):
        txt = "🌾 𝗙𝗲𝗿𝗺𝘆\n\n"
        for n, p in FARMS.items(): txt += f"• {n} — {fmt(p)} ₽\n"
        send(peer_id, txt)

    elif cmd in ("кейсы", "cases"):
        txt = "🎁 𝗞𝗲𝗶𝘀𝘆\n\n"
        for n, c in CASES.items(): txt += f"• {n} — {fmt(c['price'])} ₽ ({fmt(c['min'])}-{fmt(c['max'])})\n"
        send(peer_id, txt + "\n!кейс <название>")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  КЕЙСЫ / ИНВЕНТАРЬ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif cmd in ("кейс", "case", "открыть"):
        n = args.lower().strip()
        if n not in CASES: return send(peer_id, "❌ Кейсы: " + ", ".join(CASES.keys()))
        c = CASES[n]
        if u["balance"] < c["price"]: return send(peer_id, "💸")
        u["balance"] -= c["price"]
        win = random.randint(c["min"], c["max"])
        u["balance"] += win
        item = random.choice(list(MINE_ITEMS.keys()) + list(FISH_ITEMS.keys()))
        u["inventory"][item] = u["inventory"].get(item, 0) + 1
        save_db()
        send(peer_id, f"🎁 𝗞𝗲𝗶𝘀 «{n}»\n\n💰 Выигрыш: {fmt(win)} ₽\n📦 Предмет: {item}")

    elif cmd in ("инвентарь", "inventory", "вещи"):
        if not u["inventory"]: return send(peer_id, "📦 Инвентарь пуст")
        txt = "📦 𝗜𝗻𝘃𝗲𝗻𝘁𝗼𝗿𝘆\n\n"
        for item, count in u["inventory"].items():
            txt += f"• {item} × {count}\n"
        txt += f"\nПродать: !продать <предмет> <кол-во>"
        send(peer_id, txt)

    elif cmd == "продать":
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌ !продать <предмет> <кол-во>")
        item, count = p[0], int(p[1])
        if item not in u["inventory"] or u["inventory"][item] < count:
            return send(peer_id, "❌ Нет столько")
        price = 0
        for d in [MINE_ITEMS, FISH_ITEMS, HUNT_ITEMS]:
            if item in d: price = d[item][1]
        if price == 0: return send(peer_id, "❌ Нельзя продать")
        earn = price * count
        u["inventory"][item] -= count
        if u["inventory"][item] <= 0: del u["inventory"][item]
        u["balance"] += earn; save_db()
        send(peer_id, f"💰 Продано {item} × {count} за {fmt(earn)} ₽")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  АКТИВНОСТИ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif cmd in ("шахта", "mine", "копать"):
        item, (min_p, max_p) = random.choice(list(MINE_ITEMS.items()))
        earn = random.randint(min_p, max_p) * u.get("pickaxe_level", 1)
        u["balance"] += earn
        u["inventory"][item] = u["inventory"].get(item, 0) + 1
        save_db()
        send(peer_id, f"⛏️ Найден {item}! Продан за {fmt(earn)} ₽")

    elif cmd in ("рыбалка", "fish"):
        item, (min_p, max_p) = random.choice(list(FISH_ITEMS.items()))
        earn = random.randint(min_p, max_p) * u.get("rod_level", 1)
        u["balance"] += earn
        u["inventory"][item] = u["inventory"].get(item, 0) + 1
        save_db()
        send(peer_id, f"🎣 Пойман {item}! Продан за {fmt(earn)} ₽")

    elif cmd in ("охота", "hunt"):
        item, (min_p, max_p) = random.choice(list(HUNT_ITEMS.items()))
        earn = random.randint(min_p, max_p)
        u["balance"] += earn
        u["inventory"][item] = u["inventory"].get(item, 0) + 1
        save_db()
        send(peer_id, f"🏹 Добыт {item}! Продан за {fmt(earn)} ₽")

    elif cmd in ("ферма", "farm", "собрать"):
        if not u["farm"]: return send(peer_id, "Сначала купи ферму: !фермы")
        h = int((time.time() - u["farm_time"]) // 3600)
        if h < 1: return send(peer_id, "Рано")
        earn = {"огород": 5000, "теплица": 25000, "ранчо": 100000}[u["farm"]] * h
        u["balance"] += earn; u["farm_time"] = int(time.time())
        save_db(); send(peer_id, f"🌾 Собрано: {fmt(earn)} ₽")

    elif cmd in ("покормить", "feed"):
        if not u["pet"]: return send(peer_id, "Нет питомца")
        if u["balance"] < 500: return send(peer_id, "💸 Нужно 500 ₽")
        u["balance"] -= 500; u["pet_hunger"] = min(100, u["pet_hunger"] + 30)
        save_db(); send(peer_id, f"🍖 {u['pet']} покормлен! Сытость: {u['pet_hunger']}%")

    elif cmd in ("поиграть", "play_pet"):
        if not u["pet"]: return send(peer_id, "Нет питомца")
        u["pet_happiness"] = min(100, u["pet_happiness"] + 30)
        save_db(); send(peer_id, f"🎾 Поиграл с {u['pet']}! Счастье: {u['pet_happiness']}%")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  ИГРЫ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif cmd in ("монетка", "coin", "flip"):
        try: bet = int(args)
        except: return send(peer_id, "❌ !монетка <ставка>")
        if bet < 50 or u["balance"] < bet: return send(peer_id, "💸")
        if random.choice([True, False]):
            u["balance"] += bet; u["games_won"] += 1
            send(peer_id, f"🪙 Орёл! +{fmt(bet)} ₽")
        else:
            u["balance"] -= bet; u["games_lost"] += 1
            send(peer_id, f"🪙 Решка! -{fmt(bet)} ₽")
        save_db()

    elif cmd in ("казино", "slots", "casino", "слоты"):
        try: bet = int(args)
        except: return send(peer_id, "❌ !казино <ставка>")
        if bet < 100 or u["balance"] < bet: return send(peer_id, "💸")
        s = [random.choice(["🍒", "🍋", "🔔", "⭐", "7️⃣"]) for _ in range(3)]
        if s[0] == s[1] == s[2]:
            mult = 10 if s[0] == "7️⃣" else 5
            u["balance"] += bet * mult; u["games_won"] += 1
            send(peer_id, f"{''.join(s)} ДЖЕКПОТ ×{mult}! +{fmt(bet*mult)} ₽")
        elif s[0] == s[1] or s[1] == s[2] or s[0] == s[2]:
            u["balance"] += bet; u["games_won"] += 1
            send(peer_id, f"{''.join(s)} +{fmt(bet)} ₽")
        else:
            u["balance"] -= bet; u["games_lost"] += 1
            send(peer_id, f"{''.join(s)} -{fmt(bet)} ₽")
        save_db()

    elif cmd in ("кости", "dice"):
        try: bet = int(args)
        except: return send(peer_id, "❌ !кости <ставка>")
        if bet < 100 or u["balance"] < bet: return send(peer_id, "💸")
        d = random.randint(1, 6)
        if d >= 4:
            u["balance"] += bet; u["games_won"] += 1
            send(peer_id, f"🎲 {d} — выиграл +{fmt(bet)} ₽")
        else:
            u["balance"] -= bet; u["games_lost"] += 1
            send(peer_id, f"🎲 {d} — проиграл -{fmt(bet)} ₽")
        save_db()

    elif cmd in ("рулетка", "roulette"):
        try: bet = int(args)
        except: return send(peer_id, "❌ !рулетка <ставка>")
        if bet < 100 or u["balance"] < bet: return send(peer_id, "💸")
        n = random.randint(0, 36)
        if n == 0:
            u["balance"] -= bet; u["games_lost"] += 1
            send(peer_id, f"🎰 Выпало {n} (зеро) -{fmt(bet)} ₽")
        elif n % 2 == 0:
            u["balance"] += bet; u["games_won"] += 1
            send(peer_id, f"🎰 Выпало {n} (красное) +{fmt(bet)} ₽")
        else:
            u["balance"] -= bet; u["games_lost"] += 1
            send(peer_id, f"🎰 Выпало {n} (чёрное) -{fmt(bet)} ₽")
        save_db()

    elif cmd in ("краш", "crash"):
        try: bet = int(args)
        except: return send(peer_id, "❌ !краш <ставка>")
        if bet < 100 or u["balance"] < bet: return send(peer_id, "💸")
        crash = round(random.uniform(1.0, 10.0), 2)
        if crash >= 2.0:
            win = int(bet * crash)
            u["balance"] += win; u["games_won"] += 1
            send(peer_id, f"📈 Краш {crash}×! Выигрыш: {fmt(win)} ₽")
        else:
            u["balance"] -= bet; u["games_lost"] += 1
            send(peer_id, f"📉 Краш {crash}× — проигрыш -{fmt(bet)} ₽")
        save_db()

    elif cmd in ("угадай", "guess"):
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌ !угадай <число 1-10> <ставка>")
        try: guess, bet = int(p[0]), int(p[1])
        except: return send(peer_id, "❌ Числа")
        if bet < 100 or u["balance"] < bet: return send(peer_id, "💸")
        num = random.randint(1, 10)
        if guess == num:
            win = bet * 5
            u["balance"] += win; u["games_won"] += 1
            send(peer_id, f"🎯 Угадал! Было {num}. +{fmt(win)} ₽")
        else:
            u["balance"] -= bet; u["games_lost"] += 1
            send(peer_id, f"🎯 Мимо. Было {num}. -{fmt(bet)} ₽")
        save_db()

    elif cmd in ("кнб", "rps"):
        if args.lower() not in ("камень", "ножницы", "бумага"):
            return send(peer_id, "❌ !кнб <камень/ножницы/бумага>")
        bot_choice = random.choice(["камень", "ножницы", "бумага"])
        wins = {"камень": "ножницы", "ножницы": "бумага", "бумага": "камень"}
        if args.lower() == bot_choice:
            send(peer_id, f"🤝 Ничья! Бот выбрал {bot_choice}")
        elif wins[args.lower()] == bot_choice:
            win = 100; u["balance"] += win; u["games_won"] += 1
            save_db(); send(peer_id, f"✅ Победа! Бот: {bot_choice}. +{fmt(win)} ₽")
        else:
            lose = 100; u["balance"] -= lose; u["games_lost"] += 1
            save_db(); send(peer_id, f"❌ Проигрыш. Бот: {bot_choice}. -{fmt(lose)} ₽")

    elif cmd in ("дуэль", "duel"):
        tg = extract_user(args)
        if not tg or tg == user_id: return send(peer_id, "❌ !дуэль @id123")
        tt = get_user(tg)
        bet = 500
        if u["balance"] < bet or tt["balance"] < bet:
            return send(peer_id, f"💸 Нужно {fmt(bet)} ₽ у обоих")
        u["balance"] -= bet; tt["balance"] -= bet
        if random.choice([True, False]):
            u["balance"] += bet * 2; u["games_won"] += 1
            send(peer_id, f"⚔️ Ты победил [id{tg}]! +{fmt(bet*2)} ₽")
        else:
            tt["balance"] += bet * 2; u["games_lost"] += 1
            send(peer_id, f"⚔️ [id{tg}] победил тебя!")
        save_db()

    elif cmd in ("лотерея", "lottery"):
        if u["balance"] < 100: return send(peer_id, "💸 Билет 100 ₽")
        u["balance"] -= 100
        ticket = random.randint(100000, 999999)
        win = random.randint(1, 100)
        if win <= 5:
            prize = random.randint(10000, 100000)
            u["balance"] += prize
            send(peer_id, f"🎟️ Билет #{ticket}\n🎉 ВЫИГРЫШ {fmt(prize)} ₽!")
        else:
            send(peer_id, f"🎟️ Билет #{ticket}\n😔 Не повезло")
        save_db()

    elif cmd in ("колесо", "wheel", "spin"):
        if time.time() - u["spin_time"] < 3600:
            mins = int((3600 - (time.time() - u["spin_time"])) // 60)
            return send(peer_id, f"⏳ Крути через {mins} мин.")
        prizes = [100, 500, 1000, 5000, 10000, 50000, 100000, 0]
        win = random.choice(prizes)
        u["balance"] += win; u["spin_time"] = int(time.time())
        save_db()
        send(peer_id, f"🎡 Колесо крутится...\nВыпало: {fmt(win)} ₽!")

    elif cmd in ("коины", "coins"):
        if u["balance"] < 10: return send(peer_id, "💸 10 ₽ за монетку")
        u["balance"] -= 10
        result = random.choice(["Орёл", "Решка"])
        save_db(); send(peer_id, f"🪙 {result}!")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  СОЦИАЛ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif cmd in ("репа", "rep", "репутация"):
        tg = extract_user(args)
        if not tg or tg == user_id: return send(peer_id, "❌ !репа @id123")
        tt = get_user(tg)
        tt["reputation"] += 1
        save_db(); send(peer_id, f"⭐ +1 репутация [id{tg}] (всего: {tt['reputation']})")

    elif cmd in ("брак", "marry", "свадьба"):
        tg = extract_user(args)
        if not tg or tg == user_id: return send(peer_id, "❌ !брак @id123")
        if u["married_to"] or get_user(tg)["married_to"]:
            return send(peer_id, "💔 Кто-то уже женат")
        if u["balance"] < 50000: return send(peer_id, "💸 Свадьба стоит 50000 ₽")
        u["balance"] -= 50000
        u["married_to"] = tg; get_user(tg)["married_to"] = user_id
        save_db(); send(peer_id, f"💍 [id{user_id}] и [id{tg}] теперь семья!")

    elif cmd in ("развод", "divorce"):
        if not u["married_to"]: return send(peer_id, "Ты не женат")
        get_user(u["married_to"])["married_to"] = 0
        u["married_to"] = 0; save_db()
        send(peer_id, "💔 Развод оформлен")

    elif cmd in ("друзья", "friends"):
        if not u["friends"]: return send(peer_id, "👥 Список друзей пуст")
        txt = "👥 Друзья:\n"
        for f in u["friends"]: txt += f"• [id{f}]\n"
        send(peer_id, txt)

    elif cmd in ("добавитьдруга", "addfriend"):
        tg = extract_user(args)
        if tg and tg not in u["friends"]:
            u["friends"].append(tg); save_db()
            send(peer_id, f"✅ [id{tg}] добавлен в друзья")

    elif cmd in ("подарить", "gift"):
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌ !подарить @id123 сумма")
        tg = extract_user(p[0])
        try: amt = int(p[1])
        except: return send(peer_id, "❌ Сумма")
        if amt < 100 or u["balance"] < amt: return send(peer_id, "💸")
        u["balance"] -= amt; get_user(tg)["balance"] += amt
        save_db(); send(peer_id, f"🎁 Подарено {fmt(amt)} ₽ [id{tg}]")

    elif cmd in ("клан", "clan"):
        if u["clan_id"] == 0: return send(peer_id, "Ты не в клане. !создатьклан <название>")
        clan = DB["clans"].get(str(u["clan_id"]), {})
        send(peer_id, f"🏰 Клан: {clan.get('name', '?')}\n💰 Казна: {fmt(clan.get('balance', 0))} ₽")

    elif cmd in ("создатьклан", "createclan"):
        name = args.strip()
        if not name: return send(peer_id, "❌ !создатьклан <название>")
        if u["balance"] < 100000: return send(peer_id, "💸 Нужно 100000 ₽")
        if u["clan_id"] != 0: return send(peer_id, "Ты уже в клане")
        u["balance"] -= 100000
        clan_id = len(DB["clans"]) + 1
        DB["clans"][str(clan_id)] = {"name": name, "owner": user_id, "balance": 0, "members": [user_id]}
        u["clan_id"] = clan_id; save_db()
        send(peer_id, f"🏰 Клан «{name}» создан!")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  ПРОФИЛЬ / СТАТА
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif cmd in ("профиль", "profile", "я"):
        warns_bar = "⚠️" * t["warns"] + "⚪" * max(0, 3 - t["warns"])
        title = ""
        for tn, tv in sorted(TITLES.items(), key=lambda x: x[1], reverse=True):
            if t["balance"] >= tv: title = tn.capitalize(); break
        send(peer_id,
            f"👤 𝗣𝗿𝗼𝗳𝗶𝗹𝗲 • [id{target_id}|{get_name(target_id)}]\n\n"
            f"💰 {fmt(t['balance'])} ₽\n"
            f"🏦 {fmt(t['bank'])} ₽\n"
            f"📊 Уровень {t['level']} ({t['xp']} XP)\n"
            f"⭐ Репутация: {t['reputation']}\n"
            f"🏆 Титул: {title or 'Новичок'}\n"
            f"🏢 {t['business'] or '—'}\n"
            f"🚗 {t['car'] or '—'} | 🏠 {t['house'] or '—'}\n"
            f"🐾 {t['pet'] or '—'}\n"
            f"⚔️ Побед: {t['games_won']} | Поражений: {t['games_lost']}\n"
            f"⚠️ Варны: {warns_bar} ({t['warns']}/3)\n"
            f"💬 Сообщений: {t['messages_count']}",
            get_kb())

    elif cmd in ("топ", "top"):
        rows = sorted(DB["users"].items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
        txt = "🏆 𝗧𝗼𝗽-10\n\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, d) in enumerate(rows, 1):
            m = medals[i-1] if i <= 3 else f"{i}."
            txt += f"{m} [id{uid}|{get_name(int(uid))}] — {fmt(d['balance'])} ₽\n"
        send(peer_id, txt)

    elif cmd in ("топ уровень", "toplevel"):
        rows = sorted(DB["users"].items(), key=lambda x: x[1]["level"], reverse=True)[:10]
        txt = "📊 𝗧𝗼𝗽 𝗽𝗼 𝘂𝗿𝗼𝘃𝗻𝘆\n\n"
        for i, (uid, d) in enumerate(rows, 1):
            txt += f"{i}. [id{uid}] — уровень {d['level']}\n"
        send(peer_id, txt)

    elif cmd in ("стата", "stats", "статистика"):
        total_balance = sum(d["balance"] for d in DB["users"].values())
        total_msgs = sum(d["messages_count"] for d in DB["users"].values())
        send(peer_id,
            f"📊 𝗦𝘁𝗮𝘁𝗶𝘀𝘁𝗶𝗰𝘀\n\n"
            f"👥 Пользователей: {fmt(len(DB['users']))}\n"
            f"💰 Всего денег: {fmt(total_balance)} ₽\n"
            f"💬 Сообщений: {fmt(total_msgs)}\n"
            f"🎁 Промокодов: {len(DB['promo'])}\n"
            f"🏰 Кланов: {len(DB.get('clans', {}))}")

    elif cmd in ("титул", "title"):
        n = args.lower().strip()
        if n not in TITLES:
            return send(peer_id, "❌ Титулы: " + ", ".join(TITLES.keys()))
        if u["balance"] < TITLES[n]:
            return send(peer_id, f"💸 Нужно {fmt(TITLES[n])} ₽")
        u["balance"] -= TITLES[n]; u["title"] = n
        save_db(); send(peer_id, f"🏆 Титул «{n}» установлен!")

    elif cmd in ("достижения", "achievements", "ачивки"):
        if not u["achievements"]:
            return send(peer_id, "🏅 Достижений пока нет")
        txt = "🏅 𝗔𝗰𝗵𝗶𝗲𝘃𝗲𝗺𝗲𝗻𝘁𝘀\n\n"
        for a in u["achievements"]: txt += f"• {a}\n"
        send(peer_id, txt)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  ПРОМОКОДЫ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif cmd in ("активировать", "промо", "promo", "promocode"):
        code = args.upper().strip()
        if not code: return send(peer_id, "❌ !активировать <код>")
        if code not in DB["promo"]: return send(peer_id, "❌ Промо не найден")
        p = DB["promo"][code]
        if p["uses_left"] <= 0: return send(peer_id, "❌ Исчерпан")
        if p["reward_type"] == "balance":
            u["balance"] += int(p["reward_value"])
            msg = f"💰 +{fmt(p['reward_value'])} ₽"
        elif p["reward_type"] == "business":
            u["business"] = p["reward_value"]
            msg = f"🏢 Бизнес: {p['reward_value']}"
        elif p["reward_type"] == "level":
            u["level"] = int(p["reward_value"]); u["xp"] = u["level"] ** 2
            msg = f"📊 Уровень {p['reward_value']}"
        p["uses_left"] -= 1; save_db()
        send(peer_id, f"🎁 Активировано: {msg}")

    elif cmd in ("списокпромо", "promos"):
        if not DB["promo"]: return send(peer_id, "🎁 Промокодов нет")
        txt = "🎁 𝗣𝗿𝗼𝗺𝗼\n\n"
        for code, p in DB["promo"].items():
            txt += f"• {code} — {p['reward_type']} {p['reward_value']} ({p['uses_left']} ост.)\n"
        send(peer_id, txt)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  РАЗВЛЕЧЕНИЯ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif cmd in ("анекдот", "joke"):
        jokes = [
            "— Почему программисты путают Хэллоуин и Рождество?\n— Потому что Oct 31 == Dec 25",
            "Заходит улитка в бар, бармен её выгоняет. Через год улитка возвращается: 'Зачем ты так со мной?'",
            "— Сири, почему я одинок?\n— *открывает фронтальную камеру*",
            "Жена программиста: 'Сходи в магазин, купи батон хлеба. Если будут яйца — возьми десяток.'\nПрограммист вернулся с 10 батонами."
        ]
        send(peer_id, "😄 " + random.choice(jokes))

    elif cmd in ("факт", "fact"):
        facts = [
            "Мёд никогда не портится. Археологи находили съедобный мёд в гробницах фараонов.",
            "Осьминоги имеют три сердца и голубую кровь.",
            "Бананы — это ягоды, а клубника — нет.",
            "В среднем человек проводит 6 месяцев жизни, ожидая зелёного света.",
            "Сердце креветки находится в её голове."
        ]
        send(peer_id, "🧠 " + random.choice(facts))

    elif cmd in ("цитата", "quote"):
        quotes = [
            "«Будь собой; прочие роли уже заняты.» — Оскар Уайльд",
            "«Единственный способ делать великие дела — любить то, что делаешь.» — Стив Джобс",
            "«Будущее принадлежит тем, кто верит в красоту своих мечтаний.» — Элеонора Рузвельт"
        ]
        send(peer_id, random.choice(quotes))

    elif cmd in ("8ball", "шар", "предсказание"):
        answers = ["Да", "Нет", "Возможно", "Точно да", "Точно нет", "Спроси позже", "Звёзды молчат", "100%"]
        send(peer_id, f"🎱 {random.choice(answers)}")

    elif cmd in ("погода", "weather"):
        send(peer_id, f"🌤️ Погода: {random.choice(['☀️ Ясно', '⛅ Облачно', '🌧️ Дождь', '❄️ Снег'])}, {random.randint(-10, 30)}°C")

    elif cmd in ("совместимость", "compat"):
        tg = extract_user(args)
        if not tg: return send(peer_id, "❌ !совместимость @id123")
        pct = random.randint(0, 100)
        send(peer_id, f"💕 Совместимость [id{user_id}] и [id{tg}]: {pct}%")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  МОДЕРАЦИЯ (для админов беседы)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif cmd in ("варн", "warn"):
        if not is_admin(user_id): return send(peer_id, "🚫 Только админ бота")
        tg = extract_user(args)
        if not tg: return send(peer_id, "❌ !варн @id123")
        tt = get_user(tg); tt["warns"] += 1; save_db()
        send(peer_id, f"⚠️ [id{tg}] получил варн ({tt['warns']}/3)")
        if tt["warns"] >= 3:
            tt["muted_until"] = int(time.time()) + 3600; tt["warns"] = 0; save_db()
            send(peer_id, f"🚫 [id{tg}] мут 1ч за 3 варна")

    elif cmd in ("мут", "mute"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split(); tg = extract_user(p[0]) if p else None
        if not tg: return send(peer_id, "❌ !мут @id123 [минуты]")
        mins = int(p[1]) if len(p) > 1 else 60
        get_user(tg)["muted_until"] = int(time.time()) + mins * 60; save_db()
        send(peer_id, f"🔇 [id{tg}] мут {mins} мин")

    elif cmd in ("снятьмут", "unmute"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if tg: get_user(tg)["muted_until"] = 0; save_db(); send(peer_id, f"✅ Мут снят [id{tg}]")

    elif cmd in ("снятьварн", "unwarn"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if tg:
            tt = get_user(tg); tt["warns"] = max(0, tt["warns"] - 1); save_db()
            send(peer_id, f"✅ Варн снят [id{tg}] ({tt['warns']} ост.)")

    elif cmd in ("кик", "kick", "бан", "ban"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if not tg: return send(peer_id, "❌ !кик @id123")
        try:
            vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=tg)
            send(peer_id, f"🔨 [id{tg}] удалён из беседы")
        except Exception as e: send(peer_id, f"❌ {e}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  АДМИН-КОМАНДЫ (только DEVELOPERS)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif cmd in ("выдатьбаланс", "givebalance"):
        if not is_admin(user_id): return send(peer_id, "🚫 Только разработчики бота")
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌ !выдатьбаланс @id123 сумма")
        tg = extract_user(p[0]); amt = int(p[1])
        get_user(tg)["balance"] += amt; save_db()
        send(peer_id, f"✅ Выдано {fmt(amt)} ₽ [id{tg}]")

    elif cmd in ("забратьбаланс", "takebalance"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌ !забратьбаланс @id123 сумма")
        tg = extract_user(p[0]); amt = int(p[1])
        tt = get_user(tg); tt["balance"] = max(0, tt["balance"] - amt); save_db()
        send(peer_id, f"✅ Забрано {fmt(amt)} ₽ у [id{tg}]")

    elif cmd in ("выдатьуровень", "givelevel"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌ !выдатьуровень @id123 уровень")
        tg = extract_user(p[0]); lv = int(p[1])
        tt = get_user(tg); tt["level"] = lv; tt["xp"] = lv * lv; save_db()
        send(peer_id, f"✅ Уровень {lv} выдан [id{tg}]")

    elif cmd in ("выдатьрепу", "giverep"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌ !выдатьрепу @id123 кол-во")
        tg = extract_user(p[0]); amt = int(p[1])
        get_user(tg)["reputation"] += amt; save_db()
        send(peer_id, f"✅ +{amt} репы [id{tg}]")

    elif cmd in ("выдатьбизнес", "givebusiness"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌ !выдатьбизнес @id123 название")
        tg = extract_user(p[0]); biz = p[1].lower()
        if biz in BUSINESSES:
            tt = get_user(tg); tt["business"] = biz; tt["business_time"] = int(time.time()); save_db()
            send(peer_id, f"✅ Бизнес {biz} выдан [id{tg}]")
        else: send(peer_id, "❌ Бизнес не найден. Список: !бизнесы")

    elif cmd in ("забратьбизнес", "takebusiness"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if tg: get_user(tg)["business"] = None; save_db(); send(peer_id, f"✅ Бизнес забран [id{tg}]")

    elif cmd in ("выдатьимущество", "giveproperty"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split()
        if len(p) < 3: return send(peer_id, "❌ !выдатьимущество @id123 тип название\n(тип: car/house/yacht/phone/pet)")
        tg = extract_user(p[0]); typ = p[1].lower(); nm = p[2].lower()
        tt = get_user(tg)
        maps = {"car": CARS, "house": HOUSES, "yacht": YACHTS, "phone": PHONES, "pet": PETS}
        if typ in maps and nm in maps[typ]:
            tt[typ if typ != "car" else "car"] = nm
            if typ == "car": tt["car"] = nm
            elif typ == "house": tt["house"] = nm
            elif typ == "yacht": tt["yacht"] = nm
            elif typ == "phone": tt["phone"] = nm
            elif typ == "pet": tt["pet"] = nm
            save_db(); send(peer_id, f"✅ {nm} выдан [id{tg}]")
        else: send(peer_id, "❌ Не найдено")

    elif cmd in ("обнулить", "reset"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if not tg: return send(peer_id, "❌ !обнулить @id123")
        DB["users"][str(tg)] = {
            "balance": 1000, "bank": 0, "xp": 0, "level": 0, "warns": 0,
            "reputation": 0, "business": None, "business_time": 0, "work_time": 0,
            "bonus_time": 0, "deposit": 0, "deposit_time": 0,
            "car": None, "house": None, "yacht": None, "phone": None,
            "pet": None, "pet_hunger": 100, "pet_happiness": 100,
            "farm": None, "farm_time": 0, "married_to": 0, "clan_id": 0,
            "inventory": {}, "achievements": [], "muted_until": 0,
            "messages_count": 0, "games_won": 0, "games_lost": 0,
            "title": None, "skin": None, "daily_time": 0, "spin_time": 0,
            "friends": [], "banned": False, "nickname": None, "bio": None,
            "last_seen": 0, "register_time": int(time.time())
        }
        save_db(); send(peer_id, f"✅ [id{tg}] полностью обнулён")

    elif cmd in ("админинфо", "admininfo", "инфо"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if not tg: return send(peer_id, "❌ !админинфо @id123")
        tt = get_user(tg)
        send(peer_id,
            f"👤 𝗔𝗱𝗺𝗶𝗻 𝗜𝗻𝗳𝗼 • [id{tg}|{get_name(tg)}]\n\n"
            f"💰 {fmt(tt['balance'])} ₽\n"
            f"🏦 {fmt(tt['bank'])} ₽\n"
            f"📊 Уровень: {tt['level']} ({tt['xp']} XP)\n"
            f"⚠️ Варны: {tt['warns']}/3\n"
            f"⭐ Репутация: {tt['reputation']}\n"
            f"🏢 Бизнес: {tt['business'] or '—'}\n"
            f"🚗 Машина: {tt['car'] or '—'}\n"
            f"🏠 Дом: {tt['house'] or '—'}\n"
            f"🚢 Яхта: {tt['yacht'] or '—'}\n"
            f"📱 Телефон: {tt['phone'] or '—'}\n"
            f"🐾 Питомец: {tt['pet'] or '—'}\n"
            f"🌾 Ферма: {tt['farm'] or '—'}\n"
            f"💍 Женат на: {tt['married_to'] or '—'}\n"
            f"🏰 Клан: {tt['clan_id'] or '—'}\n"
            f"📦 Инвентарь: {len(tt['inventory'])} предметов\n"
            f"⚔️ Побед: {tt['games_won']} | Поражений: {tt['games_lost']}\n"
            f"💬 Сообщений: {tt['messages_count']}\n"
            f"🔇 Мут: {'да' if tt['muted_until'] > time.time() else 'нет'}\n"
            f"📅 Регистрация: {datetime.fromtimestamp(tt['register_time']).strftime('%d.%m.%Y')}")

    elif cmd in ("создатьпромо", "createpromo"):
        if not is_admin(user_id): return send(peer_id, "🚫 Только разработчики бота")
        p = args.split()
        if len(p) < 4:
            return send(peer_id, "❌ !создатьпромо КОД balance|business|level ЗНАЧЕНИЕ КОЛ-ВО\nПример: !создатьпромо VIP2026 balance 10000 50")
        code, rtype, rval, uses = p[0].upper(), p[1], p[2], int(p[3])
        if rtype not in ("balance", "business", "level"):
            return send(peer_id, "❌ Тип: balance / business / level")
        DB["promo"][code] = {"reward_type": rtype, "reward_value": rval, "uses_left": uses, "creator": user_id, "created": int(time.time())}
        save_db()
        send(peer_id, f"✅ Промокод `{code}` создан\nТип: {rtype}\nЗначение: {rval}\nАктиваций: {uses}")

    elif cmd in ("удалитьпромо", "deletepromo"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        code = args.upper().strip()
        if code in DB["promo"]:
            del DB["promo"][code]; save_db()
            send(peer_id, f"✅ Промо {code} удалён")
        else: send(peer_id, "❌ Не найден")

    elif cmd in ("добавитьадмина", "addadmin"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if tg and tg not in DEVELOPERS:
            DEVELOPERS.append(tg)
            os.environ["DEVELOPERS"] = ",".join(map(str, DEVELOPERS))
            send(peer_id, f"✅ [id{tg}] теперь админ бота")
        else: send(peer_id, "❌")

    elif cmd in ("списокадминов", "admins"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        txt = "👑 Админы бота:\n"
        for a in DEVELOPERS: txt += f"• [id{a}]\n"
        send(peer_id, txt)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  НЕИЗВЕСТНАЯ КОМАНДА
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    else:
        # Молча игнорируем, чтобы не спамить
        pass


# ═══════════════════════════════════════
#  ГЛАВНЫЙ ЦИКЛ
# ═══════════════════════════════════════
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.text:
        # Работаем в личке и беседах
        if not (event.from_user or event.from_chat):
            continue

        peer_id = event.peer_id
        user_id = event.user_id
        text = event.text.strip()

        # Проверка мута
        u = get_user(user_id)
        if u["muted_until"] > time.time():
            try:
                vk.messages.delete(peer_id=peer_id, message_ids=event.message_id, delete_for_all=1)
            except: pass
            continue

        # XP и уровень
        u["xp"] += 5
        u["messages_count"] += 1
        u["last_seen"] = int(time.time())
        nl = int(u["xp"] ** 0.5)
        if nl > u["level"]:
            u["level"] = nl
            if event.from_user:  # Только в личку, чтобы не спамить
                send(peer_id, f"🎉 Уровень {nl}!")
        save_db()

        # Парсинг команды
        if not text.lower().startswith(PREFIX):
            continue

        # Убираем префикс и разбиваем
        rest = text[1:].strip()
        parts = rest.split(maxsplit=1)
        cmd = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""

        try:
            handle(peer_id, user_id, cmd, args)
        except Exception as e:
            print(f"ERROR [{cmd}]:", e)
            traceback.print_exc()
            send(peer_id, f"❌ Ошибка команды: {e}")
