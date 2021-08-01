from asyncio import Task
from enum import Enum

from authlib.integrations.httpx_client import AsyncOAuth1Client
import asyncio
from math import ceil
from config import ETSY_API_BASE_URI, NO_CONCURRENT, LIMIT

from bson import ObjectId
from httpx import Response

from MyLogger import Logger
logging = Logger().logging
logging.info(f"{__name__}'s logger successfully created.")


class Method(Enum):
	get = "GET"
	post = "POST"
	put = "PUT"
	delete = "DELETE"


class EtsyUrl:
	findAllShopReceipts = lambda shop_id: "/shops/{shop_id}/receipts".format(shop_id=shop_id)
	findAllShop_Receipt2Transactions = lambda receipt_id: "/receipts/{receipt_id}/transactions".format(receipt_id=receipt_id)
	getShop_Receipt2 = lambda receipt_id_s: "/receipts/{receipt_id_s}".format(receipt_id_s=receipt_id_s)


class AsyncEtsy:
	
	def __init__(self, client_id: str, client_secret: str, token: str, token_secret: str, shop_id: str):
		self.client_id = client_id
		self.client_secret = client_secret
		self.token = token
		self.token_secret = token_secret
		self.shop_id = shop_id
		
	# async def requestToDb(self, method, url, params):
	
	async def request(self, method: Method, url: str, params: dict = None):
		if params is None:
			params = {"limit": LIMIT}
		url = ETSY_API_BASE_URI + url
		logging.info(f"Starting to fetch ({url})")
		params["limit"] = LIMIT
		async with AsyncOAuth1Client(self.client_id, self.client_secret, self.token, self.token_secret) as etsy:
			# print(params)
			res = await etsy.request(method=method.value, url=url, params=params, timeout=None)
			# print(f"({url}) Fetched page #{res.json()['params']['page']} {res.status_code}")
			logging.info(f"Done ... ({url}) ({res.status_code})")
		return res
	
	async def requestByPage(self, method, url, params, page):
		if params is None:
			params = {}
		params["page"] = page
		res = await self.request(method, url, params)
		return res
	
	async def getAllPages(self, loop, method, url, params=None):
		responses = []
		if params is None:
			params = {}
		count_res = await self.request(method, url, params)
		count = count_res.json()["count"]
		logging.info(f"Total {count} item has been found for {url}")
		dltasks = set()
		next_page = 1
		while next_page <= ceil(count / LIMIT):
			if len(dltasks) >= NO_CONCURRENT:
				_done, dltasks = await asyncio.wait(dltasks, return_when=asyncio.FIRST_COMPLETED)
				task: Task = next(iter(_done))
				res: Response = task.result()
				responses.append(res)
				# print(_done[0])
			
			dltasks.add(loop.create_task(self.requestByPage(method, url, params, next_page)))
			next_page += 1
		
		if len(dltasks) <= 0:
			return responses
		done, pending = await asyncio.wait(dltasks)
		t: Task
		for t in done:
			logging.info(t)
			res: Response = t.result()
			responses.append(res)
		return responses
	
	async def getAllTransactions(self, loop, receipt_ids):
		transactions_by_receipt_id = {}
		dltasks = set()
		receipt_ids_index = 0
		while receipt_ids_index < len(receipt_ids):
			mongodb_id, receipt_id = receipt_ids[receipt_ids_index]
			if len(dltasks) >= NO_CONCURRENT:
				_done, dltasks = await asyncio.wait(dltasks, return_when=asyncio.FIRST_COMPLETED)
				task: Task = next(iter(_done))
				res: Response = task.result()
				transactions_by_receipt_id[receipt_id] = {
					"mongodb_id": mongodb_id,
					"transactions": res.json()["results"]
				}
				
			dltasks.add(
				loop.create_task(
					self.request(
						Method.get,
						EtsyUrl.findAllShop_Receipt2Transactions(receipt_id)),
					name=f"{mongodb_id}:{receipt_id}")
			)
			await asyncio.sleep(0.15)
			receipt_ids_index += 1
		
		logging.info("Last transactions")
		if len(dltasks) <= 0:
			return transactions_by_receipt_id
		done, pending = await asyncio.wait(dltasks)
		t: Task
		for t in done:
			mongodb_id, receipt_id = t.get_name().split(":")
			logging.info(f"Transaction for Receipt_id: {receipt_id}|{mongodb_id} is done.")
			res: Response = t.result()
			transactions_by_receipt_id[receipt_id] = {
				"mongodb_id": mongodb_id,
				"transactions": res.json()["results"]
			}
		return transactions_by_receipt_id
		
	@staticmethod
	async def asyncLoop(f, **kwargs):
		logging.info(kwargs)
		loop = asyncio.get_running_loop()
		# await f(loop, **kwargs)
		done, pending = None, None
		try:
			done, pending = await asyncio.wait({loop.create_task(f(loop, **kwargs))})
			task = next(iter(done))
			# for res in task.result():
			# 	print(res.status_code)
			# 	print(res.json()["params"])
			return task.result()
		finally:
			pass
			# return task.result()
			
		# loop.close()
	
	@staticmethod
	async def getAsyncEtsyApi(etsy_connection_id: str, db):
		_id: ObjectId = ObjectId(etsy_connection_id)
		etsy_connection = await db["EtsyShopConnections"].find_one({"_id": _id})
		async_etsy_api = AsyncEtsy(
			etsy_connection["app_key"],
			etsy_connection["app_secret"],
			etsy_connection["etsy_oauth_token"],
			etsy_connection["etsy_oauth_token_secret"],
			etsy_connection["etsy_shop_name"])
		return async_etsy_api
