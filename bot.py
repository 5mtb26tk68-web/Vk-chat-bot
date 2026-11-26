import vk_api, os, json, re, time, random, threading, traceback
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

TOKEN = os.environ.get("VK_TOKEN", "")
OWNER_ID = 734176092
DEVELOPERS = [int(x) for x in os.environ.get("DEVELOPERS", "734176092").split(",") if x]
if OWNER_ID not in DEVELOPERS: DEVELOPERS.append(OWNER_ID)
PREFIX = "!"
MAT = ["хуй", "пизд", "ебан", "бляд", "сука", "долбо"]
if not TOKEN:
    print("NO TOKEN"); raise SystemExit(1)

def load_db():
    if not os.path.exists("db.json"): return {"users": {}, "promo": {}, "clans": {}}
    with open("db.json", "r", encoding="utf-8") as f: return json.load(f)
def save_db():
    with open("db.json", "w", encoding="utf-8") as f: json.dump(DB, f, ensure_ascii=False)
DB = load_db()
NEW = {"balance":1000,"bank":0,"donate":0,"xp":0,"level":0,"warns":0,"reputation":0,"business":None,"business_time":0,"work_time":0,"daily_time":0,"deposit":0,"deposit_time":0,"car":None,"house":None,"yacht":None,"phone":None,"pet":None,"pet_hunger":100,"pet_happiness":100,"farm":None,"farm_time":0,"married_to":0,"clan_id":0,"inventory":{},"achievements":[],"muted_until":0,"messages_count":0,"games_won":0,"games_lost":0,"title":None,"spin_time":0,"friends":[],"mat_count":0,"register_time":0}
def get_user(uid):
    s = str(uid)
    if s not in DB["users"]:
        d = dict(NEW); d["register_time"] = int(time.time()); DB["users"][s] = d; save_db()
    return DB["users"][s]
def ex(t):
    m = re.search(r"(?:@id|id|vk\.com/)(\d+)", str(t))
    return int(m.group(1)) if m else None
def is_ad(u): return u in DEVELOPERS
def is_own(u): return u == OWNER_ID
def fmt(n):
    try: return "{:,}".format(int(n)).replace(",", " ")
    except Exception: return str(n)

BIZ = {"ларёк":(10000,800),"кафе":(50000,4500),"магазин":(200000,20000),"ресторан":(750000,80000),"завод":(2500000,280000),"банк":(10000000,1200000),"нефтянка":(50000000,6500000),"космодром":(200000000,30000000)}
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
ACH = {"first":("Первое сообщение", lambda u: u["messages_count"] >= 1),"rich":("Миллионер", lambda u: u["balance"] >= 1000000),"lvl10":("10 уровень", lambda u: u["level"] >= 10),"gamer":("10 побед", lambda u: u["games_won"] >= 10),"boss":("Бизнесмен", lambda u: u["business"] is not None),"married":("В браке", lambda u: u["married_to"] != 0)}
SHOPS = [("business",BIZ),("car",CARS),("house",HOUSES),("yacht",YACHTS),("phone",PHONES),("pet",PETS),("farm",FARMS)]
def ach_check(u):
    got = []
    for k, v in ACH.items():
        if k not in u["achievements"]:
            try:
                if v[1](u): u["achievements"].append(k); got.append(v[0])
            except Exception: pass
    return got

try:
    from flask import Flask
    fa = Flask("")
    @fa.route("/")
    def home(): return "Astra alive!"
    threading.Thread(target=lambda: fa.run(host="0.0.0.0", port=8080), daemon=True).start()
    print("Flask :8080")
except Exception as e: print("Flask err:", e)

vks = vk_api.VkApi(token=TOKEN)
vk = vks.get_api()
lp = VkLongPoll(vks)

def kb_main():
    kb = VkKeyboard(one_time=False)
    kb.add_button("Баланс", color=VkKeyboardColor.PRIMARY); kb.add_button("Работа", color=VkKeyboardColor.POSITIVE)
    kb.add_line(); kb.add_button("Бизнесы", color=VkKeyboardColor.POSITIVE); kb.add_button("Игры", color=VkKeyboardColor.SECONDARY)
    kb.add_line(); kb.add_button("Профиль", color=VkKeyboardColor.SECONDARY); kb.add_button("Помощь", color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()
def kb_games():
    kb = VkKeyboard(one_time=False)
    kb.add_button("Казино 100", color=VkKeyboardColor.PRIMARY); kb.add_button("Монетка 100", color=VkKeyboardColor.POSITIVE)
    kb.add_line(); kb.add_button("Кости 100", color=VkKeyboardColor.POSITIVE); kb.add_button("Колесо", color=VkKeyboardColor.SECONDARY)
    kb.add_line(); kb.add_button("Шахта", color=VkKeyboardColor.SECONDARY); kb.add_button("Рыбалка", color=VkKeyboardColor.SECONDARY)
    kb.add_line(); kb.add_button("Назад", color=VkKeyboardColor.NEGATIVE)
    return kb.get_keyboard()
def kb_admin():
    kb = VkKeyboard(one_time=False)
    kb.add_button("Админинфо", color=VkKeyboardColor.PRIMARY); kb.add_button("Выдать баланс", color=VkKeyboardColor.POSITIVE)
    kb.add_line(); kb.add_button("Выдать донат", color=VkKeyboardColor.POSITIVE); kb.add_button("Создать промо", color=VkKeyboardColor.POSITIVE)
    kb.add_line(); kb.add_button("Варн", color=VkKeyboardColor.NEGATIVE); kb.add_button("Мут", color=VkKeyboardColor.NEGATIVE)
    kb.add_line(); kb.add_button("Обнулить", color=VkKeyboardColor.NEGATIVE); kb.add_button("Назад", color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()
BTNC = {"Баланс":"баланс","Работа":"работа","Бизнесы":"бизнесы","Игры":"игры","Профиль":"профиль","Помощь":"помощь","Казино 100":"казино","Монетка 100":"монетка","Кости 100":"кости","Колесо":"колесо","Шахта":"шахта","Рыбалка":"рыбалка","Админинфо":"h_info","Выдать баланс":"h_bal","Выдать донат":"h_don","Создать промо":"h_promo","Варн":"h_warn","Мут":"h_mute","Обнулить":"h_reset","Назад":"назад"}
def send(pid, msg, kb=None):
    try: vk.messages.send(peer_id=pid, message=str(msg), random_id=0, keyboard=kb if kb else kb_main())
    except Exception as e: print("Send err:", e)

HELP = ("ASTRA FULL\nЭКОНОМИКА: !баланс !работа !бонус !бизнесы !купить !продать !доход !банк !положить !снять !депозит !забрать !перевод !донат\nМАГАЗИН: !машины !дома !яхты !телефоны !питомцы !фермы !кейсы !кейс имя !инвентарь\nАКТИВ: !шахта !рыбалка !охота !ферма !покормить !поиграть\nИГРЫ: !казино !монетка !кости !рулетка !краш !угадай !кнб !дуэль !лотерея !колесо\nСОЦИАЛ: !репа @id !брак @id !развод !друзья !подарить @id сумма !клан !создатьклан имя\nПРОФИЛЬ: !профиль !топ !топуровень !стата !титул имя !достижения\nПРОМО: !активировать КОД\nФАН: !анекдот !факт !цитата !шар !погода !совместимость @id\nМОД: !варн !мут !снятьмут !снятьварн !кик\nАДМИН: !админка !админинфо @id !выдатьбаланс !забратьбаланс !выдатьдонат !забратьдонат !выдатьуровень !выдатьрепу !выдатьбизнес !забратьбизнес !выдатьимущество !обнулить !создатьпромо !удалитьпромо !списокпромо !добавитьадмина !списокадминов !рассылка текст")

def handle(pid, uid, cmd, args):
    u = get_user(uid); tid = ex(args) or uid; t = get_user(tid)
    H = {"h_info":"!админинфо @id","h_bal":"!выдатьбаланс @id сумма","h_don":"!выдатьдонат @id сумма","h_promo":"!создатьпромо КОД balance 10000 50","h_warn":"!варн @id","h_mute":"!мут @id 60","h_reset":"!обнулить @id"}
    if cmd in H:
        if not is_ad(uid): return send(pid, "Только админ")
        return send(pid, "Введи: " + H[cmd], kb_admin())
    if cmd in ("игры","games"): return send(pid, "Игры:", kb_games())
    if cmd == "назад": return send(pid, "Меню:", kb_main())
    if cmd in ("админка","admin"):
        if not is_ad(uid): return send(pid, "Только админ")
        return send(pid, "ПАНЕЛЬ. Статус: " + ("ВЛАДЕЛЕЦ" if is_own(uid) else "Админ"), kb_admin())
    if cmd in ("помощь","help"): return send(pid, HELP, kb_admin() if is_ad(uid) else kb_main())
    if cmd in ("о боте","about"): return send(pid, "Astra FULL. Владелец [id" + str(OWNER_ID) + "]. Юзеров: " + str(len(DB["users"])))
    if cmd in ("баланс","balance"):
        cr = " [ВЛАДЕЛЕЦ]" if tid == OWNER_ID else ""
        return send(pid, "БАЛАНС [id" + str(tid) + "|]" + cr + "\nДеньги: " + fmt(t["balance"]) + " р.\nБанк: " + fmt(t["bank"]) + " р.\nДонат: " + fmt(t["donate"]) + "\nУровень: " + str(t["level"]) + " (" + str(t["xp"]) + " XP)\nРеп: " + str(t["reputation"]) + "\nБизнес: " + str(t["business"] or "-") + "\nМашина: " + str(t["car"] or "-") + " | Дом: " + str(t["house"] or "-") + "\nВарны: " + str(t["warns"]) + "/3 | Сообщений: " + str(t["messages_count"]), kb_main())
    if cmd in ("донат","donate"): return send(pid, "Донат: " + fmt(u["donate"]))
    if cmd in ("работа","work"):
        if time.time() - u["work_time"] < 1800: return send(pid, "Отдыхай " + str(int((1800-(time.time()-u["work_time"]))//60)) + " мин.")
        e = 200 + u["level"]*20 + random.randint(0,100); u["balance"] += e; u["work_time"] = int(time.time()); save_db()
        return send(pid, "Заработано " + fmt(e) + " р.")
    if cmd in ("бонус","bonus","ежедневка","daily"):
        if time.time() - u["daily_time"] < 86400: return send(pid, "Бонус через " + str(int((86400-(time.time()-u["daily_time"]))//3600)) + " ч.")
        b = 500 + u["level"]*100; u["balance"] += b; u["daily_time"] = int(time.time()); save_db()
        return send(pid, "Бонус " + fmt(b) + " р.")
    if cmd in ("бизнесы","businesses"):
        return send(pid, "БИЗНЕСЫ:\n" + "\n".join(["- " + n + ": " + fmt(p[0]) + " р. (" + fmt(p[1]) + "/ч)" for n,p in BIZ.items()]) + "\n!купить <имя>")
    if cmd in ("купить","buy"):
        n = args.lower().strip()
        for key, d in SHOPS:
            if n in d:
                price = d[n][0] if isinstance(d[n], tuple) else d[n]
                if key == "business" and u["business"]: return send(pid, "Уже есть бизнес")
                if u["balance"] < price: return send(pid, "Не хватает")
                u["balance"] -= price
                if key == "business": u["business"] = n; u["business_time"] = int(time.time())
                else: u[key] = n
                save_db(); return send(pid, "Куплено: " + n)
        return send(pid, "Не найдено: !машины !дома !яхты !телефоны !питомцы !фермы")
    if cmd in ("продать","sell"):
        n = args.lower().strip(); mp = {"бизнес":("business",BIZ),"машина":("car",CARS),"дом":("house",HOUSES)}
        if n in mp and u[mp[n][0]]:
            key, d = mp[n]; val = d[u[key]]; p = (val[0] if isinstance(val, tuple) else val)//2
            u["balance"] += p; u[key] = None; save_db(); return send(pid, "Продано за " + fmt(p) + " р.")
        return send(pid, "Нечего продавать")
    if cmd in ("доход","income"):
        if not u["business"]: return send(pid, "Нет бизнеса")
        h = int((time.time()-u["business_time"])//3600)
        if h < 1: return send(pid, "Рано")
        e = BIZ[u["business"]][1]*h; u["balance"] += e; u["business_time"] = int(time.time()); save_db()
        return send(pid, "Доход " + fmt(e) + " р.")
    if cmd in ("банк","bank"): return send(pid, "БАНК\nНаличные " + fmt(u["balance"]) + " | Банк " + fmt(u["bank"]) + " | Депозит " + fmt(u["deposit"]) + "\n!положить !снять !депозит !забрать")
    if cmd in ("положить","put"):
        try: a = int(args)
        except Exception: return send(pid, "Сумма?")
        if a > u["balance"]: return send(pid, "Не хватает")
        u["balance"] -= a; u["bank"] += a; save_db(); return send(pid, "В банк " + fmt(a))
    if cmd in ("снять","withdraw"):
        try: a = int(args)
        except Exception: return send(pid, "Сумма?")
        if a > u["bank"]: return send(pid, "В банке нет")
        u["bank"] -= a; u["balance"] += a; save_db(); return send(pid, "Снято " + fmt(a))
    if cmd in ("депозит","deposit"):
        try: a = int(args)
        except Exception: return send(pid, "Сумма?")
        if a < 1000 or u["balance"] < a: return send(pid, "Мин 1000 и иметь сумму")
        u["balance"] -= a; u["deposit"] += a; u["deposit_time"] = int(time.time()); save_db()
        return send(pid, "Депозит " + fmt(a) + " (5%/ч)")
    if cmd in ("забрать","claim"):
        h = int((time.time()-u["deposit_time"])//3600); i = int(u["deposit"]*0.05*h); tot = u["deposit"]+i
        u["balance"] += tot; u["deposit"] = 0; save_db()
        return send(pid, "Забрано " + fmt(tot) + " (проценты " + fmt(i) + ")")
    if cmd in ("перевод","transfer"):
        p = args.split()
        if len(p) < 2: return send(pid, "!перевод @id сумма")
        tg = ex(p[0])
        try: a = int(p[1])
        except Exception: return send(pid, "Сумма?")
        if a < 100 or u["balance"] < a: return send(pid, "Мин 100 и иметь сумму")
        tax = int(a*0.05); u["balance"] -= a; get_user(tg)["balance"] += a-tax; save_db()
        return send(pid, "Переведено " + fmt(a-tax) + " (налог " + fmt(tax) + ")")
    if cmd in ("машины","cars"): return send(pid, "Машины: " + ", ".join(CARS.keys()))
    if cmd in ("дома","houses"): return send(pid, "Дома: " + ", ".join(HOUSES.keys()))
    if cmd in ("яхты","yachts"): return send(pid, "Яхты: " + ", ".join(YACHTS.keys()))
    if cmd in ("телефоны","phones"): return send(pid, "Телефоны: " + ", ".join(PHONES.keys()))
    if cmd in ("питомцы","pets"): return send(pid, "Питомцы: " + ", ".join(PETS.keys()))
    if cmd in ("фермы","farms"): return send(pid, "Фермы: " + ", ".join(FARMS.keys()))
    if cmd in ("кейсы","cases"): return send(pid, "Кейсы: " + ", ".join(CASES.keys()))
    if cmd in ("кейс","case"):
        n = args.lower().strip()
        if n not in CASES: return send(pid, "Кейсы: " + ", ".join(CASES.keys()))
        c = CASES[n]
        if u["balance"] < c[0]: return send(pid, "Не хватает")
        u["balance"] -= c[0]; w = random.randint(c[1], c[2]); u["balance"] += w
        it = random.choice(list(MINE.keys())+list(FISH.keys())); u["inventory"][it] = u["inventory"].get(it,0)+1; save_db()
        return send(pid, "Кейс " + n + ": " + fmt(w) + " р. + " + it)
    if cmd in ("инвентарь","inventory"):
        if not u["inventory"]: return send(pid, "Пусто")
        return send(pid, "ИНВЕНТАРЬ:\n" + "\n".join(["- " + i + " x" + str(c) for i,c in u["inventory"].items()]))
    if cmd in ("шахта","mine"):
        it,(a,b) = random.choice(list(MINE.items())); e = random.randint(a,b)
        u["balance"] += e; u["inventory"][it] = u["inventory"].get(it,0)+1; save_db(); return send(pid, "Шахта: " + it + " +" + fmt(e))
    if cmd in ("рыбалка","fish"):
        it,(a,b) = random.choice(list(FISH.items())); e = random.randint(a,b)
        u["balance"] += e; u["inventory"][it] = u["inventory"].get(it,0)+1; save_db(); return send(pid, "Рыбалка: " + it + " +" + fmt(e))
    if cmd in ("охота","hunt"):
        it,(a,b) = random.choice(list(HUNT.items())); e = random.randint(a,b)
        u["balance"] += e; u["inventory"][it] = u["inventory"].get(it,0)+1; save_db(); return send(pid, "Охота: " + it + " +" + fmt(e))
    if cmd in ("ферма","farm"):
        if not u["farm"]: return send(pid, "Купи: !фермы")
        h = int((time.time()-u["farm_time"])//3600)
        if h < 1: return send(pid, "Рано")
        e = {"огород":5000,"теплица":25000,"ранчо":100000}[u["farm"]]*h
        u["balance"] += e; u["farm_time"] = int(time.time()); save_db(); return send(pid, "Ферма +" + fmt(e))
    if cmd in ("покормить","feed"):
        if not u["pet"]: return send(pid, "Нет питомца")
        if u["balance"] < 500: return send(pid, "Нужно 500")
        u["balance"] -= 500; u["pet_hunger"] = min(100, u["pet_hunger"]+30); save_db()
        return send(pid, u["pet"] + " сытость " + str(u["pet_hunger"]) + "%")
    if cmd in ("поиграть","playpet"):
        if not u["pet"]: return send(pid, "Нет питомца")
        u["pet_happiness"] = min(100, u["pet_happiness"]+30); save_db()
        return send(pid, u["pet"] + " счастье " + str(u["pet_happiness"]) + "%")
    if cmd in ("монетка","coin"):
        bet = int(args) if args else 100
        if bet < 50 or u["balance"] < bet: return send(pid, "Ставка от 50 и иметь сумму")
        if random.choice([1,0]):
            u["balance"] += bet; u["games_won"] += 1; save_db(); return send(pid, "Орёл +" + fmt(bet))
        u["balance"] -= bet; u["games_lost"] += 1; save_db(); return send(pid, "Решка -" + fmt(bet))
    if cmd in ("казино","slots","casino"):
        bet = int(args) if args else 100
        if bet < 100 or u["balance"] < bet: return send(pid, "Ставка от 100")
        s = [random.choice(["X","O","#","*","7"]) for _ in range(3)]
        if s[0]==s[1]==s[2]:
            m = 10 if s[0]=="7" else 5; u["balance"] += bet*m; u["games_won"] += 1; save_db()
            return send(pid, "".join(s) + " ДЖЕКПОТ +" + fmt(bet*m))
        if s[0]==s[1] or s[1]==s[2]:
            u["balance"] += bet; u["games_won"] += 1; save_db(); return send(pid, "".join(s) + " +" + fmt(bet))
        u["balance"] -= bet; u["games_lost"] += 1; save_db(); return send(pid, "".join(s) + " -" + fmt(bet))
    if cmd in ("кости","dice"):
        bet = int(args) if args else 100
        if bet < 100 or u["balance"] < bet: return send(pid, "Ставка от 100")
        d = random.randint(1,6)
        if d >= 4:
            u["balance"] += bet; u["games_won"] += 1; save_db(); return send(pid, "Кость " + str(d) + " +" + fmt(bet))
        u["balance"] -= bet; u["games_lost"] += 1; save_db(); return send(pid, "Кость " + str(d) + " -" + fmt(bet))
    if cmd in ("рулетка","roulette"):
        bet = int(args) if args else 100
        if bet < 100 or u["balance"] < bet: return send(pid, "Ставка от 100")
        n = random.randint(0,36)
        if n and n % 2 == 0:
            u["balance"] += bet; u["games_won"] += 1; save_db(); return send(pid, "Рулетка " + str(n) + " +" + fmt(bet))
        u["balance"] -= bet; u["games_lost"] += 1; save_db(); return send(pid, "Рулетка " + str(n) + " -" + fmt(bet))
    if cmd in ("краш","crash"):
        bet = int(args) if args else 100
        if bet < 100 or u["balance"] < bet: return send(pid, "Ставка от 100")
        cr = round(random.uniform(1.0,10.0),2)
        if cr >= 2.0:
            w = int(bet*cr); u["balance"] += w; u["games_won"] += 1; save_db(); return send(pid, "Краш " + str(cr) + "x +" + fmt(w))
        u["balance"] -= bet; u["games_lost"] += 1; save_db(); return send(pid, "Краш " + str(cr) + "x -" + fmt(bet))
    if cmd in ("угадай","guess"):
        p = args.split()
        if len(p) < 2: return send(pid, "!угадай 1-10 ставка")
        try: g, bet = int(p[0]), int(p[1])
        except Exception: return send(pid, "Числа?")
        if u["balance"] < bet: return send(pid, "Не хватает")
        num = random.randint(1,10)
        if g == num:
            u["balance"] += bet*5; u["games_won"] += 1; save_db(); return send(pid, "Угадал! Было " + str(num) + " +" + fmt(bet*5))
        u["balance"] -= bet; u["games_lost"] += 1; save_db(); return send(pid, "Мимо, было " + str(num) + " -" + fmt(bet))
    if cmd in ("кнб","rps"):
        if args.lower() not in ("камень","ножницы","бумага"): return send(pid, "!кнб камень/ножницы/бумага")
        bc = random.choice(["камень","ножницы","бумага"]); w = {"камень":"ножницы","ножницы":"бумага","бумага":"камень"}
        if args.lower() == bc: return send(pid, "Ничья: " + bc)
        if w[args.lower()] == bc:
            u["balance"] += 100; u["games_won"] += 1; save_db(); return send(pid, "Победа, бот: " + bc + " +100")
        u["balance"] -= 100; u["games_lost"] += 1; save_db(); return send(pid, "Проигрыш, бот: " + bc + " -100")
    if cmd in ("дуэль","duel"):
        tg = ex(args)
        if not tg or tg == uid: return send(pid, "!дуэль @id")
        tt = get_user(tg)
        if u["balance"] < 500 or tt["balance"] < 500: return send(pid, "У обоих нужно 500")
        u["balance"] -= 500; tt["balance"] -= 500
        if random.choice([1,0]):
            u["balance"] += 1000; u["games_won"] += 1; save_db(); return send(pid, "Ты победил [id" + str(tg) + "] +1000")
        tt["balance"] += 1000; u["games_lost"] += 1; save_db(); return send(pid, "[id" + str(tg) + "] победил")
    if cmd in ("лотерея","lottery"):
        if u["balance"] < 100: return send(pid, "Билет 100")
        u["balance"] -= 100; tk = random.randint(100000,999999)
        if random.randint(1,100) <= 5:
            pr = random.randint(10000,100000); u["balance"] += pr; save_db(); return send(pid, "Билет " + str(tk) + " ВЫИГРЫШ " + fmt(pr))
        save_db(); return send(pid, "Билет " + str(tk) + " мимо")
    if cmd in ("колесо","spin"):
        if time.time()-u["spin_time"] < 3600: return send(pid, "Раз в час")
        w = random.choice([100,500,1000,5000,10000,50000,100000,0])
        u["balance"] += w; u["spin_time"] = int(time.time()); save_db(); return send(pid, "Колесо +" + fmt(w))
    if cmd in ("репа","rep"):
        tg = ex(args)
        if not tg or tg == uid: return send(pid, "!репа @id")
        get_user(tg)["reputation"] += 1; save_db(); return send(pid, "+1 репа [id" + str(tg) + "]")
    if cmd in ("брак","marry"):
        tg = ex(args)
        if not tg or tg == uid: return send(pid, "!брак @id")
        if u["married_to"] or get_user(tg)["married_to"]: return send(pid, "Кто-то уже в браке")
        if u["balance"] < 50000: return send(pid, "Свадьба 50000")
        u["balance"] -= 50000; u["married_to"] = tg; get_user(tg)["married_to"] = uid; save_db()
        return send(pid, "Свадьба! [id" + str(uid) + "] + [id" + str(tg) + "]")
    if cmd in ("развод","divorce"):
        if not u["married_to"]: return send(pid, "Ты не в браке")
        get_user(u["married_to"])["married_to"] = 0; u["married_to"] = 0; save_db(); return send(pid, "Развод")
    if cmd in ("друзья","friends"):
        if not u["friends"]: return send(pid, "Друзей нет")
        return send(pid, "Друзья:\n" + "\n".join(["- [id" + str(f) + "]" for f in u["friends"]]))
    if cmd in ("подарить","gift"):
        p = args.split()
        if len(p) < 2: return send(pid, "!подарить @id сумма")
        tg = ex(p[0])
        try: a = int(p[1])
        except Exception: return send(pid, "Сумма?")
        if a < 100 or u["balance"] < a: return send(pid, "Мин 100 и иметь сумму")
        u["balance"] -= a; get_user(tg)["balance"] += a; save_db(); return send(pid, "Подарок " + fmt(a) + " -> [id" + str(tg) + "]")
    if cmd in ("клан","clan"):
        if not u["clan_id"]: return send(pid, "Ты не в клане: !создатьклан имя")
        c = DB["clans"].get(str(u["clan_id"]), {})
        return send(pid, "Клан " + str(c.get("name","?")) + " казна " + fmt(c.get("balance",0)))
    if cmd in ("создатьклан","createclan"):
        if not args.strip(): return send(pid, "Имя?")
        if u["balance"] < 100000 or u["clan_id"]: return send(pid, "Нужно 100000 и не быть в клане")
        u["balance"] -= 100000; cid = len(DB["clans"])+1
        DB["clans"][str(cid)] = {"name":args.strip(),"owner":uid,"balance":0,"members":[uid]}
        u["clan_id"] = cid; save_db(); return send(pid, "Клан создан: " + args.strip())
    if cmd in ("профиль","profile"):
        cr = " [ВЛАДЕЛЕЦ]" if tid == OWNER_ID else ""
        return send(pid, "ПРОФИЛЬ [id" + str(tid) + "|]" + cr + "\nДеньги " + fmt(t["balance"]) + " | Банк " + fmt(t["bank"]) + " | Донат " + fmt(t["donate"]) + "\nУровень " + str(t["level"]) + " | Реп " + str(t["reputation"]) + " | Титул " + str(t["title"] or "-") + "\nБизнес " + str(t["business"] or "-") + " | Машина " + str(t["car"] or "-") + " | Дом " + str(t["house"] or "-") + "\nПитомец " + str(t["pet"] or "-") + " | Побед " + str(t["games_won"]) + "/Пор " + str(t["games_lost"]) + "\nАчивок " + str(len(t["achievements"])) + " | Сообщений " + str(t["messages_count"]), kb_main())
    if cmd in ("топ","top"):
        rows = sorted(DB["users"].items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
        return send(pid, "ТОП деньги:\n" + "\n".join([str(i) + ". [id" + uid + "] " + fmt(d["balance"]) for i,(uid,d) in enumerate(rows,1)]))
    if cmd in ("топуровень","toplevel"):
        rows = sorted(DB["users"].items(), key=lambda x: x[1]["level"], reverse=True)[:10]
        return send(pid, "ТОП уровень:\n" + "\n".join([str(i) + ". [id" + uid + "] ур." + str(d["level"]) for i,(uid,d) in enumerate(rows,1)]))
    if cmd in ("стата","stats"):
        tb = sum(d["balance"] for d in DB["users"].values()); tm = sum(d["messages_count"] for d in DB["users"].values())
        return send(pid, "СТАТА\nЮзеров " + str(len(DB["users"])) + "\nДенег " + fmt(tb) + "\nСообщений " + fmt(tm) + "\nПромо " + str(len(DB["promo"])) + "\nКланов " + str(len(DB["clans"])))
    if cmd in ("титул","title"):
        n = args.lower().strip()
        if n not in TITLES: return send(pid, "Титулы: " + ", ".join(TITLES.keys()))
        if u["balance"] < TITLES[n]: return send(pid, "Нужно " + fmt(TITLES[n]))
        u["balance"] -= TITLES[n]; u["title"] = n; save_db(); return send(pid, "Титул: " + n)
    if cmd in ("достижения","achievements","ачивки"):
        if not u["achievements"]: return send(pid, "Ачивок нет")
        return send(pid, "АЧИВКИ:\n" + "\n".join(["- " + ACH[k][0] for k in u["achievements"] if k in ACH]))
    if cmd in ("активировать","промо","promo"):
        code = args.upper().strip()
        if code not in DB["promo"]: return send(pid, "Промо не найден")
        p = DB["promo"][code]
        if p["uses_left"] <= 0: return send(pid, "Исчерпан")
        msg = ""
        if p["type"] == "balance": u["balance"] += int(p["value"]); msg = "+" + fmt(p["value"]) + " р."
        elif p["type"] == "business": u["business"] = p["value"]; msg = "бизнес " + p["value"]
        elif p["type"] == "level": u["level"] = int(p["value"]); u["xp"] = u["level"]**2; msg = "уровень " + p["value"]
        elif p["type"] == "donate": u["donate"] += int(p["value"]); msg = "+" + fmt(p["value"]) + " доната"
        p["uses_left"] -= 1; save_db(); return send(pid, "Промо активирован: " + msg)
    if cmd in ("анекдот","joke"): return send(pid, random.choice(["Oct 31 == Dec 25.","Сири, почему я одинок? *фронталка*","Купи батон, если яйца - десяток. Вернулся с 10 батонами."]))
    if cmd in ("факт","fact"): return send(pid, random.choice(["Мёд не портится.","У осьминога 3 сердца.","Банан - ягода."]))
    if cmd in ("цитата","quote"): return send(pid, random.choice(["Будь собой - прочие роли заняты.","Делай великое - люби своё дело."]))
    if cmd in ("шар","8ball"): return send(pid, random.choice(["Да","Нет","Возможно","Точно да","Позже"]))
    if cmd in ("погода","weather"): return send(pid, "Погода: " + str(random.randint(-10,30)) + " градусов")
    if cmd in ("совместимость","compat"):
        tg = ex(args)
        if not tg: return send(pid, "!совместимость @id")
        return send(pid, "Совместимость " + str(random.randint(0,100)) + "%")
    if cmd in ("варн","warn"):
        if not is_ad(uid): return send(pid, "Только админ")
        tg = ex(args)
        if not tg: return send(pid, "!варн @id")
        tt = get_user(tg); tt["warns"] += 1; save_db(); send(pid, "Варн [id" + str(tg) + "] " + str(tt["warns"]) + "/3")
        if tt["warns"] >= 3:
            tt["muted_until"] = int(time.time())+3600; tt["warns"] = 0; save_db(); send(pid, "[id" + str(tg) + "] мут 1ч за 3 варна")
        return True
    if cmd in ("мут","mute"):
        if not is_ad(uid): return send(pid, "Только админ")
        p = args.split(); tg = ex(p[0]) if p else None
        if not tg: return send(pid, "!мут @id мин")
        mn = int(p[1]) if len(p) > 1 else 60
        get_user(tg)["muted_until"] = int(time.time())+mn*60; save_db(); return send(pid, "[id" + str(tg) + "] мут " + str(mn) + " мин")
    if cmd in ("снятьмут","unmute"):
        if not is_ad(uid): return send(pid, "Только админ")
        tg = ex(args)
        if tg: get_user(tg)["muted_until"] = 0; save_db(); send(pid, "Размут [id" + str(tg) + "]")
        return True
    if cmd in ("снятьварн","unwarn"):
        if not is_ad(uid): return send(pid, "Только админ")
        tg = ex(args)
        if tg:
            tt = get_user(tg); tt["warns"] = max(0, tt["warns"]-1); save_db(); send(pid, "Варн снят [id" + str(tg) + "]")
        return True
    if cmd in ("кик","kick","бан","ban"):
        if not is_ad(uid): return send(pid, "Только админ")
        tg = ex(args)
        if not tg: return send(pid, "!кик @id")
        try:
            vk.messages.removeChatUser(chat_id=pid-2000000000, user_id=tg); send(pid, "[id" + str(tg) + "] кикнут")
        except Exception as e: send(pid, "Ошибка кика: " + str(e))
        return True
    if cmd in ("выдатьбаланс","givebalance"):
        if not is_ad(uid): return send(pid, "Только админ")
        p = args.split()
        if len(p) < 2: return send(pid, "!выдатьбаланс @id сумма")
        get_user(ex(p[0]))["balance"] += int(p[1]); save_db(); return send(pid, "Выдано " + fmt(p[1]) + " [id" + str(ex(p[0])) + "]")
    if cmd in ("забратьбаланс","takebalance"):
        if not is_ad(uid): return send(pid, "Только админ")
        p = args.split()
        if len(p) < 2: return send(pid, "!забратьбаланс @id сумма")
        tt = get_user(ex(p[0])); tt["balance"] = max(0, tt["balance"]-int(p[1])); save_db(); return send(pid, "Забрано " + fmt(p[1]))
    if cmd in ("выдатьдонат","givedonate"):
        if not is_own(uid): return send(pid, "Только владелец")
        p = args.split()
        if len(p) < 2: return send(pid, "!выдатьдонат @id сумма")
        get_user(ex(p[0]))["donate"] += int(p[1]); save_db(); return send(pid, "Донат +" + fmt(p[1]) + " [id" + str(ex(p[0])) + "]")
    if cmd in ("забратьдонат","takedonate"):
        if not is_own(uid): return send(pid, "Только владелец")
        p = args.split()
        if len(p) < 2: return send(pid, "!забратьдонат @id сумма")
        tt = get_user(ex(p[0])); tt["donate"] = max(0, tt["donate"]-int(p[1])); save_db(); return send(pid, "Донат -" + fmt(p[1]))
    if cmd in ("выдатьуровень","givelevel"):
        if not is_ad(uid): return send(pid, "Только админ")
        p = args.split()
        if len(p) < 2: return send(pid, "!выдатьуровень @id уровень")
        tt = get_user(ex(p[0])); tt["level"] = int(p[1]); tt["xp"] = int(p[1])**2; save_db(); return send(pid, "Уровень " + p[1] + " выдан")
    if cmd in ("выдатьрепу","giverep"):
        if not is_ad(uid): return send(pid, "Только админ")
        p = args.split()
        if len(p) < 2: return send(pid, "!выдатьрепу @id кол-во")
        get_user(ex(p[0]))["reputation"] += int(p[1]); save_db(); return send(pid, "Репа +" + p[1])
    if cmd in ("выдатьбизнес","givebusiness"):
        if not is_ad(uid): return send(pid, "Только админ")
        p = args.split()
        if len(p) < 2 or p[1].lower() not in BIZ: return send(pid, "!выдатьбизнес @id имя (см !бизнесы)")
        tt = get_user(ex(p[0])); tt["business"] = p[1].lower(); tt["business_time"] = int(time.time()); save_db()
        return send(pid, "Бизнес " + p[1] + " выдан [id" + str(ex(p[0])) + "]")
    if cmd in ("забратьбизнес","takebusiness"):
        if not is_ad(uid): return send(pid, "Только админ")
        tg = ex(args)
        if tg: get_user(tg)["business"] = None; save_db(); send(pid, "Бизнес забран [id" + str(tg) + "]")
        return True
    if cmd in ("выдатьимущество","giveproperty"):
        if not is_ad(uid): return send(pid, "Только админ")
        p = args.split()
        if len(p) < 3: return send(pid, "!выдатьимущество @id car|house|yacht|phone|pet имя")
        mp = {"car":CARS,"house":HOUSES,"yacht":YACHTS,"phone":PHONES,"pet":PETS}
        tp, nm = p[1].lower(), p[2].lower()
        if tp in mp and nm in mp[tp]:
            get_user(ex(p[0]))[tp] = nm; save_db(); return send(pid, nm + " выдан [id" + str(ex(p[0])) + "]")
        return send(pid, "Не найдено")
    if cmd in ("обнулить","reset"):
        if not is_ad(uid): return send(pid, "Только админ")
        tg = ex(args)
        if not tg: return send(pid, "!обнулить @id")
        d = dict(NEW); d["register_time"] = int(time.time()); DB["users"][str(tg)] = d; save_db()
        return send(pid, "[id" + str(tg) + "] обнулён")
    if cmd in ("админинфо","admininfo"):
        if not is_ad(uid): return send(pid, "Только админ")
        tg = ex(args)
        if not tg: return send(pid, "!админинфо @id")
        tt = get_user(tg)
        return send(pid, "АДМИН-ИНФО [id" + str(tg) + "]\nДеньги " + fmt(tt["balance"]) + " | Банк " + fmt(tt["bank"]) + " | Донат " + fmt(tt["donate"]) + "\nУровень " + str(tt["level"]) + " | Варны " + str(tt["warns"]) + " | Реп " + str(tt["reputation"]) + "\nБизнес " + str(tt["business"] or "-") + " | Машина " + str(tt["car"] or "-") + " | Дом " + str(tt["house"] or "-") + "\nЯхта " + str(tt["yacht"] or "-") + " | Телефон " + str(tt["phone"] or "-") + " | Питомец " + str(tt["pet"] or "-") + "\nБрак " + str(tt["married_to"] or "-") + " | Клан " + str(tt["clan_id"] or "-") + "\nПредметов " + str(len(tt["inventory"])) + " | Сообщений " + str(tt["messages_count"]) + "\nМут: " + ("да" if tt["muted_until"] > time.time() else "нет"))
    if cmd in ("создатьпромо","createpromo"):
        if not is_ad(uid): return send(pid, "Только админ")
        p = args.split()
        if len(p) < 4: return send(pid, "!создатьпромо КОД balance|business|level|donate ЗНАЧЕНИЕ КОЛ-ВО")
        if p[1] not in ("balance","business","level","donate"): return send(pid, "Тип: balance/business/level/donate")
        DB["promo"][p[0].upper()] = {"type":p[1],"value":p[2],"uses_left":int(p[3]),"creator":uid}
        save_db(); return send(pid, "Промо " + p[0].upper() + " создан: " + p[1] + " " + p[2] + " x" + p[3])
    if cmd in ("удалитьпромо","deletepromo"):
        if not is_ad(uid): return send(pid, "Только админ")
        c = args.upper().strip()
        if c in DB["promo"]:
            del DB["promo"][c]; save_db(); return send(pid, "Промо " + c + " удалён")
        return send(pid, "Не найден")
    if cmd in ("списокпромо","promos"):
        if not is_ad(uid): return send(pid, "Только админ")
        if not DB["promo"]: return send(pid, "Промо нет")
        return send(pid, "ПРОМО:\n" + "\n".join(["- " + c + ": " + p["type"] + " " + str(p["value"]) + " x" + str(p["uses_left"]) for c,p in DB["promo"].items()]))
    if cmd in ("добавитьадмина","addadmin"):
        if not is_own(uid): return send(pid, "Только владелец")
        tg = ex(args)
        if tg and tg not in DEVELOPERS:
            DEVELOPERS.append(tg); return send(pid, "[id" + str(tg) + "] теперь админ")
        return send(pid, "Не вышло")
    if cmd in ("списокадминов","admins"):
        return send(pid, "АДМИНЫ:\n" + "\n".join(["- [id" + str(a) + "]" + (" ВЛАДЕЛЕЦ" if a == OWNER_ID else "") for a in DEVELOPERS]))
    if cmd in ("рассылка","broadcast"):
        if not is_own(uid): return send(pid, "Только владелец")
        if not args: return send(pid, "Текст?")
        ok = 0
        for sid in list(DB["users"].keys()):
            try:
                vk.messages.send(peer_id=int(sid), message="РАССЫЛКА: " + args, random_id=0); ok += 1
            except Exception: pass
        return send(pid, "Отправлено " + str(ok) + " юзерам")
    return None

print("=" * 40)
print("ASTRA FULL запущена! Слушаю ЛС и ВСЕ беседы")
print("=" * 40)
for event in lp.listen():
    if event.type != VkEventType.MESSAGE_NEW: continue
    if not (event.from_user or event.from_chat): continue
    pid, uid = event.peer_id, event.user_id
    text = (event.text or "").strip()
    text = re.sub(r"^(\[club\d+\|[^\]]*\]|@club\S+)", "", text).strip()
    print("MSG peer=" + str(pid) + " user=" + str(uid) + " text=" + text)
    u = get_user(uid)
    if u["muted_until"] > time.time():
        try: vk.messages.delete(peer_id=pid, message_ids=event.message_id, delete_for_all=1)
        except Exception: pass
        continue
    low = text.lower()
    if any(w in low for w in MAT):
        u["mat_count"] += 1; save_db()
        try: vk.messages.delete(peer_id=pid, message_ids=event.message_id, delete_for_all=1)
        except Exception: pass
        send(pid, "[id" + str(uid) + "], без мата! (" + str(u["mat_count"]) + ")")
        continue
    u["xp"] += 5; u["messages_count"] += 1
    nl = int(u["xp"] ** 0.5)
    if nl > u["level"]:
        u["level"] = nl; send(pid, "Уровень " + str(nl) + "!")
    got = ach_check(u)
    if got: send(pid, "Ачивки: " + ", ".join(got))
    save_db()
    if not text: continue
    if text in BTNC:
        try: handle(pid, uid, BTNC[text], "")
        except Exception as e: print("BTN ERR:", e); traceback.print_exc()
        continue
    if low.startswith(PREFIX):
        parts = text[1:].strip().split(maxsplit=1)
        cmd = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""
        try: handle(pid, uid, cmd, args)
        except Exception as e:
            print("CMD ERR:", e); traceback.print_exc(); send(pid, "Ошибка: " + str(e))
