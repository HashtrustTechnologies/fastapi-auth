import os

from dotenv import load_dotenv
from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

load_dotenv()


class Envs:
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "test@test.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "testpassword")
    MAIL_FROM = os.getenv("MAIL_FROM", "test@test.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 1025))
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")


template_folder = os.getcwd()

conf = ConnectionConfig(
    MAIL_USERNAME=Envs.MAIL_USERNAME,
    MAIL_PASSWORD=Envs.MAIL_PASSWORD,
    MAIL_FROM=Envs.MAIL_FROM,
    MAIL_PORT=Envs.MAIL_PORT,
    MAIL_SERVER=Envs.MAIL_SERVER,
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER="./app/templates",
)


async def send_email_async(subject: str, email_to: str, body: dict, template: str):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=body,
        subtype="html",
    )

    fm = FastMail(conf)

    await fm.send_message(message, template_name=template)


def send_email_background(
    background_tasks: BackgroundTasks,
    subject: str,
    email_to: str,
    body: dict,
    template: str,
):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=body,
        subtype="html",
    )

    fm = FastMail(conf)

    background_tasks.add_task(fm.send_message, message, template_name=template)
