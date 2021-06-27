# from pymemcache.client import base
import json

# docker build -t myimage .
# docker run --env-file .env -d --name mycontainer -p 80:80 myimage
import os
# files = [f for f in os.listdir('.') if os.path.isfile(f)]
# for f in files:
#     print(f"{f} whattttttttttttttt")

import pprint
import smtplib
import ssl
from datetime import datetime, timedelta
from typing import List, Optional

import jwt
from bson.objectid import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Body, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request


from EtsyAPISession import EtsyAPISession
from auth import AuthHandler
from database import MongoDBConnection, EtsyShopConnection, UpdateEtsyShopConnection, InvitationEmail, User, \
    ReceiptNote, CreateReceiptNote, UpdateReceiptNote
from oauth2 import (oauth2_schema,
                    is_authenticated,
                    verify_password)
from schemas import UserData
from EtsyAPI import EtsyAPI, create_etsy_api_with_etsy_connection

# memcache = base.Client(('localhost', 11211))

context = ssl.create_default_context()
email_invitation_link = os.getenv("FRONTEND_URI") + "/#/register?email={email}&verification_code={verification_code}"

load_dotenv("../.env")

auth_handler = AuthHandler()

origins = [
    os.getenv("FRONTEND_URI"),
]
# middleware = [Middleware(CORSMiddleware, allow_origins=origins)]
print(origins)
app = FastAPI()

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

mongodb = MongoDBConnection()


# def without_keys(d, keys):
# 	return {x: d[x] for x in d if x not in keys}
@app.get("/test/env")
async def test_env():
    return {
        k: v for k, v in os.environ.items()
    }

@app.post('/user/note', response_model=ReceiptNote)
async def create_note(note_data: CreateReceiptNote = Body(...), user: UserData = Depends(is_authenticated)):
    note_data = jsonable_encoder(note_data)
    insert_note_data = await mongodb.db["Notes"].insert_one({
        "receipt_id": note_data["receipt_id"],
        "note": note_data["note"],
        "created_by": user.user,
        "status": note_data["status"]
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
async def update_note(receipt_id: str, note_data: UpdateReceiptNote = Body(...), user: UserData = Depends(is_authenticated)):
    note_data = jsonable_encoder(note_data)
    update_fields = {k: v for k, v in note_data.items() if v is not None}
    update_note_data = await mongodb.db["Notes"].update_one({"receipt_id": receipt_id}, {
        "$set": update_fields
    })
    if update_note_data.modified_count == 1:
        note = await mongodb.db["Notes"].find_one({"receipt_id": receipt_id})
        return note
    


@app.post('/auth/token')
async def authenticate(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Verify login details and issue JWT in httpOnly cookie.
    
    Raises:
        HTTPException: 401 error if username or password are not recognised.
    """
    
    user = await mongodb.db['Users'].find_one({"username": form_data.username})
    print(user)
    print(verify_password(form_data.password, user['password']))
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
        os.getenv("JWT_SECRET"),
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


@app.post('/authenticate')
def authenticatex(payload=Depends(auth_handler.auth_wrapper)):
    return {
        "payload": payload
    }


@app.post('/invite')
async def invite(invitation_details: InvitationEmail = Body(...), user: UserData = Depends(is_authenticated)):
    if "admin" not in user["scopes"]:
        raise HTTPException(status_code=400, detail='You have no permission to use this route')
    invitation_details = jsonable_encoder(invitation_details)
    invite_email_result = await mongodb.db["InvitationEmails"].insert_one(jsonable_encoder(invitation_details))
    inserted_email_invitation = await mongodb.db["InvitationEmails"].find_one({
        "_id": invite_email_result.inserted_id
    })
    print(inserted_email_invitation)
    with smtplib.SMTP_SSL(os.getenv("MAIL_HOST"), os.getenv("MAIL_PORT"), context=context) as server:
        server.login(os.getenv("MAIL_EMAIL"), os.getenv("MAIL_PASSWORD"))
        server.sendmail(
            from_addr=os.getenv("MAIL_EMAIL"),
            to_addrs=inserted_email_invitation['email'],
            msg=f"""
            Your verification code is {inserted_email_invitation['verification_code']}
            {email_invitation_link.format(
                email=inserted_email_invitation['email'],
                verification_code=inserted_email_invitation['verification_code']
            )}
            """
        )
    
    return inserted_email_invitation


@app.post("/register", response_model=User, response_model_exclude_defaults=True)
async def register(register_details: User = Body(...)):
    register_details = jsonable_encoder(register_details)
    # check if the given email is in the InvitationEmails Collection
    print(register_details)
    email_query_result = await mongodb.db["InvitationEmails"].find_one({"email": register_details["email"]})
    if email_query_result is None:
        raise HTTPException(status_code=400, detail='This email has not been invited')
    if email_query_result["is_registered"]:
        raise HTTPException(status_code=400, detail='This email has already been registered')
    verification_code = email_query_result['verification_code']
    if register_details['verification_code'] != verification_code:
        raise HTTPException(status_code=400, detail='Invalid verification code')
    check_username_result = await mongodb.db["Users"].find_one({"username": register_details['username']})
    if check_username_result is not None:
        raise HTTPException(status_code=400, detail='This username is already taken')
    # hashed_password = auth_handler.get_password_hash(register_details['password'])
    register_user_result = await mongodb.db["Users"].insert_one(register_details)
    check_inserted_user = await mongodb.db["Users"].find_one({"_id": register_user_result.inserted_id})
    if check_inserted_user is None:
        raise HTTPException(status_code=400, detail='There was an error while registering. Please try again later')
    updated_email_invitation = await mongodb.db["InvitationEmails"].update_one({"email": register_details['email']}, {
        "$set": {
            "is_registered": True
        }
    })
    find_email_invitation = await mongodb.db['InvitationEmails'].find_one({"_id": updated_email_invitation.upserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=find_email_invitation)


class LoginDetails(BaseModel):
    username: str
    password: str


@app.post("/login")
async def login(auth_details: LoginDetails = Body(...)):
    auth_details = jsonable_encoder(auth_details)
    user = await mongodb.db["Users"].find_one({"username": auth_details['username']})
    if (user is None) or (not auth_handler.verify_password(auth_details['password'], user['password'])):
        raise HTTPException(status_code=401, detail='Invalid username and/or password')
    token = auth_handler.encode_token(user['_id'], user['username'], user['is_admin'])
    return {
        "token": token
    }


@app.get("/receipts/{etsy_connection_id}")
async def get_all_receipts_by_etsy_connection(etsy_connection_id: str, user: UserData = Depends(is_authenticated)):
    # _id: ObjectId = ObjectId(etsy_connection_id)
    # etsy_connection = await mongodb.db["EtsyShopConnections"].find_one({"_id": _id})
    # etsy_api_session = EtsyAPISession(etsy_connection["etsy_oauth_token"], etsy_connection["etsy_oauth_token_secret"],
    # 								client_key=etsy_connection["app_key"],
    # 								client_secret=etsy_connection["app_secret"])
    # etsy_api = EtsyAPI(etsy_api_session.get_etsy_api_session())
    (etsy_connection, etsy_api) = await create_etsy_api_with_etsy_connection(mongodb.db, etsy_connection_id)
    shop_id = etsy_connection["etsy_shop_id"]
    all_receipts = etsy_api.findAllShopReceipts(shop_id)
    pprint.pprint(all_receipts)
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
    new_etsy_connection = await mongodb.db["EtsyShopConnections"].insert_one(jsonable_encoder({
        "verified": False,
        "app_key": app_details.app_key,
        "app_secret": app_details.app_secret,
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
async def verify_request_tokens(verify_body: VerifyEtsyConnection = Body(...),
                                user: UserData = Depends(is_authenticated)):
    etsy_connection_id: ObjectId = ObjectId(verify_body.etsy_connection_id)
    etsy_connection = await mongodb.db["EtsyShopConnections"].find_one({"_id": etsy_connection_id})
    access_token_dict: dict = EtsyAPISession.get_access_token(
        resource_owner_key=verify_body.temp_oauth_token,
        resource_owner_secret=etsy_connection['request_temporary_oauth_token_secret'],
        verifier=verify_body.oauth_verifier.split("#")[0],
        client_key=etsy_connection['app_key'],
        client_secret=etsy_connection['app_secret']
    )
    update_etsy_connection_result = await mongodb.db["EtsyShopConnections"].update_one({"_id": etsy_connection_id}, {
        "$set": {
            "etsy_oauth_token": access_token_dict["oauth_token"],
            "etsy_oauth_token_secret": access_token_dict["oauth_token_secret"],
            "verified": True
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
        if all_shops.json()['count'] != 0:
            shop_id = all_shops.json()['results'][0]['shop_id']
            shop_name = all_shops.json()['results'][0]['shop_name']
            shop_url = all_shops.json()['results'][0]['url']
            shop_banner_url = all_shops.json()['results'][0]['image_url_760x100']
            shop_icon_url = all_shops.json()['results'][0]['icon_url_fullxfull']
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
                    "shop_banner_url": shop_banner_url
                }
            })
        if update_etsy_connection_shop_details_result.modified_count == 1:
            return JSONResponse(status_code=status.HTTP_202_ACCEPTED)
        else:
            return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/connections/etsy", response_model=List[EtsyShopConnection])
async def get_all_etsy_connections(user: UserData = Depends(is_authenticated)):
    etsy_connections = await mongodb.db["EtsyShopConnections"].find(projection={
        "app_key": False,
        "app_secret": False,
        "etsy_oauth_token": False,
        "etsy_oauth_token_secret": False,
        "request_temporary_oauth_token": False,
        "request_temporary_oauth_token_secret": False
    }).to_list(10)
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
