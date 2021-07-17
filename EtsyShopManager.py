from datetime import datetime
from typing import List, Optional
from helpers import calculate_max_min_due_date

import numpy
from bson import ObjectId

from AsyncEtsyApi import AsyncEtsy, Method, EtsyUrl


class EtsyShopManager:
	
	def __init__(self, shop_name):
		self.shop_name = shop_name
	
	async def insert_receipt(self, receipt: dict, db):
		receipt.update({"shop_name": self.shop_name})
		receipt_insert_result = await db["Receipts"].insert_one(receipt)
		return receipt_insert_result.inserted_id
	
	async def insert_receipts(self, receipts: List[dict], db):
		if len(receipts) <= 0:
			return []
		for r in receipts:
			r["shop_name"] = self.shop_name
		insert_all_receipts_result = await db["Receipts"].insert_many(receipts)
		return [(str(mongodb_id), receipt["receipt_id"]) for mongodb_id, receipt in zip(insert_all_receipts_result.inserted_ids, receipts)]
		# return insert_all_receipts_result.inserted_ids
	
	async def update_receipt(self, mongodb_id: str, receipt_id: str, transactions: List[dict], db):
		if type(mongodb_id) is not ObjectId:
			mongodb_id = ObjectId(mongodb_id)
		update_receipt_result = await db["Receipts"].update_one(
			{"_id": mongodb_id, "receipt_id": receipt_id},
			{
				"$set": {
					"transactions": transactions
				}
			}
		)
	
	@staticmethod
	async def check_unpaids(etsy_connection_id, asyncEtsyApi, params, r):
		my_params = dict(params)
		my_params.pop("min_created", None)
		receipts_not_paid = []
		receipts_to_be_inserted = numpy.array([])
		unpaid_from_redis = r.get(f"{etsy_connection_id}:unpaid_receipts")
		if unpaid_from_redis is not None and len(unpaid_from_redis) > 0:
			
			unpaid_responses = await AsyncEtsy.asyncLoop(
				f=asyncEtsyApi.getAllPages,
				method=Method.get,
				url=EtsyUrl.getShop_Receipt2(unpaid_from_redis),
				params=my_params
			)
			for res in unpaid_responses:
				res_json = res.json()
				results: List[dict] = res_json["results"]
				for i, receipt in enumerate(results):
					print(receipt['receipt_id'])
					was_paid: bool = receipt["was_paid"]
					print(f"was_paid: {was_paid}")
					paid_tzs: Optional[int] = receipt["Transactions"][0]["paid_tsz"]
					if not was_paid or paid_tzs is None:
						not_paid_receipt = results.pop(i)
						receipts_not_paid.append(not_paid_receipt["receipt_id"])
						continue
					calculate_max_min_due_date(receipt)
				receipts_to_be_inserted = numpy.concatenate((receipts_to_be_inserted, results))
		return receipts_not_paid, receipts_to_be_inserted
	
	@staticmethod
	async def check_for_new_orders(asyncEtsyApi, params):
		receipts_not_paid = []
		receipts_to_be_inserted = numpy.array([])
		receipt_responses = await AsyncEtsy.asyncLoop(
			f=asyncEtsyApi.getAllPages,
			method=Method.get,
			url=EtsyUrl.findAllShopReceipts(asyncEtsyApi.shop_id),
			params=params
		)
		
		for res in receipt_responses:
			res_json = res.json()
			results: List[dict] = res_json["results"]
			for i, receipt in enumerate(results):
				print(receipt['receipt_id'])
				was_paid: bool = receipt["was_paid"]
				print(f"was_paid: {was_paid}")
				paid_tzs: Optional[int] = receipt["Transactions"][0]["paid_tsz"]
				if not was_paid or paid_tzs is None:
					not_paid_receipt = results.pop(i)
					receipts_not_paid.append(not_paid_receipt["receipt_id"])
					continue
				calculate_max_min_due_date(receipt)
			receipts_to_be_inserted = numpy.concatenate((receipts_to_be_inserted, results))
		return receipts_not_paid, receipts_to_be_inserted
	
	@staticmethod
	async def syncShop(etsy_connection_id: str, db, r):
		try:
			is_running = r.get(f"{etsy_connection_id}:is_running")
			print(f"is_running: {is_running}")
			if is_running == "True":
				return {
					"background-task": "already running"
				}
			else:
				r.set(f"{etsy_connection_id}:is_running", "True")
			last_updated = r.get(f"{etsy_connection_id}:last_updated")
			params = {
				"includes": "Transactions/MainImage,Listings/ShippingTemplate"
			}
			if last_updated is not None:
				last_updated = int(last_updated)
				print("last_updated is not None, setting min_created")
				params["min_created"] = last_updated
			current_time = int(datetime.now().timestamp())
			params["max_created"] = current_time
			if last_updated is not None:
				print(f"From = {datetime.fromtimestamp(last_updated)}\nTo = {datetime.fromtimestamp(current_time)}")
			else:
				print(f"From = -\nTo = {datetime.fromtimestamp(current_time)}")
			
			asyncEtsyApi = await AsyncEtsy.getAsyncEtsyApi(etsy_connection_id, db)
			etsyShopManager = EtsyShopManager(asyncEtsyApi.shop_id)
			
			receipts_not_paid, receipts_to_be_inserted = await EtsyShopManager.check_unpaids(etsy_connection_id, asyncEtsyApi, params, r)
			unpaid_receipts, r_to_be_inserted = await EtsyShopManager.check_for_new_orders(asyncEtsyApi, params)
			receipts_not_paid = receipts_not_paid + unpaid_receipts
			r.set(f"{etsy_connection_id}:unpaid_receipts", ','.join(str(not_paid_receipt) for not_paid_receipt in receipts_not_paid))
			receipts_to_be_inserted = numpy.concatenate((receipts_to_be_inserted, r_to_be_inserted))
			
			receipts_to_be_inserted = receipts_to_be_inserted.tolist()
			mongodb_result = await etsyShopManager.insert_receipts(receipts_to_be_inserted, db)
			if len(mongodb_result) == len(receipts_to_be_inserted):
				print("successfully inserted all receipts")
				print("setting last_updated")
				r.set(f"{etsy_connection_id}:last_updated", current_time)
		except Exception as e:
			print(e)
			pass
		finally:
			r.set(f"{etsy_connection_id}:is_running", "False")
