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


class PurchaseLabelData:
	def __init__(self, 
		name: str,
		order_id: str,
		address1: str,
		address2: str,
		city: str,
		province_code: str,
		country_code: str,
		postal_code: str,
		package_contents: str,
		store: str
	):
		self.name = name
		self.order_id = order_id,
		self.address1 = address1,
		self.address2 = address2,
		self.city = city,
		self.province_code = province_code,
		self.country_code = country_code,
		self.postal_code = postal_code,
		self.package_contents = package_contents
		self.store = store


class DirectlyFromStallionAPI(LabelProvider):
	@staticmethod
	async def get_label_by_receipt_id(receipt_id: str):
		"""
			Retriving label directly from StallionExpress API
		"""
		stallion_api: StallionAPI = StallionAPI(api_token=STALLION_API_TOKEN)
		res: dict = await stallion_api.get_status_by_order_id(order_id=receipt_id)
		if res is not None and res.get('success'):
			try:
				shipment_result = await stallion_api.get_shipment(res.get('details').get('ship_code'))
			except LabelNotFound as e:
				logging.error(e)
				return None
			else:
				return Base64ToBytes.base64_to_bytes(shipment_result['label'])
		else:
			return None

	@staticmethod
	def purchase_label(purchaseLabelData: PurchaseLabelData):
		purc


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

	async def get_status_by_order_id(self, order_id: int):
		async with AsyncClient() as client:
			headers = {
				"Authorization": f"Bearer {self.api_token}",
				'accept': 'application/json'
			}
			params = {
				'order_id': order_id,
			}
			res = await client.get(f'{STALLION_API_BASE_URL}/track', headers=headers, params=params)
			return res.json()

	async def purchase_label(self, purchaseLabelData: PurchaseLabelData ):
		async with AsyncClient() as client:
			headers = {
				"Authorization": f"Bearer {self.api_token}",
				'accept': 'application/json'
			}
			params = purchaseLabelData.dict()
			params["is_fba"] = False
			params["signature_confirmation"] = False
			params["weight_unit"] = "lbs"
			params["size_unit"] =  "in"
			params["value"] =  20
			params["currency"] = "CAD"
			params['weight'] = 0.2
			params["length"]= 5
			params["width"]= 5
			params["height"] = 5
			params["label_format"] = "pdf"
			params["purchase_label"] = True
			params["insured"] = True,
			params["needs_postage"] = True
			if purchaseLabelData.get('country_code') == 'US':
				params["package_type"] = "thick_envelope"
				params["postage_type"]= "usps_first_class_mail"
			elif purchaseLabelData.get('country_code') == 'CA':
				params["package_type"] = "thick_envelope"
				params["postage_type"] = "stallion_express_domestic"
				

class LabelNotFound(Exception):
	def __init__(self, shipment_id):
		self.shipment_id = shipment_id
		super().__init__(shipment_id)


