from motor.motor_asyncio import AsyncIOMotorClient
from .mongodb import db
from ..core.config import MONGODB_URI, MAX_CONNECTIONS_COUNT, MIN_CONNECTIONS_COUNT


async def connect_to_mongo():
	db.client = AsyncIOMotorClient(MONGODB_URI,
	                               maxPoolSize=MAX_CONNECTIONS_COUNT,
	                               minPoolSize=MIN_CONNECTIONS_COUNT)


async def close_mongo_connection():
	db.client.close()
