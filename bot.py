import discord
import asyncio
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import os

TOKEN = os.environ["TOKEN"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])
ROLE_ID = int(os.environ["ROLE_ID"])


TZ = ZoneInfo("Europe/Bucharest")
SAVE_FILE = "bosses.json"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

DEFAULT_BOSSES = [
    {"name": "👑 Regina de Aur", "respawn": 2, "last": "10:10"},
    {"name": "😈 Bossi Malefici", "respawn": 2, "last": "10:10"},
    {"name": "🔥 Alastor", "respawn": 4, "last": "08:10"},
    {"name": "⚔️ World Boss PVP", "respawn": 6, "last": "06:12"},
]

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

def save_bosses(bosses):
    with open(SAVE_FILE, "w") as f:
        json.dump([
            {
                "name": b["name"],
                "respawn": b["respawn"],
                "last_spawn": b["last_spawn"].isoformat()
            } for b in bosses
        ], f, indent=4)

def now_ro():
    return datetime.now(TZ)

def next_spawn(boss):
    spawn = boss["last_spawn"]
    while spawn + timedelta(hours=boss["respawn"]) <= now_ro():
        spawn += timedelta(hours=boss["respawn"])
        boss["last_spawn"] = spawn
        save_bosses(bosses)
    return spawn + timedelta(hours=boss["respawn"])

def fmt(delta):
    s = int(delta.total_seconds())
    return f"{s//3600}h {(s%3600)//60}m"

@client.event
async def on_ready():
    print(f"✅ Bot conectat ca {client.user}")
    client.loop.create_task(checker())

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

bosses = load_bosses()
client.run(TOKEN)
