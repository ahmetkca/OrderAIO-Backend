from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from core.config import ALLOWED_HOSTS
from .db.mongodb_utils import close_mongo_connection, connect_to_mongo

app = FastAPI()

if not ALLOWED_HOSTS:
	ALLOWED_HOST = ["*"]

app.add_middleware(
	CORSMiddleware,
	allow_origins=ALLOWED_HOSTS,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)
