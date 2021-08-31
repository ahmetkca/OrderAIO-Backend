import os
from dotenv import load_dotenv
load_dotenv(override=True)

SOCKETIO_PATH = 'socket.io'
MOUNT_LOCATION = '/ws'
ASYNC_MODE = 'asgi'
SOCKETIO_MAIN_ROOM = 'orderaio'

ENV_MODE = os.environ.get("ENV_MODE")

DEFAULT_SEARCH_LIMIT = 10
DEFAULT_SEARCH_PAGE = 1


SCHEDULED_JOB_INTERVAL = 5 if ENV_MODE == "DEV" else 15
SCHEDULED_JOB_OFFSET = 5 if ENV_MODE == "DEV" else 5

NO_CONCURRENT = 10
LIMIT = 100

FRONTEND_URI = os.environ.get("FRONTEND_URI")
JWT_SECRET = os.environ.get("JWT_SECRET")
MAIL_HOST = os.environ.get("MAIL_HOST")
MAIL_PORT = os.environ.get("MAIL_PORT")
MAIL_EMAIL = os.environ.get("MAIL_EMAIL")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
MONGODB_URI = os.environ.get("MONGODB_URI")
REDIS_TLS_URL = os.environ.get("REDIS_TLS_URL")
print(REDIS_TLS_URL)
REDIS_URL = os.environ.get("REDIS_URL")
ETSY_API_BASE_URI = os.environ.get("ETSY_API_BASE_URI")
ETSY_API_KEY = os.environ.get("ETSY_API_KEY")
ETSY_API_SECRET = os.environ.get("ETSY_API_SECRET")
CALLBACK_URI = os.environ.get("CALLBACK_URI")
STALLION_API_BASE_URL = os.environ.get("STALLION_API_BASE_URL")
STALLION_API_TOKEN = os.environ.get("STALLION_API_TOKEN")
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_USER= os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
