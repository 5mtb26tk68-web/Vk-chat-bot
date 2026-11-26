import re
import time
from vk_api.utils import get_random_id

LINKS_RE = re.compile(r"(https?://|vk\.me/|t\.me/|@all|@everyone)", re.I)
BAD_WORDS = ["блять", "сука", "хуй", "пизд", "ебат", "ебан", "бляд", "нахуй"]

DEFAULT_PERMS = {
    "mute": 20, "unmute": 20, "warn": 30, "unwarn": 30,
    "kick": 50, "ban": 60, "cban": 80, "cunban": 80,
    "silence": 60, "antilink": 70, "antimat": 70,
    "welcome": 70, "rules": 70, "all": 50, "inactive": 60,
    "createrole": 85, "delrole": 85, "giverole": 60, "takerole": 60,
    "setperm": 95
}

def send_msg(vk, peer_id, text):
    vk.messages.send(peer_id=peer_id, message=text, random_id=get_random_id())

def get_chat(db, peer_id):
    pid = str(peer_id)
    if pid not in db["chats"]:
        db["chats"][pid] = {
            "members": {}, "roles": {}, "perms": dict(DEFAULT_PERMS),
            "banned": [], "silence": False, "antilink": False, "antimat": False,
            "rules": "Правила беседы ещё не установлены.",
            "welcome": "Добро пожаловать в беседу! Ознакомься с правилами: /rules"
        }
    c = db["chats"][pid]
    for k, v in [("roles", {}), ("perms", dict(DEFAULT_PERMS)), ("banned", []), ("antimat", False), ("antilink", False), ("silence", False)]:
        if k not in c:
            c[k] = v
    return c

def get_member(chat, user_id):
    uid = str(user_id)
    if uid not in chat["members"]:
        chat["members"][uid] = {"warns": 0, "mute_until": 0, "msgs": 0, "xp": 0, "nick": None, "role": None}
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

def get_priority(vk, chat, peer_id, user_id):
    if is_vk_admin(vk, peer_id, user_id):
        return 100
    m = get_member(chat, user_id)
    r_name = m.get("role")
    if r_name and r_name in chat["roles"]:
        return chat["roles"][r_name]
    return 0

def get_name(vk, chat, user_id):
    if user_id < 0:
        return "Astra"
    m = get_member(chat, user_id)
    u = vk.users.get(user_ids=user_id).pop(0)
    disp = m["nick"] if m.get("nick") else f"{u['first_name']} {u['last_name']}"
    r_name = m.get("role")
    if r_name and r_name in chat["roles"]:
        return f"「{r_name}」 [id{user_id}|{disp}]"
    return f"[id{user_id}|{disp}]"

def extract_target(msg_obj, args):
    if "reply_message" in msg_obj:
        return msg_obj["reply_message"]["from_id"]
    if args:
        match = re.search(r"\[id(\d+)\|", " ".join(args))
        if match:
            return int(match.group(1))
    return None

def extract_reason(args, skip_nums=False):
    clean = []
    for a in args:
        if a.startswith("[id") or (skip_nums and a.isdigit()):
            continue
        clean.append(a)
    return " ".join(clean).strip() or "Без указания причины"

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
                    send_msg(vk, peer_id, f"⛔ {get_name(vk, chat, nid)} находится в ЧС беседы и был исключён!")
                except Exception:
                    pass
                return True
            send_msg(vk, peer_id, f"👋 Приветствуем, {get_name(vk, chat, nid)}!\n📌 {chat['welcome']}")
        return True

    if from_id < 0:
        return True

    member = get_member(chat, from_id)
    member["msgs"] += 1
    member["xp"] += 15
    prio = get_priority(vk, chat, peer_id, from_id)

    if prio < 10:
        has_bad = chat.get("antimat") and any(w in text.lower() for w in BAD_WORDS)
        has_link = chat.get("antilink") and LINKS_RE.search(text)
        if member["mute_until"] > time.time() or chat.get("silence") or has_link or has_bad:
            try:
                vk.messages.delete(peer_id=peer_id, cmids=msg_obj["conversation_message_id"], delete_for_all=1)
                if has_bad:
                    send_msg(vk, peer_id, f"🤬 {get_name(vk, chat, from_id)}, мат запрещён в этой беседе!")
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
        send_msg(vk, peer_id, f"📜 Astra • Правила беседы:\n━━━━━━━━━━━━━━━━━━\n{chat['rules']}")
        return True
    elif cmd == "stats":
        c_lvl = member["xp"] // 500 + 1
        r_name = member.get("role") or "Участник"
        send_msg(vk, peer_id, f"📊 Astra • Карточка участника\n━━━━━━━━━━━━━━━━━━\n👤 Игрок: {get_name(vk, chat, from_id)}\n🏷 Роль: {r_name} [Приоритет: {prio}/100]\n🔥 Уровень актива: {c_lvl} ({member['xp']} XP)\n💬 Сообщений: {member['msgs']}\n⚠️ Предупреждений: {member['warns']}/3")
        return True
    elif cmd == "roles":
        sorted_r = sorted(chat["roles"].items(), key=lambda item: list(item).pop(), reverse=True)
        lines = ["🏷 Astra • Иерархия ролей (1–100):", "━━━━━━━━━━━━━━━━━━"]
        for r_name, r_p in sorted_r:
            holders = [get_name(vk, chat, int(u)) for u, m in chat["members"].items() if m.get("role") == r_name]
            h_str = ", ".join(holders) if holders else "пусто"
            lines.append(f"▸ [{r_p}] {r_name} — {h_str}")
        send_msg(vk, peer_id, "\n".join(lines) if len(lines) > 2 else "🏷 Роли ещё не созданы.\nСоздать: /createrole [1-99] [Название]")
        return True
    elif cmd == "perms":
        lines = ["🔐 Astra • Права доступа:", "━━━━━━━━━━━━━━━━━━"]
        for c_name, req_p in sorted(chat["perms"].items(), key=lambda x: list(x).pop(), reverse=True):
            lines.append(f"▸ /{c_name} — от {req_p} приоритета")
        send_msg(vk, peer_id, "\n".join(lines))
        return True
    elif cmd == "topchat":
        top_m = sorted(chat["members"].items(), key=lambda x: list(x).pop()["msgs"], reverse=True)[:10]
        lines = ["💬 Astra • Топ-10 активных:", "━━━━━━━━━━━━━━━━━━"] + [f"{i}. {get_name(vk, chat, int(uid))} — {m['msgs']} сообщ." for i, (uid, m) in enumerate(top_m, 1)]
        send_msg(vk, peer_id, "\n".join(lines))
        return True
    elif cmd == "chatinfo":
        s_on = "ВКЛ ✅" if chat["silence"] else "ВЫКЛ ❌"
        l_on = "ВКЛ ✅" if chat["antilink"] else "ВЫКЛ ❌"
        m_on = "ВКЛ ✅" if chat["antimat"] else "ВЫКЛ ❌"
        send_msg(vk, peer_id, f"⚙ Astra • Паспорт беседы\n━━━━━━━━━━━━━━━━━━\n🤫 Тихий режим: {s_on}\n🔗 Антиссылка: {l_on}\n🤬 Антимат: {m_on}\n🏷 Создано ролей: {len(chat['roles'])}\n⛔ В ЧС беседы: {len(chat['banned'])} чел.")
        return True
    elif cmd == "nick":
        member["nick"] = " ".join(args)[:25] if args else None
        save_db(db)
        send_msg(vk, peer_id, f"✅ Твой новый ник: {get_name(vk, chat, from_id)}")
        return True

    if cmd not in chat["perms"]:
        return False

    req_prio = chat["perms"][cmd]
    if prio < req_prio:
        send_msg(vk, peer_id, f"⛔ Недостаточно прав! Для /{cmd} нужен приоритет {req_prio}+ (у тебя {prio}).")
        return True

    if cmd == "setperm":
        if len(args) < 2:
            send_msg(vk, peer_id, "❌ Пример: /setperm kick 40 (команда и приоритет 1–100)")
            return True
        target_cmd = args.pop(0).lower().lstrip("/")
        new_p_s = args.pop(0)
        if target_cmd not in chat["perms"] or not new_p_s.isdigit() or not (1 <= int(new_p_s) <= 100):
            send_msg(vk, peer_id, "❌ Неверная команда или число (1–100). Список: /perms")
            return True
        chat["perms"][target_cmd] = int(new_p_s)
        save_db(db)
        send_msg(vk, peer_id, f"🔐 Доступ к /{target_cmd} изменён на {new_p_s}+ приоритет!")
        return True

    if cmd == "createrole":
        if len(args) < 2:
            send_msg(vk, peer_id, "❌ Пример: /createrole 80 Старший Админ (приоритет 1–99)")
            return True
        p_str = args.pop(0)
        if not p_str.isdigit():
            send_msg(vk, peer_id, "❌ Сначала укажи число приоритета (1–99), затем название роли.")
            return True
        r_prio = int(p_str)
        r_name = " ".join(args)[:25].strip()
        if not (1 <= r_prio <= 99) or r_prio >= prio or not r_name:
            send_msg(vk, peer_id, f"❌ Приоритет роли должен быть от 1 до {prio - 1}!")
            return True
        chat["roles"][r_name] = r_prio
        save_db(db)
        send_msg(vk, peer_id, f"✅ Роль «{r_name}» с приоритетом [{r_prio}/100] создана!")
        return True

    elif cmd == "delrole":
        r_name = " ".join(args).strip()
        if r_name not in chat["roles"]:
            send_msg(vk, peer_id, "❌ Роль не найдена. Список ролей: /roles")
            return True
        if chat["roles"][r_name] >= prio:
            send_msg(vk, peer_id, "⛔ Нельзя удалить роль выше или равную твоему приоритету.")
            return True
        del chat["roles"][r_name]
        for m in chat["members"].values():
            if m.get("role") == r_name:
                m["role"] = None
        save_db(db)
        send_msg(vk, peer_id, f"🗑 Роль «{r_name}» удалена.")
        return True

