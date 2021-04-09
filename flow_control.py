#!/usr/bin/python

from collections import deque
from comm import *

# pid : peer_id

class FlowControlServer():
	def __init__(self, pid_l):
		self.pid__q_m = {pid: deque() for pid in pid_l}
		self.num_peers = len(pid_l)
		self.next_pid_pop_from_q = deque(pid_l)

	def __repr__(self):
		return "FlowControlServer(id= {})".format(self._id)

	def push(self, job):
		check(job.src_id in self.pid__q_m, "Job is from an unknown source", job=job)
		
		self.pid__q_m[job.src_id].append(job)
		log(DEBUG, "pushed", job=job)
	
	def pop(self):
		for _ in range(self.num_peers):
			q = self.pid__q_m[self.next_pid_pop_from_q[0]]
			self.next_pid_pop_from_q.rotate(-1)
			if len(q) > 0:
				return q.popleft()
		
		return None

class FlowControlClient():
	def __init__(self, pid_l, commer, initial_window_size=1):
		self.pid_l = pid_l
		self.commer = commer

		self.pid_wsize_m = {pid: initial_window_size for pid in pid_l}
		self.num_peers = len(self.pid_l)
		self.next_pid_push_to_q = deque(self.pid_l)
		
		self.num_jobs_pushed = 0

	def __repr__(self):
		return "FlowControlClient(pid_l= {})".format(self.pid_l)

	def push(self, job):
		log(DEBUG, "recved", job=job)

		for _ in range(self.num_peers):
			pid = self.next_pid_push_to_q[0]
			self.next_pid_push_to_q.rotate(-1)
			if self.pid_wsize_m[pid] > 0:
				self.commer.send(msg = Msg(_id=self.num_jobs_pushed, payload=job, dst_id=pid))
				self.num_jobs_pushed += 1
				log(DEBUG, "sent to pid= {}".format(pid), job=job)
				self.pid_wsize_m[pid] -= 1
				return
		log(DEBUG, "dropping", job=job)

	def handle_result(result):
		pid = result.origin_id
		self.pid_wsize_m[pid] += 1
		log(DEBUG, "inced wsize", pid=pid, wsize=self.pid_wsize_m[pid])
