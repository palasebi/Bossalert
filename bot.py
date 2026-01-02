import discord
import asyncio
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os

# variabile din environment (NU le pune direct în cod)
TOKEN = os.environ["TOKEN"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])
ROLE_ID = int(os.environ["ROLE_ID"])

TZ = ZoneInfo("Europe/Bucharest")
SAVE_FILE = "bosses.json"
MESSAGE_ID_FILE = "boss_message_id.txt"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

DEFAULT_BOSSES = [
    {"name": "👑 Regina de Aur", "respawn": 2, "last": "10:10"},
    {"name": "😈 Bossi Malefici", "respawn": 2, "last": "10:10"},
    {"name": "🔥 Alastor", "respawn": 4, "last": "08:10"},
    {"name": "⚔️ World Boss PVP", "respawn": 6, "last": "06:02"},
]

# --- Funcții pentru bossi ---
def now_ro():
    return datetime.now(TZ)

def fmt(delta):
    s = int(delta.total_seconds())
    return f"{s//3600}h {(s%3600)//60}m"

def save_bosses(bosses):
    with open(SAVE_FILE, "w") as f:
        json.dump([
            {
                "name": b["name"],
                "respawn": b["respawn"],
                "last_spawn": b["last_spawn"].isoformat()
            } for b in bosses
        ], f, indent=4)

def load_bosses():
    if not os.path.exists(SAVE_FILE):
        bosses = []
        for b in DEFAULT_BOSSES:
            h, m = map(int, b["last"].split(":"))
            bosses.append({
                "name": b["name"],
                "respawn": b["respawn"],
                "last_spawn": datetime.now(TZ).replace(hour=h, minute=m, second=0, microsecond=0)
            })
        save_bosses(bosses)
        return bosses

    with open(SAVE_FILE, "r") as f:
        data = json.load(f)
    bosses = []
    for b in data:
        bosses.append({
            "name": b["name"],
            "respawn": b["respawn"],
            "last_spawn": datetime.fromisoformat(b["last_spawn"])
        })
    return bosses

def next_spawn(boss):
    spawn = boss["last_spawn"]
    while spawn + timedelta(hours=boss["respawn"]) <= now_ro():
        spawn += timedelta(hours=boss["respawn"])
        boss["last_spawn"] = spawn
        save_bosses(bosses)
    return spawn + timedelta(hours=boss["respawn"])

# --- On ready ---
@client.event
async def on_ready():
    print(f"✅ Bot conectat ca {client.user}")
    client.loop.create_task(update_boss_message())
    client.loop.create_task(checker())

# --- Mesaj fix live ---
async def update_boss_message():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    # Încearcă să încarce mesajul existent
    msg = None
    try:
        with open(MESSAGE_ID_FILE, "r") as f:
            msg_id = int(f.read())
            msg = await channel.fetch_message(msg_id)
    except Exception:
        pass

    # Dacă nu există, creează unul nou
    if not msg:
        msg = await channel.send("⏳ Timere Bossi în curs de încărcare...")
        with open(MESSAGE_ID_FILE, "w") as f:
            f.write(str(msg.id))

    while True:
        now = now_ro()
        text = "⏳ **Boss Timers (RO)** ⏳\n\n"
        for b in bosses:
            ns = next_spawn(b)
            text += f"{b['name']} → {ns.strftime('%H:%M')} (în {fmt(ns-now)})\n"
        await msg.edit(content=text)
        await asyncio.sleep(30)  # update la fiecare 30 secunde

# --- Comanda !bossi ---
@client.event
async def on_message(msg):
    if msg.author.bot:
        return

    if msg.content.lower() == "!bossi":
        now = now_ro()
        text = "⏳ **Boss Timers (RO)** ⏳\n\n"
        for b in bosses:
            ns = next_spawn(b)
            text += f"{b['name']} → {ns.strftime('%H:%M')} (în {fmt(ns-now)})\n"
        await msg.channel.send(text)

# --- Notificări cu 10 minute înainte ---
async def checker():
    await client.wait_until_ready()
    ch = client.get_channel(CHANNEL_ID)
    role = f"<@&{ROLE_ID}>"
    notified = set()

    while True:
        now = now_ro()
        for b in bosses:
            ns = next_spawn(b)
            if ns - timedelta(minutes=10) <= now < ns and b["name"] not in notified:
                await ch.send(
                    f"⏰ {role} **{b['name']} apare la {ns.strftime('%H:%M')} (în 10 minute!)**"
                )
                notified.add(b["name"])
            if now >= ns:
                notified.discard(b["name"])
        await asyncio.sleep(30)

# --- Inițializare ---
bosses = load_bosses()
client.run(TOKEN)

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot online"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

