from fastapi import FastAPI
from fastapi_socketio import SocketManager

class MySocketManger(object):
	_instance = None
	
	def __new__(cls, app, *args, **kargs):
		if cls._instance is None:
			cls._instance = object.__new__(cls)
			MySocketManger._instance.socket_manager = SocketManager(app=app)
		return cls._instance

	def __init__(self, app):
		self.socket_manager = MySocketManger._instance.socket_manager

if __name__ == '__main__':
	app = FastAPI()
	socket_manager1 = MySocketManger(app).socket_manager
	socket_manager2 = MySocketManger(app).socket_manager
	socket_manager3 = MySocketManger(app).socket_manager
	print(id(socket_manager1))
	print(id(socket_manager2))
	print(id(socket_manager3))