import pymysql.cursors
from settings import *


def db_init():
    try:
        connection = pymysql.connect(host=host,
                                     user=user,
                                     port=port,
                                     password=password,
                                     database=database,
                                     charset=charset,
                                     cursorclass=pymysql.cursors.DictCursor)
        return connection
    except IndentationError:
        return "ошибка подключения к базе данных"


def create_table():
    connection = db_init()
    with connection.cursor() as cursor:
        sql = "show tables;"
        cursor.execute(sql)

        res = cursor.fetchall()
        for table in res:
            if table['Tables_in_schedule_bot'] == 'users':
                break
        else:
            sql = """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT,
                    schedule_id INT,
                    user_type INT,
                    auto_sending BOOLEAN,
                    PRIMARY KEY (USER_ID)
                );
                """
            cursor.execute(sql)
            connection.commit()
    connection.close()


def create_user(user_id, schedule_id, user_type):
    connection = db_init()
    with connection.cursor() as cursor:
        sql = (f"INSERT INTO users (user_id, schedule_id, user_type, auto_sending) VALUES "
               f"({user_id}, {schedule_id}, {user_type}, NULL)")
        cursor.execute(sql)
        connection.commit()
    connection.close()


def edit_schedule_id(user_id, new_schedule_id, new_user_type):
    connection = db_init()
    with connection.cursor() as cursor:
        # 1 - студент, 2 - преподаватель
        sql = (f"UPDATE users SET schedule_id = "
               f"{new_schedule_id}, user_type = {new_user_type} WHERE user_id = {user_id}")
        cursor.execute(sql)
        connection.commit()
    connection.close()


def auto_sending(user_id, auto_sending_values):
    connection = db_init()
    with connection.cursor() as cursor:
        sql = (f"UPDATE users SET auto_sending = "
               f"{1 if auto_sending_values is True else 0} WHERE user_id = {user_id}")
        cursor.execute(sql)
        connection.commit()
    connection.close()


def all_users():
    connection = db_init()
    with connection.cursor() as cursor:
        sql = "SELECT * FROM users"
        cursor.execute(sql)
        return cursor.fetchall()
    connection.close()


def user_one(user_id):
    connection = db_init()
    with connection.cursor() as cursor:
        sql = f"SELECT * FROM users WHERE user_id = {user_id}"
        cursor.execute(sql)
        return cursor.fetchone()
    connection.close()