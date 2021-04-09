import inspect, pprint, logging

# #################################  Log  ################################# #
DEBUG = 0
INFO = 1
WARNING = 2
ERROR = 3
CRITICAL = 4

# FORMAT = '[%(asctime)s - %(funcName)10s()] %(msg)s'
# FORMAT = '[%(asctime)s - %(func_name)6s()] %(msg)s'
# FORMAT = '[%(filename)s:%(lineno)d] %(func_name):: %(msg)s'
FORMAT = '%(func_name)s:: %(msg)s'

logging.basicConfig(format=FORMAT, level=logging.DEBUG) # filename='c.log'

level_log_m = {INFO: logging.info, DEBUG: logging.debug, WARNING: logging.warning, ERROR: logging.error, CRITICAL: logging.critical}

def log(level: int, _msg_: str, **kwargs):
	try:
		func_name = inspect.stack()[1][3]
	except IndexError:
		func_name = ''
	
	level_log_m[level]("{}\n{}".format(_msg_, pstr(**kwargs)), extra={'func_name': func_name})

# Always log
def alog(level: int, _msg_: str, **kwargs):
	try:
		func_name = inspect.stack()[1][3]
	except IndexError:
		func_name = ''
	
	logging.critical("{}\n{}".format(_msg_, pstr(**kwargs)), extra={'func_name': func_name})

def pstr(**kwargs):
	s = ''
	for k, v in kwargs.items():
		s += "  {}: {}\n".format(k, pprint.pformat(v))
	return s

# ###############################  Assert  ############################### #
def check(condition: bool, _msg_: str, **kwargs):
	if not condition:
		logging.error("{}\n{}".format(_msg_, pstr(**kwargs)))
		raise AssertionError()

def assert_(_msg_: str, **kwargs):
	logging.error("{}\n{}".format(_msg_, pstr(**kwargs)))
	raise AssertionError()
