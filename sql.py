import sqlalchemy
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec
import datetime
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from hashlib import sha256
from time import time
from json import load, dump
from random import choice
import os
import sqlite3

SqlAlchemyBase = dec.declarative_base()

__factory = None

# классы таблиц для базы данных


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    email = sqlalchemy.Column(
        sqlalchemy.String, index=True, unique=True, nullable=False)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    access = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey(
        'access.id'), default=1, nullable=False)
    modified_date = sqlalchemy.Column(
        sqlalchemy.DateTime, default=datetime.datetime.now)

    access_level = orm.relationship('AccessRights')
    api_key = orm.relationship('ApiKeyAsoc')
    db_links = orm.relationship('Upload_DB')

    def check_password(self, password):
        return sha256(password.encode('utf-8')).hexdigest() == self.hashed_password


class AccessRights(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'access'

    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True)
    level = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)

    user = orm.relationship("User", back_populates='access_level')


class ApiKeyAsoc(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'api_keys'

    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True)
    key = sqlalchemy.Column(sqlalchemy.String, nullable=False, index=True)
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'), nullable=False)

    user = orm.relationship("User", back_populates='api_key')


class Upload_DB(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'links'

    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'), nullable=False)
    database_name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    sourse_link = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    db_link = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    user = orm.relationship("User", back_populates='db_links')


class Upload(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'files'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    filename = sqlalchemy.Column(sqlalchemy.String(50))
    data = sqlalchemy.Column(sqlalchemy.LargeBinary)


def global_init(db_file):  # глобальная инициализация базы данных
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception('DB file required')

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f'connected with address {conn_str}')

    engine = sqlalchemy.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:  # создание сессии для работы с бд
    global __factory
    return __factory()


def sql_search(key: str) -> tuple:  # поиск по всем базам данных по ключу
    if not key:
        return dict(), 0
    start_time = time()
    fl = key + '.json'
    if fl in os.listdir('results'):
        with open(os.path.join('results', fl), 'r', encoding='utf-8') as json_file:
            data = load(json_file)
            search_time = time() - start_time
            return data, search_time
    data = dict()
    for filename in os.listdir('db'):
        if filename.endswith('.db'):
            filepath = os.path.join('db', filename)
            data[filename] = []
            with sqlite3.connect(filepath) as conn:
                cur = conn.cursor()
                rows = [row for row in cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")]
                table_names = list(map(lambda x: x[0], rows[1:]))
                for table_name in table_names:
                    column = cur.execute(
                        f"SELECT name FROM PRAGMA_TABLE_INFO('{table_name}')")
                    column_names = list(map(lambda x: x[0], column))
                    for col in column_names:
                        if key.isdigit() or '@' in key:
                            search_condition = f"WHERE {col} = '{key}'"
                        else:
                            search_condition = f"WHERE {col} LIKE '%{key}%'"
                        cur.execute(
                            f"SELECT * FROM {table_name} {search_condition}")
                        results = cur.fetchall()
                        dicts = []
                        if results:
                            for res in results:
                                ditt = dict()
                                for num, val in enumerate(res):
                                    ditt[column_names[num]] = val
                                dicts.append(ditt)
                            data[filename].extend(dicts)
    cur.close()
    with open(os.path.join('results', fl), 'w', encoding='utf-8') as json_file:
        dump(data, json_file)
    search_time = time() - start_time
    return data, search_time


# формирование результата для удобного вывода в таблицу
def sql_formate(dicts: list) -> list:
    formated_dicts = dict()
    for k, i in dicts.items():
        formated_dicts[k] = []
        for ditt in i:
            formated = ''
            for key, item in ditt.items():
                formated += f'{key}:\t{item}<br>'
            if len(formated) < 1000:
                formated_dicts[k].append(formated.strip('<br>'))
    return formated_dicts


def get_api_key(user: User) -> str:  # получение api ключа по юзеру
    db_sess = create_session()
    api_asoc = db_sess.query(ApiKeyAsoc).filter(
        ApiKeyAsoc.user_id == user.id).first()
    if api_asoc:
        return api_asoc.key


def generate_key(lenght: int) -> str:  # генерация ключа
    c = ''
    for _ in range(lenght):
        c += choice('qwertyuiopasdfghjklzxcvbnm1234567890QWERTYUIOPASDFGHJKLZXCVBNM')
    return c
