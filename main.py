import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    raise RuntimeError("❌ TOKEN không tồn tại. Kiểm tra Variables trên Railway.")

bot.run(TOKEN)


