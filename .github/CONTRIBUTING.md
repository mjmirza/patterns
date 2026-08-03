<!-- freshness: frozen -->

# Contributing

Every entry in this catalogue carries the eighteen dimensions defined in
`docs/ENTRY-TEMPLATE.md`, and every claim traces to a citation that resolves.
That bar applies equally to a maintainer's own pull request and to a first
time contributor's. Nothing merges by exception.

## Claim your entry before you write it

`main` is protected. every change lands through a pull request, never a
direct push, and the same four gates must pass before a merge is possible.

Before starting work on a queued entry, open a **draft pull request** with
just an empty target file (or the frontmatter stub) at the exact path from
`docs/AUTHORING-QUEUE.json`. That draft PR IS the claim. A CI job (`claim
check`) compares every open PR's added files against every other open PR and
against what is already published on `main`, and fails the newer PR if two
people are working on the same path. Push the real content to that same
branch as you write it; the claim never expires because the PR itself is the
claim.

If you see a `claim check` failure naming your path, someone got there
first. Rebase onto a different, unclaimed entry from the queue instead.

## Before you open a pull request

1. Read `docs/ENTRY-TEMPLATE.md`. It is the schema, not a suggestion.
2. Check `docs/AUTHORING-QUEUE.json` and the family README under
   `patterns/<family>/README.md` so a new entry does not duplicate one
   already published or already queued. Also check `gh pr list` for a draft
   PR already claiming the same path.
3. Run the local gates before you push, the same four gates CI runs:

   ```
   python3 tools/check-structure.py
   python3 tools/check-prose.py
   python3 tools/check-code.py --strict
   python3 tools/validate-refs.py --strict
   npx --yes markdownlint-cli2@0.23.2 "patterns/**/*.md" "docs/**/*.md" README.md
   ```

4. If you touch `docs/AUTHORING-QUEUE.json` or add a published entry, also
   run `python3 tools/gen-indexes.py` and
   `python3 tools/gen-catalogue-status.py`, and commit the files they
   regenerate (family `README.md`, `docs/PROGRESS.md`, `dist/`, the root
   `README.md` badges and table) in the same commit. A stale catalogue status
   is caught in CI and blocks the merge.

## What a pull request needs

- One branch per change, off `main`.
- All eighteen dimensions present, per `docs/ENTRY-TEMPLATE.md`, for a new
  entry, or a clearly scoped fix for anything else (a correction, a citation
  repair, a code fix).
- Every claim in prose either self-evidently true from the code sample shown,
  or backed by a citation in the References section that a reader can follow.
- No invented statistics, no invented production-use claims, no invented
  vendor names. If you cannot cite it, do not claim it.
- Original prose. Do not paste from a textbook or a vendor doc; write the
  explanation in your own words and cite the source you learned it from.

## What kinds of contributions are welcome

- A new pattern entry from the authoring queue, or a new family the queue is
  missing (open an issue with the `new-pattern` template first if the family
  does not exist yet).
- A factual correction to a published entry (`factual-correction` template).
- A citation repair for a link that has gone dead (`citation-problem` or
  `broken-reference` template).
- A duplicate or overlapping entry flag (`duplicate-pattern` template).
- A production-use claim that needs a source or needs retracting
  (`production-use-correction` template).

## Review

Every pull request goes through CI (structure, prose, code compile,
citations, markdown style) before a maintainer reviews it. A red CI is never
merged. See `.github/PULL_REQUEST_TEMPLATE.md` for what the description
should contain.

## License

By contributing, you agree your contribution is licensed under this
repository's CC BY 4.0 license (see `LICENSE`), and that you have the right to
license it that way.
