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
	dbp = DBPool("conncfg.json")

	@fapp.middleware("http")
	async def db_session_middleware(request: Request, call_next):
		request.state.dbobj = dbp
		logger = logging.getLogger('main')
		dbtest = await request.state.dbobj.test()
		response = None
		if not dbtest:
			try:
				await dbp.openup()
				request.state.dbobj = dbp
				response = await call_next(request)
			except:
				logger.exception("BD inacessivel")		
		else:
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

	@fapp.get("/schemata")
	async def schemata(request: Request):
		logger = logging.getLogger('main')
		schemata = []
		if not request.state.dbobj.pool is None:
			dbname = request.state.dbobj.cfgdict["database"]
			schlist = request.state.authobj["rolecfgobj"][dbname].keys()
			sqlsrc = SQL_LIST_SCHEMATA.format("'{}'".format(dbname), ",".join(["'{}'".format(x) for x in schlist]))
			try:
				async with request.state.dbobj.pool.acquire() as conn:
					async with conn.transaction():
						async for record in conn.cursor(sqlsrc):
							schemata.append(record[0])

			except:
				logger.exception("Erro em schemata")

		return { "schemata": schemata }

	@fapp.get("/hedit_candidates")
	async def hedit_candidates(request: Request, schema: str):
		logger = logging.getLogger('main')
		he_candidates = []
		if not request.state.dbobj.pool is None:
			try:
				async with request.state.dbobj.pool.acquire() as conn:
					async with conn.transaction():
						sqlstr = SQL_LIST_HIBEDIT_CANDIDATES.format(DB_SCHEMA)
						async for record in conn.cursor(sqlstr, schema):
							he_candidates.append(record)
			except:
				logger.exception("Erro em hedit_candidates")

		return {  "hedit_candidates": he_candidates }

	@fapp.get("/tablecols")
	async def tablecols(request: Request, schema: str, tname: str):
		logger = logging.getLogger('main')
		cols = []
		if not request.state.dbobj.pool is None:
			try:
				async with request.state.dbobj.pool.acquire() as conn:
					async with conn.transaction():
						sqlstr = SQL_LIST_EXISTING_COLUMNS
						dbname = request.state.dbobj.cfgdict["database"]
						async for record in conn.cursor(sqlstr, dbname, schema, tname):
							cols.append(record[0])
			except:
				logger.exception("Erro em tablecols")

		return {  "cols": cols }

	@fapp.get("/grants")
	async def grants(request: Request, schema: str, tname: str, basetable: bool):
		logger = logging.getLogger('main')
		granted_users = []
		if not request.state.dbobj.pool is None:
			try:
				async with request.state.dbobj.pool.acquire() as conn:
					async with conn.transaction():
						sqlstr = SQL_LIST_EDITGRANTS
						dbname = request.state.dbobj.cfgdict["database"]
						if basetable:
							tn = tname
						else:
							tn = tname + "_evw"
						async for record in conn.cursor(sqlstr, dbname, schema, tn):
							granted_users.append(record[0])
			except:
				logger.exception("Erro em grants")

		return {  "granted_users": granted_users }


	@fapp.get("/tablerrorflags")
	async def tablerrorflags(request: Request, schema: str, tname: str):
		logger = logging.getLogger('main')
		flags = []
		if not request.state.dbobj.pool is None:
			try:
				async with request.state.dbobj.pool.acquire() as conn:
					async with conn.transaction():
						sqlstr = SQL_THEME_ERROR_FLAGS.format(DB_SCHEMA)
						async for record in conn.cursor(sqlstr, schema, tname):
							flags.append(record[0])
			except:
				logger.exception("Erro em tablerrorflags")

		return {  "error_flags": flags }

	@fapp.get("/altphibrido_params")
	async def altphibrido_params(request: Request, schema: str):
		logger = logging.getLogger('main')

		if request.state.authobj is None:
			raise HTTPException(status_code=401, detail="Apenas acessso autenticado")	

		dbname = request.state.dbobj.cfgdict["database"]
		params_obj = request.state.authobj["rolecfgobj"][dbname][schema]

		if params_obj["cols_classes_regex"] is None:
			sqlstr = SQL_LIST_COL_CLASSES.format(DB_SCHEMA)
		else:
			sqlstr = SQL_LIST_COL_CLASSES_RE.format(DB_SCHEMA)

		cols_classes = []
		if not request.state.dbobj.pool is None:
			try:
				async with request.state.dbobj.pool.acquire() as conn:
					async with conn.transaction():
						if params_obj["cols_classes_regex"] is None:
							async for record in conn.cursor(sqlstr):
								cols_classes.append(record[0])
						else:
							async for record in conn.cursor(sqlstr, params_obj["cols_classes_regex"]):
								cols_classes.append(record[0])

			except:
				logger.exception("Erro em tablecols")

		return {  
			"editor": params_obj["editor"],
			"viewer": params_obj["viewer"],
			"cols_classes": cols_classes
		}

	@fapp.get("/altphibrido")
	async def altphibrido(request: Request, schema: str, tname: str, classname: str, editoruser: str, vieweruser: str):
		
		logger = logging.getLogger('main')

		if request.state.authobj is None:
			raise HTTPException(status_code=401, detail="Apenas acessso autenticado")	

		status = "NOTOK"
		msg = ""
		ret = -9
		if not request.state.dbobj.pool is None:

			try:
				async with request.state.dbobj.pool.acquire() as conn:
					sqlstr = SQL_ALTERAR_TEMA.format(DB_SCHEMA)
					ret = await conn.fetchval(sqlstr, schema, tname, classname, editoruser, vieweruser)
			except:
				logger.exception("Erro em altphibrido")

			if ret < 1:
				msg = f"Erro geral ret:{ret}"
			elif ret == 1:
				msg = f"Tema {schema}.{tname} não encontrado"
			elif ret == 2:
				msg = f"User de edição {editoruser} inexistente"
			elif ret == 3:
				msg = f"User de visualização {vieweruser} inexistente"
			elif ret == 4:
				status = "OK"

		return { "status": status, "msg": msg }

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


