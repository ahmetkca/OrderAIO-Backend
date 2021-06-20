import os
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

load_dotenv()

ETSY_API_KEY = os.getenv('ETSY_API_KEY')
ETSY_API_SECRET = os.getenv('ETSY_API_SECRET')


def check_keys_and_secrets(*args):
	for arg in args:
		if len(arg) == 0:
			return True
	return False



class EtsyAPISession:
	def __init__(self,
	             resource_owner_key: str,
	             resource_owner_secret: str,
	             client_key=None,
	             client_secret=None):
		if client_key is None or client_secret is None:
			client_key = os.getenv('ETSY_API_KEY')
			client_secret = os.getenv('ETSY_API_SECRET')
		self.__client_key = client_key
		self.__client_secret = client_secret
		self.__resource_owner_key: str = resource_owner_key
		self.__resource_owner_secret: str = resource_owner_secret
		self.__etsy_api_session: OAuth1Session = self.create_etsy_api_session()
	
	def get_etsy_api_session(self) -> OAuth1Session:
		return self.__etsy_api_session
	
	def create_etsy_api_session(self) -> OAuth1Session:
		if check_keys_and_secrets((
				self.__client_key,
				self.__client_secret,
				self.__resource_owner_key,
				self.__resource_owner_secret
		)):
			raise ValueError("CLIENT_KEY (APP) or CLIENT_SECRET (APP) or RESOURCE_OWNER_KEY (USER) or RESOURCE_OWNER_SECRET (USER) is not found!")
		
		etsy_api_session = OAuth1Session(
			client_key=self.__client_key,
			client_secret=self.__client_secret,
			resource_owner_key=self.__resource_owner_key,
			resource_owner_secret=self.__resource_owner_secret
		)
		return etsy_api_session
	
	@staticmethod
	def get_request_token(
			client_key=None,
			client_secret=None) -> dict:
		if client_key is None or client_secret is None:
			client_key = os.getenv('ETSY_API_KEY')
			client_secret = os.getenv('ETSY_API_SECRET')
		oauth_session = OAuth1Session(
			client_key=client_key,
			client_secret=client_secret,
			callback_uri=os.getenv("CALLBACK_URI")
		)
		request_token_dict: dict = oauth_session.fetch_request_token(
			url="https://openapi.etsy.com/v2/oauth/request_token?scope=email_r%20listings_r%20transactions_r%20profile_r%20address_r%20shops_rw"
		)
		return request_token_dict
	
	@staticmethod
	def get_access_token(resource_owner_key: str, resource_owner_secret: str, verifier: str,
	                     client_key=None,
	                     client_secret=None) -> dict:
		if client_key is None or client_secret is None:
			client_key = os.getenv('ETSY_API_KEY')
			client_secret = os.getenv('ETSY_API_SECRET')
		oauth_session = OAuth1Session(
			client_key=client_key,
			client_secret=client_secret,
			resource_owner_key=resource_owner_key,
			resource_owner_secret=resource_owner_secret
		)
		access_token_dict: dict = oauth_session.fetch_access_token(
			url="https://openapi.etsy.com/v2/oauth/access_token",
			verifier=verifier
		)
		return access_token_dict
