
import asyncio
import asyncpg
import logging
import json

from base64 import b64decode
from copy import copy

from os.path import exists

def gen_wc_internalitem(p_idx, p_extitem):
	tmpl = "{0} {1} ${2}"
	ret = ""
	op = ""
	if p_extitem[1].lower() == "eq":
		op = "="
	elif p_extitem[1].lower() == "ne":
		op = "!="
	elif p_extitem[1].lower() == "ge":
		op = ">="
	elif p_extitem[1].lower() == "le":
		op = "<="
	elif p_extitem[1].lower() == "gt":
		op = ">"
	elif p_extitem[1].lower() == "lt":
		op = "<"
	elif p_extitem[1].lower() in ("ilike", "like"):
		op = p_extitem[1]
		
	ret = tmpl.format(p_extitem[0], op, p_idx+1)
	
	return ret
	
def gen_wclause(p_wcitems):
	ret = ""
	internal_items = []
	for ii, item in enumerate(p_wcitems):
		if ii == 0:
			internal_items.append(gen_wc_internalitem(ii, item))
		else:
			if len(item) > 2:
				sep = item[2]
			else:
				sep = "AND"
			internal_items.append(sep)
			internal_items.append(gen_wc_internalitem(ii, item))
			
	if len(internal_items) > 0:
		ret = "WHERE " + ' '.join(internal_items)
	
	return ret

def sql_build_sel(p_whereclause_list, p_base_fields, p_key_fields, p_from_objects, p_skip, p_limit):

	if len(p_key_fields) > 0 and p_skip > 0:
		fields = "{}, row_number() over (order by {}) as _rn".format(p_base_fields, p_key_fields)
	else:
		fields = p_base_fields
		
	aliases = "abcdef"
	
	if p_skip > 0:
		sql_buffer = ["with _ps as (", "select", fields]
	else:
		sql_buffer = ["select", fields]
		
	from_lines = ["from"]
	
	for i, fo in enumerate(p_from_objects):
		if i == 0:
			from_lines.append(f"{fo} {aliases[i]}")
		else:
			l = len(fo) 
			assert l >= 2 and l <= 3, fo

			if len(fo) == 3:
				join_type, table_name, join_fields = fo
			elif len(fo) == 2:
				join_type, table_name = fo
				
			from_lines.append(f"{join_type} join")
			from_lines.append(f"{table_name} {aliases[i]}")
			if len(fo) == 3:
				if isinstance(join_fields, str):
					from_lines.append(f"using ({join_fields})")
				elif len(join_fields) == 1:
					from_lines.append(f"using ({join_fields[0]})")
				else:
					from_lines.append("on")
					for fld_a, fld_b in join_fields:
						from_lines.append(f"{aliases[i-1]}.{fld_a} = {aliases[i]}{fld_b}")
						
	sql_buffer.append(" ".join(from_lines))					
	
	if len(p_whereclause_list) > 0:
		sql_buffer.append(gen_wclause(p_whereclause_list))

	if p_skip == 0 and len(p_key_fields) > 0 :
		sql_buffer.append("order by {}".format(p_key_fields))
	
	idx = len(p_whereclause_list)
	if p_skip > 0:
		idx += 1
		sql_buffer.extend([
			")",
			"select * from _ps",
			"where _rn > ${}".format(idx)
			])
	
	if p_limit > 0:
		idx += 1
		sql_buffer.append("limit ${}".format(idx))
		
	return " ".join(sql_buffer)

async def set_connection_codecs(conn):
	await conn.set_type_codec(
				'json',
				encoder=json.dumps,
				decoder=json.loads,
				schema='pg_catalog'
			)	
	
class DBPool(object):
	
	def __init__(self, p_dict_or_path):
		
		cfg = None
		if isinstance(p_dict_or_path, str):
			if exists(p_dict_or_path):
				with open(p_dict_or_path) as cfgfl:
					import json
					cfg =  json.load(cfgfl)	
			else:
				raise ConnectionError(f"DBPool: missing config: {p_dict_or_path}")
		elif not isinstance(p_dict_or_path, dict):
			raise ConnectionError("DBPool: invalid config")
		else:
			cfg = p_dict_or_path
			
		assert not cfg is None, f"path:{p_dict_or_path}"
		assert isinstance(cfg, dict)

		if "password" not in cfg.keys():
			raise ConnectionError("DBPool: no password")

		try:
			passw = b64decode(cfg["password"]).decode("utf-8") 
		except AttributeError:
			passw = str(b64decode(cfg["password"]))

		self.cfgdict = copy(cfg)
		self.cfgdict["password"] = passw
		self.cfgdict["init"] = set_connection_codecs
		
		self.pool = None

		
	def isOpened(self):
		return not self.pool is None
		
	async def test(self):

		logger = logging.getLogger('main')
		ret = False
		if self.isOpened():
			try:
				async with self.pool.acquire() as conn:
					result = await conn.fetchval("SELECT 1")
				if result == 1:
					ret = True
			except:
				logger.exception("Erro em test")
		return ret
	
	async def openup(self):	

		cfgdict = {}
		for cfgkey in self.cfgdict.keys():
			if cfgkey == 'application_name':
				cfgdict["server_settings"] = {"application_name": self.cfgdict[cfgkey] }
			else:
				cfgdict[cfgkey] = self.cfgdict[cfgkey]

		self.pool = await asyncpg.create_pool(**cfgdict)
		ret = await self.test()
		return ret
		
	async def teardown(self):	
		if self.isOpened():	
			await self.pool.close()

	def sqlalchemy_connstr(self):
		return f"postgresql://{self.cfgdict['user']}:{self.cfgdict['password']}@{self.cfgdict['host']}/{self.cfgdict['database']}"
		
					
