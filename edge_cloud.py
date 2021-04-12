import time

from comm import *
from cluster import *
from flow_control import *
from jobgen import *
from plot_utils import *

class EdgeCloud():
	def __init__(self, listen_ip_l, max_len_local_q, flow_win_size):
		self.commer = Commer(listen_ip_l, self.handle_msg)
		self._id = self.commer._id

		input("Enter for connecting to peers...\n")
		# log(DEBUG, "will connect to peers in 3 sec")
		# sleep(3)
		self.commer.connect_to_peers()
		
		pid_l = [i for i in range(len(listen_ip_l)) if i != self._id]
		fc_server = FlowControlServer(pid_l)
		self.fc_client = FlowControlClient(pid_l, self.commer, flow_win_size)
		self.cluster = Cluster(fc_server, self.fc_client, self.handle_result, max_len_local_q)

		self.job_info_m = {}

	def close(self):
		self.commer.close()
	
	def put(self, job):
		job.origin_id = self._id
		self.job_info_m[job] = {'enter_time': time.time()}
		if self.cluster.put(job, src='local') == False:
			self.job_info_m[job] = {'fate': 'dropped'}

	def handle_msg(self, msg):
		log(DEBUG, "handling", msg=msg)
		payload = msg.payload
		if payload.is_job():
			self.cluster.put(payload, src='remote')
		elif payload.is_result():
			self.fc_client.handle_result(msg.src_id, payload)
			self.reg_result(payload, where='remote')

	def handle_result(self, result):
		log(DEBUG, "handling", result=result)
		if result.origin_id == self._id:
			self.reg_result(result, where='local')
		else:
			msg = Msg(result._id, payload=result, dst_id=result.origin_id)
			self.commer.send(msg)
			log(DEBUG, "sent", result=result)

	def reg_result(self, result, where):
		check(result in self.job_info_m, "Result for no job is recved", result=result, where=where)
		info = self.job_info_m[result]
		info.update(
			{
				'fate': 'finished',
				'where': where,
				'T': time.time() - info['enter_time']
			})
		log(DEBUG, "reged", result=result)

	def summarize_job_info(self):
		total_num = 0
		num_dropped = 0
		T_local_l, T_remote_l = [], []
		for job, info in self.job_info_m.items():
			if 'fate' not in info:
				continue

			total_num += 1
			fate = info['fate']
			if fate == 'dropped':
				num_dropped += 1
			elif fate == 'finished':
				where = info['where']
				T = info['T']
				if where == 'local':
					T_local_l.append(T)
				elif where == 'remote':
					T_remote_l.append(T)

		ax = plot.gca()
		add_cdf(T_local_l, ax, 'Local', next(nice_color))
		add_cdf(T_remote_l, ax, 'Remote', next(nice_color))

		fontsize = 14
		plot.ylabel('CDF', fontsize=fontsize)
		plot.xlabel('Time', fontsize=fontsize)
		
		drop_rate = num_dropped / total_num
		log(DEBUG, "", drop_rate=drop_rate)
		plot.title('Max Q len= {}, Drop rate= {}'.format(self.cluster.max_len_local_q, drop_rate), fontsize=fontsize)
		plot.legend(fontsize=fontsize)
		plot.gcf().set_size_inches(6, 4)
		plot.savefig("plot_cdf_T_id{}.png".format(self._id), bbox_inches='tight')
		plot.gcf().clear()

def parse_argv(argv):
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
	return [ip for ip in ip_l.split(',')]

def test(argv):
	ip_l = parse_argv(argv)

	ec = EdgeCloud(ip_l, max_len_local_q=10, flow_win_size=1)
	log_to_file('e{}.log'.format(ec._id))
	
	# input("Enter for putting job...\n")
	# ec.put(Job(_id=0, serv_time=1, size_inbs=1))
	input("Enter for starting jobgen...\n")
	# jg = JobGen(inter_ar_time_rv=DiscreteRV(p_l=[1], v_l=[0.5]),
	# 						serv_time_rv=Exp(1, D=1),
	# 						size_inBs_rv=DiscreteRV(p_l=[1], v_l=[1]),
	# 						out=ec,
	# 						num_jobs_to_send=1000)

	mu = 1/20
	ar = 0.9*mu if ec._id == 0 else 0.2*mu
	jg = JobGen(inter_ar_time_rv=Exp(ar),
							serv_time_rv=Exp(mu),
							size_inBs_rv=DiscreteRV(p_l=[1], v_l=[1]),
							out=ec,
							num_jobs_to_send=1000)

	input("Enter to print job_info_m...\n")
	# log(DEBUG, "", job_info_m=ec.job_info_m)
	ec.summarize_job_info()
	
	input("Enter to finish...\n")
	ec.close()
	sys.exit()

def run(argv):
	pass

if __name__ == '__main__':
	test(sys.argv[1:])
