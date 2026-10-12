import socket
import time
import struct

TARGET_IP = '192.168.11.129'
TARGET_PORT = 502

def semantic_fuzzing_attack():
    print(f"[*] Starting Combined Semantic Fuzzing against {TARGET_IP}:{TARGET_PORT}")
    print(f"[*] Will alternate between two anomaly types:")
    print(f"    Type A -> Unsupported Function Code (triggers SID 1000201)")
    print(f"    Type B -> Invalid Protocol ID          (triggers SID 1000202)\n")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((TARGET_IP, TARGET_PORT))

        for i in range(50):
            transaction_id = i
            length = 0x0002
            unit_id = 0x01

            if i % 10 == 0:
                protocol_id = 0x0001            
                function_code = 0x03            
                anomaly_type = "Type B (Invalid Protocol ID)"
            else:
                protocol_id = 0x0000            
                function_code = 60 + i
                anomaly_type = "Type A (Unsupported FC)"

            mbap_header = struct.pack('>HHHB', transaction_id, protocol_id, length, unit_id)
            payload = struct.pack('>B', function_code)
            packet = mbap_header + payload

            s.sendall(packet)
            print(f"[+] [{anomaly_type}] TID={transaction_id}, ProtocolID=0x{protocol_id:04X}, FC={function_code}")

            try:
                response = s.recv(1024)
                if response:
                    print(f"    Received response: {response.hex()}")
            except socket.timeout:
                print("    No response received.")

            time.sleep(0.1)

        s.close()
        print("\n[*] Combined semantic fuzzing complete.")
        print("[*] Check Suricata alerts for both SID 1000201 and SID 1000202.")

    except Exception as e:
        print(f"[-] Connection error occurred: {e}")

if __name__ == "__main__":
    semantic_fuzzing_attack()
