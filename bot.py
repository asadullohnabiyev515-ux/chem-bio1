import logging, httpx, threading, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN    = os.environ.get("TG_BOT_TOKEN", "8704747686:AAEL3E6QMKXvsznhxO5CKqumbSYHR3G4erM")
ADMIN_IDS    = [5145005581]
MINI_APP_URL = "https://asadullohnabiyev515-ux.github.io/milliy-sertifikat/app.html?v=1781036953"
BACKEND_URL  = os.environ.get("BACKEND_URL", "https://chem-bio1.onrender.com")
KANAL        = "@kimyo_corner"

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

async def api_get(path):
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BACKEND_URL}{path}", timeout=15)
        return r.json()

async def api_post(path, data):
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BACKEND_URL}{path}", json=data, timeout=15)
        return r.json()

async def obuna_tekshir(bot, user_id):
    try:
        member = await bot.get_chat_member(KANAL, user_id)
        return member.status in ["member","administrator","creator"]
    except Exception:
        return False

def varaq_skaner(rasm_bytes, n_savol=35):
    import numpy as np
    import cv2
    nparr = np.frombuffer(rasm_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None: return None, None, "Rasm o'qilmadi"
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    blurred = cv2.GaussianBlur(gray, (5,5), 0)
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=12,
        param1=50, param2=22, minRadius=7, maxRadius=18)
    if circles is None: return None, None, "Doiralar topilmadi!"
    circles = np.round(circles[0,:]).astype("int")
    def is_filled(g,cx,cy,r):
        mask=np.zeros(g.shape,dtype=np.uint8)
        cv2.circle(mask,(cx,cy),max(r-2,3),255,-1)
        pixels=g[mask==255]
        return len(pixels)>0 and np.sum(pixels<110)/len(pixels)>0.33
    rows={}
    for (cx,cy,r) in circles:
        k=cy//15
        if k not in rows: rows[k]=[]
        rows[k].append((cx,cy,r))
    varaq_id=""
    sorted_rows=sorted(rows.items())
    id_digits=[]
    for rk,row in sorted_rows[:4]:
        for (cx,cy,r) in sorted(row,key=lambda c:c[0]):
            if is_filled(gray,cx,cy,r): id_digits.append(str(rk%10))
    if id_digits: varaq_id="".join(id_digits[:3]).zfill(3)
    results={}; savol=1
    for rk,row in sorted_rows:
        row_s=sorted(row,key=lambda c:c[0])
        if len(row_s)>=4:
            if 33<=savol<=35: harflar=["A","B","C","D","E","F"]
            else: harflar=["A","B","C","D"]
            for idx,(cx,cy,r) in enumerate(row_s[:len(harflar)]):
                if is_filled(gray,cx,cy,r): results[str(savol)]=harflar[idx]; break
            if str(savol) not in results: results[str(savol)]=""
            savol+=1
            if savol>n_savol: break
    return results, varaq_id, None

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user=update.effective_user; uid=user.id
    if uid not in ADMIN_IDS:
        obuna=await obuna_tekshir(ctx.bot,uid)
        if not obuna:
            kb=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Kanalga obuna bo'lish",url=f"https://t.me/{KANAL[1:]}")],
                [InlineKeyboardButton("✅ Tekshirish",callback_data="obuna_tekshir")],
            ])
            await update.message.reply_text(
                f"⚠️ Kirish cheklangan\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Botdan foydalanish uchun\n"
                f"kanalga obuna bo'ling:\n\n"
                f"📣 {KANAL}",
                reply_markup=kb)
            return
    is_admin=uid in ADMIN_IDS
    tugmalar=[
        [InlineKeyboardButton("🌐 Platformaga kirish",web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton("📚 Kitoblar",callback_data="kitoblar"),
         InlineKeyboardButton("📄 Varaqalar",callback_data="varaqlar")],
    ]
    if is_admin:
        tugmalar.append([InlineKeyboardButton("👨‍🏫 Ustoz paneli",callback_data="ustoz")])
    await update.message.reply_text(
        f"Assalomu alaykum, {user.first_name}!\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎓 EduTest — Ta'lim Platformasi\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Bo'limni tanlang:",
        reply_markup=InlineKeyboardMarkup(tugmalar))

async def tugma(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; data=q.data; uid=q.from_user.id
    await q.answer()

    if data=="obuna_tekshir":
        obuna=await obuna_tekshir(ctx.bot,uid)
        if obuna:
            await q.edit_message_text(
                "✅ Obuna tasdiqlandi!\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "/start yozing.")
        else:
            kb=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Kanalga o'tish",url=f"https://t.me/{KANAL[1:]}")],
                [InlineKeyboardButton("✅ Tekshirish",callback_data="obuna_tekshir")],
            ])
            await q.edit_message_text(
                f"⚠️ Hali {KANAL} kanaliga\nobuna bo'lmagansiz!",
                reply_markup=kb)
        return

    if data=="elon_yoz" and uid in ADMIN_IDS:
        ctx.user_data["kutish"]="elon_sarlavha"
        await q.edit_message_text(
            "📢 Yangi e'lon\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "E'lon sarlavhasini yozing:")
        return

    if data=="savol_baza" and uid in ADMIN_IDS:
        ctx.user_data["kutish"]="baza_fan"
        await q.edit_message_text(
            "📥 Savol bazasi yuklash\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Fayl formati (.docx yoki .txt):\n\n"
            "Savol: Suvning formulasi?\n"
            "A) H2O\n"
            "B) CO2\n"
            "C) O2\n"
            "D) NaCl\n"
            "Togri: A\n\n"
            "Har savol orasida bo'sh qator bo'lsin.\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Fan nomini yozing:"
        )
        return

    if data=="varaq_yukla" and uid in ADMIN_IDS:
        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 20 savol",callback_data="vyuk_20"),InlineKeyboardButton("📄 30 savol",callback_data="vyuk_30")],
            [InlineKeyboardButton("📄 40 savol",callback_data="vyuk_40"),InlineKeyboardButton("📄 50 savol",callback_data="vyuk_50")],
            [InlineKeyboardButton("⬅️ Orqaga",callback_data="ustoz")],
        ])
        await q.edit_message_text(
            "📄 Varaq yuklash\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Savollar sonini tanlang,\nso'ng PDF faylni yuboring:",
            reply_markup=kb)
        return

    if data.startswith("vyuk_") and uid in ADMIN_IDS:
        soni=data[len("vyuk_"):]
        ctx.user_data["kutish"]="varaq_fayl"
        ctx.user_data["varaq_soni"]=soni
        await q.edit_message_text(f"{soni} savollik varaq PDF faylini yuboring:")
        return

    if data=="varaqlar":
        try:
            res=await api_get("/varaqlar/royxat")
            varaqlar=res.get("varaqlar",[])
        except Exception: varaqlar=[]
        if not varaqlar:
            await q.edit_message_text(
                "📄 Javob varaqlari\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "Hozircha varaq mavjud emas.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga",callback_data="bosh")]]))
            return
        tugmalar=[]
        for v in varaqlar:
            tugmalar.append([InlineKeyboardButton(f"📄 {v['soni']} savollik varaq",callback_data=f"varaqol_{v['soni']}")])
        tugmalar.append([InlineKeyboardButton("⬅️ Orqaga",callback_data="bosh")])
        await q.edit_message_text(
            "📄 Javob varaqlari\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Kerakli varaqni tanlang:",
            reply_markup=InlineKeyboardMarkup(tugmalar))
        return

    if data.startswith("varaqol_"):
        soni=data[len("varaqol_"):]
        try:
            res=await api_get("/varaqlar/royxat")
            varaqlar=res.get("varaqlar",[])
            topildi=None
            for v in varaqlar:
                if v["soni"]==soni: topildi=v; break
            if topildi and topildi.get("fayl_id"):
                await ctx.bot.send_document(chat_id=uid,document=topildi["fayl_id"],
                    caption=f"📄 {soni} savollik javob varaqi")
            else:
                await q.answer("Varaq topilmadi!",show_alert=True)
        except Exception as e:
            await q.answer(f"Xato: {str(e)}",show_alert=True)
        return

    if data=="kitoblar":
        try:
            res=await api_get("/kitob/fanlar")
            fanlar=res.get("fanlar",[])
        except Exception: fanlar=[]
        if not fanlar:
            await q.edit_message_text(
                "📚 Kitoblar\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "Hozircha kitob mavjud emas.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga",callback_data="bosh")]]))
            return
        tugmalar=[[InlineKeyboardButton(f"📖 {f}",callback_data=f"kitob_fan_{f}")] for f in fanlar]
        tugmalar.append([InlineKeyboardButton("⬅️ Orqaga",callback_data="bosh")])
        await q.edit_message_text(
            "📚 Kitoblar\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Fan tanlang:",
            reply_markup=InlineKeyboardMarkup(tugmalar))

    elif data.startswith("kitob_fan_"):
        fan=data[len("kitob_fan_"):]
        try:
            res=await api_get(f"/kitob/royxat/{fan}")
            kitoblar=res.get("kitoblar",[])
        except Exception: kitoblar=[]
        if not kitoblar:
            await q.edit_message_text(
                f"📚 {fan}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Bu fan bo'yicha kitob mavjud emas.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga",callback_data="kitoblar")]]))
            return
        tugmalar=[[InlineKeyboardButton(f"📄 {k['nomi']}",callback_data=f"kitob_ol_{fan}_{i}")] for i,k in enumerate(kitoblar)]
        tugmalar.append([InlineKeyboardButton("⬅️ Orqaga",callback_data="kitoblar")])
        await q.edit_message_text(
            f"📚 {fan}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Kitobni tanlang:",
            reply_markup=InlineKeyboardMarkup(tugmalar))

    elif data.startswith("kitob_ol_"):
        parts=data[len("kitob_ol_"):].rsplit("_",1)
        fan=parts[0]; idx=int(parts[1])
        try:
            res=await api_get(f"/kitob/royxat/{fan}")
            kitob=res["kitoblar"][idx]
            await ctx.bot.send_document(chat_id=uid,document=kitob["fayl_id"],
                caption=f"📚 {kitob['nomi']}\n📖 Fan: {fan}")
        except Exception as e:
            await q.edit_message_text(f"Xato: {str(e)}")

    elif data=="kitob_qosh" and uid in ADMIN_IDS:
        ctx.user_data["kutish"]="kitob_fan"
        await q.edit_message_text("Kitob qoshish\n\nFan nomini yozing:")

    elif data=="kitob_ochir_menu" and uid in ADMIN_IDS:
        try:
            res=await api_get("/kitob/fanlar")
            fanlar=res.get("fanlar",[])
        except Exception: fanlar=[]
        if not fanlar:
            await q.edit_message_text("Kitoblar yoq."); return
        tugmalar=[[InlineKeyboardButton(f"🗑 {f}",callback_data=f"kitob_ochir_fan_{f}")] for f in fanlar]
        tugmalar.append([InlineKeyboardButton("⬅️ Orqaga",callback_data="ustoz_kitob")])
        await q.edit_message_text("Qaysi fandan kitob ochirish?",reply_markup=InlineKeyboardMarkup(tugmalar))

    elif data.startswith("kitob_ochir_fan_") and uid in ADMIN_IDS:
        fan=data[len("kitob_ochir_fan_"):]
        try:
            res=await api_get(f"/kitob/royxat/{fan}")
            kitoblar=res.get("kitoblar",[])
        except Exception: kitoblar=[]
        tugmalar=[[InlineKeyboardButton(f"🗑 {k['nomi']}",callback_data=f"kitob_ochir_{fan}_{i}")] for i,k in enumerate(kitoblar)]
        tugmalar.append([InlineKeyboardButton("⬅️ Orqaga",callback_data="kitob_ochir_menu")])
        await q.edit_message_text(f"{fan} kitoblaridan birini ochirish:",reply_markup=InlineKeyboardMarkup(tugmalar))

    elif data.startswith("kitob_ochir_") and not data.startswith("kitob_ochir_fan_") and uid in ADMIN_IDS:
        parts=data[len("kitob_ochir_"):].rsplit("_",1)
        fan=parts[0]; idx=int(parts[1])
        try:
            async with httpx.AsyncClient() as c:
                r=await c.delete(f"{BACKEND_URL}/kitob/ochir/{fan}/{idx}",params={"ustoz_id":uid},timeout=10)
                d=r.json()
            if d.get("success"):
                await q.edit_message_text("Kitob ochirildi!")
            else:
                await q.edit_message_text(f"Xato: {d.get('detail','')}")
        except Exception as e:
            await q.edit_message_text(f"Xato: {str(e)}")

    elif data=="ustoz_kitob" and uid in ADMIN_IDS:
        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Kitob qo'shish",callback_data="kitob_qosh")],
            [InlineKeyboardButton("🗑 Kitob o'chirish",callback_data="kitob_ochir_menu")],
            [InlineKeyboardButton("⬅️ Orqaga",callback_data="ustoz")],
        ])
        await q.edit_message_text(
            "📚 Kitoblar boshqaruvi\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Amalni tanlang:",
            reply_markup=kb)

    elif data=="test_yangi_javob" and uid in ADMIN_IDS:
        ctx.user_data["kutish"]="test_javoblar"
        ctx.user_data["javoblar"]={}
        ctx.user_data["savol"]=1
        await q.edit_message_text(
            "✍️ Yangi javoblar kiritish\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Har bir savol javobini ketma-ket yozing:")
        await savol_sora_q(ctx, uid)

    elif data=="savol_qosh" and uid in ADMIN_IDS:
        ctx.user_data["kutish"]="savol_fan"
        await q.edit_message_text(
            "❓ Savol qo'shish\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Fan nomini yozing:")

    elif data=="bosh":
        try: await q.delete_message()
        except Exception: pass
        await ctx.bot.send_message(chat_id=uid,text="/start yozing")

    elif data=="natija":
        ctx.user_data["kutish"]="natija_kod"
        await q.edit_message_text(
            "📊 Natija tekshirish\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Test kodini yozing:")

    elif data=="ustoz" and uid in ADMIN_IDS:
        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Test yaratish",callback_data="test_yarat"),
             InlineKeyboardButton("📋 Testlarim",callback_data="testlar")],
            [InlineKeyboardButton("🏁 Testni yakunlash",callback_data="yakunla")],
            [InlineKeyboardButton("📚 Kitoblar",callback_data="ustoz_kitob"),
             InlineKeyboardButton("📄 Varaq yuklash",callback_data="varaq_yukla")],
            [InlineKeyboardButton("📢 E'lon yozish",callback_data="elon_yoz")],
            [InlineKeyboardButton("❓ Savol qo'shish",callback_data="savol_qosh")],
            [InlineKeyboardButton("⬅️ Bosh menyu",callback_data="bosh")],
        ])
        await q.edit_message_text(
            "👨‍🏫 USTOZ PANELI\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Amalni tanlang:",
            reply_markup=kb)

    elif data=="test_yarat" and uid in ADMIN_IDS:
        ctx.user_data["kutish"]="test_fan"
        await q.edit_message_text(
            "➕ Yangi test yaratish\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Fan nomini yozing:")

    elif data.startswith("test_nusxa_") and uid in ADMIN_IDS:
        asl_kod = data[len("test_nusxa_"):]
        try:
            res = await api_get(f"/test/tekshir/{asl_kod}")
            if res.get("topildi"):
                res2 = await api_post("/test/yarat", {
                    "kod": asl_kod,
                    "fan": res.get("fan", ""),
                    "ustoz_id": uid,
                    "javoblar": res.get("javoblar", {}),
                    "tur": res.get("tur", "milliy"),
                    "savollar_soni": res.get("savollar_soni", 40)
                })
                if res2.get("success"):
                    yangi_kod = res2.get("kod", "")
                    await q.edit_message_text("Yangi sessiya yaratildi!\n\nEski kod: "+asl_kod+"\nYangi kod: "+yangi_kod+"\n\nBu kodni oquvchilarga yuboring!")
                else:
                    await q.edit_message_text(f"Xato: {res2.get('detail','')}")
        except Exception as e:
            await q.edit_message_text(f"Xato: {str(e)}")

    elif data=="testlar" and uid in ADMIN_IDS:
        try:
            res=await api_get(f"/ustoz/testlar/{uid}")
            testlar=res.get("testlar",[])
            if not testlar:
                await q.edit_message_text(
                    "📋 Testlarim\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    "Hozircha test mavjud emas.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga",callback_data="ustoz")]]))
                return
            matn="📋 TESTLARIM\n━━━━━━━━━━━━━━━━━━\n\n"
            for t in testlar:
                holat="✅ Tugagan" if t["tugadi"] else "🟢 Aktiv"
                tur="🏆 Milliy" if t.get("tur","milliy")=="milliy" else f"📝 Oddiy ({t.get('savollar_soni',40)} savol)"
                matn+=f"📌 {t['kod']} — {t['fan']}\n   {tur} | 👥 {t['talabalar']} ta | {holat}\n\n"
            await q.edit_message_text(matn,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga",callback_data="ustoz")]]))
        except Exception as e:
            await q.edit_message_text(f"Xato: {str(e)}")

    elif data=="yakunla" and uid in ADMIN_IDS:
        ctx.user_data["kutish"]="yakunla_kod"
        await q.edit_message_text(
            "🏁 Testni yakunlash\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Test kodini yozing:")

    elif data=="skaner" and uid in ADMIN_IDS:
        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton("📷 30 savollik",callback_data="skaner_30"),
             InlineKeyboardButton("📷 35 savollik",callback_data="skaner_35")],
            [InlineKeyboardButton("📷 40 savollik",callback_data="skaner_40")],
            [InlineKeyboardButton("⬅️ Orqaga",callback_data="ustoz")],
        ])
        await q.edit_message_text(
            "📷 Varaq skaneri\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Varaq turini tanlang:",
            reply_markup=kb)

    elif data in ["skaner_30","skaner_35","skaner_40"] and uid in ADMIN_IDS:
        soni=int(data.split("_")[1])
        ctx.user_data["skaner_n_savol"]=soni
        ctx.user_data["kutish"]="skaner_kod"
        await q.edit_message_text(f"{soni} savollik\n\nTest kodini yozing:")

async def rasm_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    holat=ctx.user_data.get("kutish")
    if holat=="kitob_fayl" and uid in ADMIN_IDS:
        fan=ctx.user_data.get("kitob_fan","")
        nomi=ctx.user_data.get("kitob_nomi","")
        try:
            fayl_id=update.message.photo[-1].file_id
            res=await api_post("/kitob/qosh",{"fan":fan,"nomi":nomi,"fayl_id":fayl_id,"ustoz_id":uid})
            if res.get("success"):
                await update.message.reply_text(f"Kitob qoshildi!\n{nomi}\nFan: {fan}")
            else:
                await update.message.reply_text(f"Xato: {res.get('detail','')}")
        except Exception as e:
            await update.message.reply_text(f"Xato: {str(e)}")
        ctx.user_data.pop("kutish",None)
        return

    if uid not in ADMIN_IDS: return
    if holat!="skaner_rasm":
        await update.message.reply_text("Ustoz paneli → Varaq skanerlash"); return
    test_kod=ctx.user_data.get("skaner_test_kod","")
    n_savol=ctx.user_data.get("skaner_n_savol",35)
    await update.message.reply_text("Skanerlanyapti...")
    try:
        photo=update.message.photo[-1]
        file=await ctx.bot.get_file(photo.file_id)
        rasm_bytes=await file.download_as_bytearray()
        javoblar,varaq_id,xato=varaq_skaner(bytes(rasm_bytes),n_savol)
        if xato:
            await update.message.reply_text(f"Xato: {xato}"); return
        oquvchi=None
        if varaq_id:
            try:
                res=await api_get(f"/student/id/{test_kod}/{varaq_id}")
                if res.get("success"): oquvchi=res["oquvchi"]
            except Exception: pass
        if not oquvchi:
            ctx.user_data["skaner_javoblar"]=javoblar
            ctx.user_data["kutish"]="skaner_id_qolda"
            await update.message.reply_text("Varaq ID aniqlanmadi. ID raqamini kiriting:")
            return
        matn=f"Skanerlandi!\n{oquvchi['ism']} {oquvchi['familiya']}\nID: {varaq_id}\nTest: {test_kod}\n"
        await update.message.reply_text(matn)
        if n_savol==40:
            ctx.user_data["skaner_javoblar"]=javoblar
            ctx.user_data["skaner_varaq_id"]=varaq_id
            ctx.user_data["kutish"]="skaner_ochiq_36"
            await update.message.reply_text("36-savol javobini yozing:")
            return
        res=await api_post("/natija/skaner",{"test_kod":test_kod,"varaq_id":varaq_id,"javoblar":javoblar})
        if res.get("success"):
            await update.message.reply_text(f"{oquvchi['ism']} natijasi saqlandi!")
        else:
            await update.message.reply_text(f"Xato: {res.get('detail','')}")
        ctx.user_data.pop("kutish",None)
    except Exception as e:
        await update.message.reply_text(f"Xato: {str(e)}")
        ctx.user_data.pop("kutish",None)

async def fayl_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    if uid not in ADMIN_IDS: return
    if ctx.user_data.get("kutish")=="baza_matn_yoki_fayl":
        fan=ctx.user_data.get("baza_fan","")
        mavzu=ctx.user_data.get("baza_mavzu","")
        try:
            fayl=update.message.document
            if not fayl:
                await update.message.reply_text("Fayl yuboring (.docx yoki .txt)!")
                return
            file=await ctx.bot.get_file(fayl.file_id)
            fayl_bytes=await file.download_as_bytearray()
            matn=""
            fname=fayl.file_name or ""
            if fname.endswith(".docx"):
                import io
                from docx import Document
                doc=Document(io.BytesIO(bytes(fayl_bytes)))
                matn="\n".join([p.text for p in doc.paragraphs])
            else:
                matn=bytes(fayl_bytes).decode("utf-8","ignore")
            res=await api_post("/savol/fayldan",{"fan":fan,"mavzu":mavzu,"matn":matn,"ustoz_id":uid})
            if res.get("success"):
                await update.message.reply_text(
                    "Savollar qoshildi!\n"
                    "Fan: "+fan+"\n"
                    "Mavzu: "+mavzu+"\n"
                    "Jami: "+str(res.get("qoshildi",0))+" ta savol"
                )
            else:
                await update.message.reply_text("Xato: "+str(res.get("detail","")))
        except Exception as e:
            await update.message.reply_text("Xato: "+str(e))
        ctx.user_data.pop("kutish",None)
        return

    if ctx.user_data.get("kutish")=="varaq_fayl":
        soni=ctx.user_data.get("varaq_soni","")
        try:
            fayl_id=update.message.document.file_id
            res=await api_post("/varaqlar/qosh",{"soni":soni,"fayl_id":fayl_id,"nomi":f"{soni} savollik varaq"})
            if res.get("success"):
                await update.message.reply_text(f"Varaq saqlandi!\n{soni} savollik varaq")
            else:
                await update.message.reply_text(f"Xato: {res.get('detail','')}")
        except Exception as e:
            await update.message.reply_text(f"Xato: {str(e)}")
        ctx.user_data.pop("kutish",None)
        return

    if ctx.user_data.get("kutish")!="kitob_fayl": return
    fan=ctx.user_data.get("kitob_fan","")
    nomi=ctx.user_data.get("kitob_nomi","")
    try:
        fayl_id=update.message.document.file_id
        res=await api_post("/kitob/qosh",{"fan":fan,"nomi":nomi,"fayl_id":fayl_id,"ustoz_id":uid})
        if res.get("success"):
            await update.message.reply_text(f"Kitob qoshildi!\n{nomi}\n{fan}")
        else:
            await update.message.reply_text(f"Xato: {res.get('detail','')}")
    except Exception as e:
        await update.message.reply_text(f"Xato: {str(e)}")
    ctx.user_data.pop("kutish",None)

async def matn_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    holat=ctx.user_data.get("kutish"); uid=update.effective_user.id; text=update.message.text.strip()

    if holat=="elon_sarlavha" and uid in ADMIN_IDS:
        ctx.user_data["elon_sarlavha"]=text
        ctx.user_data["kutish"]="elon_matn"
        await update.message.reply_text("E\'lon matnini yozing:")
        return

    if holat=="elon_matn" and uid in ADMIN_IDS:
        sarlavha=ctx.user_data.get("elon_sarlavha","")
        try:
            res=await api_post("/elon/qosh",{"sarlavha":sarlavha,"matn":text,"ustoz_id":uid})
            if res.get("success"):
                await update.message.reply_text("E\'lon qo\'shildi!\n\n📢 "+sarlavha+"\n\n"+text)
            else:
                await update.message.reply_text("Xato: "+str(res.get("detail","")))
        except Exception as e:
            await update.message.reply_text("Xato: "+str(e))
        ctx.user_data.pop("kutish",None)
        return

    if holat=="baza_fan" and uid in ADMIN_IDS:
        ctx.user_data["baza_fan"]=text
        ctx.user_data["kutish"]="baza_mavzu"
        await update.message.reply_text("MAVZU nomini yozing:")
        return

    if holat=="baza_mavzu" and uid in ADMIN_IDS:
        ctx.user_data["baza_mavzu"]=text
        ctx.user_data["kutish"]="baza_matn_yoki_fayl"
        await update.message.reply_text(
            "Endi savollarni yuboring:\n\n"
            "1️⃣ Word (.docx) fayl yuboring\n"
            "2️⃣ Yoki formatlangan matnni to'g'ridan yozing/nusxalang"
        )
        return

    if holat=="baza_matn_yoki_fayl" and uid in ADMIN_IDS:
        fan=ctx.user_data.get("baza_fan","")
        mavzu=ctx.user_data.get("baza_mavzu","")
        try:
            res=await api_post("/savol/fayldan",{"fan":fan,"mavzu":mavzu,"matn":text,"ustoz_id":uid})
            if res.get("success"):
                await update.message.reply_text(
                    "Savollar qoshildi!\n"
                    "Fan: "+fan+"\n"
                    "Mavzu: "+mavzu+"\n"
                    "Jami: "+str(res.get("qoshildi",0))+" ta savol"
                )
            else:
                await update.message.reply_text("Xato: "+str(res.get("detail","")))
        except Exception as e:
            await update.message.reply_text("Xato: "+str(e))
        ctx.user_data.pop("kutish",None)
        return

    if holat=="savol_fan" and uid in ADMIN_IDS:
        ctx.user_data["savol_fan"]=text
        ctx.user_data["kutish"]="savol_mavzu"
        await update.message.reply_text("Fan: "+text+"\n\nMavzuni yozing:")
    elif holat=="savol_mavzu" and uid in ADMIN_IDS:
        ctx.user_data["savol_mavzu"]=text
        ctx.user_data["kutish"]="savol_text"
        await update.message.reply_text("Mavzu: "+text+"\n\nSavol matnini yozing:")
    elif holat=="savol_text" and uid in ADMIN_IDS:
        ctx.user_data["savol_text"]=text
        ctx.user_data["kutish"]="savol_a"
        await update.message.reply_text("A variantini yozing:")
    elif holat=="savol_a" and uid in ADMIN_IDS:
        ctx.user_data["savol_a"]=text
        ctx.user_data["kutish"]="savol_b"
        await update.message.reply_text("B variantini yozing:")
    elif holat=="savol_b" and uid in ADMIN_IDS:
        ctx.user_data["savol_b"]=text
        ctx.user_data["kutish"]="savol_c"
        await update.message.reply_text("C variantini yozing:")
    elif holat=="savol_c" and uid in ADMIN_IDS:
        ctx.user_data["savol_c"]=text
        ctx.user_data["kutish"]="savol_d"
        await update.message.reply_text("D variantini yozing:")
    elif holat=="savol_d" and uid in ADMIN_IDS:
        ctx.user_data["savol_d"]=text
        ctx.user_data["kutish"]="savol_togri"
        await update.message.reply_text(
            "A: "+ctx.user_data["savol_a"]+"\nB: "+ctx.user_data["savol_b"]+
            "\nC: "+ctx.user_data["savol_c"]+"\nD: "+ctx.user_data["savol_d"]+
            "\n\nTogri javob (A/B/C/D):"
        )
    elif holat=="savol_togri" and uid in ADMIN_IDS:
        togri=text.strip().upper()
        if togri not in ["A","B","C","D"]:
            await update.message.reply_text("Faqat A,B,C,D!"); return
        ctx.user_data.pop("kutish",None)
        try:
            res=await api_post("/savol/qosh",{
                "fan":ctx.user_data.get("savol_fan",""),
                "mavzu":ctx.user_data.get("savol_mavzu",""),
                "savol":ctx.user_data.get("savol_text",""),
                "variantlar":{"A":ctx.user_data.get("savol_a",""),"B":ctx.user_data.get("savol_b",""),"C":ctx.user_data.get("savol_c",""),"D":ctx.user_data.get("savol_d","")},
                "togri_javob":togri,"qiyinlik":"orta","ustoz_id":uid
            })
            if res.get("success"):
                await update.message.reply_text("Savol qoshildi!\nFan: "+ctx.user_data.get("savol_fan","")+"\nTogri: "+togri)
            else:
                await update.message.reply_text("Xato: "+str(res.get("detail","")))
        except Exception as e:
            await update.message.reply_text("Xato: "+str(e))
        for k in ["savol_fan","savol_mavzu","savol_text","savol_a","savol_b","savol_c","savol_d"]:
            ctx.user_data.pop(k,None)

    elif holat=="kitob_fan" and uid in ADMIN_IDS:
        ctx.user_data["kitob_fan"]=text
        ctx.user_data["kutish"]="kitob_nomi"
        await update.message.reply_text("Fan: "+text+"\n\nKitob nomini yozing:")
    elif holat=="kitob_nomi" and uid in ADMIN_IDS:
        ctx.user_data["kitob_nomi"]=text
        ctx.user_data["kutish"]="kitob_fayl"
        await update.message.reply_text("Kitob: "+text+"\n\nPDF yoki rasm faylni yuboring!")

    elif holat=="test_fan" and uid in ADMIN_IDS:
        ctx.user_data["test_fan"]=text; ctx.user_data["kutish"]="test_kod_input"
        await update.message.reply_text("Fan: "+text+"\n\nTest kodini kiriting:")
    elif holat=="test_kod_input" and uid in ADMIN_IDS:
        kod = text.upper()
        ctx.user_data["test_kod"] = kod
        try:
            res = await api_get(f"/test/tekshir/{kod}")
            if res.get("topildi"):
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 Javoblarni nusxalash", callback_data=f"test_nusxa_{kod}")],
                    [InlineKeyboardButton("✍️ Yangi javoblar kiritish", callback_data="test_yangi_javob")],
                ])
                ctx.user_data["kutish"] = None
                await update.message.reply_text(kod+" kodi mavjud! Nima qilasiz?", reply_markup=kb)
                return
        except Exception:
            pass
        ctx.user_data["kutish"]="test_vaqt"
        await update.message.reply_text(
            "⏱️ Test vaqtini kiriting (daqiqada):\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Masalan: 90 (milliy), 60 (oddiy), 45 ..."
        )
    elif holat=="test_vaqt" and uid in ADMIN_IDS:
        try:
            vaqt = int(text.strip())
            if vaqt < 5 or vaqt > 300:
                await update.message.reply_text("Vaqt 5 dan 300 gacha bo'lishi kerak!"); return
        except ValueError:
            await update.message.reply_text("Faqat raqam kiriting! Masalan: 90"); return
        ctx.user_data["test_vaqt"] = vaqt
        ctx.user_data["kutish"] = "test_javoblar"
        ctx.user_data["javoblar"] = {}; ctx.user_data["savol"] = 1
        await update.message.reply_text(f"✅ Vaqt: {vaqt} daqiqa\n\nEndi javoblarni kiriting:")
        await savol_sora(update, ctx)

    elif holat=="test_javoblar" and uid in ADMIN_IDS:
        n=ctx.user_data.get("savol",1); javob=text.strip().upper()
        if n<=32 and javob not in ["A","B","C","D"]:
            await update.message.reply_text("Faqat A,B,C,D!"); return
        elif 33<=n<=35 and javob not in ["A","B","C","D","E","F"]:
            await update.message.reply_text("Faqat A,B,C,D,E,F!"); return
        ctx.user_data["javoblar"][str(n)]=javob; ctx.user_data["savol"]=n+1
        if n+1<=40: await savol_sora(update,ctx)
        else: await test_saqlash(update,ctx)

    elif holat=="natija_kod":
        ctx.user_data.pop("kutish",None)
        try:
            res=await api_get(f"/test/tekshir/{text.upper()}")
            if not res.get("topildi"):
                await update.message.reply_text("Test topilmadi!"); return
            if res.get("tugadi"):
                await update.message.reply_text("Test yakunlangan.")
            else:
                await update.message.reply_text("Test aktiv!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Testga kirish",
                        web_app=WebAppInfo(url=MINI_APP_URL+"?kod="+text.upper()))]]))
        except Exception as e:
            await update.message.reply_text("Xato: "+str(e))

    elif holat=="yakunla_kod" and uid in ADMIN_IDS:
        ctx.user_data.pop("kutish",None); kod=text.upper()
        await update.message.reply_text("Yakunlanmoqda...")
        try:
            res=await api_post("/test/yakunla",{"test_kod":kod,"ustoz_id":uid})
            if res.get("success"):
                natijalar=res["natijalar"]; togri_javoblar=res.get("togri_javoblar",{})
                maks_ball=res.get("maks_ball",75); n_savol=len(togri_javoblar)
                matn="Yakunlandi! Jami: "+str(res["jami"])+"\n\nTop 5:\n"
                for n in natijalar[:5]:
                    matn+=str(n["orin"])+". "+n["ism"]+" "+n["familiya"]+" — "+str(n["ball"])+" ball\n"
                await update.message.reply_text(matn)
                for n in natijalar:
                    try:
                        if n.get("user_id") and n["user_id"]!=0:
                            notogri=[]
                            for i in range(1,n_savol+1):
                                k=str(i); oj=n["javoblar"].get(k,"").strip().upper()
                                tj=togri_javoblar.get(k,"").strip().upper()
                                if oj!=tj and tj: notogri.append(str(i)+": "+str(oj or "?")+" → "+tj)
                            xabar=n["ism"]+" "+n["familiya"]+"!\n"
                            xabar+="Togri: "+str(n["togri_soni"])+"/"+str(n_savol)+"\n"
                            xabar+="Ball: "+str(n["ball"])+"/"+str(maks_ball)+"\n"
                            xabar+="Orin: "+str(n["orin"])+"/"+str(res["jami"])+"\n\n"
                            if notogri: xabar+="Notogri ("+str(len(notogri))+"):\n"+"\n".join(notogri[:15])
                            else: xabar+="Hammasi togri!"
                            await ctx.bot.send_message(chat_id=n["user_id"],text=xabar)
                    except Exception: pass
                async with httpx.AsyncClient() as c:
                    r=await c.get(f"{BACKEND_URL}/excel/{kod}",timeout=30)
                    if r.status_code==200:
                        await ctx.bot.send_document(chat_id=uid,document=r.content,
                            filename=f"natija_{kod}.xlsx",caption="Natijalar — "+kod)
            else:
                await update.message.reply_text("Xato: "+str(res.get("detail","")))
        except Exception as e:
            await update.message.reply_text("Xato: "+str(e))

    elif holat=="skaner_kod" and uid in ADMIN_IDS:
        ctx.user_data["skaner_test_kod"]=text.upper(); ctx.user_data["kutish"]="skaner_rasm"
        await update.message.reply_text("Test kodi: "+text.upper()+"\n\nVaraq rasmini yuboring!")

    elif holat=="skaner_id_qolda" and uid in ADMIN_IDS:
        varaq_id=text.strip().zfill(3)
        javoblar=ctx.user_data.get("skaner_javoblar",{})
        test_kod=ctx.user_data.get("skaner_test_kod","")
        n_savol=ctx.user_data.get("skaner_n_savol",35)
        try:
            res=await api_get(f"/student/id/{test_kod}/{varaq_id}")
            if res.get("success"):
                oquvchi=res["oquvchi"]
                await update.message.reply_text("Topildi: "+oquvchi["ism"]+" "+oquvchi["familiya"])
                if n_savol==40:
                    ctx.user_data["skaner_varaq_id"]=varaq_id
                    ctx.user_data["kutish"]="skaner_ochiq_36"
                    await update.message.reply_text("36-savol javobini yozing:")
                    return
                res2=await api_post("/natija/skaner",{"test_kod":test_kod,"varaq_id":varaq_id,"javoblar":javoblar})
                if res2.get("success"): await update.message.reply_text("Saqlandi!")
                else: await update.message.reply_text("Xato: "+str(res2.get("detail","")))
            else:
                await update.message.reply_text("ID "+varaq_id+" topilmadi!")
        except Exception as e:
            await update.message.reply_text("Xato: "+str(e))
        ctx.user_data.pop("kutish",None)

    elif holat and holat.startswith("skaner_ochiq_") and uid in ADMIN_IDS:
        savol_n=int(holat.split("_")[-1])
        ctx.user_data["skaner_javoblar"][str(savol_n)]=text.strip()
        if savol_n<40:
            ctx.user_data["kutish"]=f"skaner_ochiq_{savol_n+1}"
            await update.message.reply_text(str(savol_n+1)+"-savol javobini yozing:")
        else:
            javoblar=ctx.user_data["skaner_javoblar"]
            varaq_id=ctx.user_data.get("skaner_varaq_id","")
            test_kod=ctx.user_data.get("skaner_test_kod","")
            try:
                res=await api_post("/natija/skaner",{"test_kod":test_kod,"varaq_id":varaq_id,"javoblar":javoblar})
                if res.get("success"):
                    o=res["oquvchi"]
                    await update.message.reply_text(o["ism"]+" "+o["familiya"]+" saqlandi!")
                else:
                    await update.message.reply_text("Xato: "+str(res.get("detail","")))
            except Exception as e:
                await update.message.reply_text("Xato: "+str(e))
            ctx.user_data.pop("kutish",None)

async def savol_sora(update,ctx):
    n=ctx.user_data.get("savol",1)
    if n<=32: v="A/B/C/D"
    elif n<=35: v="A/B/C/D/E/F"
    else: v="Javob yozing"
    await update.message.reply_text(str(n)+"-savol: "+v+"\nJarayon: "+str(len(ctx.user_data.get("javoblar",{})))+"/40")

async def savol_sora_q(ctx,uid):
    n=ctx.user_data.get("savol",1)
    if n<=32: v="A/B/C/D"
    elif n<=35: v="A/B/C/D/E/F"
    else: v="Javob yozing"
    await ctx.bot.send_message(chat_id=uid,text=str(n)+"-savol: "+v+"\nJarayon: "+str(len(ctx.user_data.get("javoblar",{})))+"/40")

async def test_saqlash(update,ctx):
    uid=update.effective_user.id
    try:
        vaqt = ctx.user_data.get("test_vaqt", 90)
        res=await api_post("/test/yarat",{"kod":ctx.user_data["test_kod"],"fan":ctx.user_data.get("test_fan",""),"ustoz_id":uid,"javoblar":ctx.user_data["javoblar"],"tur":ctx.user_data.get("test_tur","milliy"),"savollar_soni":ctx.user_data.get("test_soni",40),"vaqt":vaqt})
        if res.get("success"):
            await update.message.reply_text("Test yaratildi!\nKod: "+ctx.user_data["test_kod"]+"\n⏱️ Vaqt: "+str(vaqt)+" daqiqa")
        else:
            await update.message.reply_text("Xato: "+str(res.get("detail","")))
    except Exception as e:
        await update.message.reply_text("Xato: "+str(e))
    for k in ["test_fan","test_kod","javoblar","savol","kutish","test_vaqt"]:
        ctx.user_data.pop(k,None)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args): pass

def health_server():
    port=int(os.environ.get("PORT",8080))
    HTTPServer(("0.0.0.0",port),HealthHandler).serve_forever()

def main():
    threading.Thread(target=health_server,daemon=True).start()
    log.info("Health server ishga tushdi ✅")
    app=ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CallbackQueryHandler(tugma))
    app.add_handler(MessageHandler(filters.PHOTO,rasm_handler))
    app.add_handler(MessageHandler(filters.Document.ALL,fayl_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,matn_handler))
    log.info("Bot ishga tushdi ✅")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__":
    main()
