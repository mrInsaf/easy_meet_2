import sqlite3
from sqlite3 import IntegrityError
import datetime

# установите путь к базе данных, если он отличается от директории с программой
connect = sqlite3.connect('/Users/eliseymuxin/PycharmProjects/easy_meet_2/src/easy_meet.db')
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

    cursor.execute(query, record)
    connect.commit()


def create_group(date, address, coordinates, owner_id):
    # datetime_str = date + ' ' + time
    # record = [address, datetime_str]
    record = [address, date, coordinates[0], coordinates[1], owner_id]
    insert('groups', record)
    group_id = select(
        f'select id from groups where destination = "{address}" and meet_time = "{date}" and owner_id = {owner_id}')
    return group_id[0]


def create_trip(group_id, user_id, departure, transport_type, interim_point=None):
    record = [group_id, user_id, departure, interim_point, transport_type]
    insert('trips', record)


def create_user(chat_id, username, first_name=None, last_name=None):
    if not user_exist(username):
        record = [chat_id, username, first_name, last_name]
        insert('users', record)


def get_chat_id_by_username(username):
    chat_id = select(f'select chat_id from users where username = "{username}"')
    return chat_id[0][0]


def user_exist(username):
    usernames = select(f'select * from users where username = "{username}"')
    if len(usernames) == 0:
        return False
    else:
        return True


def check_user_in_group(group_id, username) -> bool:
    user = select(f'select * from trips tr join users u on tr.user_id = u.chat_id where group_id = {group_id} and '
                  f'username = "{username}"')
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
