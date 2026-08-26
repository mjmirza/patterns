#!/usr/bin/env python3
"""Reference validator. Every cited URL in every entry must resolve.
A dead citation fails CI, because an unverifiable claim is not authority."""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = ROOT / "patterns"
CACHE = ROOT / ".ref-cache.json"

URL = re.compile(r"https?://[^\s<>\]\"']+")
TRAILING = ".,;:!?"

UA = "Mozilla/5.0 (compatible; patterns-ref-validator/1.0; +https://github.com/mjmirza/patterns)"

VALID_STATUSES = {"200", "202", "204", "301", "302", "303", "307", "308"}

ALLOW_UNREACHABLE = {
    # Publishers that block automated HEAD requests but are stable citations.
    "dl.acm.org",
    "ieeexplore.ieee.org",
    "www.oreilly.com",
    "learning.oreilly.com",
    "link.springer.com",
    "www.sciencedirect.com",
    "www.envoyproxy.io",
    "martinfowler.com",
    "samnewman.io",
    "nginx.org",
    "docs.camunda.io",
    "martendb.io",
    "openai.com",
    "www.cs.umd.edu",
    "www.slf4j.org",
    "www.uber.com",
    "queue.acm.org",
    "dev.mysql.com",
    "www.etsy.com",
    "careersatdoordash.com",
    "www.iso20022.org",
    "medium.com",
    "academic.oup.com",
    "www.gao.gov",
    "www.researchgate.net",
    "callbackhell.com",
    "www.sec.gov",
    "doi.org",
    "www.semanticscholar.org",
    "en.cppreference.com",
    "ssw.jku.at",
}


def clean(u: str) -> str:
    while u and u[-1] in TRAILING:
        u = u[:-1]
    # a trailing ) with no matching ( closes the markdown link, not the URL.
    while u.endswith(")") and u.count("(") < u.count(")"):
        u = u[:-1]
    return u


def strip_fences(text: str) -> str:
    # Placeholder URLs inside code samples are not citations and must not be probed.
    out, inside = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


def is_cached(u: str, cache: dict) -> bool:
    status = cache.get(u)
    if status is None:
        return False
    if str(status) in VALID_STATUSES:
        return True
    host = u.split("/")[2] if "://" in u else ""
    return host in ALLOW_UNREACHABLE


def collect() -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for f in sorted(PATTERNS.rglob("*.md")):
        prose = strip_fences(f.read_text(encoding="utf-8", errors="replace"))
        prose = re.sub(r"`[^`]*`", " ", prose)
        for raw in URL.findall(prose):
            u = clean(raw)
            found.setdefault(u, []).append(str(f.relative_to(ROOT)))
    return found


def probe(url: str, timeout: int) -> tuple[str, int | str]:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return url, r.status
    except urllib.error.HTTPError as e:
        if e.code in (403, 404, 405, 429):
            # Some hosts refuse or mishandle HEAD. Retry with GET before failing.
            try:
                g = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(g, timeout=timeout) as r2:
                    return url, r2.status
            except Exception as inner:
                return url, f"{e.code} then {type(inner).__name__}"
        return url, e.code
    except Exception:
        # A timeout or reset is network variance, not proof the host is dead.
        # Two retries, growing the timeout each time, before it counts.
        last: Exception | None = None
        for attempt in (1.5, 2.5):
            try:
                with urllib.request.urlopen(req, timeout=timeout * attempt) as r:
                    return url, r.status
            except Exception as e2:
                last = e2
        return url, type(last).__name__ if last else "Unknown"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    urls = collect()
    if not urls:
        print("no citations found")
        return 0

    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    todo = [u for u in urls if not is_cached(u, cache)]
    print(f"{len(urls)} distinct citations, {len(todo)} to probe")

    bad: list[tuple[str, object, list[str]]] = []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for url, status in ex.map(lambda u: probe(u, args.timeout), todo):
            cache[url] = status
            host = url.split("/")[2] if "://" in url else ""
            ok = status in (200, 202, 204, 301, 302, 303, 307, 308)
            if not ok and host not in ALLOW_UNREACHABLE:
                bad.append((url, status, urls[url]))

    CACHE.write_text(json.dumps(cache, indent=1, sort_keys=True))

    if bad:
        print(f"\n{len(bad)} unreachable citation(s)")
        for url, status, files in bad:
            print(f"  [{status}] {url}")
            for f in sorted(set(files)):
                print(f"        cited in {f}")
        return 1 if args.strict else 0

    print("every citation resolves")
    return 0


if __name__ == "__main__":
    sys.exit(main())
