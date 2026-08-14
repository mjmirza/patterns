.PHONY: check structure refs prose code catalogue catalogue-check all stats

all: check

check: structure prose code refs catalogue-check

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
	@python3 tools/gen-by-problem-by-language.py

catalogue-check: catalogue
	@git diff --exit-code -- README.md docs/PROGRESS.md dist/ docs/BY-PROBLEM.md docs/BY-LANGUAGE.md || \
		(echo "Catalogue status is stale. Run 'make catalogue' and commit." && exit 1)

stats:
	@echo "families: $$(ls patterns | wc -l | tr -d ' ')"
	@echo "entries:  $$(find patterns -name '*.md' ! -name 'README.md' | wc -l | tr -d ' ')"
	@echo "words:    $$(find patterns -name '*.md' -exec cat {} + | wc -w | tr -d ' ')"
