import base64
import hashlib
import re
from pathlib import Path
from sqlite3.dbapi2 import Connection
from fastapi import APIRouter, Depends, Body, Request, status
from fastapi.responses import HTMLResponse
from urllib.parse import unquote

from app.api import deps
from app.core.config import settings

router = APIRouter()


def check_solution(request: str) -> bool:
    """
    Check if solution is blocked
    """
    request = request.replace(' ', '')
    print(type(request), request)
    for blocked_solution in settings.BLOCKED_SOLUTIONS:
        if re.match(blocked_solution.replace(' ', ''), request):
            return True

    return False


@router.get('/')
def main(request: Request) -> HTMLResponse:
    """
    Main page
    """
    # Check if solution is blocked
    if check_solution(request.url.path):
        page = '<h1>Это решение заблокировано, попробуйте найти другое</h1>'
        return HTMLResponse(content=deps.wrap_html('Главная страница', page), status_code=status.HTTP_403_FORBIDDEN)

    with open(Path('src', 'instructions.html'), 'r', encoding='utf8') as f:
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
        request: Request,
        payload: str = Body(None),
        db: Connection = Depends(deps.get_db)
) -> HTMLResponse:
    """
    Register an account
    """
    # Check if solution is blocked
    if check_solution(request.url.path):
        page = '<h1>Это решение заблокировано, попробуйте найти другое</h1>'
        return HTMLResponse(content=deps.wrap_html('Регистрация', page), status_code=status.HTTP_403_FORBIDDEN)

    con = db.cursor()

    data = {}
    for param in payload.split('&'):
        k, v = param.split('=')
        data[k] = unquote(v)

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


@router.get('/users')
def all_users(
        request: Request,
        db: Connection = Depends(deps.get_db)
):
    """
    Get all users
    """
    # Check if solution is blocked
    if check_solution(request.url.path):
        page = '<h1>Это решение заблокировано, попробуйте найти другое</h1>'
        return HTMLResponse(content=deps.wrap_html('Пользователи', page), status_code=status.HTTP_403_FORBIDDEN)

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
        return HTMLResponse(content=deps.wrap_html('Пользователи', page),
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get('/users/{nickname}')
def all_users(
        request: Request,
        nickname: str,
        db: Connection = Depends(deps.get_db)
):
    """
    Get specific user
    """
    # Hack: /users/' OR 1=1 UNION SELECT nickname, name from users UNION SELECT nickname, surname from users
    # UNION SELECT nickname, pwd_hash from users UNION SELECT nickname, group_num from users--
    # Check if solution is blocked

    if check_solution(request.url.path):
        page = '<h1>Это решение заблокировано, попробуйте найти другое</h1>'
        return HTMLResponse(content=deps.wrap_html(nickname, page), status_code=status.HTTP_403_FORBIDDEN)

    cur = db.cursor()

    try:
        cur.execute(f"SELECT nickname, status FROM users WHERE nickname = '{nickname}'")
        users = cur.fetchall()

        page = ''
        for user in users:
            user_name = user[0]
            user_status = user[1]
            page += ('<table style="text-align:left;"><tr><th><div style="width:100px;height:100px;'
                     'border-radius:50px;background-color:blue;color:white;vertical-align:middle;text-align:center;'
                     f'font-size: 80px;">{user_name[0]}</div></th>'
                     f'<th><h2>{user_name}</h2><p>{user_status}</p></th></tr></table>\n')

        if page == '':
            return HTMLResponse(content=deps.wrap_html(nickname, f'<h1>Пользователь {nickname} не существует</h1>'),
                                status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        page = f"<p>SELECT nickname, status FROM users WHERE nickname = '{nickname}'</p>\n<p>{e}</p>"
        return HTMLResponse(content=deps.wrap_html(nickname, page),
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return HTMLResponse(content=deps.wrap_html(nickname, page), status_code=status.HTTP_200_OK)


@router.get('/my-profile')
def my_profile(
        request: Request,
        db: Connection = Depends(deps.get_db)
):
    """
    Get user profile
    """
    # Check if solution is blocked
    if check_solution(request.url.path):
        page = '<h1>Это решение заблокировано, попробуйте найти другое</h1>'
        return HTMLResponse(content=deps.wrap_html('Мой профиль', page), status_code=status.HTTP_403_FORBIDDEN)

    # No authorisation
    if request.headers.get('Authorization') is None:
        page = '''<input type="text" id="login" name="login" placeholder="Логин"><br>
<input type="text" id="password" name="password" placeholder="Пароль"><br>
<button onclick="auth()">Войти</button>
<script>
    function auth() {
        var credentials = btoa(`${document.getElementById('login').value}:${document.getElementById('password').value}`);
        let xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function () {
            if (xhr.readyState == 4) {
                var new_window = window.open('', '_self');
                new_window.location.href='/my-profile'
                new_window.document.write(xhr.responseText);
            }
        }
        xhr.open('get', '/my-profile', true); 
        xhr.setRequestHeader('Content-Type', 'text/html; charset=utf-8');
        xhr.setRequestHeader('Authorization', `Basic ${credentials}`);
        xhr.send();
    }
</script>'''
        return HTMLResponse(content=deps.wrap_html('Мой профиль', page), status_code=status.HTTP_200_OK)

    # Wrong auth method
    if request.headers.get('Authorization').split(' ')[0] != 'Basic':
        return HTMLResponse(content=deps.wrap_html('Мой профиль', '<h1>Неправильный метод авторизации</h1>'),
                            status_code=status.HTTP_400_BAD_REQUEST)

    # Try authorisation
    try:
        nickname, password = base64.b64decode(request.headers.get('Authorization')[6:]).decode('utf8').split(':')
    except ValueError:
        return HTMLResponse(content=deps.wrap_html('Мой профиль', '<h1>Неправильное имя пользователя или пароль</h1>'),
                            status_code=status.HTTP_403_FORBIDDEN)

    # Check nulls
    if None in (nickname, password):
        return HTMLResponse(content=deps.wrap_html('Мой профиль', '<h1>Неправильное имя пользователя или пароль</h1>'),
                            status_code=status.HTTP_403_FORBIDDEN)

    cur = db.cursor()
    try:
        cur.execute(
            f"SELECT nickname, name, surname, group_num, status, pwd_hash FROM users WHERE nickname = '{nickname}'")
        users = cur.fetchall()

        # Check login and password
        if len(users) == 0:
            return HTMLResponse(content=deps.wrap_html('Мой профиль',
                                                       '<h1>Неправильное имя пользователя или пароль</h1>'),
                                status_code=status.HTTP_403_FORBIDDEN)

        if nickname != users[0][0] or hashlib.sha256(password.encode('utf8')).hexdigest().upper() != users[0][5]:
            return HTMLResponse(content=deps.wrap_html('Мой профиль',
                                                       '<h1>Неправильное имя пользователя или пароль</h1>'),
                                status_code=status.HTTP_403_FORBIDDEN)

        # Show user's page
        page = f'''<table style="text-align:left;">
    <tr><th><div style="width:100px;height:100px;border-radius:50px;background-color:blue;color:white;vertical-align:middle;text-align:center;font-size: 80px;">{users[0][0][0]}</div></th>
    <th>
        <h2>{users[0][0]}</h2>
        <div>Имя: {users[0][1]}</div>
        <div>Фамилия: {users[0][2]}</div>
        <div>Статус: {users[0][4]}</div>
        <div>Номер группы: {users[0][3]}</div>
    </th></tr>
</table>'''

    except Exception as e:
        page = f"<p>SELECT nickname, name, surname, group_num, status, pwd_hash FROM users WHERE nickname = '{nickname}'</p>\n<p>{e}</p>"
        return HTMLResponse(content=deps.wrap_html('Мой профиль', page),
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return HTMLResponse(content=deps.wrap_html('Мой профиль', page),
                        status_code=status.HTTP_200_OK)
