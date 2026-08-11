# Family folder naming. Hard rule

## The rule

The `## The families` table in `README.md` is the single canonical source of
truth for every family folder name under `patterns/`. A `patterns/<slug>/`
directory's `<slug>` MUST exactly match the slug linked in that table's row
for the corresponding family number. There is no other source of truth for
family folder naming. Not `docs/AUTHORING-QUEUE.json`, not
`tools/gen-indexes.py`'s `FAMILY_TITLES`, not `tools/gen-catalogue-status.py`'s
`FAMILY_ORIGIN`, not memory, not a guess. Those files derive from the table
and must be kept in sync with it, never the reverse.

## Why

Family folder slugs drifted from the README table more than once. For
example, `patterns/11-ddd/` existed on disk while the table linked
`patterns/11-domain-driven-design/`. Each drift meant broken links from the
README to the actual folder, and inconsistent naming across the repo. This
doc and its CI gate exist so that class of mismatch cannot recur silently.

## Enforcement

`tools/check-family-names.py` parses the README families table and asserts
that every `patterns/<slug>/` directory on disk has a slug present in that
table. It is wired into the `structure` job of `.github/workflows/ci.yml` and
runs on every push and pull request. A mismatch fails CI.

Run it locally before opening a PR.

```
python3 tools/check-family-names.py
```

## Renaming a family folder

If a family folder must be renamed, correcting a past drift or an
intentional rename, update all of the following together, in one commit.

1. `git mv patterns/<old-slug> patterns/<new-slug>`
2. The frontmatter `family:` field in every pattern file in that folder
3. `README.md`, in the families table row for that family
4. `tools/gen-indexes.py`, the `FAMILY_TITLES` dict
5. `tools/gen-catalogue-status.py`, the `FAMILY_ORIGIN` dict
6. `dist/catalogue-status.json` and `dist/catalogue-status.csv`, regenerated
7. `docs/AUTHORING-QUEUE.json`, if it references the old slug

Then confirm zero remaining references to the old slug (`grep -rn
"<old-slug>" .` outside `.git/`), regenerate indexes and catalogue status,
and run all five gates (structure, prose, refs, code, markdownlint) before
opening a PR.
