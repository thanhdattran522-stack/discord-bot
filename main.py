import discord
from discord.ext import commands
import aiohttp # Nâng cấp: Xử lý bất đồng bộ để chống treo bot
import asyncio
import os
import json
from datetime import datetime, timezone
from dateutil import parser

# --- 1. CẤU HÌNH HỆ THỐNG ---
TOKEN = os.getenv("TOKEN") 
FILE_DB = "blacklist_data.json"

# Nạp dữ liệu từ kho lưu trữ
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

# Hàm bổ trợ API siêu tốc
async def fetch_roblox(session, url, method="GET", data=None):
    try:
        if method == "POST":
            async with session.post(url, json=data) as response:
                return await response.json()
        async with session.get(url) as response:
            return await response.json()
    except:
        return None

# UI: Nút bấm trinh sát danh sách nhóm của đối tượng
class GroupView(discord.ui.View):
    def __init__(self, group_text):
        super().__init__(timeout=60)
        self.group_text = group_text

    @discord.ui.button(label="Xem danh sách nhóm đối tượng", style=discord.ButtonStyle.grey, emoji="📋")
    async def check_groups(self, interaction: discord.Interaction, button: discord.ui.Button):
        content = self.group_text[:1990] + "..." if len(self.group_text) > 2000 else self.group_text
        await interaction.response.send_message(content=content, ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ Hệ thống KSQS đã Online.")

# --- 2. QUẢN LÝ BLACKLIST HÀNG LOẠT (TỐI ƯU) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def blacklist_add(ctx, *, ids_str: str):
    """Add hàng loạt cách nhau bởi dấu phẩy"""
    raw_ids = ids_str.replace(" ", "").split(",")
    added_count = 0
    for r_id in raw_ids:
        if r_id.isdigit():
            g_id = int(r_id)
            if g_id not in DANH_SACH_DEN:
                DANH_SACH_DEN.append(g_id)
                added_count += 1
    save_data()
    await ctx.send(f"✅ Đã thêm `{added_count}` ID vào kho lưu trữ. Tổng số: `{len(DAN_SACH_DEN)}`.")

@bot.command()
@commands.has_permissions(administrator=True)
async def blacklist_remove(ctx, *, ids_str: str):
    """Xoá hàng loạt cách nhau bởi dấu phẩy"""
    raw_ids = ids_str.replace(" ", "").split(",")
    removed_count = 0
    for r_id in raw_ids:
        if r_id.isdigit():
            g_id = int(r_id)
            if g_id in DANH_SACH_DEN:
                DANH_SACH_DEN.remove(g_id)
                removed_count += 1
    save_data()
    await ctx.send(f"🗑️ Đã gỡ bỏ `{removed_count}` ID khỏi kho lưu trữ.")

# --- 3. LỆNH KIỂM TRA TÁC CHIẾN (FULL OPTION + FIX TREO) ---
@bot.command()
async def kiemtra(ctx, username: str):
    async with aiohttp.ClientSession() as session:
        try:
            # Lấy thông tin cơ bản
            u_data = await fetch_roblox(session, "https://users.roblox.com/v1/usernames/users", "POST", {"usernames": [username], "excludeBannedUsers": True})
            if not u_data or not u_data.get("data"):
                return await ctx.send(f"❌ Không tìm thấy đối tượng: {username}")
            
            u_id = u_data["data"][0]["id"]
            
            # Chạy song song các request để tối ưu tốc độ
            tasks = [
                fetch_roblox(session, f"https://users.roblox.com/v1/users/{u_id}"),
                fetch_roblox(session, f"https://friends.roblox.com/v1/users/{u_id}/friends/count"),
                fetch_roblox(session, f"https://groups.roblox.com/v2/users/{u_id}/groups/roles"),
                fetch_roblox(session, f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={u_id}&size=420x420&format=Png")
            ]
            u_info, friends_data, g_data, thumb_data = await asyncio.gather(*tasks)
            
            friends = friends_data.get("count", 0)
            all_groups = g_data.get("data", [])
            thumb = thumb_data["data"][0]["imageUrl"]
            
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
            bad_found = [f"🛑 **{g['group']['name']}** ({g['group']['id']})\n   └ Rank: **{g['role']['name']}**" 
                         for g in all_groups if g['group']['id'] in DANH_SACH_DEN]

            # Khởi tạo Embed
            embed = discord.Embed(title="HỆ THỐNG KIỂM TRA KSQS SROV", color=0xff0000 if (warns or bad_found) else 0x2ecc71)
            embed.set_author(name="Bộ Tư Lệnh Kiểm Soát Quân Sự")
            embed.set_thumbnail(url=thumb)
            
            desc = [
                f"📌 **Displayname:** {u_data['data'][0]['displayName']}",
                f"👤 **Username:** {u_data['data'][0]['name']}",
                f"🆔 **Roblox ID:** {u_id}",
                f"🛡️ **Safe Chat:** {'🔴 Bật' if sc else '🟢 Tắt'}",
                f"🗓️ **Gia nhập:** {created.strftime('%d/%m/%Y')}",
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
            
            group_list_text = f"📋 **TẤT CẢ NHÓM CỦA {username.upper()}:**\n\n" + "\n".join([f"• {g['group']['name']} ({g['group']['id']}) - Rank: {g['role']['name']}" for g in all_groups])
            view = GroupView(group_list_text)

            await ctx.send(embed=embed, view=view)
        except Exception as e: await ctx.send(f"⚠️ Lỗi: {e}")

# --- 4. LỆNH XEM TOÀN BỘ DANH SÁCH ĐEN (FIX LAG) ---
@bot.command()
async def check_blacklist(ctx):
    if not DANH_SACH_DEN: return await ctx.send("📝 Kho đang trống dữ liệu.")
    await ctx.send(f"📡 **Đang trinh sát {len(DANH_SACH_DEN)} nhóm...** (Vui lòng chờ)")
    
    async with aiohttp.ClientSession() as session:
        lines = []
        for i in range(0, len(DANH_SACH_DEN), 10): # Xử lý theo đợt 10 nhóm
            batch = DANH_SACH_DEN[i:i+10]
            for g_id in batch:
                res = await fetch_roblox(session, f"https://groups.roblox.com/v1/groups/{g_id}")
                name = res.get("name", "N/A") if res else "Lỗi API"
                lines.append(f"🛑 **{name}** (`{g_id}`)")
            await asyncio.sleep(0.5) # Nghỉ để tránh bị Roblox chặn
                
        content = f"📋 **DANH SÁCH ĐEN ({len(DANH_SACH_DEN)} NHÓM):**\n\n" + "\n".join(lines)
        for j in range(0, len(content), 2000): await ctx.send(content[j:j+2000])

if TOKEN: bot.run(TOKEN)
