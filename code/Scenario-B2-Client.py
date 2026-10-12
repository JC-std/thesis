import socket
import struct
import argparse
import time
import sys

ALL_EXCEPTION_CODES = [
    (0x01, "Illegal Function",             1000203),
    (0x02, "Illegal Data Address",         1000204),
    (0x03, "Illegal Data Value",           1000205),
    (0x04, "Slave Device Failure",         1000206),
    (0x05, "Acknowledge",                  1000207),
    (0x06, "Slave Device Busy",            1000208),
    (0x07, "Negative Acknowledge",         1000209),
    (0x08, "Memory Parity Error",          1000210),
    (0x0A, "Gateway Path Unavailable",     1000211),
    (0x0B, "Gateway Target Device Failed", 1000212),
]

ORIGINAL_FC = 0x03


def parse_sid_filter(sid_arg: str):
    if not sid_arg:
        return ALL_EXCEPTION_CODES

    requested = set()
    for part in sid_arg.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            requested.add(int(part))
        except ValueError:
            print(f"[Warning] Ignoring invalid SID value: {part}")

    valid_sids = {sid for _, _, sid in ALL_EXCEPTION_CODES}
    unknown = requested - valid_sids
    if unknown:
        print(f"[Warning] Unknown SID(s) ignored: {sorted(unknown)}")

    filtered = [item for item in ALL_EXCEPTION_CODES if item[2] in requested]

    if not filtered:
        print("[Error] No valid SID matched, nothing to run")
        sys.exit(1)

    return filtered


def build_exception_packet(trans_id: int, exception_code: int) -> bytes:
    unit_id = 0x01
    function_code = ORIGINAL_FC | 0x80
    pdu = struct.pack("!BB", function_code, exception_code)
    length = len(pdu) + 1
    header = struct.pack("!HHHB", trans_id, 0x0000, length, unit_id)
    return header + pdu


def build_request_packet(trans_id: int) -> bytes:
    unit_id = 0x01
    pdu = struct.pack("!BHH", ORIGINAL_FC, 0x0000, 0x0001)
    length = len(pdu) + 1
    header = struct.pack("!HHHB", trans_id, 0x0000, length, unit_id)
    return header + pdu


def run_server(host: str, port: int, cases):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(5)
    print(f"[Server] Listening on {host}:{port}, expecting to handle {len(cases)} test case(s)")

    trans_id = 1
    for code, name, sid in cases:
        print(f"[Server] Waiting for connection to trigger SID {sid} ({name}, 0x{code:02X}) ...")
        conn, addr = srv.accept()
        conn.settimeout(2)
        print(f"[Server]   Connected: {addr}")
        try:
            try:
                conn.recv(1024)
            except socket.timeout:
                pass
            pkt = build_exception_packet(trans_id, code)
            conn.sendall(pkt)
            print(f"[Server]   Sent Exception 0x{code:02X} -> SID {sid}, "
                  f"packet length={len(pkt)} bytes")
        except (BrokenPipeError, ConnectionResetError):
            print("[Server]   Connection dropped, skipping this case")
        finally:
            conn.close()
            trans_id += 1
            time.sleep(0.2)

    srv.close()
    print(f"[Server] All {len(cases)} test case(s) have been sent")


def run_client(host: str, port: int, cases):
    print(f"[Client] Preparing to initiate {len(cases)} connection(s) to {host}:{port}")
    for i, (code, name, sid) in enumerate(cases, start=1):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((host, port))
            req = build_request_packet(i)
            s.sendall(req)
            print(f"[Client] Connection #{i} request sent (targeting SID {sid} {name})")
            try:
                resp = s.recv(1024)
                print(f"[Client]   Received response: {resp.hex()} (length={len(resp)} bytes)")
            except socket.timeout:
                print("[Client]   No response received (timeout)")
            s.close()
        except ConnectionRefusedError:
            print("[Client] Connection refused, please verify the server script is running and listening on 502")
            break
        except Exception as e:
            print(f"[Client] Error occurred: {e}")
            break
        time.sleep(0.2)

    print("[Client] Test sequence finished")


def main():
    parser = argparse.ArgumentParser(description="Modbus B2 (Exception Response) test script")
    parser.add_argument("mode", choices=["server", "client"], help="Execution mode")
    parser.add_argument("--host", default=None,
                         help="server mode: bind address (default 0.0.0.0) / client mode: target server IP (required)")
    parser.add_argument("--port", type=int, default=502, help="Modbus TCP port, default 502")
    parser.add_argument("--sids", default=None,
                         help="Comma-separated list of SIDs to run, e.g. 1000203,1000205,1000210. "
                              "If omitted, all 10 SIDs (1000203-1000212) will be executed")
    args = parser.parse_args()

    cases = parse_sid_filter(args.sids)

    if args.mode == "server":
        host = args.host or "0.0.0.0"
        run_server(host, args.port, cases)
    else:
        if not args.host:
            print("[Error] client mode requires --host <server_ip>")
            sys.exit(1)
        run_client(args.host, args.port, cases)


if __name__ == "__main__":
    main()
