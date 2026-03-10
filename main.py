import os
import asyncio
import time
from datetime import datetime
import pytz
import requests
from telethon import TelegramClient, events, Button
from telethon.tl.types import User
import heroku3

# ======================== متغيرات البيئة ========================
BOT_TOKEN = os.environ.get("TOKEN", "")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "")
TIMEZONE_STR = os.environ.get("TIMEZONE", "Asia/Baghdad")
DEVELOPER_ID = int(os.environ.get("DEVELOPER_ID", "6373993992"))
HEROKU_API_KEY = os.environ.get("HEROKU_API_KEY", "")
HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME", "")

# حالات التشغيل
AUTO_RENAME_ENABLED = os.environ.get("AUTO_RENAME_ENABLED", "true").lower() == "true"
AUTO_BIO_ENABLED = os.environ.get("AUTO_BIO_ENABLED", "false").lower() == "true"
DIGIT_STYLE = int(os.environ.get("DIGIT_STYLE", "3"))  # 1: عادي، 2: عريض 𝟷𝟸𝟹، 3: عريض 𝟬𝟭𝟮
CUSTOM_BIO = os.environ.get("CUSTOM_BIO", f"المطور @BD_0I")

# ======================== تعريفات الأرقام ========================
DIGIT_STYLES = {
    1: {'0':'0','1':'1','2':'2','3':'3','4':'4','5':'5','6':'6','7':'7','8':'8','9':'9'},
    2: {'0':'𝟶','1':'𝟷','2':'𝟸','3':'𝟹','4':'𝟺','5':'𝟻','6':'𝟼','7':'𝟽','8':'𝟾','9':'𝟿'},
    3: {'0':'𝟬','1':'𝟭','2':'𝟮','3':'𝟯','4':'𝟰','5':'𝟱','6':'𝟲','7':'𝟳','8':'𝟴','9':'𝟵'}
}

# ======================== إنشاء عميل البوت ========================
bot = TelegramClient('bot_session', api_id=None, api_hash=None).start(bot_token=BOT_TOKEN)

# ======================== دوال مساعدة ========================
def convert_digits(number_str, style):
    digit_map = DIGIT_STYLES.get(style, DIGIT_STYLES[3])
    return ''.join(digit_map.get(ch, ch) for ch in number_str)

def get_formatted_time():
    now = datetime.now(pytz.timezone(TIMEZONE_STR))
    hour = now.hour
    minute = now.minute
    
    # تحويل إلى 12 ساعة
    if hour == 0:
        hour_12 = 12
        period = "ص"
    elif hour == 12:
        hour_12 = 12
        period = "م"
    elif hour > 12:
        hour_12 = hour - 12
        period = "م"
    else:
        hour_12 = hour
        period = "ص"
    
    time_str = f"{hour_12:02d}:{minute:02d}"
    styled_time = convert_digits(time_str, DIGIT_STYLE)
    
    return f"مَ {styled_time} {period}َ"

def get_formatted_bio():
    now = datetime.now(pytz.timezone(TIMEZONE_STR))
    hour = now.hour
    minute = now.minute
    
    if hour == 0:
        hour_12 = 12
        period = "ص"
    elif hour == 12:
        hour_12 = 12
        period = "م"
    elif hour > 12:
        hour_12 = hour - 12
        period = "م"
    else:
        hour_12 = hour
        period = "ص"
    
    time_str = f"{hour_12:02d}:{minute:02d}"
    styled_time = convert_digits(time_str, DIGIT_STYLE)
    
    return f"{CUSTOM_BIO} {styled_time} {period}"

# ======================== تحديث متغيرات البيئة ========================
def update_config_var(key, value):
    if not HEROKU_API_KEY or not HEROKU_APP_NAME:
        return False
    try:
        heroku = heroku3.from_key(HEROKU_API_KEY)
        app = heroku.apps()[HEROKU_APP_NAME]
        app.update_config({key: str(value)})
        return True
    except Exception as e:
        print(f"⚠️ فشل تحديث {key}: {e}")
        return False

# ======================== دوال حذف آخر رسالة ========================
async def delete_last_message():
    try:
        get_updates_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {
            "chat_id": CHANNEL_USERNAME,
            "limit": 10,
            "allowed_updates": ["channel_post"]
        }
        
        response = requests.get(get_updates_url, params=params)
        updates = response.json()
        
        if updates.get("ok") and updates.get("result"):
            for update in reversed(updates["result"]):
                if "channel_post" in update:
                    message_id = update["channel_post"]["message_id"]
                    delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
                    delete_data = {
                        "chat_id": CHANNEL_USERNAME,
                        "message_id": message_id
                    }
                    delete_response = requests.post(delete_url, json=delete_data)
                    if delete_response.json().get("ok"):
                        return True
        return False
    except:
        return False

# ======================== تغيير اسم القناة ========================
async def rename_channel():
    global AUTO_RENAME_ENABLED
    if not AUTO_RENAME_ENABLED:
        return
    
    new_name = get_formatted_time()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] تغيير الاسم إلى: {new_name}")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setChatTitle"
    data = {"chat_id": CHANNEL_USERNAME, "title": new_name}
    
    try:
        response = requests.post(url, data=data)
        result = response.json()
        if result.get("ok"):
            print("✅ تم تغيير الاسم")
            await asyncio.sleep(2)
            await delete_last_message()
        else:
            print(f"❌ فشل تغيير الاسم: {result.get('description')}")
    except Exception as e:
        print(f"⚠️ خطأ في تغيير الاسم: {e}")

# ======================== تغيير البايو ========================
async def update_bio():
    global AUTO_BIO_ENABLED
    if not AUTO_BIO_ENABLED:
        return
    
    new_bio = get_formatted_bio()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] تحديث البايو إلى: {new_bio}")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setChatDescription"
    data = {"chat_id": CHANNEL_USERNAME, "description": new_bio}
    
    try:
        response = requests.post(url, data=data)
        result = response.json()
        if result.get("ok"):
            print("✅ تم تحديث البايو")
        else:
            print(f"❌ فشل تحديث البايو: {result.get('description')}")
    except Exception as e:
        print(f"⚠️ خطأ في تحديث البايو: {e}")

# ======================== بوت التحكم (الخاص بالمطور) ========================
@bot.on(events.NewMessage(pattern='/start', func=lambda e: e.is_private))
async def start_handler(event):
    if event.sender_id != DEVELOPER_ID:
        await event.reply("⚠️ هذا البوت خاص بالمطور فقط.")
        return
    
    buttons = [
        [Button.inline("📛 الاسم الوقتي", data="rename_menu")],
        [Button.inline("📝 البايو الوقتي", data="bio_menu")],
        [Button.inline("🔢 تغيير نمط الأرقام", data="change_style")],
        [Button.inline("📊 الحالة العامة", data="status")]
    ]
    await event.reply("🔧 **لوحة تحكم البوت الرئيسية**\nاختر ما تريد:", buttons=buttons)

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    if event.sender_id != DEVELOPER_ID:
        await event.answer("غير مصرح", alert=True)
        return
    
    data = event.data.decode()
    
    # ===== قائمة الاسم الوقتي =====
    if data == "rename_menu":
        status = "✅ مفعل" if AUTO_RENAME_ENABLED else "⏸️ معطل"
        buttons = [
            [Button.inline("✅ تشغيل" if not AUTO_RENAME_ENABLED else "⏸️ إيقاف", data="rename_toggle")],
            [Button.inline("🔙 رجوع للقائمة الرئيسية", data="back_main")]
        ]
        await event.edit(f"📛 **الاسم الوقتي**\nالحالة: {status}\nاختر إجراء:", buttons=buttons)
    
    elif data == "rename_toggle":
        new_state = not AUTO_RENAME_ENABLED
        update_config_var("AUTO_RENAME_ENABLED", str(new_state).lower())
        globals()['AUTO_RENAME_ENABLED'] = new_state
        await event.answer(f"تم {'تفعيل' if new_state else 'إيقاف'} الاسم الوقتي", alert=True)
        await start_handler(event)  # العودة للقائمة الرئيسية
    
    # ===== قائمة البايو الوقتي =====
    elif data == "bio_menu":
        status = "✅ مفعل" if AUTO_BIO_ENABLED else "⏸️ معطل"
        buttons = [
            [Button.inline("✅ تشغيل" if not AUTO_BIO_ENABLED else "⏸️ إيقاف", data="bio_toggle")],
            [Button.inline("✏️ تعيين نص البايو", data="set_bio")],
            [Button.inline("🔙 رجوع للقائمة الرئيسية", data="back_main")]
        ]
        await event.edit(f"📝 **البايو الوقتي**\nالحالة: {status}\nالنص الحالي: `{CUSTOM_BIO}`\nاختر إجراء:", buttons=buttons)
    
    elif data == "bio_toggle":
        new_state = not AUTO_BIO_ENABLED
        update_config_var("AUTO_BIO_ENABLED", str(new_state).lower())
        globals()['AUTO_BIO_ENABLED'] = new_state
        await event.answer(f"تم {'تفعيل' if new_state else 'إيقاف'} البايو الوقتي", alert=True)
        await start_handler(event)
    
    elif data == "set_bio":
        async with bot.conversation(DEVELOPER_ID) as conv:
            await event.edit("📝 أرسل الآن النص الجديد للبايو (سيتم إضافة الوقت تلقائياً):")
            response = await conv.get_response()
            new_bio = response.text
            update_config_var("CUSTOM_BIO", new_bio)
            globals()['CUSTOM_BIO'] = new_bio
            await response.reply("✅ تم تعيين نص البايو بنجاح!")
        await start_handler(event)
    
    # ===== قائمة تغيير نمط الأرقام =====
    elif data == "change_style":
        style_names = {1: "عادي (123)", 2: "عريض (𝟷𝟸𝟹)", 3: "عريض (𝟬𝟭𝟮)"}
        buttons = [
            [Button.inline(f"{style_names[1]}", data="style_1")],
            [Button.inline(f"{style_names[2]}", data="style_2")],
            [Button.inline(f"{style_names[3]}", data="style_3")],
            [Button.inline("🔙 رجوع", data="back_main")]
        ]
        await event.edit("🔢 اختر نمط الأرقام:", buttons=buttons)
    
    elif data.startswith("style_"):
        new_style = int(data.split("_")[1])
        update_config_var("DIGIT_STYLE", str(new_style))
        globals()['DIGIT_STYLE'] = new_style
        await event.answer(f"تم تغيير النمط إلى {new_style}", alert=True)
        await start_handler(event)
    
    # ===== عرض الحالة =====
    elif data == "status":
        style_names = {1: "عادي", 2: "عريض 𝟷𝟸𝟹", 3: "عريض 𝟬𝟭𝟮"}
        status_text = (
            f"📊 **الحالة العامة**\n"
            f"الاسم الوقتي: {'✅ مفعل' if AUTO_RENAME_ENABLED else '⏸️ معطل'}\n"
            f"البايو الوقتي: {'✅ مفعل' if AUTO_BIO_ENABLED else '⏸️ معطل'}\n"
            f"نمط الأرقام: {style_names[DIGIT_STYLE]}\n"
            f"نص البايو: `{CUSTOM_BIO}`"
        )
        buttons = [[Button.inline("🔙 رجوع", data="back_main")]]
        await event.edit(status_text, buttons=buttons)
    
    # ===== العودة للقائمة الرئيسية =====
    elif data == "back_main":
        await start_handler(event)

# ======================== الحلقات المتوازية ========================
async def rename_loop():
    while True:
        await rename_channel()
        await asyncio.sleep(60)

async def bio_loop():
    while True:
        await update_bio()
        await asyncio.sleep(60)

# ======================== التشغيل الرئيسي ========================
async def main():
    print("="*60)
    print("🚀 بوت التحكم المتكامل بالقناة")
    print("="*60)
    print(f"📢 القناة: {CHANNEL_USERNAME}")
    print(f"🤖 المطور: {DEVELOPER_ID}")
    print(f"🔢 نمط الأرقام: {DIGIT_STYLE}")
    print(f"📛 الاسم: {'مفعل' if AUTO_RENAME_ENABLED else 'معطل'}")
    print(f"📝 البايو: {'مفعل' if AUTO_BIO_ENABLED else 'معطل'}")
    print("="*60)
    
    # تشغيل جميع الحلقات والبوت معاً
    await asyncio.gather(
        rename_loop(),
        bio_loop(),
        bot.run_until_disconnected()
    )

if __name__ == "__main__":
    asyncio.run(main())
