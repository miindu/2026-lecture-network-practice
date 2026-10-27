

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



\## Task 2 - Parts B and C: OSPF Experiment



The local OSPF experiment was not performed.



Docker Desktop was unavailable, and WSL 2 could not start because firmware virtualization was reported as disabled. The visible BIOS settings did not provide an identifiable virtualization option.



Consequently, routing tables before and after a link failure and actual reconvergence times were not measured.



OSPF link failure detection may depend on the hello and dead intervals when no faster failure signal is available. Link restoration is different because a new neighbor adjacency must be established.



A link-cost change does not require physical link failure detection. Its new routing information can be propagated through LSAs, followed by SPF recalculation. However, actual comparative timings were not measured.



These explanations are theoretical and do not replace the required measurements.



\## Task 3 - SPF Optimization



The baseline performed 1001 full SPF runs for 1000 link-change events.



The implemented router performed 924 full SPF runs and produced zero incorrect forwarding tables.



This avoided approximately 8% of full SPF runs.



The optimized implementation had a longer measured wall-clock time than the baseline because it constructs graph signatures and manages a cache. This demonstrates that reducing SPF calls does not necessarily reduce total execution time when the optimization itself introduces overhead.



