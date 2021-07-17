from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from apscheduler.jobstores.mongodb import MongoDBJobStore


class MyScheduler:
	def __init__(self, mongodb) -> None:
		# jobstores = {
		# 	"mongo": MongoDBJobStore(
		# 		database="multiorder",
		# 		collection="apscheduler.jobs",
		# 		host=mongodb.client.HOST,
		# 		port=mongodb.client.PORT
		# 	)
		# }
		# print(dir(mongodb.client))
		self.scheduler = AsyncIOScheduler()
		self.scheduler.start()
