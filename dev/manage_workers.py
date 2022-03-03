
import psutil
import sys

from os import scandir, remove
from os.path import abspath, dirname, splitext, join as path_join
from subprocess import Popen

from common import DEFAULT_WORKERS, WORKER_PIDFILE_PREFIX


def find_pids_in_files():

	found_pids = {}
	wd_path = path_join(dirname(abspath(__file__)), "workers_data")
	for de in scandir(wd_path):
		if de.is_file():
			fname, ext = splitext(de.name)
			if ext == ".pid":
				prefix, num = fname.split("_")
				if prefix == WORKER_PIDFILE_PREFIX:
					wnum = int(num)
					with open(de.path, "r") as fo:
						content = fo.read()
						found_pids[wnum] = {
							"pid": int(content.strip()),
							"path": de.path
						}

	found_wnums = [n for n in found_pids.keys()]
	for wnumkey in found_wnums:
		if not psutil.pid_exists(found_pids[wnumkey]["pid"]):
			remove(found_pids[wnumkey]["path"])
			del found_pids[wnumkey]
		else:
			p = psutil.Process(found_pids[wnumkey]["pid"])
			if not 'background_worker.py' in p.cmdline():
				remove(found_pids[wnumkey]["path"])
				del found_pids[wnumkey]

	return found_pids

def ensure_enough_workers_running(expected_process_count=0):

	found_pids = find_pids_in_files()

	if expected_process_count < 1:
		needed_count = DEFAULT_WORKERS
	else:
		needed_count = expected_process_count

	ordered_wnums = sorted([n for n in found_pids.keys()])
	bkgrwrkr_path = path_join(dirname(abspath(__file__)), "background_worker.py")
	wd_pid_path = path_join(dirname(abspath(__file__)), "workers_data")


	if len(found_pids.keys()) > needed_count:	

		excess_wnums =  ordered_wnums[needed_count:]
		for ewn in excess_wnums:
			p = psutil.Process(found_pids[ewn]["pid"])
			p.terminate()

	elif len(ordered_wnums) < needed_count:

		if len(ordered_wnums) == 0:
			wn_seed = 0
		else:
			wn_seed = max(ordered_wnums)

		newprocs_count = needed_count - len(found_pids.keys())
		for n in range(newprocs_count):
			wn = wn_seed + n + 1
			popen_list = [sys.executable, bkgrwrkr_path, str(wn)]
			w_pid_path = path_join(wd_pid_path, f"worker_{wn}.pid")
			p = Popen(popen_list)
			with open(w_pid_path, "w") as fo:
				fo.write(str(p.pid))


def kill_all_workers():

	found_pids = find_pids_in_files()
	found_wnums = [n for n in found_pids.keys()]

	for wnumkey in found_wnums:

		if psutil.pid_exists(found_pids[wnumkey]["pid"]):
			p = psutil.Process(found_pids[wnumkey]["pid"])
			if 'background_worker.py' in p.cmdline():
				p.terminate()

		remove(found_pids[wnumkey]["path"])
		del found_pids[wnumkey]		

