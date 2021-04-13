import time

from comm import *
from cluster import *
from flow_control import *
from jobgen import *
from plot_utils import *

class EdgeCloud():
	def __init__(self, listen_ip_l, max_delay, flow_win_size):
		self.max_delay = max_delay
		self.commer = Commer(listen_ip_l, self.handle_msg)
		self._id = self.commer._id

		input("Enter for connecting to peers...\n")
		# log(DEBUG, "will connect to peers in 3 sec")
		# sleep(3)
		self.commer.connect_to_peers()

		pid_l = [i for i in range(len(listen_ip_l)) if i != self._id]
		fc_server = FlowControlServer(pid_l)
		self.fc_client = FlowControlClient(pid_l, self.commer, flow_win_size)
		self.cluster = Cluster(self._id, fc_server, self.fc_client, self.handle_result, max_delay)

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
			self.reg_result(payload, msg.src_id)

	def handle_result(self, result):
		log(DEBUG, "handling", result=result)
		if result.origin_id == self._id:
			self.reg_result(result, self._id)
		else:
			msg = Msg(result._id, payload=result, dst_id=result.origin_id)
			self.commer.send(msg)
			log(DEBUG, "sent", result=result)

	def reg_result(self, result, from_id):
		check(result in self.job_info_m, "Result for no job is recved", result=result, from_id=from_id)
		info = self.job_info_m[result]
		t = time.time() - info['enter_time']
		if t < 0:
			log(WARNING, "Negative turnaround time", result=result, t=t)
			return

		info.update(
			{
				'fate': 'finished',
				'from_id': from_id,
				'T': 1000*t
			})

		self.cluster.update_delay_controller(t, from_id)

		log(DEBUG, "reged", result=result)

	def summarize_job_info(self):
		num_dropped = 0
		T_local_l, T_remote_l = [], []
		for job, info in self.job_info_m.items():
			if 'fate' not in info:
				continue

			fate = info['fate']
			if fate == 'dropped':
				num_dropped += 1
			elif fate == 'finished':
				from_id = info['from_id']
				T = info['T']
				if self._id == from_id:
					T_local_l.append(T)
				else:
					T_remote_l.append(T)

		ax = plot.gca()
		add_cdf(T_local_l, ax, 'Local', next(nice_color), drawline_x_l=[1000*self.max_delay])
		add_cdf(T_remote_l, ax, 'Remote', next(nice_color))

		fontsize = 14
		plot.ylabel('CDF', fontsize=fontsize)
		plot.xlabel('Time (msec)', fontsize=fontsize)

		num_total = len(T_local_l) + len(T_remote_l) + num_dropped
		f_dropped = round(num_dropped / num_total, 2)
		f_remote = round(len(T_remote_l) / num_total, 2)
		log(DEBUG, "", f_dropped=f_dropped, f_remote=f_remote)
		plot.title('f_dropped= {}, f_remote= {}'.format(f_dropped, f_remote), fontsize=fontsize)
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

	ec = EdgeCloud(ip_l, max_delay=0.07, flow_win_size=1)
	log_to_file('e{}.log'.format(ec._id))

	# input("Enter for putting job...\n")
	# ec.put(Job(_id=0, serv_time=1, size_inbs=1))
	input("Enter for starting jobgen...\n")
	# jg = JobGen(inter_ar_time_rv=DiscreteRV(p_l=[1], v_l=[0.5]),
	# 						serv_time_rv=Exp(1, D=1),
	# 						size_inBs_rv=DiscreteRV(p_l=[1], v_l=[1]),
	# 						out=ec,
	# 						num_jobs_to_send=1000)

	avg_serv_time = 0.01
	mu = float(1/avg_serv_time)
	ar = 0.9*mu if ec._id == 0 else 0.2*mu
	jg = JobGen(inter_ar_time_rv=Exp(ar),
							serv_time_rv=DiscreteRV(p_l=[1], v_l=[avg_serv_time*1000], norm_factor=1000), # Exp(mu),
							size_inBs_rv=DiscreteRV(p_l=[1], v_l=[1]),
							out=ec,
							num_jobs_to_send=2000)

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
