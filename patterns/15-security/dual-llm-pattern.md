---
name: Dual LLM Pattern
slug: dual-llm-pattern
family: 15-security
category: Security
aliases: [Privileged and Quarantined LLM, Two-LLM Isolation]
first_described: "Simon Willison's own blog post introducing the pattern"
maturity: emerging
related: [lethal-trifecta-threat-model]
incompatible_with: []
verified: 2026-08-23
---

# Dual LLM Pattern

## 1. Name, aliases, and lineage

The Dual LLM pattern splits an agent's reasoning across two separate model
instances, one that can act on a person's behalf but only ever reads
trusted input, and one that reads untrusted content but is never given the
ability to act.

This entry sources it directly from Simon Willison's own blog, fetched
live. "the Privileged LLM is the core of the AI assistant. It accepts
input from trusted sources, primarily the user themselves, and acts on
that input in various ways... it has access to tools" (Simon Willison,
"The Dual LLM pattern for building AI assistants that can resist prompt
injection," 2023-04-25,
https://simonwillison.net/2023/Apr/25/dual-llm-pattern/, verified
2026-08-23). "the Quarantined LLM is used any time we need to work with
untrusted content... this LLM does not have access to tools, and is
expected to have the potential to go rogue at any moment" (same source).

## 2. Problem and context

Willison's own text states the problem directly, naming the failure mode
this pattern exists to contain. an LLM that both reads untrusted content
and can act on tools is vulnerable to prompt injection, where "unfiltered
content output by the Quarantined LLM is never forwarded on to the
Privileged LLM" (Willison, "Dual LLM," verified 2026-08-23) is exactly the
rule the pattern enforces to prevent an attacker's instructions, smuggled
inside content the model reads, from ever reaching the model that holds
tool access.

## 3. Forces

The direct tension the pattern resolves is between capability and
exposure. a single, capable LLM that can both read anything and act on
tools is maximally useful and maximally exploitable in the same instance.
splitting the two responsibilities across two model instances removes the
single point where a hostile instruction and tool access coexist, at the
cost Willison names directly under dimension 10.

## 4. Applicability and non-applicability

This entry explicitly checked the fetched source for a stated
applicability boundary and found an explicit, direct one. Willison states
plainly that even this pattern "isn't a 100% reliable solution" and that
"users are still vulnerable to social engineering" attacks that trick a
person directly rather than the model (Willison, "Dual LLM," verified
2026-08-23), naming social-engineering-driven human error as a case the
pattern does not cover regardless of how the two LLMs are isolated.

## 5. Structure

Willison's own text names a third component that sits between the two
models. "the Controller is regular software, not a language model... it
handles interactions with users, triggers the LLMs and executes actions on
behalf of the Privileged LLM" (Willison, "Dual LLM," verified 2026-08-23),
meaning the Controller, not either model, is what actually calls tools,
gated by the Privileged LLM's decisions and never by anything the
Quarantined LLM produced directly.

## 6. ASCII structure diagram

```
   trusted user input
          |
          v
  +-------------------+        +----------------------+
  |  Privileged LLM    |<------>|  Controller           |
  |  has tool access    |        |  plain software, not   |
  |  never reads        |        |  a model, executes     |
  |  untrusted content   |        |  actions on the        |
  +-------------------+        |  Privileged LLM's      |
                                |  behalf                |
                                +----------------------+
                                          ^
                                          | a filtered handle only,
                                          | never raw unfiltered text
                                          |
                                +----------------------+
                                |  Quarantined LLM       |
                                |  no tool access         |
                                |  reads untrusted content |
                                +----------------------+
                                          ^
                                          |
                              untrusted content (web page,
                              email, document, tool result)
```

## 7. Dynamics

Willison's own text describes the runtime path directly, already quoted
in dimension 2, unfiltered Quarantined LLM output never reaches the
Privileged LLM. the Controller mediates every step, per dimension 5, so
the only path from untrusted content back to the Privileged LLM is through
software the Controller controls, never a direct model-to-model handoff.

## 8. Implementation variants

This entry explicitly checked the fetched source for a second, independent
implementation of this exact two-model split and did not find one
described in Willison's own post. the post instead references a related
academic direction. "CaMeL offers a promising new direction for mitigating
prompt injection attacks" (Simon Willison, "CaMeL offers a promising new
direction for mitigating prompt injection attacks," 2025-04-11,
https://simonwillison.net/2025/Apr/11/camel/, verified 2026-08-23), which
this entry reports as a related, distinct academic approach rather than a
second implementation of the same two-LLM structure.

## 9. Known production uses

This entry explicitly checked the fetched source for a named, deployed
production system built on this exact pattern and did not find one.
Willison's own text frames the pattern as a proposed design rather than a
shipped product, and this entry reports that absence directly rather than
inventing a production case study the source does not supply.

## 10. Consequences

Willison's own text states the cost directly and unusually plainly for a
pattern he himself is proposing. "it's pretty bad! ... this pattern
results in a great deal more implementation complexity and a degraded user
experience" (Willison, "Dual LLM," verified 2026-08-23), a direct,
self-stated trade against the isolation benefit named in dimension 2.

## 11. Failure modes and misuse

Willison's own text names the sharpest failure mode directly, already
quoted in dimension 4, a social-engineering attack aimed at the person
rather than either model bypasses the isolation entirely, since the
isolation boundary this pattern builds sits between the two LLMs, not
between an attacker and the human operator.

## 12. Trade-off matrix

| Dimension | Dual LLM pattern | A single, capable LLM |
|---|---|---|
| Reads untrusted content and holds tool access at once | Never, split across two instances, dimension 5 | Yes, the exact exposure this pattern removes |
| Implementation complexity | Higher, dimension 10 | Lower |
| User experience | Degraded, dimension 10 | Smoother |
| Vulnerable to social engineering of the human | Yes, explicitly stated, dimension 4 | Yes, unrelated to this pattern |
| Reliability against prompt injection | Not 100%, dimension 4 | Lower still, single point of exposure |

## 13. Related and incompatible patterns

The Lethal Trifecta threat model, already sourced in this catalogue's own
sibling entry, names the exact three conditions, private data access,
untrusted content exposure, and external communication ability, that the
Dual LLM pattern is one concrete architecture for avoiding, since splitting
tool access away from the model that reads untrusted content breaks the
trifecta's third condition for the model that can see attacker-controlled
text.

## 14. Refactoring path in and out

This entry explicitly checked the fetched source for a documented,
staged migration from a single-LLM design to the dual-LLM split, or an
explicit path back, and did not find either described as a formal process.
Willison's own post presents the two-model split as the design itself
rather than a migration with named steps, and this entry reports that
directly.

## 15. Testing and verification

This entry explicitly checked the fetched source for a testing or
verification method specific to this pattern and did not find one. the
Controller's own mediation of every Quarantined-to-Privileged handoff, per
dimension 5 and 7, is the closest verifiable structural property in the
post, but it is an architectural guarantee, not a documented test
methodology, and this entry reports that distinction directly.

## 16. Observability signals

This entry explicitly checked the fetched source for a named metric or log
signal specific to this pattern and did not find one. this entry reports
that absence directly rather than inventing an observability surface the
source does not describe.

## 17. Security and privacy implications

The entire pattern is a security mechanism, and Willison's own text states
its guarantee and its limit together, already quoted in dimensions 2, 4,
and 10, unfiltered untrusted output never reaches the tool-holding model,
but the isolation is not a complete solution and does not protect against
social engineering of the human operator.

## 18. References

1. Simon Willison, "The Dual LLM pattern for building AI assistants that
   can resist prompt injection," 2023-04-25,
   https://simonwillison.net/2023/Apr/25/dual-llm-pattern/, verified
   2026-08-23.
2. Simon Willison, "CaMeL offers a promising new direction for mitigating
   prompt injection attacks," 2025-04-11,
   https://simonwillison.net/2025/Apr/11/camel/, verified 2026-08-23.
3. Simon Willison, "The lethal trifecta for AI agents," 2025-06-16,
   https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/, verified
   2026-08-23.

## Code

TypeScript, Python, and Go implementations of a minimal Controller
following the mechanism from dimensions 5 through 7, holding the only
path between a quarantined reader and a privileged actor, and refusing to
forward raw quarantined output.

```typescript
interface QuarantinedResult {
  handle: string;
  summary: string;
}

class Controller {
  private store = new Map<string, string>();

  runQuarantined(untrustedContent: string): QuarantinedResult {
    const handle = "q-" + this.store.size;
    this.store.set(handle, untrustedContent);
    const summary = "quarantined content stored under " + handle;
    return { handle, summary };
  }

  runPrivileged(handle: string, allowedAction: string): string {
    if (!this.store.has(handle)) {
      throw new Error("unknown handle: " + handle);
    }
    return "privileged action '" + allowedAction + "' executed against handle " + handle;
  }
}
```

```python
from typing import Dict, NamedTuple


class QuarantinedResult(NamedTuple):
    handle: str
    summary: str


class Controller:
    def __init__(self) -> None:
        self._store: Dict[str, str] = {}

    def run_quarantined(self, untrusted_content: str) -> QuarantinedResult:
        handle = "q-" + str(len(self._store))
        self._store[handle] = untrusted_content
        summary = "quarantined content stored under " + handle
        return QuarantinedResult(handle=handle, summary=summary)

    def run_privileged(self, handle: str, allowed_action: str) -> str:
        if handle not in self._store:
            raise ValueError("unknown handle: " + handle)
        return "privileged action '" + allowed_action + "' executed against handle " + handle
```

```go
package controller

import "fmt"

type QuarantinedResult struct {
	Handle  string
	Summary string
}

type Controller struct {
	store map[string]string
}

func NewController() *Controller {
	return &Controller{store: make(map[string]string)}
}

func (c *Controller) RunQuarantined(untrustedContent string) QuarantinedResult {
	handle := fmt.Sprintf("q-%d", len(c.store))
	c.store[handle] = untrustedContent
	summary := "quarantined content stored under " + handle
	return QuarantinedResult{Handle: handle, Summary: summary}
}

func (c *Controller) RunPrivileged(handle string, allowedAction string) (string, error) {
	if _, ok := c.store[handle]; !ok {
		return "", fmt.Errorf("unknown handle: %s", handle)
	}
	return "privileged action '" + allowedAction + "' executed against handle " + handle, nil
}
```
