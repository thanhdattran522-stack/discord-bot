import discord
from discord.ext import commands
import requests
import os
import json
from datetime import datetime, timezone
from dateutil import parser

# --- 1. KHỞI TẠO HỆ THỐNG ---
TOKEN = os.getenv("TOKEN") 
FILE_DB = "blacklist_data.json"

if os.path.exists(FILE_DB):
    with open(FILE_DB, "r") as f:
        DANH_SACH_DEN = json.load(f)
else:
    DANH_SACH_DEN = []

def save_data():
    with open(FILE_DB, "w") as f:
        json.dump(DANH_SACH_DEN, f)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)

# UI: Nút bấm xem danh sách nhóm đối tượng đang tham gia
class GroupView(discord.ui.View):
    def __init__(self, group_text):
        super().__init__(timeout=60)
        self.group_text = group_text

    @discord.ui.button(label="Xem danh sách nhóm đối tượng", style=discord.ButtonStyle.grey, emoji="📋")
    async def check_groups(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Discord giới hạn 2000 ký tự mỗi tin nhắn
        content = self.group_text[:1990] + "..." if len(self.group_text) > 2000 else self.group_text
        await interaction.response.send_message(content=content, ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ Hệ thống KSQS Tổng Lực đã Online!")

# --- 2. QUẢN LÝ BLACKLIST HÀNG LOẠT ---
@bot.command()
@commands.has_permissions(administrator=True)
async def blacklist_add(ctx, *, ids_str: str):
    """Add hàng loạt: ?blacklist_add 123, 456, 789"""
    raw_ids = ids_str.replace(" ", "").split(",")
    added_count = 0
    for r_id in raw_ids:
        if r_id.isdigit():
            g_id = int(r_id)
            if g_id not in DANH_SACH_DEN:
                DANH_SACH_DEN.append(g_id)
                added_count += 1
    save_data()
    await ctx.send(f"✅ Đã thêm `{added_count}`vào kho lưu trữ.")

@bot.command()
@commands.has_permissions(administrator=True)
async def blacklist_remove(ctx, *, ids_str: str):
    """Xoá hàng loạt: ?blacklist_remove 123, 456"""
    raw_ids = ids_str.replace(" ", "").split(",")
    removed_count = 0
    for r_id in raw_ids:
        if r_id.isdigit():
            g_id = int(r_id)
            if g_id in DANH_SACH_DEN:
                DAN_SACH_DEN.remove(g_id)
                removed_count += 1
    save_data()
    await ctx.send(f"🗑️ Đã gỡ bỏ `{removed_count}` mục tiêu khỏi radar.")

# --- 3. LỆNH KIỂM TRA TÁC CHIẾN (FULL OPTION) ---
@bot.command()
async def kiemtra(ctx, username: str):
    try:
        # Lấy thông tin cơ bản
        res = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username], "excludeBannedUsers": True}).json()
        if not res.get("data"): return await ctx.send(f"❌ Không tìm thấy đối tượng: {username}")
        
        u_id = res["data"][0]["id"]
        u_info = requests.get(f"https://users.roblox.com/v1/users/{u_id}").json()
        friends = requests.get(f"https://friends.roblox.com/v1/users/{u_id}/friends/count").json().get("count", 0)
        g_data = requests.get(f"https://groups.roblox.com/v2/users/{u_id}/groups/roles").json()
        all_groups = g_data.get("data", [])
        thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={u_id}&size=420x420&format=Png").json()["data"][0]["imageUrl"]
        
        created = parser.isoparse(u_info["created"]).replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - created).days
        sc = u_info.get("isVieweeSafeChat")

        # Phân tích an ninh
        warns = []
        if sc: warns.append("🔴 Safe Chat: **BẬT**")
        if age < 100: warns.append(f"🔴 Tuổi acc: **THẤP** ({age}/100 ngày)")
        if friends < 50: warns.append(f"🔴 Bạn bè: **ÍT** ({friends}/50)")
        if len(all_groups) < 5: warns.append(f"🔴 Nhóm: **ÍT** ({len(all_groups)}/5)")

        # Quét Blacklist & Rank
        bad_found = []
        for g in all_groups:
            if g['group']['id'] in DANH_SACH_DEN:
                bad_found.append(f"🛑 **{g['group']['name']}** ({g['group']['id']})\n   └ Rank: **{g['role']['name']}**")

        # Khởi tạo Embed
        embed = discord.Embed(title="HỆ THỐNG KIỂM TRA KSQS SROV", color=0xff0000 if (warns or bad_found) else 0x2ecc71)
        embed.set_author(name="Bộ Tư Lệnh Kiểm Soát Quân Sự", icon_url="https://www.roblox.com/asset/?id=12345678") # Thay bằng ID logo của ngài
        embed.set_thumbnail(url=thumb)
        
        desc = [
            f"📌 **Displayname:** {res['data'][0]['displayName']}",
            f"👤 **Username:** {res['data'][0]['name']}",
            f"🆔 **Roblox ID:** {u_id}",
            f"🛡️ **Safe Chat:** {'🔴 Bật' if sc else '🟢 Tắt'}",
            f"🗓️ **Ngày Gia nhập:** {created.strftime('%d/%m/%Y')}",
            f"⏳ **Tuổi acc:** {age} ngày",
            f"👥 **Bạn bè:** {friends}",
            f"🏰 **Số group:** {len(all_groups)}",
            "──────────────────",
            "⚠️ **Cảnh báo tiêu chuẩn:**",
            ("\n".join(warns) if warns else "✅ Không có"),
            "",
            "🚫 **Group blacklist:**",
            ("\n".join(bad_found) if bad_found else "✅ Không phát hiện"),
            "──────────────────",
            f"**KẾT LUẬN: {'❌ KHÔNG ĐỦ ĐIỀU KIỆN' if (warns or bad_found) else '✅ ĐỦ ĐIỀU KIỆN'}**"
        ]
        embed.description = "\n".join(desc)
        
        # Tạo danh sách toàn bộ group để hiện khi bấm nút
        group_list_text = f"📋 **TẤT CẢ NHÓM CỦA {username.upper()}:**\n\n" + "\n".join([f"• {g['group']['name']} ({g['group']['id']}) - Rank: {g['role']['name']}" for g in all_groups])
        view = GroupView(group_list_text)

        await ctx.send(embed=embed, view=view)
    except Exception as e: await ctx.send(f"⚠️ Lỗi: {e}")

# --- 4. LỆNH XEM TOÀN BỘ DANH SÁCH ĐEN CỦA BOT ---
@bot.command()
async def check_blacklist(ctx):
    if not DANH_SACH_DEN: return await ctx.send("📝 Kho đang trống dữ liệu.")
    await ctx.send("📡 **Đang trích xuất danh sách đen toàn hệ thống...**")
    lines = []
    for g_id in DANH_SACH_DEN:
        try:
            res = requests.get(f"https://groups.roblox.com/v1/groups/{g_id}").json()
            lines.append(f"🛑 **{res.get('name', 'N/A')}** (`{g_id}`)")
        except: lines.append(f"🛑 ID: `{g_id}` (Lỗi API)")
    
    content = f"📋 **DANH SÁCH ĐEN ({len(DANH_SACH_DEN)} NHÓM):**\n\n" + "\n".join(lines)
    for i in range(0, len(content), 2000): await ctx.send(content[i:i+2000])

if TOKEN: bot.run(TOKEN)
