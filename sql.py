import sqlalchemy
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec
import datetime
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from hashlib import sha256
from time import time
import os
import sqlite3

SqlAlchemyBase = dec.declarative_base()

__factory = None
    

class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    email = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=False)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    access = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('access.id'), default=1, nullable=False)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    
    access_level = orm.relationship('AccessRights')
    api_key = orm.relationship('ApiKeyAsoc')
    
    def check_password(self, password):
        return sha256(password.encode('utf-8')).hexdigest() == self.hashed_password
    
class AccessRights(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'access'
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    level = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    
    user = orm.relationship("User", back_populates='access_level')

class ApiKeyAsoc(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'api_keys'
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    key = sqlalchemy.Column(sqlalchemy.String, nullable=False, index=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'), nullable=False)
    
    user = orm.relationship("User", back_populates='api_key')

def global_init(db_file):
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


def create_session() -> Session:
    global __factory
    return __factory()


def sql_search(key: str) -> tuple:
    if not key:
        return dict(), 0
    start_time = time()
    data = dict()
    for filename in os.listdir('db'):
        if filename.endswith('.db'):
            filepath = os.path.join('db', filename)
            data[filename] = []
            with sqlite3.connect(filepath) as conn:
                cur = conn.cursor()
                rows = [row for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                table_names = list(map(lambda x: x[0], rows[1:]))
                for table_name in table_names:
                    column = cur.execute(f"SELECT name FROM PRAGMA_TABLE_INFO('{table_name}')")
                    column_names = list(map(lambda x: x[0], column))
                    for col in column_names:
                        if key.isdigit() or '@' in key:
                            search_condition = f"WHERE {col} = '{key}'"
                        else:
                            search_condition = f"WHERE {col} LIKE '%{key}%'"
                        cur.execute(f"SELECT * FROM {table_name} {search_condition}")
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
    search_time = time() - start_time
    return data, search_time

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

def get_api_key(user: User) -> str | None:
    db_sess = create_session()
    api_asoc = db_sess.query(ApiKeyAsoc).filter(ApiKeyAsoc.user_id == user.id).first()
    if api_asoc:
        return api_asoc.key