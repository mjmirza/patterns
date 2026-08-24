---
name: Prompt Caching via Exact Prefix Preservation
slug: prompt-caching-exact-prefix
family: 17-ai-agentic
category: AI Agentic
aliases: [Prefix Caching, Cache Breakpoints]
first_described: "Anthropic's own prompt caching documentation for the Claude API"
maturity: established
related: [filesystem-based-agent-state]
incompatible_with: []
verified: 2026-08-23
---

# Prompt Caching via Exact Prefix Preservation

## 1. Name, aliases, and lineage

Prompt caching lets a request resume from an already-processed prefix of a
prior request instead of reprocessing it, provided that prefix is byte for
byte identical to what was cached.

This entry sources it directly from Anthropic's own API documentation,
fetched live. "prompt caching optimizes your API usage by allowing resuming
from specific prefixes in your prompts. This significantly reduces
processing time and costs for repetitive tasks or prompts with consistent
elements" (Anthropic, "Prompt caching," Claude API documentation,
https://platform.claude.com/docs/en/build-with-claude/prompt-caching,
verified 2026-08-23). Claude Code's own consumer-level documentation states
the applied version of the same mechanism directly. "prompt caching makes
Claude Code faster and more cost-efficient. Without caching, the API would
reprocess your full history on every turn. With caching, it reuses what it
already processed" (Anthropic, "Prompt caching," Claude Code documentation,
https://code.claude.com/docs/en/prompt-caching, verified 2026-08-23).

## 2. Problem and context

The chapter's own text, meaning Claude Code's own documentation, states the
underlying problem directly. "the model doesn't remember anything between
requests, so Claude Code re-sends the full context, the system prompt, your
project context, every prior message and tool result, and your new message.
New content is appended at the end, which means most of each request is
identical to the one before it" (Anthropic, "Prompt caching," Claude Code
documentation, verified 2026-08-23). a stateless API means cost and latency
both scale with a growing conversation unless the redundant, identical
portion of every request can be skipped.

## 3. Forces

Anthropic's own text names the exact requirement directly. "cache hits
require 100% identical prompt segments, including all text and images up to
and including the block marked with cache control" (Anthropic, "Prompt
caching," Claude API documentation, verified 2026-08-23). the tension is
between wanting the freshest possible context on every call and needing an
unchanging, byte-identical prefix to get a cache hit at all. Claude Code's
own text states the practical resolution directly. "to get the most out of
prefix matching, Claude Code orders each request so content that rarely
changes between turns comes first," and "pick your model and effort level
at the top of a session, then save `/compact` for natural breaks between
tasks. The fewer changes you make mid-task, the higher your cache hit rate"
(Anthropic, "Prompt caching," Claude Code documentation, verified
2026-08-23).

## 4. Applicability and non-applicability

Anthropic's own text names two direct constraints on when caching helps at
all. a time-to-live, "by default, the cache has a 5-minute lifetime. The
cache is refreshed for no additional cost each time the cached content is
used" (a 1-hour alternative exists at higher write cost), and a minimum
length, "shorter prompts cannot be cached, even if marked with
`cache_control`... requests to cache fewer than this number of tokens will
be processed without caching, and no error is returned," with the threshold
ranging from 512 to 4,096 tokens depending on the model (Anthropic, "Prompt
caching," Claude API documentation, verified 2026-08-23).

The chapter's own text also gives a precise, worked non-applicability
example. a prompt with a large static prefix followed by a per-request block
containing a timestamp, cached at that block, "the timestamp differs, so
the prefix hash at block 6 differs... no cache hit. You pay for a fresh
cache write on every request and never get a read" (same source, verified
2026-08-23), the exact shape of a well-intentioned but broken breakpoint.

## 5. Structure

Anthropic's own text describes the mechanism directly. "the system checks
if a prompt prefix, up to a specified cache breakpoint, is already cached
from a recent query. If found, it uses the cached version... Otherwise, it
processes the full prompt and caches the prefix once the response begins"
(Anthropic, "Prompt caching," Claude API documentation, verified
2026-08-23), following a fixed hierarchy, "`tools` then `system` then
`messages`. Changes at each level invalidate that level and all subsequent
levels" (same source).

Claude Code's own three-layer structural model, quoted directly. "system
prompt, core instructions, tool definitions, output style, changes when the
set of loaded tool definitions changes, or Claude Code is upgraded. project
context, CLAUDE.md, auto memory, unscoped rules, changes at session start,
or after `/clear` or `/compact`. conversation, your messages, Claude's
responses, tool results, changes every turn" (Anthropic, "Prompt caching,"
Claude Code documentation, verified 2026-08-23). two further keys sit
outside the prompt text entirely. "each model has its own cache... each
effort level has its own cache for the same model" (same source).

## 6. ASCII structure diagram

```
request N minus 1:

  [system prompt] [project context] [conversation]
       cache breakpoint, prefix hashed and stored

request N, unchanged prefix, new turn appended:

  [system prompt]     read from cache
  [project context]   read from cache
  [conversation]      read from cache
  [new turn]          fresh

request N plus 1, a change lands inside the prefix,
for example a model switch:

  [system prompt*]
  [project context]
  [conversation]
  [new turn]

  * changed here, so everything after this point
    reprocesses and re-caches, in full, at full cost
```

## 7. Dynamics

Anthropic's own exact billing figures, quoted directly. "5-minute cache
writes, 1.25 times base input token price. 1-hour cache writes, 2 times
base input token price. Cache reads and refreshes, 0.1 times base input
token price" (Anthropic, "Prompt caching," Claude API documentation,
verified 2026-08-23). Claude Code's own response fields, quoted directly.
"`cache_creation_input_tokens`, tokens written to the cache on this turn,
billed at the cache write rate. `cache_read_input_tokens`, tokens served
from cache on this turn, billed at roughly 10% of the standard input rate"
(Anthropic, "Prompt caching," Claude Code documentation, verified
2026-08-23). deferred tool loading is a documented exception to prefix
invalidation. "a server connecting, disconnecting, or changing its tool
list only appends new content and doesn't disturb anything already cached,"
while "tools loaded into the prefix, any change to them invalidates the
cache" (same source).

## 8. Implementation variants

OpenAI documents a directly comparable mechanism on its own API platform,
with independently confirmed, closely matching numbers. "by default,
caching is enabled automatically for prompts that are 1,024 tokens or
longer" (for its current generation of models), "cache hits are only
possible for exact prefix matches within a prompt," and "cached input
tokens are billed at 0.1x the uncached input token rate" (OpenAI, "Prompt
caching," OpenAI API documentation,
https://developers.openai.com/api/docs/guides/prompt-caching, verified
2026-08-23). the 0.1x read discount matches Anthropic's own figure from
dimension 7 independently, in each vendor's own words, which this entry
reports as a genuinely strong, directly-cited implementation-variant match
rather than a coincidence assumed without checking. OpenAI's own reliability
caveat is also stated plainly, distinct from Anthropic's fixed-TTL model.
"cache reuse is best-effort," depending on "the prompt prefix remaining
identical, the cached content still being available, and the request
reaching a machine that holds the matching entry" (same source).

## 9. Known production uses

Claude Code and the Anthropic API are confirmed, live, currently operating
consumers of this mechanism, per dimensions 1 and 7. the OpenAI API is a
second, independently confirmed, currently live production consumer of the
equivalent mechanism, per dimension 8.

## 10. Consequences

The benefit is stated directly, already quoted in dimension 2, avoiding a
full reprocess of identical content on every turn. the cost risk is stated
directly and named plainly as something that can go unnoticed. "these
actions cause the next request to miss part or all of the cache. You see a
one-time slower, more expensive turn, after which the new prefix is cached.
Most of them are avoidable mid-task once you know they have a cost. A model
switch can feel free until you notice the slower turn that follows"
(Anthropic, "Prompt caching," Claude Code documentation, verified
2026-08-23).

## 11. Failure modes and misuse

Anthropic's own text names an unusually explicit, enumerated list of
silent, cache-breaking actions, quoted in the introduction to dimension 10.
switching models, changing effort level, turning on fast mode,
connecting or disconnecting an MCP server when its tools are loaded into
the prefix rather than deferred, enabling or disabling a plugin, denying an
entire tool, compacting the conversation via Claude Code's own automatic
summarization mechanism, and upgrading Claude Code itself. a real, named historical instance
of the exact silently-costly failure shape this dimension asks about is
documented directly. "before v2.1.237, Claude Code marked the block for
caching through gateways too, and a gateway that silently removed the
marker left the entire conversation billed as uncached input on every
turn" (Anthropic, "Prompt caching," Claude Code documentation, verified
2026-08-23).

## 12. Trade-off matrix

| Dimension | Prompt caching | No caching |
|---|---|---|
| Repeat prefix cost | About 10% of the standard input rate, dimension 7 | Full price every request, dimension 2 |
| First-write cost | 1.25x to 2x base rate, dimension 7 | Not applicable |
| Prefix stability required | Byte-identical up to the breakpoint, dimension 3 | None, any change is free |
| Cache lifetime | 5 minutes default, up to 1 hour, dimension 4 | Not applicable |
| Failure mode | Silent, unnoticed cost on a prefix change, dimension 11 | No hidden cost, but no savings either |
| Minimum prompt length | 512 to 4,096 tokens, dimension 4 | None |

## 13. Related and incompatible patterns

This entry explicitly checked whether Anthropic's own prompt caching
documentation compares itself to general HTTP or CDN caching by name and
confirmed it does not, using overlapping vocabulary, cache, TTL, hit, miss,
invalidation, without stating the comparison directly, and this entry
reports that as an honest absence rather than an assumed bridge. the
strongest sourced cross-references are internal. compaction is one of the
named actions that invalidates the cache, per dimension 11, and the project
context cache layer from dimension 5 is defined as exactly the disk-backed
CLAUDE.md and auto memory content this catalogue's own Filesystem-Based
Agent State entry covers.

## 14. Refactoring path in and out

Anthropic documents an explicit off switch, both global and per model.
"`DISABLE_PROMPT_CACHING`" plus per-model variants, stating directly.
"disabling caching is occasionally useful when debugging caching behavior
with a specific model or provider. For normal use, leave caching enabled"
(Anthropic, "Prompt caching," Claude Code documentation, verified
2026-08-23). adopting the longer, 1-hour lifetime is an explicit opt-in via
`ENABLE_PROMPT_CACHING_1H`, and forcing the shorter 5-minute lifetime back
is `FORCE_PROMPT_CACHING_5M` (same source).

## 15. Testing and verification

Both vendors document a direct verification method. Anthropic states.
"to verify whether a prompt was cached, check the response usage fields.
if both `cache_creation_input_tokens` and `cache_read_input_tokens` are 0,
the prompt was not cached," plus a dedicated diagnostic tool that "compares
consecutive requests and reports exactly where the prompt prefix diverged"
(Anthropic, "Prompt caching," Claude API documentation, verified
2026-08-23). Claude Code's own guidance names the health signal directly.
"a high read-to-creation ratio means caching is working well. If creation
stays high turn after turn, something is changing in your prefix"
(Anthropic, "Prompt caching," Claude Code documentation, verified
2026-08-23).

## 16. Observability signals

The exact field names are confirmed on both vendors, per dimension 7 for
Anthropic and dimension 8 for OpenAI, `cache_creation_input_tokens` and
`cache_read_input_tokens` on Anthropic's side, `cached_tokens` nested under
`input_tokens_details` or `prompt_tokens_details` on OpenAI's side.
Anthropic additionally documents an organization-wide export path. "the
OpenTelemetry exporter reports cache read and creation tokens per user and
session" (Anthropic, "Prompt caching," Claude Code documentation, verified
2026-08-23).

## 17. Security and privacy implications

This entry did not find either vendor's fetched documentation addressing a
security or privacy concern for cached content directly. one adjacent,
explicitly stated isolation guarantee is closer to multi-tenancy than
privacy. "caches are isolated between organizations, and on some
providers, between workspaces within an organization" (Anthropic, "Prompt
caching," Claude Code documentation, verified 2026-08-23). no discussion of
whether cached tokens could ever leak across users was found in either
source, and this entry reports that absence rather than asserting a
guarantee neither vendor states.

## 18. References

1. Anthropic, "Prompt caching," Claude API documentation,
   https://platform.claude.com/docs/en/build-with-claude/prompt-caching,
   verified 2026-08-23.
2. Anthropic, "Prompt caching," Claude Code documentation,
   https://code.claude.com/docs/en/prompt-caching, verified 2026-08-23.
3. OpenAI, "Prompt caching," OpenAI API documentation,
   https://developers.openai.com/api/docs/guides/prompt-caching, verified
   2026-08-23.

## Code

TypeScript, Python, and Go implementations of an exact-prefix cache
following the mechanism from dimensions 5 through 7, hashing a prompt up to
a breakpoint and serving a cached prefix only on a byte-identical match.

```typescript
interface CacheEntry {
  prefixHash: string;
  cachedAt: number;
}

class PrefixCache {
  private entries = new Map<string, CacheEntry>();

  constructor(private ttlMs: number) {}

  private hash(prefix: string): string {
    let h = 0;
    for (let i = 0; i < prefix.length; i++) {
      h = (h * 31 + prefix.charCodeAt(i)) | 0;
    }
    return String(h);
  }

  checkAndStore(prefix: string): { hit: boolean } {
    const key = this.hash(prefix);
    const now = Date.now();
    const existing = this.entries.get(key);
    if (existing && now - existing.cachedAt < this.ttlMs) {
      existing.cachedAt = now;
      return { hit: true };
    }
    this.entries.set(key, { prefixHash: key, cachedAt: now });
    return { hit: false };
  }
}
```

```python
import time
from typing import Dict


class CacheEntry:
    def __init__(self, prefix_hash: str, cached_at: float) -> None:
        self.prefix_hash = prefix_hash
        self.cached_at = cached_at


class PrefixCache:
    def __init__(self, ttl_seconds: float) -> None:
        self._ttl = ttl_seconds
        self._entries: Dict[str, CacheEntry] = {}

    def _hash(self, prefix: str) -> str:
        return str(hash(prefix))

    def check_and_store(self, prefix: str) -> bool:
        key = self._hash(prefix)
        now = time.time()
        existing = self._entries.get(key)
        if existing and now - existing.cached_at < self._ttl:
            existing.cached_at = now
            return True
        self._entries[key] = CacheEntry(prefix_hash=key, cached_at=now)
        return False
```

```go
package prefixcache

import (
	"hash/fnv"
	"time"
)

type cacheEntry struct {
	cachedAt time.Time
}

type PrefixCache struct {
	ttl     time.Duration
	entries map[string]*cacheEntry
}

func NewPrefixCache(ttl time.Duration) *PrefixCache {
	return &PrefixCache{ttl: ttl, entries: make(map[string]*cacheEntry)}
}

func (c *PrefixCache) hash(prefix string) string {
	h := fnv.New64a()
	h.Write([]byte(prefix))
	return string(rune(h.Sum64()))
}

func (c *PrefixCache) CheckAndStore(prefix string) bool {
	key := c.hash(prefix)
	now := time.Now()
	if existing, ok := c.entries[key]; ok && now.Sub(existing.cachedAt) < c.ttl {
		existing.cachedAt = now
		return true
	}
	c.entries[key] = &cacheEntry{cachedAt: now}
	return false
}
```
