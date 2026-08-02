# Resume Protocol

State lives on disk, never in a conversation. A fresh session with no memory of
this project can pick up exactly where the last one stopped by following the
four steps below. Compaction, a session limit, or a machine restart costs
nothing beyond the entries that were mid-write.

## 1. Where things stand

```bash
cd ~/repositories/patterns
python3 tools/next-batch.py --status
```

Prints per family, done over total, plus the overall count. The definition of
done is a PASS from `tools/check-structure.py`. Nothing else counts, so a
partially written entry is correctly reported as unfinished.

## 2. Get the next batch

```bash
python3 tools/next-batch.py --size 8
```

Prints a JSON array of the next eight unfinished entries, already shaped as the
`args` payload the authoring workflow expects. Add `--family 17-ai-agentic` to
restrict it to one family.

## 3. Run the batch

Invoke the Workflow tool with the lean authoring script and pass the JSON from
step 2 as `args`.

```
scriptPath: ~/.claude/projects/-Users-mirzaiqbal-repositories-patterns/
            <session>/workflows/scripts/patterns-lean.js
args:       <the JSON array from step 2>
```

The script runs in chunks of eight, skips any entry that already passes the
gate, and writes nothing for an entry that is already complete. Re-running a
finished batch costs one cheap gate run per entry.

## 4. Commit and push after every batch

```bash
python3 tools/gen-indexes.py
python3 tools/check-structure.py
python3 tools/check-prose.py
git add -A
git commit -m "feat(<family>): add <entries>"
git push
```

Never let more than one chunk of work sit uncommitted. A limit hit between
commits is the only way to lose finished work.

## Why a compacted session costs nothing

The authoring plan used to live in the assistant's working memory, which made
compaction expensive. It now lives in three files.

| File | Holds |
|---|---|
| `docs/AUTHORING-QUEUE.json` | Every remaining entry, its slug, family, and path |
| `docs/ENTRY-TEMPLATE.md` | The 18-dimension contract every entry must satisfy |
| `tools/next-batch.py` | The only source of truth for what is still outstanding |

An assistant needs no prior knowledge of this project. It needs this file.

## Adding focus briefs

Entries in the queue carry an empty `focus` field. A focus brief tells the
authoring agent which distinctions, failure modes, and citations matter for that
specific pattern, and it is the difference between a competent entry and a sharp
one. Fill it in before running a batch where the pattern has a well known trap,
for example Singleton and double-checked locking, or Observer and the lapsed
listener leak.

An empty focus is acceptable. The template alone produces a valid entry.

## The four decisions that need a human

1. Flipping the repository from private to public.
2. Refreshing the Kimi API key if the second council engine is wanted.
3. Raising `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` beyond the default.
4. Approving any change to the 18-dimension contract.

Everything else runs without input.
