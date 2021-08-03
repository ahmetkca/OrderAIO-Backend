from pathlib import Path
from fastapi_mail import FastMail, MessageSchema,ConnectionConfig
from config import MAIL_PORT, MAIL_PASSWORD, MAIL_EMAIL, MAIL_HOST


conf = ConnectionConfig(
    MAIL_USERNAME = MAIL_EMAIL,
    MAIL_PASSWORD = MAIL_PASSWORD,
    MAIL_FROM = MAIL_EMAIL,
    MAIL_PORT = MAIL_PORT,
    MAIL_SERVER = MAIL_HOST,
    MAIL_TLS = True,
    MAIL_SSL = False,
    USE_CREDENTIALS = True,
	TEMPLATE_FOLDER = './templates'
)


def get_mail_service():
	fm = FastMail(conf)
	return fm