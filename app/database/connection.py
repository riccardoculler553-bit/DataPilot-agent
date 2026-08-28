import os

import pymysql
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    database = os.getenv("DB_NAME")
    # 断言非空，类型检查器能识别
    assert user is not None and password is not None and host is not None and database is not None, "Missing DB env vars"

    connection = pymysql.connect(
        user=user,
        password=password,
        host=host,
        database=database,
        port=int(os.getenv("DB_PORT", "3306")),
        charset="utf8",
        cursorclass=pymysql.cursors.DictCursor,
    )
    return connection