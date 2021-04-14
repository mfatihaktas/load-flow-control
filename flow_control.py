#!/usr/bin/python

from collections import deque
from comm import *
from controller import *

# pid : peer_id

class FlowControlServer():
	def __init__(self, pid_l):
		self.pid__q_m = {pid: deque() for pid in pid_l}
		self.num_peers = len(pid_l)
		self.next_pid_pop_from_q = deque(pid_l)

	def __repr__(self):
		return "FlowControlServer(id= {})".format(self._id)

	def push(self, job):
		check(job.origin_id in self.pid__q_m, "Job is from an unknown source", job=job)

		self.pid__q_m[job.origin_id].append(job)
		log(DEBUG, "pushed", job=job)
		return True

	def pop(self):
		for _ in range(self.num_peers):
			q = self.pid__q_m[self.next_pid_pop_from_q[0]]
			self.next_pid_pop_from_q.rotate(-1)
			if len(q) > 0:
				return q.popleft()

		return None

class FlowControlClient():
	def __init__(self, _id, pid_l, fc_server, commer, max_delay):
		self._id = _id
		self.pid_l = pid_l
		self.fc_server = fc_server
		self.commer = commer

		self.pid_delay_controller_m = {pid: DelayController(pid, max_delay) for pid in pid_l}
		self.num_peers = len(self.pid_l)
		self.next_pid_push_to_q = deque(self.pid_l)

		self.num_jobs_pushed = 0

	def __repr__(self):
		return "FlowControlClient(id= {}, pid_l= {})".format(self._id, self.pid_l)

	def push(self, job):
		log(DEBUG, "recved", job=job)

		for _ in range(self.num_peers):
			pid = self.next_pid_push_to_q[0]
			self.next_pid_push_to_q.rotate(-1)
			log(DEBUG, "***", pid=pid)
			if pid == self._id:
				self.fc_server.push(job)
				return True
			else:
				if self.pid_delay_controller_m[pid].put():
					self.commer.send(msg = Msg(_id=self.num_jobs_pushed, payload=job, dst_id=pid))
					self.num_jobs_pushed += 1
					log(DEBUG, "sent to pid= {}".format(pid), job=job)
					return True
		log(DEBUG, "dropping", job=job)
		return False

	def update_delay_controller(self, peer_id, t):
		self.pid_delay_controller_m[peer_id].update(t)
		log(DEBUG, "done", peer_id=peer_id, t=t)
