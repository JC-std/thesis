import socket
import time
import struct

TARGET_IP = '192.168.11.129'
TARGET_PORT = 502

def semantic_fuzzing_attack():
    print(f"[*] Starting Semantic Fuzzing (Logic Anomaly Probing) against {TARGET_IP}:{TARGET_PORT}")
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((TARGET_IP, TARGET_PORT))
        
        for i in range(50):
            transaction_id = i
            protocol_id = 0x0000  
            length = 0x0002       
            unit_id = 0x01
            
            unsupported_fc = 60 + i  
            
            mbap_header = struct.pack('>HHHB', transaction_id, protocol_id, length, unit_id)
            payload = struct.pack('>B', unsupported_fc)
            
            packet = mbap_header + payload
            
            s.send(packet)
            print(f"[+] Sending valid-structure probe: Transaction ID={transaction_id}, Testing Function Code={unsupported_fc}")
            
            response = s.recv(1024)
            if response:
                print(f"    Received device response: {response.hex()}")
            
            time.sleep(0.1)
            
        s.close()
        print("[*] Fuzzing attack complete! The device should have returned numerous Exceptions; please check Graylog.")
        
    except Exception as e:
        print(f"[-] Connection error occurred: {e}")

if __name__ == "__main__":
    semantic_fuzzing_attack()
