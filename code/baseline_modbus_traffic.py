from pymodbus.client import ModbusTcpClient
import time

TARGET_IP = "192.168.11.129"
TARGET_PORT = 502
UNIT_ID = 1

client = ModbusTcpClient(TARGET_IP, port=TARGET_PORT)

if not client.connect():
    print("[-] Failed to connect to Modbus server")
    exit(1)

print("[+] Connected to Modbus server")

def show_result(name, fc, response):
    if response is None:
        print(f"{name} FC {fc}: No response")
    elif response.isError():
        print(f"{name} FC {fc}: Exception/Error response -> {response}")
    else:
        print(f"{name} FC {fc}: Normal response -> {response}")

for i in range(3):
    print(f"\n[Round {i+1}] Sending baseline Modbus read requests")

    rr1 = client.read_coils(address=0, count=8, slave=UNIT_ID)
    show_result("Read Coils", "0x01", rr1)

    rr2 = client.read_discrete_inputs(address=0, count=8, slave=UNIT_ID)
    show_result("Read Discrete Inputs", "0x02", rr2)

    rr3 = client.read_holding_registers(address=0, count=8, slave=UNIT_ID)
    show_result("Read Holding Registers", "0x03", rr3)

    time.sleep(1)

client.close()
print("\n[+] Baseline traffic test completed")