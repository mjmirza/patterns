---
name: Byzantine Fault Tolerance
slug: byzantine-fault-tolerance
family: 12-data-storage
category: Data and Storage
aliases: [BFT, Byzantine Generals Problem, PBFT]
first_described: "Lamport, Shostak, Pease, 1982, 'The Byzantine Generals Problem'"
maturity: canonical
related: []
incompatible_with: []
verified: 2026-08-23
---

# Byzantine Fault Tolerance

## 1. Name, aliases, and lineage

Byzantine fault tolerance is a distributed system's ability to keep
operating correctly even when some of its nodes fail in an arbitrary,
possibly malicious way, sending contradictory information to different
observers, rather than simply crashing or going silent.

This entry sources it directly from Wikipedia's own current article,
fetched live. "a Byzantine fault is a condition of a system, particularly
a distributed computing system, where a fault occurs such that different
symptoms are presented to different observers" (Wikipedia, "Byzantine
fault," https://en.wikipedia.org/wiki/Byzantine_fault, verified
2026-08-23). the problem was "conceived and formalized by Robert Shostak,
who dubbed it the interactive consistency problem" in 1978, and Leslie
Lamport "devised a colorful allegory in which a group of army generals
formulate a plan for attacking a city," with the name eventually settling
on "Byzantine" (same source). the original paper itself, hosted directly by
Lamport, is titled "The Byzantine Generals Problem" (Leslie Lamport, Robert
Shostak, Marshall Pease, 1982, https://lamport.azurewebsites.net/pubs/byz.pdf,
verified 2026-08-23).

## 2. Problem and context

A distributed system that assumes a failed node simply stops responding,
a crash fault, is defenseless against a node that instead keeps
responding but lies, sending one answer to one peer and a contradictory
answer to another. the interactive consistency problem, named directly in
dimension 1, is exactly this, how a set of correct nodes can still reach
agreement when some unknown subset of nodes is actively working against
that agreement rather than merely absent.

## 3. Forces

The direct tension is between how many nodes a system can afford to run,
and how many of those nodes can misbehave before agreement becomes
impossible. Wikipedia's own text states the classic quantitative result
directly. "a minimum of 3n+1 are needed" to tolerate n faulty nodes, and
"Marshall Pease generalized the algorithm for any n greater than 0,
proving that 3n+1 is both necessary and sufficient" (Wikipedia, "Byzantine
fault," verified 2026-08-23), the exact node-count cost this fault model
imposes.

## 4. Applicability and non-applicability

Hyperledger Fabric's own current documentation states the direct,
practical applicability boundary between this fault model and the
simpler crash-fault model. "a Byzantine Fault Tolerant (BFT) ordering
service... can withstand not only crash failures, but also a subset of
nodes behaving maliciously," while "Raft is a crash fault tolerant (CFT)
ordering service" that only tolerates a node going silent, not a node that
actively lies (Hyperledger Fabric, "The Ordering Service," Hyperledger
Fabric documentation,
https://hyperledger-fabric.readthedocs.io/en/latest/orderer/ordering_service.html,
verified 2026-08-23). a system that only needs to survive a node crashing
does not need the extra node count and coordination cost Byzantine fault
tolerance imposes, per dimension 3.

## 5. Structure

Wikipedia's own text names the historical progression of the algorithm's
own structure directly, already partially quoted in dimension 3. "Leslie
Lamport later proved the sufficiency of 3n using digital signatures"
(Wikipedia, "Byzantine fault," verified 2026-08-23), a distinct structural
variant from the original signature-free result, trading a cryptographic
signing step for a lower node-count requirement.

## 6. ASCII structure diagram

```
  a crash-fault-tolerant system, per dimension 4:

  node A --+
  node B --+---> agreement (majority of nodes respond,
  node C --+       or stay silent, never lie)

  a Byzantine-fault-tolerant system, tolerating n
  malicious nodes among 3n+1 total, per dimension 3:

  node A (honest)  -----> "value X"  -----+
  node B (honest)  -----> "value X"  -----+---> agreement
  node C (honest)  -----> "value X"  -----+     reached despite
  node D (faulty)  -----> "value Y"  -----+     node D lying
                          to node A,             differently to
                          "value Z"              different peers
                          to node B
```

## 7. Dynamics

Wikipedia's own text names the concrete, high-performance implementation
of this fault model directly. "in 1999, Miguel Castro and Barbara Liskov
introduced the 'Practical Byzantine Fault Tolerance' (PBFT) algorithm,
which provides high-performance Byzantine state machine replication,
processing thousands of requests per second with sub-millisecond
increases in latency" (Wikipedia, "Byzantine fault," verified 2026-08-23),
the first widely cited result showing the fault model could run at
practical, production-relevant speed rather than only as a theoretical
proof of possibility.

## 8. Implementation variants

Hyperledger Fabric's own text names a concrete, modern, named variant
directly, already partially quoted in dimension 4. its BFT ordering
service "uses the SmartBFT protocol" and "can function when up to (but
not including) a third of the orderer nodes are controlled by a malicious
party" (Hyperledger Fabric, "The Ordering Service," verified 2026-08-23),
a direct, contemporary descendant of the same 3n+1-family bound named in
dimension 3, applied to a blockchain ordering service rather than the
original generals allegory.

## 9. Known production uses

Hyperledger Fabric's own BFT ordering service, using the SmartBFT
protocol, is a real, currently shipping production feature, confirmed
directly against the project's own live documentation under dimensions 4
and 8. PBFT itself, per dimension 7, is the foundational algorithm
demonstrating the fault model runs at production-relevant throughput and
latency.

## 10. Consequences

The benefit is stated directly, already implied across dimensions 2 and
4, a system tolerates a subset of its own nodes actively lying, not just
crashing. the cost is stated with equal directness under dimension 3, a
minimum of 3n+1 total nodes to tolerate n faulty ones, meaning Byzantine
fault tolerance costs strictly more nodes and coordination than
crash-fault tolerance for the same fault-tolerance count, per the
Hyperledger Fabric contrast under dimension 4.

## 11. Failure modes and misuse

The clearest, most directly sourced failure mode is running under the
required node count for the fault tolerance a system claims, already
named directly in dimension 3, fewer than 3n+1 total nodes cannot
guarantee agreement in the presence of n Byzantine-faulty nodes, per
Pease's own proven necessity result. a second, distinct misuse is
choosing Byzantine fault tolerance where only crash-fault tolerance was
ever needed, per dimension 4, paying the extra node-count and
coordination cost for a threat model the deployment does not actually
face.

## 12. Trade-off matrix

| Dimension | Byzantine fault tolerance | Crash fault tolerance |
|---|---|---|
| Faults tolerated | Arbitrary, including malicious lying, dimension 2 | Only a node going silent, dimension 4 |
| Minimum total nodes for n faults | 3n+1, dimension 3 | More than half of the nodes suffice, dimension 4 |
| Named production example | Hyperledger Fabric's SmartBFT orderer, dimension 8 | Hyperledger Fabric's Raft orderer, dimension 4 |
| Coordination cost | Higher, dimension 10 | Lower |
| Fault model coverage | Superset of crash-fault tolerance | Narrower |

## 13. Related and incompatible patterns

Raft, already named directly in dimension 4 via Hyperledger Fabric's own
documentation, is the direct, sourced crash-fault-tolerant counterpart
this pattern is contrasted against throughout, the two solving the same
agreement problem under two genuinely different fault models. this entry
explicitly checked the fetched sources for a comparison to Paxos by name
and did not find one drawn directly in the fetched material, and reports
that absence directly rather than asserting a bridge the sources do not
state.

## 14. Refactoring path in and out

Hyperledger Fabric's own documentation names the concrete, practical lever
directly, already quoted in dimension 4 and 8, choosing the BFT ordering
service over the Raft ordering service, or the reverse, is a deployment
configuration choice on that platform, trading node count and
coordination overhead for tolerance against malicious, not just crashed,
nodes.

## 15. Testing and verification

This entry explicitly checked the fetched sources for a documented test
methodology specific to Byzantine fault tolerance and did not find one
described as a formal process beyond the algorithm's own proven
correctness bounds, already named in dimension 3 and 5, Pease's proof of
necessity and sufficiency for 3n+1, and Lamport's proof of sufficiency for
3n with digital signatures. this entry reports those proofs as the
verification method the pattern's own literature provides, a mathematical
guarantee rather than an operational test suite.

## 16. Observability signals

This entry explicitly checked the fetched sources for a named runtime
metric or dashboard specific to Byzantine fault tolerance and did not
find one described. the closest directly sourced signal is PBFT's own
stated performance characteristic, per dimension 7, throughput in
requests per second and latency overhead, which an operator would compare
against the unreplicated baseline to judge the fault-tolerance layer's
own cost.

## 17. Security and privacy implications

This entire pattern IS a security mechanism, already stated in full under
dimensions 2 and 8, tolerating a subset of nodes that actively behave
maliciously, up to but not including one third of the total under the
SmartBFT bound named in dimension 8. Lamport's own later variant, per
dimension 5, adds a cryptographic signing step specifically to lower the
node-count requirement, a direct security-mechanism trade-off, more
cryptographic work per message in exchange for fewer total nodes needed.

## 18. References

1. Wikipedia, "Byzantine fault,"
   https://en.wikipedia.org/wiki/Byzantine_fault, verified 2026-08-23.
2. Leslie Lamport, Robert Shostak, Marshall Pease, "The Byzantine Generals
   Problem," 1982, https://lamport.azurewebsites.net/pubs/byz.pdf,
   verified 2026-08-23.
3. Hyperledger Fabric, "The Ordering Service," Hyperledger Fabric
   documentation,
   https://hyperledger-fabric.readthedocs.io/en/latest/orderer/ordering_service.html,
   verified 2026-08-23.

## Code

TypeScript, Python, and Go implementations of a minimal Byzantine
agreement check following the mechanism from dimensions 3 and 6, counting
distinct reported values across a set of nodes and confirming a
supermajority agrees, following the 3n+1 bound.

```typescript
function byzantineAgreement(reports: string[], faultTolerance: number): string | null {
  const requiredNodes = 3 * faultTolerance + 1;
  if (reports.length < requiredNodes) {
    throw new Error("insufficient nodes for the claimed fault tolerance");
  }
  const counts = new Map<string, number>();
  for (const value of reports) {
    counts.set(value, (counts.get(value) ?? 0) + 1);
  }
  const majorityThreshold = reports.length - faultTolerance;
  for (const [value, count] of counts) {
    if (count >= majorityThreshold) {
      return value;
    }
  }
  return null;
}
```

```python
from collections import Counter
from typing import List, Optional


def byzantine_agreement(reports: List[str], fault_tolerance: int) -> Optional[str]:
    required_nodes = 3 * fault_tolerance + 1
    if len(reports) < required_nodes:
        raise ValueError("insufficient nodes for the claimed fault tolerance")
    counts = Counter(reports)
    majority_threshold = len(reports) - fault_tolerance
    for value, count in counts.items():
        if count >= majority_threshold:
            return value
    return None
```

```go
package byzantine

import "errors"

func ByzantineAgreement(reports []string, faultTolerance int) (string, error) {
	requiredNodes := 3*faultTolerance + 1
	if len(reports) < requiredNodes {
		return "", errors.New("insufficient nodes for the claimed fault tolerance")
	}
	counts := make(map[string]int)
	for _, value := range reports {
		counts[value]++
	}
	majorityThreshold := len(reports) - faultTolerance
	for value, count := range counts {
		if count >= majorityThreshold {
			return value, nil
		}
	}
	return "", errors.New("no agreement reached")
}
```
