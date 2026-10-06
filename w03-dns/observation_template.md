# Week 3 Observation

## Task 1
Root server는 최종 IP를 직접 관리하는 서버가 아니라 다음 계층(TLD)의 NS를 알려 주는 역할을 하므로, 최종 A 레코드 대신 delegation을 돌려줬다. Glue가 없는 delegation에서는 NS 이름 자체를 root부터 다시 resolve해서 그 NS의 IP를 얻은 뒤 원래 질의를 계속했다.
`python3 task1_resolve.py www.korea.ac.kr` 결과에서 총 **[HOPS]개 서버**를 물었고, no-glue 때문에 **[EXTRA]개 추가 서버 질의**가 필요했다. 평소 노트북은 recursive resolver에 한 번만 요청하지만, 여기서는 그 resolver가 대신 하던 과정을 직접 수행했다.

## Task 2
캡처에서 delegation 응답은 Answer가 0이고 Authority에 NS가 있었고, 최종 answer 응답은 Answer section에 A 레코드가 있었다. 내 third-party 규칙은 원래 이름과 최종 CNAME의 마지막 두 label이 다르면 third-party로 보는 것이었는데, 이 규칙은 **[REPORT에서 WRONG으로 나온 사이트]**에서 틀렸다.
두 네트워크와 여러 resolver를 비교한 결과 CDN-hosted 사이트 **[X]/[N]개**에서 서로 다른 address set이 관찰됐다. 따라서 이 결과는 DNS steering 주장을 **[어느 정도 지지한다 / 강하게 지지하지 못한다]**고 판단했다.

## Task 3
BaselineCache는 실제 TTL을 버리고 모든 레코드를 60초로 취급해서, TTL이 60초보다 짧은 레코드는 stale로 제공하고 TTL이 긴 레코드는 너무 일찍 버려 불필요한 upstream query를 만든다. 또한 list 선형 탐색보다 dict 조회가 더 적절하다.
이 workload에서 올바른 캐시의 floor는 **275 upstream queries**다. 각 이름은 최초 요청에서 반드시 upstream을 가야 하고, 그 뒤에도 그 이름의 TTL이 끝난 뒤 처음 오는 요청은 새 값을 얻기 위해 반드시 upstream을 가야 하므로 이 횟수들은 피할 수 없으며, TTL을 정확히 지키는 구현이 275를 달성하므로 그보다 낮출 수 없다.
