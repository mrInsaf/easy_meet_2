import os
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from dateutil.parser import parse
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.callback_data import CallbackData
import asyncio
import logging
from geo_api import get_coordinates_by_address, get_data_by_coordinates, get_map_by_coordinates
from db import db_add_group, db_create_user, check_user_in_group, user_exist, get_chat_id_by_username, \
    add_user_to_group, see_group_list, update_departure
import db_real
from weather import get_weather_by_coordinates
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram_calendar import simple_cal_callback, SimpleCalendar, dialog_cal_callback, DialogCalendar
import datetime
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import PhotoSize


class CreateGroupState(StatesGroup):
    date = State()
    time = State()
    address = State()
    coordinates = State()
    db_push = State()


class StartState(StatesGroup):
    start_menu = State()


class CreateTripState(StatesGroup):
    invitor = State()
    group_id = State()
    departure = State()
    transport_type = State()


class AddUserState(StatesGroup):
    get_group_id = State()
    get_username = State()
    add_user = State()


storage = MemoryStorage()
FORMAT = '%(asctime)s - [%(levelname)s] -  %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

TOKEN = '6234694339:AAFV3O4emFYQmIxD307xvDw9Kde5rpb8OH0'
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=["start"])
async def start_command(massage: types.Message, state: FSMContext):
    try:
        db_real.create_user(massage.from_user.id, massage.from_user.username, massage.from_user.first_name,
                            massage.from_user.last_name)
    except Exception as ex:
        logger.warning(ex)
    finally:
        await massage.reply(
            f"Привет, {massage.from_user.first_name}, я EasyMeet.\nПопробуй команду /help чтобы посмотреть на что я способен.")

    kb = InlineKeyboardMarkup()
    buttons = [InlineKeyboardButton(text='Создать встречу', callback_data='create_group'),
               InlineKeyboardButton(text='Присоединиться к встрече', callback_data='join_group')]

    your_groups = db_real.select(
        f'select * from groups where owner_id = {massage.from_user.id} and meet_time >= date()')
    if len(your_groups):
        buttons.append(InlineKeyboardButton(text='Пригласить на встречу', callback_data='invite_user'))
    kb.add(*buttons)
    await massage.reply(text='Выберите желаемое действие', reply_markup=kb)
    await StartState.start_menu.set()


@dp.callback_query_handler(state=StartState.start_menu)
async def start_processing(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'create_group':
        await CreateGroupState.date.set()
        await input_date(callback.message)
    if callback.data == 'invite_user':
        kb = InlineKeyboardMarkup(row_width=1)
        time_dest = db_real.select(
            f'select id, meet_time, destination from groups where owner_id = {callback.from_user.id} and meet_time >= date() order by id')
        buttons = [InlineKeyboardButton(text=str(td[0]) + ' | ' + str(td[1]) + ' | ' + str(td[2]),
                                        callback_data=f'Пользователь выбрал группу {td[0]}')
                   for td in time_dest]
        kb.add(*buttons)
        await bot.send_message(chat_id=callback.from_user.id,
                               text='Выберите поездку, в котопрую хотите добавить пользователя', reply_markup=kb)
        await AddUserState.get_group_id.set()
    if callback.data == 'join_group':
        await CreateTripState.invitor.set()
        await bot.send_message(chat_id=callback.from_user.id, text='Введите ID группы: ')


@dp.message_handler(commands=["help"])
async def help_command(massage: types.Message):
    help_data = "/create_group [дата] [время] [адрес] - создать группу поездки. Бот вернёт id группы\n" \
                "/change_group_date [дата] - изменить дату встречи\n" \
                "/change_group_time [время] - изменить время встречи\n" \
                "/change_group_address [адрес] - изменить адрес встречи\n" \
                "/add_user_to_group [id группы] [username] - добавить пользователя в группу\n" \
                "/delete_user_from_group [id группы] [username] - удалить пользователя из группы\n" \
                "/ask_to_join_group [id группы] - попросить присоединиться к группе\n" \
                "/leave_group [id группы] - покинуть группу\n" \
                "/get_group_list [id группы] - посмотреть участников группы\n" \
                "/add_departure [id группы] [адрес] - задать место отправления для пользователя в группе\n" \
                "/get_meet_data [id группы] - посомтреть информацию по поездке\n" \
                "/change_departure [id группы] [адрес] - измениить место отправления для пользователя в группе\n" \
                "/notice_me [id группы] [количество минут] - попросить бота напомнить о поездке за определённое количтво минут\n" \
                "/get_weather [адрес] - текущий прогноз погоды по адресу\n" \
                "/get_weather [id группы] - текущий прогноз погоды по адресу встречи\n"
    await bot.send_message(massage.from_user.id, help_data)


@dp.message_handler(state=CreateTripState.invitor)
async def ask_to_add_user_to_group(message: Message, state: FSMContext):
    group_id = message.text
    if not db_real.check_group_by_id(message.text):
        await message.reply('Группы с таким ID нет, попробуйте еще раз')
    else:
        if not db_real.check_user_in_group(group_id, message.from_user.username):
            owner_id = db_real.select(f'select owner_id from groups where id = {group_id}')[0][0]
            await state.update_data(invitor=owner_id)
            await bot.send_message(message.from_user.id,
                                   f'Отправил запрос на вступление в мероприятие {group_id}')
            keyboard = types.InlineKeyboardMarkup()
            accept = types.InlineKeyboardButton(text='Принять', callback_data="user accept join to group")
            decline = types.InlineKeyboardButton(text='Отказаться', callback_data="user decline join to group")
            keyboard.add(accept, decline)
            await bot.send_message(owner_id,
                                   f"Пользователь {message.from_user.username} хочет вступить в группу {group_id}",
                                   reply_markup=keyboard)
            await CreateTripState.group_id.set()
        else:
            await bot.send_message(message.from_user.id,
                                   f'Вы уже состоите в мероприятии {group_id}')


async def invite_user_to_join_group(group_id, my_username, invite_username):
    keyboard = types.InlineKeyboardMarkup()
    menu_1 = types.InlineKeyboardButton(text='Присоединиться', callback_data="user accept invite to group")
    menu_2 = types.InlineKeyboardButton(text='Отказаться', callback_data="user decline invite to group")
    keyboard.add(menu_1, menu_2)
    chat_id = db_real.get_chat_id_by_username(invite_username)
    await bot.send_message(db_real.get_chat_id_by_username(my_username),
                           f'Отправил приглашение на вступление в мероприятие {group_id} пользователю {invite_username}')
    await bot.send_message(chat_id, f"Пользователь {my_username} пригласил вас в группу {group_id}",
                           reply_markup=keyboard)


@dp.message_handler(state=AddUserState.get_username)
async def user_to_group(massage: types.Message, state=FSMContext):
    username = massage.text
    data = await state.get_data()
    group_id = data.get('get_group_id')
    try:
        if not db_real.user_exist(username):
            raise RuntimeError("User does not exist")
        if not db_real.check_user_in_group(group_id, username):
            await AddUserState.add_user.set()
            await invite_user_to_join_group(group_id, massage.from_user.username, username)
            await state.finish()
        else:
            await bot.send_message(massage.from_user.id, "Пользователь уже в группе")
    except Exception as ex:
        logger.warning(ex)
        await massage.reply("Неправильный ввод")


@dp.callback_query_handler(state=AddUserState.get_group_id)
async def input_user(callback: CallbackQuery, state: FSMContext):
    group_id = callback.data.split()[-1]
    await state.update_data(get_group_id=group_id)
    await bot.send_message(callback.from_user.id, 'Напишите никнейм пользователя, которого хотите добавить:')
    await AddUserState.get_username.set()


@dp.message_handler(commands=["get_group_list"])
async def get_group_list(massage: types.Message):
    trip_data = massage.text.split()
    print(trip_data)
    try:
        group_id = int(trip_data[1])
        group_list = db_real.select(f'select username from trips tr join users u on tr.user_id = u.chat_id where '
                                    f'group_id = {group_id}')
        print(group_list)
        if len(group_list):
            await massage.reply(f"Участники группы: {', '.join(group_list)}")
        else:
            await massage.reply("Группа пока пуста(")
    except Exception as ex:
        logger.warning(ex)
        await massage.reply("Неправильный ввод")


@dp.message_handler(commands=["get_weather"])
async def weather_by_address(massage: types.Message):
    try:
        trip_address = ' '.join(massage.text.split()[1:])
        address_coordinates = get_coordinates_by_address(trip_address)
        if not address_coordinates:
            raise ValueError("Неправильный адрес")
        weather = get_weather_by_coordinates(address_coordinates)
        await bot.send_message(massage.from_user.id, weather)
    except Exception as ex:
        logger.warning(ex)
        await massage.reply("Ты что-то ввёл не так(")


@dp.message_handler(commands=["add_departure"])
async def add_departure(massage: types.Message):
    trip_data = massage.text.split()
    try:
        group_id = int(trip_data[1])
        trip_address = ' '.join(trip_data[2:])
        address_coordinates = get_coordinates_by_address(trip_address)
        if not address_coordinates:
            raise ValueError("Неправильный адрес")
        if update_departure(group_id, massage.from_user.id, address_coordinates):
            await bot.send_message(massage.from_user.id, "Адрес успешно изменён")
        else:
            raise RuntimeError("cant find trip by group_id user_id")
    except Exception as ex:
        logger.warning(ex)
        await massage.reply("Ты что-то ввёл не так(")


@dp.callback_query_handler(state=CreateTripState.group_id)
async def join_trip(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'user accept join to group':
        await bot.send_message(chat_id=callback.from_user.id, text='Вы приняли ')


@dp.callback_query_handler()
async def trip_callback(callback: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    if callback.data == "user accept invite to group":
        group_id = int(callback.message.text.split()[-1])
        invitor = db_real.get_chat_id_by_username(callback.message.text.split()[1])
        await state.update_data(invitor=invitor)
        await CreateTripState.group_id.set()
        await state.update_data(group_id=group_id)
        await create_trip(callback.from_user.id)
    elif callback.data == "user decline invite to group":
        group_id = int(callback.message.text.split()[-1])
        print(group_id)
        invitor_username = db_real.get_chat_id_by_username(callback.message.text.split()[1])
        print(callback.message.text.split())
        print(invitor_username)
        await bot.send_message(invitor_username,
                               f"Пользователь {callback.from_user.username} отказался присоединяться к группе {group_id}")


@dp.message_handler(commands=["create_group"])
async def input_date(message: Message):
    await message.answer("Выберите дату мероприятия: ", reply_markup=await SimpleCalendar().start_calendar())
    await CreateGroupState.date.set()


@dp.callback_query_handler(simple_cal_callback.filter(), state=CreateGroupState.date)
async def process_input_date(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.answer(
            f'Вы выбрали {date.strftime("%d-%m-%Y")}'
        )
        await state.update_data(date=date.date())
        await CreateGroupState.next()
        await callback_query.message.answer("Выберите время поездки: ")
        data = await state.get_data()


@dp.message_handler(state=CreateGroupState.time)
async def input_time(message: Message, state: FSMContext):
    try:
        time = datetime.datetime.strptime(message.text, '%H:%M')
        await state.update_data(time=message.text)
        await message.answer(f'Вы ввели время: {message.text}')
        await state.update_data(time=time.time())
        await CreateGroupState.next()
        await bot.send_message(chat_id=message.from_user.id, text='Введите адрес поездки: ')
    except Exception as ex:
        logger.warning(ex)
        await message.answer(f'Вы ввели неправильное время')
        await CreateGroupState.time.set()


@dp.message_handler(state=CreateGroupState.address)
async def input_address(message: Message, state: FSMContext):
    address_coordinates = get_coordinates_by_address(message.text)
    if not address_coordinates:
        await message.answer('Неправильный адрес')
        await CreateGroupState.address.set()
        raise ValueError("Неправильный адрес")
    else:
        await state.update_data(address=message.text)
        map = get_map_by_coordinates(address_coordinates[0], address_coordinates[1])
        if map:
            await message.answer('Вы выбрали следующий адресс')
            await message.answer_photo(photo=map)
    await state.update_data(coordinates=str(address_coordinates))
    await CreateGroupState.db_push.set()


@dp.message_handler(state=CreateGroupState.db_push)
async def db_push(message: Message, state: FSMContext):
    data = await state.get_data()
    datetime_obj = datetime.datetime.combine(data['date'], data['time'])
    group_id = db_real.create_group(datetime_obj, data['address'], data['coordinates'], message.from_user.id)
    await state.update_data(db_push=group_id)
    await message.reply(f'ID вашей встречи: {group_id}')
    await state.finish()
    await CreateTripState.group_id.set()
    await state.update_data(group_id=group_id)
    await create_trip(message.from_user.id)


async def create_trip(user_id):
    await bot.send_message(user_id, 'Введите адрес отправления')
    await CreateTripState.departure.set()


@dp.message_handler(state=CreateTripState.departure)
async def input_departure(message: Message, state: FSMContext):
    address_coordinates = get_coordinates_by_address(message.text)
    if not address_coordinates:
        await message.answer('Неправильный адрес')
        await CreateGroupState.address.set()
        raise ValueError("Неправильный адрес")
    else:
        await state.update_data(departure=message.text)
        await message.answer(f'Вы ввели адрес с координатами: {address_coordinates}')

    await state.update_data(departure=message.text)
    car_button = InlineKeyboardButton("Автомобиль", callback_data="car")
    public_transport_button = InlineKeyboardButton("Общественный транспорт", callback_data="public transport")

    keyboard = InlineKeyboardMarkup().row(car_button, public_transport_button)

    await bot.send_message(message.from_user.id, 'Выберите предпочитаемый вид траспорта', reply_markup=keyboard)
    await CreateTripState.transport_type.set()


@dp.callback_query_handler(state=CreateTripState.transport_type)
async def input_transport_type(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if callback_query.data == "car":
        await callback_query.answer('Вы выбрали автомобиль')
        await state.update_data(transport_type='car')

    elif callback_query.data == "public transport":
        await state.update_data(transport_type='public transport')
        await callback_query.answer('Вы выбрали общественный транспорт')

    else:
        await callback_query.answer('Я тупой дебил, не понимаю, на какую кнопку вы нажали')

    data = await state.get_data()
    db_real.create_trip(data['group_id'], callback_query.from_user.id, data['departure'], data['transport_type'])
    await bot.send_message(callback_query.from_user.id, 'Готово, рассчитываю время выхода...')
    await bot.send_message(callback_query.from_user.id, f"Вы присоединились к группе {data['group_id']}!")
    await bot.send_message(data['invitor'],
                           f"Пользователь {callback_query.from_user.username} присоединился к группе {data['group_id']}")
    await state.finish()


if __name__ == "__main__":
    executor.start_polling(dp)
