import os
import asyncio
import requests
from datetime import datetime
import pytz
from telethon import TelegramClient, events, Button
import heroku3

# ======================== متغيرات البيئة ========================
BOT_TOKEN = os.environ.get("TOKEN", "")
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "")
DEVELOPER_ID = int(os.environ.get("DEVELOPER_ID", "6373993992"))
HEROKU_API_KEY = os.environ.get("HEROKU_API_KEY", "")
HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME", "")

# حالة تشغيل الاسم الوقتي
AUTO_RENAME_ENABLED = os.environ.get("AUTO_RENAME_ENABLED", "true").lower() == "true"

# نمط الأرقام (افتراضي: عريض 𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵)
DIGIT_MAP_STR = os.environ.get("DIGIT_MAP", "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵")
if len(DIGIT_MAP_STR) != 10:
    DIGIT_MAP_STR = "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
DIGIT_MAP = {str(i): DIGIT_MAP_STR[i] for i in range(10)}

# التحقق من البيانات الأساسية
if not BOT_TOKEN:
    raise ValueError("❌ TOKEN must be set")
if not API_ID or not API_HASH:
    raise ValueError("❌ API_ID and API_HASH must be set (get them from my.telegram.org)")
if not CHANNEL_USERNAME:
    raise ValueError("❌ CHANNEL_USERNAME must be set")

# ======================== إعدادات ثابتة ========================
TIMEZONE = pytz.timezone('Asia/Baghdad')

# ======================== إنشاء عميل البوت ========================
bot = TelegramClient('bot_session', API_ID, API_HASH)

# ======================== دوال مساعدة ========================
def convert_digits(number_str):
    return ''.join(DIGIT_MAP.get(ch, ch) for ch in number_str)

def get_formatted_time():
    now = datetime.now(TIMEZONE)
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
    styled_time = convert_digits(time_str)
    
    return f"𓏺 {styled_time} . {period}َ"

# ======================== تحديث متغيرات البيئة وإعادة التشغيل ========================
def update_config_and_restart(key, value):
    if not HEROKU_API_KEY or not HEROKU_APP_NAME:
        return False
    try:
        heroku = heroku3.from_key(HEROKU_API_KEY)
        app = heroku.apps()[HEROKU_APP_NAME]
        app.update_config({key: value})
        app.restart()
        return True
    except Exception as e:
        print(f"⚠️ فشل تحديث {key}: {e}")
        return False

# ======================== حذف آخر رسالة في القناة ========================
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

# ======================== تغيير اسم القناة (مع حذف آخر رسالة) ========================
async def rename_channel():
    global AUTO_RENAME_ENABLED
    if not AUTO_RENAME_ENABLED:
        return
    
    new_name = get_formatted_time()
    print(f"[{datetime.now(TIMEZONE).strftime('%H:%M:%S')}] تغيير الاسم إلى: {new_name}")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setChatTitle"
    data = {"chat_id": CHANNEL_USERNAME, "title": new_name}
    
    try:
        response = requests.post(url, data=data)
        result = response.json()
        if result.get("ok"):
            print("✅ تم تغيير الاسم")
            await asyncio.sleep(2)  # انتظار لظهور رسالة النظام
            await delete_last_message()
        else:
            print(f"❌ فشل تغيير الاسم: {result.get('description')}")
    except Exception as e:
        print(f"⚠️ خطأ في تغيير الاسم: {e}")

# ======================== دوال إنشاء النصوص والأزرار ========================
def get_main_menu_text():
    return "🔧 **لوحة تحكم البوت**\nاختر ما تريد:"

def get_main_menu_buttons():
    return [
        [Button.inline("📛 الاسم الوقتي", data="rename_menu")],
        [Button.inline("🔢 تغيير نمط الأرقام", data="change_font")],
        [Button.inline("📊 الحالة العامة", data="status")]
    ]

def get_rename_menu_text():
    status = "✅ مفعل" if AUTO_RENAME_ENABLED else "⏸️ معطل"
    return f"📛 **الاسم الوقتي**\nالحالة: {status}\nاختر إجراء:"

def get_rename_menu_buttons():
    return [
        [Button.inline("✅ تشغيل" if not AUTO_RENAME_ENABLED else "⏸️ إيقاف", data="rename_toggle")],
        [Button.inline("🔙 رجوع للقائمة الرئيسية", data="back_main")]
    ]

def get_font_change_text():
    return (
        "🔤 **تغيير نمط الأرقام**\n"
        "أرسل سلسلة من 10 أحرف تمثل الأرقام من 0 إلى 9 بالترتيب.\n"
        "مثال للخط العريض: `𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵`\n"
        "مثال للأرقام العادية: `0123456789`\n\n"
        "سيتم حفظ النمط وإعادة تشغيل البوت."
    )

def get_status_text():
    return (
        f"📊 **الحالة العامة**\n"
        f"الاسم الوقتي: {'✅ مفعل' if AUTO_RENAME_ENABLED else '⏸️ معطل'}\n"
        f"نمط الأرقام الحالي: `{DIGIT_MAP_STR}`"
    )

def get_status_buttons():
    return [[Button.inline("🔙 رجوع", data="back_main")]]

# ======================== بوت التحكم (الخاص بالمطور) ========================
@bot.on(events.NewMessage(pattern='/start', func=lambda e: e.is_private))
async def start_handler(event):
    if event.sender_id != DEVELOPER_ID:
        await event.reply("⚠️ هذا البوت خاص بالمطور فقط.")
        return
    
    await event.reply(
        get_main_menu_text(),
        buttons=get_main_menu_buttons()
    )

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    if event.sender_id != DEVELOPER_ID:
        await event.answer("غير مصرح", alert=True)
        return
    
    data = event.data.decode()
    
    if data == "rename_menu":
        await event.edit(
            get_rename_menu_text(),
            buttons=get_rename_menu_buttons()
        )
    
    elif data == "rename_toggle":
        new_state = not AUTO_RENAME_ENABLED
        if HEROKU_API_KEY and HEROKU_APP_NAME:
            heroku = heroku3.from_key(HEROKU_API_KEY)
            app = heroku.apps()[HEROKU_APP_NAME]
            app.update_config({"AUTO_RENAME_ENABLED": str(new_state).lower()})
        globals()['AUTO_RENAME_ENABLED'] = new_state
        await event.answer(f"تم {'تفعيل' if new_state else 'إيقاف'} الاسم الوقتي", alert=True)
        await event.edit(
            get_main_menu_text(),
            buttons=get_main_menu_buttons()
        )
    
    elif data == "change_font":
        await event.edit(get_font_change_text())
        async with bot.conversation(DEVELOPER_ID) as conv:
            response = await conv.get_response()
            new_map = response.text.strip()
            if len(new_map) != 10:
                await response.reply("❌ يجب أن يكون الطول 10 أحرف بالضبط.")
                await event.edit(
                    get_main_menu_text(),
                    buttons=get_main_menu_buttons()
                )
                return
            if update_config_and_restart("DIGIT_MAP", new_map):
                await response.reply("✅ تم تحديث نمط الأرقام وإعادة تشغيل البوت. سيتم تفعيل التغيير بعد لحظات.")
            else:
                await response.reply("⚠️ فشل تحديث النمط (Heroku API غير مضبوط).")
    
    elif data == "status":
        await event.edit(
            get_status_text(),
            buttons=get_status_buttons()
        )
    
    elif data == "back_main":
        await event.edit(
            get_main_menu_text(),
            buttons=get_main_menu_buttons()
        )

# ======================== حلقة تغيير الاسم ========================
async def rename_loop():
    while True:
        await rename_channel()
        await asyncio.sleep(60)

# ======================== التشغيل الرئيسي ========================
async def main():
    await bot.start(bot_token=BOT_TOKEN)
    
    print("="*60)
    print("🚀 بوت تغيير اسم القناة التلقائي")
    print("="*60)
    print(f"📢 القناة: {CHANNEL_USERNAME}")
    print(f"🤖 المطور: {DEVELOPER_ID}")
    print(f"📛 الاسم: {'مفعل' if AUTO_RENAME_ENABLED else 'معطل'}")
    print(f"🔤 نمط الأرقام: {DIGIT_MAP_STR}")
    print("="*60)
    
    await asyncio.gather(
        rename_loop(),
        bot.run_until_disconnected()
    )

if __name__ == "__main__":
    asyncio.run(main())
