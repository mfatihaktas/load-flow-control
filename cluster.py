import threading, time, random
from collections import deque

from debug_utils import *
from msg import *
from controller import *

class Cluster():
	def __init__(self, _id, fc_server, fc_client, handle_result, max_delay):
		self._id = _id
		self.fc_server = fc_server
		self.fc_client = fc_client
		self.handle_result = handle_result

		self.wait_for_ajob = threading.Condition()
		self.is_waiting_for_ajob = False
		t = threading.Thread(target=self.run, daemon=True)
		t.start()

	def put(self, job):
		log(DEBUG, "recved", job=job)

		r = False
		if job.origin_id == self._id:
			r = self.fc_client.push(job)
		else:
			r = self.fc_server.push(job)

		if self.is_waiting_for_ajob:
			with self.wait_for_ajob:
				self.wait_for_ajob.notifyAll()
				log(DEBUG, "notified")

		return r

	def update_delay_controller(self, from_id, t):
		self.fc_client.update_delay_controller(from_id, t)

	def run(self):
		while True:
			job = self.fc_server.pop()
			if job is None:
				self.is_waiting_for_ajob = True
				with self.wait_for_ajob:
					log(DEBUG, "waiting for a job")
					self.wait_for_ajob.wait()
					log(DEBUG, "a job has arrived!")
					self.is_waiting_for_ajob = False
				continue

			log(DEBUG, "will serv", job=job)
			time.sleep(job.serv_time)
			log(DEBUG, "finished serving", job=job)

			r = result_from_job(job)
			self.handle_result(r)
