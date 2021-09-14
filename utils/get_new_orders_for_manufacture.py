import datetime
from typing import List
import pymongo
import pytz
import os, sys
p = os.path.abspath('.')
sys.path.insert(1, p)

from database import MongoDB
from MyLogger import Logger
logging = Logger().logging

from GoogleSpreadsheetsAPI import create_spreadsheet

import asyncio


def get_barcode_formula(cell):
    return f'=IF({cell}="","", image("http://generator.onbarcode.com/linear.aspx?TYPE=4&DATA="&{cell}&"&UOM=0&X=1&Y=20&LEFT-MARGIN=0&RIGHT-MARGIN=0&TOP-MARGIN=0&BOTTOM-MARGIN=0&RESOLUTION=72&ROTATE=0&BARCODE-WIDTH=0&BARCODE-HEIGHT=0&SHOW-TEXT=false&TEXT-FONT=Arial%7c9%7cRegular&TextMargin=6&FORMAT=gif&ADD-CHECK-SUM=false&I=1.0&N=2.0&SHOW-START-STOP-IN-TEXT=true&PROCESS-TILDE=false"))'


async def get_todays_order():
    mongodb = MongoDB()
    todays_datetime: datetime = datetime.datetime.now(tz=pytz.timezone('Canada/Eastern'))
    from_datetime: datetime = todays_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    to_datetime: datetime = from_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)
    ts_from_datetime: int = datetime.datetime.timestamp(from_datetime)
    ts_to_datetime: int = datetime.datetime.timestamp(to_datetime)
    logging.debug(f"From_datetime timestamp: {ts_from_datetime}")
    logging.debug(f"To_datetime timestamp: {ts_to_datetime}")
    logging.debug(f"From_datetime: {from_datetime}")
    logging.debug(f"To_datetime: {to_datetime}")
    orders = await mongodb.db['Receipts'].find(
        {
            'creation_tsz': {
                "$gte": ts_from_datetime,
                "$lte": ts_to_datetime
            }
        },
        projection={
            '_id': False,
            'name': True,
            'shop_name': True,
            'receipt_id': True,
            'Transactions': True,
            'max_due_date': True
        }
    ).sort("creation_tzs", pymongo.ASCENDING).to_list(length=None)
    
    to_spreadsheet = [
        [
            'Store',
            "Buyer's Name",
            'Order No',
            'Length And Color',
            'Style',
            'Personalization',
            'Max Due Date',
            'Barcode'
        ]
    ]
    
    current_transaction_num = 2
    for order in orders:
        receipt_id = order['receipt_id']
        shop_name = order['shop_name']
        max_due_date = order['max_due_date']
        name = order['name']
        transactions: List[dict] = order['Transactions']
        for transaction in transactions:
            variations = transaction['variations']
            variations_retrieved = []
            for variation in variations:
                variations_retrieved.append(variation['formatted_value'])

            item = [
                shop_name,
                name,
                receipt_id,
                *variations_retrieved,
                datetime.datetime.strftime(max_due_date, "%d %B, %Y"),
                get_barcode_formula(f'C{current_transaction_num}')
            ]
            to_spreadsheet.append(
                item        
            )
            current_transaction_num += 1
            logging.debug(f"{item}")
    emailAddresses = await mongodb.db['ShareEmailAdressesWithGoogleSpreadsheet'].find({}, projection={'_id': False}).to_list(length=None)
    spreadsheet_id = create_spreadsheet.create_spreadsheetand_and_share(
        datetime.datetime.strftime(
            datetime.datetime.now(
                tz=pytz.timezone('Canada/Eastern')
            ), 
            "%d-%B-%Y_orders"
        ),
        to_spreadsheet,
        emailAddresses[0]['email']
    )
    logging.debug(f"Spreadsheet id: {spreadsheet_id}")
    

if __name__ == '__main__':
    asyncio.run(get_todays_order())
    
	