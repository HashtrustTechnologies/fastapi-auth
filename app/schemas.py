from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserIn(UserBase):
    password: str

    class Config:
        orm_mode = True


class UserOut(UserBase):
    id: int
    email: EmailStr

    first_name: Optional[str] = None
    last_name: Optional[str] = None

    class Config:
        orm_mode = True


class Login(BaseModel):
    password: str
    email: str

    class Config:
        orm_mode = True


class UserInDB(UserBase):
    hashed_password: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int


class TokenData(BaseModel):
    email: Optional[str] = None


class PasswordSchema(BaseModel):
    password: str
    re_password: str

    class Config:
        orm_mode = True


class ForgetPasswordSchema(BaseModel):
    email: EmailStr

    class Config:
        orm_mode = True


class ResetPasswordSchema(BaseModel):
    reset_password_token: str
    new_password: str
    confirm_password: str

    class Config:
        orm_mode = True
