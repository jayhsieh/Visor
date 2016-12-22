# Fake log files generator
#
# Usage:
#	python 3.4 fake_log_gen [fake_logfile]
#
# Format:
#
#  Error log:
#	[Wed Oct 11 14:32:52 2000] [error] [client 127.0.0.1] client denied by server configuration: /export/home/live/ap/htdocs/test


import random
import json
import logging
import argparse
import asyncio
from asyncio import coroutine


class fake_log_gen():
	
	def __init__(self, log, config, log_type):
		self.log = log
		self.log_type = log_type
		# Dict that contains config info
		self.config = config

	def run(self): 
		loop = asyncio.get_event_loop()
		# The event loop
		if self.log_type == 'error':
			loop.run_until_complete(
				asyncio.wait([
					self.heartbeat_lines(),
					self.warn_lines(),
					self.error_lines()]
				)
			)
			loop.close()
		else:
			loop.run_until_complete(
				asyncio.wait([
					self.heartbeat_lines()]
				)
			)
			loop.close()


	@coroutine
	def heartbeat_lines(self):
		while True:
			self.log.info("[-] [-] " + self.config["heartbeat"]["message"])
			yield from asyncio.sleep(int(self.config["heartbeat"]["interval"]))
	
	@coroutine
	def warn_lines(self):

		warn_min = self.config["warn"]["interval"]["min"]
		warn_max = self.config["warn"]["interval"]["max"]
		warnings = self.config["warn"]["message"]

		while True:
			pid = ''.join(str(random.randint(0, 9)) for i in range(5))
			tid = ''.join(str(random.randint(0, 9)) for i in range(10))
			ip = '.'.join(str(random.randint(0, 255)) for i in range(4))
			self.log.warning("[pid %s:tid %s] [client %s] %s", pid, tid, ip, warnings[random.randrange(len(warnings))])
			yield from asyncio.sleep(random.uniform(warn_min, warn_max))

	@coroutine
	def error_lines(self):
	
		error_min = self.config["error"]["interval"]["min"]
		error_max = self.config["error"]["interval"]["max"]
		errors = self.config["error"]["message"]

		while True:
			pid = ''.join(str(random.randint(0, 9)) for i in range(5))
			tid = ''.join(str(random.randint(0, 9)) for i in range(10))
			ip = '.'.join(str(random.randint(0, 255)) for i in range(4))
			self.log.error("[pid %s:tid %s] [client %s] %s", pid, tid, ip, errors[random.randrange(len(errors))])
			yield from asyncio.sleep(random.uniform(error_min, error_max))

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("fake_logfile", help="fake logfile")
	parser.add_argument("form", help="log format")
	args = parser.parse_args()

	# Identify the log format
	log_type = args.form
	if log_type not in ['error', 'access']:
		print('Argument error.')

	# Instantiate the logger
	log = logging.getLogger(None)
	# Set the level
	logging.basicConfig(level=logging.INFO)
	# Instantiate a file Handler
	out = logging.FileHandler(args.fake_logfile)
	# Instantiate a Formatter
	# Format the time string
	log_format = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%a %b %d %H:%M:%S %Y")
	# Set the Formatter for this Handler to form
	out.setFormatter(log_format)
	# Add the file Handler 'out' to the logger'log'
	log.addHandler(out)

	#Test Logging
	'''log.info("INFO!")
	log.error("Error!")
	'''

	# Load the configure json file to a dict
	with open("../config/fake_log_gen.json") as config_file:
		config = json.load(config_file)

	# Instantiate a fake log generator
	log_gen = fake_log_gen(log, config, log_type)
	log_gen.run()



if __name__ == "__main__":
	main()


