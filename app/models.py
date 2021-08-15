from sqlalchemy import Boolean, Column, DateTime, Integer, String

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    user_profile_image = Column(String, nullable=True)


class SessionToken(Base):
    __tablename__ = "tokens"
    access_token = Column(String, index=True, primary_key=True)
    token_type = Column(String, index=True)


class SessionTokenData(Base):
    __tablename__ = "tokendata"
    username = Column(String, index=True, primary_key=True)


class Codes(Base):
    __tablename__ = "codes"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String)
    reset_code = Column(String)
    active = Column(Boolean, default=True)
    expired_in = Column(DateTime)


class BlackLists(Base):
    __tablename__ = "blacklists"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    token = Column(String, unique=True)
    email = Column(String)
