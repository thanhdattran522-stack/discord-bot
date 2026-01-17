import discord
from discord.ext import commands
import requests
import os
from datetime import datetime, timezone
from dateutil import parser
from keep_alive import keep_alive

keep_alive()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DANH_SACH_DEN = [35041999, 1059424707, 994446201, 35706033,36055514, 34771501, 34766049, 16098118,
    33295727, 34825823]

@bot.event
async def on_ready():
    print("Bot đã online!")

@bot.command()
async def check(ctx, username: str):
    try:
        payload = {"usernames": [username], "excludeBannedUsers": True}
        res = requests.post(
            "https://users.roblox.com/v1/usernames/users",
            json=payload
        ).json()

        if not res["data"]:
            await ctx.send("❌ Không tìm thấy user")
            return

        user_id = res["data"][0]["id"]

        info = requests.get(
            f"https://users.roblox.com/v1/users/{user_id}"
        ).json()

        friends = requests.get(
            f"https://friends.roblox.com/v1/users/{user_id}/friends/count"
        ).json()["count"]

        groups = requests.get(
            f"https://groups.roblox.com/v2/users/{user_id}/groups/roles"
        ).json()["data"]

        created = parser.isoparse(info["created"]).replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - created).days

        blacklist = [
            f"🚨 {g['group']['name']} ({g['group']['id']})"
            for g in groups
            if g["group"]["id"] in DANH_SACH_DEN
        ]

        embed = discord.Embed(
            title="🎖️ HỒ SƠ QUÂN NHÂN",
            color=0x2b2d31
        )

        embed.add_field(name="👤 Username", value=username)
        embed.add_field(name="🆔 Roblox ID", value=user_id)
        embed.add_field(name="👥 Bạn bè", value=friends)
        embed.add_field(name="⏳ Tuổi tài khoản", value=f"{age} ngày")

        if blacklist:
            embed.add_field(
                name="🛑 GROUP BLACKLIST!",
                value="\n".join(blacklist),
                inline=False
            )
            embed.color = 0xff0000
        else:
            embed.add_field(
                name="🛡️ Trạng thái",
                value="✅ Không blacklist",
                inline=False
            )

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"⚠️ Lỗi: {e}")

bot.run(os.environ["DISCORD_TOKEN"])
