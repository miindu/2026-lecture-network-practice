#!/usr/bin/env python3
"""Week 3 · Task 3 — Beat the baseline cache.

Textbook §2.4.2 (caching) and §2.4.3 (TTL).
"""


class BaselineCache:
    """The deliberately bad baseline supplied with the lab."""

    FIXED_LIFETIME = 60

    def __init__(self, upstream):
        self.upstream = upstream
        self.entries = []

    def lookup(self, name, now):
        for entry in self.entries:
            if entry[0] == name:
                if now - entry[2] < self.FIXED_LIFETIME:
                    return entry[1]
                self.entries.remove(entry)
                break
        address, ttl = self.upstream(name)
        self.entries.append([name, address, now])
        return address

    def stats(self):
        return {"entries": len(self.entries)}


class YourCache:
    """TTL-respecting DNS cache with O(1)-average lookup by name."""

    def __init__(self, upstream):
        self.upstream = upstream
        # name -> (address, expires_at)
        self.entries = {}

    def lookup(self, name, now):
        entry = self.entries.get(name)
        if entry is not None:
            address, expires_at = entry
            if now < expires_at:
                return address
            del self.entries[name]

        address, ttl = self.upstream(name)
        self.entries[name] = (address, now + ttl)
        return address

    def stats(self):
        return {"entries": len(self.entries)}
