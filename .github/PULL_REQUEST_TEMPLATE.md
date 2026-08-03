## What this changes

<!-- One or two sentences. A new entry, a correction, a citation repair, tooling. -->

## Verification

<!-- Paste the real output of the four gates you ran locally. Not a claim that
     they pass -- the actual command output. -->

- [ ] `python3 tools/check-structure.py`
- [ ] `python3 tools/check-prose.py`
- [ ] `python3 tools/check-code.py --strict`
- [ ] `python3 tools/validate-refs.py --strict`
- [ ] `npx --yes markdownlint-cli2@0.23.2 ...`
- [ ] If a published entry or the queue changed: `tools/gen-indexes.py` and
      `tools/gen-catalogue-status.py` were re-run and the regenerated files
      are committed in this PR.

## For a new or corrected entry

- [ ] All eighteen dimensions from `docs/ENTRY-TEMPLATE.md` are present.
- [ ] Every factual claim traces to a citation that resolves.
- [ ] No invented statistics, production-use claims, or vendor names.
- [ ] Prose is original, not paraphrased from a single source without
      attribution.

## Notes for reviewers

<!-- Anything a reviewer should specifically look at: a contested
     classification, a claim you are not fully sure of, a source you could
     not independently confirm. -->
