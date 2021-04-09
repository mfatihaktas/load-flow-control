import time

from comm import *
from cluster import *
from flow_control import *

class EdgeCloud():
	def __init__(self, listen_ip_l):
		self.commer = Commer(listen_ip_l, self.handle_msg)
		self._id = self.commer._id

		input("Enter for connecting to peers...\n")
		# log(DEBUG, "will connect to peers in 3 sec")
		# sleep(3)
		self.commer.connect_to_peers()
		
		pid_l = [i for i in range(len(listen_ip_l)) if i != self._id]
		fc_server = FlowControlServer(pid_l)
		fc_client = FlowControlClient(pid_l, self.commer)
		self.cluster = Cluster(fc_server, fc_client, self.handle_result, max_q_local_len=20)

		self.job_info_m = {}

	def put(self, job):
		job.origin_id = self._id
		self.job_info_m[job] = {'enter_time': time.time()}
		self.cluster.put(job, typ='local')

	def handle_msg(self, msg):
		log(DEBUG, "handling", msg=msg)
		payload = msg['payload']
		if payload.is_job():
			self.cluster.put(payload)
		elif payload.is_result():
			self.reg_result(result)

	def handle_result(self, result):
		log(DEBUG, "handling", result=result)
		if result._id == self._id:
			self.reg_result(result)
		else:
			msg = Msg(result._id, payload=result, dst_id=result.origin_id)
			self.commer.send(msg)
			log(DEBUG, "sent", result=result)

	def reg_result(self, result):
		check(result in self.job_info_m, "Result for no job is recved", result=result)
		self.job_info_m[result]['finish_time'] = time.time()
		log(DEBUG, "reged", result=result)

def run(argv):
	ip_l = None
	try:
		opts, args = getopt.getopt(argv, '', ['ip_l='])
	except getopt.GetoptError:
		assert_("Wrong args;", opts=opts, args=args)
	
	for opt, arg in opts:
		if opt == '--ip_l':
			ip_l = arg
		else:
			assert_("Unexpected opt= {}, arg= {}".format(opt, arg))

	check(ip_l is not None, "ip_l is not set.")
	ip_l = [ip for ip in ip_l.split(',')]

	ec = EdgeCloud(ip_l)
	
	input("Enter for putting job...\n")
	ec.put(Job(_id=0, serv_time=1, size_inbs=1))

	input("Enter to print job_info_m...\n")
	log(DEBUG, "", job_info_m=ec.job_info_m)
	
	input("Enter to finish...\n")

if __name__ == '__main__':
	run(sys.argv[1:])