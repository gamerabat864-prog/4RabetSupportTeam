import os
import logging
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Logging configuration setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6442666467"))
WEBSITE_URL = "https://4rabetgame.netlify.app/"

# ==================== DATABASE SETUP (SQLite) ====================
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            username TEXT,
            language TEXT DEFAULT 'en',
            first_seen TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def register_user_if_new(user_id: int, full_name: str, username: str) -> bool:
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()
    
    is_new = False
    if not exists:
        cursor.execute(
            "INSERT INTO users (user_id, full_name, username, first_seen) VALUES (?, ?, ?, ?)",
            (user_id, full_name, username, datetime.now())
        )
        conn.commit()
        is_new = True
        
    conn.close()
    return is_new

def get_user_lang(user_id: int) -> str:
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "en"

def set_user_lang(user_id: int, lang: str):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()

def get_total_users_count() -> int:
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_all_user_ids() -> list:
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

# ==================== TEXTS & TRANSLATIONS ====================
TEXTS = {
    "en": {
        "welcome": (
            "<b>Welcome to 4Rabet Support Assistance!</b>\n\n"
            "We are here to help guide you through common account, deposit, "
            "withdrawal, and verification inquiries.\n\n"
            "<i>Disclaimer: This is an independent assistance guide. "
            f"You can access the portal via our <a href='{WEBSITE_URL}'>website link (user-provided and unverified)</a>.</i>\n\n"
            "Please select a support category below:"
        ),
        "btn_email": "📧 Email Confirmation Problem",
        "btn_withdrawal": "💸 Withdrawal Problem",
        "btn_deposit": "💳 Deposit Problem",
        "btn_kyc": "🛡️ KYC Problem",
        "btn_other": "❓ Other Problem",
        "btn_back": "🔙 Back to Main Menu",
        "btn_lang": "🌐 Change Language",
        "solution_msg": (
            "<b>⚠️ Official Support Guideline:</b>\n\n"
            "To resolve this issue instantly, please log in using the <b>4Rabet Old Version</b>.\n\n"
            "Once you log in through the old version, your problem will be automatically solved within **5 to 10 minutes**.\n\n"
            f"🔗 Access Portal: <a href='{WEBSITE_URL}'>Click Here to Open Website</a>"
        )
    },
    "hi": {
        "welcome": (
            "<b>4Rabet Support Assistance mein aapka swagat hai!</b>\n\n"
            "Hum yahan aapki account, deposit, withdrawal, aur verification samasyaon mein sahayata ke liye hain.\n\n"
            "<i>Disclaimer: Yeh ek independent support guide hai. "
            f"Aap portal ko hamare <a href='{WEBSITE_URL}'>website link (user-provided and unverified)</a> ke zariye access kar sakte hain.</i>\n\n"
            "Kripya niche diye gaye support category ko chunein:"
        ),
        "btn_email": "📧 Email Confirmation Samasya",
        "btn_withdrawal": "💸 Withdrawal Samasya",
        "btn_deposit": "💳 Deposit Samasya",
        "btn_kyc": "🛡️ KYC Samasya",
        "btn_other": "❓ Anya Samasya",
        "btn_back": "🔙 Main Menu Par Wapas",
        "btn_lang": "🌐 Bhasha Badlein (Change Language)",
        "solution_msg": (
            "<b>⚠️ Zaroori Sujhav (Official Support Guideline):</b>\n\n"
            "Apni is samasya ko turant hal karne ke liye, kripya <b>4Rabet ke Old Version</b> se login karein.\n\n"
            "Old version se login karne ke baad, aapki problem **5 se 10 minute ke andar** thik ho jayegi.\n\n"
            f"🔗 Portal Link: <a href='{WEBSITE_URL}'>Yahan Click Karke Website Kholein</a>"
        )
    }
}

def get_main_keyboard(lang: str) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    keyboard = [
        [InlineKeyboardButton(t["btn_email"], callback_data="cat_issue")],
        [InlineKeyboardButton(t["btn_withdrawal"], callback_data="cat_issue")],
        [InlineKeyboardButton(t["btn_deposit"], callback_data="cat_issue")],
        [InlineKeyboardButton(t["btn_kyc"], callback_data="cat_issue")],
        [InlineKeyboardButton(t["btn_other"], callback_data="cat_issue")],
        [
            InlineKeyboardButton(t["btn_lang"], callback_data="action_lang"),
            InlineKeyboardButton("🌐 Website", url=WEBSITE_URL)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_sub_keyboard(lang: str) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    keyboard = [
        [InlineKeyboardButton(t["btn_back"], callback_data="action_back")],
        [InlineKeyboardButton(t["btn_lang"], callback_data="action_lang")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = user.id
    username_str = f"@{user.username}" if user.username else "Not Available"
    
    is_new = register_user_if_new(chat_id, user.full_name, username_str)
    
    if is_new:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        admin_message = (
            "🚨 <b>New User Started Bot!</b>\n\n"
            f"👤 <b>Name:</b> {user.full_name}\n"
            f"🔗 <b>Username:</b> {username_str}\n"
            f"🆔 <b>User ID:</b> <code>{chat_id}</code>\n"
            f"⏰ <b>Time:</b> {current_time}"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Admin notification failed: {e}")

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()

    lang = get_user_lang(chat_id)

    if not row or row[0] is None:
        lang_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
                InlineKeyboardButton("🇮🇳 Hindi", callback_data="set_lang_hi")
            ]
        ])
        await update.message.reply_text(
            "<b>Please choose your preferred language / अपनी भाषा चुनें:</b>",
            reply_markup=lang_markup,
            parse_mode="HTML"
        )
        return

    await update.message.reply_text(
        TEXTS[lang]["welcome"],
        reply_markup=get_main_keyboard(lang),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    lang = get_user_lang(user_id)
    
    if data == "set_lang_en":
        set_user_lang(user_id, "en")
        await query.edit_message_text(
            TEXTS["en"]["welcome"],
            reply_markup=get_main_keyboard("en"),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        return
        
    elif data == "set_lang_hi":
        set_user_lang(user_id, "hi")
        await query.edit_message_text(
            TEXTS["hi"]["welcome"],
            reply_markup=get_main_keyboard("hi"),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        return
        
    elif data == "action_lang":
        lang_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
                InlineKeyboardButton("🇮🇳 Hindi", callback_data="set_lang_hi")
            ],
            [InlineKeyboardButton(TEXTS[lang]["btn_back"], callback_data="action_back")]
        ])
        await query.edit_message_text(
            "<b>Select your language / अपनी भाषा चुनें:</b>",
            reply_markup=lang_markup,
            parse_mode="HTML"
        )
        return
        
    elif data == "action_back":
        await query.edit_message_text(
            TEXTS[lang]["welcome"],
            reply_markup=get_main_keyboard(lang),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        return

    elif data == "cat_issue":
        solution_text = TEXTS[lang]["solution_msg"]
        await query.edit_message_text(
            solution_text,
            reply_markup=get_sub_keyboard(lang),
            parse_mode="HTML",
            disable_web_page_preview=True
        )

# ==================== ADMIN COMMANDS ====================
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    
    total_users = get_total_users_count()
    await update.message.reply_text(
        f"📊 <b>Bot Statistics:</b>\n\n"
        f"👥 Total Registered Users: <b>{total_users}</b>",
        parse_mode="HTML"
    )

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /broadcast Your message here")
        return
        
    broadcast_text = " ".join(context.args)
    user_ids = get_all_user_ids()
    
    success_count = 0
    fail_count = 0
    
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=broadcast_text, parse_mode="HTML")
            success_count += 1
        except Exception:
            fail_count += 1

    await update.message.reply_text(
        f"📢 <b>Broadcast Completed!</b>\n\n"
        f"✅ Success: {success_count}\n"
        f"❌ Failed: {fail_count}",
        parse_mode="HTML"
    )

# ==================== MAIN APPLICATION ====================
def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing!")
        return

    init_db()

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Pro Bot is starting polling with SQLite database...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
  
