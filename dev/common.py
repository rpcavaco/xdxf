
from os import getcwd, makedirs
from os.path import join as path_join, exists, abspath, dirname

REDIS_BASE_URL = "redis://:XarmZombSevreGter1X!inoDeaG6L!27Dv@localhost:6379"
REDIS_WEBAPP_MSG_KEY = "xdxf_webapp_messages"
REDIS_ALLBGWRKRS_MSG_KEY = "xdxf_allbgworkers_messages"
REDIS_BGWRKR_MSG_KEY_PATT = "xdxf_bgworker{:02d}_messages"

DEFAULT_WORKERS = 1
WORKER_PIDFILE_PREFIX = "worker"

TAILLOGS_LINES = 60

def getRedisMonitorURL():
	database_num = 0
	return database_num, f"{REDIS_BASE_URL}/{database_num}"

def getRedisWorkerURL():
	database_num = 0
	return database_num, f"{REDIS_BASE_URL}/{database_num}"	


# def getXXXX_CSVDir():
# 	ret = path_join(dirname(abspath(__file__)), "stcp_csv")
# 	if not exists(ret):
# 		makedirs(ret)
# 	return ret


