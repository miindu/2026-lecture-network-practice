\# Week 5 · Task 2 — IP Address, NAT, and DHCP Report



\## Part A. My Network Address



\### A1. Interface Address and Subnet Mask



On my home Wi-Fi, my computer was assigned the private IPv4 address `172.30.1.43` with subnet mask `255.255.255.0` (`/24`).



\### A2. Subnet Range



For `172.30.1.43/24`, the first 24 bits identify the network and the remaining 8 bits identify hosts.



\- Network address: `172.30.1.0`

\- First usable address: `172.30.1.1`

\- Last usable address: `172.30.1.254`

\- Broadcast address: `172.30.1.255`



The subnet contains 256 total addresses, of which 254 are normally usable host addresses. These values can be checked using the `network\_range` function implemented in Task 1.



\### A3. Default Gateway



The default gateway was `172.30.1.254`, which is within the usable address range of `172.30.1.1` through `172.30.1.254`.



The gateway must be reachable on the local network so that the computer can forward packets destined for other networks to the router.



\### A4. Public IP Address



The external address-checking service reported `14.37.156.17`.



This differs from the computer's private address `172.30.1.43`.



\### A5. Private Addresses and NAT



`172.30.1.43` belongs to the RFC 1918 private range `172.16.0.0/12`. The observed external address `14.37.156.17` is a public IPv4 address.



Because the local private address and externally observed public address differ, the connection uses at least one layer of NAT.



The collected data does not establish whether there is exactly one NAT layer or more than one. To distinguish them, I would inspect the router's WAN address and compare it with the externally observed address. If the router has a public WAN address matching the external address, a single NAT layer is likely. If the router's WAN address is private or belongs to the shared address range `100.64.0.0/10`, another upstream translation layer may exist.



\## Part B. Comparing Two Networks



| Item | Home Wi-Fi | Phone Hotspot |

|---|---|---|

| Private IPv4 address | 172.30.1.43 | 10.117.16.59 |

| Subnet mask | 255.255.255.0 | 255.255.255.0 |

| Network | 172.30.1.0/24 | 10.117.16.0/24 |

| Default gateway | 172.30.1.254 | 10.117.16.62 |

| Public IPv4 address | 14.37.156.17 | 211.36.143.23 |



\### B3. What Changed and Why?



Both the private and public IPv4 addresses changed when switching from home Wi-Fi to the phone hotspot.



The private address changed because the two networks use different local address ranges and different DHCP servers. The home network assigned an address in `172.30.1.0/24`, while the hotspot assigned an address in `10.117.16.0/24`.



The public address changed because the traffic was routed through a different internet connection. The home connection used `14.37.156.17`, while the mobile connection was observed as `211.36.143.23`.



The subnet mask remained `255.255.255.0` on both networks. Both networks assigned RFC 1918 private addresses.



\## Part C. DHCP Packet Capture



The Wireshark capture includes DHCP Discover, Offer, Request, and ACK messages.



\### C2. DHCP Discover Source and Destination



\- Source IP address: `0.0.0.0`

\- Destination IP address: `255.255.255.255`



The source address is `0.0.0.0` because the DHCP client has not yet obtained a usable IPv4 address.



The destination is the limited broadcast address `255.255.255.255` because the client does not initially know the DHCP server's address and must discover an available server on the local network.



\### C3. DHCP Lease Time



The Windows network configuration recorded a lease starting at approximately 23:35:34 and expiring at approximately 00:35:36 on the home Wi-Fi, indicating a lease of approximately one hour.



The exact lease time offered in the DHCP packet should be verified using DHCP Option 51 in the captured Offer or ACK message.



\### C4. Why DHCP ACK May Be Unicast



At the beginning of DHCP, the client does not yet have a configured IP address, so Discover uses broadcast.



Later in the exchange, the server has selected an address for the client and knows the client's hardware address. Depending on the client's broadcast flag and the server's behavior, the ACK may be sent as a unicast packet instead of a broadcast packet.



In my capture, the ACK was sent from `172.30.1.254` to `255.255.255.255`, so this particular ACK was broadcast.

