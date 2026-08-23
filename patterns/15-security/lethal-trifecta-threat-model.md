---
name: Lethal Trifecta Threat Model
slug: lethal-trifecta-threat-model
family: 15-security
category: Security
aliases: [The Lethal Trifecta, Trifecta Threat Model for AI Agents]
first_described: "Simon Willison's own blog post naming and defining the three conditions"
maturity: emerging
related: [dual-llm-pattern]
incompatible_with: []
verified: 2026-08-23
---

# Lethal Trifecta Threat Model

## 1. Name, aliases, and lineage

The lethal trifecta names the three conditions that, present together in
one agent, let an attacker steal a person's private data through a prompt
injection, without any single one of the three being dangerous on its own.

This entry sources it directly from Simon Willison's own blog, fetched
live. "if you are a user of LLM systems that use tools... it is critically
important that you understand the risk of combining tools with the
following three characteristics. Failing to understand this can let an
attacker steal your data. The lethal trifecta of capabilities is. access to
your private data, one of the most common purposes of tools in the first
place. exposure to untrusted content, any mechanism by which text, or
images, controlled by a malicious attacker could become available to your
LLM. the ability to externally communicate in a way that could be used to
steal your data" (Simon Willison, "The lethal trifecta for AI agents,"
2025-06-16, https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/,
verified 2026-08-23).

## 2. Problem and context

Willison's own text states why the three conditions matter only in
combination, not individually. an agent with private-data access alone is
merely useful. an agent exposed to untrusted content alone is merely
reading the internet. an agent that can communicate externally alone is
merely doing its job. the danger appears specifically "if you combine
these three factors" (Willison, "Lethal Trifecta," verified 2026-08-23),
because that combination gives an attacker's injected instructions,
smuggled inside the untrusted content, both something worth stealing and a
channel to steal it through.

## 3. Forces

The direct tension the threat model names is between agent usefulness and
agent safety, and each of the three conditions independently makes an
agent MORE useful. private-data access is why the tool exists at all, per
dimension 2. reading untrusted content, web pages, emails, documents, is
how an agent stays informed. external communication is how an agent
reports back or acts on a person's behalf. removing any one of the three
closes the trifecta but also removes real capability, which is the trade
this threat model forces a designer to make explicit.

## 4. Applicability and non-applicability

Willison's own text states an explicit limitation on how fully this threat
can be defended against today. "we still don't know how to 100% reliably
prevent this from happening" (Willison, "Lethal Trifecta," verified
2026-08-23), and the post expresses direct skepticism toward vendor
guardrail products claiming otherwise. this entry reports that stated
limitation directly, an agent genuinely exhibiting all three conditions at
once carries a real, currently unsolved risk, not a risk fully closed by
any single mitigation.

## 5. Structure

The three conditions themselves are the entire structure of the threat
model, already quoted in full under dimension 1, access to private data,
exposure to untrusted content, and the ability to externally communicate.
Willison's own text frames removing any single leg as the practical
defense. "for end users combining tools themselves, the primary defense is
avoiding the trifecta entirely rather than relying on technical
mitigations" (Willison, "Lethal Trifecta," verified 2026-08-23).

## 6. ASCII structure diagram

```
  +------------------------+  +------------------------+  +------------------------+
  | LEG 1                  |  | LEG 2                  |  | LEG 3                  |
  | private data access    |  | untrusted content       |  | external               |
  |                        |  | exposure                |  | communication          |
  +------------------------+  +------------------------+  +------------------------+
              |                          |                          |
              +--------------------------+--------------------------+
                                         |
                                         v
                          all three present at once, on the
                          same agent, in the same request:
                          THE LETHAL TRIFECTA. an attacker's
                          instructions, smuggled inside LEG 2,
                          can now reach something worth
                          stealing (LEG 1) and a channel to
                          steal it through (LEG 3).

  removing ANY ONE leg from a given agent's capability set
  closes the trifecta for that agent, per dimension 5.
```

## 7. Dynamics

This entry explicitly checked the fetched source for a described runtime
mechanism, a specific request path or sequence of events, rather than a
static definition, and found the article states the threat as a
capability combination rather than a step-by-step attack sequence. the
closest dynamic description is the exfiltration path itself, already
implied in dimension 1's third condition, an attacker's data leaves the
system through whatever channel satisfies "the ability to externally
communicate," and this entry reports that the source frames the risk
structurally rather than as a narrated sequence.

## 8. Implementation variants

Willison's own text names two named, distinct mitigation directions rather
than implementation variants of the trifecta itself. a design-patterns
academic paper "recommends six patterns that can help," with the core
insight that "once an LLM agent has ingested untrusted input, it must be
constrained so that it is impossible for that input to trigger any
consequential actions" (Willison, "Lethal Trifecta," verified 2026-08-23),
and a second, named approach, "CaMeL offers a promising new direction for
mitigating prompt injection attacks" (Simon Willison, "CaMeL offers a
promising new direction for mitigating prompt injection attacks,"
2025-04-11, https://simonwillison.net/2025/Apr/11/camel/, verified
2026-08-23). this catalogue's own Dual LLM Pattern entry is a third,
concrete architecture that satisfies the same avoid-the-trifecta advice
from dimension 5 by permanently separating the untrusted-content leg from
the private-data and external-comms legs across two model instances.

## 9. Known production uses

This entry explicitly checked the fetched source for a named, deployed
system that suffered or avoided this exact threat and did not find a
specific production case study in the fetched material. Willison's own
post frames the trifecta as a general threat model for anyone building or
combining agent tools, not a report on a specific incident, and this entry
reports that absence directly.

## 10. Consequences

The threat, when all three conditions hold, is data theft, already stated
directly in dimension 1. the mitigation cost is capability loss, per
dimension 3, removing a leg to close the trifecta necessarily removes
whatever that leg provided, private-data access, information currency, or
the ability to act externally.

## 11. Failure modes and misuse

Willison's own text names the sharpest, most direct misuse case as trusting
a mitigation to be complete when it is not, already quoted in dimension 4,
a vendor guardrail product claiming to reliably prevent this class of
attack is a claim the article treats with explicit skepticism. this entry
reports that directly as the named failure mode rather than inventing a
more elaborate one.

## 12. Trade-off matrix

| Dimension | All three legs present (the trifecta) | Any one leg removed |
|---|---|---|
| Data-theft risk via prompt injection | Present, dimension 1 | Closed for that agent, dimension 5 |
| Agent usefulness | Maximal, dimension 3 | Reduced by whatever the removed leg provided |
| Reliability of current technical mitigations | Not 100%, explicitly stated, dimension 4 | Not applicable, the trifecta itself is avoided |
| Primary recommended defense | None fully reliable | Avoid combining all three, dimension 5 |

## 13. Related and incompatible patterns

This catalogue's own Dual LLM Pattern entry is the direct, sourced bridge,
already named in dimension 8, a concrete architecture that closes the
trifecta by structurally separating the untrusted-content-reading model
from the tool-and-private-data-holding model, so the same agent as a
whole retains all three capabilities while no single model instance within
it ever holds more than two of the three conditions at once.

## 14. Refactoring path in and out

This entry explicitly checked the fetched source for a documented,
staged migration path for an existing agent that already exhibits the
trifecta, and did not find one described as a formal process. the article
names avoiding the combination as the defense, per dimension 5, which for
an existing system means removing or gating one of the three
capabilities, rather than a named, staged migration procedure.

## 15. Testing and verification

This entry explicitly checked the fetched source for a testing or
verification method specific to detecting or confirming the trifecta in a
given agent's design and did not find one. this entry reports that
absence directly. the closest verifiable action available is the
structural audit implied by the definition itself, per dimension 5, does
this agent's capability set include all three named conditions
simultaneously, which is a design review question rather than a
documented automated test.

## 16. Observability signals

This entry explicitly checked the fetched source for a named metric, log
signal, or detection mechanism specific to this threat model and did not
find one. this entry reports that absence directly rather than inventing
an observability surface the source does not describe.

## 17. Security and privacy implications

The entire threat model is a security and privacy concern by definition,
already stated in full under dimension 1, private data theft via prompt
injection when an agent holds all three named capabilities at once.
Willison's own stated limitation from dimension 4, that no current
technical mitigation reliably closes this to 100 percent, is the honest
security posture this entry reports rather than a stronger guarantee the
source itself does not make.

## 18. References

1. Simon Willison, "The lethal trifecta for AI agents," 2025-06-16,
   https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/, verified
   2026-08-23.
2. Simon Willison, "CaMeL offers a promising new direction for mitigating
   prompt injection attacks," 2025-04-11,
   https://simonwillison.net/2025/Apr/11/camel/, verified 2026-08-23.
3. Simon Willison, "The Dual LLM pattern for building AI assistants that
   can resist prompt injection," 2023-04-25,
   https://simonwillison.net/2023/Apr/25/dual-llm-pattern/, verified
   2026-08-23.

## Code

TypeScript, Python, and Go implementations of a capability-set auditor
following the mechanism from dimensions 1 and 5, flagging an agent
configuration as exhibiting the lethal trifecta only when all three named
conditions are present at once, and clearing it when any one is absent.

```typescript
interface AgentCapabilities {
  privateDataAccess: boolean;
  untrustedContentExposure: boolean;
  externalCommunication: boolean;
}

function hasLethalTrifecta(caps: AgentCapabilities): boolean {
  return (
    caps.privateDataAccess &&
    caps.untrustedContentExposure &&
    caps.externalCommunication
  );
}

function missingLegs(caps: AgentCapabilities): string[] {
  const legs: Array<[string, boolean]> = [
    ["private data access", caps.privateDataAccess],
    ["untrusted content exposure", caps.untrustedContentExposure],
    ["external communication", caps.externalCommunication],
  ];
  return legs.filter(([, present]) => !present).map(([name]) => name);
}
```

```python
from dataclasses import dataclass
from typing import List


@dataclass
class AgentCapabilities:
    private_data_access: bool
    untrusted_content_exposure: bool
    external_communication: bool


def has_lethal_trifecta(caps: AgentCapabilities) -> bool:
    return (
        caps.private_data_access
        and caps.untrusted_content_exposure
        and caps.external_communication
    )


def missing_legs(caps: AgentCapabilities) -> List[str]:
    legs = [
        ("private data access", caps.private_data_access),
        ("untrusted content exposure", caps.untrusted_content_exposure),
        ("external communication", caps.external_communication),
    ]
    return [name for name, present in legs if not present]
```

```go
package trifecta

type AgentCapabilities struct {
	PrivateDataAccess        bool
	UntrustedContentExposure bool
	ExternalCommunication    bool
}

func HasLethalTrifecta(caps AgentCapabilities) bool {
	return caps.PrivateDataAccess &&
		caps.UntrustedContentExposure &&
		caps.ExternalCommunication
}

func MissingLegs(caps AgentCapabilities) []string {
	type leg struct {
		name    string
		present bool
	}
	legs := []leg{
		{"private data access", caps.PrivateDataAccess},
		{"untrusted content exposure", caps.UntrustedContentExposure},
		{"external communication", caps.ExternalCommunication},
	}
	var missing []string
	for _, l := range legs {
		if !l.present {
			missing = append(missing, l.name)
		}
	}
	return missing
}
```
