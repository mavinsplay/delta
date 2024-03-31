import sqlalchemy
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec
import datetime
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from hashlib import sha256

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
