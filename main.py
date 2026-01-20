import discord
from discord.ext import commands
import requests
import os
import json
from datetime import datetime, timezone
from dateutil import parser

# 1. CẤU HÌNH & LƯU TRỮ DỮ LIỆU
TOKEN = os.getenv("TOKEN")
FILE_DB = "blacklist_dynamic.json"

# Danh sách ID gốc (Cố định)
DANH_SACH_DEN_GOC = [35041999, 123456] 

# Tải danh sách ID bổ sung từ file
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

# --- LỆNH QUẢN TRỊ: THÊM & XOÁ GROUP BLACKLIST ---

@bot.command()
@commands.has_permissions(administrator=True)
async def blacklist_add(ctx, group_id: int):
    """Thêm một ID group vào danh sách đen bổ sung"""
    if group_id not in DANH_SACH_DEN_GOC and group_id not in DANH_SACH_THEM:
        DANH_SACH_THEM.append(group_id)
        save_dynamic_data()
        await ctx.send(f"🚫 **Hệ thống ghi nhận:**\n• Đã thêm ID `{group_id}` vào danh sách.")
    else:
        await ctx.send(f"⚠️ ID `{group_id}` đã có trong danh sách.")

@bot.command()
@commands.has_permissions(administrator=True)
async def blacklist_remove(ctx, group_id: int):
    """Xoá một ID group khỏi danh sách đen bổ sung"""
    if group_id in DANH_SACH_THEM:
        DANH_SACH_THEM.remove(group_id)
        save_dynamic_data()
        await ctx.send(f"✅ **Hệ thống cập nhật:**\n• Đã xoá ID `{group_id}` khỏi danh sách.")
    elif group_id in DANH_SACH_DEN_GOC:
        await ctx.send(f"❌ Không thể xoá ID thuộc danh sách gốc của Bộ Tư Lệnh.")
    else:
        await ctx.send(f"⚠️ Không tìm thấy ID `{group_id}` trong dữ liệu.")

# --- LỆNH XEM DANH SÁCH TÊN GROUP ---
@bot.command()
async def check_blacklist(ctx):
    """Liệt kê tên các group bị blacklist"""
    tong_den = list(set(DANH_SACH_DEN_GOC + DANH_SACH_THEM))
    await ctx.send("📡 **Đang truy xuất danh sách đen...**")
    
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
        # Lấy thông tin Roblox
        payload = {"usernames": [username], "excludeBannedUsers": True}
        res = requests.post("https://users.roblox.com/v1/usernames/users", json=payload).json()
        if not res.get("data"): return await ctx.send(f"❌ Không tìm thấy: **{username}**")

        u_data = res["data"][0]
        user_id, actual_name, display_name = u_data["id"], u_data["name"], u_data["displayName"]

        info = requests.get(f"https://users.roblox.com/v1/users/{user_id}").json()
        friends = requests.get(f"https://friends.roblox.com/v1/users/{user_id}/friends/count").json().get("count", 0)
        groups_data = requests.get(f"https://groups.roblox.com/v2/users/{user_id}/groups/roles").json()
        all_groups = groups_data.get("data", [])
        
        avatar_url = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png").json()["data"][0]["imageUrl"]
        
        created_date = parser.isoparse(info["created"]).replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - created_date).days
        sc_bool = info.get("isVieweeSafeChat")

        # KIỂM TRA 4 TẦNG LỌC
        warns = []
        if sc_bool: warns.append("🔴 Safe Chat: **BẬT** (Loại)")
        if age < 100: warns.append(f"🔴 Tuổi tài khoản: **THẤP** ({age}/100 ngày)")
        if friends < 50: warns.append(f"🔴 Bạn bè: **ÍT** ({friends}/50 người)")
        if len(all_groups) < 5: warns.append(f"🔴 Nhóm: **ÍT** ({len(all_groups)}/5 group)")

        # Kiểm tra Blacklist & Rank
        bad_found = []
        tong_den = list(set(DANH_SACH_DEN_GOC + DANH_SACH_THEM))

        for g in all_groups:
            g_id = g['group']['id']
            if g_id in tong_den:
                bad_found.append(f"🛑 **{g['group']['name']}** ({g_id})\n   └ Rank: *{g['role']['name']}*")

        # THIẾT KẾ EMBED (SỬA LỖI NỐI CHUỖI)
        embed = discord.Embed(title="HỆ THỐNG KIỂM TRA KIỂM SOÁT QUÂN SỰ SROV", color=0x2ecc71)
        embed.set_author(name="Bộ Tư Lệnh Kiểm Soát Quân Sự")
        embed.set_thumbnail(url=avatar_url)
        
        desc = f"📌 **Displayname:** {display_name}\n"
        desc += f"👤 **Username:** {actual_name}\n"
        desc += f"🆔 **Roblox ID:** {user_id}\n"
        desc += f"🛡️ **Safe Chat:** {'🔴 Bật' if sc_bool else '🟢 Tắt'}\n"
        desc += f"🗓️ **Ngày gia nhập:** {created_date.strftime('%d/%m/%Y')}\n"
        desc += f"⏳ **Tuổi tài khoản:** {age} ngày\n"
        desc += f"👥 **Số bạn bè:** {friends} người\n"
        desc += f"🏰 **Số group tham gia:** {len(all_groups)}\n"
        desc += f"──────────────────\n\n"

        if warns:
            desc += "⚠️ **CẢNH BÁO TIÊU CHUẨN:**\n" + "\n".join(warns) + "\n\n"

        desc += "🚫 **GROUP BỊ BLACKLIST:**\n"
        desc += ("\n".join(bad_found) if bad_found else "✅ Không phát hiện") + "\n\n"
        desc += f"──────────────────\n\n"

        if not bad_found and not warns:
            desc += "✅ **KẾT LUẬN: ĐỦ ĐIỀU KIỆN**"
            embed.color = 0x2ecc71
        else:
            desc += "❌ **KẾT LUẬN: KHÔNG ĐỦ ĐIỀU KIỆN**"
            embed.color = 0xff0000

        embed.description = desc
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"⚠️ Lỗi: {e}")

bot.run(TOKEN)
