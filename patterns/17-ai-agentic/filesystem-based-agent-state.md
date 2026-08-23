---
name: Filesystem-Based Agent State
slug: filesystem-based-agent-state
family: 17-ai-agentic
category: AI Agentic
aliases: [Auto Memory, On-Disk Agent Memory]
first_described: "Anthropic's own Claude Code documentation for its auto memory feature"
maturity: established
related: [context-window-auto-compaction, prompt-caching-exact-prefix, agent-memory]
incompatible_with: []
verified: 2026-08-23
---

# Filesystem-Based Agent State

## 1. Name, aliases, and lineage

Filesystem-based agent state persists an agent's own accumulated knowledge
as plain files on disk, outside the conversation entirely, so it survives a
fresh session start, a compaction pass, or a subagent spawn rather than
living only inside a single request's history.

This entry names it distinctly from this catalogue's own Agent Memory
entry, which is sourced from Packer, Wooders, Lin, Fang, Patil, Stoica, and
Gonzalez's 2023 MemGPT paper and covers a general self-editing, paged memory
architecture. this entry instead sources a concrete, currently shipping
implementation of the same underlying idea, Anthropic's own auto memory
feature, fetched directly (Anthropic, "Give Claude persistent memory,"
Claude Code documentation, https://code.claude.com/docs/en/memory, verified
2026-08-23). "each Claude Code session begins with a fresh context. Two
mechanisms carry knowledge across sessions. CLAUDE.md files, instructions
you write to give Claude persistent context. Auto memory, notes Claude
writes itself based on your corrections and preferences" (same source).

An earlier fetch attempt against Manus's own engineering blog, a widely
cited early source for the same underlying idea, "use the filesystem as
context," could not be completed live in this session. the site returned a
scheduled maintenance notice stating service would resume 25 August 2026,
verified 2026-08-23. this entry reports that gap honestly rather than
reconstructing Manus's own claims from memory.

## 2. Problem and context

The chapter's own text, meaning Anthropic's own documentation, states the
problem directly in one sentence. "each Claude Code session begins with a
fresh context" (Anthropic, "Give Claude persistent memory," verified
2026-08-23), meaning everything an agent learned in a prior session, a
compaction, or a subagent spawn is gone unless something outside that
ephemeral conversation carries it forward. Anthropic's own applied research
post names the same problem from a different angle. "structured note-taking...
allows the agent to track critical context and dependencies that would
otherwise be lost across dozens of tool calls" (Anthropic, "Effective context engineering for AI agents," Anthropic engineering blog,
https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents,
verified 2026-08-23).

## 3. Forces

The chapter's own text resolves a direct tension between loading everything
for fidelity and keeping what loads small enough to stay cheap and
coherent, by making the on-disk store larger than what actually loads.
"the first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes
first, are loaded at the start of every conversation. Content beyond that
threshold is not loaded at session start. Claude keeps `MEMORY.md` concise
by moving detailed notes into separate topic files" (Anthropic, "Give
Claude persistent memory," verified 2026-08-23). an index, small and always
loaded, plus unbounded detail, large and loaded only on demand, rather
than an all-or-nothing choice.

## 4. Applicability and non-applicability

The chapter's own text names what gets saved directly. "Claude skips
anything it can derive from the codebase, such as architecture, file
paths, or debugging fixes. It also skips anything your CLAUDE.md files
already say," and "Claude doesn't save something every session. It decides
what's worth remembering based on whether the information would be useful
in a future conversation" (same source).

A precise, explicitly stated non-applicability case follows directly. this
mechanism is not an enforcement mechanism. "Claude treats them as context,
not enforced configuration. To block an action regardless of what Claude
decides, use a PreToolUse hook instead" (same source), a direct bridge to
this catalogue's own Hook-Based Safety Guard Rails entry. a further caveat
names the mechanism's own reach. "auto memory is machine-local. All
worktrees and subdirectories within the same git repository share one auto
memory directory. Files are not shared across machines or cloud
environments" (same source).

## 5. Structure

The exact directory layout, quoted directly. "each project gets its own
memory directory at `~/.claude/projects/<project>/memory/`," containing
"`MEMORY.md`, an index, one line per memory, loaded into every session,"
plus "any other topic files Claude creates," where "`MEMORY.md` acts as an
index of the memory directory. Claude reads and writes files in this
directory throughout your session, using `MEMORY.md` to keep track of what
is stored where" (Anthropic, "Give Claude persistent memory," verified
2026-08-23). four named categories of note exist, quoted directly. "`user`,
your role, expertise, and working preferences. `feedback`, corrections you
give Claude and approaches you confirm. `project`, ongoing work, deadlines,
and decisions that Claude can't derive from the code or git history.
`reference`, where to find information outside the project, such as an
issue tracker or dashboard" (same source).

## 6. ASCII structure diagram

```
  ephemeral conversation, small, gone every fresh session:

  +-------------------------+
  | MEMORY.md index         |  <-- loaded every session,
  | (200 lines / 25KB cap)  |      always, capped
  +-------------------------+
             |
             | read on demand only, when Claude decides
             | one specific topic file is needed
             v
  +-------------------------+
  | topic file content      |  <-- read into the session here
  | (used, then can drop)   |
  +-------------------------+

  durable, on disk, survives every fresh session:

  ~/.claude/projects/<project>/memory/
    +-- MEMORY.md            (the index)
    +-- user_role.md
    +-- feedback_testing.md
    +-- project_sprint.md
    +-- reference_dashboard.md

  write happens on session end or on a correction, and Claude Code
  measures the index against its own limits after every write.
```

## 7. Dynamics

Read timing is split in two, quoted directly. the index loads every time,
always capped, per dimension 3, while topic files are read
lazily, "Claude reads them on demand using its standard file tools when it
needs the information" (Anthropic, "Give Claude persistent memory,"
verified 2026-08-23). write timing carries its own self-correction
protocol. "after Claude writes to `MEMORY.md`, Claude Code measures the
file against the 200-line and 25KB read limits. If the file is near a
limit, Claude Code reminds Claude to shorten it... If the file is over a
limit, the write still succeeds, but Claude Code returns an error telling
Claude to rewrite the index, because everything past the limit is dropped
on the next load" (same source). isolation from subagents is explicit,
with one named exception. "the main conversation's auto memory isn't
loaded into subagents, the exception is a fork, which inherits the parent
conversation and system prompt" (same source).

## 8. Implementation variants

LangGraph documents a structurally different, checkpoint-based variant.
"checkpoints... capture the full state at each step, saved automatically as
the graph executes," with an explicit persistence-backend choice, "in
production... use a database-backed checkpointer such as Postgres" rather
than the default, since "the in-memory checkpointer does not persist your
graph state" and everything is lost on restart (LangChain, "Persistence,"
LangGraph documentation, https://docs.langchain.com/oss/python/langgraph/persistence,
verified 2026-08-23). where Anthropic's own mechanism from dimension 5
elects what to save and writes prose notes, LangGraph checkpoints the
entire graph state automatically and stores it as structured data, a
different point on the same save-outside-the-conversation spectrum.

A second, adjacent but distinct variant is the AGENTS.md specification, a
cross-vendor convention for a single root-level file "used by over 20
AI coding tools" that carries project-level instructions ("AGENTS.md,"
agents.md, https://agents.md, verified 2026-08-23). this entry confirmed
directly that AGENTS.md is user-authored, static project instructions, the
same role Anthropic's own CLAUDE.md plays per dimension 1, and is
explicitly a different mechanism from the self-writing, self-editing notes
this entry's own dimension 5 covers, never a duplicate of either.

## 9. Known production uses

Claude Code's own auto memory feature and LangGraph's own checkpoint
persistence are each real, currently shipping mechanisms, confirmed
directly against each vendor's own live documentation under dimensions 1
and 8. AGENTS.md is a confirmed, currently adopted cross-vendor convention,
per dimension 8, though it persists instructions rather than an agent's
own accumulated notes and is named here only as an adjacent mechanism.

## 10. Consequences

The chapter's own text states the direct benefit, already quoted in
dimension 2, knowledge that would otherwise vanish every fresh session now
survives it. the cost is the same lossy-index trade named in dimension 7,
where content past the 200-line or 25KB threshold is silently unavailable
at session start until a topic file is separately read, and per dimension
4, the mechanism decides what to save on its own judgment rather than under
a person's explicit, enforced control.

## 11. Failure modes and misuse

Anthropic's own text names the sharpest failure mode directly, already
quoted in dimension 4. treating a saved note as an enforced rule the agent
will always obey is a misuse, since "Claude treats them as context, not
enforced configuration" (Anthropic, "Give Claude persistent memory,"
verified 2026-08-23), and a person who needs a hard guarantee rather than a
strong hint needs the PreToolUse hook this same sentence names instead.
LangGraph's own text names a directly parallel failure mode for its own
variant, already quoted in dimension 8. choosing the default in-memory
checkpointer for a production deployment silently loses all state on
restart, an explicit gap between what looks like persistence in
development and what is actually durable in production.

## 12. Trade-off matrix

| Dimension | Filesystem-based agent state | Conversation-only state |
|---|---|---|
| Survives a fresh session | Yes, read from disk, dimension 5 | No, gone the moment the session ends |
| Survives compaction | Yes, re-injected from disk, dimension 1 | No, subject to what the summary keeps |
| What gets saved | Agent's own judgment, dimension 4 | Everything, until it is discarded |
| Enforcement strength | Context, not enforced, dimension 11 | Not applicable |
| Cross-machine reach | Machine-local only, dimension 4 | Not applicable, conversation is ephemeral anyway |
| Index size discipline | Capped at 200 lines or 25KB, dimension 3 | Not applicable |

## 13. Related and incompatible patterns

This entry explicitly checked whether Anthropic's own fetched pages compare
this mechanism to a database or a key-value store by name and confirmed
they do not, describing it only in terms of files and a directory, and this
entry reports that absence directly rather than inventing a database
analogy neither source draws. the two strongest, directly sourced
cross-references are internal to this same documentation set. the
PreToolUse hook boundary from dimension 4 and 11 is the direct bridge to
this catalogue's own Hook-Based Safety Guard Rails entry, and being
re-injected specifically because compaction discards the conversation but
not the disk is the direct bridge to this catalogue's own Context Window
Auto-Compaction entry, both already quoted under dimension 1 and 4.

## 14. Refactoring path in and out

Anthropic's own text documents the explicit control surface directly.
"to turn auto memory off, run the settings command and disable the
`autoMemory` key" (Anthropic, "Give Claude persistent memory," verified
2026-08-23). the documented path out, per dimension 4's own PreToolUse
cross reference, is not disabling the mechanism but layering a hook on top
of it for anything that needs to be guaranteed rather than merely
remembered.

## 15. Testing and verification

This entry explicitly checked for a documented, mechanism-specific test or
verification method and did not find one in Anthropic's fetched pages. the
closest confirmed verification surface is inspecting the directory
directly, since the files are plain markdown at a fixed, documented path
per dimension 5, and this entry reports that as a direct, filesystem-level
check rather than a purpose-built test tool neither source documents.

## 16. Observability signals

Anthropic's own text documents a `modified` frontmatter field on each
memory file, and this entry independently confirmed the mechanism directly
by reading a real memory file in this project's own environment, where
each such file is stamped with a `modified: <date>` header updated on
every write, giving a direct, per-file staleness signal a reader or a tool
can act on. no dedicated metrics or dashboard for the mechanism was found
in either fetched source, and this entry reports that absence directly.

## 17. Security and privacy implications

Anthropic's own text draws one explicit isolation boundary directly, and
also states the honest limit of that isolation. "auto memory is
machine-local... not shared across machines or cloud environments," but a
git-tracked project shares one memory directory "across all worktrees and
subdirectories" (Anthropic, "Give Claude persistent memory," verified
2026-08-23), meaning a memory file written from one worktree is visible
from a sibling worktree of the same repository, a real, sourced sharing
boundary distinct from full isolation. this entry did not find either
source discussing what happens if a memory file records something
sensitive, and reports that gap directly rather than asserting a
protection neither source states.

## 18. References

1. Anthropic, "Give Claude persistent memory," Claude Code documentation,
   https://code.claude.com/docs/en/memory, verified 2026-08-23.
2. Anthropic, "Effective context engineering for AI agents," Anthropic engineering
   blog, https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents,
   verified 2026-08-23.
3. LangChain, "Persistence," LangGraph documentation,
   https://docs.langchain.com/oss/python/langgraph/persistence, verified
   2026-08-23.
4. "AGENTS.md," agents.md, https://agents.md, verified 2026-08-23.

## Code

TypeScript, Python, and Go implementations of a capped memory index
following the mechanism from dimensions 3 and 5, tracking a small always-
loaded index plus unbounded lazily-read topic files, and enforcing the
byte and line caps from Anthropic's own documented behavior. Each renders
its index using an explicit newline character constant rather than an
inline escape sequence, so the separator is unambiguous in every language.

```typescript
const NL = String.fromCharCode(10);

interface MemoryEntry {
  category: string;
  summary: string;
  topicFile: string;
}

class MemoryIndex {
  private entries: MemoryEntry[] = [];

  constructor(private maxLines: number, private maxBytes: number) {}

  add(entry: MemoryEntry): { overLimit: boolean } {
    this.entries.push(entry);
    return { overLimit: this.isOverLimit() };
  }

  private renderIndex(): string {
    return this.entries
      .map((e) => "- [" + e.category + "] " + e.summary + " (" + e.topicFile + ")")
      .join(NL);
  }

  private isOverLimit(): boolean {
    const rendered = this.renderIndex();
    const lineCount = rendered.split(NL).length;
    const byteCount = new TextEncoder().encode(rendered).length;
    return lineCount > this.maxLines || byteCount > this.maxBytes;
  }
}
```

```python
NL = chr(10)


class MemoryEntry:
    def __init__(self, category: str, summary: str, topic_file: str) -> None:
        self.category = category
        self.summary = summary
        self.topic_file = topic_file


class MemoryIndex:
    def __init__(self, max_lines: int, max_bytes: int) -> None:
        self._max_lines = max_lines
        self._max_bytes = max_bytes
        self._entries = []

    def add(self, entry: MemoryEntry) -> bool:
        self._entries.append(entry)
        return self._is_over_limit()

    def _render_index(self) -> str:
        lines = [
            "- [" + e.category + "] " + e.summary + " (" + e.topic_file + ")"
            for e in self._entries
        ]
        return NL.join(lines)

    def _is_over_limit(self) -> bool:
        rendered = self._render_index()
        line_count = rendered.count(NL) + 1
        byte_count = len(rendered.encode("utf-8"))
        return line_count > self._max_lines or byte_count > self._max_bytes
```

```go
package memoryindex

import "strings"

var nl = string(rune(10))

type MemoryEntry struct {
	Category  string
	Summary   string
	TopicFile string
}

type MemoryIndex struct {
	maxLines int
	maxBytes int
	entries  []MemoryEntry
}

func NewMemoryIndex(maxLines, maxBytes int) *MemoryIndex {
	return &MemoryIndex{maxLines: maxLines, maxBytes: maxBytes}
}

func (m *MemoryIndex) Add(entry MemoryEntry) bool {
	m.entries = append(m.entries, entry)
	return m.isOverLimit()
}

func (m *MemoryIndex) renderIndex() string {
	var lines []string
	for _, e := range m.entries {
		lines = append(lines, "- ["+e.Category+"] "+e.Summary+" ("+e.TopicFile+")")
	}
	return strings.Join(lines, nl)
}

func (m *MemoryIndex) isOverLimit() bool {
	rendered := m.renderIndex()
	lineCount := strings.Count(rendered, nl) + 1
	byteCount := len(rendered)
	return lineCount > m.maxLines || byteCount > m.maxBytes
}
```
