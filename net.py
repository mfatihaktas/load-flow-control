#!/usr/bin/python

from mininet.cli import CLI
from mininet.log import setLogLevel, info #, error
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import Controller
from mininet.link import TCLink

from debug_utils import *

class MyTopo(Topo):
	def __init__(self):
		Topo.__init__(self)

		e1 = self.addHost('e1')
		e2 = self.addHost('e2')
		s1 = self.addSwitch('s1')

		link_opts = dict(bw=1, delay='5ms', loss=0, max_queue_size=1000, use_htb=True)
		# wide_linkopts = dict(bw=1, delay='50ms', loss=0, max_queue_size=1000, use_htb=True)
		# dsa_linkopts = dict(bw=1000, delay='1ms', loss=0, max_queue_size=10000, use_htb=True)
		self.addLink(e1, s1, **link_opts)
		self.addLink(s1, e2, **link_opts)

def run_tnodes(hosts):
	#Start
	"""
	for host in hosts:
		host.cmdPrint('pwd')
		host.sendCmd('./run.sh %s &' % host.name)
	"""
	popens = {}
	for host in hosts:
		host.cmdPrint('pwd')
		popens[host] = host.popen('./run.sh %s' % host.name)
	"""
	#Monitor them and print output
	for host,popen in popens.items():
		out, err = popen.communicate()
		print '%s; out=%s, err=%s' % (host.name,out,err)
	"""
	"""
	for host, line in pmonitor( popens ):
	  if host:
      print "<%s>: %s" % ( host.name, line.strip() )
	"""
	log(INFO, "done.")

if __name__ == '__main__':
	setLogLevel('info')
	info('# Creating network\n')
	net = Mininet(topo=MyTopo(), link=TCLink, controller=Controller)
	# c0 = net.addController('c0')
	# net = Mininet(topo=MyTopo(), link=TCLink, controller=RemoteController)
	# cont = net.addController('r1', controller=RemoteController, ip='10.39.1.71',port=6633)
	# cont.start()
	
	e1, e2 = net.getNodeByName('e1', 'e2')
	e1.setIP(ip='10.0.0.1', prefixLen=32) #, intf='eth0')
	e2.setIP(ip='10.0.0.2', prefixLen=32) #, intf='eth0')
	e1.setMAC(mac='00:00:00:01:00:01')
	e2.setMAC(mac='00:00:00:01:00:02')
	
	## To fix "network is unreachable"
	e1.setDefaultRoute(intf='e1-eth0')
	e2.setDefaultRoute(intf='e2-eth0')

	net.start()
  # run_tnodes([t11, t21, t31])
	CLI(net)
	net.stop()
  
