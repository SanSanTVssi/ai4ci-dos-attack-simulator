import os
import sys
import ctypes
import threading
from scapy.all import *
from queue import Queue

banner = '''-----------------------
SniffnDetect v.1.1
-----------------------
'''

class SniffnDetect():
	def __init__(self):
		self.INTERFACE = conf.iface
		self.MY_IP = self.INTERFACE.ip
		self.MY_MAC = self.INTERFACE.mac
		self.WEBSOCKET = None
		self.PACKETS_QUEUE = Queue()
		self.MAC_TABLE = {}
		self.RECENT_ACTIVITIES = []
		self.FILTERED_ACTIVITIES = {
			'TCP-SYN': {'flag': False, 'activities': [], 'attacker-mac': []},
			'TCP-SYNACK': {'flag': False, 'activities': [], 'attacker-mac': []},
			'ICMP-POD': {'flag': False, 'activities': [], 'attacker-mac': []},
			'ICMP-SMURF': {'flag': False, 'activities': [], 'attacker-mac': []},
		}
		self.flag = False

	def sniffer_threader(self):
		while self.flag:
			pkt = sniff(count=1)
			with threading.Lock():
				self.PACKETS_QUEUE.put(pkt[0])

	def analyze_threader(self):
		while self.flag:
			pkt = self.PACKETS_QUEUE.get()
			self.analyze_packet(pkt)
			self.PACKETS_QUEUE.task_done()

	def check_avg_time(self, activities):
		time = 0
		c = -1
		while c>-31:
			time += activities[c][0] - activities[c-1][0]
			c -= 1
		time /= len(activities)
		return ( time<2 and self.RECENT_ACTIVITIES[-1][0] - activities[-1][0] < 10)

	def find_attackers(self, mac_data):
		msg = []
		for mac in mac_data:
			msg.append("["+str(self.MAC_TABLE[mac])+" ("+mac+")]" if mac in self.MAC_TABLE else "[Unknown IP ("+mac+")]")
		return " ".join(msg)
	
	def set_flags(self):
		for category in self.FILTERED_ACTIVITIES:
			if len(self.FILTERED_ACTIVITIES[category]['activities'])>20:
				self.FILTERED_ACTIVITIES[category]['flag'] = check_avg_time(self.FILTERED_ACTIVITIES[category]['activities'])
				if self.FILTERED_ACTIVITIES[category]['flag']:
					self.FILTERED_ACTIVITIES[category]['attacker-mac'] = list(set([i[3] for i in self.FILTERED_ACTIVITIES[category]['activities']]))
	
	def analyze_packet(self, pkt):
		src_ip, dst_ip, src_port, dst_port, tcp_flags, icmp_type = None, None, None, None, None, None
		protocol = []

		if len(self.RECENT_ACTIVITIES)>15:
			self.RECENT_ACTIVITIES = self.RECENT_ACTIVITIES[-15:]
		
		for category in self.FILTERED_ACTIVITIES:
			if len(self.FILTERED_ACTIVITIES[category]['activities'])>30:
				self.FILTERED_ACTIVITIES[category]['activities'] = self.FILTERED_ACTIVITIES[category]['activities'][-30:]

		self.set_flags()

		src_mac = pkt[Ether].src if Ether in pkt else None
		dst_mac = pkt[Ether].dst if Ether in pkt else None
			
		if IP in pkt:
			src_ip = pkt[IP].src
			dst_ip = pkt[IP].dst
		elif IPv6 in pkt:
			src_ip = pkt[IPv6].src
			dst_ip = pkt[IPv6].dst
		
		if TCP in pkt:
			protocol.append("TCP")
			src_port = pkt[TCP].sport
			dst_port = pkt[TCP].dport
			tcp_flags = pkt[TCP].flags.flagrepr()
		if UDP in pkt:
			protocol.append("UDP")
			src_port = pkt[UDP].sport
			dst_port = pkt[UDP].dport
		if ICMP in pkt:
			protocol.append("ICMP")
			icmp_type = pkt[ICMP].type # 8 for echo-request and 0 for echo-reply
		
		if ARP in pkt and pkt[ARP].op in (1,2):
			protocol.append("ARP")
			if pkt[ARP].hwsrc in self.MAC_TABLE.keys() and self.MAC_TABLE[pkt[ARP].hwsrc] != pkt[ARP].psrc:
				self.MAC_TABLE[pkt[ARP].hwsrc] = pkt[ARP].psrc
			if pkt[ARP].hwsrc not in self.MAC_TABLE.keys():
				self.MAC_TABLE[pkt[ARP].hwsrc] = pkt[ARP].psrc
		
		load_len = len(pkt[Raw].load) if Raw in pkt else None

		attack_type = None
		
		if ICMP in pkt:
			if src_ip == self.MY_IP and src_mac != self.MY_MAC:
				self.FILTERED_ACTIVITIES['ICMP-SMURF']['activities'].append([pkt.time,])
				attack_type = 'ICMP-SMURF PACKET'

			if load_len>1024:
				self.FILTERED_ACTIVITIES['ICMP-POD']['activities'].append([pkt.time,])
				attack_type = 'ICMP-PoD PACKET'

		if dst_ip == self.MY_IP:
			if TCP in pkt:
				if tcp_flags == "S":
					self.FILTERED_ACTIVITIES['TCP-SYN']['activities'].append([pkt.time,])
					attack_type = 'TCP-SYN PACKET'

				elif tcp_flags == "SA":
					self.FILTERED_ACTIVITIES['TCP-SYNACK']['activities'].append([pkt.time,])
					attack_type = 'TCP-SYNACK PACKET'

		self.RECENT_ACTIVITIES.append([pkt.time, protocol, src_ip, dst_ip, src_mac, dst_mac, src_port, dst_port, load_len, attack_type])
	
	def start(self):
		if not self.flag:
			self.flag = True
			sniff_thread = threading.Thread(target=self.sniffer_threader)
			sniff_thread.daemon = True
			sniff_thread.start()
			analyze_thread = threading.Thread(target=self.analyze_threader)
			analyze_thread.daemon = True
			analyze_thread.start()
		return self.flag
	
	def stop(self):
		self.flag = False
		self.PACKETS_QUEUE = Queue()
		self.RECENT_ACTIVITIES = []
		self.FILTERED_ACTIVITIES = {
			'TCP-SYN': {'flag': False, 'activities': [], 'attacker-mac': []},
			'TCP-SYNACK': {'flag': False, 'activities': [], 'attacker-mac': []},
			'ICMP-POD': {'flag': False, 'activities': [], 'attacker-mac': []},
			'ICMP-SMURF': {'flag': False, 'activities': [], 'attacker-mac': []},
		}
		return self.flag

def clear_screen():
	if "linux" in sys.platform:
		os.system("clear")
	elif "win32" in sys.platform:
		os.system("cls")
	else:
		pass
	
def is_admin():
	try:
		return os.getuid() == 0
	except AttributeError:
		pass
	try:
		return ctypes.windll.shell32.IsUserAnAdmin() == 1
	except AttributeError:
		return False

'''
def main():
	global mac_table, recent_activities, filtered_activities, PACKETS_QUEUE, INTERFACE, MY_NETMASK, MY_IP, MY_MAC
	sniff_thread = threading.Thread(target=sniffer_threader)
	sniff_thread.daemon = True
	sniff_thread.start()
	analyze_thread = threading.Thread(target=analyze_threader)
	analyze_thread.daemon = True
	analyze_thread.start()
	while True:
		global mac_table, recent_activities, filtered_activities, PACKETS_QUEUE, INTERFACE, MY_NETMASK, MY_IP, MY_MAC
		clear_screen()
		print(banner)
		print("[i] Current Interface = {}\n[i] Current IP = {}\n[i] Current Subnet Mask = {}\n[i] Current MAC = {}\n[i] Recent Activities:".format(INTERFACE, MY_IP, MY_NETMASK, MY_MAC))
		for i in recent_activities[::-1]:
			if i[8]:
				msg = ' '.join(i[1])+" "+str(i[2])+":"+str(i[6])+" ("+str(i[4])+") => "+str(i[3])+":"+str(i[7])+" ("+str(i[5])+") ["+str(i[8])+" bytes]"
			else:
				msg = ' '.join(i[1])+" "+str(i[2])+":"+str(i[6])+" ("+str(i[4])+") => "+str(i[3])+":"+str(i[7])+" ("+str(i[5])+")"
			if i[9]:
				print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i[0])), msg, i[9])
			else:
				print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i[0])), msg)
		print("[i] ICMP Smurf Attack:\t {}\n[i] Ping of Death:\t {}\n[i] TCP SYN Flood:\t {}\n[i] TCP SYN-ACK Flood:\t {}".format(
		filtered_activities['ICMP-SMURF']['flag'], filtered_activities['ICMP-POD']['flag'],
		filtered_activities['TCP-SYN']['flag'], filtered_activities['TCP-SYNACK']['flag'],
		))
		if any([filtered_activities[category]['flag'] for category in filtered_activities]):
			print("[i] Potential Attacker(s):\n")
			for category in filtered_activities:
				if category == 'ICMP-POD':
					print("Ping of Death Attacker(s): ", find_attackers(filtered_activities[category]['attacker-mac']))
				elif category == 'ICMP-SMURF':
					print("ICMP Smurf Attacker(s): ", find_attackers(filtered_activities[category]['attacker-mac']))
				elif category == 'TCP-SYNACK':
					print("SYN-ACK Flood Attacker(s): ", find_attackers(filtered_activities[category]['attacker-mac']))
				elif category == 'TCP-SYN':
					print("SYN Flood Attacker(s): ", find_attackers(filtered_activities[category]['attacker-mac']))
			print()
		time.sleep(0.5)

if __name__=="__main__":
	mac_table = {}
	recent_activities = []
	filtered_activities = {
		'TCP-SYN': {'flag': False, 'activities': [], 'attacker-mac': []},
		'TCP-SYNACK': {'flag': False, 'activities': [], 'attacker-mac': []},
		'ICMP-POD': {'flag': False, 'activities': [], 'attacker-mac': []},
		'ICMP-SMURF': {'flag': False, 'activities': [], 'attacker-mac': []},
	}

	PACKETS_QUEUE = Queue()

	clear_screen()
	if not is_admin():
		print("[-] Please execute the script with root or administrator priviledges.")
		sys.exit(" Exiting.")
	
	INTERFACE = conf.iface
	MY_IP = [x[4] for x in conf.route.routes if x[2] != '0.0.0.0' and x[3]==INTERFACE][0]
	MY_MAC = get_if_hwaddr(INTERFACE)
	MY_NETMASK = [IPv4Address(x[1]).compressed for x in conf.route.routes if x[3]==INTERFACE and x[4]==MY_IP and x[2]=='0.0.0.0' and IPv4Address(x[1]).compressed.startswith("255.") and IPv4Address(x[0]).compressed.startswith(MY_IP.split(".")[0]) and IPv4Address(x[0]).compressed.endswith(".0")][0]

	try:
		print("[+] Starting sniffing module at {}\n".format(str(datetime.now()).split(".")[0]))
		main()
	except KeyboardInterrupt:
		print("\n[-] Ctrl+C triggered.")
	except EOFError:
		print("\n[-] Ctrl+Z triggered.")
	except:
		print("[-] Some unknown error occured.")
		print("[!] EXCEPTION: "+traceback.print_exc())
	finally:
		sys.exit("\n[-] Exiting.")
'''