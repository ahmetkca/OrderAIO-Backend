import datetime
from typing import List, Optional
from starlette import status
from schemas import UserData
from fastapi import APIRouter, Depends, HTTPException
from oauth2 import is_authenticated
from database import MongoDB, ReceiptNoteStatus
from pydantic import BaseModel
import pprint
from LabelProvider import StallionAPI
from config import STALLION_API_TOKEN

mongodb = MongoDB()

router = APIRouter(
    prefix="/shipments",
    tags=["shipments"],
    responses={404: {"description": "Not found"}},
)


@router.get('/status/{order_id}', status_code=status.HTTP_200_OK)
async def get_stallion_status_by_order_id(order_id: int, user: UserData = Depends(is_authenticated)):
	stallion_api: StallionAPI = StallionAPI(api_token=STALLION_API_TOKEN)
	res: dict = await stallion_api.get_status_by_order_id(order_id=order_id)
	if res is not None and res.get('success'):
		return res.get('status')
	else:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No Label found for Order ID {order_id}")


@router.post('/purchase/{order_id}')
async def purchase_stallion_label(order_id: int, user: UserData = Depends(is_authenticated)):
	# First check if there is already label with given order id
	# if there is no label found with the given id then check if there is enough credit to purchase label
	# if there is enough creadit then go ahead and purchase the label
	# with given name, address, package content, package size, etc.
	...

@router.get('/')
async def return_all_shipments_by_parameters():
	...
