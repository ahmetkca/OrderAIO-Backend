import os
from dotenv import load_dotenv
load_dotenv()

SCHEDULED_JOB_INTERVAL = 25

NO_CONCURRENT = 10
LIMIT = 100

FRONTEND_URI = os.environ.get("FRONTEND_URI")
JWT_SECRET = os.environ.get("JWT_SECRET")
MAIL_HOST = os.environ.get("MAIL_HOST")
MAIL_PORT = os.environ.get("MAIL_PORT")
MAIL_EMAIL = os.environ.get("MAIL_EMAIL")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
MONGODB_URI = os.environ.get("MONGODB_URI")
REDIS_URL = os.environ.get("REDIS_URL")
ETSY_API_BASE_URI = os.environ.get("ETSY_API_BASE_URI")
ETSY_API_KEY = os.environ.get("ETSY_API_KEY")
ETSY_API_SECRET = os.environ.get("ETSY_API_SECRET")
CALLBACK_URI = os.environ.get("CALLBACK_URI")
