from debug_utils import *

class DelayController():
	def __init__(self, _id, max_delay):
		self._id = _id
		self.max_delay = max_delay

		self.q_len_limit = 2
		self.q_len = 0
		self.q_len_max = 2
		self.avg_delay = 0
		self.a = 0.9

	def update(self, t): # t: turnaround_time
		self.q_len = max(0, self.q_len - 1)

		self.avg_delay = (1 - self.a)*self.avg_delay + self.a*t
		if self.avg_delay > 0.8*self.max_delay:
			# self.q_len_limit = max(1, self.q_len_limit*1/2)
			self.q_len_limit = int(self.q_len_limit*1/2)
			log(WARNING, "reduced q_len_limit; id= {}".format(self._id))
		else:
			if self.q_len_limit < 2*self.q_len_max:
				self.q_len_limit += 1/self.q_len_limit if self.q_len_limit >= 1 else 1
				log(WARNING, "inced q_len_limit; id= {}".format(self._id))
		log(DEBUG, "id= {}".format(self._id), avg_delay=self.avg_delay, max_delay=self.max_delay, q_len_limit=self.q_len_limit, q_len=self.q_len)

	def put(self):
		if self.q_len <= self.q_len_limit:
			self.q_len += 1
			self.q_len_max = max(self.q_len_max, self.q_len)
			return True
		else:
			return False
