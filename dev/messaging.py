
import logging
import aioredis
import json


from typing import List

from fastapi import WebSocket
from starlette.websockets import WebSocketState


class MessagingMgr:
	
	def __init__(self, p_redis_url, p_webapp_msg_key, p_allworkers_msg_key, p_worker_msg_key_patt) -> None:
		# super().__init__()
		self.webapp_msg_key = p_webapp_msg_key
		self.allworkers_msg_key = p_allworkers_msg_key
		self.worker_msg_key_patt = p_worker_msg_key_patt
		self.redis = aioredis.from_url(p_redis_url, encoding='utf-8')
		self.active_websockets: List[WebSocket] = []

	def _run_message(self, p_classname, p_uuid, args=None) -> str:
		ret = { 
			"msg": "run",
			"task_uid": p_uuid,
			"classname": p_classname
		}
		if not args is None:
			ret["args"] = args
		return json.dumps(ret)

	async def checkRedis(self):
		ret = await self.redis.ping()
		return ret

	def _cancel_message(self, p_worker_num, p_task_uid) -> str:
		return json.dumps({ 
			"msg": "cancel",
			"worker": p_worker_num,
			"task_uid": p_task_uid
		})

	async def shutdown(self):
		while len(self.active_websockets) > 0:
			ws = self.active_websockets.pop()
			if ws.client_state == WebSocketState.CONNECTED:
				await ws.close()
			ws = None
		await self.redis.close()

	async def connectws(self, websocket: WebSocket):
		await websocket.accept()
		self.active_websockets.append(websocket)	

	async def disconnectws(self, websocket: WebSocket):
		if websocket.client_state == WebSocketState.CONNECTED:
			await websocket.close()
		self.active_websockets.remove(websocket)

	async def broadcastws(self, p_payload):
		for ws in self.active_websockets:
			await ws.send_json(p_payload)

	async def sendRunTaskRequestToWorkers(self, p_task_classname, p_uuid, args=None):
		logger = logging.getLogger('main')
		msg = self._run_message(p_task_classname, p_uuid, args=args)
		logger.debug(f"sendTaskRequestToWorkers, msg: {msg}")
		ret = await self.redis.lpush(self.allworkers_msg_key, msg)
		return ret

	async def sendCancelTaskRequestToWorker(self, p_worker_num, p_task_uid):
		logger = logging.getLogger('main')
		msg = self._cancel_message(p_worker_num, p_task_uid)
		msgkey = self.worker_msg_key_patt.format(p_worker_num)
		logger.debug(f"sendCancelTaskRequestToWorker, msg: {msg}, msgkey: {msgkey}")
		ret = await self.redis.lpush(msgkey, msg)
		return ret

	async def getWorkerMessageFromRedis(self):
		async with self.redis as r:
			return await r.brpop(self.webapp_msg_key)

	async def waitOnWorkerMessages(self):
		logger = logging.getLogger('main')
		try:
			while True:
				payload = await self.getWorkerMessageFromRedis()
				logger.debug(f"waitOnWorkerMessages, msg: {payload}")
				try:
					json_load = json.loads(payload[1])
				except Exception as e:
					logger.exception("waitOnWorkerMessages")
					json_load = { "erro": str(e) }
				await self.broadcastws(json_load)
		except:
			logger.exception("Exceção em waitOnWorkerMessages")


