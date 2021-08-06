
from MyLogger import Logger
import asyncio
from database import MongoDB
mongodb = MongoDB()
logging = Logger().logging

async def get_etsy_connections():
	logging.info("FastAPI startup_event")
	etsy_connections = await mongodb.db["EtsyShopConnections"].find().to_list(100)
	return etsy_connections


class SyncEtsyShopReceipts:
	def __init__(self):
		loop = asyncio.get_event_loop()
		self.etsy_connections = []
		try:
			self.etsy_connections = loop.run_until_complete(get_etsy_connections())
		except Exception as e:
			logging.exception(e)
		else:
			logging.info("Got Etsy Connections from MongoDD.")
			logging.info("Starting to schedule syncEtsyReceipts job for each Etsy Connections.")

	def get_jobs_to_schedule(self):
		for etsy_connection in self.etsy_connections:
			yield str(etsy_connection["_id"])