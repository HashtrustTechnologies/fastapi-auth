from datetime import datetime, timedelta

from fastapi.exceptions import HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def find_black_list_token(db: Session, token: str):
    return db.query(models.BlackLists).filter(models.BlackLists.token == token).first()


def create_user(db: Session, user: schemas.UserIn):
    new = user.dict()
    hash = get_password_hash(user.dict()["password"])
    new["hashed_password"] = hash

    del new["password"]

    db_dialogue = models.User()
    db_dialogue.hashed_password = new["hashed_password"]
    db_dialogue.first_name = new["first_name"]
    db_dialogue.last_name = new["last_name"]
    db_dialogue.email = new["email"]

    db.add(db_dialogue)
    db.commit()
    db.refresh(db_dialogue)

    return db_dialogue


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(db, email: str, password: str):
    user = get_user_by_email(db, email)

    if not user:
        return False

    if not verify_password(password, user.hashed_password):
        return False

    return user


def update_password(password: str, db: Session, user: models.User):
    hash = get_password_hash(password)
    if pwd_context.verify(password, user.hashed_password):
        raise HTTPException(
            status_code=409, detail="Old password and updated password are same."
        )
    user.hashed_password = hash
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_email_by_token(db: Session, token: str):
    data = db.query(models.Codes).filter(models.Codes.reset_code == token).first()
    return data.email


def create_reset_code(db: Session, email: str, reset_code: str):
    user_reset_code = models.Codes(
        email=email,
        reset_code=reset_code,
        expired_in=datetime.now() + timedelta(days=10),
    )
    db.add(user_reset_code)
    db.commit()
    db.refresh(user_reset_code)
    return user_reset_code


def save_black_list_token(db: Session, token: str, email: str):
    black_list_token = models.BlackLists(token=token, email=email)
    db.add(black_list_token)
    db.commit()
    db.refresh(black_list_token)
    return black_list_token


def check_reset_token_validity(db: Session, token: str):
    data = db.query(models.Codes).filter(models.Codes.reset_code == token).first()
    if data:
        if not data.active:
            raise Exception("Token is not active.")
        if data.expired_in < datetime.now():
            raise Exception("Token has expired")
        return data
    raise Exception("No details found of password reset token.")


def mark_token_inactive(db: Session, token: str):
    data = db.query(models.Codes).filter(models.Codes.reset_code == token).first()
    if not data:
        raise Exception("No details found of password reset token.")
    data.active = False
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


def update_user_profile(db: Session, user_data: schemas.UserBase, user):

    db.query(models.User).filter(models.User.id == user.id).update(user_data)
    db.commit()
    return get_user_by_email(db, user_data.email)


def upload_profile_image(db: Session, user_image):

    db_profile_image = models.User(user_profile_image=user_image)
    db.add(db_profile_image)
    db.commit()
    db.refresh(db_profile_image)
    return db_profile_image


def delete_user_data(db: Session, user_id: int):
    db_delete_user_data = (
        db.query(models.User).filter(models.User.id == user_id).delete()
    )
    db.commit()
    return db_delete_user_data
