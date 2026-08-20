.PHONY: check structure refs prose code catalogue catalogue-check duplicates duplicates-test all stats

all: check

check: structure prose code refs catalogue-check duplicates-test

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

duplicates:
	@python3 tools/check-duplicates.py --strict

duplicates-test:
	@python3 tools/check-duplicates-test.py

stats:
	@echo "families: $$(ls patterns | wc -l | tr -d ' ')"
	@echo "entries:  $$(find patterns -name '*.md' ! -name 'README.md' | wc -l | tr -d ' ')"
	@echo "words:    $$(find patterns -name '*.md' -exec cat {} + | wc -w | tr -d ' ')"
