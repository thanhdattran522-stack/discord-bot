import os
import discord
from discord.ext import commands

TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    print("❌ Không tìm thấy TOKEN")
else:
    print("✅ Đã load TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

bot.run(TOKEN)
