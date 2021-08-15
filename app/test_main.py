import json
import uuid

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import main
from .database import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


@sa.event.listens_for(engine, "connect")
def do_connect(dbapi_connection, connection_record):
    dbapi_connection.isolation_level = None


@pytest.fixture()
def session():
    connection = engine.connect()
    session = TestingSessionLocal(bind=connection)

    yield session
    session.close()
    connection.close()


@pytest.fixture()
def client(session):
    def override_get_db():
        yield session

    main.app.dependency_overrides[main.get_db] = override_get_db
    yield TestClient(main.app)
    del main.app.dependency_overrides[main.get_db]


HEADERS = {"accept": "application/json", "Content-Type": "application/json"}


USERNAME = str(uuid.uuid4())
PASSWORD = str(uuid.uuid4())
EMAIL = str(uuid.uuid4()) + "@gmail.com"


def test_user_register(client):
    payload = {
        "password": PASSWORD,
        "email": EMAIL,
        "first_name": str(uuid.uuid4()),
        "last_name": str(uuid.uuid4()),
    }

    response = client.post(
        "/api/v1/register",
        headers=HEADERS,
        json=payload,
    )
    response = json.loads(response.text)
    assert response["email"] == EMAIL


def test_user_register_with_missing_field(client):
    payload = {
        "password": str(uuid.uuid4()),
        "first_name": str(uuid.uuid4()),
        "last_name": str(uuid.uuid4()),
    }

    response = client.post(
        "/api/v1/register",
        headers=HEADERS,
        json=payload,
    )
    response = json.loads(response.text)
    assert response["detail"][0]["type"] == "value_error.missing"


def test_login_with_wrong_credentails(client):
    HEADERS["Content-Type"] = "application/x-www-form-urlencoded"

    data = {
        "grant_type": "",
        "username": str(uuid.uuid4()),
        "password": str(uuid.uuid4()),
        "scope": "",
        "client_id": "",
        "client_secret": "",
    }

    response = client.post(
        "/api/v1/login",
        headers=HEADERS,
        data=data,
    )
    response = json.loads(response.text)
    assert response["detail"] == "Incorrect username or password"


def test_get_user_token(client):
    HEADERS["Content-Type"] = "application/x-www-form-urlencoded"

    data = {
        "grant_type": "",
        "username": EMAIL,  # form expects username, we give it the email.
        "password": PASSWORD,
        "scope": "",
        "client_id": "",
        "client_secret": "",
    }

    response = client.post(
        "/api/v1/login",
        headers=HEADERS,
        data=data,
    )
    response = json.loads(response.text)
    HEADERS["Authorization"] = "Bearer {}".format(response["access_token"])
    HEADERS["Content-Type"] = "application/json"
    return response["access_token"]


def test_update_password_error(client):
    PAYLOAD = {"password": "test@123", "re_password": "test"}
    response = client.put(
        "/api/v1/update_password",
        headers=HEADERS,
        data=json.dumps(PAYLOAD),
    )
    response = json.loads(response.text)
    assert response["detail"] == "password and re_password does not match"


def test_update_password_correct(client):
    PAYLOAD = {"password": "test@123", "re_password": "test@123"}
    response = client.put(
        "/api/v1/update_password",
        headers=HEADERS,
        data=json.dumps(PAYLOAD),
    )
    response = json.loads(response.text)
    assert (
        response["message"]
        == "Password is updated Successfully. Please login again with updated password"
    )
