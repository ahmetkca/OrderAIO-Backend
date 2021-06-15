from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from EtsyAPISession import EtsyAPISession
from database import MongoDBConnection, EtsyShopConnection, UpdateEtsyShopConnection
from fastapi.middleware.cors import CORSMiddleware
from bson.objectid import ObjectId

from EtsyAPI import EtsyAPI

load_dotenv()
app = FastAPI()

origins = [
	"http://localhost",
	"http://localhost:3000",
]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

mongodb = MongoDBConnection()


@app.get("/{id}")
async def root(etsy_connection_id: str):
	_id: ObjectId = ObjectId(etsy_connection_id)
	etsy_connection = await mongodb.db["EtsyShopConnections"].find_one({"_id": _id})
	etsy_api_session = EtsyAPISession(etsy_connection["etsy_oauth_token"], etsy_connection["etsy_oauth_token_secret"])
	etsy_api = EtsyAPI(etsy_api_session.get_etsy_api_session())
	user_profile = etsy_api.findAllUserShops()
	return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=user_profile.json())


@app.post("/connect/etsy")
async def connect_etsy_shop():
	request_token_dict: dict = EtsyAPISession.get_request_token()
	new_etsy_connection = await mongodb.db["EtsyShopConnections"].insert_one(jsonable_encoder({
		"verified": False,
		"request_temporary_oauth_token": request_token_dict["oauth_token"],
		"request_temporary_oauth_token_secret": request_token_dict["oauth_token_secret"]
	}))
	response = {
		"login_url": request_token_dict["login_url"],
		"etsy_connection_documentid": str(new_etsy_connection.inserted_id)
	}
	return JSONResponse(status_code=status.HTTP_201_CREATED, content=response)


class VerifyEtsyConnection(BaseModel):
	oauth_verifier: str
	temp_oauth_token: str
	etsy_connection_id: str


@app.put("/verify/etsy")
async def verify_request_tokens(verifyBody: VerifyEtsyConnection = Body(...)):
	print(verifyBody)
	id: ObjectId = ObjectId(verifyBody.etsy_connection_id)
	print(id)
	etsy_connection = await mongodb.db["EtsyShopConnections"].find_one({"_id": id})
	print(etsy_connection)
	access_token_dict: dict = EtsyAPISession.get_access_token(
		resource_owner_key=verifyBody.temp_oauth_token,
		resource_owner_secret=etsy_connection['request_temporary_oauth_token_secret'],
		verifier=verifyBody.oauth_verifier.split("#")[0]
	)
	print(access_token_dict)
	update_etsy_connection_result = await mongodb.db["EtsyShopConnections"].update_one({"_id": id}, {
		"$set": {
			"etsy_oauth_token": access_token_dict["oauth_token"],
			"etsy_oauth_token_secret": access_token_dict["oauth_token_secret"],
			"verified": True
		}
	})
	if update_etsy_connection_result.modified_count == 1:
		return JSONResponse(status_code=status.HTTP_202_ACCEPTED)


# raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


@app.get("/connections/etsy", response_model=List[EtsyShopConnection])
async def get_all_etsy_connections():
	etsy_connections = await mongodb.db["EtsyShopConnections"].find().to_list(10)
	return etsy_connections


@app.get("/connection/etsy/{id}", response_model=EtsyShopConnection)
async def get_etsy_connection(id: str):
	id = ObjectId(id)
	if (
			etsy_connection := await mongodb.db.EtsyShopConnections.find_one({"_id": id})
	) is not None:
		return etsy_connection
	
	raise HTTPException(status_code=404, detail=f"EtsyShopConnection {id} not found")


@app.put("/connection/etsy/{id}", response_model=EtsyShopConnection)
async def update_etsy_connection(id: str, etsy_connection_fields: UpdateEtsyShopConnection = Body(...)):
	id = ObjectId(id)
	etsy_connection = {k: v for k, v in etsy_connection_fields.dict().items() if v is not None}
	
	if len(etsy_connection) >= 1:
		update_result = await mongodb.db["EtsyShopConnections"].update_one({
			"_id": id
		}, {
			"$set": etsy_connection
		})
		
		if update_result.modified_count == 1:
			if (
					updated_etsy_connection := await mongodb.db["EtsyShopConnections"].find_one({"_id": id})
			) is not None:
				return updated_etsy_connection
	
	if (
			existing_etsy_connection := await mongodb.db["EtsyShopConnections"].find_one({"_id": id})
	) is not None:
		return existing_etsy_connection
	
	raise HTTPException(status_code=404, detail=f"EtsyShopConnection {id} not found")


@app.delete("/connection/etsy/{id}")
async def delete_etsy_connection(id: str):
	id = ObjectId(id)
	delete_result = await mongodb.db["EtsyShopConnections"].delete_one({
		"_id": id
	})
	
	if delete_result.deleted_count == 1:
		return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)
	
	raise HTTPException(status_code=404, detail=f"EtsyShopConnection {id} not found")
