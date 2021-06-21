from fastapi import APIRouter

router = APIRouter(
	prefix="/users",
	tags=["users"]
)

@router.get('/')
async def read_users():
	# Query users from MongoDB Database and return them
	pass


@router.get('/{user_id}')
async def read_users(user_id: str):
	# Check if the given user_id exist in the MongoDB Database
	# iff it exists, return the user document
	pass
