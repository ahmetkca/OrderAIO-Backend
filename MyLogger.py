import logging
from config import ENV_MODE

class Logger(object):
	_instance = None

	def __new__(cls):
		if cls._instance is None:
			print("No Logger found.")
			cls._instance = object.__new__(cls)
			logging.basicConfig(
				format='%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
				datefmt='%Y-%m-%d,%H:%M:%S',
				level=logging.INFO,
				handlers=[
					logging.StreamHandler(),
					logging.FileHandler(mode='w', filename='my_log.log') if ENV_MODE == "DEV" else None,
				],
				encoding='utf-8'
			)
			Logger._instance.logging = logging
		return cls._instance

	def __init__(self):
		self.logging = self._instance.logging
