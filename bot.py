import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json, time, os, re, random, threading, traceback

TOKEN = os.environ.get("VK_TOKEN", "")
OWNER_ID = 734176092
DEVELOPERS = [int(x) for x in os.environ.get("DEVELOPERS", "734176092").split(",") if x]
if OWNER_ID not in DEVELOPERS: DEVELOPERS.append(OWNER_ID)
PREFIX = "!"
MAT_WORDS = ["хуй", "пизд", "ебан", "бляд", "сука", "долбо"]
if not TOKEN:
    print("NO TOKEN"); raise SystemExit(1)
print("OK owner:", OWNER_ID)

DB_FILE = "db.json"
def load_db():
    if not os.path.exists(DB_FILE): return {"users":{}, "promo":{}, "clans":{}}
    with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(DB, f, ensure_ascii=False)
DB = load_db()

NEW_USER = {"balance":1000,"bank":0,"donate":0,"xp":0,"level":0,"warns":0,"reputation":0,
"business":None,"business_time":0,"work_time":0,"daily_time":0,"deposit":0,"deposit_time":0,
"car":None,"house":None,"yacht":None,"phone":None,"pet":None,"pet_hunger":100,
"pet_happiness":100,"farm":None,"farm_time":0,"married_to":0,"clan_id":0,"inventory":{},
"achievements":[],"muted_until":0,"messages_count":0,"games_won":0,"games_lost":0,
"title":None,"spin_time":0,"friends":[],"mat_count":0,"register_time":0}

def get_user(uid):
    s = str(uid)
    if s not in DB["users"]:
        d = dict(NEW_USER); d["register_time"] = int(time.time())
        DB["users"][s] = d; save_db()
    return DB["users"][s]
def extract_user(t):
    m = re.search(r"(?:@id|id|vk\.com/)(\d+)", str(t))
    return int(m.group(1)) if m else None
def is_admin(u): return u in DEVELOPERS
def is_owner(u): return u == OWNER_ID
def fmt(n):
    try: return f"{int(n):,}".replace(",", " ")
    except: return str(n)

BUSINESSES = {"ларёк":(10000,800),"кафе":(50000,4500),"магазин":(200000,20000),"ресторан":(750000,80000),"завод":(2500000,280000),"банк":(10000000,1200000),"нефтянка":(50000000,6500000),"космодром":(200000000,30000000)}
CARS = {"велик":5000,"самокат":15000,"жигуль":80000,"тойота":500000,"бмв":2000000,"мерседес":5000000,"ламборгини":25000000,"бугатти":100000000}
HOUSES = {"палатка":10000,"квартира":250000,"дом":1500000,"особняк":15000000,"замок":100000000,"остров":500000000}
YACHTS = {"лодка":50000,"катер":500000,"яхта":10000000,"мега-яхта":100000000}
PHONES = {"нокия":5000,"xiaomi":25000,"iphone":150000,"samsung":300000}
PETS = {"кот":50000,"собака":75000,"попугай":30000,"дракон":5000000}
FARMS = {"огород":100000,"теплица":500000,"ранчо":2000000}
CASES = {"деревянный":(1000,500,5000),"железный":(10000,5000,50000),"золотой":(100000,50000,500000),"платиновый":(1000000,500000,5000000),"алмазный":(10000000,5000000,50000000)}
MINE = {"камень":(10,100),"уголь":(50,300),"железо":(200,1000),"серебро":(1000,5000),"золото":(5000,25000),"алмаз":(25000,150000)}
FISH = {"карась":(5,50),"окунь":(20,150),"щука":(100,800),"сом":(500,3000),"осётр":(3000,20000),"золотая рыбка":(50000,250000)}
HUNT = {"заяц":(100,500),"лиса":(500,2000),"волк":(2000,8000),"медведь":(10000,50000),"тигр":(50000,250000)}
TITLES = {"новичок":0,"работяга":100000,"бизнесмен":1000000,"олигарх":10000000,"магнат":100000000,"легенда":1000000000}
ACHIEVES = {"first_msg":("💬 Первое сообщение", lambda u: u["messages_count"] >= 1),
"rich":("💰 Миллионер", lambda u: u["balance"] >= 1000000),
"lvl10":("📊 10 уровень", lambda u: u["level"] >= 10),
"lvl25":("📊 25 уровень", lambda u: u["level"] >= 25),
"gamer":("🎮 10 побед", lambda u: u["games_won"] >= 10),
"collector":("📦 Коллекционер", lambda u: sum(u["inventory"].values()) >= 10),
"married":("💍 В браке", lambda u: u["married_to"] != 0),
"boss":("🏢 Бизнесмен", lambda u: u["business"] is not None)}

def check_achieves(u):
    got = []
    for k, (name, cond) in ACHIEVES.items():
        if k not in u["achievements"]:
            try:
                if cond(u): u["achievements"].append(k); got.append(name)
            except: pass
    return got

try:
    from flask import Flask
    app = Flask("")
    @app.route("/")
    def home(): return "Astra alive!"
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080), daemon=True).start()
    print("Flask :8080")
except Exception as e: print("Flask err:", e)

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

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
def get_admin_kb():
    kb = VkKeyboard(one_time=False)
    kb.add_button("👑 Админинфо", color=VkKeyboardColor.PRIMARY)
    kb.add_button("💵 Выдать баланс", color=VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_button("💎 Выдать донат", color=VkKeyboardColor.POSITIVE)
    kb.add_button("🎁 Создать промо", color=VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_button("⚠️ Варн", color=VkKeyboardColor.NEGATIVE)
    kb.add_button("🔇 Мут", color=VkKeyboardColor.NEGATIVE)
    kb.add_line()
    kb.add_button("🔄 Обнулить", color=VkKeyboardColor.NEGATIVE)
    kb.add_button("◀️ Назад", color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()
BUTTON_CMDS = {"💰 Баланс":"баланс","Баланс":"баланс","💼 Работа":"работа","Работа":"работа",
"🏢 Бизнесы":"бизнесы","Бизнесы":"бизнесы","🎮 Игры":"игры","Игры":"игры",
"👤 Профиль":"профиль","Профиль":"профиль","📋 Помощь":"помощь","Помощь":"помощь",
"🎰 Казино 100":"казино","🪙 Монетка 100":"монетка","🎲 Кости 100":"кости",
"🎡 Колесо":"колесо","⛏️ Шахта":"шахта","🎣 Рыбалка":"рыбалка",
"👑 Админинфо":"h_info","💵 Выдать баланс":"h_bal","💎 Выдать донат":"h_don",
"🎁 Создать промо":"h_promo","⚠️ Варн":"h_warn","🔇 Мут":"h_mute",
"🔄 Обнулить":"h_reset","◀️ Назад":"назад","Назад":"назад"}

def send(peer_id, msg, kb=None):
    kw = {"peer_id":peer_id, "message":str(msg), "random_id":0}
    kw["keyboard"] = kb if kb else get_kb()
    try: vk.messages.send(**kw)
    except Exception as e: print("Send err:", e)

HELP = ("🌟 Astra v9 ИМБА\n\n💰 !баланс !работа !бонус !бизнесы !купить !продать !доход !банк !положить !снять !депозит !забрать !перевод !донат\n"
"🏪 !машины !дома !яхты !телефоны !питомцы !фермы !кейсы !кейс <имя> !инвентарь\n"
"⛏️ !шахта !рыбалка !охота !ферма !покормить !поиграть\n"
"🎮 !казино !монетка !кости !рулетка !краш !угадай !кнб !дуэль !лотерея !колесо\n"
"💍 !репа @id !брак @id !развод !друзья !подарить @id сумма !клан !создатьклан имя\n"
"👤 !профиль !топ !топуровень !стата !титул имя !достижения\n"
"🎁 !активировать КОД\n😄 !анекдот !факт !цитата !шар !погода !совместимость @id\n"
"🛡️ !варн !мут !снятьмут !снятьварн !кик\n"
"👑 !админка !админинфо @id !выдатьбаланс !забратьбаланс !выдатьдонат !забратьдонат !выдатьуровень !выдатьрепу !выдатьбизнес !забратьбизнес !выдатьимущество !обнулить !создатьпромо !удалитьпромо !списокпромо !добавитьадмина !списокадминов !рассылка текст")

def handle(peer_id, user_id, cmd, args):
    u = get_user(user_id)
    tid = extract_user(args) or user_id
    t = get_user(tid)
    hints = {"h_info":"!админинфо @id","h_bal":"!выдатьбаланс @id сумма","h_don":"!выдатьдонат @id сумма","h_promo":"!создатьпромо КОД balance 10000 50","h_warn":"!варн @id","h_mute":"!мут @id 60","h_reset":"!обнулить @id"}
    if cmd in hints:
        if not is_admin(user_id): return send(peer_id, "🚫")
        return send(peer_id, "👑 Введи: "+hints[cmd], get_admin_kb())
    if cmd in ("игры","games"): return send(peer_id, "🎮 Игры:", get_games_kb())
    if cmd == "назад": return send(peer_id, "📋 Меню:", get_kb())
    if cmd in ("админка","admin","панель"):
        if not is_admin(user_id): return send(peer_id, "🚫 Только админы")
        return send(peer_id, f"👑 ПАНЕЛЬ\nСтатус: {'ВЛАДЕЛЕЦ' if is_owner(user_id) else 'Админ'}", get_admin_kb())
    if cmd in ("помощь","help","команды"):
        return send(peer_id, HELP, get_admin_kb() if is_admin(user_id) else get_kb())
    if cmd in ("о боте","about"):
        return send(peer_id, f"🌟 Astra v9\n👑 [id{OWNER_ID}]\n👥 {len(DB['users'])} 🎁 {len(DB['promo'])} 🏰 {len(DB['clans'])}")
    if cmd in ("баланс","balance"):
        cr = "\n👑 ВЛАДЕЛЕЦ" if tid == OWNER_ID else ""
        return send(peer_id, f"💰 [id{tid}|]{cr}\n💵 {fmt(t['balance'])} ₽\n🏦 {fmt(t['bank'])} ₽\n💎 {fmt(t['donate'])}\n📊 Ур.{t['level']} ({t['xp']} XP)\n⭐ {t['reputation']}\n🏢 {t['business'] or '—'}\n🚗 {t['car'] or '—'} | 🏠 {t['house'] or '—'}\n⚠️ {t['warns']}/3 | 💬 {t['messages_count']}", get_kb())
    if cmd in ("донат","donate"): return send(peer_id, f"💎 Донат: {fmt(u['donate'])}")
    if cmd in ("работа","work"):
        if time.time()-u["work_time"] < 1800: return send(peer_id, f"⏳ {int((1800-(time.time()-u['work_time']))//60)} мин.")
        e = 200+u["level"]*20+random.randint(0,100)
        u["balance"] += e; u["work_time"] = int(time.time()); save_db()
        return send(peer_id, f"💼 +{fmt(e)} ₽")
    if cmd in ("бонус","bonus","ежедневка","daily"):
        if time.time()-u["daily_time"] < 86400: return send(peer_id, f"⏳ {int((86400-(time.time()-u['daily_time']))//3600)} ч.")
        b = 500+u["level"]*100
        u["balance"] += b; u["daily_time"] = int(time.time()); save_db()
        return send(peer_id, f"🎁 +{fmt(b)} ₽")
    if cmd in ("бизнесы","businesses"):
        return send(peer_id, "🏢\n"+"\n".join(f"• {n} {fmt(p[0])} ₽ ({fmt(p[1])}/ч)" for n,p in BUSINESSES.items())+"\n!купить <имя>")
    if cmd in ("купить","buy"):
        n = args.lower().strip()
        for key, d in [("business",BUSINESSES),("car",CARS),("house",HOUSES),("yacht",YACHTS),("phone",PHONES),("pet",PETS),("farm",FARMS)]:
            if n in d:
                price = d[n][0] if isinstance(d[n], tuple) else d[n]
                if key == "business" and u["business"]: return send(peer_id, "Уже есть бизнес")
                if u["balance"] < price: return send(peer_id, "💸")
                u["balance"] -= price
                if key == "business": u["business"] = n; u["business_time"] = int(time.time())
                else: u[key] = n
                save_db(); return send(peer_id, f"🎉 Куплено: {n}")
        return send(peer_id, "❌ !машины !дома !яхты !телефоны !питомцы !фермы")
    if cmd in ("продать","sell"):
        n = args.lower().strip()
        mp = {"бизнес":("business",BUSINESSES),"машина":("car",CARS),"дом":("house",HOUSES)}
        if n in mp and u[mp[n][0]]:
            key, d = mp[n]
            p = (d[u[key]][0] if isinstance(d[u[key]], tuple) else d[u[key]])//2
            u["balance"] += p; u[key] = None; save_db()
            return send(peer_id, f"💰 +{fmt(p)} ₽")
        return send(peer_id, "❌")
    if cmd in ("доход","income"):
        if not u["business"]: return send(peer_id, "Нет бизнеса")
        hh = int((time.time()-u["business_time"])//3600)
        if hh < 1: return send(peer_id, "Рано")
        e = BUSINESSES[u["business"]][1]*hh
        u["balance"] += e; u["business_time"] = int(time.time()); save_db()
        return send(peer_id, f"💵 +{fmt(e)} ₽")
    if cmd in ("банк","bank"):
        return send(peer_id, f"🏦 💵{fmt(u['balance'])} 🏦{fmt(u['bank'])} 📈{fmt(u['deposit'])}\n!положить !снять !депозит !забрать")
    if cmd in ("положить","put"):
        try: a = int(args)
        except: return send(peer_id, "❌")
        if a > u["balance"]: return send(peer_id, "💸")
        u["balance"] -= a; u["bank"] += a; save_db(); return send(peer_id, f"🏦 +{fmt(a)}")
    if cmd in ("снять","withdraw"):
        try: a = int(args)
        except: return send(peer_id, "❌")
        if a > u["bank"]: return send(peer_id, "💸")
        u["bank"] -= a; u["balance"] += a; save_db(); return send(peer_id, f"🏦 -{fmt(a)}")
    if cmd in ("депозит","deposit"):
        try: a = int(args)
        except: return send(peer_id, "❌")
        if a < 1000 or u["balance"] < a: return send(peer_id, "💸 мин 1000")
        u["balance"] -= a; u["deposit"] += a; u["deposit_time"] = int(time.time()); save_db()
        return send(peer_id, f"📈 {fmt(a)} (5%/ч)")
    if cmd in ("забрать","claim"):
        hh = int((time.time()-u["deposit_time"])//3600)
        i = int(u["deposit"]*0.05*hh); tot = u["deposit"]+i
        u["balance"] += tot; u["deposit"] = 0; save_db()
        return send(peer_id, f"💰 +{fmt(tot)} (проценты {fmt(i)})")
    if cmd in ("перевод","transfer"):
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌ !перевод @id сумма")
        tg = extract_user(p[0])
        try: a = int(p[1])
        except: return send(peer_id, "❌")
        if a < 100 or u["balance"] < a: return send(peer_id, "💸")
        tax = int(a*0.05)
        u["balance"] -= a; get_user(tg)["balance"] += a-tax; save_db()
        return send(peer_id, f"✅ {fmt(a-tax)} ₽ (налог {fmt(tax)})")
    if cmd in ("машины","cars"): return send(peer_id, "🚗 "+" | ".join(CARS.keys()))
    if cmd in ("дома","houses"): return send(peer_id, "🏠 "+" | ".join(HOUSES.keys()))
    if cmd in ("яхты","yachts"): return send(peer_id, "🚢 "+" | ".join(YACHTS.keys()))
    if cmd in ("телефоны","phones"): return send(peer_id, "📱 "+" | ".join(PHONES.keys()))
    if cmd in ("питомцы","pets"): return send(peer_id, "🐾 "+" | ".join(PETS.keys()))
    if cmd in ("фермы","farms"): return send(peer_id, "🌾 "+" | ".join(FARMS.keys()))
    if cmd in ("кейсы","cases"): return send(peer_id, "🎁 "+" | ".join(f"{n}:{fmt(c[0])}" for n,c in CASES.items()))
    if cmd in ("кейс","case"):
        n = args.lower().strip()
        if n not in CASES: return send(peer_id, "❌ "+", ".join(CASES.keys()))
        c = CASES[n]
        if u["balance"] < c[0]: return send(peer_id, "💸")
        u["balance"] -= c[0]; w = random.randint(c[1], c[2]); u["balance"] += w
        it = random.choice(list(MINE.keys())+list(FISH.keys()))
        u["inventory"][it] = u["inventory"].get(it,0)+1; save_db()
        return send(peer_id, f"🎁 +{fmt(w)} ₽ и {it}")
    if cmd in ("инвентарь","inventory"):
        if not u["inventory"]: return send(peer_id, "📦 Пусто")
        return send(peer_id, "📦\n"+"\n".join(f"• {i} ×{c}" for i,c in u["inventory"].items()))
    if cmd in ("шахта","mine"):
        it,(a,b) = random.choice(list(MINE.items())); e = random.randint(a,b)
        u["balance"] += e; u["inventory"][it] = u["inventory"].get(it,0)+1; save_db()
        return send(peer_id, f"⛏️ {it} +{fmt(e)}")
    if cmd in ("рыбалка","fish"):
        it,(a,b) = random.choice(list(FISH.items())); e = random.randint(a,b)
        u["balance"] += e; u["inventory"][it] = u["inventory"].get(it,0)+1; save_db()
        return send(peer_id, f"🎣 {it} +{fmt(e)}")
    if cmd in ("охота","hunt"):
        it,(a,b) = random.choice(list(HUNT.items())); e = random.randint(a,b)
        u["balance"] += e; u["inventory"][it] = u["inventory"].get(it,0)+1; save_db()
        return send(peer_id, f"🏹 {it} +{fmt(e)}")
    if cmd in ("ферма","farm"):
        if not u["farm"]: return send(peer_id, "!фермы")
        hh = int((time.time()-u["farm_time"])//3600)
        if hh < 1: return send(peer_id, "Рано")
        e = {"огород":5000,"теплица":25000,"ранчо":100000}[u["farm"]]*hh
        u["balance"] += e; u["farm_time"] = int(time.time()); save_db()
        return send(peer_id, f"🌾 +{fmt(e)}")
    if cmd in ("покормить","feed"):
        if not u["pet"]: return send(peer_id, "Нет питомца")
        if u["balance"] < 500: return send(peer_id, "💸")
        u["balance"] -= 500; u["pet_hunger"] = min(100,u["pet_hunger"]+30); save_db()
        return send(peer_id, f"🍖 сытость {u['pet_hunger']}%")
    if cmd in ("поиграть","playpet"):
        if not u["pet"]: return send(peer_id, "Нет питомца")
        u["pet_happiness"] = min(100,u["pet_happiness"]+30); save_db()
        return send(peer_id, f"🎾 счастье {u['pet_happiness']}%")
    if cmd in ("монетка","coin"):
        bet = int(args) if args else 100
        if bet < 50 or u["balance"] < bet: return send(peer_id, "💸")
        if random.choice([1,0]):
            u["balance"] += bet; u["games_won"] += 1; save_db(); return send(peer_id, f"🪙 Орёл +{fmt(bet)}")
        u["balance"] -= bet; u["games_lost"] += 1; save_db(); return send(peer_id, f"🪙 Решка -{fmt(bet)}")
    if cmd in ("казино","slots","casino"):
        bet = int(args) if args else 100
        if bet < 100 or u["balance"] < bet: return send(peer_id, "💸")
        s = [random.choice(["🍒","🍋","🔔","⭐","7"]) for _ in range(3)]
        if s[0]==s[1]==s[2]:
            m = 10 if s[0]=="7" else 5
            u["balance"] += bet*m; u["games_won"] += 1; save_db(); return send(peer_id, f"{''.join(s)} ДЖЕКПОТ +{fmt(bet*m)}")
        if s[0]==s[1] or s[1]==s[2]:
            u["balance"] += bet; u["games_won"] += 1; save_db(); return send(peer_id, f"{''.join(s)} +{fmt(bet)}")
        u["balance"] -= bet; u["games_lost"] += 1; save_db(); return send(peer_id, f"{''.join(s)} -{fmt(bet)}")
    if cmd in ("кости","dice"):
        bet = int(args) if args else 100
        if bet < 100 or u["balance"] < bet: return send(peer_id, "💸")
        d = random.randint(1,6)
        if d >= 4:
            u["balance"] += bet; u["games_won"] += 1; save_db(); return send(peer_id, f"🎲 {d} +{fmt(bet)}")
        u["balance"] -= bet; u["games_lost"] += 1; save_db(); return send(peer_id, f"🎲 {d} -{fmt(bet)}")
    if cmd in ("рулетка","roulette"):
        bet = int(args) if args else 100
        if bet < 100 or u["balance"] < bet: return send(peer_id, "💸")
        n = random.randint(0,36)
        if n and n % 2 == 0:
            u["balance"] += bet; u["games_won"] += 1; save_db(); return send(peer_id, f"🎰 {n} +{fmt(bet)}")
        u["balance"] -= bet; u["games_lost"] += 1; save_db(); return send(peer_id, f"🎰 {n} -{fmt(bet)}")
    if cmd in ("краш","crash"):
        bet = int(args) if args else 100
        if bet < 100 or u["balance"] < bet: return send(peer_id, "💸")
        cr = round(random.uniform(1.0,10.0),2)
        if cr >= 2.0:
            w = int(bet*cr); u["balance"] += w; u["games_won"] += 1; save_db(); return send(peer_id, f"📈 {cr}x +{fmt(w)}")
        u["balance"] -= bet; u["games_lost"] += 1; save_db(); return send(peer_id, f"📉 {cr}x -{fmt(bet)}")
    if cmd in ("угадай","guess"):
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌ !угадай 1-10 ставка")
        try: g,bet = int(p[0]),int(p[1])
        except: return send(peer_id, "❌")
        if u["balance"] < bet: return send(peer_id, "💸")
        num = random.randint(1,10)
        if g == num:
            u["balance"] += bet*5; u["games_won"] += 1; save_db(); return send(peer_id, f"🎯 {num}! +{fmt(bet*5)}")
        u["balance"] -= bet; u["games_lost"] += 1; save_db(); return send(peer_id, f"🎯 было {num}, -{fmt(bet)}")
    if cmd in ("кнб","rps"):
        if args.lower() not in ("камень","ножницы","бумага"): return send(peer_id, "❌")
        bc = random.choice(["камень","ножницы","бумага"])
        w = {"камень":"ножницы","ножницы":"бумага","бумага":"камень"}
        if args.lower() == bc: return send(peer_id, f"🤝 {bc}")
        if w[args.lower()] == bc:
            u["balance"] += 100; u["games_won"] += 1; save_db(); return send(peer_id, f"✅ бот:{bc} +100")
        u["balance"] -= 100; u["games_lost"] += 1; save_db(); return send(peer_id, f"❌ бот:{bc} -100")
    if cmd in ("дуэль","duel"):
        tg = extract_user(args)
        if not tg or tg == user_id: return send(peer_id, "❌ !дуэль @id")
        tt = get_user(tg)
        if u["balance"] < 500 or tt["balance"] < 500: return send(peer_id, "💸 500")
        u["balance"] -= 500; tt["balance"] -= 500
        if random.choice([1,0]):
            u["balance"] += 1000; u["games_won"] += 1; save_db(); return send(peer_id, f"⚔️ Ты победил [id{tg}] +1000")
        tt["balance"] += 1000; u["games_lost"] += 1; save_db(); return send(peer_id, f"⚔️ [id{tg}] победил")
    if cmd in ("лотерея","lottery"):
        if u["balance"] < 100: return send(peer_id, "💸")
        u["balance"] -= 100; tk = random.randint(100000,999999)
        if random.randint(1,100) <= 5:
            pr = random.randint(10000,100000)
            u["balance"] += pr; save_db(); return send(peer_id, f"🎟️ {tk} ВЫИГРЫШ {fmt(pr)}")
        save_db(); return send(peer_id, f"🎟️ {tk} мимо")
    if cmd in ("колесо","spin"):
        if time.time()-u["spin_time"] < 3600: return send(peer_id, "⏳ раз в час")
        w = random.choice([100,500,1000,5000,10000,50000,100000,0])
        u["balance"] += w; u["spin_time"] = int(time.time()); save_db()
        return send(peer_id, f"🎡 +{fmt(w)}")
    if cmd in ("репа","rep"):
        tg = extract_user(args)
        if not tg or tg == user_id: return send(peer_id, "❌ !репа @id")
        get_user(tg)["reputation"] += 1; save_db(); return send(peer_id, f"⭐ +1 [id{tg}]")
    if cmd in ("брак","marry"):
        tg = extract_user(args)
        if not tg or tg == user_id: return send(peer_id, "❌")
        if u["married_to"] or get_user(tg)["married_to"]: return send(peer_id, "💔")
        if u["balance"] < 50000: return send(peer_id, "💸 50000")
        u["balance"] -= 50000; u["married_to"] = tg; get_user(tg)["married_to"] = user_id; save_db()
        return send(peer_id, f"💍 [id{user_id}]+[id{tg}]")
    if cmd in ("развод","divorce"):
        if not u["married_to"]: return send(peer_id, "Не женат")
        get_user(u["married_to"])["married_to"] = 0; u["married_to"] = 0; save_db()
        return send(peer_id, "💔 Развод")
    if cmd in ("друзья","friends"):
        return send(peer_id, "👥 "+("\n".join(f"• [id{f}]" for f in u["friends"]) if u["friends"] else "пусто"))
    if cmd in ("подарить","gift"):
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌")
        tg = extract_user(p[0])
        try: a = int(p[1])
        except: return send(peer_id, "❌")
        if a < 100 or u["balance"] < a: return send(peer_id, "💸")
        u["balance"] -= a; get_user(tg)["balance"] += a; save_db()
        return send(peer_id, f"🎁 {fmt(a)} → [id{tg}]")
    if cmd in ("клан","clan"):
        if not u["clan_id"]: return send(peer_id, "!создатьклан имя")
        c = DB["clans"].get(str(u["clan_id"]),{})
        return send(peer_id, f"🏰 {c.get('name','?')} 💰{fmt(c.get('balance',0))}")
    if cmd in ("создатьклан","createclan"):
        if not args.strip(): return send(peer_id, "❌ имя")
        if u["balance"] < 100000 or u["clan_id"]: return send(peer_id, "💸/уже")
        u["balance"] -= 100000; cid = len(DB["clans"])+1
        DB["clans"][str(cid)] = {"name":args.strip(),"owner":user_id,"balance":0,"members":[user_id]}
        u["clan_id"] = cid; save_db(); return send(peer_id, f"🏰 «{args.strip()}» создан")
    if cmd in ("профиль","profile"):
        cr = "\n👑 ВЛАДЕЛЕЦ" if tid == OWNER_ID else ""
        return send(peer_id, f"👤 [id{tid}|]{cr}\n💰{fmt(t['balance'])} 🏦{fmt(t['bank'])} 💎{fmt(t['donate'])}\n📊{t['level']} ⭐{t['reputation']} 🏆{t['title'] or '—'}\n🏢{t['business'] or '—'} 🚗{t['car'] or '—'} 🏠{t['house'] or '—'}\n🐾{t['pet'] or '—'} ⚔️{t['games_won']}W/{t['games_lost']}L\n🏅 {len(t['achievements'])} ачивок | 💬 {t['messages_count']}", get_kb())
    if cmd in ("топ","top"):
        rows = sorted(DB["users"].items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
        return send(peer_id, "🏆\n"+"\n".join(f"{i}. [id{uid}] {fmt(d['balance'])}" for i,(uid,d) in enumerate(rows,1)))
    if cmd in ("топуровень","toplevel"):
        rows = sorted(DB["users"].items(), key=lambda x: x[1]["level"], reverse=True)[:10]
        return send(peer_id, "📊\n"+"\n".join(f"{i}. [id{uid}] ур.{d['level']}" for i,(uid,d) in enumerate(rows,1)))
    if cmd in ("стата","stats"):
        tb = sum(d["balance"] for d in DB["users"].values())
        tm = sum(d["messages_count"] for d in DB["users"].values())
        return send(peer_id, f"📊 👥{len(DB['users'])} 💰{fmt(tb)} 💬{fmt(tm)} 🎁{len(DB['promo'])} 🏰{len(DB['clans'])}")
    if cmd in ("титул","title"):
        n = args.lower().strip()
        if n not in TITLES: return send(peer_id, "❌ "+", ".join(TITLES.keys()))
        if u["balance"] < TITLES[n]: return send(peer_id, "💸")
        u["balance"] -= TITLES[n]; u["title"] = n; save_db(); return send(peer_id, f"🏆 {n}")
    if cmd in ("достижения","achievements","ачивки"):
        if not u["achievements"]: return send(peer_id, "🏅 Пусто")
        names = [ACHIEVES[k][0] for k in u["achievements"] if k in ACHIEVES]
        return send(peer_id, "🏅\n"+"\n".join(f"• {n}" for n in names))
    if cmd in ("активировать","промо","promo"):
        code = args.upper().strip()
        if code not in DB["promo"]: return send(peer_id, "❌ Нет промо")
        p = DB["promo"][code]
        if p["uses_left"] <= 0: return send(peer_id, "❌ Исчерпан")
        msg = ""
        if p["type"] == "balance": u["balance"] += int(p["value"]); msg = f"💰 +{fmt(p['value'])}"
        elif p["type"] == "business": u["business"] = p["value"]; msg = f"🏢 {p['value']}"
        elif p["type"] == "level": u["level"] = int(p["value"]); u["xp"] = u["level"]**2; msg = f"📊 ур.{p['value']}"
        elif p["type"] == "donate": u["donate"] += int(p["value"]); msg = f"💎 +{fmt(p['value'])}"
        p["uses_left"] -= 1; save_db(); return send(peer_id, f"🎁 {msg}")
    if cmd in ("анекдот","joke"):
        return send(peer_id, "😄 "+random.choice(["Oct 31 == Dec 25.","Сири, почему я одинок? *фронталка*","Купи батон, если яйца — десяток. Вернулся с 10 батонами."]))
    if cmd in ("факт","fact"):
        return send(peer_id, "🧠 "+random.choice(["Мёд не портится.","У осьминога 3 сердца.","Банан — ягода."]))
    if cmd in ("цитата","quote"):
        return send(peer_id, "💬 "+random.choice(["Будь собой — прочие роли заняты.","Делай великое — люби своё дело."]))
    if cmd in ("шар","8ball"):
        return send(peer_id, "🎱 "+random.choice(["Да","Нет","Возможно","Точно да","Позже"]))
    if cmd in ("погода","weather"):
        return send(peer_id, f"🌤️ {random.choice(['☀️','⛅','🌧️','❄️'])} {random.randint(-10,30)}°C")
    if cmd in ("совместимость","compat"):
        tg = extract_user(args)
        if not tg: return send(peer_id, "❌ @id")
        return send(peer_id, f"💕 {random.randint(0,100)}%")
    if cmd in ("варн","warn"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if not tg: return send(peer_id, "❌")
        tt = get_user(tg); tt["warns"] += 1; save_db()
        send(peer_id, f"⚠️ [id{tg}] {tt['warns']}/3")
        if tt["warns"] >= 3:
            tt["muted_until"] = int(time.time())+3600; tt["warns"] = 0; save_db()
            send(peer_id, f"🚫 [id{tg}] мут 1ч")
        return True
    if cmd in ("мут","mute"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split(); tg = extract_user(p[0]) if p else None
        if not tg: return send(peer_id, "❌")
        mn = int(p[1]) if len(p) > 1 else 60
        get_user(tg)["muted_until"] = int(time.time())+mn*60; save_db()
        return send(peer_id, f"🔇 [id{tg}] {mn} мин")
    if cmd in ("снятьмут","unmute"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if tg: get_user(tg)["muted_until"] = 0; save_db(); send(peer_id, f"✅ [id{tg}]")
        return True
    if cmd in ("снятьварн","unwarn"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if tg:
            tt = get_user(tg); tt["warns"] = max(0,tt["warns"]-1); save_db(); send(peer_id, f"✅ [id{tg}]")
        return True
    if cmd in ("кик","kick","бан","ban"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        tg = extract_user(args)
        if not tg: return send(peer_id, "❌")
        try:
            vk.messages.removeChatUser(chat_id=peer_id-2000000000, user_id=tg)
            send(peer_id, f"🔨 [id{tg}] кик")
        except Exception as e: send(peer_id, f"❌ {e}")
        return True
    if cmd in ("выдатьбаланс","givebalance"):
        if not is_admin(user_id): return send(peer_id, "🚫")
        p = args.split()
        if len(p) < 2: return send(peer_id, "❌")
        get_user(extract_user(p[0]))["balance"] += int(p[1]); save_db()
        return send(peer_id, f"✅
