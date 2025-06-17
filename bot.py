import json
import os
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# .env dan o‘qish
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CREATOR_ID = int(os.getenv("CREATOR_ID"))

DATA_FILE = "data.json"

# JSON bilan ishlash
def load_data():
    if not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size == 0:
        with open(DATA_FILE, "w") as f:
            json.dump({"films": {}}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == CREATOR_ID:
        buttons = [
            [InlineKeyboardButton("🛠 Admin", callback_data="admin_panel")],
            [InlineKeyboardButton("📋 List", callback_data="list_codes")]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("Tanlang:", reply_markup=keyboard)
    else:
        await update.message.reply_text("Iltimos, kino kodini kiriting:")

# Inline tugmalar
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()

    if query.data == "admin_panel":
        if user_id == CREATOR_ID:
            context.user_data["admin_step"] = "await_code"
            await query.message.reply_text("🎬 Iltimos, yangi kino kodini kiriting:")
    elif query.data == "list_codes":
        if user_id == CREATOR_ID:
            codes = "\n".join(data["films"].keys()) or "Hozircha hech qanday kod mavjud emas."
            await query.message.reply_text(f"📋 Mavjud kodlar:\n{codes}")
        else:
            await query.message.reply_text("❌ Sizga bu buyruq ruxsat etilmagan.")

# Matnli xabarlarni qabul qilish
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip().upper()
    data = load_data()

    # Admin uchun
    if user_id == CREATOR_ID:
        step = context.user_data.get("admin_step")
        if step == "await_code":
            context.user_data["film_code"] = text
            context.user_data["admin_step"] = "await_ids"
            await update.message.reply_text("📩 Endi kino xabar IDlarini yuboring (masalan: 123,124):")
            return
        elif step == "await_ids":
            film_code = context.user_data.get("film_code")
            try:
                ids = [int(x.strip()) for x in text.split(",")]
                data["films"].setdefault(film_code, []).extend(ids)
                data["films"][film_code] = list(set(data["films"][film_code]))  # dublikatlarni olib tashlash
                save_data(data)
                await update.message.reply_text(f"✅ {film_code} kodi uchun {len(ids)} ta xabar saqlandi.")
            except:
                await update.message.reply_text("❌ Faqat sonlardan iborat, vergul bilan ajratilgan ID yuboring.")
            context.user_data.clear()
            return

    # Foydalanuvchi uchun
    if text in data["films"]:
        for msg_id in data["films"][text]:
            try:
                await context.bot.copy_message(
                    chat_id=update.effective_chat.id,
                    from_chat_id=CHANNEL_ID,
                    message_id=msg_id
                )
            except Exception:
                await update.message.reply_text("⚠️ Kino xabarini jo‘natib bo‘lmadi.")
    else:
        await update.message.reply_text("🛑 Bu kodga mos kino topilmadi.")

# Flask keep-alive (Render uchun)
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot tirik!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# Main
def main():
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot ishga tushdi (Render).")
    app.run_polling()

if __name__ == "__main__":
    main()
