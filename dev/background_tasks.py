
import logging

from time import mktime
from os.path import join as path_join #, getmtime
#from datetime import datetime as dt
from common import SCHEMA_CARTOGRAFIA, getDXFOutPath
from background_worker import AbstractBackgroundTask
from uuid import uuid4


class GenDXF(AbstractBackgroundTask):

	def __init__(self, p_redis_url:str, p_thisworkermsg_key_patt: str, p_worker_num: int) -> None:
		super().__init__("Gerar DXF", SCHEMA_CARTOGRAFIA, p_redis_url, p_thisworkermsg_key_patt, p_worker_num)

	async def dorun(self, p_payload):
		
		await super().dorun(p_payload)

		logger = logging.getLogger('background_worker')
		em_erro = False
		table_name = "import_payshop"

		if not await self.testdb():			
			return
		else:
			try:
				quatro_cantos = p_payload["args"]["quatro_cantos"]
				tipo_cart = p_payload["args"]["tipo_cart"]

				filename = f"{uuid4()}.dxf"

				await self.newdbtask("GEN_DXF")
				await self.inittask(f"Inicio de geração ficheiro DXF {filename}")			
				dxfoutdir = getDXFOutPath()
				
				fullpath = path_join(dxfoutdir, filename)

				logger.info(f".... gerar {fullpath} com args {p_payload['args']}")


				# ogr2ogr

				await self.endtask("Final de de geração ficheiro DXF", inerror=False)

			except Exception as e:
				em_erro = True
				logger.exception(f"BackgroundWorker {self.workernum}, excecao em '{self.name}'")
				await self.endtask(f"Quebra na geração ficheiro DXF {str(e)}", inerror=em_erro)

			finally:
				await self.finishdbtask(em_erro)








