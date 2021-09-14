import logging
from config import ENV_MODE

class Logger(object):
	_instance = None

	def __new__(cls):
		if cls._instance is None:
			print("No Logger found.")
			cls._instance = object.__new__(cls)
			logging.basicConfig(
				level=logging.DEBUG if ENV_MODE == 'DEV' else logging.INFO,
				format='%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
				datefmt='%Y-%m-%d,%H:%M:%S',
				handlers=[
					logging.StreamHandler(),
				],
				encoding='utf-8'
			)
			Logger._instance.logging = logging
		return cls._instance

	def __init__(self):
		self.logging = self._instance.logging
