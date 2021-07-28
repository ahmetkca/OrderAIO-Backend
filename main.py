import ujson
import pprint
import smtplib
import ssl
from datetime import datetime, timedelta
from typing import List, Optional

import jwt
from bson.objectid import ObjectId
from fastapi import FastAPI, Depends, Body, HTTPException, status, BackgroundTasks, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from redis import ResponseError
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from EtsyAPISession import EtsyAPISession
from EtsyShopManager import EtsyShopManager
from auth import AuthHandler
from database import MongoDB, MyRedis, EtsyShopConnection, UpdateEtsyShopConnection, InvitationEmail, User, \
	ReceiptNote, CreateReceiptNote, UpdateReceiptNote
from oauth2 import (oauth2_schema,
                    is_authenticated,
                    verify_password)
from schemas import UserData, ReceiptStatus
from EtsyAPI import EtsyAPI, create_etsy_api_with_etsy_connection
from MyScheduler import MyScheduler
from config import FRONTEND_URI, JWT_SECRET, MAIL_EMAIL, MAIL_HOST, MAIL_PASSWORD, MAIL_PORT, SCHEDULED_JOB_INTERVAL


mongodb = MongoDB()
r = MyRedis().r
myScheduler = MyScheduler()

context = ssl.create_default_context()
email_invitation_link = FRONTEND_URI + "/#/register?email={email}&verification_code={verification_code}"


auth_handler = AuthHandler()

origins = [
	FRONTEND_URI,
]

print(origins)
app = FastAPI()


# @app.on_event("startup")
# async def startup_event():
# 	myScheduler.scheduler.start()
# 	etsy_connections = await mongodb.db["EtsyShopConnections"].find().to_list(100)
# 	job_offset = 0
# 	for etsy_connection in etsy_connections:
# 		_id = str(etsy_connection["_id"])
# 		myScheduler.scheduler.add_job(
# 			EtsyShopManager.syncShop,
# 			"interval",
# 			minutes=SCHEDULED_JOB_INTERVAL + job_offset,
# 			kwargs={"etsy_connection_id": _id,
# 			        "db": mongodb.db,
# 			        "r": r},
# 			id=f"{_id}:syncShopProcess",
# 			name=f"{_id}:syncShopProcess",
# 			# jobstore="mongodb"
# 		)
# 		job_offset += 5
# 	myScheduler.scheduler.print_jobs()


@app.on_event("shutdown")
async def shutdown_event():
	await mongodb.client.close()
	r.close()


@app.get("/")
async def root():
	return {"root": "boot"}


app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.post('/user/note', response_model=ReceiptNote)
async def create_note(note_data: CreateReceiptNote = Body(...), user: UserData = Depends(is_authenticated)):
	note_data = jsonable_encoder(note_data)
	insert_note_data = await mongodb.db["Notes"].insert_one({
		"receipt_id": note_data["receipt_id"],
		"note": note_data["note"],
		"created_by": user.user,
		"status": note_data["status"],
		"created_at": datetime.now()
	})
	inserted_note_Data = await mongodb.db["Notes"].find_one({"_id": insert_note_data.inserted_id})
	pprint.pprint(inserted_note_Data)
	return inserted_note_Data


@app.get("/user/note/{receipt_id}", response_model=ReceiptNote)
async def get_note_by_receipt_id(receipt_id: str, user: UserData = Depends(is_authenticated)):
	note = await mongodb.db["Notes"].find_one({"receipt_id": receipt_id})
	if note is not None:
		return note
	else:
		return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"There is no note found for {receipt_id}")


@app.put("/user/note/{receipt_id}", response_model=ReceiptNote)
async def update_note(receipt_id: str, note_data: UpdateReceiptNote = Body(...),
                      user: UserData = Depends(is_authenticated)):
	note_data = jsonable_encoder(note_data)
	note_data["updated_at"] = datetime.now()
	# update_fields = {k: v for k, v in note_data.items() if v is not None}
	update_note_data = await mongodb.db["Notes"].update_one({"receipt_id": receipt_id}, {
		"$set": note_data
	})
	if update_note_data.modified_count == 1:
		note = await mongodb.db["Notes"].find_one({"receipt_id": receipt_id})
		return note


@app.post('/auth/logout')
async def logout(request: Request):
	response = JSONResponse({"status": "logged_out"})
	response.set_cookie(
		oauth2_schema.token_name,
		"",
		expires=0,
		httponly=True,
		secure=True,
	)
	return response


@app.post('/auth/token')
async def authenticate(form_data: OAuth2PasswordRequestForm = Depends()):
	"""
    Verify login details and issue JWT in httpOnly cookie.
    
    Raises:
        HTTPException: 401 error if username or password are not recognised.
    """
	
	user = await mongodb.db['Users'].find_one({"username": form_data.username})
	# print(user)
	# print(verify_password(form_data.password, user['password']))
	if (user is None) or (not verify_password(form_data.password, user['password'])):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid username and/or password')
	payload = {
		"user": user["username"],
		"user_id": user["_id"],
		"scopes": user["scopes"] if user["scopes"] is not None else [""]
	}
	issued_at = datetime.utcnow()
	expires_in = timedelta(hours=6)
	expire = issued_at + expires_in
	# print(expire)
	payload.update({"exp": expire, "iat": issued_at, "sub": "jwt-cookies-test"})
	encoded_jwt = jwt.encode(
		payload,
		JWT_SECRET,
		algorithm="HS256"
	)
	response = JSONResponse({"status": "authenticated"})
	response.set_cookie(
		oauth2_schema.token_name,
		encoded_jwt,
		expires=expires_in.seconds,
		httponly=True,
		secure=True,
	)
	return response


@app.get('/auth/test')
async def auth_test(_request: Request, user: UserData = Depends(is_authenticated)):
	"""Return sample JSON iff the user is authenticated.
    """
	return {"status": "ok", "user": user}


# @app.post('/authenticate')
# def authenticatex(payload=Depends(auth_handler.auth_wrapper)):
# 	return {
# 		"payload": payload
# 	}


@app.post('/invite')
async def invite(background_tasks: BackgroundTasks, invitation_details: InvitationEmail = Body(...),
                 user: UserData = Depends(is_authenticated), ):
	print(invitation_details)
	created_at = invitation_details.created_at
	if "admin" not in user.scopes:
		raise HTTPException(status_code=400, detail='You have no permission to use this endpoint')
	# invitation_details.created_at = datetime.now()
	
	invitation_details = jsonable_encoder(invitation_details)
	check_email_result = await mongodb.db["InvitationEmails"].find_one({"email": invitation_details["email"]})
	if check_email_result is not None:
		if check_email_result["is_registered"]:
			raise HTTPException(status_code=400,
			                    detail=f'{invitation_details["email"]} has already been registered.')
		else:
			raise HTTPException(status_code=400,
			                    detail=f'Invitation email has been already sent to {invitation_details["email"]}')
	invitation_details["created_at"] = created_at
	invite_email_result = await mongodb.db["InvitationEmails"].insert_one(invitation_details)
	inserted_email_invitation = await mongodb.db["InvitationEmails"].find_one({
		"_id": invite_email_result.inserted_id
	})
	print(inserted_email_invitation)
	
	def send_email_invite():
		with smtplib.SMTP_SSL(MAIL_HOST, MAIL_PORT, context=context) as server:
			server.login(MAIL_EMAIL, MAIL_PASSWORD)
			server.sendmail(
				from_addr=MAIL_EMAIL,
				to_addrs=inserted_email_invitation['email'],
				msg=f"""
	            Your verification code is {inserted_email_invitation['verification_code']}
	            
	            The verification code will expire in 30 minutes!
	            
	            You can complete your registration by using below link:
	            {email_invitation_link.format(
					email=inserted_email_invitation['email'],
					verification_code=inserted_email_invitation['verification_code']
				)}
	            """
			)
	
	background_tasks.add_task(send_email_invite)
	
	return {**inserted_email_invitation, "status": "Waiting for verification"}


@app.post("/register", response_model=User, response_model_exclude_defaults=True)
async def register(register_details: User = Body(...)):
	created_at = register_details.created_at
	register_details = jsonable_encoder(register_details)
	# check if the given email is in the InvitationEmails Collection
	print(register_details)
	
	email_query_result = await mongodb.db["InvitationEmails"].find_one({"email": register_details["email"]})
	if email_query_result is None:
		raise HTTPException(status_code=400, detail='This email has not been invited or verification code has been expired.')
	if email_query_result["is_registered"]:
		raise HTTPException(status_code=400, detail='This email has already been registered')
	verification_code = email_query_result['verification_code']
	if register_details['verification_code'] != verification_code:
		raise HTTPException(status_code=400, detail='Invalid verification code')
	check_username_result = await mongodb.db["Users"].find_one({"username": register_details['username']})
	if check_username_result is not None:
		raise HTTPException(status_code=400, detail='This username is already taken')
	# hashed_password = auth_handler.get_password_hash(register_details['password'])
	register_details["created_at"] = created_at
	register_user_result = await mongodb.db["Users"].insert_one(register_details)
	
	check_inserted_user = await mongodb.db["Users"].find_one({"_id": register_user_result.inserted_id})
	if check_inserted_user is None:
		raise HTTPException(status_code=400, detail='There was an error while registering. Please try again later')
	updated_email_invitation = await mongodb.db["InvitationEmails"].update_one({"email": register_details['email']}, {
		"$set": {
			"is_registered": True
		}
	})
	print(f"upserted id: {updated_email_invitation.upserted_id}")
	find_email_invitation = await mongodb.db['InvitationEmails'].find_one({"email": email_query_result["email"]})
	print(find_email_invitation)
	find_email_invitation["created_at"] = find_email_invitation["created_at"].isoformat()
	return JSONResponse(status_code=status.HTTP_200_OK, content=find_email_invitation)


class LoginDetails(BaseModel):
	username: str
	password: str


# @app.post("/login")
# async def login(auth_details: LoginDetails = Body(...)):
# 	auth_details = jsonable_encoder(auth_details)
# 	user = await mongodb.db["Users"].find_one({"username": auth_details['username']})
# 	if (user is None) or (not auth_handler.verify_password(auth_details['password'], user['password'])):
# 		raise HTTPException(status_code=401, detail='Invalid username and/or password')
# 	token = auth_handler.encode_token(user['_id'], user['username'], user['is_admin'])
# 	return {
# 		"token": token
# 	}


@app.get("/search")
async def search(request: Request,
                 from_date: Optional[datetime] = None,
                 to_date: Optional[datetime] = None,
                 query: Optional[str] = None,
                 is_completed: Optional[bool] = None,
                 shop_name: Optional[str] = None,
                 projection: Optional[List[str]] = Query(None),
                 user: UserData = Depends(is_authenticated)):
	path = request.url.path + "?" + request.url.query
	cached = r.get(path)
	print(projection)
	if cached is not None:
		print(f"{path} is cached.")
		res = ujson.loads(cached)
		return res
	mongodb_filter = {}
	collation = {}
	if is_completed is None and from_date is None and to_date is None and query is None and shop_name is None:
		return {"error": "No query parameter(s) provided."}
	if is_completed is not None:
		mongodb_filter["is_completed"] = is_completed
	if shop_name is not None:
		mongodb_filter["shop_name"] = shop_name
	if from_date is not None and to_date is not None:
		mongodb_filter["max_due_date"] = {
			"$lte": to_date,
			"$gte": from_date
		}
	elif from_date is not None and to_date is None:
		mongodb_filter["max_due_date"] = {
			"$lte": from_date,
			"$gte": from_date
		}
	elif to_date is not None and from_date is None:
		mongodb_filter["max_due_date"] = {
			"$lte": to_date,
			"$gte": to_date
		}
	print(mongodb_filter)
	if query is not None:
		is_int: bool = False
		try:
			int(query)
		except ValueError:
			is_int = False
		else:
			query = int(query)
			is_int = True
		if is_int:
			mongodb_filter["receipt_id"] = query
		else:
			mongodb_filter["name"] = query
			collation["locale"] = "en"
			collation["strength"] = 1
	proj = {"_id": False}
	if projection is not None and len(projection) > 0:
		for p in projection:
			if p == "_id":
				continue
			proj[p] = True
	print(mongodb_filter)
	receipts = await mongodb.db["Receipts"].find(mongodb_filter,
	                                             collation=collation if collation is not None and len(
		                                             collation.keys()) > 0 else None,
	                                             projection=proj).to_list(10000)

	for receipt in receipts:
		try:
			receipt["max_due_date"] = receipt["max_due_date"].isoformat()
			receipt["min_due_date"] = receipt["min_due_date"].isoformat()
		except KeyError:
			continue
	try:
		r.set(path, ujson.dumps(receipts), ex=1800, nx=True)
	except ResponseError as e:
		print(e)
	finally:
		return receipts


@app.get("/async_etsy/sync/{etsy_connection_id}")
async def sync(etsy_connection_id: str, background_tasks: BackgroundTasks, user: UserData = Depends(is_authenticated)):
	is_running = r.get(f"{etsy_connection_id}:is_running")
	if is_running == "True":
		return {
			"background-task": "already running"
		}
	background_tasks.add_task(
		func=EtsyShopManager.syncShop,
		etsy_connection_id=etsy_connection_id,
		db=mongodb.db,
		r=r
	)
	
	return {
		"background-task": "processing"
	}


@app.get('/receipts/{etsy_connection_id}/{receipt_id}')
async def get_receipt_by_id(etsy_connection_id: str, receipt_id: str, user: UserData = Depends(is_authenticated)):
	etsy_api = await create_etsy_api_with_etsy_connection(mongodb.db, etsy_connection_id, 1)
	# shop_id = etsy_connection["etsy_shop_id"]
	receipt = etsy_api.getShop_Receipt2(receipt_id)
	print(receipt)
	return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=receipt)


@app.get('/listings/{etsy_connection_id}/{listing_id}')
async def get_listing(etsy_connection_id: str, listing_id: int):
	etsy_api = await create_etsy_api_with_etsy_connection(mongodb.db, etsy_connection_id, 1)
	etsy_api.getListing(listing_id)


@app.get('/shipping/templates/{etsy_connection_id}/{shipping_template_id}')
async def get_shipping_template(etsy_connection_id: str, shipping_template_id: int):
	etsy_api = await create_etsy_api_with_etsy_connection(mongodb.db, etsy_connection_id, 1)
	etsy_api.getShippingTemplate(shipping_template_id)


@app.get("/shops/{etsy_connection_id}/receipts/{status}/")
async def get_receipts_by_status(etsy_connection_id: str, status: ReceiptStatus):
	(etsy_connection, etsy_api) = await create_etsy_api_with_etsy_connection(mongodb.db, etsy_connection_id)
	shop_id = etsy_connection["etsy_shop_id"]
	etsy_api.findAllShopReceiptsByStatus(shop_id, status)


@app.get("/receipts/{etsy_connection_id}")
async def get_all_receipts_by_etsy_connection(etsy_connection_id: str,
                                              min_created: Optional[int] = None,
                                              max_created: Optional[int] = None,
                                              min_last_modified: Optional[int] = None,
                                              max_last_modified: Optional[int] = None,
                                              was_paid: Optional[bool] = None,
                                              was_shipped: Optional[bool] = None,
                                              user: UserData = Depends(is_authenticated)):
	# _id: ObjectId = ObjectId(etsy_connection_id)
	# etsy_connection = await mongodb.db["EtsyShopConnections"].find_one({"_id": _id})
	# etsy_api_session = EtsyAPISession(etsy_connection["etsy_oauth_token"], etsy_connection["etsy_oauth_token_secret"],
	# 								client_key=etsy_connection["app_key"],
	# 								client_secret=etsy_connection["app_secret"])
	# etsy_api = EtsyAPI(etsy_api_session.get_etsy_api_session())
	(etsy_connection, etsy_api) = await create_etsy_api_with_etsy_connection(mongodb.db, etsy_connection_id)
	shop_id = etsy_connection["etsy_shop_id"]
	all_receipts = etsy_api.findAllShopReceipts(shop_id,
	                                            min_created=min_created,
	                                            max_created=max_created,
	                                            min_last_modified=min_last_modified,
	                                            max_last_modified=max_last_modified,
	                                            was_paid=was_paid,
	                                            was_shipped=was_shipped)
	# pprint.pprint(all_receipts)
	return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=all_receipts)


@app.get('/search/{etsy_connection_id}')
async def searchTest(etsy_connection_id: str):
	(etsy_connection, etsy_api) = await create_etsy_api_with_etsy_connection(mongodb.db, etsy_connection_id)
	shop_id = etsy_connection["etsy_shop_id"]
	res = etsy_api.searchAllShopReceipts(shop_id)
	return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=res)


@app.get('/transactions/{receipt_id}/{etsy_connection_id}')
async def get_all_transactions_by_receipt_id(receipt_id: str, etsy_connection_id: str,
                                             user: UserData = Depends(is_authenticated)):
	etsy_api = await create_etsy_api_with_etsy_connection(mongodb.db, etsy_connection_id, 1)
	all_transactions_by_receipt_id = etsy_api.findAllShop_Receipt2Transactions(receipt_id)
	return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=all_transactions_by_receipt_id)


@app.get('/images/{listing_id}/{listing_image_id}/{etsy_connection_id}')
async def get_image_of_transaction(listing_id: str, listing_image_id: str, etsy_connection_id: str,
                                   user: UserData = Depends(is_authenticated)):
	etsy_api = await create_etsy_api_with_etsy_connection(mongodb.db, etsy_connection_id, 1)
	images = etsy_api.getImage_Listing(listing_id, listing_image_id)
	return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=images.json())


class ConnectEtsyAppDetails(BaseModel):
	app_key: Optional[str]
	app_secret: Optional[str]


@app.post("/connect/etsy")
async def connect_etsy_shop(app_details: ConnectEtsyAppDetails = Body(...), user: UserData = Depends(is_authenticated)):
	print(app_details)
	request_token_dict: dict = EtsyAPISession.get_request_token(app_details.app_key, app_details.app_secret)
	app_details = jsonable_encoder(app_details)
	app_details["created_at"] = datetime.utcnow()
	new_etsy_connection = await mongodb.db["EtsyShopConnections"].insert_one({
		"verified": False,
		"app_key": app_details["app_key"],
		"app_secret": app_details["app_secret"],
		"request_temporary_oauth_token": request_token_dict["oauth_token"],
		"request_temporary_oauth_token_secret": request_token_dict["oauth_token_secret"],
		"created_at": app_details["created_at"]
	})
	response = {
		"login_url": request_token_dict["login_url"],
		"etsy_connection_documentid": str(new_etsy_connection.inserted_id)
	}
	return JSONResponse(status_code=status.HTTP_200_OK, content=response)


class VerifyEtsyConnection(BaseModel):
	oauth_verifier: str
	temp_oauth_token: str
	etsy_connection_id: str


@app.put("/verify/etsy")
async def verify_request_tokens(verify_body: VerifyEtsyConnection = Body(...),
                                user: UserData = Depends(is_authenticated)):
	etsy_connection_id: ObjectId = ObjectId(verify_body.etsy_connection_id)
	etsy_connection = await mongodb.db["EtsyShopConnections"].find_one({"_id": etsy_connection_id})
	if etsy_connection is None or etsy_connection["verified"]:
		raise HTTPException(status_code=400, detail="Etsy connection id not found or it has already been connected.")
	access_token_dict: dict = EtsyAPISession.get_access_token(
		resource_owner_key=verify_body.temp_oauth_token,
		resource_owner_secret=etsy_connection['request_temporary_oauth_token_secret'],
		verifier=verify_body.oauth_verifier.split("#")[0],
		client_key=etsy_connection['app_key'],
		client_secret=etsy_connection['app_secret']
	)
	if len(access_token_dict.keys()) == 0:
		await mongodb.db["EtsyShopConnections"].delete_one({"_id": etsy_connection_id})
		raise HTTPException(status_code=400, detail="Request token has expired.")
	update_etsy_connection_result = await mongodb.db["EtsyShopConnections"].update_one({"_id": etsy_connection_id}, {
		"$set": {
			"etsy_oauth_token": access_token_dict["oauth_token"],
			"etsy_oauth_token_secret": access_token_dict["oauth_token_secret"],
			"verified": True,
			"updated_at": datetime.utcnow()
		}
	})
	if update_etsy_connection_result.modified_count == 1:
		etsy_api_session = EtsyAPISession(access_token_dict["oauth_token"],
		                                  access_token_dict["oauth_token_secret"],
		                                  client_key=etsy_connection["app_key"],
		                                  client_secret=etsy_connection["app_secret"])
		etsy_api = EtsyAPI(etsy_api_session.get_etsy_api_session())
		all_shops = etsy_api.findAllUserShops()
		shop_id = None
		shop_name = None
		shop_url = None
		shop_banner_url = None
		shop_icon_url = None
		all_shops_json = all_shops.json()
		if all_shops_json['count'] != 0:
			shop_id = all_shops_json['results'][0]['shop_id']
			shop_name = all_shops_json['results'][0]['shop_name']
			shop_url = all_shops_json['results'][0]['url']
			shop_banner_url = all_shops_json['results'][0]['image_url_760x100']
			shop_icon_url = all_shops_json['results'][0]['icon_url_fullxfull']
		user = etsy_api.getUser()
		etsy_owner_email = None
		if user.json()['count'] != 0:
			etsy_owner_email = user.json()['results'][0]['primary_email']
		
		update_etsy_connection_shop_details_result = await mongodb.db["EtsyShopConnections"].update_one(
			{"_id": etsy_connection_id}, {
				"$set": {
					"etsy_owner_email": etsy_owner_email,
					"etsy_shop_id": shop_id,
					"etsy_shop_name": shop_name,
					"shop_url": shop_url,
					"shop_icon_url": shop_icon_url,
					"shop_banner_url": shop_banner_url,
					"updated_at": datetime.utcnow()
				}
			})
		if update_etsy_connection_shop_details_result.modified_count == 1:
			return JSONResponse(status_code=status.HTTP_200_OK, content={"detail": "Successfully connected to Etsy."})
		


@app.get("/connections/etsy", response_model=List[EtsyShopConnection])
async def get_all_etsy_connections(user: UserData = Depends(is_authenticated)):
	etsy_connections = await mongodb.db["EtsyShopConnections"].find(projection={
		"app_key": False,
		"app_secret": False,
		"etsy_oauth_token": False,
		"etsy_oauth_token_secret": False,
		"request_temporary_oauth_token": False,
		"request_temporary_oauth_token_secret": False
	}).to_list(100)
	pprint.pprint(etsy_connections)
	return etsy_connections


@app.get("/connection/etsy/{etsy_connection_id}", response_model=EtsyShopConnection)
async def get_etsy_connection(etsy_connection_id: str, user: UserData = Depends(is_authenticated)):
	_id = ObjectId(etsy_connection_id)
	etsy_connection = await mongodb.db.EtsyShopConnections.find_one(filter={
		"_id": _id
	}, projection={
		"app_key": False,
		"app_secret": False,
		"etsy_oauth_token": False,
		"etsy_oauth_token_secret": False,
		"request_temporary_oauth_token": False,
		"request_temporary_oauth_token_secret": False
	})
	if etsy_connection is not None:
		return etsy_connection
	
	raise HTTPException(status_code=404, detail=f"EtsyShopConnection {_id} not found")


@app.put("/connection/etsy/{id}", response_model=EtsyShopConnection)
async def update_etsy_connection(id: str, etsy_connection_fields: UpdateEtsyShopConnection = Body(...),
                                 user: UserData = Depends(is_authenticated)):
	id = ObjectId(id)
	etsy_connection = {k: v for k, v in etsy_connection_fields.dict().items() if v is not None}
	
	if len(etsy_connection) >= 1:
		update_result = await mongodb.db["EtsyShopConnections"].update_one({
			"_id": id
		}, {
			"$set": etsy_connection
		})
		
		if update_result.modified_count == 1:
			updated_etsy_connection = await mongodb.db["EtsyShopConnections"].find_one({"_id": id})
			if updated_etsy_connection is not None:
				return updated_etsy_connection
	
	existing_etsy_connection = await mongodb.db["EtsyShopConnections"].find_one({"_id": id})
	if existing_etsy_connection is not None:
		return existing_etsy_connection
	
	raise HTTPException(status_code=404, detail=f"EtsyShopConnection {id} not found")


@app.delete("/connection/etsy/{id}")
async def delete_etsy_connection(id: str, user: UserData = Depends(is_authenticated)):
	id = ObjectId(id)
	delete_result = await mongodb.db["EtsyShopConnections"].delete_one({
		"_id": id
	})
	
	if delete_result.deleted_count == 1:
		return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)
	
	raise HTTPException(status_code=404, detail=f"EtsyShopConnection {id} not found")
