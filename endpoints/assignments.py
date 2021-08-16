from starlette import status
from schemas import UserData
from fastapi import APIRouter, Depends, HTTPException
from oauth2 import is_authenticated
from database import MongoDB

mongodb = MongoDB()

router = APIRouter(
    prefix="/assignments",
    tags=["assignments"],
    responses={404: {"description": "Not found"}},
)


@router.get('/')
async def read_assigned_notes(user: UserData = Depends(is_authenticated)):
	assigned_notes = await mongodb.db['Notes'].find({'assigned_to': user.user}, projection={'_id': False}).to_list(999)
	print(user.user)
	if assigned_notes is None or len(assigned_notes) == 0:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No assigned receipts found")
	return assigned_notes
