import pprint

import requests
from bson.objectid import ObjectId
from requests import HTTPError, Response
from requests_oauthlib import OAuth1Session
# from async_oauthlib import OAuth1Session
from EtsyAPISession import EtsyAPISession
from schemas import ReceiptStatus
from config import ETSY_API_BASE_URI


ETSYAPI_REFERENCE = {
	"findUserProfile": {
		"HTTP Method": "GET",
		"URI": "/users/:user_id/profile",
		"Parameters": "user_id"
	}
}

LIMIT = 100


async def create_etsy_api_with_etsy_connection(db, etsy_connection_id: str, want: int = 2):
	_id: ObjectId = ObjectId(etsy_connection_id)
	etsy_connection = await db["EtsyShopConnections"].find_one({"_id": _id})
	etsy_api_session = EtsyAPISession(etsy_connection["etsy_oauth_token"], etsy_connection["etsy_oauth_token_secret"],
	                                  client_key=etsy_connection["app_key"],
	                                  client_secret=etsy_connection["app_secret"])
	etsy_api = EtsyAPI(etsy_api_session.get_etsy_api_session())
	if want == 1:
		return etsy_api
	else:
		return etsy_connection, etsy_api


class EtsyAPI:
	
	def __init__(self, session: OAuth1Session):
		self.__session = session
		
	def get_session(self):
		return self.__session
	
	def findUserProfile(self):
		response = self.__session.get(f"{ETSY_API_BASE_URI}/users/__SELF__/profile")
		return response
	
	def findAllUserShops(self):
		response = self.__session.get(f"{ETSY_API_BASE_URI}/users/__SELF__/shops")
		if response.status_code == 200:
			return response
		raise HTTPError("User shops not found")
	
	def getUser(self):
		response = self.__session.get(f"{ETSY_API_BASE_URI}/users/__SELF__")
		return response
	
	def getShop_Receipt2(self, receipt_id: int):
		response = self.__session.get(f"{ETSY_API_BASE_URI}/receipts/{receipt_id}")
		print(response.text)
		
		print(response.status_code)
		res_json = response.json()
		pprint.pprint(res_json)
		return res_json["results"]
	
	def findAllShopReceipts(self, shop_id: str,
	                        **kwargs):
		current_page: int = 1
		base_url: str = f"{ETSY_API_BASE_URI}/shops/{shop_id}/receipts?limit={LIMIT}"
		for k, v in kwargs.items():
			if v is not None:
				if k == "was_shipped" or k == "was_paid":
					try:
						v = str(v).lower()
					except KeyError:
						pass
				base_url = base_url + f"&{k}={v}"
		print(base_url)
		base_url = base_url + "&page={current_page}"
		response = self.__session.get(
			base_url.format(current_page=current_page)
			# f"{ETSY_API_BASE_URI}/shops/{shop_id}/receipts?limit={LIMIT}&was_shipped=false"
		)
		
		try:
			response.raise_for_status()
		except requests.exceptions.HTTPError as e:
			# Whoops it wasn't a 200
			return "Error: " + str(e)
		
		# pprint.pprint(response)
		res_json = response.json()
		
		# pprint.pprint(res_json)
		results = {
			"results": res_json["results"]
		}
		# print(res_json)
		# print(results["results"])
		while res_json["pagination"]["next_page"] is not None:
			current_page = res_json["pagination"]["next_page"]
			print(base_url.format(current_page=current_page))
			response = self.__session.get(
				base_url.format(current_page=current_page)
				# f"{ETSY_API_BASE_URI}/shops/{shop_id}/receipts?limit={LIMIT}&page={current_page}&was_shipped=false"
			)
			res_json = response.json()
			results["results"].extend(res_json["results"])
		print(f"COUNT: {len(results['results'])}")
		# await self.__session.close()
		# print(results)
		return results
	
	def findAllShopTransactions(self, shop_id: str):
		response = self.__session.get(f"{ETSY_API_BASE_URI}/shops/{shop_id}/transactions")
		return response
	
	def findAllShop_Receipt2Transactions(self, receipt_id):
		response = self.__session.get(f"{ETSY_API_BASE_URI}/receipts/{receipt_id}/transactions?limit={LIMIT}")
		res_json = response.json()
		results = {
			"results": res_json["results"]
		}
		while res_json["pagination"]["next_page"] is not None:
			next_page = res_json["pagination"]["next_page"]
			response = self.__session.get(
				f"{ETSY_API_BASE_URI}/receipts/{receipt_id}/transactions?limit={LIMIT}&page={next_page}")
			res_json = response.json()
			results["results"].extend(res_json['results'])
		return results
	
	def getImage_Listing(self, listing_id: str, listing_image_id: str) -> Response:
		response: Response = self.__session.get(f"{ETSY_API_BASE_URI}/listings/{listing_id}/images/{listing_image_id}")
		return response
	
	"""
	Synopsis:       Searches the set of Receipt objects associated to a Shop by a query
	HTTP Method:    GET
	URI:            /shops/:shop_id/receipts/search
	Parameters:
		Name            Required    Default     Type
		shop_id         Y 	  	                shop_id_or_name
		search_query 	Y 	  	                string
		limit 	        N 	        25 	        int
		offset 	        N 	        0 	        int
		page 	        N 	  	                int
	"""
	
	def searchAllShopReceipts(self, shop_id: str):
		search_query: str = '14957 Clemson Dr'
		response = self.__session.get(
			f"{ETSY_API_BASE_URI}/shops/{shop_id}/receipts/search?limit={LIMIT}&search_query={search_query}"
		)
		res_json = response.json()
		results = {
			"results": res_json["results"]
		}
		pprint.pprint(res_json)
		while res_json["pagination"]["next_page"] is not None:
			next_page = res_json["pagination"]["next_page"]
			response = self.__session.get(
				f"{ETSY_API_BASE_URI}/shops/{shop_id}/receipts/search?limit={LIMIT}&page={next_page}")
			res_json = response.json()
			results["results"].extend(res_json['results'])
		return results
	
	def getListing(self, listing_id):
		response = self.__session.get(f"{ETSY_API_BASE_URI}/listings/{listing_id}")
		res_json = response.json()
		pprint.pprint(res_json)
		
	def getShippingTemplate(self, shipping_template_id):
		response = self.__session.get(f"{ETSY_API_BASE_URI}/shipping/templates/{shipping_template_id}")
		res_json = response.json()
		pprint.pprint(res_json)
		
	def findAllShopReceiptsByStatus(self, shop_id: str, status: ReceiptStatus):
		response = self.__session.get(f"{ETSY_API_BASE_URI}/shops/{shop_id}/receipts/{status}")
		res_json = response.json()
		pprint.pprint(res_json)
		print(res_json["count"])
