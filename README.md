# 🛡️ Modbus TCP Threat Monitoring Framework

[![Standard](https://img.shields.io/badge/Standard-ISA%2FIEC_62443--3--3-blue.svg)](https://www.isa.org/isa99/)
[![Kill Chain](https://img.shields.io/badge/Framework-ICS_Cyber_Kill_Chain-red.svg)](https://www.sans.org/)
[![DPI](https://img.shields.io/badge/DPI-Suricata-orange.svg)](https://suricata.io/)
[![SIEM](https://img.shields.io/badge/SIEM-Graylog-green.svg)](https://www.graylog.org/)

This repository contains the source code, attack simulation scripts, and Suricata detection rules for the paper: **"Design and Implementation of a Modbus TCP Threat Monitoring Framework Based on ISA/IEC 62443 and the ICS Cyber Kill Chain Using Suricata and Graylog"**.

This project provides a reproducible virtualized testbed for evaluating Deep Packet Inspection (DPI) rules against various Modbus TCP attack scenarios.

---

## 🏗️ Experimental Environment Setup

The experimental testbed consists of two virtual machines:

*   **VM1 (Attacker Node):** Kali Linux (IP: `192.168.11.128`). Runs the Python attack scripts and Nmap.
*   **VM2 (Defender Node):** Ubuntu 22.04 LTS (IP: `192.168.11.129`). Hosts the OT simulation layer (ModbusPal) and security monitoring layer (Suricata, Graylog).

### ⚙️ Prerequisites (Kali Linux / VM1)
Ensure Python 3.11+ is installed along with the required communication library:
```bash
pip install pymodbus
```

---

## 🚀 Attack Scenarios & Detection Rules (Step-by-Step)

Before running the scenarios, ensure that **ModbusPal** (listening on TCP/502), **Suricata** (with `local.rules` loaded), and **Graylog** are actively running on VM2.

### 🟢 Step 0: Baseline Traffic Generation
Establish a benign traffic baseline to verify that normal operations do not trigger false positive alerts.

*   **Execution Script:**
    ```bash
    python baseline_modbus_traffic.py
    ```
*   **Target Function Codes:** `FC 01`, `FC 02`, `FC 03`.
*   **Triggered Rules:** *None (Benign Traffic)*.
*   **Expected Result:** The console displays normal read responses. Suricata generates no alerts.

---

### 🔍 Step 1: Scenario A - Reconnaissance Scanning
Simulates an attacker attempting to discover Modbus TCP devices in the network.

> **Kill Chain Stage:** Test | **Severity:** Normal | **IEC 62443-3-3:** FR 5 (Restricted Data Flow)

*   **Execution Command:**
    ```bash
    nmap -p 502 --script modbus-discover 192.168.11.129
    ```
*   **Correlated Suricata Rules:**
    ```text
    alert tcp any any -> any 502 (msg:"5.2.1 Test: Scenario A - Nmap Modbus Scan Phase 1 (FC 17)"; modbus:function 17; classtype:attempted-recon; sid:1000101; rev:1;)
    alert tcp any any -> any 502 (msg:"5.2.1 Test: Scenario A - Nmap Modbus Scan Phase 2 (FC 43 Device Identification)"; flow:established,to_server; modbus:function 43; classtype:attempted-recon; sid:1000102; rev:3;)
    ```

---

### 💣 Step 2: Scenario B - Modbus Protocol Fuzzing
Simulates sending malformed packets, unsupported function codes, or triggering excessive exception responses.

> **Kill Chain Stage:** Deliver | **Severity:** Normal | **IEC 62443-3-3:** FR 3 (System Integrity)

*   **Execution Scripts:**
    ```bash
    python scenario-B.py          # Probes unsupported FCs (60-109)
    python Scenario-B1.py         # Alternates between Invalid Protocol ID and unsupported FCs
    python Scenario-B2-Client.py  # Triggers various Modbus Exception responses
    ```
*   **Correlated Suricata Rules (Extracts):**
    ```text
    # Malformed / Unsupported FCs
    alert tcp any any -> any 502 (msg:"5.2.2 Deliver: Scenario B1 - Unsupported Modbus Function Code Probe Detected"; flow:established,to_server; dsize:>7; byte_test:2,=,0,2; byte_test:1,>,43,7; classtype:protocol-command-decode; sid:1000201; rev:2;)
    alert tcp any any -> any 502 (msg:"5.2.2 Deliver: Scenario B1 - Malformed MBAP Header Invalid Protocol ID Detected (!= 0x0000)"; flow:established,to_server; dsize:>7; byte_test:2,!=,0,2; classtype:protocol-command-decode; sid:1000202; rev:1;)
    
    # Exception Responses (0x01 to 0x0B)
    alert tcp any 502 -> any any (msg:"5.2.3 Deliver: Scenario B2 - Modbus Exception Illegal Function Detected (0x01)"; flow:established,to_client; dsize:>8; byte_test:2,=,0,2; byte_test:1,&,0x80,7; byte_test:1,=,1,8; classtype:attempted-recon; sid:1000203; rev:1;)
    alert tcp any 502 -> any any (msg:"5.2.3 Deliver: Scenario B2 - Modbus Exception Illegal Data Address Detected (0x02)"; flow:established,to_client; dsize:>8; byte_test:2,=,0,2; byte_test:1,&,0x80,7; byte_test:1,=,2,8; classtype:attempted-recon; sid:1000204; rev:1;)
    ... (Includes SIDs 1000205 to 1000212 for all covered exception codes)
    ```

---

### ⚠️ Step 3: Scenario C - Unauthorized Modification
Simulates unauthorized write operations altering control-related variables.

> **Kill Chain Stage:** Install / Modify | **Severity:** High | **IEC 62443-3-3:** FR 2 (Use Control)

*   **Execution Scripts:**
    ```bash
    python scenario-C.py          # Tamper using FC 05 (Write Coil), FC 06 (Write Register)
    python Scenario-C1.py         # Tamper using FC 15 (Multiple Coils), FC 16 (Multiple Registers)
    python Scenario-C2.py         # Advanced tamper using FC 22 (Mask), FC 23 (Read/Write Multi)
    ```
*   **Correlated Suricata Rules:**
    ```text
    alert tcp any any -> any 502 (msg:"5.2.4 Install / Modify: Scenario C1 - Modbus Write Coil (FC 05)"; flow:established,to_server; dsize:>7; byte_test:1,=,5,7; classtype:attempted-admin; sid:1000301; rev:2;)
    alert tcp any any -> any 502 (msg:"5.2.4 Install / Modify: Scenario C1 - Modbus Write Register (FC 06)"; flow:established,to_server; dsize:>7; byte_test:1,=,6,7; classtype:attempted-admin; sid:1000302; rev:2;)
    alert tcp any any -> any 502 (msg:"5.2.4 Install / Modify: Scenario C1 - Modbus Write Multiple Coils (FC 15)"; flow:established,to_server; dsize:>7; byte_test:1,=,15,7; classtype:attempted-admin; sid:1000303; rev:1;)
    alert tcp any any -> any 502 (msg:"5.2.4 Install / Modify: Scenario C1 - Modbus Write Multiple Registers (FC 16)"; flow:established,to_server; dsize:>7; byte_test:1,=,16,7; classtype:attempted-admin; sid:1000304; rev:1;)
    alert tcp any any -> any 502 (msg:"5.2.5 Install / Modify: Scenario C2 - Modbus Mask Write Register Detected (FC 22)"; flow:established,to_server; dsize:>7; byte_test:2,=,0,2; byte_test:1,=,22,7; classtype:protocol-command-decode; sid:1000305; rev:1;)
    alert tcp any any -> any 502 (msg:"5.2.5 Install / Modify: Scenario C2 - Modbus Read/Write Multiple Registers Detected (FC 23)"; flow:established,to_server; dsize:>7; byte_test:2,=,0,2; byte_test:1,=,23,7; classtype:protocol-command-decode; sid:1000306; rev:1;)
    ```

---

### 🚨 Step 4: Scenario D - Critical Command Injection
Simulates the injection of high-risk diagnostic commands that affect device communication or state.

> **Kill Chain Stage:** Execute ICS Attack | **Severity:** High | **IEC 62443-3-3:** FR 3 (System Integrity)

*   **Execution Script:**
    ```bash
    python scenario-D.py          # Injects FC 08 (Diagnostics) via raw socket
    ```
*   **Correlated Suricata Rules:**
    ```text
    alert tcp any any -> any 502 (msg:"5.2.6 Execute: Scenario D - Modbus Diagnostic Command Detected"; flow:established,to_server; dsize:>7; byte_test:2,=,0,2; byte_test:1,=,8,7; classtype:protocol-command-decode; sid:10000402; rev:1;)
    alert tcp any any -> any 502 (msg:"5.2.6 Execute: Scenario D - Modbus FC08/0001 Restart Communications Option"; flow:established,to_server; dsize:>9; byte_test:2,=,0,2;byte_test:1,=,8,7; byte_test:2,=,1,8; classtype:protocol-command-decode; sid:10000404; rev:1;)
    alert tcp any any -> any 502 (msg:"5.2.6 Execute: Scenario D - Modbus FC08/0004 Force Listen Only Mode"; flow:established,to_server; dsize:>9; byte_test:2,=,0,2; byte_test:1,=,8,7; byte_test:2,=,4,8; classtype:protocol-command-decode; sid:10000405; rev:1;)
    alert tcp any any -> any 502 (msg:"5.2.6 Execute: Scenario D - Modbus FC08/000A Clear Counters and Diagnostic Register"; flow:established,to_server; dsize:>9; byte_test:2,=,0,2; byte_test:1,=,8,7; byte_test:2,=,10,8; classtype:protocol-command-decode; sid:10000406; rev:1;)
    ```

---

### 🛑 Step 5: Scenario E - Denial-of-Service (DoS) Flooding
Simulates a resource exhaustion attack against the Modbus TCP service.

> **Kill Chain Stage:** Execute ICS Attack | **Severity:** High | **IEC 62443-3-3:** FR 7 (Resource Availability)

*   **Execution Scripts:**
    ```bash
    # Test High-rate SYN Activity
    sudo hping3 -S -p 502 --flood 192.168.11.129
    
    # Test High-rate Payload Activity
    python Scenario-E2.py --host 192.168.11.129 --port 502 --duration 10 --connections 5
    ```
*   **Correlated Suricata Rules:**
    ```text
    alert tcp any any -> any 502 (msg:"5.2.7 Execute ICS Attack: Scenario E1 - Modbus TCP/502 High-rate SYN Activity Detected"; flow:stateless,to_server; flags:S; threshold:type both, track by_src, count 20, seconds 1; classtype:attempted-dos; sid:1000501; rev:6;)
    alert tcp any any -> any 502 (msg:"5.2.8 Execute ICS Attack: Scenario E2 - Modbus TCP/502 High-rate Payload Activity Detected"; flow:established,to_server; dsize:>0; threshold:type both, track by_src, count 100, seconds 1; classtype:attempted-dos; sid:1000502; rev:1;)
    ```

---

## 📊 SIEM Integration & Traceability

When the above rules are triggered in Suricata, the logs are forwarded to Graylog. Graylog correlates these alerts based on:
1. **Rule Signatures & Time Windows**
2. **ICS Cyber Kill Chain Mapping**
3. **ISA/IEC 62443-3-3 Foundational Requirements**
4. **MITRE ATT&CK for ICS Techniques**

Please monitor the **Graylog Dashboard** during script execution to verify real-time alert generation, traffic spike visualization, and dynamic incident response notifications.
