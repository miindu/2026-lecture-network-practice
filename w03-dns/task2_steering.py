#!/usr/bin/env python3
"""Week 3 · Task 2 — Does DNS actually steer you? Measure it.

Run --collect once on each network, giving each run a label, then --report.
Example:

    python3 task2_steering.py --collect --network home-wifi
    # switch network
    python3 task2_steering.py --collect --network phone-hotspot
    python3 task2_steering.py --report
"""
import argparse
import ipaddress
import json
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
CHAINS_PATH = os.path.join(OUT, "chains.json")
REPORT_PATH = os.path.join(OUT, "report.md")
CAPTURE_PATH = os.path.join(OUT, "dns.pcapng")

SITES = [
    "www.microsoft.com",
    "www.netflix.com",
    "www.adobe.com",
    "www.cnn.com",
    "www.apple.com",
    "www.korea.ac.kr",
    "www.stanford.edu",
    "www.bbc.co.uk",
    "www.spotify.com",
    "www.github.com",
    "www.wikipedia.org",
    "www.nytimes.com",
]

RESOLVERS = {
    "system": None,
    "google": "8.8.8.8",
    "quad9": "9.9.9.9",
}

# The assignment explicitly gives Korea University as the no-CDN counterexample.
# For the steering count we treat the other listed large sites as CDN-hosted,
# including own-CDN/anycast cases where a CNAME alone cannot prove it.
NON_CDN_SITES = {"www.korea.ac.kr"}

THIRD_PARTY_SUFFIXES = (
    "akamaiedge.net", "edgekey.net", "edgesuite.net", "akamai.net",
    "fastly.net", "fastlylb.net", "cloudfront.net", "cloudflare.net",
    "azureedge.net", "azurefd.net", "impervadns.net",
)

# Same-organisation domains that a simple label comparison can mistake for a
# third party. Wikipedia/Wikimedia is the important example in this site list.
SAME_ORG_SUFFIXES = {
    "www.wikipedia.org": ("wikipedia.org", "wikimedia.org"),
    "www.netflix.com": ("netflix.com", "nflxvideo.net", "nflxso.net"),
    "www.github.com": ("github.com", "githubassets.com", "githubusercontent.com"),
    "www.microsoft.com": ("microsoft.com", "microsoftonline.com"),
    "www.apple.com": ("apple.com",),
    "www.spotify.com": ("spotify.com",),
    "www.korea.ac.kr": ("korea.ac.kr",),
    "www.stanford.edu": ("stanford.edu",),
    "www.bbc.co.uk": ("bbc.co.uk",),
    "www.adobe.com": ("adobe.com",),
    "www.cnn.com": ("cnn.com",),
    "www.nytimes.com": ("nytimes.com",),
}


def _clean_name(value):
    return value.rstrip(".").lower()


def _is_ipv4(value):
    try:
        return ipaddress.ip_address(value).version == 4
    except ValueError:
        return False


def dig(name, rtype="A", server=None):
    """Raw lookup. Transport only; returns the non-empty +short lines."""
    args = ["dig", "+short", "+time=2", "+tries=1", name, rtype]
    if server:
        args.insert(1, f"@{server}")
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [line.strip() for line in p.stdout.splitlines() if line.strip()]


def follow_cname_chain(name, server=None, max_hops=20):
    """Return [original, cname target, ...] using one resolver."""
    chain = [_clean_name(name)]
    seen = {chain[0]}
    current = chain[0]

    for _ in range(max_hops):
        answers = dig(current, "CNAME", server)
        targets = [_clean_name(x) for x in answers if not _is_ipv4(x)]
        if not targets:
            break
        target = targets[0]
        if target in seen:
            break
        chain.append(target)
        seen.add(target)
        current = target
    return chain


def lookup_addresses(name, server=None):
    return sorted({x for x in dig(name, "A", server) if _is_ipv4(x)})


def collect(network_label="network1"):
    """Collect one vantage point and merge it into out/chains.json."""
    os.makedirs(OUT, exist_ok=True)
    data = {}
    if os.path.exists(CHAINS_PATH):
        try:
            with open(CHAINS_PATH, encoding="utf-8") as f:
                old = json.load(f)
            if isinstance(old, dict):
                data = old
        except (OSError, json.JSONDecodeError):
            data = {}

    for site in SITES:
        site_data = data.setdefault(site, {"measurements": {}})
        measurements = site_data.setdefault("measurements", {})
        network_data = {}

        for resolver_name, server in RESOLVERS.items():
            chain = follow_cname_chain(site, server)
            final_name = chain[-1]
            addresses = lookup_addresses(final_name, server)
            network_data[resolver_name] = {
                "chain": chain,
                "addresses": addresses,
            }
            print(f"{site:<22} {resolver_name:<7} "
                  f"chain={len(chain) - 1:<2} A={','.join(addresses) or '-'}")

        measurements[network_label] = network_data

    with open(CHAINS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
    print(f"\nSaved {len(SITES)} sites for network '{network_label}' to {CHAINS_PATH}")


def _last_two_labels(name):
    labels = _clean_name(name).split(".")
    return ".".join(labels[-2:]) if len(labels) >= 2 else _clean_name(name)


def _ends_with(name, suffix):
    name = _clean_name(name)
    suffix = _clean_name(suffix)
    return name == suffix or name.endswith("." + suffix)


def _manual_third_party(site, final_name):
    """Evidence-based classification used as the report's human judgement."""
    final_name = _clean_name(final_name)

    for suffix in SAME_ORG_SUFFIXES.get(site, ()):
        if _ends_with(final_name, suffix):
            return False

    for suffix in THIRD_PARTY_SUFFIXES:
        if _ends_with(final_name, suffix):
            return True

    # If the observed final name stays under the site's own visible domain,
    # call it first-party. Otherwise the ownership is not proven by DNS alone;
    # use the conservative third-party judgement for this exercise and explain
    # the limitation in the report.
    if _last_two_labels(site) == _last_two_labels(final_name):
        return False
    return True


def _rule_third_party(site, final_name):
    """Intentionally simple rule required for the assignment discussion."""
    return _last_two_labels(site) != _last_two_labels(final_name)


def _pick_primary_measurement(site_data):
    measurements = site_data.get("measurements", {})
    for network_name, resolvers in measurements.items():
        if "system" in resolvers:
            return network_name, "system", resolvers["system"]
        for resolver_name, result in resolvers.items():
            return network_name, resolver_name, result
    return "-", "-", {"chain": [], "addresses": []}


def _steered(site_data):
    """True if any resolver/network produced a different A-address set."""
    seen = set()
    for resolvers in site_data.get("measurements", {}).values():
        for result in resolvers.values():
            addresses = tuple(sorted(result.get("addresses", [])))
            if addresses:
                seen.add(addresses)
    return len(seen) > 1


def _analyse_capture():
    result = {
        "available": False,
        "query_packet": "not available",
        "response_packet": "not available",
        "transaction_id": "not available",
        "delegation_packet": "not available",
        "answer_packet": "not available",
        "largest_packet": "not available",
        "largest_bytes": "not available",
        "largest_reason": "Capture analysis was not available.",
    }
    if not os.path.exists(CAPTURE_PATH) or not shutil.which("tshark"):
        return result

    def fields(display_filter, field_names):
        args = ["tshark", "-r", CAPTURE_PATH, "-Y", display_filter,
                "-T", "fields"]
        for field in field_names:
            args.extend(["-e", field])
        p = subprocess.run(args, capture_output=True, text=True)
        return [line for line in p.stdout.splitlines() if line.strip()]

    pairs = fields(
        "dns",
        ["frame.number", "dns.id", "dns.flags.response"],
    )
    queries = {}
    for row in pairs:
        parts = row.split("\t")
        if len(parts) < 3:
            continue
        frame, txid, is_response = parts[0], parts[1], parts[2]
        if is_response == "0" and txid:
            queries.setdefault(txid, frame)
        elif is_response == "1" and txid in queries:
            result["query_packet"] = queries[txid]
            result["response_packet"] = frame
            result["transaction_id"] = txid
            break

    delegation = fields(
        "dns.flags.response == 1 && dns.count.answers == 0 && dns.count.auth_rr > 0",
        ["frame.number"],
    )
    answer = fields(
        "dns.flags.response == 1 && dns.a",
        ["frame.number"],
    )
    responses = fields(
        "dns.flags.response == 1",
        ["frame.number", "frame.len", "dns.count.answers",
         "dns.count.auth_rr", "dns.count.add_rr"],
    )

    result["available"] = True
    if delegation:
        result["delegation_packet"] = delegation[0].split("\t")[0]
    if answer:
        result["answer_packet"] = answer[0].split("\t")[0]

    parsed = []
    for row in responses:
        parts = row.split("\t")
        if len(parts) < 2:
            continue
        try:
            frame = int(parts[0] or 0)
            length = int(parts[1] or 0)
            an = int((parts[2] if len(parts) > 2 else "0") or 0)
            ns = int((parts[3] if len(parts) > 3 else "0") or 0)
            ar = int((parts[4] if len(parts) > 4 else "0") or 0)
            parsed.append((length, frame, an, ns, ar))
        except ValueError:
            continue

    if parsed:
        length, frame, an, ns, ar = max(parsed)
        result["largest_packet"] = str(frame)
        result["largest_bytes"] = str(length)
        if ns + ar >= an and ns + ar > 1:
            result["largest_reason"] = (
                f"It carried many authority/additional records "
                f"(answer={an}, authority={ns}, additional={ar}), including delegation/glue data."
            )
        elif an > 1:
            result["largest_reason"] = (
                f"It carried multiple answer records (answer={an})."
            )
        else:
            result["largest_reason"] = (
                f"It was the largest captured DNS response; counts were "
                f"answer={an}, authority={ns}, additional={ar}."
            )
    return result


def report():
    if not os.path.exists(CHAINS_PATH):
        raise FileNotFoundError("Run --collect first so out/chains.json exists")

    with open(CHAINS_PATH, encoding="utf-8") as f:
        data = json.load(f)

    networks = []
    for site_data in data.values():
        for network in site_data.get("measurements", {}):
            if network not in networks:
                networks.append(network)

    rows = []
    mismatches = []
    for site in SITES:
        site_data = data.get(site, {})
        _, _, primary = _pick_primary_measurement(site_data)
        chain = primary.get("chain", []) or [site]
        final_name = chain[-1]
        chain_length = max(0, len(chain) - 1)
        final_zone = _last_two_labels(final_name)
        manual = _manual_third_party(site, final_name)
        rule = _rule_third_party(site, final_name)
        verdict = "correct" if manual == rule else "WRONG"
        if manual != rule:
            mismatches.append((site, final_name, manual, rule))
        rows.append((site, chain_length, final_zone,
                     "yes" if manual else "no",
                     ("third-party" if rule else "first-party") + f" ({verdict})"))

    cdn_sites = [site for site in SITES if site not in NON_CDN_SITES]
    steered_sites = [site for site in cdn_sites if _steered(data.get(site, {}))]

    capture = _analyse_capture()

    lines = []
    lines.append("# DNS steering report")
    lines.append("")
    lines.append("## Method and third-party rule")
    lines.append("")
    lines.append(
        "My simple rule compares only the last two labels of the original site and the "
        "final CNAME target. If they differ, the rule says third-party; if they match, "
        "it says first-party. I then checked that rule against organisational ownership "
        "and recognizable CDN provider domains, because DNS names alone do not prove ownership."
    )
    lines.append("")
    lines.append("## Site table")
    lines.append("")
    lines.append("| site | chain length | final zone | third party? | rule verdict |")
    lines.append("|---|---:|---|---|---|")
    for row in rows:
        lines.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |")

    lines.append("")
    lines.append("## Resolver/network steering")
    lines.append("")
    network_text = ", ".join(networks) if networks else "no labelled network"
    lines.append(f"Networks measured: **{network_text}**.")
    lines.append(
        f"**{len(steered_sites)} of {len(cdn_sites)} CDN-hosted sites answered differently "
        f"to a different resolver or network.**"
    )
    if steered_sites:
        lines.append("Different address sets were observed for: " + ", ".join(steered_sites) + ".")
    else:
        lines.append(
            "No different address sets were observed in this run; that does not by itself "
            "disprove steering because public resolvers may reach similar CDN mapping points."
        )

    lines.append("")
    lines.append("## A rule that was wrong")
    lines.append("")
    if mismatches:
        site, final_name, manual, rule = mismatches[0]
        lines.append(
            f"The simple last-two-label rule was wrong for **{site}** (final target "
            f"`{final_name}`). The rule called it "
            f"**{'third-party' if rule else 'first-party'}**, while the ownership/provider "
            f"check called it **{'third-party' if manual else 'first-party'}**. "
            "This shows that domain-label equality is not the same thing as organisational ownership."
        )
    else:
        lines.append(
            "The run did not expose a mismatch automatically. The rule is still structurally "
            "unsafe: for example, Wikipedia and Wikimedia are the same organisation even though "
            "`wikipedia.org` and `wikimedia.org` have different last-two-label domains, and "
            "multi-label public suffixes such as `co.uk` also break naive label logic."
        )

    lines.append("")
    lines.append("## Part A: Wireshark evidence")
    lines.append("")
    lines.append(
        f"Matching query/response example: query packet **{capture['query_packet']}**, "
        f"response packet **{capture['response_packet']}**, transaction ID "
        f"**{capture['transaction_id']}**."
    )
    lines.append(
        f"Delegation response packet: **{capture['delegation_packet']}**. "
        f"Answer response packet: **{capture['answer_packet']}**."
    )
    lines.append(
        f"Largest DNS response: packet **{capture['largest_packet']}**, "
        f"**{capture['largest_bytes']} bytes**. {capture['largest_reason']}"
    )
    if not capture["available"]:
        lines.append(
            "Run this report again inside the course container after saving `out/dns.pcapng` "
            "so tshark can fill these packet/byte fields automatically."
        )

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {REPORT_PATH}")
    print(f"Steering: {len(steered_sites)}/{len(cdn_sites)} CDN-hosted sites")
    if len(networks) < 2:
        print("WARNING: only one network label is present. Collect again from a second network.")
    if not capture["available"]:
        print("WARNING: dns.pcapng/tshark unavailable; Part A report fields are incomplete.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--collect", action="store_true")
    p.add_argument("--report", action="store_true")
    p.add_argument("--network", default="network1",
                   help="label for this vantage point, e.g. home-wifi or phone-hotspot")
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.collect:
        collect(a.network)
    elif a.report:
        report()
    else:
        p.print_help()
