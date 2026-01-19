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

DANH_SACH_DEN = [576559939, 998028484, 47361536, 205543849, 415009980, 34285411, 123469798, 32860218, 32860218, 1059424707, 130818406,  35706033, 35108918, 34973030, 35109046, 34334809, 1088491035, 1048944679, 104448675 ,1102515063, 13508102, 35186142, 35186152, 35186176, 33557471,266138500 , 34766049, 35442362, 35442355, 34766049, 35221517, 35221507, 32861180, 33295727, 494412357, 1007281007, 650288981,34935340, 34838981,  12938776, 34016213, 33896530, 33720723, 33156070, 33421910,  17387865, 34935340, 33425887, 33302258, 33302258, 33302258, 14838294, 35683955 , 994121070, 16046069, 963270266, 603089537, 32824464, 11881320, 17091729, 15027915, 14464551 , 15264532 , 14441186, 14207426095, 33142374,  33981926, 33398345, 33421910, 33422397, 33448593, 33421937, 33422341, 33422355, 33425059 , 33302258 , 33425887,  33421910 , 17387865, 34935340, 33425887, 33302258,16858236, 33398345,35058767, 35058756, 34991987, 34990235,33132192, 34887492, 35500095, 35493282, 35153514,35145871, 35138001, 35122343,  5717089, 6959311, 7508224, 5717238, 33142374, 33398345 , 33981926,33932235,6922664, 35121193,994446201,36055514,34771501,35041999,938311141,16868982,35745867,35745725,35695662,35104173]  
 
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
    print(f"✅ Bot KSQS đã online")

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

        safe_chat = "🔴Bật (Loại)" if info.get("isVieweeSafeChat") else "🟢Tắt (Bình thường)"
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
        embed.add_field(name="🏰 Tổng số group", value=f"{total_groups} nhóm", inline=True)

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
        await ctx.send(f"⚠️ Lỗi: {e}")

bot.run(TOKEN)


