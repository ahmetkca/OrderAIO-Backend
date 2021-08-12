from starlette import status
from schemas import UserData
from fastapi import APIRouter, Depends, HTTPException
from oauth2 import is_authenticated
from database import MongoDB, MyRedis

mongodb = MongoDB()
r = MyRedis().r

router = APIRouter(
    prefix="/connections_info/",
    tags=["connections", "info"],
    responses={404: {"description": "Not found"}},
)


@router.get('/{etsy_connection_id}')
async def get_etsy_connection_info(etsy_connection_id: str, user: UserData = Depends(is_authenticated)):
    ...