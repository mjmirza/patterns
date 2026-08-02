#!/usr/bin/env bash
# Authors pattern entries via the Codex CLI, which draws on the OpenAI
# subscription rather than the Claude one. See docs/RESUME.md.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SIZE="${SIZE:-4}"
FAMILY="${FAMILY:-}"
TIMEOUT="${TIMEOUT:-1800}"
LOGDIR="$REPO/.codex-logs"

mkdir -p "$LOGDIR"
command -v codex >/dev/null 2>&1 || { echo "codex CLI not found" >&2; exit 1; }

BANNED="just, leverage, delve, robust, seamless, comprehensive, crucial, vital, essential, unlock, elevate, journey, landscape, realm, harness, empower, streamline, cutting-edge, game-changer, ensure, furthermore, moreover, additionally, showcase, underscore, foster, nurture, potential, innovative, significant, notably, remarkably, meticulous, intricate"

args=(--size "$SIZE")
[[ -n $FAMILY ]] && args+=(--family "$FAMILY")

batch="$(python3 "$REPO/tools/next-batch.py" "${args[@]}")" || exit 1
count="$(printf '%s' "$batch" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')"
[[ $count == 0 ]] && { echo "queue empty for this filter"; exit 0; }

echo "codex authoring $count entries, ${TIMEOUT}s each"

field() {
  printf '%s' "$batch" | python3 -c "import json,sys; print(json.load(sys.stdin)[$1].get('$2',''))"
}

for i in $(seq 0 $((count - 1))); do
  name="$(field "$i" name)"
  path="$(field "$i" path)"
  slug="$(field "$i" slug)"
  focus="$(field "$i" focus)"

  echo "[$((i + 1))/$count] $name -> $path"

  prompt="Author a MASTER-LEVEL software pattern entry for '$name'.

READ FIRST, both mandatory.
1. $REPO/docs/ENTRY-TEMPLATE.md   the 18-dimension contract
2. $REPO/patterns/01-gof/factory-method.md   the reference standard for depth and citation style

WRITE THE FILE TO: $REPO/$path

Target 6000 to 9000 words of prose. All 18 dimensions, in order, with the exact
heading numbering used in the reference entry.

NON-NEGOTIABLE.
1. ORIGINAL PROSE. Never copy or closely paraphrase a source. refactoring.guru is forbidden as a text source.
2. VERIFY EVERY CITATION with a live web fetch before citing it. Cite URLs with the verification date 2026-08-02. Cite books by author, title, edition and chapter, and a page only where you confirmed it. If you cannot verify a source, do not cite it and do not make the claim.
3. Minimum 3 named production uses, each with a real source.
4. Code in at least 3 languages from TypeScript, Python, Java, Go, Rust, Swift. Compile or run each. javac, rustc, go, python3, node and swiftc are installed.
5. ASCII structure diagram AND dynamics diagram, inside fenced code blocks only, readable at 80 columns.
6. Dimension 4 needs an explicit non-applicability list. Dimension 11 needs Symptom, Cause, Fix triples with observable symptoms.
7. Label engineering judgement as judgement, never as a sourced fact.

BANNED IN THE FILE, the repo gates reject the write.
- Em dash and en dash characters. Use periods and commas.
- Triple-dash as a section separator. Allowed only as the YAML frontmatter delimiters at the very top.
- These words and their inflections: $BANNED
- Emojis.

${focus:+MUST COVER EXPLICITLY, each with its own citation:
$focus
}
BEFORE YOU FINISH, run and satisfy both.
  cd $REPO && python3 tools/check-structure.py 2>/dev/null | grep '$path'
  cd $REPO && python3 tools/check-prose.py 2>/dev/null | tail -2
Your file must print PASS. Fix and re-run until it does."

  ( cd "$REPO" && timeout "$TIMEOUT" codex exec --skip-git-repo-check -s workspace-write "$prompt" < /dev/null ) \
    > "$LOGDIR/$slug.log" 2>&1
  rc=$?

  if [[ -f $REPO/$path ]]; then
    words="$(wc -w < "$REPO/$path" | tr -d ' ')"
    if python3 "$REPO/tools/check-structure.py" 2>/dev/null | grep -q "^PASS $path$"; then
      echo "      PASS  $words words"
    else
      echo "      WROTE but FAILS gate  $words words  see $LOGDIR/$slug.log"
    fi
  else
    echo "      NO FILE  rc=$rc  see $LOGDIR/$slug.log"
  fi
done

echo
python3 "$REPO/tools/next-batch.py" --status | tail -3
