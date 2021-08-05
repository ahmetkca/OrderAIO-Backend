from MyLogger import Logger
logging = Logger().logging
from MyScheduler import MyScheduler
myScheduler = MyScheduler()
from EtsyShopManager import EtsyShopManager
from database import MongoDB
mongodb = MongoDB()
from config import ENV_MODE, SCHEDULED_JOB_INTERVAL, SCHEDULED_JOB_OFFSET
import asyncio


async def main():
	logging.info("FastAPI startup_event")
	etsy_connections = await mongodb.db["EtsyShopConnections"].find().to_list(100)
	job_offset = 0
	
	if ENV_MODE != "DEV":
		logging.info("... Production Environment ...")
		myScheduler.scheduler.start()
	else:
		logging.info("This is development environment.")
	for etsy_connection in etsy_connections:
		_id = str(etsy_connection["_id"])
		myScheduler.add_job(
			_id,
			EtsyShopManager.syncShop,
			"interval",
			minutes=SCHEDULED_JOB_INTERVAL + job_offset,
			kwargs={"etsy_connection_id": _id},
			id=f"{_id}:syncShopProcess",
			name=f"{_id}:syncShopProcess",
			# jobstore="mongodb"
		)
		logging.info(f"{etsy_connection['etsy_shop_name']} has been registered to the job list.")
		job_offset += SCHEDULED_JOB_OFFSET
	# from test_delete_me import test
	# myScheduler.scheduler.add_job(test, "interval", seconds=5)
	myScheduler.scheduler.print_jobs()


if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	try:
		loop.run_until_complete(main())
	except Exception as e:
		logging.exception(e)