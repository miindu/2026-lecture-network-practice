# DNS steering report

## Method and third-party rule

My simple rule compares only the last two labels of the original site and the final CNAME target. If they differ, the rule says third-party; if they match, it says first-party. I then checked that rule against organisational ownership and recognizable CDN provider domains, because DNS names alone do not prove ownership.

## Site table

| site | chain length | final zone | third party? | rule verdict |
|---|---:|---|---|---|
| www.microsoft.com | 2 | akamaiedge.net | yes | third-party (correct) |
| www.netflix.com | 1 | netflix.com | no | first-party (correct) |
| www.adobe.com | 2 | akamai.net | yes | third-party (correct) |
| www.cnn.com | 1 | fastly.net | yes | third-party (correct) |
| www.apple.com | 3 | akamaiedge.net | yes | third-party (correct) |
| www.korea.ac.kr | 0 | ac.kr | no | first-party (correct) |
| www.stanford.edu | 1 | netlifyglobalcdn.com | yes | third-party (correct) |
| www.bbc.co.uk | 2 | fastly.net | yes | third-party (correct) |
| www.spotify.com | 1 | fastly.net | yes | third-party (correct) |
| www.github.com | 1 | github.com | no | first-party (correct) |
| www.wikipedia.org | 1 | wikimedia.org | no | third-party (WRONG) |
| www.nytimes.com | 3 | fastly.net | yes | third-party (correct) |

## Resolver/network steering

Networks measured: **home-wifi, phone-hotspot**.
**8 of 11 CDN-hosted sites answered differently to a different resolver or network.**
Different address sets were observed for: www.microsoft.com, www.adobe.com, www.cnn.com, www.apple.com, www.bbc.co.uk, www.spotify.com, www.github.com, www.nytimes.com.

## A rule that was wrong

The simple last-two-label rule was wrong for **www.wikipedia.org** (final target `dyna.wikimedia.org`). The rule called it **third-party**, while the ownership/provider check called it **first-party**. This shows that domain-label equality is not the same thing as organisational ownership.

## Part A: Wireshark evidence

Matching query/response example: query packet **1**, response packet **2**, transaction ID **0xddcd**.
Delegation response packet: **2** (answer=0, authority=6, additional=11).
Final answer response packet: **6**.
Largest DNS response: packet **2**, **394 bytes**. It carried many authority/additional records, including the `.kr` NS delegation and glue addresses.
