import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import os
import json
from datetime import datetime, timezone
from dateutil import parser

# --- 1. HỆ THỐNG LƯU TRỮ VĨNH VIỄN ---
TOKEN = os.getenv("TOKEN") 
FILE_DB = "blacklist_data.json"

def load_data():
    if os.path.exists(FILE_DB):
        try:
            with open(FILE_DB, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

DANH_SACH_DEN = load_data()

def save_data():
    with open(FILE_DB, "w", encoding="utf-8") as f:
        json.dump(DANH_SACH_DEN, f, indent=4)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        # Tối ưu hóa phản ứng nhanh và giảm lỗi RESUMED
        super().__init__(command_prefix="?", intents=intents, heartbeat_timeout=150.0)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"📡 Đang nạp {len(DANH_SACH_DEN)} mục tiêu.")

    async def on_ready(self):
        print(f'✅ Đã đăng nhập thành công: {self.user.name}')
        # Thông báo bot đã online vào kênh 'thông-báo'
        for guild in self.guilds:
            channel = discord.utils.get(guild.text_channels, name="thông-báo")
            if channel:
                embed = discord.Embed(
                    title="📡 THÔNG BÁO HỆ THỐNG",
                    description=f"**Bot KSQS đã Online và sẵn sàng trinh sát!**\nHiện đang kiểm soát: `{len(DANH_SACH_DEN)}` nhóm đen.",
                    color=0x2ecc71,
                    timestamp=datetime.now()
                )
                embed.set_footer(text="Bộ Tư Lệnh Kiểm Soát Quân Sự")
                await channel.send(embed=embed)

bot = MyBot()

# --- 2. XỬ LÝ LỖI VÀ TRUY XUẤT NHANH ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return
    raise error

async def fetch_roblox(session, url, method="GET", data=None):
    try:
        if method == "POST":
            async with session.post(url, json=data) as response: return await response.json()
        async with session.get(url) as response: return await response.json()
    except: return None

class GroupView(discord.ui.View):
    def __init__(self, group_text):
        super().__init__(timeout=60)
        self.group_text = group_text

    @discord.ui.button(label="Xem danh sách nhóm đối tượng", style=discord.ButtonStyle.grey, emoji="📋")
    async def check_groups(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Trích xuất danh sách nhóm ngay lập tức (chỉ người dùng thấy)
        await interaction.response.send_message(content=self.group_text[:2000], ephemeral=True)

# --- 3. HỆ THỐNG LỆNH SLASH ( / ) ---

@bot.tree.command(name="checkaccount", description="Trinh sát hồ sơ đối tượng trên Roblox")
async def checkaccount(interaction: discord.Interaction, username: str):
    await interaction.response.defer() 
    async with aiohttp.ClientSession() as session:
        u_data = await fetch_roblox(session, "https://users.roblox.com/v1/usernames/users", "POST", {"usernames": [username], "excludeBannedUsers": True})
        if not u_data or not u_data.get("data"):
            return await interaction.followup.send(f"❌ Không tìm thấy đối tượng: {username}")
        
        u_id = u_data["data"][0]["id"]
        d_name = u_data["data"][0]["displayName"]
        u_name = u_data["data"][0]["name"]
        profile_url = f"https://www.roblox.com/users/{u_id}/profile"
        
        # Chạy song song nhiều tác vụ để tăng tốc độ phản ứng cực nhanh
        tasks = [
            fetch_roblox(session, f"https://users.roblox.com/v1/users/{u_id}"),
            fetch_roblox(session, f"https://friends.roblox.com/v1/users/{u_id}/friends/count"),
            fetch_roblox(session, f"https://groups.roblox.com/v2/users/{u_id}/groups/roles"),
            fetch_roblox(session, f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={u_id}&size=420x420&format=Png")
        ]
        u_info, friends_data, g_data, thumb_data = await asyncio.gather(*tasks)
        
        friends = friends_data.get("count", 0)
        all_groups = g_data.get("data", [])
        created = parser.isoparse(u_info["created"]).replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - created).days
        sc = u_info.get("isVieweeSafeChat")

        # --- PHÂN TÍCH AN NINH (Đầy đủ tiêu chuẩn & Group Blacklist) ---
        warns = []
        if sc: warns.append("🔴 Safe Chat: **BẬT**")
        if age < 100: warns.append(f"🔴 Tuổi acc: **THẤP** ({age}/100 ngày)")
        if friends < 50: warns.append(f"🔴 Bạn bè: **ÍT** ({friends}/50)")
        if len(all_groups) < 5: warns.append(f"🔴 Group: **ÍT** ({len(all_groups)}/5)")

        bad_found = [f"🛑 **{g['group']['name']}** ({g['group']['id']})\n   └ Rank: **{g['role']['name']}**" 
                     for g in all_groups if g['group']['id'] in DANH_SACH_DEN]

        # --- GIAO DIỆN EMBED CHUẨN KSQS ---
        embed = discord.Embed(title="HỆ THỐNG KIỂM TRA KSQS SROV", color=0x2ecc71 if not (warns or bad_found) else 0xff0000)
        embed.set_author(name="Bộ Tư Lệnh Kiểm Soát Quân Sự")
        embed.set_thumbnail(url=thumb_data["data"][0]["imageUrl"])
        
        embed.add_field(name="📌 Displayname:", value=d_name, inline=True)
        embed.add_field(name="👤 Username:", value=f"[{u_name}]({profile_url})", inline=True) # Liên kết link với username
        embed.add_field(name="🆔 Roblox ID:", value=f"`{u_id}`", inline=True)
        embed.add_field(name="🛡️ Safe Chat:", value="🟢 Tắt" if not sc else "🔴 Bật", inline=True)
        embed.add_field(name="🗓️ Gia nhập:", value=created.strftime('%d/%m/%Y'), inline=True)
        embed.add_field(name="⏳ Tuổi acc:", value=f"{age} ngày", inline=True)
        embed.add_field(name="👤 Bạn bè:", value=str(friends), inline=True)
        embed.add_field(name="🏰 Số group:", value=str(len(all_groups)), inline=True)
        
        embed.add_field(name="──────────────────", value="⚠️ **Cảnh báo tiêu chuẩn:**", inline=False)
        embed.add_field(name="_ _", value="✅ Không có ✅" if not warns else "\n".join(warns), inline=False)
        
        embed.add_field(name="──────────────────", value="🚫 **Group blacklist:**", inline=False)
        embed.add_field(name="_ _", value="✅ Không phát hiện ✅" if not bad_found else "\n".join(bad_found), inline=False)
        
        embed.add_field(name="──────────────────", value=f"**KẾT LUẬN: {'✅ ĐỦ ĐIỀU KIỆN ✅' if not (warns or bad_found) else '❌ KHÔNG ĐỦ ĐIỀU KIỆN ❌'}**", inline=False)
        
        # Danh sách nhóm cho nút bấm
        group_list_text = f"📋 **DANH SÁCH NHÓM CỦA {u_name.upper()}:**\n\n" + "\n".join([f"• {g['group']['name']} ({g['group']['id']})" for g in all_groups])
        await interaction.followup.send(embed=embed, view=GroupView(group_list_text))

@bot.tree.command(name="blacklist_add", description="Thêm ID nhóm vào danh sách đen vĩnh viễn")
async def blacklist_add(interaction: discord.Interaction, ids: str):
    if not interaction.user.guild_permissions.administrator: return
    global DANH_SACH_DEN
    raw_ids = ids.replace(" ", "").split(",")
    added = 0
    for r_id in raw_ids:
        if r_id.isdigit() and int(r_id) not in DANH_SACH_DEN:
            DANH_SACH_DEN.append(int(r_id)); added += 1
    save_data() # Lưu trữ vĩnh viễn không mất ID khi sửa code
    await interaction.response.send_message(f"✅ Đã lưu `{added}` ID. Tổng kho lưu trữ: `{len(DANH_SACH_DEN)}`.")

@bot.tree.command(name="blacklist_remove", description="Gỡ bỏ ID khỏi kho vĩnh viễn")
async def blacklist_remove(interaction: discord.Interaction, ids: str):
    if not interaction.user.guild_permissions.administrator: return
    global DANH_SACH_DEN
    raw_ids = ids.replace(" ", "").split(",")
    removed = 0
    for r_id in raw_ids:
        if r_id.isdigit() and int(r_id) in DANH_SACH_DEN:
            DANH_SACH_DEN.remove(int(r_id)); removed += 1
    save_data() # Cập nhật lại file vĩnh viễn
    await interaction.response.send_message(f"✅ Đã xóa thành công `{removed}` ID GROUP.")

@bot.tree.command(name="check_blacklist", description="Xem danh sách group blacklist hiện có")
async def check_blacklist(interaction: discord.Interaction):
    if not DANH_SACH_DEN: return await interaction.response.send_message("📝 Kho dữ liệu đang trống.")
    await interaction.response.send_message(f"📡 Đang trích xuất dữ liệu {len(DANH_SACH_DEN)} nhóm...")
    async with aiohttp.ClientSession() as session:
        results = []
        for g_id in DANH_SACH_DEN:
            res = await fetch_roblox(session, f"https://groups.roblox.com/v1/groups/{g_id}")
            results.append(f"🛑 **{res.get('name', 'N/A')}** (`{g_id}`)")
        await interaction.channel.send("\n".join(results))

if TOKEN: bot.run(TOKEN)
