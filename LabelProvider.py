import abc

import pprint
from config import STALLION_API_BASE_URL, STALLION_API_TOKEN
from httpx import AsyncClient
from database import MongoDB
import csv
from MyLogger import Logger
from base64 import b64decode
from pymongo import errors
logging = Logger().logging		


class Base64ToBytes:
	@staticmethod
	def base64_to_bytes(base64_content):
		bytes_for_write = b64decode(base64_content, validate=True)
		if bytes_for_write[0:4] != b'%PDF':
  			raise ValueError('Missing the PDF file signature')
		return bytes_for_write

class LabelProvider:
	@abc.abstractmethod
	def get_label_by_receipt_id():
		...

	@abc.abstractmethod
	def purchase_label():
		...


class StallionCsvFileManager:
	@staticmethod
	async def process_csv_file(file_content: bytes):
		"""process the csv file insert each shipment_id and its associate receipt_id (order_id) to MongoDB"""
		csv_reader = csv.DictReader(file_content.decode('utf-8').split('\n'), dialect="excel")
		insert_data = []
		for row in csv_reader:
			logging.debug(f"{row['Ship Code']} : {row['Order ID']}")
			if not row['Order ID'].isnumeric():
				continue
			insert_data.append({
				'shipment_id': row['Ship Code'],
				'receipt_id': int(row['Order ID']),
				'buyer_name': row['Name'],
				'postal_code': row['Postal Code'],
				'address_1': row['Address1'],
				'address_2': row['Address2'],
				'city': row['City'],
				'province_code': row['Province Code'],
				'country_code': row['Country Code']
			})
		mongodb = MongoDB()
		try:
			insert_many_result = await mongodb.db['Shipments'].insert_many(insert_data, ordered=False)
			logging.info(insert_many_result.inserted_ids)
		except errors.BulkWriteError as e:
			# logging.error(f"Articles bulk write insertion error {e}")
			# panic_list = list(filter(lambda x: x['code'] != 11000, e.details['writeErrors']))
			# if len(panic_list) > 0:
			# 	logging.info(f"these are not duplicate errors {panic_list}")
			# else:
			# 	for writeError in e.details['writeErrors']:
			# 		logging.info(f"{writeError}")
			pass


class StallionLabelManager(LabelProvider):
	@staticmethod
	async def get_label_by_receipt_id(receipt_id: int):
		"""
			check MongoDB with receipt_id and if there is a document with the given receipt_id,
			get the shipment_id and use stallion api to get label content
		"""
		mongodb = MongoDB()
		receipt_id_result = await mongodb.db['Shipments'].find_one({'receipt_id': receipt_id})
		if receipt_id_result is None:
			return
		stallion_api = StallionAPI(STALLION_API_TOKEN)
		try:
			shipment_result = await stallion_api.get_shipment(receipt_id_result['shipment_id'])
		except LabelNotFound as e:
			logging.error(e)
			return None
		else:
			return Base64ToBytes.base64_to_bytes(shipment_result['label'])
		...

	@staticmethod
	def purchase_label():
		...


class StallionAPI:
	def __init__(self, api_token: str):
		self.api_token = api_token
	

	async def get_shipment(self, shipment_id):
		async with AsyncClient() as client:
			headers = {
				"Authorization": f"Bearer {self.api_token}",
				'accept': 'application/json'
			}
			res = await client.get(f'{STALLION_API_BASE_URL}/shipments/{shipment_id}', headers=headers)
			if res.status_code == 200:
				res_json = res.json()
				return res_json
			else:
				raise LabelNotFound(shipment_id)


class LabelNotFound(Exception):
	def __init__(self, shipment_id):
		self.shipment_id = shipment_id
		super().__init__(shipment_id)