#!/usr/bin/env python3
"""Week 4 · Task 3 — Beat the fixed window.

Textbook §3.7.

`FixedWindow` is a sender that never adapts. It picks a window and keeps it,
forever, no matter what the network says back. It is not a strawman: it is what
you get if you skip congestion control entirely, and it was the internet's
actual failure mode in October 1986.

Write `YourControl` and beat it on the harness:

    python3 bench.py
    python3 bench.py --yours

The interface is two events and one number:

    .window        how many packets you are willing to have in flight
    .on_ack()      one packet made it there and back
    .on_loss()     a packet was dropped, or timed out waiting for its ACK

That is all the information a real TCP sender has. It cannot see the queue,
it cannot see the link rate, and neither can you. You infer them from these
two events, which is the entire idea of §3.7.
"""


class FixedWindow:
    """Send 64 packets at a time and never listen."""

    def __init__(self):
        self.window = 64

    def on_ack(self):
        pass

    def on_loss(self):
        pass


class YourControl:
    """TCP-style congestion control using slow start and AIMD."""

    def __init__(self):
        self.window = 1.0
        self.ssthresh = 20.0

    def on_ack(self):
        if self.window < self.ssthresh:
            self.window += 1.0
        else:
            self.window += 1.0 / self.window

        self.window = min(self.window, 24.0)

    def on_loss(self):
        self.ssthresh = max(2.0, self.window * 0.70)
        self.window = self.ssthresh
