.PHONY: check structure refs prose code catalogue catalogue-check by-problem-by-language by-problem-by-language-check duplicates duplicates-test test all stats

all: check

check: test structure prose code refs catalogue-check by-problem-by-language-check duplicates-test

structure:
	@python3 tools/check-structure.py

refs:
	@python3 tools/validate-refs.py --strict

prose:
	@python3 tools/check-prose.py

code:
	@python3 tools/check-code.py --strict

catalogue:
	@python3 tools/gen-catalogue-status.py

catalogue-check: catalogue
	@git diff --exit-code -- README.md docs/PROGRESS.md dist/ || \
		(echo "Catalogue status is stale. Run 'make catalogue' and commit." && exit 1)

by-problem-by-language:
	@python3 tools/gen-by-problem-by-language.py

by-problem-by-language-check: by-problem-by-language
	@git diff --exit-code -- docs/BY-PROBLEM.md docs/BY-LANGUAGE.md || \
		(echo "Discovery pathway indexes are stale. Run 'make by-problem-by-language' and commit." && exit 1)

test:
	@python3 tools/check-structure-test.py
	@python3 tools/check-family-names-test.py
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
