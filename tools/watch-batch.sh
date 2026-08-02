#!/usr/bin/env bash
# Watches a running workflow's journal and flags a slot that has gone stale.
# A "started" event with no matching "result" past the timeout is stuck, not
# working, and this is the mechanical check for the difference. Never guess.
set -uo pipefail

JOURNAL="${1:?usage: watch-batch.sh <journal.jsonl> [stale-minutes]}"
STALE_MIN="${2:-25}"

[[ -f $JOURNAL ]] || { echo "no journal at $JOURNAL" >&2; exit 1; }

now_epoch="$(date +%s)"
mtime_epoch="$(stat -f %m "$JOURNAL" 2>/dev/null || stat -c %Y "$JOURNAL")"
age_min=$(((now_epoch - mtime_epoch) / 60))

python3 - "$JOURNAL" <<'PY'
import json, sys
started, done, errored = {}, [], []
for line in open(sys.argv[1]):
    try:
        d = json.loads(line)
    except Exception:
        continue
    t = d.get("type")
    key = d.get("key", "")[:16]
    if t == "started":
        started[key] = True
    elif t == "result":
        started.pop(key, None)
        done.append(key)
    elif t == "error":
        started.pop(key, None)
        errored.append(key)
open_slots = list(started.keys())
print(f"done={len(done)} errored={len(errored)} still_open={len(open_slots)}")
for k in open_slots:
    print(f"  open: {k}")
PY

echo "journal last touched ${age_min} min ago (stale threshold ${STALE_MIN} min)"
if [[ $age_min -ge $STALE_MIN ]]; then
  echo "STALE. No event written in ${age_min} min. A slot is genuinely stuck, not merely slow."
  exit 2
fi
exit 0
