from database import MongoDB
from MyLogger import Logger
logging = Logger().logging

def test():
	logging.info("TEST DELETE ME")
	mongodb = MongoDB()