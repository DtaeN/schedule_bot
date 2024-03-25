import asyncio
import logging

from aiocron import crontab
import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from api import Dispatcher_DSTU

from db import *

from settings import TOKEN


logging.basicConfig(level=logging.INFO)
bot = Bot(TOKEN)
dp = Dispatcher()

disp = Dispatcher_DSTU()

listener_teacher_name = {}


async def _auto_sending(_day, day):
    type_week = 1 if datetime.date.today().isocalendar()[1] % 2 == 0 else 2
    for _user in all_users():
        if _user['auto_sending'] == 0 or None:
            pass
        elif _user['auto_sending'] == 1:
            await bot.send_message(chat_id=_user['user_id'], text=_schedule(_user['user_id'], _day, day, type_week))


# формат:  МИНУТЫ  ЧАСЫ  ДЕНЬ(В_МЕСЯЦЕ)  МЕСЯЦ  ДЕНЬ_НЕДЕЛИ
@crontab("0 20 * * *")
async def schedule_auto_sending():
    match datetime.datetime.now().weekday():
        case 0:
            await _auto_sending("Tuesday", "Вторник")
        case 1:
            await _auto_sending("Wednesday", "Среда")
        case 2:
            await _auto_sending("Wednesday", "Четверг")
        case 3:
            await _auto_sending("Friday", "Пятница")
        case 4:
            await _auto_sending("Saturday", "Суббота")
        case 6:
            await _auto_sending("Monday", "Понедельник")
        case _:
            pass


@dp.message(Command("start"))
async def message_start(message: types.Message):
    buttons = [
        [
            types.InlineKeyboardButton(text="Преподаватель", callback_data="teacher"),
            types.InlineKeyboardButton(text="Студент", callback_data="student")
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        f"Добро пожаловать {message.from_user.first_name}! Чьё расписание вы хотите посмотреть?",
        reply_markup=keyboard)


@dp.callback_query(F.data == "teacher")
async def teacher(callback: types.CallbackQuery):
    listener_teacher_name[callback.from_user.id] = True
    await callback.message.edit_text("Введите фамилию преподавателя:")
    await callback.answer()


@dp.message(F.text)
async def listener(message: types.Message):
    try:
        if listener_teacher_name[message.from_user.id] is True:
            buttons = []

            teachers = disp.search_teacher(message.text).items()

            if teachers is not None:
                for _id, name in teachers:
                    buttons.append([types.InlineKeyboardButton(
                            text=f"{_id} - {name}", callback_data=f"teacher_{_id}"
                        )])

                keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
                await message.answer("Выберите преподавателя:", reply_markup=keyboard)
            else:
                buttons = [
                    [
                        types.InlineKeyboardButton(text="Преподаватель", callback_data="teacher"),
                        types.InlineKeyboardButton(text="Студент", callback_data="student")
                    ]
                ]
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

                await message.answer("Преподаватель не найден", reply_markup=keyboard)

            listener_teacher_name[message.from_user.id] = False
    except KeyError:
        pass


@dp.callback_query(F.data.startswith("teacher_"))
async def callbacks_teacher(callback: types.CallbackQuery):
    if user_one(callback.from_user.id) is None:
        create_user(callback.from_user.id, int(callback.data.split('_')[1]), 2)
    else:
        edit_schedule_id(callback.from_user.id, int(callback.data.split('_')[1]), 2)

    buttons1 = [
        [
            types.InlineKeyboardButton(text="Понедельник", callback_data="call_monday"),
            types.InlineKeyboardButton(text="Вторник", callback_data="call_tuesday")
        ],
        [
            types.InlineKeyboardButton(text="Среда", callback_data="call_wednesday"),
            types.InlineKeyboardButton(text="Четверг", callback_data="call_thursday")
        ],
        [
            types.InlineKeyboardButton(text="Пятница", callback_data="call_friday"),
            types.InlineKeyboardButton(text="Суббота", callback_data="call_saturday")
        ],
        [types.InlineKeyboardButton(text="⚙️️️ Настройки", callback_data="call_settings")]
    ]

    keyboard1 = types.InlineKeyboardMarkup(inline_keyboard=buttons1)

    await callback.message.edit_text(
        f"Вы можете изменить расписание в настройках,"
        f"также в настройках вы можете настроить авто рассылку.",
        reply_markup=keyboard1)

    buttons2 = [
        [
            types.InlineKeyboardButton(text="Да", callback_data="auto_sending_on"),
            types.InlineKeyboardButton(text="Нет", callback_data="auto_sending_off"),
        ]
    ]

    keyboard2 = types.InlineKeyboardMarkup(inline_keyboard=buttons2)

    await callback.message.answer(
        "Хотите включить автоматическую рассылку расписания?", reply_markup=keyboard2)
    await callback.answer()


@dp.callback_query(F.data == "student")
async def student(callback: types.CallbackQuery):
    buttons = [
        [
            types.InlineKeyboardButton(text="1 курс", callback_data="course_k1"),
            types.InlineKeyboardButton(text="2 курс", callback_data="course_k2"),
        ],
        [
            types.InlineKeyboardButton(text="3 курс", callback_data="course_k3"),
            types.InlineKeyboardButton(text="4 курс", callback_data="course_k4"),
        ],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer(
        f"Выберите свой курс",
        reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data.startswith("course_"))
async def callbacks_course(callback: types.CallbackQuery):
    groups = disp.find_groups_by_course(callback.data[-1])

    keyboard = InlineKeyboardBuilder()
    for group in groups:
        keyboard.add(
            types.InlineKeyboardButton(
                text=f"{group.name}", callback_data=f"group_{group.id}"
            )
        )
    keyboard.adjust(3)

    await callback.message.edit_text(
        "Выберите свою группу", reply_markup=keyboard.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("group_"))
async def callbacks_groups(callback: types.CallbackQuery):
    if user_one(callback.from_user.id) is None:
        create_user(callback.from_user.id, int(callback.data.split('_')[1]), 1)
    else:
        edit_schedule_id(callback.from_user.id, int(callback.data.split('_')[1]), 1)

    buttons1 = [
        [
            types.InlineKeyboardButton(text="Понедельник", callback_data="call_monday"),
            types.InlineKeyboardButton(text="Вторник", callback_data="call_tuesday")
        ],
        [
            types.InlineKeyboardButton(text="Среда", callback_data="call_wednesday"),
            types.InlineKeyboardButton(text="Четверг", callback_data="call_thursday")
        ],
        [
            types.InlineKeyboardButton(text="Пятница", callback_data="call_friday"),
            types.InlineKeyboardButton(text="Суббота", callback_data="call_saturday")
        ],
        [types.InlineKeyboardButton(text="⚙️️️ Настройки", callback_data="call_settings")],
    ]

    keyboard1 = types.InlineKeyboardMarkup(inline_keyboard=buttons1)

    await callback.message.edit_text(f"Вы можете изменить расписание в настройках, "
                                     f"также в настройках вы можете настроить авто рассылку.",
                                     reply_markup=keyboard1)

    buttons2 = [
        [
            types.InlineKeyboardButton(text="Да", callback_data="auto_sending_on"),
            types.InlineKeyboardButton(text="Нет", callback_data="auto_sending_off"),
        ]
    ]

    keyboard2 = types.InlineKeyboardMarkup(inline_keyboard=buttons2)

    await callback.message.answer(
        "Хотите включить автоматическую рассылку расписания?", reply_markup=keyboard2)
    await callback.answer()


@dp.callback_query(F.data.startswith("auto_sending_"))
async def callbacks_auto_sending(callback: types.CallbackQuery):
    if callback.data.split("_")[2] == "on":
        auto_sending(callback.from_user.id, True)
        await callback.message.edit_text("Рассылка успешно включена")
    elif callback.data.split("_")[2] == "off":
        auto_sending(callback.from_user.id, False)
        await callback.message.edit_text("Рассылка успешно выключена")
    await callback.answer()


@dp.callback_query(F.data == "call_settings")
async def call_settings(callback: types.CallbackQuery):
    _user = user_one(callback.from_user.id)
    if _user is None:
        await callback.message.answer("Сначала, пожалуйста, выберите группу, "
                                      "для этого используйте команду /start")
    else:
        buttons = [
            [
                types.InlineKeyboardButton(text="Авто рассылка", callback_data="switch_auto-sending"),
                types.InlineKeyboardButton(text="Выбор расписания", callback_data="switch_schedule"),
            ]
        ]

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

        await callback.message.answer("⚙️ Настройки:", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data.startswith("switch_"))
async def callbacks_auto_sending(callback: types.CallbackQuery):
    if callback.data.split('_')[1] == 'auto-sending':

        buttons = [
            [
                types.InlineKeyboardButton(text="Включить", callback_data="sw_auto-sending_on"),
                types.InlineKeyboardButton(text="Выключить", callback_data="sw_auto-sending_off"),
            ]
        ]

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

        _user = user_one(callback.from_user.id)
        await callback.message.edit_text(f"В данный момент авто рассылка "
                                         f"{'включена' if _user['auto_sending'] == 1 else 'выключена'}",
                                         reply_markup=keyboard)

    elif callback.data.split('_')[1] == 'schedule':
        buttons = [
            [
                types.InlineKeyboardButton(text="Преподаватель", callback_data="teacher"),
                types.InlineKeyboardButton(text="Студент", callback_data="student")
            ]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

        await callback.message.answer(
            f"Чьё расписание вы хотите посмотреть?",
            reply_markup=keyboard,
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("sw_"))
async def callbacks_sw(callback: types.CallbackQuery):
    if callback.data.split('_')[1] == 'auto-sending':
        if callback.data.split('_')[2] == 'on':
            auto_sending(callback.from_user.id, True)
            await callback.message.edit_text("Авто рассылка успешно включина")
        elif callback.data.split('_')[2] == 'off':
            auto_sending(callback.from_user.id, False)
            await callback.message.edit_text("Авто рассылка успешно выключина")
    elif callback.data.split('_')[1] == 'group':
        edit_schedule_id(callback.from_user.id, int(callback.data.split('_')[2]), 1)
        await callback.message.edit_text(f"Группа успешна изменина на "
                                         f"{disp.find_group(int(callback.data.split('_')[2])).name}")
    await callback.answer()


@dp.callback_query(F.data.startswith("call_"))
async def callbacks_groups(callback: types.CallbackQuery):
    type_week = 1 if datetime.date.today().isocalendar()[1] % 2 == 0 else 2
    match callback.data.split('_')[1]:
        case 'monday':
            await callback.message.answer(_schedule(callback.from_user.id,
                                                    "Monday", "Понедельник", type_week),
                                          reply_markup=menu_button(type_week))
            await callback.answer()
        case 'tuesday':
            await callback.message.answer(_schedule(callback.from_user.id,
                                                    "Tuesday", "Вторник", type_week),
                                          reply_markup=menu_button(type_week))
            await callback.answer()
        case 'wednesday':
            await callback.message.answer(_schedule(callback.from_user.id,
                                                    "Wednesday", "Среда", type_week),
                                          reply_markup=menu_button(type_week))
            await callback.answer()
        case 'thursday':
            await callback.message.answer(_schedule(callback.from_user.id,
                                                    "Thursday", "Четверг", type_week),
                                          reply_markup=menu_button(type_week))
            await callback.answer()
        case 'friday':
            await callback.message.answer(_schedule(callback.from_user.id,
                                                    "Friday", "Пятница", type_week),
                                          reply_markup=menu_button(type_week))
            await callback.answer()
        case 'saturday':
            await callback.message.answer(_schedule(callback.from_user.id,
                                                    "Saturday", "Суббота", type_week),
                                          reply_markup=menu_button(type_week))
            await callback.answer()


def menu_button(type_week):
    buttons = [
        [
            types.InlineKeyboardButton(text="Показать верхнюю неделю",
                                       callback_data="menu_button_week_up")
            if type_week == 2
            else types.InlineKeyboardButton(text="Показать нижнюю неделю",
                                            callback_data="menu_button_week_down")
        ],
        [types.InlineKeyboardButton(text="⬇️ Все комманды", callback_data="button_menu")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


def all_commands_button(type_week):
    buttons = [
        [
            types.InlineKeyboardButton(text="Показать верхнюю неделю",
                                       callback_data="all_commands_button_week_up")
            if type_week == 2
            else types.InlineKeyboardButton(text="Показать нижнюю неделю",
                                            callback_data="all_commands_button_week_down")
        ],
        [
            types.InlineKeyboardButton(text="Понедельник", callback_data="call_monday"),
            types.InlineKeyboardButton(text="Вторник", callback_data="call_tuesday")
        ],
        [
            types.InlineKeyboardButton(text="Среда", callback_data="call_wednesday"),
            types.InlineKeyboardButton(text="Четверг", callback_data="call_thursday")
        ],
        [
            types.InlineKeyboardButton(text="Пятница", callback_data="call_friday"),
            types.InlineKeyboardButton(text="Суббота", callback_data="call_saturday")
        ],
        [types.InlineKeyboardButton(text="⚙️️️ Настройки", callback_data="call_settings")],
        [types.InlineKeyboardButton(text="️️️️⬆️ Свернуть", callback_data="menu_button")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.callback_query(F.data == "button_menu")
async def call_button_menu(callback: types.CallbackQuery):
    type_week = 1 if datetime.date.today().isocalendar()[1] % 2 == 0 else 2
    await callback.message.edit_text(text=callback.message.text, reply_markup=all_commands_button(type_week))
    await callback.answer()


@dp.callback_query(F.data == "menu_button")
async def call_menu_button(callback: types.CallbackQuery):
    type_week = 1 if datetime.date.today().isocalendar()[1] % 2 == 0 else 2
    await callback.message.edit_text(text=callback.message.text, reply_markup=menu_button(type_week))
    await callback.answer()


def switch_schedule(day, user_id, type_week):
    match day:
        case 'Понедельник':
            return _schedule(user_id, "Monday", "Понедельник", type_week)
        case 'Вторник':
            return _schedule(user_id, "Tuesday", "Вторник", type_week)
        case 'Среда':
            return _schedule(user_id, "Wednesday", "Среда", type_week)
        case 'Четверг':
            return _schedule(user_id, "Thursday", "Четверг", type_week)
        case 'Пятница':
            return _schedule(user_id, "Friday", "Пятница", type_week)
        case 'Суббота':
            return _schedule(user_id, "Saturday", "Суббота", type_week)


@dp.callback_query(F.data.startswith("menu_button_week_"))
async def menu_button_week(callback: types.CallbackQuery):
    if callback.data.split("_")[3] == "up":
        await callback.message.edit_text(
            text=switch_schedule(callback.message.text.split(' ')[1], callback.from_user.id, 1),
            reply_markup=menu_button(1))
    elif callback.data.split("_")[3] == "down":
        await callback.message.edit_text(
            text=switch_schedule(callback.message.text.split(' ')[1], callback.from_user.id, 2),
            reply_markup=menu_button(2))
    
    await callback.answer()


@dp.callback_query(F.data.startswith("all_commands_button_week_"))
async def all_commands_button_week(callback: types.CallbackQuery):
    if callback.data.split("_")[4] == "up":
        await callback.message.edit_text(
            text=switch_schedule(callback.message.text.split(' ')[1], callback.from_user.id, 1),
            reply_markup=all_commands_button(1))
    elif callback.data.split("_")[4] == "down":
        await callback.message.edit_text(
            text=switch_schedule(callback.message.text.split(' ')[1], callback.from_user.id, 2),
            reply_markup=all_commands_button(2))
        
    await callback.answer()


def _schedule(user_id, _weekday, weekday, type_week):
    _user = user_one(user_id)
    if _user is None:
        return (
            "Сначала, пожалуйста, выберите группу, "
            "для этого используйте команду /start"
        )
    else:
        if _user["user_type"] == 1:
            return disp.find_group_schedule_by_day(
                _user["schedule_id"], _weekday, weekday, type_week)
        else:
            return disp.find_teacher_schedule_by_day(
                _user["schedule_id"], _weekday, weekday, type_week)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    #create_table()

    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()

    asyncio.get_event_loop().run_forever()
