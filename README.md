# Modbus TCP Threat Monitoring Framework

This repository contains the source code and attack simulation scripts for the paper: **"Design and Implementation of a Modbus TCP Threat Monitoring Framework Based on ISA/IEC 62443 and the ICS Cyber Kill Chain Using Suricata and Graylog"**. 

This project provides a reproducible virtualized testbed for evaluating Deep Packet Inspection (DPI) rules against various Modbus TCP attack scenarios, mapped to the ICS Cyber Kill Chain and ISA/IEC 62443-3-3 Foundational Requirements.

## 📋 Repository Structure

*   `baseline_modbus_traffic.py`: Generates benign Modbus read requests (FC 01, 02, 03) to establish a normal traffic baseline.
*   `scenario-B.py` / `Scenario-B1.py` / `Scenario-B2-Client.py`: Scripts simulating **Protocol Fuzzing** (ICS Kill Chain: Deliver). Injects unsupported function codes and invalid protocol IDs.
*   `scenario-C.py` / `Scenario-C1.py` / `Scenario-C2.py`: Scripts simulating **Unauthorized Modification** (ICS Kill Chain: Install/Modify). Attempts to tamper with PLC coils and registers (FC 05, 06, 15, 16, 22, 23).
*   `scenario-D.py`: Script simulating **Critical Command Injection** (ICS Kill Chain: Execute Attack). Sends crafted diagnostic commands (FC 08).
*   `Scenario-E2.py`: Script simulating **Denial-of-Service Flooding** via Modbus TCP payload flooding.

## 🏗️ Experimental Environment Setup

Based on the paper's architecture, a two-VM setup is recommended:

*   **VM1 (Attacker Node):** Kali Linux (IP: `192.168.11.128`). Runs the Python attack scripts and Nmap.
*   **VM2 (Defender/Target Node):** Ubuntu (IP: `192.168.11.129`). Runs ModbusPal (PLC Simulator), Suricata (IDS), and Graylog SIEM (Docker).

*Note: If your target PLC/Simulator IP is different, please update the `TARGET_IP` variable inside each Python script.*

### Prerequisites (Kali Linux / VM1)
Ensure you have Python 3 installed. You will need the `pymodbus` library to run the scripts.
```bash
pip install pymodbus
```

---

## 🚀 Detailed Operation Steps

Before running the attack scenarios, ensure that **ModbusPal** (listening on TCP/502), **Suricata**, and **Graylog** are actively running on VM2.

### Step 0: Baseline Traffic Generation
Establish a benign traffic baseline to verify that normal operations do not trigger Suricata alerts.
1. On VM1, execute the baseline script:
   ```bash
   python baseline_modbus_traffic.py
   ```
2. **Expected Result:** The console should display normal responses for FC 0x01, 0x02, and 0x03. No alerts should appear in Graylog.

### Step 1: Scenario A - Reconnaissance Scanning (Test Stage)
Simulates an attacker attempting to discover Modbus TCP devices in the network.
1. On VM1, use Nmap to scan the target:
   ```bash
   nmap -p 502 --script modbus-discover 192.168.11.129
   ```
2. **Expected Result:** Graylog will trigger an alert for **Rule A (Normal Severity)** indicating device fingerprinting (FC 17 / FC 43).

### Step 2: Scenario B - Modbus Protocol Fuzzing (Deliver Stage)
Simulates sending malformed or semantically abnormal packets to test device robustness.
1. On VM1, execute the base fuzzing script:
   ```bash
   python scenario-B.py
   ```
2. *(Optional)* To test combined anomalies (Invalid Protocol ID and FCs), run:
   ```bash
   python Scenario-B1.py
   ```
3. *(Optional)* To test exception response handling, run the server/client combo:
   ```bash
   python Scenario-B2-Client.py
   ```
4. **Expected Result:** Graylog will trigger an alert for **Rule B (Normal Severity)**, indicating protocol fuzzing and abnormal exceptions.

### Step 3: Scenario C - Unauthorized Modification (Install/Modify Stage)
Simulates unauthorized write operations altering control-related variables.
1. On VM1, execute the basic tamper script (FC 05, FC 06):
   ```bash
   python scenario-C.py
   ```
2. *(Optional)* To test multiple coils/registers tampering (FC 15, FC 16), run:
   ```bash
   python Scenario-C1.py
   ```
3. *(Optional)* To test advanced masking and R/W operations (FC 22, FC 23), run:
   ```bash
   python Scenario-C2.py
   ```
4. **Expected Result:** Graylog will trigger an alert for **Rule C (High Severity)**, indicating unauthorized modification attempts from a non-whitelisted IP.

### Step 4: Scenario D - Critical Command Injection (Execute Attack Stage)
Simulates the injection of high-risk diagnostic commands that affect device communication.
1. On VM1, execute the raw socket injection script:
   ```bash
   python scenario-D.py
   ```
2. **Expected Result:** Graylog will trigger an alert for **Rule D (High Severity)**, detecting the FC 08 (Sub-function 0x0001) restart communication command.

### Step 5: Scenario E - Denial-of-Service Flooding (Execute Attack Stage)
Simulates a resource exhaustion attack against the Modbus TCP service.
1. On VM1, execute the high-rate payload flood script:
   ```bash
   python Scenario-E2.py --host 192.168.11.129 --port 502 --duration 10 --connections 5
   ```
2. *(Alternative method using hping3 from the thesis)*:
   ```bash
   sudo hping3 -S -p 502 --flood 192.168.11.129
   ```
3. **Expected Result:** Graylog will trigger an alert for **Rule E (High Severity)** due to the threshold of connection attempts/packets exceeding the predefined limit, and a traffic spike will be visible in the SIEM dashboard.

## 📊 Evaluation & Traceability
All alerts generated during these scenarios will automatically map to:
*   **ISA/IEC 62443-3-3** Foundational Requirements (FR 2, FR 3, FR 5, FR 7).
*   **ICS Cyber Kill Chain** Stages.
*   **MITRE ATT&CK for ICS** Tactics and Techniques.

Please check the Graylog dashboard for the correlated alert logs and severity classifications.
