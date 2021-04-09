import time

from commer import *
from cluster import *

class Controller():
	def __init__(self, listen_ip_l):
		self.commer = Commer(listen_ip_l, handle_msg)
		self._id = self.commer._id

		pid_l=[for i in range(len(listen_ip_l)) if i != self._id]
		fc_server = FlowControlServer(pid_l)
		fc_client = FlowControlClient(pid_l, self.commer)

		self.cluster = Cluster(fc_client, fc_server, handle_finished_job, max_q_local_len=20)

		self.id_job_m = {}
		# t = threading.Thread(target=self.check_for_timeouts, daemon=True)
		# t.start()

	# def check_for_timeouts(self):
	# 	while True:
	# 		for _id in self.id_job_m.keys():
	# 			job = self.id_job_m[_id]
	# 			if time.time() - job.enter_time > 10**4:
	# 				log(DEBUG, "dropping due to timeout", job=job)

	# 				del self.id_job_m[_id]
				
	# 			time.sleep(1)

	def handle_msg(self, msg):
		log(DEBUG, "handling", msg=msg)
		payload = msg['payload']
		if payload.is_job():
			self.fc_server.push(payload)
		elif payload.is_result():
			check(payload._id in self.id_job_m, "Result for no job is recved")
			self.id_job_m[payload._id].finish_time = time.time()
	
	def put(self, job):
		log(DEBUG, "recved", job=job)
		if job.src_id is None:
			job.src_id = self._id
		job.enter_time = time.time()

		if not self.cluster.put(job):
			if job.origin_id is not None: # job came from remote
				return
			
			job.origin_id = self._id
			self.id_job_m[job._id] = job
			
			p = Probe(job._id, origin_id=self._id)
			self.commer.broadcast(p)
	
	def handle_finished_job(self, job):
		log(DEBUG, "handling", job=job)
		if job.is_probe():
			probe = job
			check(probe.origin_id != self._id, "Probe should come from remote")
			msg = Msg(_id=probe._id, payload=probe, dst_id=probe.origin_id)
			self.commer.send(msg)
		elif job.is_job():
			if job.origin_id != self._id:
				msg = Msg(_id=self._id, payload=Result(_id=self._id, origin_id=self._id), dst_id=job.origin_id)
				self.commer.send(msg)
			else:
				self.id_job_m[payload._id].finish_time = time.time()

	
		
		
