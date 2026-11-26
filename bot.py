import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json, time, os, re, random, threading, traceback

# ═══════════ КОНФИГ ═══════════
TOKEN = os.environ.get("VK_TOKEN", "")
DEVELOPERS = [int(x) for x in os.environ.get("DEVELOPERS", "0").split(",") if x]
PREFIX = "!"

if not TOKEN:
    print("❌ VK_TOKEN пуст! Добавь переменную окружения VK_TOKEN на Render.")
    raise SystemExit(1)

# ═══════════ БД (json) ═══════════
DB_FILE = "db.json"
def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "promo": {}}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(DB, f, ensure_ascii=False, indent=2)

DB = load_db()

def get_user(uid):
    s = str(uid)
    if s not in DB["users"]:
        DB["users"][s] = {"balance":1000,"bank":0,"xp":0,"level":0,"warns":0,
            "reputation":0,"business":None,"business_time":0,"work_time":0,
            "bonus_time":0,"deposit":0,"deposit_time":0,"car":None,"house":None,
            "yacht":None,"phone":None,"married_to":0,"clan_id":0,"inventory":{},
            "muted_until":0,"messages_count":0}
        save_db()
    return DB["users"][s]

def extract_user(text):
    m = re.search(r"(?:@id|id)(\d+)", text)
    return int(m.group(1)) if m else None

def is_admin(uid): return uid in DEVELOPERS
def fmt(n): return f"{n:,}".replace(",", " ")

# ═══════════ ДАННЫЕ ═══════════
BUSINESSES = {"ларёк":{"price":10000,"income":800},"кафе":{"price":50000,"income":4500},
    "магазин":{"price":200000,"income":20000},"ресторан":{"price":750000,"income":80000},
    "завод":{"price":2500000,"income":280000},"банк":{"price":10000000,"income":1200000}}
CARS = {"велик":5000,"самокат":15000,"жигуль":80000,"тойота":500000,"бмв":2000000,"мерседес":5000000}
HOUSES = {"палатка":10000,"квартира":250000,"дом":1500000,"особняк":15000000}
CASES = {"деревянный":{"price":1000,"min":500,"max":5000},
    "железный":{"price":10000,"min":5000,"max":50000},"золотой":{"price":100000,"min":50000,"max":500000}}

# ═══════════ FLASK (для Render) ═══════════
try:
    from flask import Flask
    app = Flask("")
    @app.route("/")
    def home(): return "🌟 Astra alive!"
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080), daemon=True).start()
    print("🌐 Flask на :8080")
except Exception as e:
    print("⚠️ Flask нет:", e)

# ═══════════ VK ═══════════
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)
print("🌟 Astra запущена!")

def get_kb():
    kb = VkKeyboard(inline=True)
    kb.add_button("💰 Баланс", VkKeyboardColor.PRIMARY)
    kb.add_button("💼 Работа", VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_button("👤 Профиль", VkKeyboardColor.SECONDARY)
    kb.add_button("🎁 Промокод", VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()

def send(peer_id, msg, kb=None):
    kw = {"peer_id": peer_id, "message": msg, "random_id": 0}
    if kb: kw["keyboard"] = kb
    vk.messages.send(**kw)

# ═══════════ ОБРАБОТКА ═══════════
def handle(peer_id, user_id, cmd, args):
    u = get_user(user_id)

    # ── ЭКОНОМИКА ──
    if cmd in ("баланс","balance"):
        t = get_user(extract_user(args) or user_id)
        send(peer_id, f"💰 Баланс: {fmt(t['balance'])} ₽\n🏦 Банк: {fmt(t['bank'])} ₽\n"
             f"📊 Ур. {t['level']} ({t['xp']} XP)\n🏢 {t['business'] or '—'}\n"
             f"🚗 {t['car'] or '—'} | 🏠 {t['house'] or '—'}", get_kb())

    elif cmd in ("работа","work"):
        if time.time()-u["work_time"] < 1800:
            return send(peer_id, "⏳ Отдыхай!")
        earn = 200+u["level"]*20+random.randint(0,100)
        u["balance"]+=earn; u["work_time"]=int(time.time()); save_db()
        send(peer_id, f"💼 Заработано {fmt(earn)} ₽")

    elif cmd in ("бонус","bonus"):
        if time.time()-u["bonus_time"] < 86400:
            return send(peer_id, "⏳ Бонус раз в сутки")
        b=500+u["level"]*100; u["balance"]+=b; u["bonus_time"]=int(time.time()); save_db()
        send(peer_id, f"🎁 Бонус {fmt(b)} ₽")

    elif cmd in ("бизнесы","businesses"):
        txt="🏢 Бизнесы:\n"
        for n,b in BUSINESSES.items(): txt+=f"• {n} — {fmt(b['price'])} ₽ ({fmt(b['income'])}/ч)\n"
        send(peer_id, txt+"\n!купить <название>")

    elif cmd in ("купить","buy"):
        n=args.lower().strip()
        if n in BUSINESSES:
            if u["balance"]<BUSINESSES[n]["price"]: return send(peer_id,"💸 Не хватает")
            if u["business"]: return send(peer_id,"Уже есть бизнес")
            u["balance"]-=BUSINESSES[n]["price"]; u["business"]=n; u["business_time"]=int(time.time())
            save_db(); send(peer_id, f"🎉 Куплен {n}")
        elif n in CARS:
            if u["balance"]<CARS[n]: return send(peer_id,"💸 Не хватает")
            u["balance"]-=CARS[n]; u["car"]=n; save_db(); send(peer_id, f"🚗 Куплено: {n}")
        elif n in HOUSES:
            if u["balance"]<HOUSES[n]: return send(peer_id,"💸 Не хватает")
            u["balance"]-=HOUSES[n]; u["house"]=n; save_db(); send(peer_id, f"🏠 Куплено: {n}")
        else: send(peer_id, "❌ Не найдено")

    elif cmd in ("доход","income"):
        if not u["business"]: return send(peer_id,"Нет бизнеса")
        h=int((time.time()-u["business_time"])//3600)
        if h<1: return send(peer_id,"Рано")
        e=BUSINESSES[u["business"]]["income"]*h; u["balance"]+=e; u["business_time"]=int(time.time())
        save_db(); send(peer_id, f"💵 Доход {fmt(e)} ₽")

    elif cmd in ("перевод","transfer"):
        p=args.split()
        if len(p)<2: return send(peer_id,"!перевод @id123 сумма")
        tg=extract_user(p[0]); amt=int(p[1])
        if amt<100 or u["balance"]<amt: return send(peer_id,"💸")
        tax=int(amt*0.05); u["balance"]-=amt; t=get_user(tg); t["balance"]+=amt-tax
        save_db(); send(peer_id, f"✅ Переведено {fmt(amt-tax)} ₽")

    elif cmd in ("профиль","profile"):
        t=get_user(extract_user(args) or user_id)
        send(peer_id, f"👤 [id{t and user_id}|Профиль]\n💰 {fmt(t['balance'])} ₽\n"
             f"📊 Ур. {t['level']}\n⚠️ Варны {t['warns']}/3\n⭐ Реп {t['reputation']}")

    elif cmd in ("топ","top"):
        rows=sorted(DB["users"].items(), key=lambda x:x[1]["balance"], reverse=True)[:10]
        txt="🏆 Топ:\n"
        for i,(uid,d) in enumerate(rows,1): txt+=f"{i}. [id{uid}] {fmt(d['balance'])} ₽\n"
        send(peer_id, txt)

    elif cmd in ("кейс","case"):
        n=args.lower().strip()
        if n not in CASES: return send(peer_id,"❌ Кейсы: деревянный/железный/золотой")
        c=CASES[n]
        if u["balance"]<c["price"]: return send(peer_id,"💸")
        u["balance"]-=c["price"]; w=random.randint(c["min"],c["max"]); u["balance"]+=w
        save_db(); send(peer_id, f"🎁 {n}: выпало {fmt(w)} ₽")

    # ── ИГРЫ ──
    elif cmd in ("монетка","coin","flip"):
        try: bet=int(args)
        except: return send(peer_id,"!монетка <ставка>")
        if bet<50 or u["balance"]<bet: return send(peer_id,"💸")
        if random.choice([True,False]): u["balance"]+=bet; send(peer_id,f"🪙 Орёл! +{fmt(bet)}")
        else: u["balance"]-=bet; send(peer_id,f"🪙 Решка! -{fmt(bet)}")
        save_db()

    elif cmd in ("казино","slots","casino"):
        try: bet=int(args)
        except: return send(peer_id,"!казино <ставка>")
        if bet<100 or u["balance"]<bet: return send(peer_id,"💸")
        s=[random.choice("🍒🍋🔔") for _ in range(3)]
        if s[0]==s[1]==s[2]: u["balance"]+=bet*5; send(peer_id,f"{''.join(s)} ДЖЕКПОТ +{fmt(bet*5)}")
        elif s[0]==s[1] or s[1]==s[2]: u["balance"]+=bet; send(peer_id,f"{''.join(s)} +{fmt(bet)}")
        else: u["balance"]-=bet; send(peer_id,f"{''.join(s)} -{fmt(bet)}")
        save_db()

    elif cmd in ("кости","dice"):
        try: bet=int(args)
        except: return send(peer_id,"!кости <ставка>")
        if bet<100 or u["balance"]<bet: return send(peer_id,"💸")
        d=random.randint(1,6)
        if d>=4: u["balance"]+=bet; send(peer_id,f"🎲 {d} — выиграл +{fmt(bet)}")
        else: u["balance"]-=bet; send(peer_id,f"🎲 {d} — проиграл -{fmt(bet)}")
        save_db()

    # ── ПРОМОКОДЫ ──
    elif cmd in ("активировать","промо","promo"):
        code=args.upper().strip()
        if code not in DB["promo"]: return send(peer_id,"❌ Промо не найден")
        p=DB["promo"][code]
        if p["uses_left"]<=0: return send(peer_id,"❌ Исчерпан")
        if p["reward_type"]=="balance":
            u["balance"]+=int(p["reward_value"]); msg=f"💰 +{p['reward_value']} ₽"
        elif p["reward_type"]=="business":
            u["business"]=p["reward_value"]; msg=f"🏢 {p['reward_value']}"
        p["uses_left"]-=1; save_db(); send(peer_id, f"🎁 {msg}")

    elif cmd in ("создатьпромо","createpromo"):
        if not is_admin(user_id): return send(peer_id,"🚫")
        p=args.split()
        if len(p)<4: return send(peer_id,"!создатьпромо КОД balance|business ЗНАЧЕНИЕ КОЛ-ВО")
        DB["promo"][p[0].upper()]={"reward_type":p[1],"reward_value":p[2],"uses_left":int(p[3]),"creator":user_id}
        save_db(); send(peer_id, f"✅ Промо {p[0].upper()} ({p[3]} шт.)")

    # ── МОДЕРАЦИЯ ──
    elif cmd in ("варн","warn"):
        if not is_admin(user_id): return send(peer_id,"🚫")
        tg=extract_user(args)
        if not tg: return send(peer_id,"!варн @id123")
        t=get_user(tg); t["warns"]+=1; save_db()
        send(peer_id, f"⚠️ [id{tg}] варн {t['warns']}/3")
        if t["warns"]>=3:
            t["muted_until"]=int(time.time())+3600; t["warns"]=0; save_db()
            send(peer_id, f"🚫 [id{tg}] мут 1ч за 3 варна")

    elif cmd in ("мут","mute"):
        if not is_admin(user_id): return send(peer_id,"🚫")
        p=args.split(); tg=extract_user(p[0]) if p else None
        if not tg: return send(peer_id,"!мут @id123 мин")
        mins=int(p[1]) if len(p)>1 else 60
        get_user(tg)["muted_until"]=int(time.time())+mins*60; save_db()
        send(peer_id, f"🔇 [id{tg}] мут {mins} мин")

    elif cmd in ("снятьмут","unmute"):
        if not is_admin(user_id): return send(peer_id,"🚫")
        tg=extract_user(args)
        if tg: get_user(tg)["muted_until"]=0; save_db(); send(peer_id, f"✅ Мут снят [id{tg}]")

    elif cmd in ("снятьварн","unwarn"):
        if not is_admin(user_id): return send(peer_id,"🚫")
        tg=extract_user(args)
        if tg:
            t=get_user(tg); t["warns"]=max(0,t["warns"]-1); save_db()
            send(peer_id, f"✅ Варн снят [id{tg}]")

    elif cmd in ("кик","kick","бан"):
        if not is_admin(user_id): return send(peer_id,"🚫")
        tg=extract_user(args)
        if not tg: return send(peer_id,"!кик @id123")
        try:
            vk.messages.removeChatUser(chat_id=peer_id-2000000000, user_id=tg)
            send(peer_id, f"🔨 [id{tg}] удалён")
        except Exception as e: send(peer_id, f"❌ {e}")

    # ── АДМИН-ВЫДАЧА ──
    elif cmd in ("выдатьбаланс","givebalance"):
        if not is_admin(user_id): return send(peer_id,"🚫")
        p=args.split(); tg=extract_user(p[0]); amt=int(p[1])
        get_user(tg)["balance"]+=amt; save_db()
        send(peer_id, f"✅ Выдано {fmt(amt)} ₽ [id{tg}]")

    elif cmd in ("забратьбаланс","takebalance"):
        if not is_admin(user_id): return send(peer_id,"🚫")
        p=args.split(); tg=extract_user(p[0]); amt=int(p[1])
        t=get_user(tg); t["balance"]=max(0,t["balance"]-amt); save_db()
        send(peer_id, f"✅ Забрано {fmt(amt)} ₽ у [id{tg}]")

    elif cmd in ("выдатьуровень","givelevel"):
        if not is_admin(user_id): return send(peer_id,"🚫")
        p=args.split(); tg=extract_user(p[0]); lv=int(p[1])
        t=get_user(tg); t["level"]=lv; t["xp"]=lv*lv; save_db()
        send(peer_id, f"✅ Ур. {lv} выдан [id{tg}]")

    elif cmd in ("выдатьбизнес","givebusiness"):
        if not is_admin(user_id): return send(peer_id,"🚫")
        p=args.split(); tg=extract_user(p[0]); biz=p[1].lower()
        if biz in BUSINESSES:
            get_user(tg)["business"]=biz; get_user(tg)["business_time"]=int(time.time()); save_db()
            send(peer_id, f"✅ Бизнес {biz} выдан [id{tg}]")
        else: send(peer_id,"❌ Бизнес не найден")

    elif cmd in ("выдатьимущество","giveproperty"):
        if not is_admin(user_id): return send(peer_id,"🚫")
        p=args.split(); tg=extract_user(p[0]); typ=p[1].lower(); nm=p[2].lower()
        t=get_user(tg)
        if typ=="car" and nm in CARS: t["car"]=nm
        elif typ=="house" and nm in HOUSES: t["house"]=nm
        else: return send(peer_id,"❌ (car/house)")
        save_db(); send(peer_id, f"✅ {nm} выдан [id{tg}]")

    elif cmd in ("обнулить","reset"):
        if not is_admin(user_id): return send(peer_id,"🚫")
        tg=extract_user(args)
        if tg:
            DB["users"][str(tg)]={"balance":1000,"bank":0,"xp":0,"level":0,"warns":0,"reputation":0,
                "business":None,"business_time":0,"work_time":0,"bonus_time":0,"deposit":0,
                "deposit_time":0,"car":None,"house":None,"yacht":None,"phone":None,"married_to":0,
                "clan_id":0,"inventory":{},"muted_until":0,"messages_count":0}
            save_db(); send(peer_id, f"✅ [id{tg}] обнулён")

    elif cmd in ("админинфо","admininfo"):
        if not is_admin(user_id): return send(peer_id,"🚫")
        tg=extract_user(args)
        if not tg: return send(peer_id,"!админинфо @id123")
        t=get_user(tg)
        send(peer_id, f"👤 [id{tg}]\n💰 {fmt(t['balance'])} ₽\n📊 Ур.{t['level']}\n"
             f"⚠️ Варны {t['warns']}\n🏢 {t['business'] or '—'}\n🚗 {t['car'] or '—'}\n"
             f"🔇 Мут: {'да' if t['muted_until']>time.time() else 'нет'}")

    elif cmd in ("помощь","help"):
        send(peer_id, "🌟 Команды: !баланс !работа !бонус !бизнесы !купить !доход "
             "!перевод !профиль !топ !кейс !монетка !казино !кости !активировать\n"
             "Админ: !варн !мут !кик !выдатьбаланс !создатьпромо !обнулить")

# ═══════════ ЦИКЛ ═══════════
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
        peer_id, user_id, text = event.peer_id, event.user_id, event.text.strip()
        u = get_user(user_id)
        if u["muted_until"] > time.time():
            try: vk.messages.delete(peer_id=peer_id, message_ids=event.message_id, delete_for_all=1)
            except: pass
            continue
        u["xp"]+=5; u["messages_count"]+=1
        nl=int(u["xp"]**0.5)
        if nl>u["level"]:
            u["level"]=nl; send(peer_id, f"🎉 Уровень {nl}!")
        save_db()
        if not text.lower().startswith(PREFIX): continue
        parts=text[1:].strip().split(maxsplit=1)
        cmd=parts[0].lower() if parts else ""
        args=parts[1] if len(parts)>1 else ""
        try:
            handle(peer_id, user_id, cmd, args)
        except Exception as e:
            print("ERROR:", e); traceback.print_exc()
