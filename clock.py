from rq import Queue
from worker import conn

q = Queue(connection=conn)

from MyLogger import Logger
from MyScheduler import MyScheduler
from EtsyShopManager import EtsyShopManager
from config import SCHEDULED_JOB_INTERVAL, SCHEDULED_JOB_OFFSET
# from jobs import SyncEtsyShopReceipts
myScheduler = MyScheduler()
logging = Logger().logging
# syncEtsyShopReceipts = SyncEtsyShopReceipts()

# from apscheduler.schedulers.asyncio import AsyncIOScheduler

# sched = AsyncIOScheduler()


# @sched.scheduled_job()


def sync_etsy_shop_receipts(etsy_connection_id):
	q.enqueue(
		EtsyShopManager.syncShop,
		kwargs={"etsy_connection_id": etsy_connection_id},
	)


job_offset = 0
# syncEtsyShopReceipts.get_jobs_to_schedule()
for etsy_connection_id in ["60c93353ee7306108057150e", "60cd6a1adceaba8c03b9b344"]:
	myScheduler.scheduler.add_job(
		sync_etsy_shop_receipts,
		kwargs={"etsy_connection_id": etsy_connection_id}
	)
	myScheduler.scheduler.add_job(
		sync_etsy_shop_receipts,
		"interval",
		minutes=SCHEDULED_JOB_INTERVAL + job_offset,
		kwargs={"etsy_connection_id": etsy_connection_id},
		id=f"{etsy_connection_id}:syncShopProcess",
		name=f"{etsy_connection_id}:syncShopProcess"
	)
	job_offset += SCHEDULED_JOB_OFFSET
myScheduler.scheduler.start()
# myScheduler.scheduler.print_jobs()


# async def get_etsy_connections():
# 	logging.info("FastAPI startup_event")
# 	etsy_connections = await mongodb.db["EtsyShopConnections"].find().to_list(100)
# 	return etsy_connections
	


# loop = asyncio.get_event_loop()
# try:
# 	etsy_connections = loop.run_until_complete(get_etsy_connections())
# except Exception as e:
# 	logging.exception(e)
# 	exit()
# else:
# 	logging.info("Got Etsy Connections from MongoDD.")
# 	logging.info("Starting to schedule syncEtsyReceipts job for each Etsy Connections.")
# # finally:
# # 	loop.close()

# job_offset = 0
# if ENV_MODE != "DEV":
# 	logging.info("... Production Environment ...")
# else:
# 	logging.info("This is development environment.")
# for etsy_connection in etsy_connections:
# 	_id = str(etsy_connection["_id"])
# 	myScheduler.add_job(
# 		_id,
# 		EtsyShopManager.syncShop,
# 		"interval",
# 		minutes=SCHEDULED_JOB_INTERVAL + job_offset,
# 		kwargs={"etsy_connection_id": _id},
# 		id=f"{_id}:syncShopProcess",
# 		name=f"{_id}:syncShopProcess",
# 		# jobstore="mongodb"
# 	)
# 	logging.info(f"{etsy_connection['etsy_shop_name']} has been registered to the job list.")
# 	job_offset += SCHEDULED_JOB_OFFSET
# # from test_delete_me import test
# # myScheduler.scheduler.add_job(test, "interval", seconds=5)
# myScheduler.scheduler.start()
# myScheduler.scheduler.print_jobs()
