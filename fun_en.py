import re
import json
import time
import random
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

MENUS = {
    "main": "👋 Welcome! Choose a category below to see available commands:",
    "general": "👤 GENERAL:\n/profile — your stats & balance\n/stats — chat level & messages\n/nick [name] — set chat nickname\n/rules — view chat rules\n/staff — list chat moderators\n/rep @user — give reputation (+1)",
    "economy": "🏛 ECONOMY:\n/bonus — hourly reward\n/work — work every 10 min\n/bank [put/take] [amount]\n/pay @user [amount] — transfer coins\n/rob @user — steal coins\n/top — top 10 richest players",
    "games": "🎲 GAMES & FAMILY:\n/casino [bet/all] — slots x2/x5\n/roulette [red/black/green] [bet]\n/dice [1-6] [bet] — roll dice (x5)\n/duel @user [bet] — PvP battle\n/marry @user | /divorce — marriage\n/hug | /slap | /kiss @user — RP actions",
    "mod": "⚔️ MODERATION (Lvl 1-7):\n/mute @user [min] | /unmute\n/warn @user | /unwarn (Lvl 2+)\n/kick | /ban @user (Lvl 3+)\n/silence | /unsilence (Lvl 4+)\n/antilink | /all | /rules [text] | /welcome [text]\n/setlvl @user [0-6] (Lvl 6+)",
    "vip": "⭐ VIP & CLANS:\n/buyvip — buy VIP status (10,000 coins, 2x bonus & work)\n/clan create [name] (3,000 coins)\n/clan join [name] | /clan leave | /clan info"
}

def get_menu_kb():
    kb = VkKeyboard(inline=True)
    kb.add_callback_button("👤 General", color=VkKeyboardColor.POSITIVE, payload={"menu": "general"})
    kb.add_callback_button("🏛 Economy", color=VkKeyboardColor.SECONDARY, payload={"menu": "economy"})
    kb.add_line()
    kb.add_callback_button("🎲 Games / Family", color=VkKeyboardColor.SECONDARY, payload={"menu": "games"})
    kb.add_callback_button("⚔️ Moderation", color=VkKeyboardColor.SECONDARY, payload={"menu": "mod"})
    kb.add_line()
    kb.add_callback_button("⭐ VIP / Clans", color=VkKeyboardColor.NEGATIVE, payload={"menu": "vip"})
    return kb.get_keyboard()

def send_help_menu(vk, peer_id, category="main", event_id=None, user_id=None):
    text = MENUS.get(category, MENUS["main"])
    if event_id:
        vk.messages.sendMessageEventAnswer(event_id=event_id, user_id=user_id, peer_id=peer_id, event_data=json.dumps({"type": "show_snackbar", "text": f"Category: {category.upper()}"}))
    vk.messages.send(peer_id=peer_id, message=text, keyboard=get_menu_kb(), random_id=get_random_id())

def send_msg(vk, peer_id, text):
    vk.messages.send(peer_id=peer_id, message=text, random_id=get_random_id())

def get_user(db, user_id):
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {"balance": 1000, "bank": 0, "last_bonus": 0, "last_work": 0, "last_rob": 0, "partner": None, "clan": None, "rep": 0, "vip": False}
    return db["users"][uid]

def get_name(vk, user_id):
    if user_id < 0:
        return "Bot"
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
        vip_tag = "⭐ VIP" if user.get("vip") else "Regular"
        partner = get_name(vk, user["partner"]) if user.get("partner") else "None"
        clan = user.get("clan") or "None"
        send_msg(vk, peer_id, f"👤 {get_name(vk, from_id)} [{vip_tag}]\n💵 Cash: {user['balance']} | 🏦 Bank: {user.get('bank', 0)}\n🏰 Clan: {clan} | 💍 Married: {partner}\n⭐ Rep: {user.get('rep', 0)}")

    elif cmd == "bonus":
        if now - user["last_bonus"] < 3600:
            send_msg(vk, peer_id, f"⏳ Next bonus in {int((3600 - (now - user['last_bonus'])) // 60) + 1} min.")
        else:
            rew = random.randint(500, 1200) * mult
            user["balance"] += rew
            user["last_bonus"] = now
            save_db(db)
            send_msg(vk, peer_id, f"🎁 Bonus +{rew} coins! Balance: {user['balance']}")

    elif cmd == "work":
        if now - user.get("last_work", 0) < 600:
            send_msg(vk, peer_id, f"⏳ Rest for {int((600 - (now - user['last_work'])) // 60) + 1} min.")
        else:
            pay = random.randint(250, 600) * mult
            user["balance"] += pay
            user["last_work"] = now
            save_db(db)
            send_msg(vk, peer_id, f"💼 You worked and earned +{pay} coins! Balance: {user['balance']}")

    elif cmd == "bank":
        if len(args) < 2 or not args.isdigit():
            send_msg(vk, peer_id, "❌ Usage: /bank put 500 or /bank take 500")
            return
        act, amt = args.lower(), int(args)
        if act == "put" and 0 < amt <= user["balance"]:
            user["balance"] -= amt
            user["bank"] = user.get("bank", 0) + amt
            save_db(db)
            send_msg(vk, peer_id, f"🏦 Bank balance: {user['bank']} coins.")
        elif act == "take" and 0 < amt <= user.get("bank", 0):
            user["bank"] -= amt
            user["balance"] += amt
            save_db(db)
            send_msg(vk, peer_id, f"💵 Cash balance: {user['balance']} coins.")
        else:
            send_msg(vk, peer_id, "❌ Insufficient funds.")

    elif cmd == "pay":
        tid = extract_target(msg_obj, args)
        amt = next((int(a) for a in args if a.isdigit()), None)
        if not tid or not amt or tid == from_id or tid < 0 or amt <= 0 or amt > user["balance"]:
            send_msg(vk, peer_id, "❌ Usage: /pay @user 500")
            return
        get_user(db, tid)["balance"] += amt
        user["balance"] -= amt
        save_db(db)
        send_msg(vk, peer_id, f"✅ Sent {amt} coins -> {get_name(vk, tid)}")

    elif cmd == "rob":
        tid = extract_target(msg_obj, args)
        if not tid or tid == from_id or tid < 0 or now - user.get("last_rob", 0) < 1800:
            send_msg(vk, peer_id, "❌ Usage: /rob @user (30 min cooldown)")
            return
        victim = get_user(db, tid)
        user["last_rob"] = now
        if victim["balance"] < 100:
            send_msg(vk, peer_id, "🤷 Target has no cash on hand.")
            return
        if random.randint(1, 100) <= 40:
            loot = random.randint(50, min(600, victim["balance"] // 2))
            victim["balance"] -= loot
            user["balance"] += loot
            send_msg(vk, peer_id, f"🥷 Stole {loot} coins from {get_name(vk, tid)}!")
        else:
            fine = min(250, user["balance"])
            user["balance"] -= fine
            send_msg(vk, peer_id, f"🚓 Caught by police! Fined {fine} coins.")
        save_db(db)

    elif cmd == "top":
        top_u = sorted(db["users"].items(), key=lambda x: x["balance"] + x.get("bank", 0), reverse=True)[:10]
        lines = ["🏆 TOP 10 RICHEST:"] + [f"{i}. {get_name(vk, int(uid))} — {u['balance'] + u.get('bank', 0)} coins" for i, (uid, u) in enumerate(top_u, 1)]
        send_msg(vk, peer_id, "\n".join(lines))

    elif cmd == "casino":
        if not args:
            send_msg(vk, peer_id, "❌ Usage: /casino 300 or /casino all")
            return
        b_arg = args.pop(0).lower()
        bet = user["balance"] if b_arg == "all" else (int(b_arg) if b_arg.isdigit() else 0)
        if bet <= 0 or bet > user["balance"]:
            send_msg(vk, peer_id, "❌ Invalid bet.")
            return
        r = random.randint(1, 100)
        if r <= 45:
            user["balance"] += bet
            send_msg(vk, peer_id, f"🎰 Win +{bet} coins (x2)! Balance: {user['balance']}")
        elif r <= 50:
            user["balance"] += bet * 4
            send_msg(vk, peer_id, f"🔥 JACKPOT +{bet*4} coins (x5)! Balance: {user['balance']}")
        else:
            user["balance"] -= bet
            send_msg(vk, peer_id, f"📉 Lost -{bet} coins. Balance: {user['balance']}")
        save_db(db)

    elif cmd == "roulette":
        if len(args) < 2 or not args.isdigit() or args.lower() not in ["red", "black", "green"]:
            send_msg(vk, peer_id, "❌ Usage: /roulette [red/black/green] 200")
            return
        col, bet = args.lower(), int(args)
        if bet <= 0 or bet > user["balance"]:
            send_msg(vk, peer_id, "❌ Insufficient funds.")
            return
                roll = random.choices(["red", "black", "green"], weights=[48, 48, 4]).pop(0)

        if col == roll:
            win = bet * (13 if roll == "green" else 1)
            user["balance"] += win
            send_msg(vk, peer_id, f"🎡 Landed on {roll.upper()}! Won +{win} coins!")
        else:
            user["balance"] -= bet
            send_msg(vk, peer_id, f"🎡 Landed on {roll.upper()}. Lost -{bet} coins.")
        save_db(db)

    elif cmd == "dice":
        if len(args) < 2 or not args.isdigit() or not args.isdigit():
            send_msg(vk, peer_id, "❌ Usage: /dice [1-6] 200")
            return
        num, bet = int(args), int(args)
        if not (1 <= num <= 6) or bet <= 0 or bet > user["balance"]:
            send_msg(vk, peer_id, "❌ Pick 1-6 and valid bet.")
            return
        c = random.randint(1, 6)
        if num == c:
            user["balance"] += bet * 4
            send_msg(vk, peer_id, f"🎲 Rolled {c}! Exact match (x5): +{bet*4} coins!")
        else:
            user["balance"] -= bet
            send_msg(vk, peer_id, f"🎲 Rolled {c}. Lost -{bet} coins.")
        save_db(db)

    elif cmd == "duel":
        tid = extract_target(msg_obj, args)
