import discord
from discord.ext import commands
import requests
import os
from datetime import datetime, timezone
from dateutil import parser

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DANH_SACH_DEN = [
    35041999, 1059424707, 994446201, 35706033, 36055514,
    34771501, 34766049, 16098118, 33295727, 34825823
]

@bot.event
async def on_ready():
    print("✅ Bot đã online!")

@bot.command()
async def check(ctx, username: str):
    try:
        payload = {"usernames": [username], "excludeBannedUsers": True}
        res = requests.post(
            "https://users.roblox.com/v1/usernames/users",
            json=payload
        ).json()

        if not res.get("data"):
            await ctx.send(f"❌ Không tìm thấy quân nhân: **{username}**")
            return

        user_id = res["data"][0]["id"]

        info = requests.get(
            f"https://users.roblox.com/v1/users/{user_id}"
        ).json()

        friends = requests.get(
            f"https://friends.roblox.com/v1/users/{user_id}/friends/count"
        ).json().get("count", 0)

        thumb = requests.get(
            f"https://thumbnails.roblox.com/v1/users/avatar-headshot"
            f"?userIds={user_id}&size=420x420&format=Png"
        ).json()

        avatar_url = thumb["data"][0]["imageUrl"]

        safe_chat = "Bật (Hạn chế)" if info.get("isVieweeSafeChat") else "Tắt (Bình thường)"
        created_date = parser.isoparse(info["created"]).replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - created_date).days

        groups = requests.get(
            f"https://groups.roblox.com/v2/users/{user_id}/groups/roles"
        ).json()

        bad_found = [
            f"🛑 **{g['group']['name']}** ({g['group']['id']})"
            for g in groups.get("data", [])
            if g["group"]["id"] in DANH_SACH_DEN
        ]

        embed = discord.Embed(title="🎖️ HỒ SƠ QUÂN NHÂN", color=0x2b2d31)
        embed.set_thumbnail(url=avatar_url)

        embed.add_field(name="📌 Displayname", value=info["displayName"], inline=True)
        embed.add_field(name="👤 Username", value=username, inline=True)
        embed.add_field(name="🆔 Roblox ID", value=user_id, inline=True)
        embed.add_field(name="🛡️ Safe Chat", value=safe_chat, inline=True)
        embed.add_field(name="🗓️ Ngày gia nhập", value=created_date.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="⏳ Tuổi tài khoản", value=f"{age} ngày", inline=True)
        embed.add_field(name="👥 Số bạn bè", value=f"{friends} người", inline=True)

        if age < 100 or friends < 50:
            warns = []
            if age < 100:
                warns.append(f"🔴 Tuổi tài khoản thấp ({age}/100)")
            if friends < 50:
                warns.append(f"🔴 Ít bạn bè ({friends}/50)")
            embed.add_field(name="⚠️ CẢNH BÁO TIÊU CHUẨN", value="\n".join(warns), inline=False)
            embed.color = 0xffa500

        if bad_found:
            embed.add_field(name="🚨 GROUP BLACKLIST!", value="\n".join(bad_found), inline=False)
            embed.color = 0xff0000
        elif not (age < 100 or friends < 50):
            embed.add_field(name="🛡️ Trạng thái", value="✅ Không có group blacklist", inline=False)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"⚠️ Lỗi trinh sát: {e}")
if not TOKEN:
    raise RuntimeError("❌ TOKEN không tồn tại. Kiểm tra Railway Variables!")

bot.run(TOKEN)





