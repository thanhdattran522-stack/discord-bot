import discord
from discord.ext import commands
import requests
import os
from datetime import datetime, timezone
from dateutil import parser

# CẤU HÌNH HỆ THỐNG
TOKEN = os.getenv("TOKEN")
# Ngài không cần điền ID nữa, Bot sẽ tự tìm theo tên kênh
TEN_KENH_BLACKLIST = "unit-blacklist" 

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)

DANH_SACH_DEN_GROUP = [35041999, 1059424707, 994446201, 35706033, 36055514, 34771501, 33945834, 34825823, 35001403, 33896530, 34766049, 35770147, 11641165, 32783999, 35588235, 33156070, 34766049, 16098118, 33295727, 34825823, 35017460, 35706033, 34334809, 35588235, 35770147, 35017460, 35524185, 34838981, 34285411, 33295727, 661736202, 35006177, 34857314]

class GroupView(discord.ui.View):
    def __init__(self, group_text):
        super().__init__(timeout=60)
        self.group_text = group_text

    @discord.ui.button(label="Xem danh sách nhóm", style=discord.ButtonStyle.grey, emoji="📋")
    async def check_groups(self, interaction: discord.Interaction, button: discord.ui.Button):
        content = self.group_text[:1990] if len(self.group_text) > 2000 else self.group_text
        await interaction.response.send_message(content=content, ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ Bot KSQS đã online")

@bot.command()
async def kiemtra(ctx, username: str):
    try:
        # --- BƯỚC 1: DÒ TÌM KÊNH THEO TÊN TRÊN TOÀN HỆ THỐNG ---
        blacklist_channel = discord.utils.get(bot.get_all_channels(), name=TEN_KENH_BLACKLIST)
        
        names_in_channel = []
        if blacklist_channel:
            # Bot tự động quét 500 bản ghi gần nhất trong kênh tìm được
            async for message in blacklist_channel.history(limit=1000): 
                names_in_channel.append(message.content.strip().lower())

        # --- BƯỚC 2: TRUY XUẤT THÔNG TIN ROBLOX ---
        payload = {"usernames": [username], "excludeBannedUsers": True}
        res = requests.post("https://users.roblox.com/v1/usernames/users", json=payload).json()

        if not res.get("data"):
            return await ctx.send(f"❌ Không tìm thấy quân nhân: **{username}**")

        user_id = res["data"][0]["id"]
        actual_username = res["data"][0]["name"]
        info = requests.get(f"https://users.roblox.com/v1/users/{user_id}").json()
        friends = requests.get(f"https://friends.roblox.com/v1/users/{user_id}/friends/count").json().get("count", 0)
        thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png").json()
        avatar_url = thumb["data"][0]["imageUrl"]
        created_date = parser.isoparse(info["created"]).replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - created_date).days

        # --- BƯỚC 3: KIỂM TRA NHÓM ---
        groups_data = requests.get(f"https://groups.roblox.com/v2/users/{user_id}/groups/roles").json()
        all_groups = groups_data.get("data", [])
        total_groups = len(all_groups)
        
        group_display_list = []
        bad_groups = []
        for g in all_groups:
            if g['group']['id'] in DANH_SACH_DEN_GROUP:
                bad_groups.append(f"🛑 **{g['group']['name']}**")
                group_display_list.append(f"🛑 **{g['group']['name']}**")
            else:
                group_display_list.append(f"▫️ {g['group']['name']}")

        # --- BƯỚC 4: ĐỐI CHIẾU BLACKLIST TỰ ĐỘNG ---
        is_blacklisted = actual_username.lower() in names_in_channel

        # --- BƯỚC 5: TẠO HỒ SƠ ---
        embed = discord.Embed(title="🎖️ HỒ SƠ QUÂN NHÂN", color=0x2b2d31)
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="👤 Username", value=actual_username, inline=True)
        embed.add_field(name="🆔 Roblox ID", value=user_id, inline=True)
        embed.add_field(name="🏰 Tổng số group", value=f"{total_groups} nhóm", inline=True)

        # Cảnh báo quân số và tuổi tài khoản
        warns = []
        if age < 100: warns.append(f"🔴 Tuổi tài khoản thấp ({age}/100)")
        if friends < 50: warns.append(f"🔴 Ít bạn bè ({friends}/50)")
        if total_groups < 5: warns.append(f"🔴 Ít group ({total_groups}/5)")
        
        if warns:
            embed.add_field(name="⚠️ CẢNH BÁO TIÊU CHUẨN", value="\n".join(warns), inline=False)
            embed.color = 0xffa500

        # Báo động Blacklist (Tên hoặc Nhóm)
        alerts = []
        if is_blacklisted: 
            alerts.append(f"💀 **ĐỐI TƯỢNG CÓ TRONG UNIT_BLACKLIST!**")
        if bad_groups: 
            alerts.append(f"🚨 **PHÁT HIỆN GROUP BLACKLIST!**\n" + "\n".join(bad_groups))

        if alerts:
            embed.add_field(name="🚨 CẢNH BÁO BLACKLIST!", value="\n".join(alerts), inline=False)
            embed.color = 0xff0000
        elif not warns:
            embed.add_field(name="🛡️ Trạng thái", value="✅ Không có group blacklist", inline=False)

        group_text = f"📋 **DANH SÁCH CHI TIẾT ({total_groups} NHÓM):**\n\n" + "\n".join(group_display_list)
        view = GroupView(group_text)

        await ctx.send(embed=embed, view=view)
    except Exception as e:
        await ctx.send(f"⚠️ Lỗi: {e}")

bot.run(TOKEN)
