from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

REGISTER_BTN = "📝 Ro'yxatdan o'tish"


def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=REGISTER_BTN)]], resize_keyboard=True
    )


def phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni ulashish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Yoki raqamni yozing: 90 123 45 67",
    )


def admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Arizalar ro'yxati", callback_data="list")],
            [
                InlineKeyboardButton(text="📄 CSV", callback_data="export:csv"),
                InlineKeyboardButton(text="📗 Excel", callback_data="export:xlsx"),
                InlineKeyboardButton(text="📕 PDF", callback_data="export:pdf"),
            ],
        ]
    )