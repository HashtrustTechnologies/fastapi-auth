import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

from . import crud, models, schemas
from .database import SessionLocal, engine
from .send_email import send_email_background

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "edf57e1b178a0727356d496af85a1aa47caa82b9b22be4ab7c278c01ef30b827"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 100

models.Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = models.SessionTokenData(username=username)
    except JWTError:
        raise credentials_exception

    # Check blacklist token
    black_list_token = crud.find_black_list_token(db, token)
    if black_list_token:
        raise credentials_exception

    # Check user existed
    user = crud.get_user_by_email(db, email=token_data.username)
    if user is None:
        raise credentials_exception
    return user


def get_token_user(token: str = Depends(oauth2_scheme)):
    return token


@app.post("/api/v1/register", response_model=schemas.UserOut)
async def create_user(identity: schemas.UserIn, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, identity.email)
    if user:
        raise HTTPException(status_code=409, detail="Email already registered.")
    return crud.create_user(db=db, user=identity)


@app.post("/api/v1/login", response_model=schemas.Token)
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = crud.authenticate_user(
        db=db, email=form_data.username, password=form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}


@app.get("/api/v1/me")
async def get_logged_in_user(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return current_user


@app.put("/api/v1/update_password")
def update_user_password(
    request: schemas.PasswordSchema,
    token: str = Depends(get_token_user),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if request.password != request.re_password:
        raise HTTPException(
            status_code=409, detail="password and re_password does not match"
        )

    crud.update_password(password=request.password, db=db, user=current_user)
    crud.save_black_list_token(db, token, current_user.email)
    return {
        "message": "Password is updated Successfully. Please login again with updated password"
    }


@app.post("/api/v1/forgot_password")
def forget_password(
    background_tasks: BackgroundTasks,
    request: schemas.ForgetPasswordSchema,
    db: Session = Depends(get_db),
):

    # check user existed
    result = crud.get_user_by_email(db, request.email)
    if not result:
        raise HTTPException(status_code=404, details="user not found.")

    # Create reset code and save in database
    reset_code = str(uuid.uuid1())
    crud.create_reset_code(db, request.email, reset_code)

    # MAKE SURE .env FILE UPDATED
    send_email_background(
        background_tasks,
        "Password Reset",
        request.email,
        {
            "protocol": os.getenv("PROTOCOL"),
            "domain": os.getenv("DOMAIN"),
            "url": "/reset_password?reset_password_token={0:}".format(reset_code),
        },
        "password_reset_email.html",
    )
    message = "We've emailed you instructions for setting your password, if an account exists with the email you entered. You should receive them shortly. If you don't receive an email, please make sure you've entered the address you registered with, and check your spam folder."
    return {"status_code": status.HTTP_200_OK, "detail": message}


@app.post("/api/v1/reset_password")
def password_reset(request: schemas.ResetPasswordSchema, db: Session = Depends(get_db)):
    # check token is valid or not
    valid_token = crud.check_reset_token_validity(db, request.reset_password_token)
    if not valid_token:
        raise HTTPException(status_code=404, detail="Reset Token is not valid")

    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=409, detail="new_password and confirm_password does not match"
        )

    # Update password
    email = crud.get_email_by_token(db, request.reset_password_token)
    user = crud.get_user_by_email(db, email)
    crud.update_password(request.new_password, db, user)
    crud.mark_token_inactive(db, request.reset_password_token)
    return {
        "status_code": status.HTTP_200_OK,
        "detail": "Password reset successfully. Please login.",
    }


@app.post("/api/v1/logout")
def logout(
    token: str = Depends(get_token_user),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    crud.save_black_list_token(db, token, current_user.email)
    return {"status_code": status.HTTP_200_OK, "detail": "User logged out successfully"}


@app.put("/api/v1/profile_update")
def update_user_profile(
    user_data: schemas.UserBase,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    crud.update_user_profile(db, user_data, current_user)
    return {"status_code": status.HTTP_200_OK, "detail": "Profile updated successfully"}


@app.delete("/api/v1/forget_me")
def forget_me(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    crud.delete_user_data(db, user_id=current_user.id)
    return {
        "status_code": status.HTTP_200_OK,
        "detail": "Your account is successfully deleted.",
    }


@app.post("/api/v1/upload_profile_image")
def upload_profile_image(
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):
    cwd = os.getcwd()
    path_image_dir = "upload-images/user-profile/" + str(current_user.id) + "/"
    full_image_path = os.path.join(cwd, path_image_dir, file.filename)

    # Create directory if not exist
    if not os.path.exists(path_image_dir):
        dir = os.path.join(cwd, "upload-images")
        os.mkdir(dir)
        dir = os.path.join(cwd, "upload-images", "user-profile")
        os.mkdir(dir)
        dir = os.path.join(cwd, "upload-images", "user-profile", str(current_user.id))
        os.mkdir(dir)

    # Rename file to "profile.png"
    file_name = full_image_path.replace(file.filename, "profile.png")

    # Save file in user profile database
    current_user.user_profile_image = file_name
    crud.upload_profile_image(db, current_user.user_profile_image)

    return {
        "status_code": status.HTTP_200_OK,
        "detail": "Profile image upload success",
        "profile_image": os.path.join(path_image_dir, "profile.png"),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
