export const meta = {
  name: 'patterns-lean',
  description: 'Author pattern entries. Every completion is confirmed by re-running the deterministic gate, never trusted from the agent\'s own report. A stuck agent times out and retries automatically.',
  phases: [{ title: 'Author' }, { title: 'Verify' }],
}

// A stuck agent that never returns must not hang the batch forever, and its
// slot must count as failed so the existing retry logic picks it up.
const AGENT_TIMEOUT_MS = 30 * 60 * 1000
const GATE_TIMEOUT_MS = 5 * 60 * 1000

function withTimeout(promise, ms, onTimeout) {
  let timer
  const timeout = new Promise((resolve) => {
    timer = setTimeout(() => resolve(onTimeout()), ms)
  })
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer))
}

const REPO = '/Users/mirzaiqbal/repositories/patterns'

const BANNED = [
  'just','leverage','delve','robust','seamless','comprehensive','crucial','vital',
  'essential','unlock','elevate','journey','landscape','realm','harness','empower',
  'streamline','cutting-edge','game-changer','ensure','furthermore','moreover',
  'additionally','showcase','underscore','foster','nurture','potential','innovative',
  'significant','notably','remarkably','meticulous','intricate','dive into','at its core',
].join(', ')

function authorPrompt(e) {
  return `Author a MASTER-LEVEL pattern entry for **${e.name}** (${e.category}).

This file does not exist yet, or it exists and failed the gate on the last check.
That was already verified before you were dispatched, so do not re-check it and
do not skip. If a partial file exists at ${e.path}, read it, keep every part
already written, and add only what is missing. Otherwise write it from scratch.

READ BEFORE WRITING:
1. ${REPO}/docs/ENTRY-TEMPLATE.md  (the 18-dimension contract, mandatory)
2. ${REPO}/patterns/01-gof/factory-method.md  (reference standard for depth and citation style)

WRITE TO: ${REPO}/${e.path}

Target 6000 to 9000 prose words. Do not pad past that. Depth means specificity,
not length, and every extra thousand words costs real budget.

NON-NEGOTIABLE:
1. ORIGINAL PROSE ONLY. Never copy or closely paraphrase. refactoring.guru is FORBIDDEN as a text source.
2. VERIFY EVERY CITATION LIVE with WebFetch or WebSearch before citing. URLs cite verification date 2026-08-02. Books cite author, title, edition, chapter, and a page only where you confirmed it. If you cannot verify, do not claim. Report unverifiable claims in your final message.
3. Named production uses, minimum 3, each with a real source.
4. Code in at least 3 languages from TypeScript, Python, Java, Go, Rust, Swift. COMPILE OR RUN each one. javac, rustc, go, python3, node and swiftc are all installed. State anything you could not run.
5. ASCII structure diagram AND dynamics diagram, fenced code blocks only, 80 columns.
6. Dimension 4 needs an explicit non-applicability list. Dimension 11 needs Symptom, Cause, Fix triples with observable symptoms.
7. Label engineering judgement as judgement. Do not dress it as a sourced fact. See the judgement-versus-sourced-claim section of the template.

${e.focus ? 'MUST COVER EXPLICITLY, each with its own citation:\n' + e.focus + '\n' : ''}
BANNED IN THE FILE (repo gates reject the write):
- Em dash and en dash. Use periods and commas.
- Triple-dash as a section separator. Allowed ONLY as YAML frontmatter delimiters at the very top.
- These words and inflections: ${BANNED}
- Emojis.
- Placeholder URLs are fine inside code fences. Never an unverified URL in prose.

BEFORE REPORTING DONE, run:
  cd ${REPO} && python3 tools/check-structure.py 2>/dev/null | grep '${e.path}'
  cd ${REPO} && python3 tools/check-prose.py 2>/dev/null | tail -3
  cd ${REPO} && python3 tools/check-code.py --only ${e.slug} --strict
The structure grep must show PASS. check-code.py must report 0 failed.
This is the exact command CI runs; a green here means CI will not catch a
compile error you missed. Fix and re-run until both are clean.

Report in under 120 words: file path, dimensions out of 18, verified citation count, gate result, unverifiable claims.`
}

// The agent echoes raw output, never classifies it. A classifying agent
// once fabricated a PASS line for a file check-structure.py never mentioned.
async function gateCheck(paths) {
  if (!paths.length) return new Set()
  const out = await withTimeout(
    agent(
      `Run exactly this command and reply with ONLY its raw stdout, byte for ` +
      `byte, no commentary before or after, no summary, no classification:\n` +
      `cd ${REPO} && python3 tools/check-structure.py 2>/dev/null`,
      { label: 'gate-check', phase: 'Verify' },
    ),
    GATE_TIMEOUT_MS,
    () => null,
  )
  const passing = new Set()
  for (const line of String(out || '').split('\n')) {
    const m = line.match(/^PASS\s+(\S+)/)
    if (m && paths.includes(m[1])) passing.add(m[1])
  }
  return passing
}

// RENAME_OK: rewritten loop verifies via the gate, not the return value.
const raw = typeof args === 'string' ? JSON.parse(args) : args
const batch = Array.isArray(raw) ? raw : raw.entries
// 3 was empirically the ceiling: batches of 8 lost the same 3 slots at the
// same token count (534.9k) twice in a row, a resource wall, not chance.
const CHUNK = (Array.isArray(raw) ? 3 : raw.chunk) || 3
const MODEL = Array.isArray(raw) ? undefined : raw.model

log(`${batch.length} entries, chunks of ${CHUNK}, gate-verified completion, ${AGENT_TIMEOUT_MS / 60000}min stuck-agent timeout`)

function launch(e, labelSuffix = '') {
  return withTimeout(
    agent(authorPrompt(e), {
      label: `author:${e.slug}${labelSuffix}`,
      phase: 'Author',
      ...(MODEL ? { model: MODEL } : {}),
    }),
    AGENT_TIMEOUT_MS,
    () => null,
  )
}

const done = []
const stillFailing = []
for (let i = 0; i < batch.length; i += CHUNK) {
  const slice = batch.slice(i, i + CHUNK)
  log(`chunk ${Math.floor(i / CHUNK) + 1}, ${slice.map((e) => e.slug).join(', ')}`)
  await parallel(slice.map((e) => () => launch(e)))

  let passing = await gateCheck(slice.map((e) => e.path))
  let pending = slice.filter((e) => !passing.has(e.path))

  // Retry anything the gate did not confirm: timeout, error, or a claim
  // that was not backed by an actual passing file. Never trust the text.
  if (pending.length) {
    log(`gate did not confirm ${pending.length}: ${pending.map((e) => e.slug).join(', ')}, retrying once`)
    await parallel(pending.map((e) => () => launch(e, ' (retry)')))
    const retryPassing = await gateCheck(pending.map((e) => e.path))
    passing = new Set([...passing, ...retryPassing])
    pending = pending.filter((e) => !retryPassing.has(e.path))
  }

  done.push(...slice.filter((e) => passing.has(e.path)))
  stillFailing.push(...pending)
  log(`chunk complete, ${done.length}/${batch.length} gate-confirmed so far, ${stillFailing.length} still failing`)
}

return {
  attempted: batch.length,
  gate_confirmed: done.length,
  entries: done.map((e) => e.slug),
  still_failing: stillFailing.map((e) => e.slug),
}
