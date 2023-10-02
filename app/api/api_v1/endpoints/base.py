import hashlib
from typing import Any, List
from pathlib import Path
from sqlite3.dbapi2 import Connection
from fastapi import APIRouter, Depends, Body, Request, Query, HTTPException, status
from fastapi.responses import HTMLResponse

from app.api import deps

router = APIRouter()


@router.get('/')
def main() -> HTMLResponse:
    """
    Main page
    """
    with open(Path('src', 'instructions.html'), 'r') as f:
        page = f.read()

    return HTMLResponse(content=deps.wrap_html('Главная страница', page), status_code=status.HTTP_200_OK)


@router.get('/register')
def register() -> HTMLResponse:
    """
    Registration page
    """
    page = ('<form action="/register-result" method="post">'
            '<label for="nickname">Логин:</label><br>'
            '<input type="text" id="nickname" name="nickname"><br>'
            '<label for="password">Пароль:</label><br>'
            '<input type="text" id="password" name="password"><br><br>'
            '<label for="name">Имя:</label><br>'
            '<input type="text" id="name" name="name"><br>'
            '<label for="surname">Фамилия:</label><br>'
            '<input type="text" id="surname" name="surname"><br>'
            '<label for="group_num">Номер группы:</label><br>'
            '<input type="text" id="group_num" name="group_num"><br>'
            '<label for="status">Статус:</label><br>'
            '<input type="text" id="status" name="status"><br>'
            '<input type="submit" value="Зарегистрироваться">'
            '</form>')
    return HTMLResponse(content=deps.wrap_html('Регистрация', page), status_code=status.HTTP_200_OK)


@router.post('/register-result')
def register(
        payload: str = Body(None),
        db: Connection = Depends(deps.get_db)
) -> HTMLResponse:
    """
    Register an account
    """
    con = db.cursor()

    data = {}
    for param in payload.split('&'):
        k, v = param.split('=')
        data[k] = v

    nickname = data['nickname'] if 'nickname' in payload else None
    name = data['name'] if 'name' in payload else None
    surname = data['surname'] if 'surname' in payload else None
    group_num = data['group_num'] if 'group_num' in payload else None
    status_ = data['status'] if 'status' in payload else None
    password = data['password'] if 'password' in payload else None

    # Check if user exists
    try:
        con.execute(f"SELECT nickname FROM users WHERE nickname = '{nickname}'")
        users = con.fetchall()

        if len(users) > 0:
            page = (f'<h1>Пользователь с ником {nickname} уже существует</h1><br>'
                    f'<a href="javascript:history.back()">Назад к регистрации</a>')
            return HTMLResponse(content=deps.wrap_html('Регистрация', page), status_code=status.HTTP_200_OK)

    except Exception as e:
        page = f"<p>SELECT nickname FROM users WHERE nickname = '{nickname}'</p>\n<p>{e}</p>"
        return HTMLResponse(content=deps.wrap_html('Регистрация', page),
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Register new user
    pwd_hash = hashlib.sha256(password.encode('utf8')).hexdigest().upper()
    try:
        con.execute(
            f"INSERT INTO users VALUES ('{nickname}', '{name}', '{surname}', '{group_num}', '{status_}', '{pwd_hash}')")
        db.commit()

    except Exception as e:
        page = f"<p>INSERT INTO users VALUES ('{nickname}', '{name}', '{surname}', '{group_num}', '{status_}', '{pwd_hash}')</p>\n<p>{e}</p>"
        return HTMLResponse(content=deps.wrap_html('Регистрация', page),
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    page = '<h1>Поздравляем с регистрацией!</h1><br>'
    return HTMLResponse(content=deps.wrap_html('Регистрация', page), status_code=status.HTTP_200_OK)


@router.get('/test/{test}')
def test(
        test: str,
        request: Request
):
    params = request.query_params
    print(test)
    print(params)


@router.get('/users')
def all_users(
        db: Connection = Depends(deps.get_db)
):
    cur = db.cursor()

    try:
        cur.execute(f'SELECT nickname, status FROM users')
        users = cur.fetchall()

        page = ''
        for user in users:
            user_name = user[0]
            user_status = user[1]
            page += ('<table style="text-align:left;"><tr><th>'
                     '<div style="width:100px;height:100px;border-radius:50px;background-color:blue;color:white;'
                     f'vertical-align:middle;text-align:center;font-size: 80px;">{user_name[0]}</div></th><th><h2>'
                     f'<a href="/users/{user_name}">{user_name}</a></h2><p>{user_status}</p></th></tr></table>\n')

        if page == '':
            page = '<h1>Здесь пока никто не зарегистрировался</h1>'

        return HTMLResponse(content=deps.wrap_html('Пользователи', page), status_code=status.HTTP_200_OK)

    except Exception as e:
        page = f'<p>SELECT nickname, status FROM users</p>\n<p>{e}</p>'
        return HTMLResponse(content=deps.wrap_html('Регистрация', page),
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
