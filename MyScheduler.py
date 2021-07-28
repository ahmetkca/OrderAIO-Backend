from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from apscheduler.jobstores.mongodb import MongoDBJobStore


class MyScheduler(object):
	_instance = None
	
	def __new__(cls, *args, **kwargs):
		if cls._instance is None:
			cls._instance = object.__new__(cls)
			print("No Scheduler Found.")
			print("Creating a new Scheduler.")
			MyScheduler._instance.scheduler = AsyncIOScheduler()
		return cls._instance
	
	def __init__(self) -> None:
		# jobstores = {
		# 	"mongodb": MongoDBJobStore(
		# 		database="multiorder",
		# 		collection="apscheduler.jobs",
		# 		# client=mongodb.client
		# 		host=mongodb.client.HOST,
		# 		port=mongodb.client.PORT
		# 	)
		# }
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
		self.scheduler = self._instance.scheduler
		# self.scheduler.start()
