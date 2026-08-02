.PHONY: check structure refs prose links all

all: check

check: structure prose refs links

structure:
	@python3 tools/check-structure.py

refs:
	@python3 tools/validate-refs.py --strict

prose:
	@python3 tools/check-prose.py

links:
	@python3 tools/check-links.py

stats:
	@echo "families: $$(ls patterns | wc -l | tr -d ' ')"
	@echo "entries:  $$(find patterns -name '*.md' ! -name 'README.md' | wc -l | tr -d ' ')"
	@echo "words:    $$(find patterns -name '*.md' -exec cat {} + | wc -w | tr -d ' ')"
