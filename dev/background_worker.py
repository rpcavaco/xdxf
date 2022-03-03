import argparse
import asyncio
import aioredis
import logging
import json

from os import makedirs
from os.path import exists, abspath, dirname, join as path_join
from logging.handlers import RotatingFileHandler
from pydoc import locate
from abc import ABC, abstractmethod
from datetime import datetime as dt
from uuid import UUID
from aioredis.exceptions import ConnectionError

from common import getRedisWorkerURL, REDIS_ALLBGWRKRS_MSG_KEY, \
		REDIS_BGWRKR_MSG_KEY_PATT, REDIS_WEBAPP_MSG_KEY
from dbase import DBPool
from sql_src import SQL_NOVA_TAREFA, SQL_FINAL_TAREFA, SQL_LOG

def check_logs():

	path = path_join(dirname(abspath(__file__)), 'logs')
	if not exists(path):
		makedirs(path)
	full_path = path_join(path, 'background_worker.log')
	if not exists(full_path):
		open(full_path, "w")

	return full_path

class BackgroundWorker:

	def __init__(self, p_redis_url, p_allworkers_msg_key, p_thisworkermsg_key_patt, p_workernum) -> None:
		# super().__init__()
		self.allworkers_msg_key = p_allworkers_msg_key
		self.thisworker_msg_key = p_thisworkermsg_key_patt.format(p_workernum)
		self.redis_url = p_redis_url
		self.workernum = p_workernum
		self.redis = aioredis.from_url(self.redis_url, encoding='utf-8')
		self.task_instances = {}
		self.working = False # TODO verificar e completar funcionalidade de "working"

	async def processMessage(self, p_payload):

		logger = logging.getLogger('background_worker')
		if "msg" in p_payload.keys():

			msg = p_payload["msg"]
			# print("processMessage msg:", msg)

			if msg == "cancel":

				task_uid = UUID(p_payload['task_uid'])
				assert self.workernum == p_payload["worker"], f"BackgroundWorker {self.workernum} erro de num.worker inesperado na mensagem recebida, recebido: {p_payload['worker']}, esperado: {self.workernum}"
				found_pair = None

				for ti_classname in self.task_instances.keys():
					for t_instance_pair in self.task_instances[ti_classname]:
						t_instance_pair["instance"]
						if t_instance_pair["instance"].task_uid == task_uid:
							found_pair = t_instance_pair
							break 
					if not found_pair is None:
						break

				if not found_pair is None:

					# https://github.com/rpcavaco/backofficev2/issues/15#issuecomment-939800205
					cancel_flag_set = found_pair["instance"].setCancelFlag()
					if cancel_flag_set:
						await found_pair["instance"].canceltask("Tarefa cancelada - via 'cancel flag'")
					else:
						if not found_pair["task"].cancelled() and not found_pair["task"].done():
							found_pair["task"].cancel()
							try:
								await found_pair["task"]
							except asyncio.CancelledError:
								await found_pair["instance"].canceltask("Tarefa cancelada - via asyncio.cancel()")
				else:
					raise RuntimeError(f"BackgroundWorker {self.workernum}, cancel: uid not found {task_uid} in {[a.task_uid for a in self.task_instances ]}")

			elif msg == "run":

				self.working = True
				task_uid = UUID(p_payload['task_uid'])

				the_instance = None
				instance_order = -1

				if p_payload["classname"] in self.task_instances.keys():
					for oi, ti in enumerate(self.task_instances[p_payload["classname"]]):
						if not ti["instance"].inuse_flag:
							instance_order = oi
							the_instance = ti["instance"]
							break

				if the_instance is None:

					the_class = locate(p_payload["classname"])
					if the_class is None:
						logger.error(f"BackgroundWorker {self.workernum} processMessage 'run', classe inexistente { json.dumps(p_payload) }")
					else:
						if hasattr(the_class, 'dorun'):
							# INSTANCIAÇÃO DAS BACKGROUND TASKS
							the_instance = the_class(self.redis_url, self.thisworker_msg_key, self.workernum)
						else:
							logger.error(f"BackgroundWorker {self.workernum} processMessage 'run', classe sem método 'dorun' { json.dumps(p_payload) }")

					if not the_instance is None:
						if not p_payload["classname"] in self.task_instances.keys():
							self.task_instances[p_payload["classname"]] = []
						self.task_instances[p_payload["classname"]].append({
							"instance": the_instance,
							"task": None
						})
						instance_order = len(self.task_instances[p_payload["classname"]]) - 1

				if not the_instance is None:
					the_instance.setTaskUID(task_uid)
					self.task_instances[p_payload["classname"]][instance_order]["task"] = asyncio.create_task(the_instance.dorun(p_payload))

	async def getMessageFromRedis(self):
		async with self.redis as r:
			if self.working:
				# Se estiver ocupado, escutar apenas as mensagens dirigidas a si próprio, 
				#   para não remover mensagens que podem ser processadas por outro worker
				ret = await r.brpop(self.thisworker_msg_key)
			else:
				ret = await r.brpop([self.thisworker_msg_key, self.allworkers_msg_key])
			return ret

	async def waitOnWebappMessages(self):
		logger = logging.getLogger('background_worker')
		while True:
			payload = await self.getMessageFromRedis()
			logger.info(f"BackgroundWorker {self.workernum}, waitOnWebappMessages, msg: {payload}")
			try:
				rcvkey = payload[0].decode('utf-8')
				assert rcvkey == self.allworkers_msg_key or rcvkey == self.thisworker_msg_key, f"BackgroundWorker {self.workernum} erro de chave inesperada na mensagem recebida, recebido: {rcvkey}, esperado: {self.allworkers_msg_key} ou {self.thisworker_msg_key}"
				json_load = json.loads(payload[1])
			except Exception as e:
				self.working = False
				logger.exception("BackgroundWorker {self.workernum}, waitOnWebappMessages, consumindo mensagens")
				json_load = { "erro": str(e) }
				continue

			try:
				if json_load["msg"] == "stopped_working":
					self.working = False
					continue
				else:
					await self.processMessage(json_load)
			except:
				logger.exception("BackgroundWorker {self.workernum}, waitOnWebappMessages, durante processMessage")
				self.working = False


class AbstractBackgroundTask(ABC):

	def __init__(self, p_name, p_db_schema:str, p_redis_url:str, p_thisworkermsg_key: str, p_workernum: int, cancel_with_flag: bool = False) -> None:
		# super().__init__()
		# self.dbp = DBPool(DBCONN_CFG_JSON)
		self.redis = aioredis.from_url(p_redis_url, encoding='utf-8')
		self.name = p_name
		self.workernum = p_workernum
		self.thisworker_msg_key = p_thisworkermsg_key
		self.task_uid = None
		self.cancel_with_flag = cancel_with_flag # 
		self.inuse_flag = False
		self.cancel_flag = False
		self.db_schema = p_db_schema

	def _message(self, p_msg, p_status) -> str:
		return json.dumps({ 
				"worker": self.workernum,
				"task_uid": str(self.task_uid), 
				"msg": p_msg, 
				"estado": p_status,
				"ts": dt.now().strftime("%Y-%m-%d %H:%M:%S")
		})

	def _stopwork_message(self) -> str:
		return json.dumps({ 
				"msg": "stopped_working" 
		})		

	def setTaskUID(self, p_uuid):
		self.task_uid = p_uuid

	@abstractmethod
	async def dorun(self, p_payload):
		self.inuse_flag = True
		# self.cancel_flag = False
		await self.dbp.openup()

	def setCancelFlag(self):
		ret = False
		if self.cancel_with_flag:
			self.cancel_flag = True
			ret = True
		return ret

	async def testdb(self):
		ret = True
		logger = logging.getLogger('background_worker')
		try:
			assert self.dbp.isOpened(), "DBPool por abrir"
			async with self.dbp.pool.acquire() as conn:
				val = await conn.fetchval("select 1")
			if val is None:
				raise RuntimeError(f"BackgroundWorker {self.workernum}, BD indisponivel em '{self.name}'")
		except:
			ret = False
			logger.exception(f"BackgroundWorker {self.workernum}, erro na tarefa '{self.name}'")

		return ret

	async def newdbtask(self, p_idop: str, ref_ts = None):
		assert self.dbp.isOpened(), "DBPool por abrir"
		async with self.dbp.pool.acquire() as conn:
			sentinel_task_uid = await conn.fetchval(SQL_NOVA_TAREFA.format(self.db_schema), self.workernum, self.name, self.task_uid, p_idop, ref_ts)
			if sentinel_task_uid is None:
				raise RuntimeError(f"BackgroundWorker {self.workernum}, impossivel iniciar tarefa de BD em '{self.name}'")

	async def finishdbtask(self, inerror: bool):
		if not self.task_uid is None:
			assert self.dbp.isOpened(), f"BackgroundWorker {self.workernum}, DBPool por abrir"
			async with self.dbp.pool.acquire() as conn:
				await conn.execute(SQL_FINAL_TAREFA.format(self.db_schema), inerror, self.task_uid)
		self.inuse_flag = False		
		await self.redis.rpush(self.thisworker_msg_key, self._stopwork_message())

	async def _chgtask(self, p_msg, p_status):
		assert self.dbp.isOpened(), f"BackgroundWorker {self.workernum}, DBPool por abrir"
		async with self.dbp.pool.acquire() as conn:
			await conn.execute(SQL_LOG.format(self.db_schema), self.task_uid, p_msg, p_status)
		await self.redis.rpush(REDIS_WEBAPP_MSG_KEY, self._message(p_msg, p_status))	

	async def inittask(self, p_msg):
		assert self.dbp.isOpened(), f"BackgroundWorker {self.workernum}, DBPool por abrir"
		status = "START"
		await self._chgtask(p_msg, status)

	async def steptask(self, p_msg):
		assert self.dbp.isOpened(), f"BackgroundWorker {self.workernum}, DBPool por abrir"
		status = "STEP"
		await self._chgtask(p_msg, status)

	async def canceltask(self, p_msg):
		assert self.dbp.isOpened(), f"BackgroundWorker {self.workernum}, DBPool por abrir"
		status = "CANCEL"
		await self._chgtask(p_msg, status)

	async def endtask(self, p_msg, inerror: bool):
		assert self.dbp.isOpened(), f"BackgroundWorker {self.workernum}, DBPool por abrir"
		if inerror:
			status = "ERROR"
		else:
			status = "END"
		await self._chgtask(p_msg, status)


class DryRunTask(AbstractBackgroundTask):

	def __init__(self, p_db_schema:str, p_redis_url:str, p_thisworkermsg_key_patt: str, p_worker_num: int) -> None:
		super().__init__("Dry run", p_db_schema, p_redis_url, p_thisworkermsg_key_patt, p_worker_num)

	async def dorun(self, p_payload):
		
		await super().dorun(p_payload)

		logger = logging.getLogger('background_worker')
		rangeval = 4
		waittime = 2
		em_erro = False

		if not await self.testdb():			
			return
		else:
			try:
				await self.newdbtask("DRYRUN")
				await self.inittask("Inicio de -- dry run --")					
				for i in range(rangeval):
					# if self.cancel_flag:
					# 	raise RuntimeError("tarefa cancelada")
					await asyncio.sleep(waittime)
					await self.steptask(f"a executar step {i} dry run")
					if i == rangeval-1:
						raise RuntimeError(f"BackgroundWorker {self.workernum}, erro ficticio colossal em dry run")

				await self.endtask("Final -- dry run --", inerror=False)

			except Exception as e:
				em_erro = True
				logger.exception(f"BackgroundWorker {self.workernum}, excecao em '{self.name}'")
				await self.endtask(f"Quebra de -- dry run -- {str(e)}", inerror=em_erro)

			finally:
				await self.finishdbtask(em_erro)


async def main(p_worker_num):


	logger = logging.getLogger('background_worker')

	try:

		dbnum , url = getRedisWorkerURL()

		bckwrkr = BackgroundWorker(url, REDIS_ALLBGWRKRS_MSG_KEY, REDIS_BGWRKR_MSG_KEY_PATT, p_worker_num)
		logger.info(f"worker {p_worker_num}, waiting on db:{dbnum}, key:{REDIS_ALLBGWRKRS_MSG_KEY}")
		await bckwrkr.waitOnWebappMessages()

	except ConnectionError as ce:
		logger.exception(f"Worker {p_worker_num}, Redis incontactável")

	except Exception as e:
		logger.exception(f"Worker {p_worker_num}, exceção no main de background_worker")


if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("n", help="worker number", type=int)
	args = parser.parse_args()

	logger = logging.getLogger('background_worker')
	logformatter = logging.Formatter(
		'%(asctime)s %(levelname)s: %(message)s '
		'[in %(pathname)s:%(lineno)d]'
	)	
	logger.setLevel(logging.DEBUG)

	full_path = check_logs()

	handler = RotatingFileHandler(full_path, maxBytes=2097152, backupCount=10)
	handler.setFormatter(logformatter)
	logger.addHandler(handler)

	try:
		asyncio.run(main(args.n))
	except KeyboardInterrupt:
		logger.info(f"Worker {args.n}, processo cancelado via teclado")
