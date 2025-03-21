import sqlalchemy as sq
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Words(Base):
    __tablename__ = 'words'

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    word = sq.Column(sq.String(length=255), unique=True, nullable=False)
    translate = sq.Column(sq.String(length=255), unique=True, nullable=False)


class Users(Base):
    __tablename__ = 'users'

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    cid = sq.Column(sq.BigInteger, unique=True, nullable=False)


class UserWords(Base):
    __tablename__ = 'user_words'

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    word = sq.Column(sq.String(length=255))
    translate = sq.Column(sq.String(length=255))
    id_user = sq.Column(sq.Integer, sq.ForeignKey('users.id'), nullable=False)


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)