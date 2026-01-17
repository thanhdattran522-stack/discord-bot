import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ Không tìm thấy TOKEN")
    exit(1)

@bot.event
async def on_ready():
    print(f"✅ Bot đã online: {bot.user}")

bot.run(TOKEN)

