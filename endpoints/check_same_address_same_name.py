from typing import Optional
from starlette import status
from schemas import UserData
from fastapi import APIRouter, Depends, HTTPException
from oauth2 import is_authenticated
from database import MongoDB

mongodb = MongoDB()

router = APIRouter(
    prefix="/check_same_name_same_address",
    tags=["formatted_address and name"],
    responses={404: {"description": "Not found"}},
)


@router.get('/')
async def get_same_name_same_address(
	receipt_id_to_exclude: Optional[int] = None,
	name: Optional[str] = None,
	first_line: Optional[str] = None, 
	second_line: Optional[str] = None,
	city: Optional[str] = None,
	state: Optional[str] = None,
	zip: Optional[str] = None,
	user: UserData = Depends(is_authenticated)):
	filter = {}
	if receipt_id_to_exclude is None and name is None and first_line is None and second_line is None and city is None and state is None and zip is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No parameters provided.")
	if receipt_id_to_exclude is not None:
		filter['receipt_id_to_exclude'] = receipt_id_to_exclude
	if name is not None:
		filter['name'] = name
	if first_line is not None:
		filter['second_line'] = first_line
	if second_line is not None:
		filter['second_line'] = second_line
	if city is not None:
		filter['city'] = city
	if state is not None:
		filter['state'] = state
	if zip is not None:
		filter['zip'] = zip
	result_from_mongodb = await mongodb.db['Receipts'].find(filter, projection={"receipt_id": True, "_id": False}).to_list(10)
	if result_from_mongodb is None or len(result_from_mongodb) == 0:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No same address same name receipt found.")
	return result_from_mongodb


	

	
