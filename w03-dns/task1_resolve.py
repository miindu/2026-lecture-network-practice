#!/usr/bin/env python3
"""Week 3 · Task 1 — Build your own iterative resolver.

Textbook §2.4.2 - §2.4.3.

`dig +trace` walks root -> TLD -> authoritative for you. In this task you do
that walk yourself: start at a root server, read the delegation it returns,
ask the next server, and keep going until somebody answers authoritatively.
"""
import argparse
import ipaddress
import subprocess
import sys

ROOT_SERVERS = [
    "198.41.0.4",
    "199.9.14.201",
    "192.33.4.12",
]

VERIFY_NAMES = [
    ("www.korea.ac.kr", "stable"),
    ("dns.google", "stable"),
    ("en.wikipedia.org", "stable"),
    ("www.stanford.edu", "stable"),
    ("www.microsoft.com", "cdn"),
]


def _clean_name(name):
    return name.rstrip(".").lower()


def _is_ipv4(value):
    try:
        return ipaddress.ip_address(value).version == 4
    except ValueError:
        return False


def _parse_rr(line):
    """Parse one ordinary `dig` RR line into (owner, type, value)."""
    parts = line.split()
    if len(parts) < 5 or parts[2].upper() != "IN":
        return None
    owner = _clean_name(parts[0])
    rtype = parts[3].upper()
    value = parts[4].rstrip(".")
    return owner, rtype, value


class Resolver:
    """Small iterative IPv4 DNS resolver using `dig` only for transport."""

    def __init__(self, max_depth=30, timeout=2):
        self.max_depth = max_depth
        self.timeout = timeout
        self.no_glue_events = 0
        self.no_glue_extra_queries = 0

    def _query(self, server, name):
        args = [
            "dig", f"@{server}", name, "A", "+norecurse",
            "+noall", "+answer", "+authority", "+additional",
            f"+time={self.timeout}", "+tries=1",
        ]
        try:
            p = subprocess.run(args, capture_output=True, text=True,
                               timeout=self.timeout + 2)
        except (subprocess.TimeoutExpired, OSError):
            return None
        if p.returncode != 0:
            return None

        records = []
        for line in p.stdout.splitlines():
            rr = _parse_rr(line)
            if rr:
                records.append(rr)
        return records

    def resolve(self, name):
        self.no_glue_events = 0
        self.no_glue_extra_queries = 0
        path = []
        active = set()
        address = self._walk(_clean_name(name), list(ROOT_SERVERS), path,
                             active, 0)
        return address, path

    def _walk(self, name, servers, path, active, depth):
        if depth >= self.max_depth:
            raise RuntimeError("DNS resolution depth limit exceeded")
        if name in active:
            raise RuntimeError(f"DNS loop detected while resolving {name}")

        active.add(name)
        try:
            current_servers = list(dict.fromkeys(servers))
            while current_servers:
                next_servers = []
                got_referral = False

                for server in current_servers:
                    path.append(server)
                    records = self._query(server, name)
                    if records is None:
                        continue

                    # If the requested owner itself is a CNAME, restart from root
                    # for the target. This deliberately follows the chain ourselves.
                    cnames = [value for owner, rtype, value in records
                              if owner == name and rtype == "CNAME"]
                    if cnames:
                        target = _clean_name(cnames[0])
                        return self._walk(target, list(ROOT_SERVERS), path,
                                          active, depth + 1)

                    # A final A answer for the name we asked for.
                    answers = [value for owner, rtype, value in records
                               if owner == name and rtype == "A" and _is_ipv4(value)]
                    if answers:
                        return answers[0]

                    # A response may include a CNAME chain plus the final A. If
                    # the first CNAME owner was not exactly `name`, still follow
                    # the first CNAME that appears rather than treating glue as
                    # the answer.
                    any_cname = [value for _, rtype, value in records
                                 if rtype == "CNAME"]
                    if any_cname:
                        return self._walk(_clean_name(any_cname[0]),
                                          list(ROOT_SERVERS), path,
                                          active, depth + 1)

                    # Referral: authority gives NS names. Additional A records
                    # may give glue for some/all of those names.
                    ns_names = [_clean_name(value) for _, rtype, value in records
                                if rtype == "NS"]
                    if not ns_names:
                        continue

                    glue = {}
                    for owner, rtype, value in records:
                        if rtype == "A" and _is_ipv4(value):
                            glue.setdefault(owner, []).append(value)

                    for ns_name in ns_names:
                        if ns_name in glue:
                            next_servers.extend(glue[ns_name])
                        else:
                            # No glue: resolve the nameserver's own name first.
                            try:
                                self.no_glue_events += 1
                                before = len(path)
                                ns_ip = self._walk(ns_name, list(ROOT_SERVERS),
                                                   path, active, depth + 1)
                                self.no_glue_extra_queries += len(path) - before
                                next_servers.append(ns_ip)
                            except RuntimeError:
                                # One NS can be unusable; try the others.
                                continue

                    if next_servers:
                        got_referral = True
                        break

                if got_referral:
                    current_servers = list(dict.fromkeys(next_servers))
                    continue

                raise RuntimeError(f"No usable DNS answer for {name}")

            raise RuntimeError(f"No DNS servers left while resolving {name}")
        finally:
            active.discard(name)


# ------------------------------------------------------------------- harness
def dig_answer(name):
    """What the system resolver says, for comparison."""
    out = subprocess.run(["dig", "+short", name, "A"],
                         capture_output=True, text=True).stdout
    return [l for l in out.split() if l and l[0].isdigit()]


def verify():
    r, failures = Resolver(), 0
    for name, kind in VERIFY_NAMES:
        try:
            addr, path = r.resolve(name)
        except NotImplementedError:
            print("Nothing implemented yet - write Resolver.resolve first.")
            return 1
        except Exception as e:
            print(f"  FAIL  {name:<22} your resolver raised {e!r}")
            failures += 1
            continue
        expected = dig_answer(name)
        if addr in expected:
            note = ""
        elif kind == "cdn":
            note = "  <- differs, but this name is CDN-hosted. Explain it."
        else:
            note = "  <- should have matched"
            failures += 1
        print(f"  {'FAIL' if note.endswith('matched') else 'ok  '}  {name:<22} "
              f"you={addr:<16} dig={','.join(expected) or '-'}   "
              f"hops={len(path)}{note}")
    print(f"\n  {len(VERIFY_NAMES) - failures}/{len(VERIFY_NAMES)} ok")
    return 1 if failures else 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("name", nargs="?", default="www.korea.ac.kr")
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()

    if a.verify:
        sys.exit(verify())

    resolver = Resolver()
    addr, path = resolver.resolve(a.name)
    for i, server in enumerate(path, 1):
        print(f"  {i}. asked {server}")
    print(f"\n  {a.name} -> {addr}")
    print(f"  no-glue events: {resolver.no_glue_events}, "
          f"extra server queries: {resolver.no_glue_extra_queries}")


if __name__ == "__main__":
    main()
