\# Week 5 Observations



\## Task 1 — CIDR and Forwarding



For a /31 subnet, both addresses are usable under the point-to-point addressing convention. For a /32 subnet, the single address represents one host.



The destination 10.20.30.70 matches 10.0.0.0/8, 10.20.0.0/16, 10.20.30.0/24, and 10.20.30.64/26. The /26 route wins because it has the longest matching prefix. Duplicate routes are rejected.



\## Task 2 — IP Address, NAT, and DHCP



My home Wi-Fi used 172.30.1.43/24 with public address 14.37.156.17, while my phone hotspot used 10.117.16.59/24 with public address 211.36.143.23. Both connections show evidence of at least one NAT layer, but the exact number of layers cannot be confirmed without checking upstream addresses.



Both the private and public addresses changed between networks, while the /24 subnet mask remained the same. The different DHCP servers and internet connections explain these changes.



DHCP Discover used source address 0.0.0.0 and destination address 255.255.255.255 because the client had not yet obtained an IPv4 address and needed to discover a DHCP server.



\## Task 3 — Fast Longest-Prefix Match



I implemented longest-prefix matching using hash tables grouped by prefix length. The structure requires O(N) storage and checks at most 33 prefix lengths per lookup, giving O(32) lookup time for IPv4 regardless of the number of routes.



The benchmark returned zero incorrect answers and approximately 813 times faster lookup than the linear baseline. Hardware routers can use trie-based structures for efficient bitwise prefix matching.

