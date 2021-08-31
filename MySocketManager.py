from MyLogger import Logger
logging = Logger().logging
from typing import Set
import socketio
from socketio.asyncio_server import AsyncServer
from config import REDIS_TLS_URL, REDIS_URL, FRONTEND_URI, SOCKETIO_PATH, MOUNT_LOCATION, ASYNC_MODE, SOCKETIO_MAIN_ROOM
from fastapi import FastAPI


class MySocketManager:
	def __init__(self, app: FastAPI) -> None:
		self._mgr = socketio.AsyncRedisManager(REDIS_TLS_URL)
		self._sio: AsyncServer = socketio.AsyncServer(
			client_manager=self._mgr, 
			async_mode=ASYNC_MODE, 
			cors_allowed_origins=[]
		)
		self._app = socketio.ASGIApp(
			socketio_server=self._sio,
			socketio_path=SOCKETIO_PATH
		)
		app.mount(MOUNT_LOCATION, self._app)
		app.sio = self._sio
		logging.info

	def get_socket_manager(self) -> AsyncServer:
		return self._sio


# class ConnectionManager:
# 	def __init__(self, app) -> None:
# 		self.app = app
# 		self.connected_users: Set = set()

# 	def add_user(self, user_id: str) -> bool:
		
# 		try:
# 			self.connected_users.add(user_id)
