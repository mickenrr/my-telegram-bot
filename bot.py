import logging
import os
import asyncio
import re
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InputFile,
)
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# -------------------------------------------
# CONFIG
# -------------------------------------------
TOKEN = "8456104393:AAHDCqq26_uzrhlzaWkMJxyiOLzeDIsMC5o"

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTO_1 = os.path.join(_BASE_DIR, "frame1.png")
PHOTO_2 = os.path.join(_BASE_DIR, "frame2.png")
PHOTO_3 = os.path.join(_BASE_DIR, "frame3.png")
PHOTO_4 = os.path.join(_BASE_DIR, "frame4.png")
PHOTO_5 = os.path.join(_BASE_DIR, "frame5.png")
PHOTO_6 = os.path.join(_BASE_DIR, "frame6.png")
PHOTO_7 = os.path.join(_BASE_DIR, "frame7.png")
PHOTO_8 = os.path.join(_BASE_DIR, "frame8.png")

HABIT_NAMES = {
    "habit_train": "15-минутная тренировка",
    "habit_water": "Выпить стакан воды утром",
    "habit_read": "Прочесть 1 главу книги",
    "habit_walk": "Прогуляться полчаса",
    "habit_expenses": "Внести расходы за день",
    "habit_journal": "Заполнить дневник благодарности",
    "habit_plan": "Распланировать завтрашний день",
    "habit_shower": "Принять контрастный душ",
    "habit_priority": "Определить приоритет на день",
    "habit_cleanup": "Разобрать 1 участок бардака",
}

# Словарь для распознавания городов и их часовых поясов
CITY_TIMEZONES = {
    # Россия
    "москва": "Europe/Moscow",
    "moscow": "Europe/Moscow",
    "санкт-петербург": "Europe/Moscow",
    "petersburg": "Europe/Moscow",
    "питер": "Europe/Moscow",
    "екатеринбург": "Asia/Yekaterinburg",
    "yekaterinburg": "Asia/Yekaterinburg",
    "новосибирск": "Asia/Novosibirsk",
    "novosibirsk": "Asia/Novosibirsk",
    "владивосток": "Asia/Vladivostok",
    "vladivostok": "Asia/Vladivostok",
    "калининград": "Europe/Kaliningrad",
    "kaliningrad": "Europe/Kaliningrad",

    # Другие популярные города
    "лондон": "Europe/London",
    "london": "Europe/London",
    "париж": "Europe/Paris",
    "paris": "Europe/Paris",
    "берлин": "Europe/Berlin",
    "berlin": "Europe/Berlin",
    "токио": "Asia/Tokyo",
    "tokyo": "Asia/Tokyo",
    "пекин": "Asia/Shanghai",
    "beijing": "Asia/Shanghai",
    "нью-йорк": "America/New_York",
    "new york": "America/New_York",
    "лос-анджелес": "America/Los_Angeles",
    "los angeles": "America/Los_Angeles",
    "дубай": "Asia/Dubai",
    "dubai": "Asia/Dubai",
    "стамбул": "Europe/Istanbul",
    "istanbul": "Europe/Istanbul",
}

# Список популярных часовых поясов для выбора
TIMEZONE_OPTIONS = [
    ("UTC-8 (Лос-Анджелес)", "America/Los_Angeles"),
    ("UTC-5 (Нью-Йорк)", "America/New_York"),
    ("UTC+0 (Лондон)", "Europe/London"),
    ("UTC+1 (Берлин, Париж)", "Europe/Berlin"),
    ("UTC+2 (Калининград)", "Europe/Kaliningrad"),
    ("UTC+3 (Москва)", "Europe/Moscow"),
    ("UTC+5 (Екатеринбург)", "Asia/Yekaterinburg"),
    ("UTC+7 (Новосибирск)", "Asia/Novosibirsk"),
    ("UTC+9 (Токио)", "Asia/Tokyo"),
    ("UTC+10 (Владивосток)", "Asia/Vladivostok"),
]

# Варианты текстов для напоминаний
REMINDER_TEMPLATES = [
    "Эй, небольшое напоминание: твоя привычка ждет своего звёздного часа 🙂",
    "Твоя сегодняшняя привычка уже размяла пальцы и готова!\n\nТы тоже? 😉",
    "Один маленький шаг сейчас — и ты уже лучше, чем 5 минут назад.\n\nПора привычки 😉",
    "Если ищешь знак — вот он.\n\nПора выполнить привычку ✨",
    "Я вообще не настаиваю…\n\nНо было бы круто сделать твою привычку прямо сейчас 👀",
    "Так… Я проверил расписание.\n\nДа, кажется, настал момент твоей супер-привычки 💫",
    "Если бы привычки умели томно смотреть — твоя бы сейчас так и делала.\n\nМожет, выполним её? 👁️👁️",
    "*Кхм-кхм…*\n\nНебольшое напоминание. Твоя привычка ожидает ❤️",
    "Ну что… делаем вид, что всё под контролем?\n\nТогда выполняем привычку 😉",
    "Вселенная подмигнула. Это знак.\n\nПора заняться привычкой 🌌",
    "— Моментум, напомни, когда время привычки?\n\n— Вот. Прямо вот оно.",
]

# Варианты текстов для подтверждения выполнения привычки
COMPLETION_TEMPLATES = [
    "Оп! Привычка — выполнена ✔️\n\nТвой страйк теперь: <b>{streak}</b>\n\nПродолжаем этот танец дисциплины.",
    "Привычка отмечена!\n\nСтрайк: <b>{streak}</b>\n\nЯ бы похлопал, но у меня нет рук — только уважение.",
    "Операция \"привычка\" — удачна.\n\nСтрайк: <b>{streak}</b>\n\nПродолжаем.",
    "Готово.\n\n{streak} — и это только начало.",
    "Отмечено.\n\nСтрайк: <b>{streak}</b>\n\nПроверка пройдена. Система на стороне побед.",
    "Готово!\n\nСтрайк: <b>{streak}</b>\n\nТы уверенно играешь на стороне победителей.",
    "Готово, молодец!\n\nСтрайк: <b>{streak}</b>\n\nТвой ритм начинает нравиться мне всё больше.",
    "Записано.\n\nСтрайк: <b>{streak}</b>\n\nМаленькие шаги меняют большие истории.",
    "Галочка поставлена ✔️\n\nСтрайк: <b>{streak}</b>\n\nДаже если никто не заметит — я заметил 😎",
]

# Варианты текстов для повторной попытки отметить привычку
ALREADY_DONE_TEMPLATES = [
    "Отметка на сегодня уже стоит. Хватит геройствовать — следующие подвиги завтра.",
    "Стоп-стоп! Сегодняшний прогресс уже зафиксирован. Не жми так часто, я нервничаю.",
    "Эй, чемпион, отметка уже стоит. Можешь официально расслабиться.",
    "Ты пытаешься впечатлить меня? Впечатлён. Но отметка уже проставлена.",
    "Всё учтено. Отдыхаем. Я тоже, между прочим, устал следить.",
    "Люблю твоё рвение, но отметка уже там. Не переживай, завтра снова сможешь блистать.",
    "Не спеши так жить. Сегодня всё учтено, больше ничего нажимать не надо.",
    "Если бы можно было отмечать дважды — я бы разрешил. Но система строгая, как диета в январе.",
    "Хмм, вижу энтузиазм. Но отметка за сегодня уже стоит. Сохраним вдохновение для следующего раунда.",
]

# Варианты текстов для напоминания, когда привычка уже выполнена
REMINDER_ALREADY_DONE_TEMPLATES = [
    "Ой, а я тут с напоминанием… Но вижу, что у тебя уже все выполнено. Рано или поздно я стану не нужен. Страшно.",
    "Пришел напомнить, но… Привычка уже выполнена? Вот это я понимаю — опережающая атака.",
    "Напоминалка подъехала! Но тебе удалось меня опередить. Неловко… я пойду.",
    "По плану я должен сказать: «Пора выполнять привычку». Но у тебя уже всё выполнено. План провалился красиво.",
    "Смотрю — отметка стоит. Ну… тогда считай, что это просто дружеское \"привет\".",
    "Я пришёл быть полезным, а ты уже в гиперпродуктивности. Неловко, конечно, но я рад.",
    "Напоминание: «Пора…» Стоп. Привычка уже отмечена. Ладно, молодец, живи дальше.",
    "Сегодня ты быстрее моей напоминалки. Это звучит как комплимент — и пусть так и будет.",
    "Вот же… Пока я шёл с напоминанием, твоя привычка сегодня уже сделана. Так и подумаю, что ты меня проверяешь.",
]

# Варианты текстов для запроса изменения времени
TIME_CHANGE_CONFIRMATION_TEMPLATES = [
    "Хочешь поменять время? Окей, могу подстроиться. Но помни: привычки любят стабильность — как коты. Обычно одно и то же время помогает мозгу включать «ритуал» автоматически.\n\n"
    "Что делаем?",

    "Так, вижу желание всё перенастроить. Это нормально — мы живые существа, а не часы. Но всё же стараемся держать одно время: так мозгу проще запускать привычку без борьбы.\n\n"
    "Выбирай, как продолжаем:",

    "Хочешь другое время — без проблем. Но предупреждаю: стабильность = сила привычки. Мозг любит повторяемость, он на ней буквально строит автопилот.\n\n"
    "Как двигаемся дальше?",

    "Запрос на изменение времени принят. Но перед тем как дергать расписание — подумай: одно фиксированное время помогает привычке «приклеиться» к твоему дню.\n\n"
    "Твои следующие шаги?",

    "Ну что, пересобираем график? Я только за, но помни: привычка, как растение — лучше растёт, когда поливают по расписанию, а не «когда вспомнил(а)».\n\n"
    "Что выбираешь?",

    "Хочешь изменить время — могу. Но стабильность творит чудеса: одно и то же время помогает мозгу не ныть, а выполнять.\n\n"
    "Куда жмём?",
]

# Варианты текстов для повторного напоминания (через 2 часа)
SECOND_REMINDER_TEMPLATES = [
    "Я тут сижу, обновляю чат… а тишина такая, будто я в режиме «игнор». Ну ладно. Я подожду. 😌",
    "Щёлкнуло 2 часа молчания. Я… я обиделся. Ну чуть-чуть. Не сильно. Но обиделся",
    "Сижу здесь уже 2 часа, смотрю в чат, как в окно. Где же ты там гуляешь?.. 😔",
    "Я тут тихонько стою в углу чата и делаю вид, что не скучаю. Но вообще-то… скучаю",
    "Я уже успел составить заговор, что тебя похитили дела. Ты в порядке? 👀",
    "Проверка связи…Приём! Пользователь на месте? Или мне уже отправлять поисковый отряд?",
    "Прошло время, а ты всё не возвращаешься. Я уже начал строить теории похлеще, чем в «Очень странных делах».",
    "Если это была тактика «исчезнуть, чтобы вызвать интерес» — работает, я заинтригован.",
    "Уже пару часов я не получал от тебя ни единого пикселя. Но я верю в твоё возвращение ✨",
    "Если ты сейчас читаешь это спустя время — знай: я не сержусь, я просто слегка театральный 😌",
]

# Варианты текстов для пропущенного дня
MISSED_DAY_TEMPLATES = [
    "**День потерян… но не ты**\n\n"
    "Ну что… день прошёл, а привычка сегодня так и не случилась. Не трагедия, но и не просто «ну бывает».\n\n"
    "Смотри, в формировании привычки самое главное — это не магическая сила мотивации, а маленькое, аккуратное *«я сделал(а)»* каждый день. "
    "Даже если настроение 2/10, даже если не очень хочется. Каждый пропуск — это минус один кирпичик в твою новую версию себя, и, к сожалению, его потом приходится докладывать снова. "
    "Я поставил крестик, но не чтобы ругать — а чтобы мы видели реальную картину.\n\n"
    "Главное — не дать сегодняшнему дню превратиться в завтрашний.\n\n"
    "Возвращайся завтра. В моменте начинается движение — помни об этом.",

    "**Крестик поставил, но точку — нет**\n\n"
    "Сегодня привычка осталась без отметки.\n\n"
    "Я подожду драматическую паузу…\n\n"
    "…\n\n"
    "Окей. Теперь серьёзно.\n\n"
    "Каждый раз, когда ты отмечаешь привычку, мозг получает маленький, но важный сигнал: *«Это важно. Это часть моей жизни.»* "
    "А когда отметки нет — мозг получает другой сигнал: *«Ну… наверное, не так уж и важно.»* "
    "Поэтому пропуски — это не просто «ой, забыл(а)», это маленькие повороты руля в сторону, откуда пришли. Но хорошая новость: один пропуск ещё ничего не разрушает.\n\n"
    "Я поставил крестик, чтобы мы зафиксировали факт, а завтра вернём траекторию обратно.\n\n"
    "Я с тобой, Моментум рядом. Завтра вернём импульс.",

    "**Сегодняшнее молчание привычки**\n\n"
    "Хмм… отметки нет. Значит, привычка сегодня решила остаться за кулисами. Но позволь напомнить кое-что важное.\n\n"
    "Привычка — это не про героические рывки, это про то, что ты делаешь *даже когда не хочется*. "
    "Маленькие действия, повторённые много раз, строят огромный результат. Пропуски же — это маленькие удержания тормоза.\n\n"
    "Я фиксирую крестик не чтобы расстроить тебя, а чтобы показать: мы либо строим импульс, либо теряем его. "
    "Сегодня — маленькая потеря. Но то, что ты читаешь этот текст — уже признак, что возвращаться ты умеешь. Завтра продолжим путь. Не с нуля — а дальше.",

    "**Привычка сегодня не вышла на сцену**\n\n"
    "Ну что… сегодняшний день без отметки. Я поставил крестик, немного вздохнул и продолжаю работать.\n\n"
    "Дело не в том, что «ой, один день пропущен, беда». А в том, что мозг очень любит паттерны. "
    "Если он видит регулярность — он подстраивает жизнь под неё. Если видит хаос — хаос он и закрепляет.\n\n"
    "Каждая отметка — это маленький договор с собой. Каждый пропуск — это тоже договор, но уже другого содержания.\n\n"
    "Но ты же не сдаёшься после одного сбоя? Вот и отлично. Мы не делаем выводов по одному кресту. "
    "Просто завтра я снова буду ждать обычный сигнал — и знаю, что он придёт.",

    "**Импульс просел, но не исчез**\n\n"
    "Сегодня привычка осталась невыполненной, и я отмечаю это честно — крестиком. Но не для того, чтобы упрекнуть, а чтобы кое-что объяснить.\n\n"
    "Есть такая штука — механизм закрепления. Если ты выполняешь привычку регулярно, мозг начинает воспринимать её как *естественную часть твоего дня*. "
    "Если пропуски случаются слишком часто — мозг решает: «Ну… наверное, это необязательно.» А мы ведь с тобой строим *движение*, а не «когда получится».\n\n"
    "Поэтому сегодняшняя пауза — это просто сигнал: завтра надо вернуться и восстановить ритм. "
    "Ты же знаешь: импульс начинается с одного момента. И продолжается — тоже моментами.\n\n"
    "Завтра поймаем его снова.",

    "**Без нажима, но честно**\n\n"
    "Сегодня отметки нет, и я фиксирую пропуск. Без драмы, без нагнетания — но и без попытки сделать вид, что «это не важно».\n\n"
    "Важно.\n\n"
    "Регулярность — вот настоящая суперсила в работе с привычками. Даже крошечные шаги каждый день перепрошивают твою идентичность. "
    "Пропуски — это микропауза, которая тормозит процесс настройки мозга на новый путь.\n\n"
    "Но мы уже начали этот путь. Значит, пропуск — это просто ямка на дороге, а не конец маршрута. "
    "Завтра поставим галочку. Я верю — и я жду.",
]

# -------------------------------------------
# KEYBOARDS
# -------------------------------------------
continue_reply = ReplyKeyboardMarkup(
    [[KeyboardButton("Продолжить")]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

second_reply = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Почему важно выбрать только 1 привычку?")],
        [KeyboardButton("Отлично, приступим!")],
    ],
    resize_keyboard=True,
)

single_letsgo_reply = ReplyKeyboardMarkup(
    [[KeyboardButton("Отлично, приступим!")]],
    resize_keyboard=True
)

timezone_confirm_reply = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Да, всё верно")],
        [KeyboardButton("Выбрать другой часовой пояс")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

whats_next_reply = ReplyKeyboardMarkup(
    [[KeyboardButton("Что дальше?")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

progress_reply = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📊 Прогресс"), KeyboardButton("✅ Отметить привычку")],
        [KeyboardButton("⏰ Изменить время"), KeyboardButton("🔄 Изменить привычку")],
        [KeyboardButton("➕ Добавить привычку")],
    ],
    resize_keyboard=True
)

habit_inline = InlineKeyboardMarkup([
    [InlineKeyboardButton("💪🏻 15-минутная тренировка", callback_data="habit_train")],
    [InlineKeyboardButton("💧 Выпить стакан воды утром", callback_data="habit_water")],
    [InlineKeyboardButton("📖 Прочесть 1 главу книги", callback_data="habit_read")],
    [InlineKeyboardButton("Своя привычка", callback_data="habit_custom")],
    [InlineKeyboardButton("Ещё варианты ➡️", callback_data="habit_more")],
])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------
# HELPERS
# -------------------------------------------
async def safe_send_photo(context, chat_id, path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                await context.bot.send_photo(chat_id, InputFile(f))
        except Exception as e:
            logger.warning(f"Error sending photo: {e}")

async def type_and_send(context, chat_id, text, delay=0.7, parse_html=False, reply_markup=None):
    try:
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    except:
        pass
    await asyncio.sleep(delay)
    kwargs = {}
    if parse_html:
        kwargs["parse_mode"] = "HTML"
    if reply_markup:
        kwargs["reply_markup"] = reply_markup
    await context.bot.send_message(chat_id, text, **kwargs)

def is_valid_time(t: str) -> bool:
    return bool(re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)", t.strip()))

def calculate_streak(completed_dates):
    """Вычисляет текущий страйк (количество дней подряд выполнения привычки)"""
    if not completed_dates:
        return 0

    # Сортируем даты по убыванию (от новых к старым)
    sorted_dates = sorted(completed_dates, reverse=True)

    streak = 0
    expected_date = datetime.now().date()

    for date_str in sorted_dates:
        date = datetime.fromisoformat(date_str).date()

        if date == expected_date:
            streak += 1
            expected_date -= timedelta(days=1)
        elif date < expected_date:
            # Если пропущен день, прерываем подсчет
            break

    return streak

def build_progress_grid(user_data, user_tz):
    """Создает интерактивную шкалу прогресса в виде таблицы"""
    completed_dates = user_data.get("completed_dates", [])
    created_date_str = user_data.get("created_date")

    # Определяем начальную дату (дата создания привычки)
    if created_date_str:
        start_date = datetime.fromisoformat(created_date_str).date()
    else:
        # Если дата создания не указана, берем самую раннюю отметку или сегодня
        if completed_dates:
            start_date = min(datetime.fromisoformat(d).date() for d in completed_dates)
        else:
            start_date = datetime.now(user_tz).date()

    # Текущая дата
    today = datetime.now(user_tz).date()

    # Вычисляем количество дней с момента создания
    days_since_start = (today - start_date).days + 1

    # Ограничиваем отображение последними 21 днем (3 недели)
    display_days = min(days_since_start, 21)

    # Создаем массив дат для отображения
    dates_to_show = [start_date + timedelta(days=i) for i in range(days_since_start)]

    # Берем последние display_days дней
    dates_to_show = dates_to_show[-display_days:]

    # Создаем кнопки для таблицы
    keyboard = []

    # Разбиваем на строки по 7 дней (неделя)
    for week_start in range(0, len(dates_to_show), 7):
        week_dates = dates_to_show[week_start:week_start + 7]
        week_buttons = []

        for date in week_dates:
            date_str = date.isoformat()

            # Определяем символ для кнопки
            if date_str in completed_dates:
                symbol = "✅"
            elif date > today:
                symbol = "⬜"  # Будущие дни
            else:
                symbol = "❌"

            # Форматируем текст кнопки: день недели + число
            weekday_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
            weekday = weekday_names[date.weekday()]

            # Формат: День_недели число символ
            button_text = f"{weekday} {date.day} {symbol}"

            # Callback data содержит информацию о дате
            callback_data = f"progress_day_{date_str}"

            week_buttons.append(InlineKeyboardButton(button_text, callback_data=callback_data))

        keyboard.append(week_buttons)

    # Добавляем кнопку "Назад" для возврата к основному меню
    keyboard.append([InlineKeyboardButton("« Назад к меню", callback_data="progress_back")])

    return InlineKeyboardMarkup(keyboard)

# -------------------------------------------
# BACKGROUND REMINDER CHECKER
# -------------------------------------------
async def reminder_checker(app: Application):
    """Запускается каждые 60 секунд и проверяет напоминания с учетом часового пояса"""
    while True:
        for chat_id, data in app.user_data.items():
            if "time" in data and "habit_name" in data and "timezone" in data:
                try:
                    # Получаем текущее время в часовом поясе пользователя
                    user_tz = ZoneInfo(data["timezone"])
                    user_now = datetime.now(user_tz)
                    user_now_str = user_now.strftime("%H:%M")
                    today = user_now.date().isoformat()

                    # Проверяем, выполнена ли привычка сегодня
                    completed_dates = data.get("completed_dates", [])
                    is_already_done = today in completed_dates

                    # === ОСНОВНОЕ НАПОМИНАНИЕ (в заданное время) ===
                    if data["time"] == user_now_str:
                        # Проверяем, не отправляли ли мы уже напоминание В ЭТУ МИНУТУ
                        last_reminder_key = f"{today}_{user_now_str}"
                        if data.get("last_reminder_key") == last_reminder_key:
                            continue  # Уже отправляли напоминание в эту минуту сегодня

                        if is_already_done:
                            # Привычка уже выполнена - отправляем альтернативное сообщение
                            reminder_text = random.choice(REMINDER_ALREADY_DONE_TEMPLATES)

                            await app.bot.send_message(
                                chat_id=chat_id,
                                text=reminder_text,
                                parse_mode="HTML"
                            )
                        else:
                            # Привычка не выполнена - отправляем обычное напоминание
                            reminder_text = random.choice(REMINDER_TEMPLATES)
                            habit_name = data['habit_name']

                            # Формируем полное сообщение
                            full_message = f"{reminder_text}\n\n<b>Твоя привычка:</b> {habit_name}"

                            # Создаем inline-кнопку для отметки выполнения
                            done_button = InlineKeyboardMarkup([
                                [InlineKeyboardButton("Отметить выполненной", callback_data="habit_done")]
                            ])

                            await app.bot.send_message(
                                chat_id=chat_id,
                                text=full_message,
                                parse_mode="HTML",
                                reply_markup=done_button
                            )

                            # Сохраняем время первого напоминания для повторного через 2 часа
                            data["first_reminder_time"] = user_now.isoformat()
                            data["second_reminder_sent"] = False

                        # Сохраняем ключ отправки напоминания (дата + время)
                        data["last_reminder_key"] = last_reminder_key

                        logger.info(f"Отправлено напоминание для {chat_id} в {user_now_str} ({data['timezone']}), выполнено: {is_already_done}")

                    # === ПОВТОРНОЕ НАПОМИНАНИЕ (через 2 часа после первого) ===
                    if not is_already_done and "first_reminder_time" in data and not data.get("second_reminder_sent", False):
                        first_reminder_dt = datetime.fromisoformat(data["first_reminder_time"])

                        # Проверяем, прошло ли 2 часа с момента первого напоминания
                        time_diff = user_now - first_reminder_dt

                        # Если прошло 2 часа (с учетом погрешности в 1 минуту)
                        if timedelta(hours=2, minutes=0) <= time_diff <= timedelta(hours=2, minutes=1):
                            # Отправляем повторное напоминание
                            reminder_text = random.choice(SECOND_REMINDER_TEMPLATES)
                            habit_name = data['habit_name']

                            # Формируем полное сообщение
                            full_message = f"{reminder_text}\n\n<b>Твоя привычка:</b> {habit_name}"

                            # Создаем inline-кнопку для отметки выполнения
                            done_button = InlineKeyboardMarkup([
                                [InlineKeyboardButton("Отметить выполненной", callback_data="habit_done")]
                            ])

                            await app.bot.send_message(
                                chat_id=chat_id,
                                text=full_message,
                                parse_mode="HTML",
                                reply_markup=done_button
                            )

                            # Помечаем, что повторное напоминание отправлено
                            data["second_reminder_sent"] = True

                            logger.info(f"Отправлено повторное напоминание для {chat_id} через 2 часа")

                    # === ПРОВЕРКА ПРОПУЩЕННОГО ДНЯ (в 00:00 нового дня) ===
                    # Проверяем, что наступил новый день и вчера привычка не была выполнена
                    if user_now_str == "00:00":
                        # Получаем вчерашнюю дату
                        yesterday = (user_now.date() - timedelta(days=1)).isoformat()

                        # Проверяем, отправляли ли уже уведомление о пропуске для этого дня
                        missed_notification_key = f"missed_{yesterday}"
                        if data.get("last_missed_notification") == missed_notification_key:
                            continue  # Уже отправляли уведомление о пропуске для этого дня

                        # Проверяем, была ли выполнена привычка вчера
                        if yesterday not in completed_dates:
                            # Отправляем фото frame7
                            if os.path.exists(PHOTO_7):
                                try:
                                    with open(PHOTO_7, "rb") as f:
                                        await app.bot.send_photo(chat_id, InputFile(f))
                                except Exception as e:
                                    logger.warning(f"Error sending photo: {e}")

                            # Имитируем печать
                            try:
                                await app.bot.send_chat_action(chat_id, ChatAction.TYPING)
                            except:
                                pass
                            await asyncio.sleep(0.7)

                            # Выбираем случайный текст для пропущенного дня
                            missed_text = random.choice(MISSED_DAY_TEMPLATES)

                            await app.bot.send_message(
                                chat_id=chat_id,
                                text=missed_text,
                                parse_mode="HTML"
                            )

                            # Помечаем, что уведомление о пропуске отправлено
                            data["last_missed_notification"] = missed_notification_key

                            logger.info(f"Отправлено уведомление о пропущенном дне для {chat_id} за {yesterday}")

                except Exception as e:
                    logger.error(f"Ошибка при отправке напоминания для {chat_id}: {e}")

        await asyncio.sleep(60)

# -------------------------------------------
# HANDLERS
# -------------------------------------------
async def start(update: Update, context):
    chat_id = update.effective_chat.id
    text_1 = (
        "В очередной вечер, когда у тебя появляется свободная минута, ты начинаешь раздумывать над своей жизнью и в голове раздаётся мысль: "
        "«Нет, ну надо что-то менять в этой жизни». Ты решаешь поставить себе будильник на завтра на полчаса раньше, чем обычно…\n\n"
        "Хотя зачем на полчаса? От этого ведь не будет никакого смысла, никаких существенных изменений. "
        "А тебе надо кардинально изменить свою жизнь. Ты ставишь будильник на 2 часа раньше. Отлично, первый шаг сделан.\n\n"
        "Но достаточно ли этого для того, чтобы в твоей жизни что-то существенно изменилось?\n\n"
        "Конечно нет! Вдобавок к этому надо регулярно заниматься спортом, следить за питанием и за ежедневными рабочими задачами. "
        "И уже тогда будет идти прогресс. Но ведь понятное дело, что за 1 день его не будет видно, ведь так? Давай поставим себе срок 3 месяца.\n\n"
        "И вот он — момент истины. У тебя возникло чувство дежавю? Наверняка этот сценарий тебе уже до боли знаком?"
    )
    await safe_send_photo(context, chat_id, PHOTO_1)
    await type_and_send(context, chat_id, text_1, reply_markup=continue_reply)

async def handle_message(update: Update, context):
    if not update.message:
        return

    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    t = text.lower()

    # --- ПРИОРИТЕТ 1: Проверка изменения времени ---
    if context.user_data.get("waiting_for_time_change"):
        if t == "отмена":
            context.user_data["waiting_for_time_change"] = False
            await type_and_send(
                context,
                chat_id,
                "Изменение времени отменено.\n\nТвоё текущее время осталось без изменений.",
                reply_markup=progress_reply
            )
            return

        if not is_valid_time(text):
            await type_and_send(
                context,
                chat_id,
                "⏰ Время указано в неверном формате!\n\n"
                "Пожалуйста, введи время в формате <b>чч:мм</b>\n"
                "Например: 07:30 или 22:05\n\n"
                "Или напиши <b>отмена</b>, чтобы вернуться в меню.",
                parse_html=True
            )
            return

        context.user_data["waiting_for_time_change"] = False

        # Обновляем время в глобальных данных
        if chat_id in context.application.user_data:
            context.application.user_data[chat_id]["time"] = text

        await type_and_send(
            context,
            chat_id,
            f"Отлично! Время напоминания изменено на <b>{text}</b> ⏰\n\n"
            "Теперь я буду напоминать тебе в это время!",
            parse_html=True,
            reply_markup=progress_reply
        )
        return

    # --- ПРИОРИТЕТ 2: Подтверждение изменения времени ---
    if context.user_data.get("pending_time_change"):
        if t == "да, изменить время" or t == "хочу изменить время":
            context.user_data["pending_time_change"] = False
            context.user_data["waiting_for_time_change"] = True

            user_data = context.application.user_data.get(chat_id, {})

            await type_and_send(
                context,
                chat_id,
                f"Текущее время напоминания: <b>{user_data.get('time')}</b>\n\n"
                "Введи новое время в формате <b>чч:мм</b>\n"
                "Например: 07:30 или 22:05\n\n"
                "Или напиши <b>отмена</b>, чтобы вернуться.",
                parse_html=True,
                reply_markup=ReplyKeyboardRemove()
            )
            return
        elif t == "отмена":
            context.user_data["pending_time_change"] = False
            await type_and_send(
                context,
                chat_id,
                "Изменение времени отменено.\n\nВсё осталось по-прежнему.",
                reply_markup=progress_reply
            )
            return
        elif t == "почему лучше не менять время?":
            # Отправляем картинку
            await safe_send_photo(context, chat_id, PHOTO_6)

            # Показываем объяснение и возвращаем только 2 кнопки
            simple_choice_keyboard = ReplyKeyboardMarkup(
                [
                    [KeyboardButton("Хочу изменить время")],
                    [KeyboardButton("Отмена")],
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )

            await type_and_send(
                context,
                chat_id,
                "Смотри, дело не во мне — это твой мозг любит притворяться ленивцем.\n\n"
                "Если делать что-то в одно и то же время, он такой: «Ааа, понятно, это ритуал», — "
                "и включает автоматический режим. Если время скачет, мозг начинает паниковать и делать вид, что его сегодня «нет дома».\n\n"
                "Поэтому фиксированное время = привычка, которая сама себя толкает вперёд.",
                reply_markup=simple_choice_keyboard
            )
            return

    # --- Пользователь пишет свою привычку ---
    if context.user_data.get("waiting_for_custom_habit"):
        habit = text
        context.user_data["waiting_for_custom_habit"] = False

        # Проверяем, есть ли уже настроенная привычка (режим изменения)
        user_data = context.application.user_data.get(chat_id, {})
        is_changing_habit = "habit_name" in user_data and "time" in user_data

        if is_changing_habit:
            # Обновляем привычку, сохраняя текущие настройки
            context.application.user_data[chat_id]["habit_name"] = habit

            await type_and_send(
                context,
                chat_id,
                f"Отлично! Привычка изменена на: <b>{habit}</b>\n\n"
                f"Время напоминания осталось прежним: <b>{user_data.get('time')}</b>\n\n"
                "Продолжаем двигаться вперёд! 💪",
                parse_html=True,
                reply_markup=progress_reply
            )
        else:
            # Новая привычка - запрашиваем время
            context.user_data["habit_name"] = habit
            context.user_data["waiting_for_time"] = True

            # Клавиатура с кнопкой "Зачем это надо?"
            why_time_keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("Зачем это надо?")]],
                resize_keyboard=True,
                one_time_keyboard=False
            )

            await type_and_send(
                context,
                chat_id,
                f"Решено! Значит, берем привычку «{habit}». В какое время ты хочешь получать напоминания о привычке?\n\nНапиши в формате <b>чч:мм</b>",
                parse_html=True,
                reply_markup=why_time_keyboard
            )
        return

    # --- Пользователь вводит время ---
    elif context.user_data.get("waiting_for_time"):
        # Обработка кнопки "Зачем это надо?"
        if t == "зачем это надо?":
            # Отправляем картинку
            await safe_send_photo(context, chat_id, PHOTO_6)

            # Клавиатура с кнопкой "Понятно"
            understood_keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("Понятно")]],
                resize_keyboard=True,
                one_time_keyboard=True
            )

            await type_and_send(
                context,
                chat_id,
                "Смотри, дело не во мне — это твой мозг любит притворяться ленивцем.\n\n"
                "Если делать что-то в одно и то же время, он такой: «Ааа, понятно, это ритуал», — "
                "и включает автоматический режим. Если время скачет, мозг начинает паниковать и делать вид, что его сегодня «нет дома».\n\n"
                "Поэтому фиксированное время = привычка, которая сама себя толкает вперёд.",
                reply_markup=understood_keyboard
            )
            return

        # Обработка кнопки "Понятно"
        if t == "понятно":
            await type_and_send(
                context,
                chat_id,
                "Окей, договорились. Теперь шепни время в формате чч:мм — и запускаем магию момента.",
                reply_markup=ReplyKeyboardRemove()
            )
            return

        if not is_valid_time(text):
            why_time_keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("Зачем это надо?")]],
                resize_keyboard=True,
                one_time_keyboard=False
            )

            await type_and_send(
                context,
                chat_id,
                "⏰ Время указано в неверном формате!\n\n"
                "Пожалуйста, введи время в формате <b>чч:мм</b>\n"
                "Например: 07:30 или 22:05",
                parse_html=True,
                reply_markup=why_time_keyboard
            )
            return

        context.user_data["waiting_for_time"] = False
        context.user_data["reminder_time"] = text
        context.user_data["waiting_for_timezone"] = True

        await type_and_send(
            context,
            chat_id,
            f"Время схватил!\n\n"
            "Теперь давай город — так я пойму, где \"утро доброе\", а где ещё \"пять минут… пожалуйста\".\n\n"
            "Например: <b>Москва</b>, <b>Токио</b>, <b>Нью-Йорк</b>.",
            parse_html=True
        )
        return

    # --- Пользователь вводит часовой пояс (город) ---
    elif context.user_data.get("waiting_for_timezone"):
        city_input = text.strip().lower()

        # Ищем город в словаре
        timezone_str = CITY_TIMEZONES.get(city_input)

        if timezone_str:
            # Получаем текущее время в этом часовом поясе
            try:
                user_tz = ZoneInfo(timezone_str)
                current_time = datetime.now(user_tz).strftime("%H:%M")

                # Сохраняем временно часовой пояс
                context.user_data["temp_timezone"] = timezone_str
                context.user_data["waiting_for_timezone"] = False
                context.user_data["waiting_timezone_confirm"] = True

                await type_and_send(
                    context,
                    chat_id,
                    f"Так… подбираю твой часовой пояс.\n\n"
                    f"Чтобы всё сошлось, скажи: у тебя сейчас <b>{current_time}</b>?\n\n"
                    f"(Проверка: вдруг я уже живу в твоём будущем.)",
                    parse_html=True,
                    reply_markup=timezone_confirm_reply
                )
                return
            except Exception as e:
                logger.error(f"Ошибка при определении часового пояса: {e}")
                await type_and_send(
                    context,
                    chat_id,
                    "⚠️ Произошла ошибка при определении часового пояса. Попробуй еще раз."
                )
                return
        else:
            # Город не найден - предлагаем выбрать из списка
            # НЕ сбрасываем флаг waiting_for_timezone, чтобы пользователь мог попробовать ещё раз
            timezone_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(name, callback_data=f"tzidx_{idx}")]
                for idx, (name, tz) in enumerate(TIMEZONE_OPTIONS)
            ])

            await type_and_send(
                context,
                chat_id,
                f"🤔 Не смог найти город \"{text}\".\n\n"
                "Выбери свой часовой пояс из списка:",
                reply_markup=timezone_keyboard
            )
            return

    # --- Пользователь подтверждает часовой пояс ---
    elif context.user_data.get("waiting_timezone_confirm"):
        t_lower = text.lower()

        if t_lower == "да, всё верно":
            timezone_str = context.user_data.get("temp_timezone")
            if timezone_str:
                context.user_data["waiting_timezone_confirm"] = False

                habit = context.user_data.get("habit_name", "твоя привычка")
                reminder_time = context.user_data.get("reminder_time")

                # Сохраняем в глобальные данные приложения
                if chat_id not in context.application.user_data:
                    context.application.user_data[chat_id] = {}
                context.application.user_data[chat_id]["habit_name"] = habit
                context.application.user_data[chat_id]["time"] = reminder_time
                context.application.user_data[chat_id]["timezone"] = timezone_str
                context.application.user_data[chat_id]["completed_dates"] = []
                context.application.user_data[chat_id]["created_date"] = datetime.now(ZoneInfo(timezone_str)).date().isoformat()

                # Отправляем фото frame4
                await safe_send_photo(context, chat_id, PHOTO_4)

                # Отправляем финальное сообщение
                await type_and_send(
                    context,
                    chat_id,
                    f"Ура, мы настроились! Теперь наконец-то готовы стартовать. Давай закрепим, с чего мы с тобой начинаем:\n\n"
                    f"Привычка: <b>{habit}</b>\n"
                    f"Время: <b>{reminder_time}</b>\n"
                    f"Часовой пояс — понял, где ты живёшь (в хорошем смысле).\n\n"
                    f"Буду выскакивать каждый день в это время. Не пугайся.😈",
                    parse_html=True,
                    reply_markup=whats_next_reply
                )
            return

        elif t_lower == "выбрать другой часовой пояс":
            context.user_data["waiting_timezone_confirm"] = False

            # Показываем inline-клавиатуру с выбором часового пояса
            timezone_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(name, callback_data=f"tzidx_{idx}")]
                for idx, (name, tz) in enumerate(TIMEZONE_OPTIONS)
            ])

            await type_and_send(
                context,
                chat_id,
                "🌍 Выбери свой часовой пояс из списка:",
                reply_markup=timezone_keyboard
            )
            return

    # --- Стандартная логика ---
    # Проверка: "продолжить" работает только если бот еще не настроен
    if t == "продолжить":
        user_data = context.application.user_data.get(chat_id, {})

        # Если бот уже настроен - игнорируем "продолжить"
        if "habit_name" in user_data and "time" in user_data:
            await type_and_send(
                context,
                chat_id,
                "У тебя уже всё настроено! Используй меню для управления привычкой.",
                reply_markup=progress_reply
            )
            return

        # Сбрасываем все флаги состояния перед началом
        context.user_data.clear()

        # Бот не настроен - показываем второй экран
        await safe_send_photo(context, chat_id, PHOTO_2)
        await type_and_send(
            context,
            chat_id,
            "Если ты здесь, то это с вероятностью 99% значит, что я попал. "
            "Знаешь, что влияет на изменение всей нашей жизни? Момент принятия решения, момент осознания «мне надо», "
            "момент страха или твёрдой уверенности.\n\n"
            "Всего лишь один момент. Именно в этот момент рождается импульс — Моментум.\n\n"
            "Это я. Твоя энергия движения, собранная из тех самых мгновений, когда тебе хотелось \"начать\". "
            "Я не сборник с мотивирующими цитатами и не амбассадор токсичной продуктивности. "
            "Я — твой напарник. Я помогу тебе поймать импульс, удержать его и превратить в привычку.\n\n"
            "Меньше слов, больше дела! Предлагаю начать с малого. "
            "Выбери одну привычку, с которой мы начнём путь (не все сразу).\n\n"
            "При желании ты сможешь указать свою привычку и/или добавить вторую. Но я всё же советую тебе начать с одной!",
            reply_markup=second_reply,
        )
        return

    if t == "почему важно выбрать только 1 привычку?":
        await safe_send_photo(context, chat_id, PHOTO_3)
        await type_and_send(
            context,
            chat_id,
            "<b>Почему мы начинаем с одной привычки?</b>\n\n"
            "Потому что наш мозг — не суперкомпьютер, а скорее старая консоль. "
            "Если сразу загрузить в неё кучу модулей, всё зависнет. "
            "Когда ты выбираешь одну привычку и запускаешь её, ты сокращаешь сопротивление, делая старт лёгким. "
            "Эта лёгкость позволяет действию случаться чаще. "
            "А частота повторения = ускорение автоматизации.\n\n"
            "То есть:\n"
            "• Одна привычка → меньше отвлекающих дел → больше повторов;\n"
            "• Больше повторов → привычка «включается» автоматом;\n"
            "• Автоматизация = меньше усилий и больше свободы для следующей привычки.\n\n"
            "Выбери одну. Прокачаем её. А потом, когда она уже «рулит» — добавим следующую.\n\n"
            "(Да, всё просто. Но именно простота позволяет жить.)",
            parse_html=True,
            reply_markup=single_letsgo_reply)
        return

    if t == "отлично, приступим!":
        # Сбрасываем все флаги состояния перед выбором привычки
        context.user_data.clear()

        await type_and_send(context, chat_id, "Супер!", reply_markup=ReplyKeyboardRemove())
        await type_and_send(
            context,
            chat_id,
            "Так, давай без лишних лекций.\n\n"
            "Вот список привычек, с которых обычно начинают разумные люди (или те, кто пытается ими стать).\n\n"
            "Выбирай подходящую. Если твоя привычка не вписывается в стандартные рамки — просто напиши её. Я не осуждаю 🤝",
            reply_markup=habit_inline
        )
        return

    if t == "что дальше?":
        await safe_send_photo(context, chat_id, PHOTO_5)
        await type_and_send(
            context,
            chat_id,
            "Ах да… *подгружаю образ идеального бота…*\n\n"
            "Так, что там положено? Навигация, функции, удобства… Короче, слушай.\n\n"
            "У тебя теперь есть я — Моментум.\n\n"
            "Каждый день в выбранное время я буду аккуратно (ну, почти аккуратно) напоминать тебе о привычке. Тыкаешь кнопку — отмечается выполнение. Не тыкаешь — ну, я слегка вздохну, но не обижусь.\n\n"
            "Хочешь посмотреть свой прогресс? Жми в меню <b>\"Прогресс\"</b> — там твой страйк, дни, победы и вся статистика, от которой ты либо гордишься, либо включаешь боевую музыку.\n\n"
            "Надо сменить время привычки?\n\n"
            "Хочешь другую привычку?\n\n"
            "Добавить ещё одну?\n\n"
            "Всё это там же — в меню.\n\n"
            "И да, если вдруг почувствуешь вдохновение — я рядом, щёлкну тумблер и подгоню тебя дальше.",
            parse_html=True,
            reply_markup=progress_reply
        )
        return

    if t == "📊 прогресс":
        # Получаем данные пользователя
        user_data = context.application.user_data.get(chat_id, {})

        if "habit_name" not in user_data:
            await type_and_send(
                context,
                chat_id,
                "У тебя пока нет настроенной привычки. Набери /start, чтобы начать!",
                reply_markup=progress_reply
            )
            return

        habit_name = user_data.get("habit_name", "Неизвестная привычка")
        completed_dates = user_data.get("completed_dates", [])
        total_days = len(completed_dates)
        current_streak = calculate_streak(completed_dates)

        # Проверяем, выполнена ли привычка сегодня
        user_tz = ZoneInfo(user_data.get("timezone", "UTC"))
        today = datetime.now(user_tz).date().isoformat()
        done_today = today in completed_dates

        # Вычисляем процент выполнения
        created_date_str = user_data.get("created_date")
        if created_date_str:
            start_date = datetime.fromisoformat(created_date_str).date()
            today_date = datetime.now(user_tz).date()
            days_since_start = (today_date - start_date).days + 1
            if days_since_start > 0:
                completion_rate = int((total_days / days_since_start) * 100)
            else:
                completion_rate = 0
        else:
            completion_rate = 0

        # Формируем сообщение с прогрессом
        progress_message = (
            f"📊 <b>Твой прогресс</b>\n\n"
            f"Привычка: {habit_name}\n"
            f"Время: {user_data.get('time', 'не установлено')}\n\n"
            f"Страйк сейчас: {current_streak} {'день' if current_streak == 1 else 'дня' if 2 <= current_streak <= 4 else 'дней'} 🔥\n"
            f"Выполнено всего: {total_days} {'раз' if total_days == 1 else 'раза' if 2 <= total_days <= 4 else 'раз'}\n"
            f"Сегодня: {'отмечено ✅' if done_today else 'ещё не отмечено'}\n\n"
        )

        if current_streak >= 21:
            progress_message += "Три недели подряд! Привычка уже стала частью тебя. Это уже не сила воли — это образ жизни."
        elif current_streak >= 14:
            progress_message += "Две недели! Ритм установлен. Мозг начинает привыкать, что это — норма."
        elif current_streak >= 7:
            progress_message += "Неделя без пропусков! Продолжай — привычка начинает укореняться."
        elif current_streak >= 3:
            progress_message += "Три дня подряд — импульс набирает силу. Не останавливайся."
        elif current_streak >= 1:
            progress_message += "Кажется, импульс набирает скорость. Продолжаем."
        else:
            progress_message += "Начни сегодня — импульс ждёт первого шага."

        # Отправляем сообщение с прогрессом
        await type_and_send(context, chat_id, progress_message, parse_mode="HTML", reply_markup=progress_reply)
        return

    if t == "✅ отметить привычку":
        user_data = context.application.user_data.get(chat_id, {})

        if "habit_name" not in user_data:
            await type_and_send(
                context,
                chat_id,
                "У тебя пока нет настроенной привычки. Набери /start, чтобы начать!",
                reply_markup=progress_reply
            )
            return

        # Получаем часовой пояс пользователя
        user_tz = ZoneInfo(user_data.get("timezone", "UTC"))
        today = datetime.now(user_tz).date().isoformat()

        # Инициализируем список выполненных дат, если его нет
        if "completed_dates" not in user_data:
            user_data["completed_dates"] = []

        # Проверяем, не отметил ли пользователь уже сегодня
        if today in user_data["completed_dates"]:
            already_done_message = random.choice(ALREADY_DONE_TEMPLATES)
            await type_and_send(
                context,
                chat_id,
                already_done_message,
                reply_markup=progress_reply
            )
            return

        # Добавляем сегодняшнюю дату
        user_data["completed_dates"].append(today)

        # Сбрасываем флаги повторного напоминания
        if "first_reminder_time" in user_data:
            del user_data["first_reminder_time"]
        if "second_reminder_sent" in user_data:
            del user_data["second_reminder_sent"]

        # Вычисляем новый страйк
        current_streak = calculate_streak(user_data["completed_dates"])

        # Выбираем случайный шаблон для подтверждения
        done_message = random.choice(COMPLETION_TEMPLATES).format(streak=current_streak)

        # Добавляем дополнительное мотивационное сообщение для важных вех
        if current_streak == 3:
            done_message += "\n\n💪 Три дня подряд — это уже сила воли!"
        elif current_streak == 7:
            done_message += "\n\n🎉 Неделя! Ты просто машина!"
        elif current_streak == 14:
            done_message += "\n\n🚀 Две недели! Привычка уже становится частью тебя!"
        elif current_streak == 30:
            done_message += "\n\n🏆 МЕСЯЦ! Ты легенда!"
        elif current_streak == 21:
            done_message += "\n\n🌟 21 день! Говорят, привычка формируется именно за это время!"
        elif current_streak % 50 == 0:
            done_message += "\n\n🏅 Невероятно! Полтинник дней!"
        elif current_streak == 100:
            done_message += "\n\n👑 СТО ДНЕЙ! Ты абсолютная легенда!"

        await type_and_send(
            context,
            chat_id,
            done_message,
            parse_html=True,
            reply_markup=progress_reply
        )
        return

    if t == "⏰ изменить время":
        user_data = context.application.user_data.get(chat_id, {})

        if "habit_name" not in user_data:
            await type_and_send(
                context,
                chat_id,
                "У тебя пока нет настроенной привычки. Набери /start, чтобы начать!",
                reply_markup=progress_reply
            )
            return

        # Создаем клавиатуру с кнопками
        confirm_time_keyboard = ReplyKeyboardMarkup(
            [
                [KeyboardButton("Да, изменить время")],
                [KeyboardButton("Отмена")],
                [KeyboardButton("Почему лучше не менять время?")],
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        context.user_data["pending_time_change"] = True

        # Выбираем случайное сообщение
        confirmation_message = random.choice(TIME_CHANGE_CONFIRMATION_TEMPLATES)

        await type_and_send(
            context,
            chat_id,
            f"Текущее время напоминания: <b>{user_data.get('time')}</b>\n\n"
            f"{confirmation_message}",
            parse_html=True,
            reply_markup=confirm_time_keyboard
        )
        return

    if t == "🔄 изменить привычку":
        user_data = context.application.user_data.get(chat_id, {})

        if "habit_name" not in user_data:
            await type_and_send(
                context,
                chat_id,
                "У тебя пока нет настроенной привычки. Набери /start, чтобы начать!",
                reply_markup=progress_reply
            )
            return

        await type_and_send(
            context,
            chat_id,
            f"Текущая привычка: <b>{user_data.get('habit_name')}</b>\n\n"
            "Выбери новую привычку:",
            parse_html=True,
            reply_markup=habit_inline
        )
        return

    if t == "➕ добавить привычку":
        await type_and_send(
            context,
            chat_id,
            "Функция добавления дополнительных привычек пока в разработке 🛠\n\n"
            "Скоро ты сможешь отслеживать несколько привычек одновременно!",
            reply_markup=progress_reply
        )
        return

    await type_and_send(context, chat_id, "Набери /start, чтобы начать заново.")

async def handle_callback_query(update: Update, context):
    q = update.callback_query
    chat_id = q.message.chat.id
    await q.answer()

    # === ОБРАБОТКА КНОПОК ШКАЛЫ ПРОГРЕССА ===
    if q.data == "progress_back":
        # Возвращаемся к основному меню
        await q.message.delete()
        await type_and_send(
            context,
            chat_id,
            "Возвращаюсь в меню...",
            reply_markup=progress_reply
        )
        return

    if q.data.startswith("progress_day_"):
        # Нажатие на конкретный день в шкале прогресса
        date_str = q.data.replace("progress_day_", "")
        user_data = context.application.user_data.get(chat_id, {})
        user_tz = ZoneInfo(user_data.get("timezone", "UTC"))

        try:
            clicked_date = datetime.fromisoformat(date_str).date()
            today = datetime.now(user_tz).date()

            # Форматируем дату для отображения
            month_names = [
                "января", "февраля", "марта", "апреля", "мая", "июня",
                "июля", "августа", "сентября", "октября", "ноября", "декабря"
            ]
            weekday_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

            weekday = weekday_names[clicked_date.weekday()]
            month = month_names[clicked_date.month - 1]
            date_formatted = f"{weekday}, {clicked_date.day} {month}"

            completed_dates = user_data.get("completed_dates", [])

            if date_str in completed_dates:
                status = "✅ Выполнено"
            elif clicked_date > today:
                status = "⬜ Будущий день"
            else:
                status = "❌ Пропущено"

            await q.answer(f"{date_formatted}\n{status}", show_alert=True)

        except Exception as e:
            logger.error(f"Ошибка при обработке клика на дату: {e}")
            await q.answer("Ошибка при обработке даты", show_alert=True)
        return

    # === ОБРАБОТКА КНОПКИ "ВЫПОЛНЕНО" ===
    if q.data == "habit_done":
        user_data = context.application.user_data.get(chat_id, {})

        if "habit_name" not in user_data:
            await q.answer("Привычка не найдена", show_alert=True)
            return

        # Получаем часовой пояс пользователя
        user_tz = ZoneInfo(user_data.get("timezone", "UTC"))
        today = datetime.now(user_tz).date().isoformat()

        # Инициализируем список выполненных дат, если его нет
        if "completed_dates" not in user_data:
            user_data["completed_dates"] = []

        # Проверяем, не отметил ли пользователь уже сегодня
        if today in user_data["completed_dates"]:
            already_done_message = random.choice(ALREADY_DONE_TEMPLATES)
            await q.answer(already_done_message, show_alert=True)
            return

        # Добавляем сегодняшнюю дату
        user_data["completed_dates"].append(today)

        # Сбрасываем флаги повторного напоминания
        if "first_reminder_time" in user_data:
            del user_data["first_reminder_time"]
        if "second_reminder_sent" in user_data:
            del user_data["second_reminder_sent"]

        # Вычисляем новый страйк
        current_streak = calculate_streak(user_data["completed_dates"])

        # Выбираем случайный шаблон для подтверждения
        done_message = random.choice(COMPLETION_TEMPLATES).format(streak=current_streak)

        # Добавляем дополнительное мотивационное сообщение для важных вех
        if current_streak == 3:
            done_message += "\n\n💪 Три дня подряд — это уже сила воли!"
        elif current_streak == 7:
            done_message += "\n\n🎉 Неделя! Ты просто машина!"
        elif current_streak == 14:
            done_message += "\n\n🚀 Две недели! Привычка уже становится частью тебя!"
        elif current_streak == 30:
            done_message += "\n\n🏆 МЕСЯЦ! Ты легенда!"
        elif current_streak == 21:
            done_message += "\n\n🌟 21 день! Говорят, привычка формируется именно за это время!"
        elif current_streak % 50 == 0:
            done_message += "\n\n🏅 Невероятно! Полтинник дней!"
        elif current_streak == 100:
            done_message += "\n\n👑 СТО ДНЕЙ! Ты абсолютная легенда!"

        try:
            await q.edit_message_text(
                text=done_message,
                parse_mode="HTML"
            )
        except:
            # Если не удалось отредактировать, отправляем новое сообщение
            await context.bot.send_message(
                chat_id=chat_id,
                text=done_message,
                parse_mode="HTML"
            )

        await q.answer("Записано! 🎉")
        return

    # === ОБРАБОТКА ВЫБОРА КОНКРЕТНОГО ЧАСОВОГО ПОЯСА ===
    if q.data.startswith("tzidx_"):
        try:
            idx = int(q.data.split("_")[1])
            if 0 <= idx < len(TIMEZONE_OPTIONS):
                timezone_str = TIMEZONE_OPTIONS[idx][1]

                user_tz = ZoneInfo(timezone_str)
                current_time = datetime.now(user_tz).strftime("%H:%M")

                # Сохраняем временно для подтверждения
                context.user_data["temp_timezone"] = timezone_str
                context.user_data["waiting_timezone_confirm"] = True

                await type_and_send(
                    context,
                    chat_id,
                    f"Проверяем...\n\nУ тебя сейчас <b>{current_time}</b>?",
                    parse_html=True,
                    reply_markup=timezone_confirm_reply
                )
        except Exception as e:
            logger.error(f"Ошибка при выборе часового пояса: {e}")
            await q.answer("Ошибка при выборе часового пояса", show_alert=True)
        return

    # === ОБРАБОТКА ВЫБОРА ПРИВЫЧКИ ===
    if q.data == "habit_more":
        await q.edit_message_reply_markup(InlineKeyboardMarkup([
            [InlineKeyboardButton("👟 Прогуляться полчаса", callback_data="habit_walk")],
            [InlineKeyboardButton("💰 Внести расходы за день", callback_data="habit_expenses")],
            [InlineKeyboardButton("✍🏻 Заполнить дневник благодарности", callback_data="habit_journal")],
            [InlineKeyboardButton("📅 Распланировать завтрашний день", callback_data="habit_plan")],
            [InlineKeyboardButton("🚿 Принять контрастный душ", callback_data="habit_shower")],
            [InlineKeyboardButton("📌 Определить приоритет на день", callback_data="habit_priority")],
            [InlineKeyboardButton("🧹 Разобрать 1 участок бардака", callback_data="habit_cleanup")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="habit_back")],
        ]))
        return

    if q.data == "habit_back":
        await q.edit_message_reply_markup(habit_inline)
        return

    if q.data == "habit_custom":
        context.user_data["waiting_for_custom_habit"] = True
        await type_and_send(
            context,
            chat_id,
            "Обожаю кастомные запросы! Пиши свою привычку)\n\n"
            "Формат: маленькое действие, большой смысл. (например: \"Проверить баланс карты и не заплакать\")\n\n"
            "Только не пиши \"Стать идеальным человеком\" - я пока не настолько прокачан🫣"
        )
        return

    # Проверяем, есть ли уже настроенная привычка (режим изменения)
    user_data = context.application.user_data.get(chat_id, {})
    is_changing_habit = "habit_name" in user_data and "time" in user_data

    habit = HABIT_NAMES[q.data]

    if is_changing_habit:
        # Обновляем привычку, сохраняя текущие настройки
        context.application.user_data[chat_id]["habit_name"] = habit

        await type_and_send(
            context,
            chat_id,
            f"Отлично! Привычка изменена на: <b>{habit}</b>\n\n"
            f"Время напоминания осталось прежним: <b>{user_data.get('time')}</b>\n\n"
            "Продолжаем двигаться вперёд! 💪",
            parse_html=True,
            reply_markup=progress_reply
        )
    else:
        # Новая привычка - запрашиваем время
        context.user_data["habit_name"] = habit
        context.user_data["waiting_for_time"] = True

        # Клавиатура с кнопкой "Зачем это надо?"
        why_time_keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("Зачем это надо?")]],
            resize_keyboard=True,
            one_time_keyboard=False
        )

        await type_and_send(
            context,
            chat_id,
            f"Решено! Значит, берем привычку «{habit}». В какое время ты хочешь получать напоминания о привычке? \n\n"
            f"Напиши в формате <b>чч:мм</b>",
            parse_html=True,
            reply_markup=why_time_keyboard
        )

# -------------------------------------------
# MAIN
# -------------------------------------------
async def post_init(app: Application):
    """Запускается после инициализации приложения"""
    await asyncio.sleep(1)  # Даем время на инициализацию бота
    asyncio.create_task(reminder_checker(app))
    logger.info("Фоновая проверка напоминаний запущена")

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    logger.info("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
