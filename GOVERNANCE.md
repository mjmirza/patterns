# Governance

This catalogue has one maintainer. [MAINTAINERS.md](MAINTAINERS.md) names
that person. `.github/CODEOWNERS` gives them every path until a family has
its own reviewer.

## What a maintainer decides

- Whether an entry's `maturity` is `canonical`, `established`, `emerging`,
  `contested`, or `deprecated`.
- Whether a proposed pattern is a real, citable pattern or a rename of one
  already published. `docs/CATALOG-COMPARISON.md` records the comparisons
  already made. A new family is a scope decision. Open a `new-pattern` issue
  before adding the family. Do not invent entries to close a numeric gap.
- Whether a deferred queue row in `docs/AUTHORING-QUEUE.json` may be
  authored. The three deferred rows say why they stay deferred. Do not
  author them from a guess.
- Disputes about a published claim. Use the matching issue template under
  `.github/ISSUE_TEMPLATE/`. A correction lands as a pull request that
  passes the same gates as a new entry.

## What the tools decide

`tools/check-structure.py` checks the eighteen dimensions.
`tools/check-prose.py` checks prose shape.
`tools/check-code.py` compiles samples.
`tools/validate-refs.py` checks that a cited URL answers.
`tools/check-links.py` checks internal links, entry ids, kinds, review
dates, and the relationship lists.
`tools/check-duplicates.py` warns on name collisions.
`tools/gen-catalogue-status.py` and `tools/gen-entry-index.py` regenerate
the counts and `dist/entries.json`.

A URL that returns success is not proof the page supports the sentence
beside it. That limit is stated in [docs/CITATION-POLICY.md](docs/CITATION-POLICY.md).
No tool in this repository pretends to close it.

## Identity

Every entry carries an id of the form `pat.<family number>.<slug>`. Twelve slugs are
published in more than one family. Those relationships use `family/slug`.
A bare slug is allowed only when one file owns it.

`related` and `incompatible_with` are catalogue links.
`related_concepts` and `incompatible_concepts` are names that are not
published entries. Keeping them separate is how a typo becomes a failed
check instead of a silent break.

## Review dates

`verified`, `last_reviewed`, and `next_review_due` are calendar dates.
`last_reviewed` was filled from `verified` when those fields were added.
`next_review_due` is 180 days after `last_reviewed` until someone who
re-reads the entry sets a new date. The stale-entry count in the README
still comes from git history, via `tools/gen-catalogue-status.py`, not
from this date.

Eight release entries had `verified` set to the boolean true. Those dates were repaired
from the commit date of the file. That is the only dated record those
files had.

## License

Contributions are licensed under the OpenRoots Agent License 2.3. See
`LICENSE` and `.github/CONTRIBUTING.md`.
