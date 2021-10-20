import datetime
from typing import List
import pymongo
import pytz
import os, sys
import html
p = os.path.abspath('.')
sys.path.insert(1, p)

from database import MongoDB
from MyLogger import Logger
logging = Logger().logging

from .GoogleSpreadsheetsAPI import create_spreadsheet

import asyncio


def get_barcode_formula(cell):
    return f'=IF({cell}="","", image("http://generator.onbarcode.com/linear.aspx?TYPE=4&DATA="&{cell}&"&UOM=0&X=1&Y=20&LEFT-MARGIN=0&RIGHT-MARGIN=0&TOP-MARGIN=0&BOTTOM-MARGIN=0&RESOLUTION=72&ROTATE=0&BARCODE-WIDTH=0&BARCODE-HEIGHT=0&SHOW-TEXT=false&TEXT-FONT=Arial%7c9%7cRegular&TextMargin=6&FORMAT=gif&ADD-CHECK-SUM=false&I=1.0&N=2.0&SHOW-START-STOP-IN-TEXT=true&PROCESS-TILDE=false"))'


async def get_todays_order(year=None, month=None, day=None):
    mongodb = MongoDB()
    todays_datetime: datetime = datetime.datetime.now(tz=pytz.timezone('Canada/Eastern'))
    # todays_datetime: datetime = datetime.datetime.now()
    from_datetime: datetime = todays_datetime.replace(
        day=day if day is not None else todays_datetime.day,
        month=month if month is not None else todays_datetime.month,
        year=year if year is not None else todays_datetime.year,
        hour=0, 
        minute=0, 
        second=0, 
        microsecond=0
    )
    to_datetime: datetime = from_datetime.replace(
        day=day if day is not None else todays_datetime.day,
        month=month if month is not None else todays_datetime.month,
        year=year if year is not None else todays_datetime.year,
        hour=23, 
        minute=59, 
        second=59, 
        microsecond=999999)
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
            'max_due_date': True,
            'formatted_address': True,
        }
    ).sort("creation_tzs", pymongo.ASCENDING).to_list(length=None)
    logging.info(f"#=<>=# {len(orders)} orders have been created between {from_datetime} to {to_datetime}. #=<>=#")
    spreadsheet_headers = await mongodb.db['ToSpreadsheetHeaders'].find(projection={"_id": False,"headers": True}).to_list(length=1)
    spreadsheet_headers = spreadsheet_headers[0]["headers"]
    spreadsheet_headers = list(map(lambda x: x.lower(), spreadsheet_headers))

    to_spreadsheet = [
        spreadsheet_headers
    ]
    
    current_transaction_num = 2
    for order in orders:
        receipt_id = order['receipt_id']
        shop_name = order['shop_name']
        # max_due_date = order['max_due_date']
        # name = order['name']
        transactions: List[dict] = order.get('Transactions')
        formatted_address = order.get('formatted_address')
        country = formatted_address.split('\n')
        country = country[len(country) - 1]
        for transaction in transactions:
            sku: str = transaction.get('product_data').get('sku')
            variations = transaction['variations']
            variations_retrieved = ["" for _ in range(len(spreadsheet_headers))]
            print(variations_retrieved)
            for variation in variations:
                # variations_retrieved.append(variation['formatted_value'])
                formatted_name: str = variation.get('formatted_name').lower()
                formatted_name = html.unescape(formatted_name)
                formatted_value: str = variation.get('formatted_value')
                formatted_value = html.unescape(formatted_value)
                
                try:
                    print(formatted_name, " == ", formatted_value, f" index({spreadsheet_headers.index(formatted_name)})")
                    # print(spreadsheet_headers)
                    variations_retrieved[spreadsheet_headers.index(formatted_name)] = formatted_value
                except (IndexError, ValueError) as e:
                    print(e)
                    pass
            variations_retrieved = variations_retrieved[4:]
            print(variations_retrieved)

            item = [
                shop_name,
                # name,
                receipt_id,
                sku,
                country,
                *variations_retrieved,
                # datetime.datetime.strftime(max_due_date, "%d %B, %Y"),
                # get_barcode_formula(f'C{current_transaction_num}')
            ]
            to_spreadsheet.append(
                item        
            )
            current_transaction_num += 1
            logging.debug(f"{item}")
    emailAddresses = await mongodb.db['ShareEmailAdressesWithGoogleSpreadsheet'].find({}, projection={'_id': False}).to_list(length=None)
    spreadsheet_id = await create_spreadsheet.create_spreadsheetand_and_share(
        datetime.datetime.strftime(
            from_datetime, 
            "%d-%B-%Y_orders"
        ),
        to_spreadsheet,
        mongodb,
        emailAddresses[0]['email']
    )
    logging.debug(f"Spreadsheet id: {spreadsheet_id}")
    

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--day", help="day of the datetime (1-31)")
    parser.add_argument("-m", "--month", help="month of the datetime (1-12)")
    parser.add_argument("-y", "--year", help="year of the datetime")

    args = parser.parse_args()
    asyncio.run(get_todays_order(
        day=int(args.day) if args.day is not None else None,
        month=int(args.month) if args.month is not None else None, 
        year=int(args.year) if args.year is not None else None
    ))
    
	