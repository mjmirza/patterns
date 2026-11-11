.PHONY: check structure refs prose code links catalogue catalogue-check by-problem-by-language by-problem-by-language-check entries entries-check duplicates duplicates-test test all stats

all: check

check: test structure prose links code refs catalogue-check by-problem-by-language-check entries-check duplicates-test

structure:
	@python3 tools/check-structure.py

refs:
	@python3 tools/validate-refs.py --strict

prose:
	@python3 tools/check-prose.py

links:
	@python3 tools/check-links.py

entries:
	@python3 tools/gen-entry-index.py

entries-check: entries
	@git ls-files --error-unmatch dist/entries.json >/dev/null || \
		(echo "dist/entries.json is not tracked. Run 'make entries' and commit it." && exit 1)
	@git diff --exit-code -- dist/entries.json || \
		(echo "Entry index is stale. Run 'make entries' and commit." && exit 1)

code:
	@python3 tools/check-code.py --strict

catalogue:
	@python3 tools/gen-catalogue-status.py

catalogue-check: catalogue
	@git diff --exit-code -- README.md docs/PROGRESS.md dist/catalogue-status.json dist/catalogue-status.csv || \
		(echo "Catalogue status is stale. Run 'make catalogue' and commit." && exit 1)

by-problem-by-language:
	@python3 tools/gen-by-problem-by-language.py

by-problem-by-language-check: by-problem-by-language
	@git diff --exit-code -- docs/BY-PROBLEM.md docs/BY-LANGUAGE.md || \
		(echo "Discovery pathway indexes are stale. Run 'make by-problem-by-language' and commit." && exit 1)

test:
	@python3 tools/check-structure-test.py
	@python3 tools/check-links-test.py
	@python3 tools/check-family-names-test.py
	@python3 tools/check-prose-test.py
	@python3 tools/gen-indexes-test.py
	@python3 tools/gen-by-problem-by-language-test.py
	@python3 tools/gen-catalogue-status-test.py
	@python3 tools/check-code-test.py
	@python3 tools/check-claims-test.py
	@python3 tools/next-batch-test.py

duplicates:
	@python3 tools/check-duplicates.py --strict

duplicates-test:
	@python3 tools/check-duplicates-test.py

stats:
	@echo "families: $$(ls patterns | wc -l | tr -d ' ')"
	@echo "entries:  $$(find patterns -name '*.md' ! -name 'README.md' | wc -l | tr -d ' ')"
	@echo "words:    $$(find patterns -name '*.md' -exec cat {} + | wc -w | tr -d ' ')"
