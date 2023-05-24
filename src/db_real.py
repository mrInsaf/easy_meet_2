import sqlite3
from sqlite3 import IntegrityError
import datetime

# установите путь к базе данных, если он отличается от директории с программой
connect = sqlite3.connect('easy_meet.db')
connect.execute("PRAGMA foreign_keys = 1")
cursor = connect.cursor()


def select(query):
    cursor.execute(query)
    records = cursor.fetchall()
    for i, rec in enumerate(records):
        rr = []
        for r in rec:
            rr.append(r)
        records[i] = rr
        # print(records[i])
    connect.commit()
    return records


def insert(table_name, record):
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    table_info = cursor.fetchone()[0]

    # проверяем, есть ли в таблице table_name столбец с первичным ключом
    if "PRIMARY KEY" in table_info:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        query = f"""INSERT INTO {table_name} ({str(columns[1:]).replace('[', '').replace(']', '').replace("'", '')}) VALUES ({','.join(['?'] * len(record))});"""
    else:
        query = f"""INSERT INTO {table_name} VALUES ({','.join(['?'] * len(record))});"""

    print(record)
    cursor.execute(query, record)
    connect.commit()


def create_group(date, address, owner_id, lat, long, password):
    # datetime_str = date + ' ' + time
    # record = [address, datetime_str]
    record = [address, date, owner_id, lat, long, password]
    insert('groups', record)
    group_id = select(
        f'select id from groups where destination = "{address}" and meet_time = "{date}" and owner_id = {owner_id}')
    return group_id[0][0]


def create_trip(group_id, chat_id, departure, transport_type, trip_time, interim_point=''):
    user_id = get_user_id_by_chat_id(chat_id)
    record = [group_id, user_id, departure, interim_point, transport_type, trip_time]
    query = f"""INSERT INTO trips (group_id, user_id, departure, interim_point, transport_type, trip_time) VALUES ({','.join(['?'] * len(record))});"""
    cursor.execute(query, record)
    connect.commit()


def create_user(chat_id, username, first_name=None, last_name=None):
    if not user_exist(username):
        record = [chat_id, username, first_name, last_name]
        insert('users', record)


def get_chat_id_by_username(username):
    chat_id = select(f'select chat_id from users where username = "{username}"')
    return chat_id[0][0]


def get_user_id_by_chat_id(chat_id):
    user_id = select(f'select id from users where chat_id = "{chat_id}"')
    return user_id[0][0]


def user_exist(username):
    usernames = select(f'select * from users where username = "{username}"')
    if len(usernames) == 0:
        return False
    else:
        return True


def check_user_in_group(group_id, username) -> bool:
    user_id = get_user_id_by_chat_id(get_chat_id_by_username(username))
    user = select(f'select * from trips where group_id = {group_id} and user_id = {user_id}')
    if len(user):
        return True
    else:
        return False


def check_group_by_id(id):
    user = select(f'select * from groups where id = {id}')
    if len(user):
        return True
    else:
        return False


def get_arrival_coordinates(group_id):
    coordinates = select(f'select latitude, longitude from groups where id = {group_id}')
    return coordinates[0]


def get_group_data(group_id):
    group_data = select(f'select destination, meet_time from groups where id = {group_id}')
    return group_data[0]

def get_trip_data(group_id, user_id):
    trip_data = select(f'select trip_time from trips where group_id = {group_id} and user_id = {user_id}')
    return trip_data[0][0]


def get_user_groups(chat_id):
    user_id = get_user_id_by_chat_id(chat_id)
    data = select(f'select group_id, departure, trip_time from trips where user_id = {user_id}')
    result = []
    for item in data:
        group_data = get_group_data(item[0])
        result += [item + group_data]
    print(result)
    return result


def is_noticed(group_id, chat_id) -> bool:
    user_id = get_user_id_by_chat_id(chat_id)
    status = select(f'select is_noticed from trips where group_id = {group_id} and user_id = {user_id}')
    return status[0][0]


def set_noticed(group_id, chat_id):
    user_id = get_user_id_by_chat_id(chat_id)
    cursor.execute(f'update trips set is_noticed = 1 where group_id = {group_id} and user_id = {user_id}')
    connect.commit()

def check_access(group_id):
    password = select(f'select password from groups where id = {group_id}')
    return password[0][0]


def get_coordinates_by_group(group_id):
    coordinates = select(f'select latitude, longitude from groups where id = {group_id}')
    return coordinates[0]

