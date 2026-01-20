import discord
from discord.ext import commands
import requests
import os
import json
from datetime import datetime, timezone
from dateutil import parser

# 1. KHO DỮ LIỆU ĐỊNH DANH ĐEN (Ngài hãy dán toàn bộ ID vào đây)
DANH_SACH_DEN_GOC = [
    576559939, 998028484, 47361536, 205543849, 415009980, 34285411, 123469798, 32860218, 
    1059424707, 130818406, 35706033, 35108918, 34973030, 35109046, 34334809, 1088491035, 
    1048944679, 104448675, 1102515063, 13508102, 34766049, 35442362, 35442355, 33295727, 
    494412357, 1007281007, 650288981, 34935340, 34838981, 12938776, 34016213, 33896530, 
    33156070, 33421910, 17387865, 33302258, 14838294, 35683955, 994121070, 16046069, 
    963270266, 603089537, 32824464, 11881320, 17091729, 15027915, 14464551, 15264532, 
    14441186, 33142374, 33981926, 33398345, 994446201, 36055514, 34771501, 35041999, 
    35745867, 35695662, 35104173
]

DANH_SACH_THEM = []
FILE_DB = "blacklist_dynamic.json"
if os.path.exists(FILE_DB):
    with open(FILE_DB, "r") as f:
        DANH_SACH_THEM = json.load(f)

def save_dynamic_data():
    with open(FILE_DB, "w") as f:
        json.dump(DANH_SACH_THEM, f)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)

# --- LỆNH QUẢN TRỊ: THÊM/XOÁ NHÓM ---
@bot.command()
@commands.has_permissions(administrator=True)
async def blacklist_add(ctx, group_id: int):
    if group_id not in DANH_SACH_DEN_GOC and group_id not in DANH_SACH_THEM:
        DANH_SACH_THEM.append(group_id)
        save_dynamic_data()
        await ctx.send(f"🚫 Đã thêm ID `{group_id}` vào radar.")
    else: await ctx.send("⚠️ ID đã tồn tại.")

@bot.command()
@commands.has_permissions(administrator=True)
async def blacklist_remove(ctx, group_id: int):
    if group_id in DANH_SACH_THEM:
        DANH_SACH_THEM.remove(group_id)
        save_dynamic_data()
        await ctx.send(f"✅ Đã xoá ID `{group_id}`.")
    else: await ctx.send("⚠️ Không tìm thấy ID hoặc đây là ID gốc.")

# --- LỆNH KIỂM TRA TOÀN BỘ DANH SÁCH ĐEN ---
@bot.command()
async def check_blacklist(ctx):
    """Hiện toàn bộ group có trong code (Gốc + Thêm)"""
    tong_den = list(set(DANH_SACH_DEN_GOC + DANH_SACH_THEM))
    await ctx.send("📡 **Đang truy xuất toàn bộ danh sách đen...**")
    
    lines = []
    for g_id in tong_den:
        try:
            res = requests.get(f"https://groups.roblox.com/v1/groups/{g_id}").json()
            name = res.get("name", "Không xác định")
            lines.append(f"🛑 **{name}** (`{g_id}`)")
        except:
            lines.append(f"🛑 ID: `{g_id}` (Lỗi API)")
            
    content = "📋 **DANH SÁCH NHÓM ĐỊNH DANH ĐEN:**\n\n" + "\n".join(lines)
    for i in range(0, len(content), 2000):
        await ctx.send(content[i:i+2000])

# --- LỆNH KIỂM TRA HỒ SƠ (FIX SYNTAX & 4 TẦNG LỌC) ---
@bot.command()
async def kiemtra(ctx, username: str):
    try:
        res = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username], "excludeBannedUsers": True}).json()
        if not res.get("data"): return await ctx.send(f"❌ Không tìm thấy: **{username}**")

        u_data = res["data"][0]
        user_id, actual_name, display_name = u_data["id"], u_data["name"], u_data["displayName"]

        info = requests.get(f"https://users.roblox.com/v1/users/{user_id}").json()
        friends = requests.get(f"https://friends.roblox.com/v1/users/{user_id}/friends/count").json().get("count", 0)
        g_data = requests.get(f"https://groups.roblox.com/v2/users/{user_id}/groups/roles").json()
        all_groups = g_data.get("data", [])
        avatar_url = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png").json()["data"][0]["imageUrl"]
        
        created_date = parser.isoparse(info["created"]).replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - created_date).days
        sc_bool = info.get("isVieweeSafeChat")

        # 4 TẦNG LỌC AN NINH
        warns = []
        if sc_bool: warns.append("🔴 Safe Chat: **BẬT** (Loại)")
        if age < 100: warns.append(f"🔴 Tuổi tài khoản: **THẤP** ({age}/100 ngày)")
        if friends < 50: warns.append(f"🔴 Bạn bè: **ÍT** ({friends}/50 người)")
        if len(all_groups) < 5: warns.append(f"🔴 Nhóm: **ÍT** ({len(all_groups)}/5 group)")

        bad_found = []
        tong_den = list(set(DANH_SACH_DEN_GOC + DANH_SACH_THEM))
        for g in all_groups:
            if g['group']['id'] in tong_den:
                bad_found.append(f"🛑 **{g['group']['name']}** ({g['group']['id']})\n   └ Rank: *{g['role']['name']}*")

        # FIX LỖI SYNTAX (Dùng += thay vì lồng ngoặc)
        embed = discord.Embed(title="HỆ THỐNG KIỂM TRA KIỂM SOÁT QUÂN SỰ SROV", color=0x2ecc71)
        embed.set_author(name="Bộ Tư Lệnh Kiểm Soát Quân Sự")
        embed.set_thumbnail(url=avatar_url)
        
        desc = f"📌 **Displayname:** {display_name}\n👤 **Username:** {actual_name}\n🆔 **Roblox ID:** {user_id}\n🛡️ **Safe Chat:** {'🔴 Bật' if sc_bool else '🟢 Tắt'}\n🗓️ **Ngày gia nhập:** {created_date.strftime('%d/%m/%Y')}\n⏳ **Tuổi tài khoản:** {age} ngày\n👥 **Số bạn bè:** {friends} người\n🏰 **Số group tham gia:** {len(all_groups)}\n──────────────────\n\n"

        if warns: desc += "⚠️ **CẢNH BÁO TIÊU CHUẨN:**\n" + "\n".join(warns) + "\n\n"
        desc += "🚫 **GROUP BỊ BLACKLIST:**\n" + ("\n".join(bad_found) if bad_found else "✅ Không phát hiện") + "\n\n──────────────────\n\n"
        
        if not bad_found and not warns:
            desc += "✅ **KẾT LUẬN: ĐỦ ĐIỀU KIỆN**"; embed.color = 0x2ecc71
        else:
            desc += "❌ **KẾT LUẬN: KHÔNG ĐỦ ĐIỀU KIỆN**"; embed.color = 0xff0000

        embed.description = desc
        await ctx.send(embed=embed)
    except Exception as e: await ctx.send(f"⚠️ Lỗi: {e}")

bot.run(TOKEN)
