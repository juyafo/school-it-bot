from html import escape
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from ..config import settings
from ..db import get_all_applications
from ..exports import to_csv, to_pdf, to_xlsx
from ..keyboards import admin_kb

router = Router()
router.message.filter(F.from_user.id.in_(settings.admin_ids))
router.callback_query.filter(F.from_user.id.in_(settings.admin_ids))

TZ = ZoneInfo("Asia/Tashkent")
EXPORTERS = {"csv": to_csv, "xlsx": to_xlsx, "pdf": to_pdf}


@router.message(Command("admin"))
async def admin_panel(message: Message):
    apps = await get_all_applications()
    await message.answer(
        f"👨‍💼 <b>Admin panel</b>\nJami arizalar: <b>{len(apps)}</b>",
        reply_markup=admin_kb(),
    )


@router.callback_query(F.data == "list")
async def show_list(call: CallbackQuery):
    await call.answer()
    apps = await get_all_applications()
    if not apps:
        await call.message.answer("Hozircha arizalar yo'q.")
        return

    lines = [
        f"{i}. <b>{escape(a.full_name)}</b> — {a.grade} — {a.phone}"
        f"{' — @' + escape(a.username) if a.username else ''} "
        f"<i>({a.created_at.astimezone(TZ):%d.%m %H:%M})</i>"
        for i, a in enumerate(apps, 1)
    ]

    # Telegram xabari 4096 belgidan oshmasligi uchun bo'laklab yuboramiz
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) + 1 > 3800:
            await call.message.answer(chunk)
            chunk = ""
        chunk += line + "\n"
    if chunk:
        await call.message.answer(chunk)


@router.callback_query(F.data.startswith("export:"))
async def export(call: CallbackQuery):
    fmt = call.data.split(":", 1)[1]
    exporter = EXPORTERS.get(fmt)
    if not exporter:
        await call.answer("Noma'lum format", show_alert=True)
        return

    apps = await get_all_applications()
    if not apps:
        await call.answer("Hozircha arizalar yo'q.", show_alert=True)
        return

    await call.answer("Tayyorlanmoqda...")
    data = exporter(apps)
    await call.message.answer_document(
        BufferedInputFile(data, filename=f"arizalar.{fmt}"),
        caption=f"Jami: {len(apps)} ta ariza",
    )