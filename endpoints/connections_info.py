import pytz
from starlette import status
from schemas import UserData
from fastapi import APIRouter, Depends, HTTPException
from oauth2 import is_authenticated
from database import MongoDB, MyRedis
from bson import ObjectId
from datetime import datetime
from database import ReceiptNoteStatus

mongodb = MongoDB()
r = MyRedis().r

router = APIRouter(
    prefix="/connections_info",
    tags=["connections", "info"],
    responses={404: {"description": "Not found"}},
)


@router.get('/{etsy_connection_id}')
async def get_etsy_connection_info(etsy_connection_id: str, user: UserData = Depends(is_authenticated)):
    last_updated = r.get(f'{etsy_connection_id}:last_updated')
    if last_updated is not None:
        last_updated = int(last_updated)
        last_updated = datetime.fromtimestamp(last_updated, pytz.timezone('Canada/Eastern'))
    from_etsy_connection = await mongodb.db['EtsyShopConnections'].find_one({'_id': ObjectId(etsy_connection_id)})
    print(from_etsy_connection)
    total_num_of_orders = await mongodb.db['Receipts'].find({'shop_name': from_etsy_connection['etsy_shop_name']}).to_list(length=None)
    total_num_of_orders = len(total_num_of_orders)
    print(total_num_of_orders)
    now: datetime = datetime.now()
    now = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # now = now.isoformat()
    print(now)
    num_of_uncompleted_orders_due_today = await mongodb.db['Receipts'].aggregate([
		{
			'$lookup': {
				'from': 'Notes', 
				'localField': 'receipt_id', 
				'foreignField': 'receipt_id', 
				'as': 'Note'
			}
		}, {
			'$match': {
                'shop_name': from_etsy_connection['etsy_shop_name'],
                'max_due_date': now,
                'Note.status': ReceiptNoteStatus.uncompleted,
            }
		}, {
			'$unwind': {
				'path': '$Note',
				'preserveNullAndEmptyArrays': True
			}
		}, {
            '$count': 'num_of_uncompleted_orders_due_today'
        }
	]).to_list(length=None)
    print(num_of_uncompleted_orders_due_today)
    if len(num_of_uncompleted_orders_due_today) > 0:
        num_of_uncompleted_orders_due_today = num_of_uncompleted_orders_due_today[0]['num_of_uncompleted_orders_due_today']
    print(f'({from_etsy_connection["etsy_shop_name"]}) # of uncompleted orders due today: ', num_of_uncompleted_orders_due_today)
    num_of_uncompleted_orders = await mongodb.db['Receipts'].aggregate([
		{
			'$lookup': {
				'from': 'Notes', 
				'localField': 'receipt_id', 
				'foreignField': 'receipt_id', 
				'as': 'Note'
			}
		}, {
			'$match': {
                'shop_name': from_etsy_connection['etsy_shop_name'],
                'Note.status': ReceiptNoteStatus.uncompleted
            }
		}, {
			'$unwind': {
				'path': '$Note',
				'preserveNullAndEmptyArrays': True
			}
		}, {
            '$count': 'num_of_uncompleted_orders'
        }
	]).to_list(length=None)
    print(num_of_uncompleted_orders)
    if len(num_of_uncompleted_orders) > 0:
        num_of_uncompleted_orders = num_of_uncompleted_orders[0]['num_of_uncompleted_orders']
    
    print(f'({from_etsy_connection["etsy_shop_name"]}) # of uncompleted orders: ', num_of_uncompleted_orders)
    return {
        'total_num_of_orders': total_num_of_orders,
        'num_of_uncompleted_orders_due_today': num_of_uncompleted_orders_due_today,
        'num_of_uncompleted_orders': num_of_uncompleted_orders,
        'last_updated': last_updated
    }
    # find({'max_due_date': {'$lte': now, '$gte': now}}).to_length(length=None)

