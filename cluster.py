import threading, time, random
from collections import deque

from debug_utils import *
from msg import *

class Cluster():
	def __init__(self, fc_server, fc_client, handle_result, max_q_local_len=20):
		self.fc_server = fc_server
		self.fc_client = fc_client
		self.handle_result = handle_result
		self.max_q_local_len = max_q_local_len
		
		self.q = deque()

		self.wait_for_ajob = threading.Condition()
		self.is_waiting_for_ajob = False
		t = threading.Thread(target=self.run, daemon=True)
		t.start()

	def put(self, job, typ='local'):
		log(DEBUG, "recved", job=job)

		if typ == 'local':
			if len(self.q) < self.max_q_local_len:
				self.q.append(job)
				log(DEBUG, "put into local q", job=job)
			else:
				self.fc_client.push(job)
		elif typ == 'remote':
			self.fc_server.push(job)

		if self.is_waiting_for_ajob:
			with self.wait_for_ajob:
				self.wait_for_ajob.notifyAll()
				log(DEBUG, "notified")
	
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
			self.handle_result(result_from_job(job))
