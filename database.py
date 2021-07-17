import os
from datetime import datetime
from enum import Enum
from typing import Optional, List
import secrets
from urllib.parse import urlparse

import motor.motor_asyncio
import redis
from bson import ObjectId

from pydantic import BaseModel, Field, EmailStr, AnyHttpUrl, validator
from oauth2 import get_password_hash
from config import MONGODB_URI, REDIS_URL



# class MongoDBConnection:
# 	def __init__(self):
# 		self.client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
# 		self.db = self.client.multiorder

class MyRedis(object):
	_instance = None
	
	def __new__(cls, *args, **kwargs):
		if cls._instance is None:
			print("#===================#")
			cls._instance = object.__new__(cls)
			try:
				print("Connecting to Redis...")
				url = urlparse(REDIS_URL)
				r = redis.Redis(host=url.hostname, 
				                port=url.port, 
				                username=url.username, 
				                password=url.password,
				                ssl=True,
				                ssl_cert_reqs=None, decode_responses=True)
				MyRedis._instance.r = r
				redis_info = MyRedis._instance.r.info()
				MyRedis._instance.r.ping()
			except Exception as e:
				print("Error: Redis connection not established {}".format(e))
			else:
				print("Redis connection established\nconnected clients: {}\nredis_version: {}".format(redis_info["connected_clients"],
				                                                                                      redis_info["redis_version"]))
			print("#===================#")
		return cls._instance
	
	def __init__(self):
		self.r: redis.Redis = self._instance.r
		
	def __del__(self):
		self.r.close()


class MongoDB(object):
	_instance = None
	
	def __new__(cls):
		if cls._instance is None:
			print("#===================#")
			print("No connected MongoDB connection found.")
			cls._instance = object.__new__(cls)
			try:
				print("Connecting to MongoDB")
				mongodb = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
				MongoDB._instance.client = mongodb
			except Exception as e:
				print("Error: MongoDB connection not established {}".format(e))
			else:
				print("MongoDB connection successfully established.")
			print("#===================#")
		return cls._instance
	
	def __init__(self):
		self.client = self._instance.client
		self.db = self.client.multiorder


class PyObjectId(ObjectId):
	@classmethod
	def __get_validators__(cls):
		yield cls.validate
	
	@classmethod
	def validate(cls, v):
		if not ObjectId.is_valid(v):
			raise ValueError("Invalid objectid")
		return ObjectId(v)
	
	@classmethod
	def __modify_schema__(cls, field_schema):
		field_schema.update(type="string")


class ReceiptNoteStatus(str, Enum):
	completed: str = "COMPLETED"
	uncompleted: str = "UNCOMPLETED"


class CreateReceiptNote(BaseModel):
	receipt_id: str
	note: str
	status: ReceiptNoteStatus = Field(default=ReceiptNoteStatus.uncompleted)


class UpdateReceiptNote(BaseModel):
	receipt_id: str
	note: Optional[str]
	status: Optional[ReceiptNoteStatus]


class ReceiptNote(BaseModel):
	id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
	receipt_id: str
	created_by: str
	updated_by: Optional[str]
	note: str
	status: ReceiptNoteStatus = Field(default=ReceiptNoteStatus.uncompleted)
	
	class Config:
		allow_population_by_field_name = True
		arbitrary_types_allowed = True
		validate_assignment = True
		json_encoders = {ObjectId: str}


class InvitationEmail(BaseModel):
	id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
	email: EmailStr = Field(allow_mutation=False, unique=True)
	verification_code: str = None
	is_registered: bool = False
	created_at: datetime = Field(default=datetime.utcnow())
	
	@validator('verification_code', pre=True, always=True)
	def generate_verification_code(cls, v) -> str:
		return secrets.token_urlsafe(16)
	
	@validator('is_registered', pre=True, always=True)
	def check_is_registered(cls, v):
		return False
	
	class Config:
		allow_population_by_field_name = True
		arbitrary_types_allowed = True
		validate_assignment = True
		json_encoders = {ObjectId: str}


class Roles(str, Enum):
	admin = "admin"
	user = "user"


class User(BaseModel):
	id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
	email: EmailStr = Field(unique=True)
	username: str = Field(unique=True)
	password: str = Field(...)
	scopes: List[Roles] = Field(default=[Roles.user])
	verification_code: str = Field(...)
	created_at: datetime = Field(default=datetime.utcnow())
	
	# @validator('is_admin', pre=True, always=True)
	# def default_is_admin(cls, v):
	# 	if v:
	# 		return False
	# 	return False
	
	@validator('password', pre=True, always=True)
	def hash_password(cls, v):
		return get_password_hash(v)
	
	class Config:
		allow_mutation = False
		allow_population_by_field_name = True
		arbitrary_types_allowed = True
		validate_assignment = True
		json_encoders = {ObjectId: str}


class EtsyShopConnection(BaseModel):
	id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
	app_key: Optional[str]
	app_secret: Optional[str]
	etsy_shop_name: Optional[str]
	etsy_shop_id: Optional[str]
	shop_icon_url: Optional[AnyHttpUrl]
	shop_banner_url: Optional[AnyHttpUrl]
	shop_url: Optional[AnyHttpUrl]
	etsy_owner_email: Optional[EmailStr]
	etsy_user_id: Optional[str]
	etsy_oauth_token: Optional[str]
	etsy_oauth_token_secret: Optional[str]
	# temp_oauth_verifier: Optional[str] = Field(alias="verifier")
	request_temporary_oauth_token: Optional[str]
	request_temporary_oauth_token_secret: Optional[str]
	verified: bool = Field(default=False)
	created_at: datetime = Field(default=datetime.utcnow())
	
	class Config:
		allow_population_by_field_name = True
		arbitrary_types_allowed = True
		json_encoders = {ObjectId: str}


class UpdateEtsyShopConnection(BaseModel):
	etsy_shop_name: Optional[str]
	etsy_shop_id: Optional[str]
	etsy_owner_email: Optional[EmailStr]
	etsy_user_id: Optional[str]
	etsy_oauth_token: Optional[str]
	etsy_oauth_token_secret: Optional[str]
	verified: Optional[bool]
# temp_oauth_verifier: Optional[str]
