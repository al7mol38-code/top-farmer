@bot.command(name="متصدرين")
async def leaderboard(ctx):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    # جلب أكثر 3 أعضاء تفاعلاً بناءً على مجموع الرسائل ووقت الصوت
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

    # إعداد بيانات المراكز الثلاثة (افتراضي إن وجدوا)
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

    # تكملة المراكز في حال كان عدد الأعضاء أقل من 3
    while len(data) < 3:
        data.append({"mention": "---", "msgs": "0 رسالة", "voice": "0 ساعة و 0 دقيقة"})

    # بناء نص الـ Embed
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
    
    # ربط الصورة مباشرة بالـ Embed (تأكد من رفع الصورة أو وضع رابطها المباشر هنا)
    # يمكنك وضع رابط الصورة المباشر أو إرفاقها كملف محلي
    embed.set_image(url="رابط_الصورة_المباشر_هنا") # أو ضع ملف مرفق إذا أردت

    await ctx.reply(embed=embed, mention_author=True)
