import discord
from discord.ext import commands
import requests
import os
from datetime import datetime, timezone
from dateutil import parser

# CẤU HÌNH HỆ THỐNG
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("❌ TOKEN không tồn tại – kiểm tra Railway Variables")

intents = discord.Intents.default()
intents.message_content = True
# ĐỔI TIỀN TỐ SANG ?
bot = commands.Bot(command_prefix="?", intents=intents)

DANH_SACH_DEN = [35041999, 1059424707, 994446201, 35706033, 36055514, 34771501, 33945834, 34825823, 35001403, 33896530, 34766049, 35770147, 11641165, 32783999, 35588235, 33156070, 34766049, 16098118, 33295727, 34825823, 35017460, 35706033, 34334809, 35588235, 35770147, 35017460, 35524185, 34838981, 34285411, 33295727, 661736202, 35006177, 34857314]

# LỚP XỬ LÝ NÚT BẤM (BUTTON)
class GroupView(discord.ui.View):
    def __init__(self, group_text):
        super().__init__(timeout=60)
        self.group_text = group_text

    @discord.ui.button(label="Xem danh sách nhóm", style=discord.ButtonStyle.grey, emoji="📋")
    async def check_groups(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.group_text) > 2000:
            content = self.group_text[:1990] + "..."
        else:
            content = self.group_text
        await interaction.response.send_message(content=content, ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ KSQS bot đã online")

# ĐỔI TÊN LỆNH SANG kiemtra
@bot.command()
async def kiemtra(ctx, username: str):
    try:
        # 1. TRUY XUẤT THÔNG TIN CƠ BẢN
        payload = {"usernames": [username], "excludeBannedUsers": True}
        res = requests.post("https://users.roblox.com/v1/usernames/users", json=payload).json()

        if not res.get("data"):
            await ctx.send(f"❌ Không tìm thấy quân nhân: **{username}**")
            return

        user_id = res["data"][0]["id"]
        info = requests.get(f"https://users.roblox.com/v1/users/{user_id}").json()
        friends = requests.get(f"https://friends.roblox.com/v1/users/{user_id}/friends/count").json().get("count", 0)
        thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png").json()
        avatar_url = thumb["data"][0]["imageUrl"]

        safe_chat = "Bật (Hạn chế)" if info.get("isVieweeSafeChat") else "Tắt (Bình thường)"
        created_date = parser.isoparse(info["created"]).replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - created_date).days

        # 2. TRUY XUẤT DỮ LIỆU NHÓM
        groups_data = requests.get(f"https://groups.roblox.com/v2/users/{user_id}/groups/roles").json()
        all_groups = groups_data.get("data", [])
        total_groups = len(all_groups)
        
        group_display_list = []
        bad_found = []

        for g in all_groups:
            g_name = g['group']['name']
            g_id = g['group']['id']
            role = g['role']['name']
            
            if g_id in DANH_SACH_DEN:
                entry = f"🛑 **{g_name}** (ID: {g_id}) - *{role}*"
                bad_found.append(entry)
                group_display_list.append(entry)
            else:
                group_display_list.append(f"▫️ {g_name} - *{role}*")

        # 3. TẠO EMBED HIỂN THỊ
        embed = discord.Embed(title="🎖️ HỒ SƠ QUÂN NHÂN", color=0x2b2d31)
        embed.set_thumbnail(url=avatar_url)
        
        embed.add_field(name="📌 Displayname", value=info["displayName"], inline=True)
        embed.add_field(name="👤 Username", value=username, inline=True)
        embed.add_field(name="🆔 Roblox ID", value=user_id, inline=True)
        
        embed.add_field(name="🛡️ Safe Chat", value=safe_chat, inline=True)
        embed.add_field(name="🗓️ Ngày gia nhập", value=created_date.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="⏳ Tuổi tài khoản", value=f"{age} ngày", inline=True)
        
        embed.add_field(name="👥 Số bạn bè", value=f"{friends} người", inline=True)
        embed.add_field(name="🏰 Tổng số group", value=f"{total_groups} group", inline=True)

        # CẢNH BÁO TIÊU CHUẨN
        if age < 100 or friends < 50 or total_groups < 5:
            warns = []
            if age < 100: warns.append(f"🔴 Tuổi tài khoản thấp ({age}/100)")
            if friends < 50: warns.append(f"🔴 Ít bạn bè ({friends}/50)")
            if total_groups < 5: warns.append(f"🔴 Ít group ({total_groups}/5)")
            
            embed.add_field(name="⚠️ CẢNH BÁO TIÊU CHUẨN", value="\n".join(warns), inline=False)
            embed.color = 0xffa500

        # BLACKLIST CHECK
        if bad_found:
            embed.add_field(name="🚨 GROUP BLACKLIST PHÁT HIỆN!", value="\n".join(bad_found), inline=False)
            embed.color = 0xff0000
        elif not (age < 100 or friends < 50 or total_groups < 5):
            embed.add_field(name="🛡️ Trạng thái hiện tại", value="✅ Không có group blacklist", inline=False)

        # NÚT BẤM XEM CHI TIẾT
        group_text = f"📋 **DANH SÁCH CHI TIẾT ({total_groups} NHÓM):**\n\n" + ("\n".join(group_display_list) if group_display_list else "Không tham gia nhóm nào.")
        view = GroupView(group_text)

        await ctx.send(embed=embed, view=view)

    except Exception as e:
        await ctx.send(f"⚠️ Lỗi trinh sát: {e}")

bot.run(TOKEN)
