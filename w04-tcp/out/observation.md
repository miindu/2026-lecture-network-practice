Week 4 — TCP Programming Observations



Task 1 — Reliable Delivery



I implemented stop-and-wait with sequence numbers, ACKs, and retransmissions to handle packet loss and duplicates. Both test seeds delivered all 2,000 bytes correctly, despite 40 losses in seed 246 and 29 losses in seed 999. The channel recorded 323 and 299 total sends, including ACKs, compared with a minimum of 250 data packets.



Task 2 — TCP Measurement



In Wireshark, I identified the three-way handshake in packets 263–265, an MSS of 1460 bytes, window scaling of 256, and SACK support. The advertised receive window was 65,280 bytes in packet 270, while packet 269 showed 2,853 bytes in flight, suggesting that the receive window was not limiting the transfer at that moment.



Across five transfers per network, home Wi-Fi achieved a median throughput of 136.03 Mbps and a median handshake time of 10.7 ms, compared with 30.90 Mbps and 32.1 ms on the phone hotspot. The difference may reflect RTT, wireless conditions, and congestion, rather than handshake time alone.



Task 3 — Congestion Control



The fixed-window baseline achieved 986.8 goodput but caused 37.4% packet loss, 2,340 retransmissions, and an average queue of 8.8. My slow-start and AIMD controller, with a window cap of 24, achieved 977.8 goodput (99% of baseline), 0% loss, zero retransmissions, and an average queue of 3.9.



Reducing the loss backoff from 50% to 25% improved goodput but increased the average queue to approximately 5.0, failing the queue requirement. Adding the window cap kept the queue below the limit while preserving high throughput.

