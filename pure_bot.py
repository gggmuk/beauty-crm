"""
BeautyCRM — Standalone Telegram Bot (Полная версия на СОМАХ для Кыргызстана)

Запуск:
    python pure_bot.py --token "8667022066:AAHYqj4AXUhe9k9YjeNb4gJRzdU7TbaCUEQ" --admin-id 8606304859

Все функции (клиентская запись, управление услугами, настройка графика по кнопкам, журнал, CRM)
выполняются на 100% внутри Telegram в валюте СОМ (сом / KGS).
"""

import argparse
import asyncio
import logging
import os
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

script_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(script_dir, "bot.log")

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(log_file_path, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("beauty_bot")

# ============================================================
# IN-MEMORY DATA STORAGE (Сомы / KGS)
# ============================================================

# Services: service_id -> dict
SERVICES_DB: Dict[str, dict] = {
    "s1": {
        "id": "s1",
        "title": "💅 Маникюр + Гель-лак",
        "duration": 90,
        "price": 1500,
        "prepayment": 300,
    },
    "s2": {
        "id": "s2",
        "title": "🦶 Смарт Педикюр",
        "duration": 60,
        "price": 1800,
        "prepayment": 400,
    },
    "s3": {
        "id": "s3",
        "title": "✨ Коррекция + Окрашивание бровей",
        "duration": 45,
        "price": 800,
        "prepayment": 200,
    },
    "s4": {
        "id": "s4",
        "title": "👁 Ламинирование ресниц",
        "duration": 60,
        "price": 1200,
        "prepayment": 300,
    },
}

# Weekly Schedule: day_idx (0-6) -> dict
SCHEDULE_DB: Dict[int, dict] = {
    0: {"is_working": True, "start": "10:00", "end": "19:00"},
    1: {"is_working": True, "start": "10:00", "end": "19:00"},
    2: {"is_working": True, "start": "10:00", "end": "19:00"},
    3: {"is_working": True, "start": "10:00", "end": "19:00"},
    4: {"is_working": True, "start": "10:00", "end": "19:00"},
    5: {"is_working": True, "start": "10:00", "end": "18:00"},
    6: {"is_working": False, "start": "10:00", "end": "18:00"},
}

# Appointments: appt_id -> dict
APPOINTMENTS_DB: Dict[str, dict] = {}

# CRM Clients: telegram_id -> dict
CLIENTS_DB: Dict[int, dict] = {}

# Master / Admin Telegram IDs
ADMIN_IDS: List[int] = []

# FSM Conversation States
(
    ADD_SVC_TITLE,
    ADD_SVC_DURATION,
    ADD_SVC_PRICE,
    ADD_SVC_PREPAYMENT,
) = range(4)

DAY_NAMES_RU = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def is_admin(user_id: int) -> bool:
    """Check if user is master/admin."""
    return user_id in ADMIN_IDS if ADMIN_IDS else True


def get_available_slots_for_date(target_date: date, service_duration_min: int) -> List[datetime]:
    """Calculate free slots for a given date."""
    day_of_week = target_date.weekday()
    sched = SCHEDULE_DB.get(day_of_week)
    if not sched or not sched["is_working"]:
        return []

    sh, sm = map(int, sched["start"].split(":"))
    eh, em = map(int, sched["end"].split(":"))

    start_dt = datetime.combine(target_date, time(sh, sm))
    end_dt = datetime.combine(target_date, time(eh, em))

    duration = timedelta(minutes=service_duration_min)
    step = timedelta(minutes=30)
    buffer_min = timedelta(minutes=15)

    busy_intervals = []
    for appt in APPOINTMENTS_DB.values():
        if appt["status"] in ["confirmed", "pending"]:
            a_start = appt["start_time"]
            a_end = appt["end_time"] + buffer_min
            busy_intervals.append((a_start, a_end))

    available = []
    curr = start_dt
    now = datetime.now()

    while curr + duration <= end_dt:
        slot_end = curr + duration
        if curr > now:
            overlap = any(curr < b_end and slot_end > b_start for b_start, b_end in busy_intervals)
            if not overlap:
                available.append(curr)
        curr += step

    return available


# ============================================================
# CLIENT FLOW HANDLERS (/start)
# ============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Client /start command."""
    user = update.effective_user

    # Register client in CRM
    if user.id not in CLIENTS_DB:
        CLIENTS_DB[user.id] = {
            "id": user.id,
            "name": user.full_name,
            "phone": None,
            "visits": 0,
            "spent": 0,
            "last_visit": None,
            "status": "Постоянный",
        }

    text = (
        f"👋 <b>Саламатсызбы, {user.first_name}!</b>\n\n"
        f"Добро пожаловать в бот онлайн-записи бьюти-студии!\n"
        f"Здесь вы можете выбрать услугу, удобную дату и время за 1 минуту."
    )

    keyboard = [
        [InlineKeyboardButton("💅 Записаться на услугу", callback_data="client_book")],
        [
            InlineKeyboardButton("📋 Мои Записи", callback_data="client_my_appts"),
            InlineKeyboardButton("🎁 Акции & Бонусы", callback_data="client_promo"),
        ],
    ]

    if is_admin(user.id):
        keyboard.append([InlineKeyboardButton("⚙️ Панель Мастера (/admin)", callback_data="admin_menu")])

    await update.message.reply_html(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def client_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle client inline buttons."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "client_book":
        if not SERVICES_DB:
            await query.edit_message_text(
                "❌ Услуги пока не добавлены мастером.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 В Главное Меню", callback_data="client_main")]]),
            )
            return

        keyboard = []
        for s_id, s in SERVICES_DB.items():
            btn_text = f"{s['title']} — {s['price']} сом ({s['duration']} мин)"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"book_svc:{s_id}")])

        keyboard.append([InlineKeyboardButton("⬅️ В главное меню", callback_data="client_main")])
        await query.edit_message_text(
            "💅 <b>Шаг 1 из 3: Выберите услугу</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data.startswith("book_svc:"):
        s_id = data.split(":")[1]
        context.user_data["selected_service_id"] = s_id
        service = SERVICES_DB[s_id]

        # Step 2: Select Date (Next 7 days)
        keyboard = []
        today = date.today()
        days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

        row = []
        for i in range(7):
            d = today + timedelta(days=i)
            day_str = d.strftime("%d.%m")
            weekday = days_ru[d.weekday()]
            label = f"{weekday} {day_str}"
            row.append(InlineKeyboardButton(label, callback_data=f"book_date:{d.isoformat()}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton("⬅️ Изменить услугу", callback_data="client_book")])

        await query.edit_message_text(
            f"💅 <b>Услуга:</b> {service['title']}\n"
            f"💰 <b>Цена:</b> {service['price']} сом\n\n"
            f"<b>Шаг 2 из 3: Выберите дату визита</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data.startswith("book_date:"):
        date_str = data.split(":")[1]
        target_date = date.fromisoformat(date_str)
        context.user_data["selected_date"] = date_str

        s_id = context.user_data.get("selected_service_id")
        service = SERVICES_DB[s_id]

        slots = get_available_slots_for_date(target_date, service["duration"])

        if not slots:
            keyboard = [[InlineKeyboardButton("📅 Выбрать другую дату", callback_data=f"book_svc:{s_id}")]]
            await query.edit_message_text(
                f"❌ На {target_date.strftime('%d.%m.%Y')} нет свободных слотов (выходной или все занято).\n\n"
                f"Пожалуйста, выберите другую дату.",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return

        keyboard = []
        row = []
        for slot in slots:
            t_str = slot.strftime("%H:%M")
            row.append(InlineKeyboardButton(t_str, callback_data=f"book_slot:{slot.isoformat()}"))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton("⬅️ Назад к выбору даты", callback_data=f"book_svc:{s_id}")])

        await query.edit_message_text(
            f"⏰ <b>Свободное время на {target_date.strftime('%d.%m.%Y')}:</b>\n\n"
            f"Выберите удобный слот:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data.startswith("book_slot:"):
        slot_iso = data.split(":", 1)[1]
        slot_dt = datetime.fromisoformat(slot_iso)

        s_id = context.user_data.get("selected_service_id")
        service = SERVICES_DB[s_id]

        appt_id = str(uuid4())[:8]
        end_dt = slot_dt + timedelta(minutes=service["duration"])

        APPOINTMENTS_DB[appt_id] = {
            "id": appt_id,
            "client_id": user_id,
            "client_name": query.from_user.full_name,
            "service_title": service["title"],
            "price": service["price"],
            "prepayment": service["prepayment"],
            "start_time": slot_dt,
            "end_time": end_dt,
            "status": "confirmed",
        }

        # Update CRM metrics
        client = CLIENTS_DB.get(user_id, {})
        client["visits"] = client.get("visits", 0) + 1
        client["spent"] = client.get("spent", 0) + service["price"]
        client["last_visit"] = datetime.now().strftime("%d.%m.%Y")

        start_str = slot_dt.strftime("%d.%m.%Y в %H:%M")

        text = (
            f"✅ <b>Запись успешно подтверждена!</b>\n\n"
            f"💅 <b>Услуга:</b> {service['title']}\n"
            f"🕒 <b>Дата и время:</b> {start_str}\n"
            f"💰 <b>Стоимость:</b> {service['price']} сом\n"
            f"💵 <b>Предоплата:</b> {service['prepayment']} сом\n\n"
            f"Ждем вас! Напоминание придет за 24 часа и за 2 часа до визита."
        )

        keyboard = [[InlineKeyboardButton("🏠 В Главное Меню", callback_data="client_main")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

        # Push notification to Master
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"🔔 <b>Новая запись от клиента!</b>\n\n"
                        f"👤 <b>Клиент:</b> {query.from_user.full_name}\n"
                        f"💅 <b>Услуга:</b> {service['title']}\n"
                        f"🕒 <b>Время:</b> {start_str}\n"
                        f"💰 <b>Сумма:</b> {service['price']} сом (Предоплата: {service['prepayment']} сом)"
                    ),
                    parse_mode="HTML",
                )
            except Exception:
                pass

    elif data == "client_my_appts":
        my_appts = [a for a in APPOINTMENTS_DB.values() if a["client_id"] == user_id]
        if not my_appts:
            text = "📋 У вас пока нет активных записей."
            keyboard = [[InlineKeyboardButton("💅 Записаться прямо сейчас", callback_data="client_book")]]
        else:
            text = "📋 <b>Ваши записи:</b>\n\n"
            keyboard = []
            for a in my_appts:
                t_str = a["start_time"].strftime("%d.%m.%Y в %H:%M")
                status_icon = "✅" if a["status"] == "confirmed" else "❌"
                text += f"{status_icon} <b>{a['service_title']}</b>\n   🕒 {t_str} — {a['price']} сом\n\n"
                if a["status"] == "confirmed":
                    keyboard.append([InlineKeyboardButton(f"❌ Отменить запись ({t_str})", callback_data=f"cancel_appt:{a['id']}")])

            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="client_main")])

        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("cancel_appt:"):
        appt_id = data.split(":")[1]
        if appt_id in APPOINTMENTS_DB:
            APPOINTMENTS_DB[appt_id]["status"] = "cancelled"
            await query.edit_message_text(
                "❌ <b>Ваша запись отменена.</b> Будем рады видеть вас в следующий раз!",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data="client_main")]]),
            )

    elif data == "client_promo":
        text = (
            "🎁 <b>Акции & Бонусная система</b>\n\n"
            "• <b>Приведи подругу</b> — получи 300 сом бонусом на следующую процедуру!\n"
            "• Каждый 5-й визит со скидкой 15%!"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="client_main")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "client_main":
        text = "🏠 <b>Главное меню:</b>"
        keyboard = [
            [InlineKeyboardButton("💅 Записаться на услугу", callback_data="client_book")],
            [
                InlineKeyboardButton("📋 Мои Записи", callback_data="client_my_appts"),
                InlineKeyboardButton("🎁 Акции & Бонусы", callback_data="client_promo"),
            ],
        ]
        if is_admin(user_id):
            keyboard.append([InlineKeyboardButton("⚙️ Панель Мастера (/admin)", callback_data="admin_menu")])

        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


# ============================================================
# RENDER HELPER FUNCTIONS (Clean & Non-Recursive)
# ============================================================

async def render_schedule_screen(query):
    """Render the schedule screen cleanly without callback recursion."""
    text = "⏰ <b>Настройка Графика Работы (Пн-Вс):</b>\n\n"
    keyboard = []

    for idx, name in enumerate(DAY_NAMES_RU):
        sch = SCHEDULE_DB[idx]
        status_icon = "🟢" if sch["is_working"] else "🔴"
        status_text = f"{sch['start']} - {sch['end']}" if sch["is_working"] else "Выходной"

        text += f"{status_icon} <b>{name}:</b> {status_text}\n"

        # Interactive Toggle Button
        btn_label = f"{status_icon} {name}: {status_text}"
        keyboard.append([InlineKeyboardButton(btn_label, callback_data=f"adm_tog_day:{idx}")])

    keyboard.append([InlineKeyboardButton("⬅️ Панель Мастера", callback_data="admin_menu")])
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def render_services_screen(query):
    """Render the services list screen cleanly."""
    text = "💅 <b>Ваш Прайс-Лист Услуг (в Сомах):</b>\n\n"
    keyboard = []

    if not SERVICES_DB:
        text += "Услуги пока не добавлены."
    else:
        for s_id, s in SERVICES_DB.items():
            text += f"• <b>{s['title']}</b>\n  💰 {s['price']} сом | ⏱ {s['duration']} мин | 💵 Пред.: {s['prepayment']} сом\n\n"
            keyboard.append([InlineKeyboardButton(f"🗑 Удалить «{s['title']}»", callback_data=f"adm_del_svc:{s_id}")])

    keyboard.append([InlineKeyboardButton("➕ Добавить новую услугу", callback_data="adm_add_service")])
    keyboard.append([InlineKeyboardButton("⬅️ Панель Мастера", callback_data="admin_menu")])

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


# ============================================================
# MASTER / ADMIN FLOW HANDLERS (/admin)
# ============================================================

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Master /admin command."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ Доступ только для мастера/администратора.")
        return

    text = (
        "⚙️ <b>Панель Мастера (BeautyCRM Admin)</b>\n\n"
        "Управление услугами, графиком работы, журналом и клиентами в сомах (KGS):"
    )
    keyboard = [
        [InlineKeyboardButton("💅 Мои Услуги и Цены", callback_data="adm_services")],
        [InlineKeyboardButton("⏰ График Работы (Пн-Вс)", callback_data="adm_schedule")],
        [InlineKeyboardButton("📅 Журнал Записей", callback_data="adm_appointments")],
        [InlineKeyboardButton("👥 База Клиентов (CRM)", callback_data="adm_crm")],
    ]
    await update.message.reply_html(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle master inline query buttons cleanly."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if not is_admin(user_id):
        return

    if data == "admin_menu":
        text = "⚙️ <b>Панель Мастера (BeautyCRM Admin)</b>\n\nВыберите раздел:"
        keyboard = [
            [InlineKeyboardButton("💅 Мои Услуги и Цены", callback_data="adm_services")],
            [InlineKeyboardButton("⏰ График Работы (Пн-Вс)", callback_data="adm_schedule")],
            [InlineKeyboardButton("📅 Журнал Записей", callback_data="adm_appointments")],
            [InlineKeyboardButton("👥 База Клиентов (CRM)", callback_data="adm_crm")],
        ]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    # ================= 1. Services Management =================
    elif data == "adm_services":
        await render_services_screen(query)

    elif data.startswith("adm_del_svc:"):
        s_id = data.split(":")[1]
        if s_id in SERVICES_DB:
            del SERVICES_DB[s_id]
        await render_services_screen(query)

    # ================= 2. Schedule Management (Пн-Вс) =================
    elif data == "adm_schedule":
        await render_schedule_screen(query)

    elif data.startswith("adm_tog_day:"):
        day_idx = int(data.split(":")[1])
        # Toggle working day status cleanly
        SCHEDULE_DB[day_idx]["is_working"] = not SCHEDULE_DB[day_idx]["is_working"]
        await render_schedule_screen(query)

    # ================= 3. Appointments Journal =================
    elif data == "adm_appointments":
        if not APPOINTMENTS_DB:
            text = "📅 <b>Журнал Записей пуст.</b>\nЗаписи от клиентов будут появляться здесь."
            keyboard = [[InlineKeyboardButton("⬅️ Панель Мастера", callback_data="admin_menu")]]
        else:
            text = "📅 <b>Журнал Записей Клиентов:</b>\n\n"
            keyboard = []

            for a_id, a in APPOINTMENTS_DB.items():
                t_str = a["start_time"].strftime("%d.%m.%Y в %H:%M")
                status_str = "✅ Подтверждена" if a["status"] == "confirmed" else "❌ Отменена"
                text += f"👤 <b>{a['client_name']}</b>\n💅 {a['service_title']} ({a['price']} сом)\n🕒 {t_str} — [{status_str}]\n\n"

                if a["status"] == "confirmed":
                    keyboard.append([
                        InlineKeyboardButton(f"❌ Отменить ({a['client_name']})", callback_data=f"adm_cancel_appt:{a_id}")
                    ])

            keyboard.append([InlineKeyboardButton("⬅️ Панель Мастера", callback_data="admin_menu")])

        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("adm_cancel_appt:"):
        a_id = data.split(":")[1]
        if a_id in APPOINTMENTS_DB:
            APPOINTMENTS_DB[a_id]["status"] = "cancelled"

        # Re-render appointments journal
        text = "📅 <b>Журнал Записей Клиентов:</b>\n\n"
        keyboard = []

        for a_id, a in APPOINTMENTS_DB.items():
            t_str = a["start_time"].strftime("%d.%m.%Y в %H:%M")
            status_str = "✅ Подтверждена" if a["status"] == "confirmed" else "❌ Отменена"
            text += f"👤 <b>{a['client_name']}</b>\n💅 {a['service_title']} ({a['price']} сом)\n🕒 {t_str} — [{status_str}]\n\n"

            if a["status"] == "confirmed":
                keyboard.append([
                    InlineKeyboardButton(f"❌ Отменить ({a['client_name']})", callback_data=f"adm_cancel_appt:{a_id}")
                ])

        keyboard.append([InlineKeyboardButton("⬅️ Панель Мастера", callback_data="admin_menu")])
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    # ================= 4. CRM Client Directory =================
    elif data == "adm_crm":
        text = "👥 <b>База Клиентов CRM (в Сомах):</b>\n\n"
        if not CLIENTS_DB:
            text += "Клиенты пока не зафиксированы."
        else:
            for c in CLIENTS_DB.values():
                text += f"• <b>{c['name']}</b>\n  Визитов: {c['visits']} | LTV (Выручка): {c['spent']} сом\n\n"

        keyboard = [[InlineKeyboardButton("⬅️ Панель Мастера", callback_data="admin_menu")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


# ============================================================
# FSM: ADD SERVICE DIALOG
# ============================================================

async def add_service_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("✏️ Введите <b>название новой услуги</b> (например: Маникюр Френч):", parse_mode="HTML")
    return ADD_SVC_TITLE


async def add_service_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_svc_title"] = update.message.text
    await update.message.reply_text("⏱ Введите <b>длительность услуги в минутах</b> (например: 60):", parse_mode="HTML")
    return ADD_SVC_DURATION


async def add_service_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["new_svc_duration"] = int(update.message.text)
        await update.message.reply_text("💰 Введите <b>стоимость услуги в сомах</b> (например: 1500):", parse_mode="HTML")
        return ADD_SVC_PRICE
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число (минуты).")
        return ADD_SVC_DURATION


async def add_service_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["new_svc_price"] = int(update.message.text)
        await update.message.reply_text("💵 Введите <b>сумму предоплаты в сомах</b> (или 0):", parse_mode="HTML")
        return ADD_SVC_PREPAYMENT
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число (сомы).")
        return ADD_SVC_PRICE


async def add_service_prepayment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        prepayment = int(update.message.text)
        new_id = f"s{len(SERVICES_DB) + 1}"

        SERVICES_DB[new_id] = {
            "id": new_id,
            "title": context.user_data["new_svc_title"],
            "duration": context.user_data["new_svc_duration"],
            "price": context.user_data["new_svc_price"],
            "prepayment": prepayment,
        }

        await update.message.reply_text(
            f"✅ <b>Услуга «{context.user_data['new_svc_title']}» ({context.user_data['new_svc_price']} сом) успешно создана!</b>\n\n"
            f"Введите /admin чтобы открыть меню мастера.",
            parse_mode="HTML",
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число (сомы).")
        return ADD_SVC_PREPAYMENT


async def cancel_fsm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


# ============================================================
# MAIN ENTRYPOINT
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="BeautyCRM Pure Telegram Bot (Kyrgyzstan SOM)")
    parser.add_argument("--token", required=True, help="Telegram Bot Token from @BotFather")
    parser.add_argument("--admin-id", type=int, help="Telegram ID of the master/admin")
    args = parser.parse_args()

    if args.admin_id:
        ADMIN_IDS.append(args.admin_id)

    logger.info("🚀 Starting BeautyCRM Telegram Bot (SOM / KGS)...")

    app = Application.builder().token(args.token).build()

    # FSM for adding new service
    add_svc_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_service_start, pattern="^adm_add_service$")],
        states={
            ADD_SVC_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_title)],
            ADD_SVC_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_duration)],
            ADD_SVC_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_price)],
            ADD_SVC_PREPAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_prepayment)],
        },
        fallbacks=[CommandHandler("cancel", cancel_fsm)],
        per_message=False,
    )

    # Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))

    app.add_handler(add_svc_conv)

    app.add_handler(CallbackQueryHandler(client_callback_handler, pattern="^(client_|book_|cancel_appt:)"))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(adm_|admin_)"))

    logger.info("✅ Bot is online and listening! Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
