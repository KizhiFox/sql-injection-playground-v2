import sqlite3
from typing import Generator

from app.core.config import settings


def get_db() -> Generator:
    try:
        con = sqlite3.connect(settings.SQLITE_FILENAME)
        yield con
    finally:
        con.close()


def wrap_html(title: str, body: str) -> str:
    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>{title}</title>
</head>
<body>
<div>
<a href="/">Главная страница</a> | 
<a href="/users">Список пользователей</a> | 
<a href="/my-profile">Вход</a> | 
<a href="/register">Регистрация</a>
</div>
{body}
</body>
</html>'''
