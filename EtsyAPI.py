from requests_oauthlib import OAuth1Session

ETSYAPI_BASE_URI = "https://openapi.etsy.com/v2"

ETSYAPI_REFERENCE = {
	"findUserProfile": {
		"HTTP Method": "GET",
		"URI": "/users/:user_id/profile",
		"Parameters": "user_id"
	}
}


class EtsyAPI:
	
	def __init__(self, session: OAuth1Session):
		self.__session = session
	
	def findUserProfile(self):
		response = self.__session.get(f"{ETSYAPI_BASE_URI}/users/__SELF__/profile")
		return response
	
	def findAllUserShops(self):
		response = self.__session.get(f"{ETSYAPI_BASE_URI}/users/477130646/shops")
		return response
