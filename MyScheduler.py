from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from MyLogger import Logger
from config import ENV_MODE, MONGODB_URI
logging = Logger().logging
# from database import MongoDB
# mongodb = MongoDB()


class MyScheduler(object):
	_instance = None
	
	def __new__(cls, *args, **kwargs):
		if cls._instance is None:
			logging.info("No Scheduler found creating one.")
			cls._instance = object.__new__(cls)
			MyScheduler._instance.scheduler = AsyncIOScheduler()
		return cls._instance
	
	def __init__(self) -> None:
		jobstores = {
			"mongodb": MongoDBJobStore(
				database="multiorder",
				collection="apscheduler.jobs",
				# client=mongodb.client
				host=MONGODB_URI,
				# port=mongodb.client.PORT
			)
		}
		# print(dir(mongodb.client))
		# redis_connection_url = urlparse(REDIS_TLS_URL)
		# jobstores = {
		# 	"redis": RedisJobStore(host=redis_connection_url.hostname,
		# 	                       port=redis_connection_url.port,
		# 	                       username=redis_connection_url.username,
		# 	                       password=redis_connection_url.password,
		# 	                       ssl=True,
		# 	                       ssl_cert_reqs=None)
		# }
		self.jobs = {}
		self.scheduler: AsyncIOScheduler = self._instance.scheduler
		if ENV_MODE == "DEV":
			self.scheduler.configure( job_defaults={'misfire_grace_time': 3600})
		else:
			self.scheduler.configure(jobstores=jobstores, job_defaults={'misfire_grace_time': 3600})
		# self.scheduler.start()

	def add_job(self, my_id, *args, **kwargs):
		try:
			self.jobs[my_id]
		except KeyError:
			logging.info(f"No job with the id {my_id} found. Adding to the job list.")
			self.scheduler.add_job(*args, **kwargs)
		else:
			logging.info(f"There is already a job with the id {my_id}.")
