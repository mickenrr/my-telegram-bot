import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

TOKEN = "7791993635:AAFruTN9tQYjB8_G24plyroCsgaMAjnF-EI"
ADMIN_CHAT_ID = 7818769419

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MOSCOW = ZoneInfo("Europe/Moscow")

WAITING_TIP     = "waiting_for_tip"
WAITING_REF     = "waiting_for_referensy"
WAITING_KONTENT = "waiting_for_kontent"
WAITING_DOP     = "waiting_for_dopolnitelno"


def is_night() -> bool:
    now = datetime.now(MOSCOW)
    return now.hour >= 22 or now.hour < 9


def clear_waiting(ud: dict) -> None:
    for key in (WAITING_TIP, WAITING_REF, WAITING_KONTENT, WAITING_DOP):
        ud.pop(key, None)


# ── keyboards ────────────────────────────────────────────────────────────────

def kb_start() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, поехали!", callback_data="start_yes")],
        [InlineKeyboardButton("➕ Сначала расскажи подробнее", callback_data="start_more")],
    ])

def kb_ready() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👍 Да, готов!", callback_data="ready")],
    ])

def kb_q1() -> InlineKeyboardMarkup:
    options = [
        ("🖥 Корпоративный сайт", "tip_corp"),
        ("🛍 Интернет-магазин",   "tip_shop"),
        ("📄 Лендинг",            "tip_landing"),
        ("💼 Портфолио",          "tip_portfolio"),
        ("🏠 Сайт-визитка",       "tip_vizitka"),
        ("🔧 Доработка существующего", "tip_dorabotka"),
        ("❓ Другое",             "tip_other"),
    ]
    return InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=d)] for t, d in options])

def kb_q2() -> InlineKeyboardMarkup:
    options = [
        ("🎯 Привлечь клиентов",    "zad_clients"),
        ("💼 Показать экспертность", "zad_expert"),
        ("🛒 Продавать онлайн",     "zad_sell"),
        ("📋 Собрать заявки",       "zad_leads"),
        ("🌐 Укрепить бренд",       "zad_brand"),
        ("🔄 Заменить старый сайт", "zad_replace"),
    ]
    return InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=d)] for t, d in options])

def kb_q3() -> InlineKeyboardMarkup:
    options = [
        ("📄 1–5 страниц",   "ob_small"),
        ("📚 6–15 страниц",  "ob_medium"),
        ("🗂 16–30 страниц", "ob_large"),
        ("🏢 30+ страниц",   "ob_xlarge"),
    ]
    return InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=d)] for t, d in options])

def kb_q4() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Да, скину ссылки",   callback_data="ref_links")],
        [InlineKeyboardButton("💬 Опишу словами",       callback_data="ref_words")],
        [InlineKeyboardButton("🎨 Нет, доверяю вкусу", callback_data="ref_trust")],
    ])

def kb_q6() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Нет, всё сказал",  callback_data="dop_no")],
        [InlineKeyboardButton("💬 Написать текстом", callback_data="dop_write")],
    ])


# ── question senders ──────────────────────────────────────────────────────────

async def send_q1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(
        "Отлично! Начнём 🚀\n\n*Вопрос 1 из 6*\nКакой тип проекта вам нужен?",
        reply_markup=kb_q1(),
        parse_mode="Markdown",
    )

async def send_q2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(
        "*Вопрос 2 из 6*\nКакая главная задача сайта?",
        reply_markup=kb_q2(),
        parse_mode="Markdown",
    )

async def send_q3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(
        "*Вопрос 3 из 6*\nКакой примерный объём сайта?",
        reply_markup=kb_q3(),
        parse_mode="Markdown",
    )

async def send_q4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(
        "*Вопрос 4 из 6*\nЕсть ли у вас референсы — сайты, которые вам нравятся?",
        reply_markup=kb_q4(),
        parse_mode="Markdown",
    )

async def send_q5(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(
        "*Вопрос 5 из 6*\n"
        "Есть ли у вас готовый контент: тексты, фото, логотип?\n\n"
        "_Напишите в свободной форме_ — что есть, чего нет, что нужно подготовить.",
        parse_mode="Markdown",
    )
    context.user_data[WAITING_KONTENT] = True

async def send_q6(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(
        "*Вопрос 6 из 6*\nЕсть ли дополнительные пожелания или вопросы?",
        reply_markup=kb_q6(),
        parse_mode="Markdown",
    )


# ── completion ────────────────────────────────────────────────────────────────

def user_label(user) -> str:
    """Возвращает строку с именем и юзернеймом клиента."""
    parts = []
    full_name = " ".join(filter(None, [user.first_name, user.last_name]))
    if full_name:
        parts.append(full_name)
    if user.username:
        parts.append(f"@{user.username}")
    else:
        parts.append(f"id{user.id}")
    return " · ".join(parts)


def user_link(user) -> str:
    return user.username or str(user.id)


async def forward_to_admin(context: ContextTypes.DEFAULT_TYPE, user, question: str, answer: str) -> None:
    """Пересылает свободный ответ клиента администратору в реальном времени."""
    text = (
        f"✏️ {user_label(user)}\n"
        f"↳ {question}\n\n"
        f"{answer}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)


async def send_admin_notification(context: ContextTypes.DEFAULT_TYPE, user, ud: dict) -> None:
    now = datetime.now(MOSCOW)

    text = (
        f"🔔 НОВАЯ ЗАЯВКА!\n\n"
        f"👤 {user_label(user)}\n"
        f"📅 {now.strftime('%d.%m.%Y')} в {now.strftime('%H:%M')}\n\n"
        f"1. Проект: {ud.get('tip_proekta', '—')}\n"
        f"2. Задача: {ud.get('zadacha_saita', '—')}\n"
        f"3. Объём: {ud.get('obem', '—')}\n"
        f"4. Референсы: {ud.get('referensy', '—')}\n"
        f"5. Контент: {ud.get('kontent', '—')}\n"
        f"6. Доп: {ud.get('dopolnitelno', '—')}\n\n"
        f"✍ Написать: t.me/{user_link(user)}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)


async def send_final(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_night():
        text = (
            "Спасибо! Мы получили вашу заявку 🌙\n\n"
            "Сейчас уже поздно, но утром наш менеджер свяжется с вами и расскажет о следующих шагах.\n\n"
            "Хорошего вечера! 😴"
        )
    else:
        text = (
            "Отлично, заявка принята! 🎉\n\n"
            "Наш менеджер свяжется с вами в ближайшее время — обычно это занимает не больше часа.\n\n"
            "До скорой встречи! 👋"
        )
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(text)
    await send_admin_notification(context, update.effective_user, context.user_data)
    clear_waiting(context.user_data)


# ── handlers ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text(
        "Привет! 👋\n\n"
        "Я помогу подобрать решение для вашего сайта. "
        "Это займёт всего 2–3 минуты.\n\n"
        "Готовы начать?",
        reply_markup=kb_start(),
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    ud = context.user_data

    if data == "start_yes":
        await send_q1(update, context)

    elif data == "start_more":
        await query.message.reply_text(
            "Мы — команда веб-разработчиков. Создаём сайты под ключ: "
            "от простых лендингов до крупных интернет-магазинов.\n\n"
            "Сначала я задам вам 6 коротких вопросов, чтобы понять, "
            "что именно вам нужно, — а потом мы свяжемся и всё обсудим детально. 🙂",
            reply_markup=kb_ready(),
        )

    elif data == "ready":
        await send_q1(update, context)

    # Q1
    elif data.startswith("tip_"):
        labels = {
            "tip_corp":      "Корпоративный сайт",
            "tip_shop":      "Интернет-магазин",
            "tip_landing":   "Лендинг",
            "tip_portfolio": "Портфолио",
            "tip_vizitka":   "Сайт-визитка",
            "tip_dorabotka": "Доработка существующего",
        }
        if data == "tip_other":
            await query.message.reply_text("Опишите свой проект в нескольких словах:")
            ud[WAITING_TIP] = True
        else:
            ud["tip_proekta"] = labels[data]
            await send_q2(update, context)

    # Q2
    elif data.startswith("zad_"):
        labels = {
            "zad_clients": "Привлечь клиентов",
            "zad_expert":  "Показать экспертность",
            "zad_sell":    "Продавать онлайн",
            "zad_leads":   "Собрать заявки",
            "zad_brand":   "Укрепить бренд",
            "zad_replace": "Заменить старый сайт",
        }
        ud["zadacha_saita"] = labels[data]
        await send_q3(update, context)

    # Q3
    elif data.startswith("ob_"):
        labels = {
            "ob_small":  "1–5 страниц",
            "ob_medium": "6–15 страниц",
            "ob_large":  "16–30 страниц",
            "ob_xlarge": "30+ страниц",
        }
        ud["obem"] = labels[data]
        await send_q4(update, context)

    # Q4
    elif data == "ref_links":
        await query.message.reply_text("Отлично! Скиньте ссылки на сайты, которые вам нравятся:")
        ud[WAITING_REF] = True

    elif data == "ref_words":
        await query.message.reply_text("Хорошо! Опишите словами, какой стиль или ощущение вам близко:")
        ud[WAITING_REF] = True

    elif data == "ref_trust":
        ud["referensy"] = "Доверяет вкусу агентства"
        await send_q5(update, context)

    # Q6
    elif data == "dop_no":
        ud["dopolnitelno"] = "Нет"
        await send_final(update, context)

    elif data == "dop_write":
        await query.message.reply_text("Напишите ваши пожелания или вопросы:")
        ud[WAITING_DOP] = True


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ud = context.user_data
    text = update.message.text.strip()
    user = update.effective_user

    if ud.get(WAITING_TIP):
        ud.pop(WAITING_TIP)
        ud["tip_proekta"] = text
        await forward_to_admin(context, user, "Тип проекта (свободный ввод)", text)
        await send_q2(update, context)

    elif ud.get(WAITING_REF):
        ud.pop(WAITING_REF)
        ud["referensy"] = text
        await forward_to_admin(context, user, "Референсы", text)
        await send_q5(update, context)

    elif ud.get(WAITING_KONTENT):
        ud.pop(WAITING_KONTENT)
        ud["kontent"] = text
        await forward_to_admin(context, user, "Контент", text)
        await send_q6(update, context)

    elif ud.get(WAITING_DOP):
        ud.pop(WAITING_DOP)
        ud["dopolnitelno"] = text
        await forward_to_admin(context, user, "Доп. пожелания", text)
        await send_final(update, context)

    else:
        await update.message.reply_text("Чтобы начать, отправьте /start")


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
