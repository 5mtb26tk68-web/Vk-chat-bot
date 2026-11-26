import re
import time
from vk_api.utils import get_random_id

LINKS_RE = re.compile(r"(https?://|vk\.me/|t\.me/|@all|@everyone)", re.I)
BAD_WORDS = ["блять", "сука", "хуй", "пизд", "ебат", "ебан", "бляд", "нахуй"]

def send_msg(vk, peer_id, text):
    vk.messages.send(peer_id=peer_id, message=text, random_id=get_random_id())

def get_chat(db, peer_id):
    pid = str(peer_id)
    if pid not in db["chats"]:
        db["chats"][pid] = {"members": {}, "roles": {}, "banned": [], "silence": False, "antilink": False, "antimat": False, "rules": "Правила беседы не заданы.", "welcome": "Добро пожаловать в беседу!"}
    c = db["chats"][pid]
    for k, v in [("roles", {}), ("banned", []), ("antimat", False), ("antilink", False), ("silence", False)]:
        if k not in c:
            c[k] = v
    return c

def get_member(chat, user_id):
    uid = str(user_id)
    if uid not in chat["members"]:
        chat["members"][uid] = {"lvl": 0, "warns": 0, "mute_until": 0, "msgs": 0, "xp": 0, "nick": None, "role": None}
    m = chat["members"][uid]
    if "xp" not in m:
        m["xp"] = m.get("msgs", 0) * 10
    if "role" not in m:
        m["role"] = None
    return m

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

def get_priority(vk, chat, peer_id, user_id):
    if is_vk_admin(vk, peer_id, user_id):
        return 100
    m = get_member(chat, user_id)
    r_name = m.get("role")
    if r_name and r_name in chat["roles"]:
        return chat["roles"][r_name]
    return m.get("lvl", 0) * 10

def get_name(vk, chat, user_id):
    if user_id < 0:
        return "Бот"
    m = get_member(chat, user_id)
    u = vk.users.get(user_ids=user_id).pop(0)
    disp = m["nick"] if m.get("nick") else f"{u['first_name']} {u['last_name']}"
    r_name = m.get("role")
    if r_name:
        prio = chat["roles"].get(r_name, 0)
        return f"[{r_name} • {prio}] [id{user_id}|{disp}]"
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
    chat_id = peer_id - 2000000000

    if "action" in msg_obj and msg_obj["action"].get("type") in ["chat_invite_user", "chat_invite_user_by_link"]:
        nid = msg_obj["action"].get("member_id", from_id)
        if nid > 0:
            if nid in chat["banned"]:
                try:
                    vk.messages.removeChatUser(chat_id=chat_id, member_id=nid)
                    send_msg(vk, peer_id, f"🚫 {get_name(vk, chat, nid)} в ЧС чата и был исключён!")
                except Exception:
                    pass
                return True
            send_msg(vk, peer_id, f"✨ Приветствуем, {get_name(vk, chat, nid)}!\n💬 {chat['welcome']}")
        return True

    if from_id < 0:
        return True

    member = get_member(chat, from_id)
    member["msgs"] += 1
    member["xp"] += 15
    lvl = get_lvl(vk, chat, peer_id, from_id)
    prio = get_priority(vk, chat, peer_id, from_id)

    if lvl == 0 and prio < 10:
        has_bad = chat.get("antimat") and any(w in text.lower() for w in BAD_WORDS)
        has_link = chat.get("antilink") and LINKS_RE.search(text)
        if member["mute_until"] > time.time() or chat.get("silence") or has_link or has_bad:
            try:
                vk.messages.delete(peer_id=peer_id, cmids=msg_obj["conversation_message_id"], delete_for_all=1)
                if has_bad:
                    send_msg(vk, peer_id, f"🤬 {get_name(vk, chat, from_id)}, мат запрещён!")
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

    if cmd == "rules" and not args:
        send_msg(vk, peer_id, f"📜 ПРАВИЛА БЕСЕДЫ:\n━━━━━━━━━━━━━━\n{chat['rules']}")
        return True
    elif cmd == "stats":
        c_lvl = member["xp"] // 500 + 1
        r_txt = f"{member['role']} (приоритет {prio})" if member.get("role") else f"Нет (приоритет {prio})"
        send_msg(vk, peer_id, f"📊 СТАТИСТИКА В БЕСЕДЕ\n━━━━━━━━━━━━━━\n👤 Игрок: {get_name(vk, chat, from_id)}\n🏷 Роль: {r_txt}\n🎖 Ранг модератора: {lvl}/7\n🔥 Уровень общения: {c_lvl} ({member['xp']} XP)\n💬 Сообщений: {member['msgs']}\n⚠️ Варнов: {member['warns']}/3")
        return True
    elif cmd == "roles":
        sorted_r = sorted(chat["roles"].items(), key=lambda x: x[1], reverse=True)
        lines = ["🏷 ИЕРАРХИЯ РОЛЕЙ ЧАТА (1–100):", "━━━━━━━━━━━━━━"]
        for r_name, r_p in sorted_r:
            holders = [get_name(vk, chat, int(u)) for u, m in chat["members"].items() if m.get("role") == r_name]
            h_str = ", ".join(holders) if holders else "никого"
            lines.append(f"▸ [{r_p}] {r_name} — {h_str}")
        send_msg(vk, peer_id, "\n".join(lines) if len(lines) > 2 else "🏷 Роли ещё не созданы.\nСоздать: /createrole [1-99] [Название]")
        return True
    elif cmd == "topchat":
        top_m = sorted(chat["members"].items(), key=lambda x: x[1]["msgs"], reverse=True)[:10]
        lines = ["💬 ТОП-10 АКТИВНЫХ В ЧАТЕ:", "━━━━━━━━━━━━━━"] + [f"{i}. {get_name(vk, chat, int(uid))} — {m['msgs']} сообщ." for i, (uid, m) in enumerate(top_m, 1)]
        send_msg(vk, peer_id, "\n".join(lines))
        return True
    elif cmd == "chatinfo":
        s_on = "ВКЛ ✅" if chat["silence"] else "ВЫКЛ ❌"
        l_on = "ВКЛ ✅" if chat["antilink"] else "ВЫКЛ ❌"
        m_on = "ВКЛ ✅" if chat["antimat"] else "ВЫКЛ ❌"
        send_msg(vk, peer_id, f"⚙ НАСТРОЙКИ БЕСЕДЫ\n━━━━━━━━━━━━━━\n🤫 Тихий режим: {s_on}\n🔗 Антиссылка: {l_on}\n🤬 Антимат: {m_on}\n🏷 Создано ролей: {len(chat['roles'])}\n⛔ В ЧС чата: {len(chat['banned'])} чел.")
        return True
    elif cmd == "nick":
        member["nick"] = " ".join(args)[:25] if args else None
        save_db(db)
        send_msg(vk, peer_id, f"✅ Твой ник в беседе: {get_name(vk, chat, from_id)}")
        return True
    elif cmd == "staff":
        lines = ["🛡 АДМИНИСТРАЦИЯ ЧАТА (1–7 ранг):", "━━━━━━━━━━━━━━"]
        for uid, m in chat["members"].items():
            if m.get("lvl", 0) > 0:
                lines.append(f"▸ {get_name(vk, chat, int(uid))} — [{m['lvl']} ранг]")
        send_msg(vk, peer_id, "\n".join(lines) if len(lines) > 2 else "🛡 Назначенных модераторов нет (действуют админы ВК).")
        return True

    mod_cmds = ["mute", "unmute", "warn", "unwarn", "kick", "ban", "cban", "cunban", "silence", "unsilence", "antilink", "antimat", "welcome", "rules", "all", "setlvl", "inactive", "createrole", "delrole", "giverole", "takerole"]
    if cmd not in mod_cmds:
        return False

    if lvl < 1 and prio < 10:
        send_msg(vk, peer_id, "⛔ Недостаточно прав.")
        return True

    # Создание и удаление шаблонов ролей (Приоритет 70+ или Ранг 5+)
    if cmd == "createrole":
        if lvl < 5 and prio < 70:
            send_msg(vk, peer_id, "⛔ Создавать роли могут только модераторы 5+ ранга или с приоритетом 70+.")
            return True
        if len(args) < 2 or not args[0].isdigit():
            send_msg(vk, peer_id, "❌ Пример: /createrole 80 Старший Админ (приоритет 1–99)")
            return True
        r_prio = int(args.pop(0))
        r_name = " ".join(args)[:25].strip()
        if not (1 <= r_prio <= 99) or r_prio >= prio or not r_name:
            send_msg(vk, peer_id, f"❌ Приоритет должен быть от 1 до {prio - 1}!")
            return True
        chat["roles"][r_name] = r_prio
        save_db(db)
        send_msg(vk, peer_id, f"✅ Создана роль «{r_name}» с приоритетом [{r_prio}/100]!")
        return True
    elif cmd == "delrole":
        if lvl < 5 and prio < 70:
            send_msg(vk, peer_id, "⛔ Недостаточно прав.")
            return True
        r_name = " ".join(args).strip()
        if r_name not in chat["roles"]:
            send_msg(vk, peer_id, "❌ Такой роли нет в списке /roles.")
            return True
        if chat["roles"][r_name] >= prio:
            send_msg(vk, peer_id, "⛔ Нельзя удалить роль с приоритетом выше или равным твоему.")
            return True
        del chat["roles"][r_name]
        for m in chat["members"].values():
            if m.get("role") == r_name:
                m["role"] = None
        save_db(db)
        send_msg(vk, peer_id, f"🗑 Роль «{r_name}» полностью удалена.")
        return True

    if cmd in ["silence", "unsilence", "antilink", "antimat", "welcome", "rules", "all", "inactive"]:
        if lvl < 4 and prio < 50:
            send_msg(vk, peer_id, "⛔ Требуется 4+ ранг или приоритет 50+.")
            return True
        if cmd == "silence":
            chat["silence"] = True
            save_db(db)
            send_msg(vk, peer_id, "🤫 Тихий режим ВКЛЮЧЁН.")
        elif cmd == "unsilence":
            chat["silence"] = False
            save_db(db)
            send_msg(vk, peer_id, "💬 Тихий режим ВЫКЛЮЧЕН.")
        elif cmd == "antilink":
            chat["antilink"] = not chat.get("antilink", False)
            save_db(db)
            send_msg(vk, peer_id, f"🔗 Антиссылка: {'ВКЛ ✅' if chat['antilink'] else 'ВЫКЛ ❌'}")
