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

		self.delay_controller = DelayController(_id, max_delay)
		self.q = deque()

		self.wait_for_ajob = threading.Condition()
		self.is_waiting_for_ajob = False
		t = threading.Thread(target=self.run, daemon=True)
		t.start()

	def put(self, job, src='local'):
		log(DEBUG, "recved", job=job)

		r = False
		if src == 'local':
			if self.delay_controller.put():
				self.q.append(job)
				log(DEBUG, "put into local q", job=job, len_q=len(self.q))
				r = True
			else:
				r = self.fc_client.push(job)
		elif src == 'remote':
			r = self.fc_server.push(job)

		if self.is_waiting_for_ajob:
			with self.wait_for_ajob:
				self.wait_for_ajob.notifyAll()
				log(DEBUG, "notified")

		return r

	def update_delay_controller(self, t, from_id):
		if from_id == self._id: # local
			self.delay_controller.update(t)
		else:
			self.fc_client.update_delay_controller(from_id, t)

	def next_in_line(self):
		if len(self.q) > 0:
			return self.q.popleft()
		return self.fc_server.pop()

	def run(self):
		while True:
			job = self.next_in_line()
			if job is None:
				self.is_waiting_for_ajob = True
				with self.wait_for_ajob:
					log(DEBUG, "waiting for a job")
					self.wait_for_ajob.wait()
					log(DEBUG, "a job has arrived!")
					self.is_waiting_for_ajob = False
				continue

			# waiting_time = time.time() - job.enter_time
			# if waiting_time >= job.max_waiting_time:
			# 	log(WARNING, "waiting_time= {} > max_waiting_time= {}, dropping the job".format(waiting_time, job.max_waiting_time), job=job)
			# 	continue

			log(DEBUG, "will serv", job=job)
			time.sleep(job.serv_time)
			log(DEBUG, "finished serving", job=job)

			r = result_from_job(job)
			self.handle_result(r)
