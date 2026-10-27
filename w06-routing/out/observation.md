

\# Week 6 - Routing Observations



\## Task 1 - Link-State Routing



Dijkstra's algorithm computes the shortest path from a source router to each reachable destination.



In the provided topology, the shortest path from u to w has cost 3, using u -> x -> y -> w. Therefore, the forwarding table at u selects x as the first hop toward w.



When link u-x fails, the forwarding table changes. The first hops toward w, x, y, and z change from x to v.



\## Task 2 - Part A: Traceroute



Three destinations were measured from a Windows computer using tracert.



\### A2 - Domestic route



The first hop toward www.korea.ac.kr was 172.30.1.254, a private network gateway.



The last responding router was 211.44.125.216 at hop 8. Subsequent hops did not respond.



The measurement was not confirmed to be from the campus network, so the campus exit hop cannot be identified reliably.



\### A3 - Overseas route



www.stanford.edu resolved to 15.197.167.90, associated with AWS Global Accelerator.



The destination was reached at hop 17, with RTT measurements of 18 ms, 7 ms, and 8 ms.



No clear transoceanic latency jump was observed. The traceroute appears to terminate at a nearby accelerator endpoint rather than demonstrating the route to a physical server in California.



Therefore, the ocean-crossing hop and submarine cable could not be determined from this measurement.



\### A4 - Anycast



The traceroute to 1.1.1.1 reached the destination at hop 10.



The final RTT measurements were 14 ms, 9 ms, and 10 ms.



The relatively low latency is consistent with reaching a nearby Cloudflare anycast endpoint. The precise physical location cannot be determined from hop count alone.



\### A5 - Missing hop responses



Asterisks in traceroute can occur for different reasons:



1\. Routers may filter or rate-limit ICMP Time Exceeded responses.

2\. Probe packets or responses may be lost due to congestion or network problems.



A missing response does not necessarily mean that forwarding has stopped. Later hops sometimes responded after earlier hops timed out.



\## Task 2 - Part B: OSPF Link Failure and Restoration

Three FRRouting 9.1.0 routers (r1, r2, r3) were started using Docker Compose. OSPF neighbor relationships were confirmed to be in the Full state.

### B2 - Routes Learned Through OSPF

Before the failure, r1 was directly connected to 172.18.0.0/16 through eth0 and 172.19.0.0/16 through eth1, each with an OSPF cost of 10.

The network 172.20.0.0/16 was reached through either r2 or r3, with a total cost of 20. Two equal-cost next hops were present.

### B3 - Link Failure

The r1-r2 link was disabled by bringing down eth1 on r1.

After the failure, r1 reached 172.19.0.0/16 through r3 at 172.18.0.3 via eth0, with an OSPF cost of 30.

The route to 172.20.0.0/16 continued through r3, with a cost of 20. The alternative next hop through r2 disappeared.

### B4 - Reconvergence Time

The scenario script detected a change in the OSPF routing table after 2 seconds.

This value was measured by polling the routing table once per second, so it is an approximate detection time rather than a precise protocol convergence timestamp.

### B5 - Link Restoration

After eth1 was brought back up and 30 seconds were allowed for recovery, r1 again showed 172.19.0.0/16 as directly connected through eth1 with cost 10.

The two equal-cost paths toward 172.20.0.0/16 were also restored.

The exact restoration convergence time was not measured. Therefore, a numerical comparison between failure and restoration times cannot be made.

## Task 2 - Part C: OSPF Link Cost Change

The OSPF cost of r1's eth0 interface was increased from 10 to 100.

After the change, r1 reached 172.18.0.0/16 through r2 at 172.19.0.2 via eth1, with a cost of 30, instead of selecting the expensive direct OSPF path.

The route toward 172.20.0.0/16 used r2 via eth1, with cost 20, rather than two equal-cost next hops.

This confirms that OSPF selects routes based on accumulated path cost rather than simply the number of hops.

The updated routing table was checked after a 15-second wait. Because the precise moment of convergence was not measured, the cost-change convergence time cannot be quantitatively compared with the 2-second link-failure measurement.

## Task 3 - SPF Optimization



The baseline performed 1001 full SPF runs for 1000 link-change events.



The implemented router performed 924 full SPF runs and produced zero incorrect forwarding tables.



This avoided approximately 8% of full SPF runs.



The optimized implementation had a longer measured wall-clock time than the baseline because it constructs graph signatures and manages a cache. This demonstrates that reducing SPF calls does not necessarily reduce total execution time when the optimization itself introduces overhead.



