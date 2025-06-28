import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TELEGRAM_BOT_TOKEN

# Create session and bot
session = AiohttpSession()
bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session)

# Create Router
router = Router()

# Handler for /start command
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply("👋 Hello! I'm SpeakNowly bot. I'll help you authenticate.")

# Function to send a confirmation message with a button
async def send_confirmation_message(telegram_id: int, phone: str, lang: str = "en") -> None:
    texts = {
        "en": f"Your phone number: {phone}\nTo complete authentication, click below ⬇️",
        "ru": f"Ваш номер телефона: {phone}\nЧтобы завершить авторизацию, нажмите ниже ⬇️",
        "uz": f"Sizning telefon raqamingiz: {phone}\nAvtorizatsiyani yakunlash uchun pastdagiga bosing ⬇️",
    }
    text = texts.get(lang, texts["en"])

    labels = {"en": "Confirm", "ru": "Подтвердить", "uz": "Tasdiqlash"}
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=labels.get(lang, "Confirm"),
                    url=f"https://api.speaknowly.com/api/v1/accounts/auth/telegram/?phone={phone}"
                )
            ]
        ]
    )

    await bot.send_message(chat_id=telegram_id, text=text, reply_markup=keyboard)

# Main function to run the bot (if you want to run as a separate process)
async def main():
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

# Run for testing
if __name__ == "__main__":
    asyncio.run(main())
