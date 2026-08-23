---
name: Egress Lockdown
slug: egress-lockdown
family: 15-security
category: Security
aliases: [Default-Deny Egress, Network Egress Policy, FQDN-Based Egress Control]
first_described: "Kubernetes' own NetworkPolicy resource and Cilium's own toFQDNs rule, current documentation"
maturity: established
related: [lethal-trifecta-threat-model]
incompatible_with: []
verified: 2026-08-23
---

# Egress Lockdown

## 1. Name, aliases, and lineage

Egress lockdown restricts what a workload is allowed to connect OUT to, on
the network, so a compromised or misused process cannot freely reach an
arbitrary destination.

This entry sources it directly from two current, live implementations.
Kubernetes' own default egress behaviour, fetched live. "by default, a pod
is non-isolated for egress; all outbound connections are allowed. A pod
becomes isolated for egress if there is any NetworkPolicy that both selects
the pod and has 'Egress' in its policyTypes" (Kubernetes, "Network
Policies," Kubernetes documentation,
https://kubernetes.io/docs/concepts/services-networking/network-policies/,
verified 2026-08-23). Cilium's own FQDN-based egress mechanism, fetched
live. "for a given domain name, IPs from responses to all pods managed by
a Cilium instance are allowed by policy (respecting TTLs)" (Cilium, "Layer
7 Protocol Visibility," Cilium documentation,
https://docs.cilium.io/en/stable/security/policy/layer7/, verified
2026-08-23).

## 2. Problem and context

A workload that can reach any destination on the network can also be
misused to reach an attacker's destination, whether through a genuine
compromise or, for an LLM-driven agent, through a prompt injection that
steers it toward an exfiltration channel. This entry's own already
published Lethal Trifecta Threat Model entry names one of its three
required conditions directly as the presence of "the ability to
externally communicate in a way that could exfiltrate this data," so
removing or bounding that ability is a direct mitigation for that named
risk.

## 3. Forces

The tension named directly in the fetched sources is between reachability
by IP address and reachability by name. Kubernetes' own base mechanism
targets IP ranges. "the egress list of applicable NetworkPolicies are
permitted" for traffic "to" an ipBlock CIDR (Kubernetes, "Network
Policies," verified 2026-08-23), but many legitimate destinations, cloud
APIs, third-party services, resolve to IP addresses that change over
time, and a policy scoped only to a CIDR block breaks the moment the
provider's IP changes. Cilium's own text names the mechanism it built to
resolve this directly, a name-based rule rather than an address-based
one, quoted in full under dimension 1 and 6.

## 4. Applicability and non-applicability

The fetched sources name a concrete, structural non-applicability case
directly. "creating a NetworkPolicy resource without a controller that
implements it will have no effect" (Kubernetes, "Network Policies,"
verified 2026-08-23), a NetworkPolicy object alone enforces nothing
without a compatible network plugin actually reading and applying it, and
Cilium's own FQDN rule carries its own named dependency. "only IPs in
intercepted DNS responses to an application will be allowed" and this
"security model assumes that the intercepted DNS responses come from
trusted cluster DNS servers" (Cilium, "Layer 7 Protocol Visibility,"
verified 2026-08-23), so the mechanism does not apply where DNS traffic
itself cannot be intercepted and trusted.

## 5. Structure

Kubernetes' own text names the default-deny structural shape directly.
"when isolated for egress, the only allowed connections from the pod are
those matching an allowed egress rule" (Kubernetes, "Network Policies,"
verified 2026-08-23), an allowlist rather than a blocklist. Cilium's own
FQDN rule structure names its two match forms directly, matchName for an
exact domain and matchPattern for a wildcard, per the quoted YAML under
dimension 6.

## 6. ASCII structure diagram

```
  Default-deny egress, IP-based:

  +--------+     +-------------------+     +---------------------+
  | pod    | --> | NetworkPolicy      | --> | allowed ipBlock CIDR  |
  | role db|     | egress policyType  |     | only, all else denied |
  +--------+     +-------------------+     +---------------------+

  FQDN-based egress, Cilium:

  +--------+    +----------------+    +-------------------------+
  | pod    | -> | toFQDNs rule   | -> | matchName: cilium.io      |
  |        |    | DNS-aware      |    | matchPattern: *.sub.cilium.io |
  +--------+    +----------------+    +-------------------------+

  the DNS answer's IPs, not just a fixed CIDR, become the allowed set,
  per dimension 3 and 5.
```

## 7. Dynamics

Kubernetes' own text names the evaluation order directly. "network
policies do not conflict, they are additive... thus, order of evaluation
does not affect the policy result" (Kubernetes, "Network Policies,"
verified 2026-08-23), and reply traffic on an already-allowed connection
is "implicitly allowed" (same source), so the runtime dynamic only ever
widens what a specific already-permitted flow can do in its return
direction, never a separate new outbound flow. Cilium's own FQDN dynamic
resolves at DNS-query time. the pod's own DNS lookup is what populates the
currently-allowed IP set for a matchName, per dimension 1 and 3, so the
allowed destinations track the name's current resolution rather than a
value fixed at policy-authoring time.

## 8. Implementation variants

This entry confirmed two genuinely distinct implementation variants
directly. Kubernetes' own native NetworkPolicy object, IP and CIDR based,
requiring a compatible CNI plugin to enforce it, naming "Antrea," "Calico,"
"Cilium," and "Kube-router" as real, current providers (Kubernetes,
"Network Policies," verified 2026-08-23). Cilium's own toFQDNs extension
on top of that same policy model, name based rather than address based,
per dimension 1, 5, and 6.

## 9. Known production uses

Kubernetes' NetworkPolicy resource and Cilium's own DNS-aware egress
policy are each real, currently shipping, widely deployed open-source
mechanisms, confirmed directly against each project's own live
documentation under dimensions 1, 5, and 8.

## 10. Consequences

The benefit is stated directly, already implied under dimension 2 and 3.
a workload whose outbound reach is bounded to a named allowlist cannot be
steered toward an arbitrary attacker destination, even if its own logic or
its own prompt is compromised, per the Lethal Trifecta Threat Model
cross-reference. the cost is the named structural dependency under
dimension 4, the lockdown enforces nothing without a compatible plugin
actually installed and reading the policy object, and a wildcard FQDN rule
depends on DNS interception actually being trusted, per the same
dimension.

## 11. Failure modes and misuse

The sharpest, most directly sourced failure mode is the silent no-op named
in dimension 4 verbatim. a NetworkPolicy object that exists in the cluster
but has no compatible controller reading it changes nothing, which reads,
to an operator inspecting only the policy YAML, as if egress were already
locked down when it is not.

## 12. Trade-off matrix

| Dimension | Egress lockdown, default-deny | No egress policy, open by default |
|---|---|---|
| Default reachability | Deny, allowlist only, dimension 3 and 5 | Any destination, unrestricted |
| Cloud service IPs that change | Handled via FQDN rules, dimension 3 and 6 | Not applicable, no restriction to break |
| Enforcement dependency | Requires a compatible CNI plugin, dimension 4 | None, no enforcement needed |
| Exfiltration risk after a compromise | Bounded to the allowed set, dimension 10 | Unbounded |
| Operational cost | Maintaining an explicit allowlist | None |

## 13. Related and incompatible patterns

This entry cross-references the already-published Lethal Trifecta Threat
Model entry directly, per dimension 2 and 10, as the risk model this
mechanism is one concrete way to reduce, bounding the third named
condition (the ability to externally communicate) rather than removing
private data access or untrusted content exposure.

## 14. Refactoring path in and out

Kubernetes' own text names the concrete lever for adding this control
directly, already quoted in dimension 5, applying a NetworkPolicy object
with Egress in its policyTypes and an explicit egress allow list. Cilium's
own equivalent lever, per dimension 6, is adding a toFQDNs rule alongside
or instead of a CIDR-based rule, neither of which the fetched sources
describe as a staged migration, both are direct policy additions.

## 15. Testing and verification

This entry explicitly checked the fetched sources for a documented test
methodology specific to egress-policy correctness and did not find one
described as a formal process. the closest verifiable behavior is
Kubernetes' own stated default, per dimension 3, which a test would
exercise by confirming a pod with an applied egress policy can reach only
the allowed destinations and is denied everything else, and by confirming
a toFQDNs rule permits the named domain's currently resolved IPs.

## 16. Observability signals

This entry explicitly checked the fetched sources for a named metric or
dashboard specific to egress-policy health and did not find one described
on the specific pages fetched. the closest directly sourced signal is
whether a NetworkPolicy object has a compatible controller actually
enforcing it, per dimension 4 and 11, which an operator would need to
confirm out of band, since the policy object alone gives no signal that
it is being honored.

## 17. Security and privacy implications

Bounding a workload's outbound reach is itself the security control this
entry describes, per dimension 2 and 10, directly reducing the blast
radius of a compromise or a prompt injection by removing the destinations
an attacker could otherwise reach for exfiltration.

## 18. References

1. Kubernetes, "Network Policies," Kubernetes documentation,
   https://kubernetes.io/docs/concepts/services-networking/network-policies/,
   verified 2026-08-23.
2. Cilium, "Security," Cilium documentation,
   https://docs.cilium.io/en/stable/security/policy/index.html, verified
   2026-08-23.
3. Cilium, "Layer 7 Protocol Visibility," Cilium documentation,
   https://docs.cilium.io/en/stable/security/policy/layer7/, verified
   2026-08-23.

## Code

TypeScript, Python, and Go implementations of a minimal FQDN-based egress
allowlist checker following the mechanism from dimensions 3 and 6,
matching a requested destination against a set of allowed exact names and
single-label wildcard patterns before permitting the connection.

```typescript
function matchesPattern(host: string, pattern: string): boolean {
  const hostParts = host.split(".");
  const patternParts = pattern.split(".");
  if (hostParts.length !== patternParts.length) {
    return false;
  }
  for (let i = 0; i < patternParts.length; i++) {
    if (patternParts[i] !== "*" && patternParts[i] !== hostParts[i]) {
      return false;
    }
  }
  return true;
}

class EgressAllowlist {
  private names: Set<string> = new Set();
  private patterns: string[] = [];

  allowName(name: string): void {
    this.names.add(name);
  }

  allowPattern(pattern: string): void {
    this.patterns.push(pattern);
  }

  isAllowed(host: string): boolean {
    if (this.names.has(host)) {
      return true;
    }
    return this.patterns.some((pattern) => matchesPattern(host, pattern));
  }
}
```

```python
from typing import List, Set


def matches_pattern(host: str, pattern: str) -> bool:
    host_parts = host.split(".")
    pattern_parts = pattern.split(".")
    if len(host_parts) != len(pattern_parts):
        return False
    for host_part, pattern_part in zip(host_parts, pattern_parts):
        if pattern_part != "*" and pattern_part != host_part:
            return False
    return True


class EgressAllowlist:
    def __init__(self) -> None:
        self._names: Set[str] = set()
        self._patterns: List[str] = []

    def allow_name(self, name: str) -> None:
        self._names.add(name)

    def allow_pattern(self, pattern: str) -> None:
        self._patterns.append(pattern)

    def is_allowed(self, host: str) -> bool:
        if host in self._names:
            return True
        return any(matches_pattern(host, pattern) for pattern in self._patterns)
```

```go
package egress

import "strings"

func matchesPattern(host string, pattern string) bool {
	hostParts := strings.Split(host, ".")
	patternParts := strings.Split(pattern, ".")
	if len(hostParts) != len(patternParts) {
		return false
	}
	for i, part := range patternParts {
		if part != "*" && part != hostParts[i] {
			return false
		}
	}
	return true
}

type Allowlist struct {
	names    map[string]bool
	patterns []string
}

func NewAllowlist() *Allowlist {
	return &Allowlist{names: make(map[string]bool)}
}

func (a *Allowlist) AllowName(name string) {
	a.names[name] = true
}

func (a *Allowlist) AllowPattern(pattern string) {
	a.patterns = append(a.patterns, pattern)
}

func (a *Allowlist) IsAllowed(host string) bool {
	if a.names[host] {
		return true
	}
	for _, pattern := range a.patterns {
		if matchesPattern(host, pattern) {
			return true
		}
	}
	return false
}
```
