"""
Telegram account cleaner.

Cleans up your own Telegram account in bulk: deletes chats with bots, leaves
channels and groups, deletes private chats, deletes channels/groups you own
and removes your profile photos.

It logs in as YOU (a "userbot" via Telegram's MTProto API). A normal
@BotFather bot cannot do this: bots cannot see or touch your chats.

Every chat starts checked (except channels/groups you own); you uncheck what
you want to keep. Nothing is deleted until you have seen the list and typed "yes".
"""
import asyncio
import os
import re
import sys
from pathlib import Path

from telethon import TelegramClient, functions, utils
from telethon.errors import FloodWaitError, PhoneNumberInvalidError, RPCError
from telethon.tl.types import Channel, ChannelForbidden, Chat, ChatForbidden, User

HERE = Path(__file__).resolve().parent
SESSION = str(HERE / "tg_cleanup")
TELEGRAM_SERVICE_ID = 777000  # the chat that sends your login codes; never touched

# Display order in the checklist, and what happens to each type.
KINDS = {
    "bots": "delete chat (optionally block the bot)",
    "channels": "leave",
    "groups": "leave",
    "people": "delete chat",
    "owned": "DELETE for everyone (you own it)",
}

HELP = (
    "Type numbers to check/uncheck (e.g. 3 7 12-20)  |  a = check all  |  n = uncheck all\n"
    "+bots / -bots = check/uncheck a whole type (also channels, groups, people, owned)\n"
    "l = show list again  |  d = done, continue  |  q = quit without changes"
)


def load_credentials():
    env = HERE / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
    try:
        api_id, api_hash = int(os.environ["API_ID"]), os.environ["API_HASH"]
    except (KeyError, ValueError):
        api_id, api_hash = None, ""
    if not api_id or not api_hash:
        sys.exit("Put API_ID and API_HASH in .env first (get them at https://my.telegram.org/apps).")
    return api_id, api_hash


def classify(entity):
    if isinstance(entity, User):
        if entity.is_self or entity.id == TELEGRAM_SERVICE_ID:
            return None
        return "bots" if entity.bot else "people"
    if isinstance(entity, Channel):
        if entity.creator:
            return "owned"
        return "channels" if entity.broadcast else "groups"
    if isinstance(entity, ChannelForbidden):
        return "channels" if entity.broadcast else "groups"
    if isinstance(entity, Chat):
        return "owned" if entity.creator else "groups"
    if isinstance(entity, ChatForbidden):
        return "groups"
    return None


def label(entity):
    name = utils.get_display_name(entity) or "(no name)"
    username = getattr(entity, "username", None)
    return f"{name} (@{username})" if username else f"{name} [id {entity.id}]"


def ask(prompt):
    return input(prompt).strip()


def ask_yes_no(prompt):
    return ask(f"{prompt} (y/N): ").lower() in ("y", "yes")


def print_checklist(items, checked):
    print()
    current = None
    for i, ((kind, entity), on) in enumerate(zip(items, checked), 1):
        if kind != current:
            current = kind
            print(f"\n  --- {kind}: {KINDS[kind]} ---")
        print(f"  {i:>4}  [{'x' if on else ' '}]  {label(entity)}")


def checklist(items):
    """Let the user check/uncheck chats. Returns the checked items, or None to quit."""
    checked = [kind != "owned" for kind, _ in items]
    print_checklist(items, checked)
    while True:
        counts = ", ".join(
            f"{kind} {sum(on for (k, _), on in zip(items, checked) if k == kind)}"
            f"/{sum(k == kind for k, _ in items)}"
            for kind in KINDS if any(k == kind for k, _ in items)
        )
        print(f"\nChecked {sum(checked)} of {len(items)}  ({counts})\n{HELP}")
        command = ask("> ").lower()
        if not command:
            continue
        if command in ("d", "done"):
            return [item for item, on in zip(items, checked) if on]
        if command in ("q", "quit"):
            return None
        if command in ("l", "list"):
            print_checklist(items, checked)
            continue
        if command in ("a", "all"):
            checked = [True] * len(items)
        elif command in ("n", "none"):
            checked = [False] * len(items)
        elif command[:1] in "+-" and command[1:] in KINDS:
            for i, (kind, _) in enumerate(items):
                if kind == command[1:]:
                    checked[i] = command[0] == "+"
        else:
            bad = []
            for token in re.split(r"[\s,]+", command):
                match = re.fullmatch(r"(\d+)(?:-(\d+))?", token)
                start, end = (int(match[1]), int(match[2] or match[1])) if match else (0, 0)
                if not match or not 1 <= min(start, end) <= max(start, end) <= len(items):
                    bad.append(token)
                    continue
                for n in range(min(start, end), max(start, end) + 1):
                    checked[n - 1] = not checked[n - 1]
            if bad:
                print(f"Didn't understand: {' '.join(bad)} (numbers go from 1 to {len(items)})")
                continue
        print_checklist(items, checked)


async def with_retry(make_call):
    while True:
        try:
            return await make_call()
        except FloodWaitError as e:
            print(f"    Telegram asked us to slow down, waiting {e.seconds}s...")
            await asyncio.sleep(e.seconds + 1)


async def delete_owned(client, entity):
    if isinstance(entity, Channel):
        await client(functions.channels.DeleteChannelRequest(entity))
    else:
        await client(functions.messages.DeleteChatRequest(chat_id=entity.id))


async def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    api_id, api_hash = load_credentials()
    client = TelegramClient(SESSION, api_id, api_hash)
    try:
        # asks for phone, login code and 2FA password in this terminal
        await client.start(phone=lambda: ask("Phone number WITH country code (e.g. +8801XXXXXXXXX): "))
    except PhoneNumberInvalidError:
        await client.disconnect()
        sys.exit("Telegram rejected that number. Use the international format with +, e.g. +8801XXXXXXXXX.")

    me = await client.get_me()
    print(f"\nLogged in as {label(me)}\nScanning your chats (archived ones included)...")

    found = {kind: [] for kind in KINDS}
    async for dialog in client.iter_dialogs():
        kind = classify(dialog.entity)
        if kind:
            found[kind].append(dialog.entity)
    items = [(kind, entity) for kind in KINDS for entity in found[kind]]
    photos = await client.get_profile_photos("me", limit=None)

    print("\nEverything starts checked, except channels/groups you own. Uncheck what you want to keep.")
    picked = checklist(items) if items else []
    if picked is None:
        print("Cancelled, nothing changed.")
        return await client.disconnect()

    picked_kinds = {kind for kind, _ in picked}
    delete_photos = bool(photos) and ask_yes_no(f"Also delete your {len(photos)} profile photo(s)?")
    block_bots = "bots" in picked_kinds and ask_yes_no("Also block the bots?")
    revoke_people = "people" in picked_kinds and ask_yes_no(
        "Delete private chats for the other person too? (No = only from your side)"
    )

    if not picked and not delete_photos:
        print("Nothing picked. Bye.")
        return await client.disconnect()

    plan = {kind: [e for k, e in picked if k == kind] for kind in KINDS if kind in picked_kinds}

    print("\n================ SUMMARY: nothing deleted yet ================")
    for kind, entities in plan.items():
        print(f"  {kind:<9} {len(entities):>4}  -> {KINDS[kind]}")
    if delete_photos:
        print(f"  {'photos':<9} {len(photos):>4}  -> delete")
    print("==============================================================")

    if ask("Type yes to go ahead: ").lower() != "yes":
        print("Cancelled, nothing changed.")
        return await client.disconnect()
    if plan.get("owned") and ask(
        f"You checked {len(plan['owned'])} channel(s)/group(s) YOU OWN. They will be gone for every member, "
        "and that cannot be undone. Type DELETE to confirm: "
    ) != "DELETE":
        print("Skipping owned channels/groups.")
        plan.pop("owned")

    done = failed = 0
    for kind, entities in plan.items():
        print(f"\nCleaning {kind}...")
        for entity in entities:
            try:
                if kind == "owned":
                    await with_retry(lambda: delete_owned(client, entity))
                elif kind == "bots":
                    if block_bots:
                        await with_retry(lambda: client(functions.contacts.BlockRequest(id=entity)))
                    await with_retry(lambda: client.delete_dialog(entity))
                elif kind == "people":
                    await with_retry(lambda: client.delete_dialog(entity, revoke=revoke_people))
                else:
                    await with_retry(lambda: client.delete_dialog(entity))
                print(f"  ok   {label(entity)}")
                done += 1
            except RPCError as e:
                print(f"  FAIL {label(entity)}: {e.__class__.__name__}")
                failed += 1
            await asyncio.sleep(0.4)  # stay well under Telegram's rate limits

    if delete_photos:
        print("\nDeleting profile photos...")
        try:
            await with_retry(lambda: client(functions.photos.DeletePhotosRequest(
                id=[utils.get_input_photo(p) for p in photos]
            )))
            print(f"  ok   {len(photos)} photo(s)")
            done += len(photos)
        except RPCError as e:
            print(f"  FAIL photos: {e.__class__.__name__}")
            failed += 1

    print(f"\nDone. {done} cleaned, {failed} failed.")
    if ask_yes_no("Log this script out of your account now? (recommended if you won't run it again soon)"):
        await client.log_out()
        print("Logged out; the session file was removed.")
    else:
        await client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
