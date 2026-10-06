\# Week 3 DNS Observations



\## Task 1

The root server did not return the final address because DNS follows delegation; my resolver followed root -> TLD -> authoritative servers. For www.korea.ac.kr, it started at root server 198.41.0.4 and reached 163.152.6.10.

This lookup had no missing-glue event, but when glue is absent my resolver resolves the NS hostname first and then continues. CDN names such as www.microsoft.com can legitimately return a different address from dig because different resolution paths may select different edge servers.



\## Task 2

My third-party rule compares the last two labels, but it misclassified www.wikipedia.org because wikipedia.org and wikimedia.org differ even though they belong to the same organisation.

Across home Wi-Fi and a phone hotspot using the system, Google, and Quad9 resolvers, 8 of 11 CDN-hosted sites returned different address sets, providing evidence of DNS steering.



\## Task 3

The baseline ignores the real TTL, causing stale answers for short TTLs and unnecessary upstream queries for long TTLs. My TTL-aware cache produced 275 upstream queries and 0 stale answers.

275 is the lower bound because every first lookup and the first lookup after each TTL expiration must contact upstream; fewer queries would require using expired or previously unfetched information

