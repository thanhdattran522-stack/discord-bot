import discord
from discord.ext import commands
import requests
import os
import json
from datetime import datetime, timezone
from dateutil import parser

# 1. CẤU HÌNH HỆ THỐNG
TOKEN = os.getenv("TOKEN")
FILE_DB = "blacklist_dynamic.json"

# Kho ID Blacklist gốc của ngài (Giữ nguyên toàn bộ)
DANH_SACH_DEN_GOC = [576559939, 998028484, 47361536, 205543849, 415009980, 34285411, 123469798, 32860218, 32860218, 1059424707, 130818406,  35706033, 35108918, 34973030, 35109046, 34334809, 1088491035, 1048944679, 104448675 ,1102515063, 13508102, 35186142, 35186152, 35186176, 33557471,266138500 , 34766049, 35442362, 35442355, 34766049, 35221517, 35221507, 32861180, 33295727, 494412357, 1007281007, 650288981,34935340, 34838981,  12938776, 34016213, 33896530, 33720723, 33156070, 33421910,  17387865, 34935340, 33425887, 33302258, 33302258, 33302258, 14838294, 35683955 , 994121070, 16046069, 963270266, 603089537, 32824464, 11881320, 17091729, 15027915, 14464551 , 15264532 , 14441186, 14207426095, 33142374,  33981926, 33398345, 33421910, 33422397, 33448593, 33421937, 33422341, 33422355, 33425059 , 33302258 , 33425887,  33421910 , 17387865, 34935340, 33425887, 33302258,16858236, 33398345,35058767, 35058756, 34991987, 34990235,33132192, 34887492, 35500095, 35493282, 35153514,35145871, 35138001, 35122343,  5717089, 6959311, 7508224, 5717238, 33142374, 33398345 , 33981926,33932235,6922664, 35121193,994446201,36055514,34771501,35041999,938311141,16868982,35745867,35745725,35695662,35104173]  
 

DANH_SACH_THEM = []
if os.path.exists(FILE_DB):
    with open(FILE_DB, "r") as f:
        DANH_SACH_THEM = json.load(f)

def save_dynamic_data():
    with open(FILE_DB, "w") as f:
        json.dump(DANH_SACH_THEM, f)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)

class GroupView(discord.ui.View):
    def __init__(self, group_text):
        super().__init__(timeout=60)
        self.group_text = group_text

    @discord.ui.button(label="Xem danh sách nhóm", style=discord.ButtonStyle.grey, emoji="📋")
    async def check_groups(self, interaction: discord.Interaction, button: discord.ui.Button):
        content = self.group_text[:1990] + "..." if len(self.group_text) > 2000 else self.group_text
        await interaction.response.send_message(content=content, ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ Bot KSQS đã online")

# --- LỆNH QUẢN LÝ ---
@bot.command()
@commands.has_permissions(administrator=True)
async def blacklist_add(ctx, group_id: int):
    if group_id not in DANH_SACH_DEN_GOC and group_id not in DANH_SACH_THEM:
        DANH_SACH_THEM.append(group_id)
        save_dynamic_data()
        await ctx.send(f"🚫 **Đã thêm blacklist:**\n• {group_id}")
    else:
        await ctx.send(f"⚠️ ID {group_id} đã nằm trong kho lưu trữ.")

@bot.command()
@commands.has_permissions(administrator=True)
async def blacklist_remove(ctx, group_id: int):
    if group_id in DANH_SACH_THEM:
        DANH_SACH_THEM.remove(group_id)
        save_dynamic_data()
        await ctx.send(f"✅ **Đã xoá blacklist:**\n• {group_id}")
    else:
        await ctx.send(f"❌ Không thể xoá ID gốc hoặc ID không tồn tại.")

# --- LỆNH KIỂM TRA CHÍNH ---
@bot.command()
async def kiemtra(ctx, username: str):
    try:
        # Lấy thông tin từ Roblox API
        payload = {"usernames": [username], "excludeBannedUsers": True}
        res = requests.post("https://users.roblox.com/v1/usernames/users", json=payload).json()

        if not res.get("data"):
            return await ctx.send(f"❌ Không tìm thấy quân nhân: **{username}**")

        u_data = res["data"][0]
        user_id = u_data["id"]
        actual_name = u_data["name"]
        display_name = u_data["displayName"]

        info = requests.get(f"https://users.roblox.com/v1/users/{user_id}").json()
        friends = requests.get(f"https://friends.roblox.com/v1/users/{user_id}/friends/count").json().get("count", 0)
        thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png").json()
        avatar_url = thumb["data"][0]["imageUrl"]
        
        safe_chat = "🔴 Bật (Loại)" if info.get("isVieweeSafeChat") else "🟢 Tắt (Bình thường)"
        created_date = parser.isoparse(info["created"]).replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - created_date).days

        # Đối soát Blacklist Group
        tong_den = list(set(DANH_SACH_DEN_GOC + DANH_SACH_THEM))
        g_data = requests.get(f"https://groups.roblox.com/v2/users/{user_id}/groups/roles").json()
        all_groups = g_data.get("data", [])
        
        bad_found = []
        full_list = []
        for g in all_groups:
            gid = g['group']['id']
            if gid in tong_den:
                bad_found.append(f"🛑 **{g['group']['name']}** ({gid})")
                full_list.append(f"🛑 **{g['group']['name']}**")
            else:
                full_list.append(f"▫️ {g['group']['name']}")

        # THIẾT KẾ EMBED THEO CHUẨN ĐƠN VỊ
        embed = discord.Embed(title="HỆ THỐNG KIỂM TRA KIỂM SOÁT QUÂN SỰ SROV", color=0x2ecc71)
        embed.set_author(name="Bộ Tư Lệnh Kiểm Soát Quân Sự")
        embed.set_thumbnail(url=avatar_url)

        # Xử lý Cảnh báo tiêu chuẩn
        warns = []
        if age < 100: warns.append(f"🔴 Tuổi tài khoản thấp ({age}/100 ngày)")
        if friends < 50: warns.append(f"🔴 Ít bạn bè ({friends}/50 người)")
        if len(all_groups) < 5: warns.append(f"🔴 Tham gia quá ít group ({len(all_groups)}/5)")

        desc = (
            f"**📌 Displayname:** {display_name}\n"
            f"**👤 Username:** {actual_name}\n"
            f"**🆔 Roblox ID:** {user_id}\n"
            f"**🛡️ Safe Chat:** {safe_chat}\n"
            f"**🗓️ Ngày gia nhập:** {created_date.strftime('%d/%m/%Y')}\n"
            f"**⏳ Tuổi tài khoản:** {age} ngày\n"
            f"**👥 Số bạn bè:** {friends} người\n"
            f"**🏰 Số group tham gia:** {len(all_groups)}\n\n"
        )

        if warns:
            desc += "⚠️ **CẢNH BÁO TIÊU CHUẨN:**\n" + "\n".join(warns) + "\n\n"

        desc += "**Group bị blacklist:**\n"
        desc += (" • ".join(bad_found) if bad_found else "Không có") + "\n\n"

        # KẾT LUẬN CUỐI CÙNG
        if not bad_found and not warns:
            desc += "✅ **KẾT LUẬN: ĐỦ ĐIỀU KIỆN**"
            embed.color = 0x2ecc71
        else:
            desc += "❌ **KẾT LUẬN: KHÔNG ĐỦ ĐIỀU KIỆN**"
            embed.color = 0xff0000

        embed.description = desc
        view = GroupView("\n".join(full_list))
        await ctx.send(embed=embed, view=view)

    except Exception as e:
        await ctx.send(f"⚠️ Lỗi: {e}")

bot.run(TOKEN)
