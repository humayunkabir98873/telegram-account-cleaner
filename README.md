# Telegram Account Cleaner

**Bulk delete Telegram chats, leave all channels and groups, remove bot chats and delete profile photos in one go.**
A free, open-source Python script (Telethon userbot) for cleaning up your Telegram account,
with a checklist so you pick exactly what goes and what stays.

Tired of opening hundreds of chats one by one to tap *Delete* or *Leave*? This script lists every chat on
your account, lets you check or uncheck each one, and then cleans up everything you picked automatically.

![Python](https://img.shields.io/badge/python-3.9%2B-blue) ![Telethon](https://img.shields.io/badge/Telethon-1.36%2B-2CA5E0) ![License: MIT](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **Delete all bot chats** at once, and optionally **block every bot**
- **Leave all Telegram channels** you joined
- **Leave all Telegram groups** and supergroups you joined
- **Delete private chats** with people, from your side only or **for both sides**
- **Delete channels and groups you own** (off by default, needs an extra `DELETE` confirmation)
- **Delete all your profile photos**
- **Checklist:** every chat starts checked; uncheck the ones you want to keep, by number, by range or by whole type
- **Archived chats included**, so nothing hides in folders
- **Safe by design:** shows a summary and changes nothing until you type `yes`
- **Never touches** Saved Messages or the official Telegram chat that sends your login codes
- **Handles rate limits:** if Telegram says "slow down" (FloodWait), it waits and continues by itself
- **Logs itself out at the end** if you want, removing the login session from your computer
- Works on **Windows, macOS and Linux**

## Why a script and not a Telegram bot?

A normal bot made with @BotFather **cannot see or touch your personal chats**. Telegram doesn't allow it.
This script logs in **as you**, through Telegram's official MTProto API (the same API the Telegram desktop
apps use), using the [Telethon](https://github.com/LonamiWebs/Telethon) library. That's the only way to
bulk-clean a Telegram account.

---

## Requirements

- Python 3.9 or newer ([download](https://www.python.org/downloads/))
- A Telegram account
- Your own Telegram **api_id** and **api_hash** (free, takes a minute: see below)

## Installation

### 1. Download the code

```bash
git clone https://github.com/humayunkabir98873/telegram-account-cleaner.git
cd telegram-account-cleaner
```

Or click **Code > Download ZIP** on this page and unzip it.

### 2. Install the library

```bash
pip install -r requirements.txt
```

### 3. Get your api_id and api_hash

1. Go to <https://my.telegram.org/apps> and log in with your phone number.
2. If you don't have an app yet, create one. The name and short name can be anything.
3. Copy the **App api_id** and **App api_hash**.

> **Already have an app?** Telegram allows only **one app per account**, so you can't create another one.
> Just use the api_id and api_hash of the app you already have. Its name doesn't matter.

### 4. Add your credentials

Copy `.env.example` to a new file named `.env` and fill it in:

```env
API_ID=1234567
API_HASH=0123456789abcdef0123456789abcdef
```

---

## Usage

```bash
python tg_cleanup.py
```

### First login

The first time, it asks for:

1. **Your phone number with the country code**, for example `+8801XXXXXXXXX` or `+14155550123`.
   Don't use the local format (like `01XXXXXXXXX`): Telegram rejects it with *"The phone number is invalid"*.
2. **The login code** Telegram sends to your Telegram app.
3. **Your 2FA password**, if you have two-step verification on.

### Pick what to clean

The script scans all your chats and shows them as a numbered checklist. Everything starts **checked**
(except channels/groups you own), so you just **uncheck what you want to keep**:

```
  --- bots: delete chat (optionally block the bot) ---
     1  [x]  Some Bot (@some_bot)
     2  [x]  Another Bot (@another_bot)

  --- channels: leave ---
     3  [x]  News Channel (@news)

  --- groups: leave ---
     4  [x]  Study Group [id 1234567890]

  --- people: delete chat ---
     5  [x]  A Friend (@a_friend)

  --- owned: DELETE for everyone (you own it) ---
     6  [ ]  My Channel (@my_channel)

Checked 5 of 6  (bots 2/2, channels 1/1, groups 1/1, people 1/1, owned 0/1)
```

| Type this | What it does |
|---|---|
| `3 7 12-20` | check/uncheck those numbers (single numbers and ranges) |
| `a` | check all |
| `n` | uncheck all |
| `+bots` / `-bots` | check/uncheck a whole type: `bots`, `channels`, `groups`, `people`, `owned` |
| `l` | show the list again |
| `d` | done, continue |
| `q` | quit without changing anything |

**Example:** to clean only bots and channels, type `n`, then `+bots`, then `+channels`, then `d`.

### Final questions and confirmation

After `d`, the script asks:

- Delete your profile photos too?
- Block the bots too?
- Delete private chats for the other person too, or only from your side?

Then it shows a summary like this and waits for you to type `yes`:

```
================ SUMMARY: nothing deleted yet ================
  bots         2  -> delete chat (optionally block the bot)
  channels     1  -> leave
  groups       1  -> leave
==============================================================
Type yes to go ahead:
```

If you checked channels/groups **you own**, you must also type `DELETE`, because deleting them removes
them for every member and can't be undone.

---

## What each type does

| Type | Action |
|---|---|
| **bots** | Deletes the chat with the bot. Can also block the bot so it can't message you again. |
| **channels** | Leaves the channel. |
| **groups** | Leaves the group or supergroup. |
| **people** | Deletes the private chat. Choose "for both sides" to also remove it for the other person. |
| **owned** | Permanently deletes the channel/group for all members. Off by default. |
| **photos** | Deletes all your profile pictures. |

## Security and privacy

- Everything runs **on your own computer**. Nothing is sent anywhere except to Telegram itself.
- `.env` (your api_hash) and `tg_cleanup.session` (your login) give **full access to your Telegram account**.
  Never share them or upload them. Both are already in `.gitignore`.
- At the end, the script offers to **log itself out**, which deletes the session file. Say yes unless you'll run it again soon.
- You can also end the session anytime in Telegram: **Settings > Devices**.
- Read the code before running it. It's one short file: [`tg_cleanup.py`](tg_cleanup.py).

## Troubleshooting

| Problem | Fix |
|---|---|
| `PhoneNumberInvalidError` / *The phone number is invalid* | Enter the number in international format with `+` and the country code, e.g. `+8801XXXXXXXXX`. |
| *Put API_ID and API_HASH in .env first* | Create `.env` from `.env.example` and fill in both values. |
| Can't create a new app on my.telegram.org | Each account gets only one app. Use the credentials of the app you already have. |
| *Telegram asked us to slow down, waiting Ns* | Normal on big accounts. The script waits and carries on by itself. |
| `ModuleNotFoundError: No module named 'telethon'` | Run `pip install -r requirements.txt`. |
| Some items show `FAIL` | Telegram refused that one item (for example, a chat that no longer exists). The rest still run. |

## Limitations

- **Deleting your whole Telegram account** is not possible through the API. Do it at <https://my.telegram.org/deactivate>.
- "Delete for both sides" only works where Telegram allows it.
- Leaving a channel doesn't delete messages you posted in it.

## FAQ

**Can I get banned for using this?**
The script uses Telegram's official API at a gentle pace and respects rate limits. It only acts on your own
account. Use it at your own risk, as with any third-party Telegram tool.

**Can I undo it?**
You can rejoin public channels and groups. Deleted chats, deleted owned channels/groups and deleted photos
**cannot** be restored. That's why there's a checklist, a summary and a `yes` confirmation.

**Does it delete Saved Messages?**
No. Saved Messages and the official Telegram service chat are always skipped.

## Disclaimer

This project is not affiliated with Telegram. You are responsible for what you delete from your account.

## License

[MIT](LICENSE)

---

**Keywords:** telegram cleaner, delete all telegram chats, leave all telegram channels, leave all telegram groups,
telegram bulk delete, mass leave telegram groups, delete telegram bot chats, block all bots telegram,
delete telegram profile photos, telegram userbot, telethon script, clean telegram account, telegram mass unsubscribe
