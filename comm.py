#!/usr/bin/python

import sys, socket, socketserver, getopt, threading, subprocess, json, time

from msg import *
from debug_utils import *

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
	def __init__(self, _id, server_addr, call_back):
		socketserver.TCPServer.__init__(self, server_addr, ThreadedTCPRequestHandler)
		self._id = _id
		self.call_back = call_back

	def __repr__(self):
		return "ThreadedTCPServer(id= {})".format(self._id)

MSG_LEN_HEADER_SIZE = 10

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
	def handle(self):
		while True:
			log(DEBUG, "waiting to recv msg_len_header")
			msg_len_header = self.request.recv(MSG_LEN_HEADER_SIZE)
			log(DEBUG, "recved", msg_len_header=msg_len_header)
			msg_len = int(msg_len_header)
			if msg_len == 0:
				log(DEBUG, "Recved end signal...terminating the request handler.")
				return

			msg_str = self.request.recv(msg_len)
			msg = msg_from_str(msg_str)
			# cur_thread = threading.current_thread()
			log(DEBUG, "recved", msg=msg)

			if msg.payload.size_inBs > 0:
				total_size = msg.payload.size_inBs
				log(DEBUG, 'will recv payload', total_size=total_size)
				while total_size > 0:
					to_recv_size = min(total_size, 10*1024)
					self.request.recv(to_recv_size)
					# data = self.request.recv(1)
					# recved_size = sys.getsizeof(data)
					log(DEBUG, 'recved', size=to_recv_size)
					total_size -= to_recv_size
				log(DEBUG, 'finished recving the payload', total_size=msg.payload.size_inBs)

			self.server.call_back(msg)

def get_eth0_ip():
	# search and bind to eth0 ip address
	intf_list = subprocess.getoutput("ifconfig -a | sed 's/[ \t].*//;/^$/d'").split('\n')
	intf_eth0 = None
	for intf in intf_list:
		if 'eth0' in intf:
			intf_eth0 = intf

	check(intf_eth0 is not None, "Could not find interface with eth0.")
	intf_eth0_ip = subprocess.getoutput("ip address show dev " + intf_eth0).split()
	intf_eth0_ip = intf_eth0_ip[intf_eth0_ip.index('inet') + 1].split('/')[0]
	return intf_eth0_ip

def msg_len_header(msg_size):
	msg_size_str = str(msg_size)
	return ('0' * (MSG_LEN_HEADER_SIZE - len(msg_size_str)) + msg_size_str).encode('utf-8')

class Commer():
	def __init__(self, listen_ip_l, handle_msg, listen_port=5000):
		self.listen_ip_l = listen_ip_l
		self.listen_port = listen_port

		self._id = None
		listen_ip = get_eth0_ip()
		for _id, ip in enumerate(listen_ip_l):
			if listen_ip == ip:
				self._id = _id
				break
		check(self._id is not None, "id has not been set")

		log(DEBUG, "id= {}, listen_ip= {}, listen_port= {}".format(self._id, listen_ip, listen_port))

		self.server = ThreadedTCPServer(self._id, (listen_ip_l[self._id], listen_port), handle_msg)
		self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
		self.server_thread.start()
		log(DEBUG, "server started running in thread")

		self.peer_id__socket_m = {}

	def __repr__(self):
		return "Commer(id= {}, listen_ip_l= {}, listen_port= {})".format(self._id, self.listen_ip_l, self.listen_port)

	def close(self):
		for peer_id, sock in self.peer_id__socket_m.items():
			sock.sendall(msg_len_header(0))
			log(DEBUG, "sent end signal", peer_id=peer_id)
			sock.close()
			log(DEBUG, "closed socket", peer_id=peer_id)
		self.server.shutdown()

	def connect_to(self, to_id):
		check(0 <= to_id < len(self.listen_ip_l) and to_id != self._id, "Wrong to_id= {}".format(to_id))
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect((self.listen_ip_l[to_id], self.listen_port))
		except IOError as e:
			if e.errno == errno.EPIPE: # insuffient buffer at the server side
				assert_("broken pipe err")

		log(DEBUG, "connected", _id=self._id, to_id=to_id)
		self.peer_id__socket_m[to_id] = sock

	def connect_to_peers(self):
		for peer_id, ip in enumerate(self.listen_ip_l):
			if self._id == peer_id:
				continue
			self.connect_to(peer_id)
		log(DEBUG, "done")

	def send(self, msg):
		check(msg.dst_id in self.peer_id__socket_m, "Unexpected msg.dst_id= {}".format(msg.dst_id))
		socket = self.peer_id__socket_m[msg.dst_id]

		msg.src_id = self._id

		msg_str = msg.to_str().encode('utf-8')
		msg_size = len(msg_str)
		header = msg_len_header(msg_size)
		socket.sendall(header)
		log(DEBUG, "sent header")

		socket.sendall(msg_str)
		log(DEBUG, "sent msg", msg=msg)

		# TODO: Payload is generated synthetically for now
		payload = bytearray(msg.payload.size_inBs)
		log(DEBUG, "sending payload")
		socket.sendall(payload)
		log(DEBUG, "sent payload", payload_size=msg.payload.size_inBs)

	def send_close_signal(self, peer_id):
		check(peer_id in self.peer_id__socket_m, "Unexpected peer_id= {}".format(peer_id))
		socket = self.peer_id__socket_m[peer_id]

	def broadcast(self, msg):
		for peer_id in self.peer_id__socket_m:
			msg.dst_id = peer_id
			self.send(msg)

def handle_msg(msg):
	log(INFO, "recved", msg=msg)

def test(argv):
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

	c = Commer(ip_l, handle_msg=handle_msg)

	input("Enter for connecting to peers...")
	c.connect_to_peers()

	input("Enter for broadcasting to peers...")
	msg = Msg(_id=0, payload=Job(_id=0, serv_time=1, size_inBs=1))
	c.broadcast(msg)

if __name__ == '__main__':
	test(sys.argv[1:])
