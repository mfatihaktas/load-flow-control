import threading, time

from debug_utils import *
from rvs import *
from msg import *

class JobGen():
	def __init__(self, inter_ar_time_rv, serv_time_rv, size_inBs_rv, out, num_jobs_to_send):
		self.inter_ar_time_rv = inter_ar_time_rv
		self.serv_time_rv = serv_time_rv
		self.size_inBs_rv = size_inBs_rv
		self.out = out
		self.num_jobs_to_send = num_jobs_to_send

		self.num_jobs_sent = 0
		t = threading.Thread(target=self.run, daemon=True)
		t.start()

	def run(self):
		while 1:
			inter_ar_time = self.inter_ar_time_rv.sample() # random.expovariate(self.rate)
			log(DEBUG, "sleeping ...", inter_ar_time=inter_ar_time)
			time.sleep(inter_ar_time / 1000)

			self.num_jobs_sent += 1
			self.out.put(
				Job(_id = self.num_jobs_sent,
						serv_time = self.serv_time_rv.sample(),
						size_inBs = self.size_inBs_rv.sample()))

			if self.num_jobs_sent == self.num_jobs_to_send:
				return
