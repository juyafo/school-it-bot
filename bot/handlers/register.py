from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..config import settings
from ..db import Application, SessionMaker
from ..keyboards import DAYS, REGISTER_BTN, days_kb, main_kb, phone_kb
from ..states import Register
from ..utils import normalize_phone, parse_grade

router = Router()

WELCOME = (
    "Assalomu alaykum! 👋\n\n"
    "Maktabimizdagi <b>IT kursiga</b> ro'yxatdan o'tish uchun "
    "quyidagi tugmani bosing."
)
SUCCESS = (
    "🎉 Siz muvaffaqiyatli ro‘yxatdan o‘tdingiz!\n\n"
    "📚 Birinchi dars:\n"
    "📍 Ma’naviyat zali\n"
    "🕐 Soat 13:30\n\n"
    "Sizni kutamiz! 😊"
)
ALREADY = (
    "Siz allaqachon ro‘yxatdan o‘tgansiz ✅\n\n"
    "📚 Birinchi dars:\n"
    "📍 Ma’naviyat zali\n"
    "🕐 Soat 13:30"
)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(WELCOME, reply_markup=main_kb())


@router.message(Command("id"))
async def my_id(message: Message):
    await message.answer(f"Sizning ID: <code>{message.from_user.id}</code>")


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=main_kb())


@router.message(F.text == REGISTER_BTN)
async def begin(message: Message, state: FSMContext):
    async with SessionMaker() as session:
        exists = await session.scalar(
            select(Application.id).where(Application.tg_id == message.from_user.id)
        )
    if exists:
        await message.answer(ALREADY)
        return
    await state.set_state(Register.full_name)
    await message.answer(
        "Ism va familiyangizni yozing:\n<i>Masalan: Aliyev Vali</i>",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Register.full_name, F.text)
async def get_name(message: Message, state: FSMContext):
    name = " ".join(message.text.split())
    if len(name.split()) < 2 or len(name) > 100:
        await message.answer(
            "Iltimos, ism va familiyani to'liq yozing.\n<i>Masalan: Aliyev Vali</i>"
        )
        return
    await state.update_data(full_name=name)
    await state.set_state(Register.grade)
    await message.answer("Nechanchi sinfda o'qiysiz?\n<i>Masalan: 9-a</i>")


@router.message(Register.grade, F.text)
async def get_grade(message: Message, state: FSMContext):
    grade = parse_grade(message.text)
    if not grade:
        await message.answer(
            "Sinfni to'g'ri yozing (1 dan 11 gacha va harf).\n<i>Masalan: 9-a</i>"
        )
        return
    await state.update_data(grade=grade)
    await state.set_state(Register.days)
    await message.answer(
        "Qaysi kunlari darsga qatnasha olasiz? Pastdan birini tanlang:",
        reply_markup=days_kb(),
    )


@router.callback_query(Register.days, F.data.startswith("days:"))
async def get_days(call: CallbackQuery, state: FSMContext):
    days = DAYS.get(call.data.split(":", 1)[1])
    if not days:
        await call.answer("Noma'lum tanlov", show_alert=True)
        return
    await state.update_data(days=days)
    await state.set_state(Register.free_time)
    await call.message.edit_text(f"📅 Kunlar: <b>{days}</b>")
    await call.message.answer(
        "Qaysi vaqtda bo'sh bo'lasiz? Soatlarni yozing:\n"
        "<i>Masalan: 15:00 dan 18:00 gacha</i>"
    )
    await call.answer()


@router.message(Register.days)
async def days_reminder(message: Message):
    await message.answer("Iltimos, yuqoridagi tugmalardan birini tanlang 👆")


@router.message(Register.free_time, F.text)
async def get_free_time(message: Message, state: FSMContext):
    free_time = " ".join(message.text.split())
    if not 3 <= len(free_time) <= 100:
        await message.answer(
            "Vaqtni qisqa yozing (3 dan 100 belgigacha).\n"
            "<i>Masalan: 15:00 dan 18:00 gacha</i>"
        )
        return
    await state.update_data(free_time=free_time)
    await state.set_state(Register.phone)
    await message.answer(
        "Telefon raqamingizni yozing yoki pastdagi tugma orqali ulashing:",
        reply_markup=phone_kb(),
    )


@router.message(Register.phone, F.contact)
async def get_contact(message: Message, state: FSMContext, bot: Bot):
    if message.contact.user_id != message.from_user.id:
        await message.answer("Iltimos, o'zingizning raqamingizni ulashing yoki yozing.")
        return
    phone = normalize_phone(message.contact.phone_number)
    if not phone:
        await message.answer("Raqam noto'g'ri. Iltimos, qo'lda yozing: 90 123 45 67")
        return
    await finish(message, state, bot, phone)


@router.message(Register.phone, F.text)
async def get_phone_text(message: Message, state: FSMContext, bot: Bot):
    phone = normalize_phone(message.text)
    if not phone:
        await message.answer(
            "Raqam noto'g'ri. Quyidagicha yozing:\n<i>90 123 45 67</i> yoki "
            "<i>+998901234567</i>"
        )
        return
    await finish(message, state, bot, phone)


async def finish(message: Message, state: FSMContext, bot: Bot, phone: str):
    data = await state.get_data()
    user = message.from_user
    app = Application(
        tg_id=user.id,
        username=user.username,
        full_name=data["full_name"],
        grade=data["grade"],
        days=data["days"],
        free_time=data["free_time"],
        phone=phone,
    )
    try:
        async with SessionMaker() as session:
            session.add(app)
            await session.commit()
    except IntegrityError:
        await state.clear()
        await message.answer(ALREADY, reply_markup=main_kb())
        return

    await state.clear()
    await message.answer(SUCCESS, reply_markup=main_kb())

    text = (
        "🆕 <b>Yangi ariza</b>\n\n"
        f"👤 {escape(app.full_name)}\n"
        f"🏫 {app.grade}\n"
        f"📅 {app.days}\n"
        f"🕐 {escape(app.free_time)}\n"
        f"📞 {app.phone}\n"
        f"🔗 {'@' + escape(app.username) if app.username else 'username yo`q'}"
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            pass