import threading

from debug_utils import *
from rvs import *

class JobGen():
	def __init__(self, rate, self.serv_time_rv, self.size_inbs_rv):
		self.rate = rate

		self.num_jobs_sent = 0
		t = threading.Thread(target=self.run, daemon=True)
		t.start()

	def run(self):
		while 1:
			inter_ar_time = random.expovariate(self.ar)
			log(DEBUG, "sleeping ...", inter_ar_time=inter_ar_time)
			sleep(inter_ar_time)

			self.num_jobs_sent += 1
			self.out.put(
				Job(_id = self.num_jobs_sent,
						serv_time = self.serv_time_rv.sample(),
						size_inbs = self.size_inbs_rv.sample()))
