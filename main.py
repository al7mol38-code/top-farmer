import os
import discord
from discord.ext import commands
import time
import sqlite3
from database import init_db, get_user_data, update_user_data, reset_user_data

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

voice_sessions = {}   

TARGET_CHANNEL_ID = 1533463995795636366
ALLOWED_ROLE_IDS = [1547803947295580240, 1533463569683845160, 1533463570564649121]
RESET_ROLE_IDS = [1533463569683845160, 1533463570564649121]

DB_PATH = '/data/bot_data.db' if os.path.exists('/data') else 'bot_data.db'

@bot.event
async def on_ready():
    init_db()
    print(f"تم تسجيل الدخول بنجاح باسم: {bot.user} وقاعدة البيانات تعمل بنجاح.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    update_user_data(message.author.id, messages_add=1)
    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    
    user_id = member.id
    current_time = time.time()
    is_muted = after.self_mute or after.mute or after.self_deaf or after.deaf

    if before.channel is None and after.channel is not None:
        if not is_muted:
            voice_sessions[user_id] = current_time

    elif before.channel is not None and after.channel is None:
        if user_id in voice_sessions:
            duration = current_time - voice_sessions[user_id]
            update_user_data(user_id, voice_add=duration)
            del voice_sessions[user_id]

    elif before.channel is not None and after.channel is not None:
        if is_muted and user_id in voice_sessions:
            duration = current_time - voice_sessions[user_id]
            update_user_data(user_id, voice_add=duration)
            del voice_sessions[user_id]
        elif not is_muted and user_id not in voice_sessions:
            voice_sessions[user_id] = current_time

# 1. أمر الحذف
@bot.command(name="حذف")
async def delete_messages(ctx, limit: int = 10):
    if not any(role.id in ALLOWED_ROLE_IDS for role in ctx.author.roles):
        await ctx.reply("عذراً، لا تمتلك الرتبة الصلاحية لاستخدام هذا الأمر.", delete_after=5)
        return

    if not ctx.message.reference:
        await ctx.reply("يرجى الرد (Reply) على رسالة الشخص المراد حذف رسائله.", delete_after=5)
        return

    referenced_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    target_user = referenced_message.author

    deleted = await ctx.channel.purge(limit=limit, check=lambda m: m.author.id == target_user.id)
    await ctx.send(f"تم حذف {len(deleted)} رسالة للعضو {target_user.mention}.", delete_after=5)

# 2. أمر النشاط
@bot.command(name="نشاط")
async def activity_stats(ctx, member: discord.Member = None):
    if ctx.channel.id != TARGET_CHANNEL_ID:
        await ctx.reply(f"عذراً، يرجى استخدام أمر النشاط داخل الروم المخصص فقط: <#{TARGET_CHANNEL_ID}>", delete_after=5)
        return

    target = member or ctx.author
    u_id = target.id
    
    data = get_user_data(u_id)
    msgs = data['messages']
    total_seconds = data['voice_seconds']
    
    if u_id in voice_sessions:
        total_seconds += (time.time() - voice_sessions[u_id])
    
    minutes = int(total_seconds // 60)
    hours = minutes // 60
    rem_mins = minutes % 60

    embed = discord.Embed(title=f"إحصائيات تفاعل العضو: {target.display_name}", color=discord.Color.blue())
    embed.description = f"مرحباً بك، هذه هي إحصائيات تفاعل {target.mention}:"
    embed.add_field(name="💬 عدد الرسائل", value=f"{msgs} رسالة", inline=False)
    embed.add_field(name="🔊 الوقت الصوتي (النشط فقط)", value=f"{hours} ساعة و {rem_mins} دقيقة", inline=False)
    
    await ctx.reply(embed=embed, mention_author=True)

# 3. أمر المتصدرين (Leaderboard) مع الصورة والتصميم المطلوب
@bot.command(name="متصدرين")
async def leaderboard(ctx):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, messages, voice_seconds 
        FROM activity 
        ORDER BY (messages + (voice_seconds / 60)) DESC 
        LIMIT 3
    ''')
    top_users = cursor.fetchall()
    conn.close()

    if not top_users:
        await ctx.reply("لا توجد بيانات تفاعل مسجلة حتى الآن.", delete_after=5)
        return

    data = []
    for row in top_users:
        u_id, msgs, v_secs = row
        member = ctx.guild.get_member(u_id)
        mention = member.mention if member else f"<@!{u_id}>"
        
        minutes = int(v_secs // 60)
        hours = minutes // 60
        rem_mins = minutes % 60
        voice_str = f"{hours} ساعة و {rem_mins} دقيقة"
        
        data.append({"mention": mention, "msgs": f"{msgs} رسالة", "voice": voice_str})

    while len(data) < 3:
        data.append({"mention": "---", "msgs": "0 رسالة", "voice": "0 ساعة و 0 دقيقة"})

    description = f"""> *"Absolute Farmer"* 🎬
.. قائمة الأعضاء الأكثر نشاطاً وتأثيراً في الكتابي والصوتي:

━━━━━━━━━━━━━━━━━━━
🥇 المركز الأول: {data[0]['mention']}
💬 التفاعل: {data[0]['msgs']} | 🔊 الوقت الصوتي: {data[0]['voice']}

🥈 المركز الثاني: {data[1]['mention']}
💬 التفاعل: {data[1]['msgs']} | 🔊 الوقت الصوتي: {data[1]['voice']}

🥉 المركز الثالث: {data[2]['mention']}
💬 التفاعل: {data[2]['msgs']} | 🔊 الوقت الصوتي: {data[2]['voice']}
━━━━━━━━━━━━━━━━━━━

🔥استمرو !"""

    embed = discord.Embed(
        title="🏆 قائمة متفاعلين السيرفر المتصدرين (Leaderboard) 🏆",
        description=description,
        color=discord.Color.gold()
    )
    
    # رابط صورة Absolute Cinema (استبدله برابط صورتك المباشر إن أردت)
    embed.set_image(url="https://i.imgur.com/ضع_رابط_الصورة_المباشر_هنا.jpg")

    await ctx.reply(embed=embed, mention_author=True)

# 4. أمر ريست (تصفير لشخص واحد)
@bot.command(name="ريست")
async def reset_stats(ctx, member: discord.Member = None):
    if not any(role.id in RESET_ROLE_IDS for role in ctx.author.roles):
        await ctx.reply("عذراً، هذا الأمر مخصص لرتب الإدارة المحددة فقط.", delete_after=5)
        return

    target = member
    if not target and ctx.message.reference:
        try:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            target = ref_msg.author
        except:
            pass

    if not target:
        await ctx.reply("يرجى عمل منشن للعضو أو الرد على رسالته لتصفير إحصائياته.", delete_after=5)
        return

    u_id = target.id
    reset_user_data(u_id)
    if u_id in voice_sessions:
        voice_sessions[u_id] = time.time()

    await ctx.reply(f"✅ تم تصفير إحصائيات العضو {target.mention} بنجاح من قاعدة البيانات.", mention_author=True)

# 5. أمر ريست الكل (للجميع)
@bot.command(name="ريست-الكل", aliases=["ريست_الكل"])
async def reset_all_stats(ctx):
    if not any(role.id in RESET_ROLE_IDS for role in ctx.author.roles):
        await ctx.reply("عذراً، هذا الأمر مخصص لرتب الإدارة المحددة فقط.", delete_after=5)
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM activity')
    conn.commit()
    conn.close()

    current_time = time.time()
    voice_sessions.clear()
    for guild in ctx.bot.guilds:
        for member in guild.members:
            if member.voice and member.voice.channel:
                is_muted = member.voice.self_mute or member.voice.mute or member.voice.self_deaf or member.voice.deaf
                if not is_muted:
                    voice_sessions[member.id] = current_time

    await ctx.reply("⚠️ **تم تصفير إحصائيات (الرسائل والوقت الصوتي) لجميع أعضاء السيرفر بالكامل بنجاح!**", mention_author=True)

bot.run(os.getenv("DISCORD_TOKEN"))
