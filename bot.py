import json
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from keep_alive import keep_alive

# .env dan o‘qish
load_dotenv()
BOT_TOKEN   = os.getenv("BOT_TOKEN")
CHANNEL_ID  = int(os.getenv("CHANNEL_ID"))
CREATOR_ID  = int(os.getenv("CREATOR_ID"))

DATA_FILE = "data.json"

# --- JSON yuklash/saqlash ---
def load_data() -> dict:
    if not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size == 0:
        with open(DATA_FILE, "w") as f:
            json.dump({"films": {}}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data: dict) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- /start komandasi ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == CREATOR_ID:
        kb = ReplyKeyboardMarkup(
            [["🛠 Admin", "/list"]],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        await update.message.reply_text("Tanlang:", reply_markup=kb)
    else:
        await update.message.reply_text("Iltimos, kino kodini kiriting:")

# --- /list komandasi ---
async def list_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CREATOR_ID:
        await update.message.reply_text("⛔ Siz uchun ruxsat yo‘q.")
        return

    data = load_data()
    codes = list(data["films"].keys())
    if not codes:
        await update.message.reply_text("📭 Hozircha kino yo‘q.")
        return

    msg = "🎬 Saqlangan kino kodlari:\n\n"
    for code in codes:
        msg += f"- {code} ({len(data['films'][code])} ta post)\n"
    await update.message.reply_text(msg)

# --- Matnli xabarlar ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id  = update.effective_user.id
    raw_text = update.message.text.strip()
    text     = raw_text.upper()
    data     = load_data()

    if user_id == CREATOR_ID:
        if raw_text == "🛠 Admin":
            context.user_data["admin_step"] = "await_code"
            await update.message.reply_text("🎬 Kino kodini kiriting:")
            return

        step = context.user_data.get("admin_step")

        if step == "await_code":
            context.user_data["film_code"] = text
            context.user_data["admin_step"] = "await_ids"
            await update.message.reply_text("📩 Kino xabar IDlarini yuboring (masalan: 123,124):")
            return

        if step == "await_ids":
            film_code = context.user_data.get("film_code")
            try:
                ids = [int(x.strip()) for x in raw_text.split(",")]
                data["films"].setdefault(film_code, []).extend(ids)
                data["films"][film_code] = list(set(data["films"][film_code]))
                save_data(data)
                await update.message.reply_text(f"✅ {film_code} uchun {len(ids)} ta xabar saqlandi.")
            except ValueError:
                await update.message.reply_text("❌ Faqat son va vergul ishlating.")
            context.user_data.clear()
            return

    # Oddiy foydalanuvchi uchun
    if text in data["films"]:
        for msg_id in data["films"][text]:
            try:
                await context.bot.copy_message(
                    chat_id=update.effective_chat.id,
                    from_chat_id=CHANNEL_ID,
                    message_id=msg_id
                )
            except Exception as e:
                await update.message.reply_text("❌ Kino yuborilmadi.")
                print(f"[xatolik] {e}")
    else:
        await update.message.reply_text("🛑 Bu kodga mos kino topilmadi.")

# --- Main ---
def main():
    keep_alive()  # Flask HTTP server (Render+UptimeRobot)
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_codes))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    print("✅ Bot ishga tushdi (Render).")
    app.run_polling()

if __name__ == "__main__":
    main()
