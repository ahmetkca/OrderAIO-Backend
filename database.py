import os
from typing import Optional

import motor.motor_asyncio
from bson import ObjectId
from dotenv import load_dotenv
from pydantic import BaseModel, Field, EmailStr

load_dotenv()


class MongoDBConnection:
	def __init__(self):
		self.client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
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


class EtsyShopConnection(BaseModel):
	id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
	app_key: Optional[str]
	app_secret: Optional[str]
	etsy_shop_name: Optional[str] = Field(alias="shop_name")
	etsy_shop_id: Optional[str] = Field(alias="shop_id")
	etsy_owner_email: Optional[EmailStr]
	etsy_user_id: Optional[str] = Field(alias="user_id")
	etsy_oauth_token: Optional[str] = Field(alias="oauth_token")
	etsy_oauth_token_secret: Optional[str] = Field(alias="oauth_token_secret")
	# temp_oauth_verifier: Optional[str] = Field(alias="verifier")
	request_temporary_oauth_token: str = Field(alias="temp_oauth_token")
	request_temporary_oauth_token_secret: str = Field(alias="temp_oauth_token_secret")
	verified: bool = Field(default=False)
	
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
