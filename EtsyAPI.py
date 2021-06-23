import pprint

from bson.objectid import ObjectId
from requests import HTTPError, Response
from requests_oauthlib import OAuth1Session
from EtsyAPISession import EtsyAPISession

ETSYAPI_BASE_URI = "https://openapi.etsy.com/v2"

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
	
	def findUserProfile(self):
		response = self.__session.get(f"{ETSYAPI_BASE_URI}/users/__SELF__/profile")
		return response
	
	def findAllUserShops(self):
		response = self.__session.get(f"{ETSYAPI_BASE_URI}/users/__SELF__/shops")
		if response.status_code == 200:
			return response
		raise HTTPError("User shops not found")
	
	def getUser(self):
		response = self.__session.get(f"{ETSYAPI_BASE_URI}/users/__SELF__")
		return response
	
	def findAllShopReceipts(self, shop_id: str):
		response = self.__session.get(f"{ETSYAPI_BASE_URI}/shops/{shop_id}/receipts?limit={LIMIT}&was_shipped=false")
		res_json = response.json()
		results = {
			"results": res_json["results"]
		}
		while res_json["pagination"]["next_page"] is not None:
			current_page = res_json["pagination"]["next_page"]
			print(current_page)
			response = self.__session.get(
				f"{ETSYAPI_BASE_URI}/shops/{shop_id}/receipts?limit={LIMIT}&page={current_page}&was_shipped=false")
			res_json = response.json()
			results["results"].extend(res_json["results"])
		print(results)
		return results
	
	def findAllShopTransactions(self, shop_id: str):
		response = self.__session.get(f"{ETSYAPI_BASE_URI}/shops/{shop_id}/transactions")
		return response
	
	def findAllShop_Receipt2Transactions(self, receipt_id):
		response = self.__session.get(f"{ETSYAPI_BASE_URI}/receipts/{receipt_id}/transactions?limit={LIMIT}")
		res_json = response.json()
		results = {
			"results": res_json["results"]
		}
		while res_json["pagination"]["next_page"] is not None:
			next_page = res_json["pagination"]["next_page"]
			response = self.__session.get(
				f"{ETSYAPI_BASE_URI}/receipts/{receipt_id}/transactions?limit={LIMIT}&page={next_page}")
			res_json = response.json()
			results["results"].extend(res_json['results'])
		return results
	
	def getImage_Listing(self, listing_id: str, listing_image_id: str) -> Response:
		response: Response = self.__session.get(f"{ETSYAPI_BASE_URI}/listings/{listing_id}/images/{listing_image_id}")
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
			f"{ETSYAPI_BASE_URI}/shops/{shop_id}/receipts/search?limit={LIMIT}&search_query={search_query}"
		)
		res_json = response.json()
		results = {
			"results": res_json["results"]
		}
		pprint.pprint(res_json)
		while res_json["pagination"]["next_page"] is not None:
			next_page = res_json["pagination"]["next_page"]
			response = self.__session.get(
				f"{ETSYAPI_BASE_URI}/shops/{shop_id}/receipts/search?limit={LIMIT}&page={next_page}")
			res_json = response.json()
			results["results"].extend(res_json['results'])
		return results
