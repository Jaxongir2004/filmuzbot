# Kino Kod Bot - Aiogram 3
# Telegram bot foydalanuvchidan kino kodini olib, yopiq kanaldan kino yuboradi.
# Admin paneli orqali adminlar kino kodi va message ID ni bog'lay oladi.

import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram import Router
import asyncio

API_TOKEN = '7801413763:AAEAtZS06L-7qR_hl3uYVDz7f0BsWnbrkAM'  # <-- o'zgartiring
ADMINS = [7784829606]  # <-- o'zgartiring
DATA_FILE = 'kino_data.json'

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# ------ STATES ------ #
class CodeState(StatesGroup):
    waiting_for_code = State()

class AddKinoState(StatesGroup):
    waiting_for_code = State()
    waiting_for_channel = State()
    waiting_for_message_id = State()

# ------ JSON DB ------ #
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ------ START ------ #
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Assalomu alaykum! Iltimos, kino kodini kiriting:")
    await state.set_state(CodeState.waiting_for_code)

@router.message(CodeState.waiting_for_code)
async def handle_code(message: Message, state: FSMContext):
    code = message.text.strip()
    data = load_data()
    if code in data:
        await bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=data[code]['channel_id'],
            message_id=data[code]['message_id']
        )
    else:
        await message.answer("Bunday kodga ega kino topilmadi. Qayta urinib ko'ring.")
    await state.clear()

# ------ ADMIN PANEL ------ #
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id in ADMINS:
        await message.answer("Admin paneliga xush kelibsiz:\n/kod_qoshish - yangi kod qo‘shish\n/kodlar - barcha kodlar ro‘yxati")
    else:
        await message.answer("Siz admin emassiz.")

@router.message(Command("kod_qoshish"))
async def add_kod_start(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await message.answer("Yangi kino kodi kiriting:")
        await state.set_state(AddKinoState.waiting_for_code)

@router.message(AddKinoState.waiting_for_code)
async def add_code_step(message: Message, state: FSMContext):
    await state.update_data(code=message.text.strip())
    await message.answer("Kino joylashgan kanal ID sini kiriting (masalan: -1001234567890):")
    await state.set_state(AddKinoState.waiting_for_channel)

@router.message(AddKinoState.waiting_for_channel)
async def add_channel_step(message: Message, state: FSMContext):
    await state.update_data(channel_id=message.text.strip())
    await message.answer("Kino joylashgan message ID sini kiriting:")
    await state.set_state(AddKinoState.waiting_for_message_id)

@router.message(AddKinoState.waiting_for_message_id)
async def add_message_id_step(message: Message, state: FSMContext):
    data = await state.get_data()
    code = data['code']
    channel_id = data['channel_id']
    message_id = int(message.text.strip())

    db = load_data()
    db[code] = {
        "channel_id": channel_id,
        "message_id": message_id
    }
    save_data(db)

    await message.answer(f"✅ Kod '{code}' muvaffaqiyatli qo‘shildi!", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@router.message(Command("kodlar"))
async def list_kodlar(message: Message):
    if message.from_user.id in ADMINS:
        data = load_data()
        if not data:
            await message.answer("Hozircha hech qanday kod mavjud emas.")
            return
        text = "<b>Mavjud kodlar:</b>\n"
        for k, v in data.items():
            text += f"\n<code>{k}</code> → Kanal: <code>{v['channel_id']}</code>, MsgID: <code>{v['message_id']}</code>"
        await message.answer(text)

# ------ MAIN ------ #
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
