import datetime
import json
from bson import ObjectId


class JSONEncoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, ObjectId):
			return str(o)
		if isinstance(o, datetime.datetime):
			return o.__str__()
		return json.JSONEncoder.default(self, o)
