# class bcolors:
#     HEADER = '\033[95m'
#     OKBLUE = '\033[94m'
#     OKCYAN = '\033[96m'
#     OKGREEN = '\033[92m'
#     WARNING = '\033[93m'
#     FAIL = '\033[91m'
#     ENDC = '\033[0m'
#     BOLD = '\033[1m'
#     UNDERLINE = '\033[4m'
from pydantic import BaseModel
from termcolor import colored
# import asyncio
# from rq import Queue
# from worker import conn

# q = Queue(connection=conn)
# from apscheduler.schedulers.blocking import BlockingScheduler
# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from apscheduler.schedulers.background import BackgroundScheduler
from MyLogger import Logger
from MyScheduler import MyScheduler
from EtsyShopManager import syncShop
# syncShop = EtsyShopManager.syncShop
from config import SCHEDULED_JOB_INTERVAL, SCHEDULED_JOB_OFFSET
# from threading import Timer
# from jobs import SyncEtsyShopReceipts
# myScheduler = BlockingScheduler()
# from apscheduler.executors.pool import ProcessPoolExecutor
myScheduler = MyScheduler().scheduler
# executors = {
#     'default': {'type': 'threadpool', 'max_workers': 20},
#     'processpool': ProcessPoolExecutor(max_workers=5)
# }
logging = Logger().logging
# import time
import os
from database import MongoDB
from fastapi import FastAPI
mongodb = MongoDB()

app = FastAPI()

job_offset = 0
@app.on_event("startup")
async def startup_event():
	global job_offset
	mongodb = MongoDB()
	logging.info("FastAPI startup_event")
	etsy_connections = await mongodb.db["EtsyShopConnections"].find().to_list(100)
	
	for etsy_connection_id in etsy_connections:
		etsy_connection_id = str(etsy_connection_id['_id'])
		logging.info(colored(f"ETSY_CONNECTION_ID: {etsy_connection_id}", 'blue', 'on_white', attrs=['reverse', 'blink']))
		# myScheduler.add_job(
		# 	syncShop,
		# 	kwargs={"etsy_connection_id": etsy_connection_id},
		# 	replace_existing=True,
		# 	jobstore='mongodb'
		# )
		myScheduler.add_job(
			syncShop,
			"interval",
			minutes=SCHEDULED_JOB_INTERVAL + job_offset,
			kwargs={"etsy_connection_id": etsy_connection_id},
			id=f"{etsy_connection_id}:syncShopProcess",
			name=f"{etsy_connection_id}:syncShopProcess",
			replace_existing=True,
			jobstore='mongodb'
		)
		job_offset += SCHEDULED_JOB_OFFSET
	print('Press Ctrl+C to exit')
	myScheduler.start()



	

@app.get("/")
async def root():
    return {"message": "APScheduler"}


def test(foo):
	print("ITS WORKING HAHAHAHAHAH", foo)


class SyncShopProcess(BaseModel):
	etsy_connection_id: str


@app.post('/apscheduler/add/syncShopProcess')
async def add_sync_shop_job_to_scheduler(etsy_connection_idx: SyncShopProcess):
	global job_offset
	etsy_connection_id = etsy_connection_idx.dict().get('etsy_connection_id')
	check_mongodb = await mongodb.db['apscheduler.jobs'].find_one({"_id": f'{etsy_connection_id}:syncShopProcess'})
	if check_mongodb is not None:
		return {"error": f'{etsy_connection_id}:syncShopProcess ALREADY EXISTS.'}
	# myScheduler.add_job(
	# 	syncShop,
	# 	"interval",
	# 	minutes=SCHEDULED_JOB_INTERVAL + job_offset,
	# 	kwargs={"etsy_connection_id": etsy_connection_id},
	# 	id=f"{etsy_connection_id}:syncShopProcess",
	# 	name=f"{etsy_connection_id}:syncShopProcess",
	# 	replace_existing=True,
	# 	jobstore='mongodb'
	# )
	myScheduler.add_job(
		syncShop,
		"interval",
		minutes=SCHEDULED_JOB_INTERVAL + job_offset,
		kwargs={"etsy_connection_id": etsy_connection_id},
		id=f"{etsy_connection_id}:syncShopProcess",
		name=f"{etsy_connection_id}:syncShopProcess",
		replace_existing=True,
		jobstore='mongodb'
	)
	return {"success": f'{etsy_connection_id}:syncShopProcess SUCCESSFULLY ADDED TO THE JOBLIST.'}



# import random
# syncEtsyShopReceipts = SyncEtsyShopReceipts()

# from apscheduler.schedulers.asyncio import AsyncIOScheduler

# sched = AsyncIOScheduler()


# @sched.scheduled_job()


# def sync_etsy_shop_receipts(etsy_connection_id):
# 	q.enqueue(
# 		syncShop,
# 		job_id=etsy_connection_id,
# 		description=f"Fetch new Receipts and check unpaid receipts for ETSY_SHOP:{etsy_connection_id}",
# 		kwargs={"etsy_connection_id": etsy_connection_id},
# 	)


# job_offset = 0
# # syncEtsyShopReceipts.get_jobs_to_schedule()
# for etsy_connection_id in syncEtsyShopReceipts.get_jobs_to_schedule():
# 	logging.info(colored(f"ETSY_CONNECTION_ID: {etsy_connection_id}", 'blue', 'on_white', attrs=['reverse', 'blink']))
# 	myScheduler.add_job(
# 		syncShop,
# 		kwargs={"etsy_connection_id": etsy_connection_id},
# 		replace_existing=True,
# 		jobstore='mongodb'
# 	)
# 	myScheduler.add_job(
# 		syncShop,
# 		"interval",
# 		minutes=SCHEDULED_JOB_INTERVAL + job_offset,
# 		kwargs={"etsy_connection_id": etsy_connection_id},
# 		id=f"{etsy_connection_id}:syncShopProcess",
# 		name=f"{etsy_connection_id}:syncShopProcess",
# 		replace_existing=True,
# 		jobstore='mongodb'
# 	)
# 	job_offset += SCHEDULED_JOB_OFFSET

# print('Press Ctrl+C to exit')
# myScheduler.start()
# print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
# def test_jb(a):
# 	print(f"TEST JOB {a * random.randint(1, 99)}")

# def add_job_after():
# 	myScheduler.add_job(
# 		test_jb,
# 		"interval",
# 		seconds=15,
# 		args=[random.randint(1, 99)]
# 	)

# test = Timer(30, add_job_after)
# Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.

# try:
# 	asyncio.get_event_loop().run_forever()
# except (KeyboardInterrupt, SystemExit):
# 	pass
# finally:
# 	pass


	


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
