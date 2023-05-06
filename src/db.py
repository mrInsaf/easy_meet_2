groups = list()
users = list()
trips = list()


# create new group
def db_add_group(date, address, coordinates, owner) -> int:
    groups.append((date, address, coordinates, owner))
    return len(groups) - 1


def user_exist(username: str) -> bool:
    for user in users:
        if user[1] == username:
            return True
    return False


# create new user
def db_create_user(chat_id, username, first_name, last_name):
    if user_exist(username):
        return
    users.append((chat_id, username, first_name, last_name))


def check_user_in_group(group_id, username) -> bool:
    for trip in trips:
        if trip[0] == group_id and trip[1] == username:
            return True
    return False


def get_chat_id_by_username(username: str) -> int:
    for user in users:
        if user[1] == username:
            return user[0]


def get_username_by_chat_id(chat_id: int) -> str:
    for user in users:
        if user[0] == chat_id:
            return user[1]


def add_user_to_group(group_id, chat_id):
    trips.append((group_id, chat_id, None, None, None))


def see_group_list(group_id: int) -> list:
    group_list = list()
    for trip in trips:
        if trip[0] == group_id:
            group_list.append("@" + get_username_by_chat_id(trip[1]))
    return group_list


def update_departure(group_id: int, user_id: int, address_coordinates: tuple) -> bool:
    global trips
    update_num = None
    for i in range(len(trips)):
        if trips[0] == group_id and trips[1] == user_id:
            update_num = i
            break
    if update_num:
        new_trip = (trips[0], trips[1], address_coordinates, trips[3], trips[4])
        trips = trips[:update_num] + [new_trip] + trips[update_num + 1:]
        return True
    return False
