import sqlite3
from pathlib import Path

from app.core.config import settings


if not Path(settings.SQLITE_FILENAME).exists():
    print(f'Creating new database "{settings.SQLITE_FILENAME}"')
    con = sqlite3.connect(settings.SQLITE_FILENAME)
    cur = con.cursor()
    cur.execute('CREATE TABLE users (nickname text, name text, surname text, group_num text, status text, pwd_hash text)')
    con.commit()
    con.close()
else:
    print(f'Database is already exists at "{settings.SQLITE_FILENAME}"')
