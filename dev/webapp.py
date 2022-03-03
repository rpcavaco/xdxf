import logging
import re
from logging.handlers import RotatingFileHandler


# from typing import Optional
from fastapi import FastAPI, Request, HTTPException #BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dbase import DBPool #, sql_build_sel
# from copy import copy
# from datetime import datetime as dt
# from io import BytesIO #, StringIO

from sql_src import *
from config import ROLE_CFG, AUTH_USERS, DB_SCHEMA

#from openpyxl import Workbook
# from openpyxl.styles import Font
# from openpyxl.worksheet.dimensions import ColumnDimension, DimensionHolder
# from openpyxl.utils import get_column_letter

from common import getRedisMonitorURL, REDIS_WEBAPP_MSG_KEY, \
	REDIS_ALLBGWRKRS_MSG_KEY, REDIS_BGWRKR_MSG_KEY_PATT, TAILLOGS_LINES
from messaging import MessagingMgr
from manage_workers import ensure_enough_workers_running, kill_all_workers
from background_worker import check_logs as bgcheck_logs

def create_app():

	logger = logging.getLogger('main')
	logformatter = logging.Formatter(
		'%(asctime)s %(levelname)s: %(message)s '
		'[in %(pathname)s:%(lineno)d]'
	)	
	logger.setLevel(logging.DEBUG)

	handler = RotatingFileHandler('log/webapp.log', maxBytes=2097152, backupCount=10)
	handler.setFormatter(logformatter)
	logger.addHandler(handler)

	fapp = FastAPI()
	# dbp = DBPool("conncfg.json")
	dbnum, url = getRedisMonitorURL()
	mmgr = MessagingMgr(url, REDIS_WEBAPP_MSG_KEY, REDIS_ALLBGWRKRS_MSG_KEY, REDIS_BGWRKR_MSG_KEY_PATT)

	@fapp.middleware("http")
	async def session_middleware(request: Request, call_next):
		# request.state.dbobj = dbp
		request.state.mmgr = mmgr
		# logger = logging.getLogger('main')
		# dbtest = await request.state.dbobj.test()
		response = await call_next(request)
		return response

	@fapp.middleware("http")
	async def auth_session_middleware(request: Request, call_next):
		found = False
		if "remote-user" in request.headers:
			remote_user = request.headers["remote-user"]
			splits = re.split(r"[\\]+", remote_user)
			if len(splits) == 2:
				domain = splits[0]
				user = splits[1]
				if domain in AUTH_USERS.keys():
					if user in AUTH_USERS[domain].keys():
						rolename = AUTH_USERS[domain][user]
						rolecfgobj = ROLE_CFG[rolename]
						request.state.authobj = {
							"domain": domain,
							"user": user,
							"rolecfgobj": rolecfgobj
						}
						found = True 
		if not found:
			request.state.authobj = None
		response = await call_next(request)
		return response

	@fapp.on_event("startup")
	async def startup():
		await dbp.openup()

	@fapp.on_event("shutdown")
	async def shutdown():
		await dbp.teardown()

	@fapp.get("/")
	async def homepage():
		return FileResponse('static/index.html')

	@fapp.get("/favicon.ico")
	async def homepage():
		return FileResponse('static/media/fcmp.png')

	@fapp.get("/hello")
	async def hello(request: Request):
		if not request.state.dbobj is None:
			ret = await request.state.dbobj.test()
			dbname = request.state.dbobj.cfgdict["database"]
		else:
			ret = False
			dbname = "None"
		authobj = request.state.authobj
		# bckgrdstate = request.state.bckmgr.getIsInExecution();
		# return { "dbpooltest": ret, "bckgrdstate": bckgrdstate } 
		return { "dbpooltest": ret, "database": dbname, "authobj": authobj } 

	@fapp.get("/reconnect")
	async def reconnect(request: Request):
		res = "OK"
		dbtest = await request.state.dbobj.test()
		if not dbtest:
			try:
				await request.state.dbobj.openup()
			except:
				res = "NOTOK"
		return { "res": res } 

	# @fapp.get("/schemata")
	# async def schemata(request: Request):
	# 	logger = logging.getLogger('main')
	# 	schemata = []
	# 	if not request.state.dbobj.pool is None:
	# 		dbname = request.state.dbobj.cfgdict["database"]
	# 		schlist = request.state.authobj["rolecfgobj"][dbname].keys()
	# 		sqlsrc = SQL_LIST_SCHEMATA.format("'{}'".format(dbname), ",".join(["'{}'".format(x) for x in schlist]))
	# 		try:
	# 			async with request.state.dbobj.pool.acquire() as conn:
	# 				async with conn.transaction():
	# 					async for record in conn.cursor(sqlsrc):
	# 						schemata.append(record[0])

	# 		except:
	# 			logger.exception("Erro em schemata")

	# 	return { "schemata": schemata }

	@fapp.get("/dryrun")
	async def dryrun(request: Request, uuid: str):
		ensure_enough_workers_running()
		ret = await mmgr.sendRunTaskRequestToWorkers("background_worker.DryRunTask", uuid)
		return { "res": "OK", "ret": ret }

	# @fapp.websocket("/ws")
	# async def websocket_endpoint(websocket: WebSocket):
	# 	await bckmgr.connectws(websocket)
	# 	try:
	# 		while True:
	# 			data = await websocket.receive_json()
	# 			print("wsdata", data)
	# 	except WebSocketDisconnect:
	# 		await bckmgr.disconnectws(websocket)

	# fapp.mount("/output", StaticFiles(directory='output'), name='output')
	fapp.mount("/css", StaticFiles(directory='static/css'), name='static_css')
	fapp.mount("/js", StaticFiles(directory='static/js'), name='static_js')
	fapp.mount("/media", StaticFiles(directory='static/media'), name='static_media')

	return fapp


app = create_app()

# if __name__ == "__main__":
#	teste_xml()


