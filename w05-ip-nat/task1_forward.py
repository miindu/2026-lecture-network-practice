#!/usr/bin/env python3
"""Week 5 · Task 1 — Subnets and longest-prefix match.

Textbook §4.3.2 (IPv4 addressing, CIDR) and §4.3.3 (forwarding).

    python3 task1_forward.py --verify
"""
import argparse


def ip_to_int(address):
    parts = address.split(".")
    if len(parts) != 4:
        raise ValueError("Invalid IP address")

    number = 0
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            raise ValueError("Invalid IP address")
        number = (number << 8) | int(part)

    return number


def int_to_ip(number):
    return ".".join(
        str((number >> shift) & 255)
        for shift in (24, 16, 8, 0)
    )


def parse_cidr(cidr):
    parts = cidr.split("/")
    if len(parts) != 2:
        raise ValueError("Invalid CIDR")

    network = ip_to_int(parts[0])

    if not parts[1].isdigit():
        raise ValueError("Invalid prefix")

    prefix = int(parts[1])
    if prefix < 0 or prefix > 32:
        raise ValueError("Invalid prefix")

    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF

    if (network & mask) != network:
        raise ValueError("Host bits are set")

    return network, prefix


def network_range(cidr):
    network, prefix = parse_cidr(cidr)

    broadcast = network | ((1 << (32 - prefix)) - 1)

    if prefix >= 31:
        first = network
        last = broadcast
    else:
        first = network + 1
        last = broadcast - 1

    return (
        int_to_ip(first),
        int_to_ip(last),
        int_to_ip(broadcast)
    )


class ForwardingTable:
    def __init__(self):
        self.routes = []

    def add(self, cidr, next_hop):
        network, prefix = parse_cidr(cidr)

        for net, plen, hop in self.routes:
            if net == network and plen == prefix:
                raise ValueError("Duplicate route")

        self.routes.append((network, prefix, next_hop))

    def lookup(self, address):
        ip = ip_to_int(address)
        best_prefix = -1
        best_hop = None

        for network, prefix, hop in self.routes:
            mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF

            if (ip & mask) == network and prefix > best_prefix:
                best_prefix = prefix
                best_hop = hop

        return best_hop


# ------------------------------------------------------------------- harness
RANGE_CASES = [
    ("192.168.0.0/24",  "192.168.0.1",   "192.168.0.254",  "192.168.0.255"),
    ("10.0.0.0/8",      "10.0.0.1",      "10.255.255.254", "10.255.255.255"),
    ("172.16.32.0/20",  "172.16.32.1",   "172.16.47.254",  "172.16.47.255"),
    ("203.0.113.64/26", "203.0.113.65",  "203.0.113.126",  "203.0.113.127"),
]

TABLE = [
    ("0.0.0.0/0",       "default-gw"),
    ("10.0.0.0/8",      "campus"),
    ("10.20.0.0/16",    "eng-building"),
    ("10.20.30.0/24",   "lab-floor"),
    ("10.20.30.64/26",  "lab-rack-2"),
    ("192.168.1.0/24",  "home"),
]

LOOKUP_CASES = [
    ("10.20.30.70",   "lab-rack-2"),
    ("10.20.30.10",   "lab-floor"),
    ("10.20.99.1",    "eng-building"),
    ("10.99.0.1",     "campus"),
    ("8.8.8.8",       "default-gw"),
    ("192.168.1.77",  "home"),
]


def verify():
    fails = 0
    for cidr, first, last, bcast in RANGE_CASES:
        try:
            got = network_range(cidr)
        except NotImplementedError:
            print("  network_range is still a stub"); return 1
        except Exception as e:
            print(f"  FAIL  {cidr:<18} raised {e!r}"); fails += 1; continue
        ok = tuple(got) == (first, last, bcast)
        print(f"  {'ok  ' if ok else 'FAIL'}  {cidr:<18} {got}")
        fails += not ok

    t = ForwardingTable()
    try:
        for cidr, hop in TABLE:
            t.add(cidr, hop)
    except NotImplementedError:
        print("  ForwardingTable is still a stub"); return 1

    for addr, expect in LOOKUP_CASES:
        got = t.lookup(addr)
        ok = got == expect
        print(f"  {'ok  ' if ok else 'FAIL'}  {addr:<16} -> {got}  (want {expect})")
        fails += not ok

    print(f"\n  {len(RANGE_CASES) + len(LOOKUP_CASES) - fails}"
          f"/{len(RANGE_CASES) + len(LOOKUP_CASES)} ok")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())

