import re
import time
from vk_api.utils import get_random_id

LINKS_RE = re.compile(r"(https?://|vk\.me/|t\.me/|@all|@everyone)", re.I)

def send_msg(vk, peer_id, text):
    vk.messages.send(peer_id=peer_id, message=text, random_id=get_random_id())

def get_chat(db, peer_id):
    pid = str(peer_id)
    if pid not in db["chats"]:
        db["chats"][pid] = {"members": {}, "silence": False, "antilink": False, "rules": "No spam, respect others.", "welcome": "Welcome to the chat!"}
    return db["chats"][pid]

def get_member(chat, user_id):
    uid = str(user_id)
    if uid not in chat["members"]:
        chat["members"][uid] = {"lvl": 0, "warns": 0, "mute_until": 0, "msgs": 0, "nick": None}
    return chat["members"][uid]

def is_vk_admin(vk, peer_id, user_id):
    try:
        items = vk.messages.getConversationMembers(peer_id=peer_id)["items"]
        for i in items:
            if i["member_id"] == user_id:
                return i.get("is_admin", False) or i.get("is_owner", False)
    except Exception:
        return False
    return False

def get_lvl(vk, chat, peer_id, user_id):
    if is_vk_admin(vk, peer_id, user_id):
        return 7
    return get_member(chat, user_id).get("lvl", 0)

def get_name(vk, chat, user_id):
    if user_id < 0:
        return "Bot"
    m = get_member(chat, user_id)
    u = vk.users.get(user_ids=user_id).pop(0)
    disp = m["nick"] if m.get("nick") else f"{u['first_name']} {u['last_name']}"
    return f"[id{user_id}|{disp}]"

def extract_target(msg_obj, args):
    if "reply_message" in msg_obj:
        return msg_obj["reply_message"]["from_id"]
    if args:
        match = re.search(r"\[id(\d+)\|", " ".join(args))
        if match:
            return int(match.group(1))
    return None

def handle_mod(vk, db, save_db, msg_obj):
    peer_id = msg_obj["peer_id"]
    from_id = msg_obj["from_id"]
    text = msg_obj.get("text", "").strip()

    if peer_id < 2000000000:
        return False

    chat = get_chat(db, peer_id)

    if "action" in msg_obj and msg_obj["action"].get("type") in ["chat_invite_user", "chat_invite_user_by_link"]:
        nid = msg_obj["action"].get("member_id", from_id)
        if nid > 0:
            send_msg(vk, peer_id, f"👋 {get_name(vk, chat, nid)}, {chat['welcome']}")
        return True

    if from_id < 0:
        return True

    member = get_member(chat, from_id)
    member["msgs"] += 1
    lvl = get_lvl(vk, chat, peer_id, from_id)

    if lvl == 0:
        if member["mute_until"] > time.time() or chat.get("silence") or (chat.get("antilink") and LINKS_RE.search(text)):
            try:
                vk.messages.delete(peer_id=peer_id, cmids=msg_obj["conversation_message_id"], delete_for_all=1)
            except Exception:
                pass
            return True

    if not text.startswith("/"):
        return False

    parts = text[1:].split()
    if not parts:
        return False
    cmd = parts.pop(0).lower()
    args = parts
    chat_id = peer_id - 2000000000

    if cmd == "rules" and not args:
        send_msg(vk, peer_id, f"📜 Chat Rules:\n{chat['rules']}")
        return True
    elif cmd == "stats":
        send_msg(vk, peer_id, f"📊 {get_name(vk, chat, from_id)}\n🎖 Access Level: {lvl}/7\n💬 Messages: {member['msgs']}\n⚠️ Warns: {member['warns']}/3")
        return True
    elif cmd == "nick":
        member["nick"] = " ".join(args)[:25] if args else None
        save_db(db)
        send_msg(vk, peer_id, f"✅ Nickname updated: {get_name(vk, chat, from_id)}")
        return True
    elif cmd == "staff":
        lines = ["🛡 CHAT STAFF (Levels 1-7):"]
        for uid, m in chat["members"].items():
            if m.get("lvl", 0) > 0:
                lines.append(f"• {get_name(vk, chat, int(uid))} — Level {m['lvl']}")
        send_msg(vk, peer_id, "\n".join(lines) if len(lines) > 1 else "🛡 No custom staff assigned yet (only VK admins).")
        return True

    mod_cmds = ["mute", "unmute", "warn", "unwarn", "kick", "ban", "silence", "unsilence", "antilink", "welcome", "rules", "all", "setlvl"]
    if cmd not in mod_cmds:
        return False

    if lvl < 1:
        send_msg(vk, peer_id, "⛔ Access denied (Level 1+ required).")
        return True

    if cmd in ["silence", "unsilence", "antilink", "welcome", "rules", "all"]:
        if lvl < 4:
            send_msg(vk, peer_id, "⛔ Level 4+ required.")
            return True
        if cmd == "silence":
            chat["silence"] = True
            save_db(db)
            send_msg(vk, peer_id, "🤫 Silence mode ON. Only staff (Lvl 1+) can chat.")
        elif cmd == "unsilence":
            chat["silence"] = False
            save_db(db)
            send_msg(vk, peer_id, "💬 Silence mode OFF!")
        elif cmd == "antilink":
            chat["antilink"] = not chat.get("antilink", False)
            save_db(db)
            send_msg(vk, peer_id, f"🔗 Anti-Link: {'ON ✅' if chat['antilink'] else 'OFF ❌'}")
        elif cmd == "welcome":
            chat["welcome"] = " ".join(args) if args else "Welcome to the chat!"
            save_db(db)
            send_msg(vk, peer_id, "✅ Welcome message updated.")
        elif cmd == "rules":
            chat["rules"] = " ".join(args)
            save_db(db)
            send_msg(vk, peer_id, "✅ Rules updated.")
        elif cmd == "all":
            items = vk.messages.getConversationMembers(peer_id=peer_id)["items"]
            tags = [f"[id{i['member_id']}|🔔]" for i in items if i["member_id"] > 0]
            send_msg(vk, peer_id, "📢 Attention everyone!\n" + " ".join(tags))
        return True

    tid = extract_target(msg_obj, args)
    if not tid or tid == from_id or tid < 0:
        send_msg(vk, peer_id, "❌ Tag a user (@user) or reply to their message.")
        return True

    t_lvl = get_lvl(vk, chat, peer_id, tid)
    if t_lvl >= lvl:
        send_msg(vk, peer_id, "⛔ Cannot target a user with equal or higher level.")
        return True

    tm = get_member(chat, tid)

    if cmd == "setlvl" and lvl >= 6:
        new_l = next((int(a) for a in args if a.isdigit() and 0 <= int(a) <= 6), None)
        if new_l is None or new_l >= lvl:
            send_msg(vk, peer_id, "❌ Usage: /setlvl @user [0-6]")
            return True
        tm["lvl"] = new_l
        save_db(db)
        send_msg(vk, peer_id, f"🎖 {get_name(vk, chat, tid)} is now Level {new_l}!")
    elif cmd == "mute":
        mins = next((int(a) for a in args if a.isdigit()), 15)
        tm["mute_until"] = time.time() + mins * 60
        save_db(db)
        send_msg(vk, peer_id, f"🔇 {get_name(vk, chat, tid)} muted for {mins} min.")
    elif cmd == "unmute":
        tm["mute_until"] = 0
        save_db(db)
        send_msg(vk, peer_id, f"🔊 {get_name(vk, chat, tid)} unmuted.")
    elif cmd == "warn":
        tm["warns"] += 1
        if tm["warns"] >= 3:
            tm["warns"] = 0
            save_db(db)
            try:
                vk.messages.removeChatUser(chat_id=chat_id, member_id=tid)
                send_msg(vk, peer_id, f"🚨 {get_name(vk, chat, tid)} reached 3/3 warns and was kicked!")
            except Exception:
                send_msg(vk, peer_id, f"🚨 {get_name(vk, chat, tid)} reached 3/3 warns!")
        else:
            save_db(db)
            send_msg(vk, peer_id, f"⚠️ {get_name(vk, chat, tid)} warned ({tm['warns']}/3).")
    elif cmd == "unwarn":
        tm["warns"] = 0
        save_db(db)
        send_msg(vk, peer_id, f"🛡 Warns cleared for {get_name(vk, chat, tid)}.")
    elif cmd in ["kick", "ban"] and lvl >= 3:
        try:
            vk.messages.removeChatUser(chat_id=chat_id, member_id=tid)
            send_msg(vk, peer_id, f"🔨 {get_name(vk, chat, from_id)} kicked {get_name(vk, chat, tid)}.")
        except Exception as e:
            send_msg(vk, peer_id, f"❌ Kick error: {e}")

    return True
