# table for sqlite aplication, sqlite is used as relational DB
# DB is going to be a connection from sqlite to FastAPI application

from database import Base
from sqlalchemy import Column, Integer, String, Boolean, Float


class Transaction(Base):
    __tablename__ = 'transactions' # creates a table in sqlite db called transactions

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    category = Column(String)
    description = Column(String)
    is_income = Column(Boolean)
    date = Column(String)


class User(Base):
    __tablename__ = 'Users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)