import datetime
from typing import List, Optional
from starlette import status
from schemas import UserData
from fastapi import APIRouter, Depends, HTTPException
from oauth2 import is_authenticated
from database import MongoDB, ReceiptNoteStatus
from pydantic import BaseModel
import pprint

mongodb = MongoDB()

router = APIRouter(
    prefix="/new_search",
    tags=["new search"],
    responses={404: {"description": "Not found"}},
)


class NewSearchBody(BaseModel):
	from_date: Optional[datetime.datetime] = None
	to_date: Optional[datetime.datetime] = None
	query: Optional[str] = None
	receipt_status: Optional[ReceiptNoteStatus] = None
	shop_name: Optional[str] = None
	projection: Optional[List[str]] = None
	


@router.post('/')
async def new_search(
	search_body: NewSearchBody,
	user: UserData = Depends(is_authenticated) 
):
	search_body = search_body.dict()
	search_body = {k: search_body[k] for k in search_body.keys() if search_body[k] is not None}
	pprint.pprint(search_body)
	return search_body