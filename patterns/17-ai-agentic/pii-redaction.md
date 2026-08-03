---
name: PII Redaction
slug: pii-redaction
family: 17-ai-agentic
category: AI Agentic
aliases: [PII Scrubbing, PII Masking, De-identification, Sensitive Data Redaction, Data Sanitization Guardrail]
first_described: "Sweeney 2002 (k-anonymity, structured-data de-identification); HHS 45 CFR 164.514(b)(2) Safe Harbor 2000; OWASP LLM02 2025 edition, Sensitive Information Disclosure (agentic/LLM framing)"
maturity: established
related: [input-guardrails, output-guardrails, function-calling, structured-output, tool-result-caching, agent-memory, model-context-protocol, retrieval-augmented-generation, chunking-strategies]
incompatible_with: []
verified: 2026-08-03
---

# PII Redaction

## 1. Name, aliases, and lineage

The pattern described here is commonly called PII Redaction inside agent and
LLM pipelines, and the underlying idea is older than the models it now
protects. It is a detection-and-transformation stage that finds spans of
personally identifiable information in text, structured payloads, or tool
arguments, and replaces or removes those spans before the data crosses a
trust boundary, most commonly the boundary into a model's context window, the
boundary into a log or cache, or the boundary out of a model's response back
to a person.

Two lineages feed the current name. The first is statistical disclosure
control for structured data, formalized as k-anonymity by Latanya Sweeney,
who defined a released table as k-anonymous when each combination of
quasi-identifying attributes matches at least k rows, so no single row can be
singled out by those attributes alone (summarized in Wikipedia, "De-identification",
https://en.wikipedia.org/wiki/De-identification, verified
2026-08-03, citing Sweeney's original formulation). The same period produced
the regulatory definition still in force for health data in the United
States, the Safe Harbor method under the HIPAA Privacy Rule, 45 CFR
164.514(b)(2), which lists specific identifier categories, names,
geographic subdivisions smaller than a state, telephone and fax numbers,
electronic mail addresses, social security numbers, medical record numbers,
health plan beneficiary numbers, account numbers, certificate or license
numbers, vehicle and device identifiers, URLs, IP addresses, biometric
identifiers, full-face photographs, and any other unique identifying number
or code, that must be removed for a health record to count as de-identified
(Cornell Law School, Legal Information Institute, 45 CFR 164.514,
https://www.law.cornell.edu/cfr/text/45/164.514, verified 2026-08-03). Safe
Harbor also requires dates to be generalized to year only and ZIP codes
truncated to three digits for the released record to qualify.

The second lineage is the practice of PII detection and anonymization as a
software component, independent of any particular regulation. Amazon
Comprehend shipped PII entity detection and redaction as an API in its
document analysis service, returning typed entities such as `NAME`,
`SSN`, and `CREDIT_DEBIT_NUMBER` with confidence scores and character
offsets, and a separate redaction mode that returns the input text with each
detected span replaced by asterisks (Amazon Web Services, "Detecting PII
entities", Amazon Comprehend Developer Guide,
https://docs.aws.amazon.com/comprehend/latest/dg/how-pii.html, verified
2026-08-03). Google's equivalent product, marketed originally as Cloud Data
Loss Prevention and now as Sensitive Data Protection, exposes a family of
de-identification transformations rather than a single redact action, a
character masking that replaces characters with a symbol, a full redaction
that removes the value, a cryptographic hashing that pseudonymizes a value
into a stable surrogate, a date shifting that perturbs dates while preserving
interval relationships, and bucketing or generalization (Google Cloud,
"De-identify sensitive data",
https://docs.cloud.google.com/sensitive-data-protection/docs/deidentify-sensitive-data,
verified 2026-08-03). Microsoft's open-source contribution, Presidio,
frames the same job as two cooperating modules, an Analyzer that identifies
PII using "Named Entity Recognition, regular expressions, rule based logic
and checksum with relevant context in multiple languages", and an Anonymizer
that applies operators such as replace, mask, redact, hash, or encrypt to the
spans the Analyzer finds, with a companion Image Redactor that applies the
same idea to images via OCR (Presidio documentation,
https://presidio.dataprivacystack.org/, verified 2026-08-03, the project
began under `microsoft/presidio` on GitHub and moved to the Data Privacy
Stack organization).

The name PII Redaction, applied specifically to agent and LLM pipelines, is
newer. It appears as a named mitigation inside the OWASP Top 10 for Large
Language Model Applications, in the entry OWASP catalogs as LLM02 in the
2025 edition, titled Sensitive Information Disclosure, which lists
"Sanitization" and "Tokenization and Redaction" among its data protection
techniques, describing the second as using "pattern matching to detect and
redact confidential content before processing" (OWASP GenAI Security Project,
https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/,
verified 2026-08-03). Inside that entry the pattern sits alongside input
guardrails and output guardrails as one of the concrete transformations a
guardrail can apply, rather than as a separate risk category of its own.

A note on scope, because the alias list above hides a real distinction. PII
Redaction as covered in this entry is a text and payload transformation
applied inline in a running pipeline. It is a close cousin of, but not the
same pattern as, differential privacy, which perturbs aggregate statistics
or training gradients with calibrated noise so no single training example
can be recovered, and k-anonymity as applied to a released structured
dataset, which groups rows rather than transforming free text. Those two are
named as related, contrasted approaches in dimension 12 rather than treated
as the same mechanism.

## 2. Problem and context

An agent pipeline routinely moves text through places where a human name, an
email address, a card number, or a medical record number does not belong.
retrieval-augmented-generation pulls a support ticket into a prompt so the
model can answer a follow-up question, and the ticket contains a customer's
home address. A tool call returns a database row so an agent can summarize
an account, and the row contains a social security number. A conversation
gets written to long-term agent memory so the assistant remembers the user
next session, and the raw transcript contains a credit card number the user
typed while asking for help with a billing dispute. A request and response
pair gets logged for debugging, and the log now holds the same sensitive
value in plaintext, outside any of the access controls that protected it in
the source system.

None of these are adversarial. Nobody is trying to exfiltrate data. The
context is written by a well-meaning developer wiring one API to another,
and the sensitive value travels because moving text between systems is
exactly what the pipeline is built to do. The problem PII Redaction answers
is narrower than "prevent data breaches" and more specific, at each
point a payload crosses a trust boundary, whether that is the boundary into
a third-party model provider, the boundary into a durable store, or the
boundary from the model back to a screen, does the payload still contain
values that identify a natural person, and if so, transform or remove them
before the crossing completes.

The context that makes this pattern necessary rather than optional is
regulatory and contractual as much as technical. GDPR defines personal
data broadly, "any information relating to an identified or identifiable
natural person ('data subject')" (European Union, General Data Protection
Regulation, Article 4(1), https://gdpr-info.eu/art-4-gdpr/, verified
2026-08-03), which means a system that forwards personal data to a model
provider is a controller making a processing decision, and that decision
needs either a lawful basis and a data processing agreement, or a technical
control that removes the personal data before the forwarding happens.
HIPAA's Safe Harbor route exists precisely because de-identified data falls
outside the Privacy Rule's restrictions once the 18 identifier categories
are gone (Cornell LII, 45 CFR 164.514, cited above). PII Redaction is the
pattern that makes either compliance path technically enforceable inside a
pipeline that was not designed, from the outset, to keep sensitive fields
walled off.

## 3. Forces

**Recall versus precision.** A detector tuned to catch every possible name,
address, and account number will also flag ordinary text, a person's first
name that happens to match a common word, a product SKU shaped like a phone
number, a version string shaped like a credit card. A detector tuned to
avoid those false positives will miss real PII in unusual formats,
misspellings, or languages the recognizer was not built for. The pattern
cannot maximize both at once, and the two error types have different costs,
a missed detection leaks a person's data, a false positive corrupts the
text a downstream consumer, human or model, needs to reason correctly.

**Reversibility versus data minimization.** A pipeline that needs to restore
the original value later, to display it back to the authorized user, to
apply a business rule that depends on the real account number, needs a
reversible transform, a token vault, a pseudonym mapping, or a
format-preserving encryption. A pipeline that never needs the original value
again should prefer an irreversible transform, because the reversible
mapping is itself a new store of the exact data the pattern exists to
protect, and every additional copy of sensitive data is additional risk.

**Fidelity versus safety.** Full redaction, replacing "my card number is
4111 1111 1111 1111" with "my card number is [CREDIT_CARD]", removes the
information a downstream model might need to reason about the request, for
example to confirm the last four digits match a stored record. Partial
masking that preserves format and a few characters, "4111 **** **** 1111",
keeps enough shape for the reasoning to work but discloses fewer digits than
raw text. The pattern sits on a spectrum from full removal to light masking,
and the right point on that spectrum is a product decision, not a
technical default.

**Latency and cost versus coverage.** A regex and checksum pass over a
request is single-digit milliseconds. A named entity recognition model adds
tens to low hundreds of milliseconds depending on model size and hardware,
and a second LLM call used as a PII classifier adds a full round trip, often
hundreds of milliseconds to seconds. An agent pipeline making several tool
calls per turn pays this cost at every crossing point it protects, so
coverage has to be weighed against the total latency budget of the turn.

**Where in the pipeline the check runs.** Running redaction only on the
final user-visible output protects the person reading the screen, but does
nothing about the value sitting in the model provider's logs, the vector
store, or the agent's memory. Running it only on input protects the model
provider from ever seeing the raw value, but a model that already
memorized similar data from training, or that receives PII through a tool
result rather than the direct prompt, can still reproduce something
sensitive on the way out. The pattern generally needs more than one
crossing point instrumented, which raises both the cost and the
maintenance burden discussed in dimension 3's latency force.

**Auditability versus the redaction itself.** A compliance program needs to
prove redaction ran, which usually means logging that a `CREDIT_CARD` span
was found and removed at a timestamp. Logging the fact of a detection is
safe. Logging the detected text defeats the entire pattern by creating the
exact leak the redaction pass exists to prevent, so the audit trail has to
be designed to prove behavior without repeating the sensitive value.

## 4. Applicability and non-applicability

Reach for PII Redaction when:

- Text or structured data that may contain a natural person's identifying
  information is about to cross into a third-party model provider's
  context window, and the provider's data processing terms do not already
  cover the sensitivity level of that data.
- A conversation, tool result, or retrieved document is about to be written
  to a durable store, a vector database, an agent memory table, an
  application log, or a cache, that has broader read access or a longer
  retention period than the original source system.
- A regulation or contract specifically names de-identification as a
  qualifying control, such as HIPAA's Safe Harbor method, and the pipeline
  needs that specific legal status rather than a general access control.
- A model's raw output is shown to a user who is not authorized to see the
  underlying identifiable data, for example a support agent's LLM summary
  shown to a different team that should see aggregate patterns but not
  individual customer identities.
- Retrieval brings unstructured documents, tickets, transcripts, emails,
  into a prompt from a corpus that was never curated to be PII-free, which
  is the normal case for retrieval-augmented-generation over real
  operational data.

Do NOT reach for PII Redaction when:

- The data never leaves a system that already has the correct legal basis,
  access controls, and retention policy for that exact data, for example a
  single-tenant, self-hosted model serving only the data's own owner with no
  third party in the loop and no additional persistence. Adding a redaction
  pass here adds latency and failure modes for no additional protection.
- The task genuinely requires the identifying value to complete correctly,
  and no downstream reviewer needs the identifying value hidden, for
  example an internal fraud investigation tool whose entire purpose is
  correlating account numbers across systems. Redacting the account number
  here breaks the tool.
- Structured, tabular data is being prepared for statistical release or
  research sharing rather than passed through a live text pipeline. That
  case calls for k-anonymity, l-diversity, or differential privacy applied
  to the dataset as a whole, which reason about a released dataset's
  re-identification risk rather than about a single free-text span, and is
  covered as a related, contrasting pattern in dimension 12, not this one.
- The value is sensitive to the business but does not identify a natural
  person, an internal project codename, an unreleased price, a trade
  secret. That is confidentiality, not PII, and belongs under
  Input Guardrails or Output Guardrails using a different rule set than the
  identifier-focused recognizers this pattern is built around.
- The system has no way to define what counts as PII for its domain and no
  stakeholder has reviewed which categories matter. A redaction pass built
  on guessed categories gives a false sense of coverage that is worse than
  an honest absence of the control, because it invites the assumption that
  the compliance question is already answered.

## 5. Structure

- **Source.** The place a payload originates, a user message, a retrieved
  document chunk, a tool call's arguments, a tool call's result, or a
  model's generated response. Every source can carry PII and is treated
  the same way by the pattern regardless of which side of the model call
  it sits on.
- **Recognizer registry.** A set of independent detectors, each responsible
  for one entity type. Recognizers are commonly built from three
  techniques layered together, regular expressions for values with a
  predictable shape, such as email addresses and phone numbers, checksum
  or format validators that reduce false positives on shape-matched
  candidates, such as the Luhn algorithm confirming a 16-digit span is
  actually a valid card number rather than an arbitrary number sequence
  (Amazon Web Services, Amazon Comprehend Developer Guide, cited above,
  which documents the same check-digit validation for Canadian Social
  Insurance Numbers), and named entity recognition models for
  context-dependent categories such as person names and addresses that
  have no fixed shape.
- **Scorer.** Assigns a confidence value to each candidate span, and a
  per-entity-type minimum threshold decides whether the candidate is acted
  on. This is the mechanism that lets the pattern trade recall against
  precision per entity type, a card number match can require a high
  checksum-confirmed score because false positives on digit strings are
  common, while an email match can use a lower threshold because the shape
  is close to unambiguous.
- **Span merger.** Resolves overlapping detections from different
  recognizers, typically by keeping the highest-scoring span and discarding
  or truncating spans that overlap it, so a single value is never
  double-redacted or left partially redacted at a boundary.
- **Transformer, also called Anonymizer.** Applies an operator to each
  confirmed span. Presidio names four common operators, replace with a
  static placeholder, mask with a repeated character, redact by removing
  the value, hash into a deterministic surrogate, and encrypt into a
  reversible ciphertext (Presidio documentation, cited above). Google's
  Sensitive Data Protection adds date shifting and bucketing as additional
  operators for structured and semi-structured fields (Google Cloud,
  cited above).
- **Vault, also called token store.** Present only when the transform is
  reversible. Maps each generated token or pseudonym back to the original
  value, scoped to the smallest lifetime and audience that the use case
  allows. The vault is itself a new store of the sensitive data and is
  covered in dimension 17 as an attack surface the pattern introduces.
- **Sink.** The destination the transformed payload is now safe to reach,
  a model provider's context window, a log line, a cache entry, or a
  screen. The pattern's entire purpose is that the sink never receives the
  untransformed span.

## 6. ASCII structure diagram

```
+------------------+     +----------------------+     +------------------+
|      Source      |---->|  Recognizer Registry  |---->|      Scorer      |
| (message, tool    |     | regex | NER | check-  |     | per-entity-type  |
|  result, chunk,   |     | sum | rule based       |     | min-score gate   |
|  model output)    |     +----------------------+     +--------+---------+
+------------------+                                            |
                                                                 v
+------------------+     +----------------------+     +------------------+
|       Sink        |<----|      Transformer     |<----|   Span Merger    |
| model context |    |     | replace | mask | hash |    | resolve overlaps |
| log | cache | UI  |     | redact | encrypt        |    +------------------+
+--------+---------+     +----------+-----------+
         |                          |
         | (if reversible)          v
         |                +------------------+
         +--------------->|   Vault / Token   |
        restore on read   |      Store        |
                          +------------------+
```

## 7. Dynamics

```
turn begins
  |
  v
[SOURCE] raw payload produced (user msg / tool result / retrieved chunk)
  |
  v
for each Recognizer in registry:
    candidates = Recognizer.find(payload)
    for each candidate:
        score = Recognizer.confidence(candidate)
        if score >= entity_type.min_score:
            emit Span(start, end, entity_type, score)
  |
  v
[MERGE] sort spans by start offset
         resolve overlaps, keep highest score
  |
  v
[TRANSFORM] for each merged Span:
                operator = policy[entity_type]
                token_or_mask = operator.apply(span.text)
                if operator.reversible:
                    vault[token_or_mask] = span.text   # never logged
                splice token_or_mask into payload at span offsets
  |
  v
[LOG, metadata only] entity_type counts, span count, latency
                       -- never the matched text --
  |
  v
[SINK] transformed payload forwarded
  |
  v
   .-- if sink is model context --.
  |  model reasons over tokens,    |
  |  may echo a token back         |
   `--------------------------------'
  |
  v
[RESPONSE PATH, optional] if a reversible token appears in the
  model's own output AND the current caller is the original,
  authorized data owner:
      restore(response, vault)
  else:
      leave tokens in place, do not restore for a different audience
  |
  v
turn ends; vault entries expire on their own TTL, independent of the turn
```

## 8. Implementation variants

- **Regex plus checksum only.** The cheapest variant, appropriate for
  entity types with a fixed, checkable shape, emails, phone numbers, credit
  card numbers validated with Luhn, IBAN numbers validated with the
  ISO 7064 mod-97 check. No model inference required, single-digit
  millisecond latency, but blind to any entity type without a fixed shape,
  most importantly person names and street addresses.
- **NER-augmented, hybrid pipeline.** Presidio's own architecture is the
  reference implementation of this variant, combining the same three
  recognizer types named in dimension 1, regex, checksum, and named entity
  recognition, running together, with each recognizer voting on the same
  span and the highest-confidence result winning (Presidio documentation,
  cited above). This is the variant that covers names and addresses, at
  the cost of loading and running a language model per request.
- **Managed API, request-response.** Amazon Comprehend and Google Sensitive
  Data Protection both expose PII detection and transformation as a hosted
  API call, trading operational ownership of the recognizer models for
  network latency and a per-call cost, and for the ability to detect
  country-specific identifier types, an Indian Aadhaar number or a UK
  National Insurance Number, that a general-purpose open-source recognizer
  set may not cover out of the box (Amazon Web Services, cited above, lists
  country-specific entity types as a distinct category from universal
  types).
- **LLM-as-detector.** A separate model call classifies or extracts spans
  instead of, or in addition to, the recognizer registry, useful for
  entity types too context-dependent for regex or a fixed NER label set,
  for example distinguishing a person's home address from a business
  address the person happens to be discussing. This is the most expensive
  variant in both latency and cost, and it introduces a second model
  provider relationship, or a second call to the same provider, that is
  itself a place PII could leak if the detector call is not scoped
  separately from the pipeline it is protecting.
- **Streaming, incremental redaction.** For token-by-token streamed model
  output, the transformer cannot wait for the full response before
  scanning it, because the point of streaming is to show output as it
  arrives. Implementations buffer a small trailing window of recent
  tokens, long enough to complete the longest expected entity pattern,
  and only release text to the sink once the window confirms no partial
  match is pending at the boundary.
- **Format-preserving, partial masking.** Rather than a fixed placeholder,
  the transform keeps some characters, typically the last four digits of
  an account or card number, matching how card networks display numbers to
  cardholders under PCI DSS convention. This variant trades some
  disclosure for fidelity the downstream consumer needs, and should be a
  deliberate policy choice per entity type rather than a default, because
  it discloses more than full redaction by design.
- **Reversible pseudonymization with a scoped vault.** Each detected span
  is replaced with a stable, opaque token, and the mapping from token to
  original value is stored separately with its own access control and
  time-to-live, letting an authorized downstream process, or the same
  session later, restore the original value without the untransformed
  value ever having reached the sink it was protected from.

## 9. Known production uses

- **Amazon Comprehend PII detection and redaction.** A named, general
  availability feature of AWS's natural language processing service,
  detecting a fixed catalog of universal entity types, `NAME`, `ADDRESS`,
  `SSN`, `CREDIT_DEBIT_NUMBER`, `EMAIL`, `PHONE`, `BANK_ACCOUNT_NUMBER`, and
  country-specific types, `IN_AADHAAR`, `UK_NATIONAL_INSURANCE_NUMBER`,
  `PASSPORT_NUMBER`, and returning either the entity list with confidence
  scores and offsets or a fully redacted copy of the input document with
  each entity replaced by asterisks (Amazon Web Services, "Detecting PII
  entities", https://docs.aws.amazon.com/comprehend/latest/dg/how-pii.html,
  verified 2026-08-03).
- **Google Sensitive Data Protection, de-identification transformations.**
  A named, general availability API within Google Cloud that applies
  masking, redaction, cryptographic hashing for pseudonymization, date
  shifting, and bucketing to detected sensitive values inside text and
  structured data, described in Google's own documentation as covering
  "Masking sensitive data by partially or fully replacing characters with a
  symbol" and "Redacts a given value by removing it completely" among its
  named transformation methods (Google Cloud, "De-identify sensitive
  data",
  https://docs.cloud.google.com/sensitive-data-protection/docs/deidentify-sensitive-data,
  verified 2026-08-03).
- **Microsoft Presidio.** An open-source project originally published under
  `microsoft/presidio` on GitHub and now maintained under the Data Privacy
  Stack organization, shipping an Analyzer, Anonymizer, Image Redactor, and
  Structured module, described by the project as providing "fast
  identification and anonymization modules for private entities in text
  and images", distributed for use "from Python or PySpark workloads
  through Docker to Kubernetes" (Presidio documentation,
  https://presidio.dataprivacystack.org/, verified 2026-08-03). Presidio is
  the reference implementation most frequently cited by other open-source
  agent frameworks that add a PII-redaction guardrail stage, because it is
  the one general-purpose, self-hostable recognizer and anonymizer engine
  with a documented plugin architecture for custom recognizers.

## 10. Consequences

Positive:

- Removes or reduces identifiable data at exactly the points where it
  would otherwise cross into a system, a model provider, a log store, a
  cache, that was not designed with that data's sensitivity in mind, which
  is the most direct way to shrink the blast radius of any later breach of
  that downstream system.
- Gives a pipeline a specific, auditable answer to whether personal data
  reached the model provider, and whether it reached the log store,
  because the detection event itself, entity type, span count, timestamp,
  can be recorded without recording the sensitive value.
- Decouples the sensitivity policy from any single call site. A change to
  which entity types are considered sensitive, or which operator applies
  to each type, is a change to the recognizer registry and transform
  policy, not a change scattered across every place text is forwarded.
- Composes with input and output guardrails as a graduated response,
  rather than blocking a request outright because it contains PII, the
  pipeline can sanitize and continue, which is usually the better user
  experience for the very common case where PII appears incidentally in an
  otherwise legitimate request.

Negative:

- Adds a class of silent failure that is worse than a visible one. A
  recognizer with a gap, a new PII shape it was never built to catch, does
  not raise an error, it simply lets the value through, and nothing in the
  pipeline's normal operation reveals the miss until an audit or an
  incident does.
- Degrades the fidelity of the text a model reasons over. A heavily
  redacted prompt can leave a model unable to answer a question that
  depended on the exact value that was removed, and the failure shows up
  as a wrong or evasive answer with no obvious link back to the redaction
  pass that caused it.
- Introduces new state, the recognizer registry's model weights or regex
  set, and the vault when reversible transforms are used, that has to be
  versioned, tested, and kept current as new PII formats and new locales
  appear, which is ongoing engineering work rather than a one-time setup.
- Cannot, by itself, close every leak path. A model trained on data that
  included similar PII can still produce a plausible-looking but entirely
  fabricated value that happens to match a real person's actual data by
  coincidence or by memorization, a risk PII Redaction on the current
  request's payload does nothing to address.

## 11. Failure modes and misuse

- **Symptom.** A downstream reviewer or a customer support workflow
  receives a response full of opaque tokens, `[NAME_a1b2]`,
  `[ADDRESS_c3d4]`, and the response reads as unusable rather than useful.
  **Cause.** Full redaction was applied uniformly to every entity type
  regardless of whether the consuming context actually needed the value
  hidden from that specific audience.
  **Fix.** Move to a masking or partial-disclosure operator for entity
  types the audience is authorized to see in part, and reserve full
  redaction for the entity types and audiences where the policy genuinely
  requires it.

- **Symptom.** A card number typed with unusual spacing, or a phone number
  in an international format the regex set was not written for, appears
  unredacted in a log line, discovered months later during an audit.
  **Cause.** The recognizer registry's shape-based patterns covered only
  the formats present in the test fixtures used when the recognizers were
  written, and no canary or regression corpus tracked new formats over
  time.
  **Fix.** Maintain a growing, versioned corpus of real and synthetic PII
  in every format the business has ever seen, run it against the
  recognizer registry on every change, and treat any drop in recall on
  that corpus as a release blocker.

- **Symptom.** A request containing a very long, adversarially crafted
  digit sequence causes the redaction pass to hang or the process to spike
  CPU to one core for seconds at a time.
  **Cause.** A regex used for a checksum-eligible entity type, most
  commonly a broad digit-sequence pattern intended to catch card numbers,
  has catastrophic backtracking on certain inputs, a well-known regular
  expression denial-of-service risk when quantifiers are nested or
  overlapping.
  **Fix.** Replace ambiguous nested quantifiers with possessive or atomic
  matching where the regex engine supports it, bound the maximum input
  length the recognizer scans per call, and add a wall-clock timeout
  around the recognizer pass with a fail-closed default.

- **Symptom.** The same customer's account number gets a different token
  on every turn of a conversation, and a model that previously reasoned
  correctly about the account discussed earlier now treats each mention as
  an unrelated, opaque value.
  **Cause.** The token generation scheme derives a token from a
  request-scoped source, a random nonce or the current timestamp, instead
  of a deterministic function of the underlying value, such as a keyed
  hash, so the same input value never maps to the same output token across
  calls.
  **Fix.** Derive tokens deterministically from the original value within
  a session or a defined scope, for example an HMAC of the value with a
  session-scoped key, so repeated mentions of the same value produce the
  same token and coreference across turns still works.

- **Symptom.** A security review finds that the token vault, meant to be
  the safest place in the system because it is the only place mapping
  tokens back to real values, has broader read access than the systems it
  was built to protect, or no expiry at all.
  **Cause.** The vault was implemented as an afterthought, a key-value
  store added to make restoration work, without applying the same access
  control, encryption at rest, and retention policy review that the
  original sensitive data source required.
  **Fix.** Treat the vault as a first-class sensitive data store subject to
  the same controls as the source system, with a retention policy no
  longer than the shortest window any consumer legitimately needs to
  restore a value, and default to a short, explicit TTL rather than
  indefinite retention.

- **Symptom.** PII appears in a request log or a cache entry even though
  the code path that forwards requests to the model provider is correctly
  redacting first.
  **Cause.** Logging or caching happens at a layer, an HTTP client
  middleware, a request tracing library, that captures the payload before
  the redaction pass runs, or in parallel with it rather than strictly
  after it, so the ordering guarantee the pipeline assumed does not
  actually hold at runtime.
  **Fix.** Redact as close to the point of data ingestion as the
  architecture allows, and add an explicit integration test that asserts
  the log and cache layers never observe the raw payload, not only that
  the model-facing payload is redacted.

- **Symptom.** A field embedded inside a tool call's JSON arguments, or a
  base64-encoded attachment referenced inside a message, still contains
  PII in a downstream trace, even though free-text fields in the same
  request are clean.
  **Cause.** The recognizer registry was wired to scan only the top-level
  message text, and structured fields, nested JSON, encoded blobs, tool
  arguments, were never passed through the same detection pass.
  **Fix.** Walk the full payload structure, not only its top-level text
  field, decoding common encodings before scanning, and apply the same
  recognizer registry to every string leaf in the structure, including
  tool call arguments and tool call results.

## 12. Trade-off matrix

| Concern | PII Redaction, this pattern | Access Control, RBAC | k-anonymity, dataset release | Differential Privacy | Full Encryption at Rest |
|---|---|---|---|---|---|
| Unit of protection | A span inside free text or a payload | Who may read a whole record | A row inside a released table | An aggregate statistic or gradient | An entire stored record |
| Works on unstructured text | Yes, its primary use case | No, orthogonal | No, requires tabular structure | No, requires an aggregation function | Yes, but protects storage, not the model's view |
| Protects data reaching a model provider | Yes, directly | No, the provider still sees the full record if authorized | Not applicable, dataset-release scenario | Not applicable at inference time | No, decryption happens before the model sees it |
| Reversible | Optional, per policy | Not applicable | No, generalization loses information | No, by design | Yes, that is the point |
| Added latency per request | Low to moderate, milliseconds to low hundreds of milliseconds | Near zero, a lookup | Not applicable at request time | Not applicable at request time | Low, hardware-accelerated in most stores |
| Guarantees no re-identification | No, best effort, dependent on recognizer coverage | No, protects access, not content | Yes, mathematically, for the released table as a whole | Yes, mathematically, with a formal privacy budget | No, does not address who is authorized to decrypt |
| Regulatory alignment | Directly supports HIPAA Safe Harbor and GDPR data minimization for in-flight text | Supports GDPR access-control obligations, not de-identification | Directly supports HIPAA Safe Harbor for tabular releases | Supports statistical disclosure limits for published aggregates | Supports GDPR and breach-notification safe harbors for data at rest |

## 13. Related and incompatible patterns

- **Input Guardrails.** PII Redaction is frequently implemented as one
  transformation an input guardrail applies, rather than as a
  freestanding stage. the guardrail's decision is not only allow or block,
  it can be sanitize-and-continue, with PII Redaction supplying the
  sanitize step. The two are complementary. a guardrail without a
  redaction transform can only refuse a request that contains PII, which
  is often the wrong response to an otherwise legitimate message.
- **Output Guardrails.** The same relationship holds on the way out. an
  output guardrail decides whether a model's response is safe to show, and
  PII Redaction is the transform that lets a response continue to the user
  after a leaked training-data fragment or a regurgitated identifier is
  removed, rather than the whole response being discarded.
- **Function Calling and Structured Output.** Tool arguments and tool
  results are exactly the kind of structured payload described in
  dimension 11's fix for nested-field blind spots. Any pipeline using
  function calling needs the recognizer registry to walk into argument and
  result objects, not only top-level chat text.
- **Tool Result Caching.** A cache is a durable store with a different
  access surface and often a longer retention window than the request
  that produced the cached value. Redacting before writing to cache, not
  after, is the only ordering that avoids caching the sensitive value in
  the first place.
- **Agent Memory.** Long-term memory persists across sessions and is
  frequently retrieved into future prompts without the original
  conversation's context, which makes memory a higher-value target for
  redaction than a single request, because a miss here compounds across
  every future session that retrieves the stored fact.
- **Model Context Protocol.** Every MCP resource read and tool call is a
  crossing point in the sense this pattern cares about, a server exposing
  a resource that may contain PII, or a client receiving a tool result
  that may contain PII, both benefit from the same recognizer-and-transform
  pass applied at the protocol boundary.
- **Retrieval-Augmented Generation and Chunking Strategies.** Documents
  ingested into a retrieval corpus were frequently written for a narrower
  audience than the corpus will eventually serve. Redacting at ingestion
  time, before chunking and embedding, is cheaper than redacting every
  retrieved chunk at query time, but requires the ingestion pipeline to
  know the final consumer's trust level in advance, which is not always
  true for a corpus serving multiple downstream agents with different
  authorization levels.
- **K-anonymity and Differential Privacy, as a contrast rather than a
  composition.** These operate on a released dataset or an aggregate
  statistic as a whole, deciding whether the dataset or statistic itself
  carries re-identification risk, while PII Redaction operates on a single
  in-flight payload. The two are not incompatible, a dataset could be
  k-anonymized before ingestion and its individual retrieved chunks could
  still be redacted at query time as a second layer, but they answer
  different questions and neither substitutes for the other.

## 14. Refactoring path in and out

**Introducing the pattern into a pipeline that lacks it.** Start at the
lowest-risk, highest-value crossing point rather than trying to cover every
boundary in one change. The usual order, cheapest first, highest value
first.

1. Add redaction to the logging and tracing layer first. this protects
   against the most common accidental leak, a debug log capturing a full
   request body, and can be done without touching the model-facing request
   path at all, which limits the blast radius of a mistake in the first
   iteration.
2. Add a canary corpus of known PII shapes and wire it into a test that
   runs the current logging redaction against it, establishing a
   measurable recall baseline before extending coverage further.
3. Extend the same recognizer registry to the output path, redacting or
   masking a model's response before it reaches the user, which protects
   against a model regurgitating a value it should not have memorized or
   should not disclose to this particular audience.
4. Extend to the input path last, once the recognizer registry's false
   positive rate on real traffic is understood well enough that redacting
   before the model sees the text does not silently degrade answer
   quality for a large fraction of requests.
5. Extend to durable stores, memory and cache, once the token vault's
   access control, encryption, and retention policy have been reviewed
   with the same rigor as the source systems that originally held the
   data, per dimension 11's vault failure mode.

**Removing the pattern.** Removing PII Redaction is a higher-risk change
than removing most other patterns in this catalog, because its absence is
silent, nothing breaks visibly when it is gone, the risk only shows up
later as a compliance finding or an incident. Remove it only when a
stronger, already-reviewed upstream control supersedes it for every
crossing point the pattern was protecting, for example the pipeline moved
entirely to a self-hosted model with no third-party data processor in the
loop and no durable store outside the source system's own access controls,
and that supersession has been reviewed against the same regulatory
requirements, HIPAA Safe Harbor, GDPR Article 4, that motivated adding the
pattern in the first place.

## 15. Testing and verification

- **Labeled corpus recall and precision.** Maintain a versioned corpus of
  text samples with every PII span hand-labeled by entity type, mixing real
  formats seen in production, anonymized, with synthetic edge cases. Run
  the full recognizer registry against the corpus on every change and
  track recall and precision per entity type as a release gate. this is
  the same evaluation shape any classifier needs, applied specifically to
  the entity types the business has committed to protecting.
- **Round-trip property tests for reversible transforms.** For every
  entity type using a reversible operator, a property test should assert
  that a redacted-then-restored text equals the original text for a wide
  range of generated inputs, catching bugs in token generation, span
  offset arithmetic, or vault key collisions before they reach production.
- **Boundary tests around score thresholds.** Because the scorer applies a
  per-entity-type minimum confidence, tests should include candidates
  scored slightly above and slightly below each threshold to confirm the cutoff
  behaves as configured, rather than relying only on clearly-high-confidence
  or clearly-low-confidence fixtures that never exercise the boundary.
- **Ordering integration tests.** A test that exercises the full pipeline,
  not the redaction function in isolation, and asserts that the raw
  payload never reaches the log sink, the cache sink, or the model
  provider client, directly addresses the ordering failure mode described
  in dimension 11, where redaction runs but a parallel or earlier capture
  point sees the unredacted value anyway.
- **Locale and encoding coverage.** Tests should include non-English names
  and addresses, right-to-left scripts, and common encodings, URL-encoded
  and base64-encoded substrings, since a recognizer registry built and
  tested only against English, Latin-script, plaintext samples will have
  systematic blind spots outside that set.
- **Adversarial and red-team prompts.** Include prompts that attempt to
  coax a model into repeating a value it was shown in redacted form, or
  into inferring the original value from context clues surrounding the
  token, verifying that the token itself, and its surrounding context,
  does not leak enough information to reconstruct the redacted value.

## 16. Observability signals

- **Detections per entity type, per request.** A count, never the matched
  text, logged alongside the request identifier, giving a dashboard of
  which entity types actually appear in traffic and at what rate, which is
  the input needed to prioritize recognizer coverage work.
- **Zero-detection rate over a rolling window.** A recognizer that
  previously matched a steady rate of a given entity type and drops to
  zero matches is a strong regression signal, most often caused by an
  upstream format change or a broken recognizer, and should page a human
  faster than waiting for an audit to discover the miss.
- **Latency added by the redaction pass, separate from total request
  latency.** Tracked per recognizer variant, since regex-only, NER, and
  LLM-as-detector variants have order-of-magnitude different costs, and a
  latency regression in one recognizer should be attributable without
  digging through the whole request trace.
- **Vault size, key age distribution, and eviction rate.** For reversible
  transforms, a vault that grows without bound, or whose oldest keys are
  far older than any legitimate use case needs, is evidence the retention
  policy from dimension 11's vault fix is not actually being enforced in
  practice.
- **False positive reports from consumers.** A structured channel for a
  downstream system or a human reviewer to flag a redaction that clearly
  should not have fired, feeding directly back into the labeled corpus used
  in dimension 15's recall and precision testing, closing the loop between
  production behavior and the test suite.
- **Fail-open versus fail-closed counter.** A count of how many times the
  redaction pass itself errored, and whether the pipeline's configured
  behavior on that error was to pass the payload through unredacted or to
  block the request. This number should be close to zero in steady state,
  and any nonzero fail-open count deserves the same attention as a security
  incident, per dimension 17.

## 17. Security and privacy implications

The single largest privacy implication of this pattern is one most teams
building it do not anticipate. a reversible transform's token vault is a new
concentrated store of exactly the sensitive data the pattern was built to
protect, and it needs the same encryption at rest, access control, and
retention discipline as the original source system, not less, because a
breach of the vault re-links every token in it back to real personal data
in one step. Dimension 11's vault-specific failure mode and dimension 16's
vault observability signals both exist because this is the most common
place the pattern's own implementation becomes the risk.

Second, a failure inside the redaction pass itself must default to fail
closed for any entity type the policy treats as high sensitivity. a pass
that catches an internal error and silently forwards the unredacted payload
rather than blocking the request converts every bug in the recognizer code
into a data leak, and because the failure is silent, per dimension 10's
negative consequences, it is unlikely to be noticed until an audit finds it.

Third, the redacted placeholder itself carries information. a message that
contains the token `[SSN]` discloses, to anyone who can see that token, that
the original message contained a social security number, even without
disclosing the value. For most use cases this is an acceptable, minor
disclosure, but for a use case where the presence of a given entity type is
itself sensitive, a health condition category inferred from a
`MEDICAL_RECORD_NUMBER` token appearing at all, the placeholder choice
should be reviewed as a data minimization decision in its own right, not
assumed to be neutral.

Fourth, partial masking and format-preserving transforms are a deliberate,
graduated disclosure, not a lesser form of full redaction. showing the last
four digits of a card number, the way payment networks display it to
cardholders, discloses less than the full number but more than nothing, and
the choice of how many characters to preserve per entity type is a policy
decision that should be documented and reviewed the same way a full-redaction
policy is, rather than treated as an implementation detail.

Fifth, never place vault contents, or any structure that could let a model
reconstruct a token-to-value mapping, inside the model's own context. A
model that is shown both a redacted token and, anywhere in the same or a
later context, the mapping needed to reverse it, has effectively been shown
the original value, defeating the entire purpose of running the
transformation before the crossing into the model's context in the first
place.

## 18. References

- Latanya Sweeney's k-anonymity model for structured-data de-identification,
  summarized in Wikipedia, "De-identification",
  https://en.wikipedia.org/wiki/De-identification, verified 2026-08-03.
- US Department of Health and Human Services, HIPAA Privacy Rule, Safe
  Harbor method of de-identification, codified at 45 CFR 164.514(b)(2),
  text via Cornell Law School, Legal Information Institute,
  https://www.law.cornell.edu/cfr/text/45/164.514, verified 2026-08-03.
- European Union, General Data Protection Regulation, Article 4(1),
  definition of personal data, and Article 4(5), definition of
  pseudonymisation, https://gdpr-info.eu/art-4-gdpr/, verified 2026-08-03.
- OWASP GenAI Security Project, entry LLM02, 2025 edition, Sensitive
  Information Disclosure, OWASP Top 10 for Large Language Model
  Applications,
  https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/,
  verified 2026-08-03.
- Amazon Web Services, "Detecting PII entities", Amazon Comprehend
  Developer Guide,
  https://docs.aws.amazon.com/comprehend/latest/dg/how-pii.html, verified
  2026-08-03.
- Google Cloud, "De-identify sensitive data", Sensitive Data Protection
  documentation,
  https://docs.cloud.google.com/sensitive-data-protection/docs/deidentify-sensitive-data,
  verified 2026-08-03.
- Microsoft Presidio project documentation, Analyzer, Anonymizer, Image
  Redactor, and Structured modules, https://presidio.dataprivacystack.org/,
  verified 2026-08-03. Originally published under `microsoft/presidio` on
  GitHub, https://github.com/microsoft/presidio, verified 2026-08-03.

## Code examples

Three languages, each implementing the same pattern shape, a recognizer
registry combining regex shape matching with Luhn checksum validation for
credit card candidates, a scorer applying per-entity-type minimum
confidence, a span merger resolving overlaps, and a reversible transform
into a token vault that supports exact round-trip restoration. All three
were run directly and produce identical output on the same input, verified
2026-08-03.

### TypeScript

```typescript
type Recognizer = {
  entityType: string;
  pattern: RegExp;
  score: (match: string) => number;
  minScore: number;
};

function luhnValid(number: string): boolean {
  const digits = number.replace(/\D/g, "").split("").map(Number);
  if (digits.length < 12) return false;
  let checksum = 0;
  const parity = digits.length % 2;
  digits.forEach((d, i) => {
    if (i % 2 === parity) {
      d *= 2;
      if (d > 9) d -= 9;
    }
    checksum += d;
  });
  return checksum % 10 === 0;
}

const recognizers: Recognizer[] = [
  {
    entityType: "EMAIL",
    pattern: /\b[\w.+-]+@[\w-]+\.[\w.-]+\b/g,
    score: () => 0.95,
    minScore: 0.5,
  },
  {
    entityType: "CREDIT_CARD",
    pattern: /\b(?:\d[ -]*?){13,16}\b/g,
    score: (m) => (luhnValid(m) ? 0.95 : 0.3),
    minScore: 0.85,
  },
  {
    entityType: "PHONE",
    pattern: /\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g,
    score: () => 0.6,
    minScore: 0.5,
  },
];

interface Span {
  start: number;
  end: number;
  entityType: string;
  text: string;
  score: number;
}

function detect(text: string): Span[] {
  const spans: Span[] = [];
  for (const r of recognizers) {
    r.pattern.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = r.pattern.exec(text)) !== null) {
      const score = r.score(m[0]);
      if (score >= r.minScore) {
        spans.push({
          start: m.index,
          end: m.index + m[0].length,
          entityType: r.entityType,
          text: m[0],
          score,
        });
      }
    }
  }
  spans.sort((a, b) => a.start - b.start);
  const merged: Span[] = [];
  for (const s of spans) {
    const last = merged[merged.length - 1];
    if (last && s.start < last.end) {
      if (s.score > last.score) merged[merged.length - 1] = s;
      continue;
    }
    merged.push(s);
  }
  return merged;
}

function redact(text: string, spans: Span[], vault: Map<string, string>): string {
  let out = "";
  let cursor = 0;
  for (const s of spans) {
    out += text.slice(cursor, s.start);
    const token = `[${s.entityType}_${s.start}_${s.end}]`;
    vault.set(token, s.text);
    out += token;
    cursor = s.end;
  }
  out += text.slice(cursor);
  return out;
}

function restore(redacted: string, vault: Map<string, string>): string {
  let result = redacted;
  for (const [token, original] of vault) {
    result = result.split(token).join(original);
  }
  return result;
}

const sample =
  "Hi, this is Jordan. My email is jordan.k@example.com and my card " +
  "is 4111 1111 1111 1111. Call me at 415-555-0199.";
const spans = detect(sample);
const vault = new Map<string, string>();
const redacted = redact(sample, spans, vault);
console.log("REDACTED :", redacted);
if (restore(redacted, vault) !== sample) throw new Error("round trip failed");
```

Run with `npx tsx redact.ts`, output confirmed.

```
REDACTED : Hi, this is Jordan. My email is [EMAIL_32_52] and my card is [CREDIT_CARD_68_87]. Call me at [PHONE_100_112].
```

### Python

```python
import re
import hashlib
from dataclasses import dataclass
from typing import Callable

@dataclass
class Span:
    start: int
    end: int
    entity_type: str
    text: str
    score: float

def luhn_valid(number: str) -> bool:
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) < 12:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0

RECOGNIZERS: list[tuple[str, re.Pattern, Callable[[str], float]]] = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), lambda m: 0.95),
    ("PHONE", re.compile(r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), lambda m: 0.6),
    (
        "CREDIT_CARD",
        re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
        lambda m: 0.95 if luhn_valid(m) else 0.3,
    ),
]

MIN_SCORE = {"EMAIL": 0.5, "PHONE": 0.5, "CREDIT_CARD": 0.85}

def detect(text: str) -> list[Span]:
    spans: list[Span] = []
    for entity_type, pattern, score_fn in RECOGNIZERS:
        for m in pattern.finditer(text):
            score = score_fn(m.group(0))
            if score >= MIN_SCORE[entity_type]:
                spans.append(Span(m.start(), m.end(), entity_type, m.group(0), score))
    spans.sort(key=lambda s: s.start)
    merged: list[Span] = []
    for s in spans:
        if merged and s.start < merged[-1].end:
            if s.score > merged[-1].score:
                merged[-1] = s
            continue
        merged.append(s)
    return merged

def redact(text: str, spans: list[Span], vault: dict[str, str]) -> str:
    out, cursor = [], 0
    for s in spans:
        out.append(text[cursor:s.start])
        token = f"[{s.entity_type}_{hashlib.sha256(s.text.encode()).hexdigest()[:8]}]"
        vault[token] = s.text
        out.append(token)
        cursor = s.end
    out.append(text[cursor:])
    return "".join(out)

def restore(redacted: str, vault: dict[str, str]) -> str:
    for token, original in vault.items():
        redacted = redacted.replace(token, original)
    return redacted

sample = (
    "Hi, this is Jordan. My email is jordan.k@example.com and my card "
    "is 4111 1111 1111 1111. Call me at 415-555-0199."
)
vault: dict[str, str] = {}
redacted = redact(sample, detect(sample), vault)
print("REDACTED :", redacted)
assert restore(redacted, vault) == sample
```

Run with `python3 redact.py`, output confirmed.

```
REDACTED : Hi, this is Jordan. My email is [EMAIL_6eb8e3bc] and my card is [CREDIT_CARD_6a7e0e79]. Call me at [PHONE_5ed9f390].
```

### Go

```go
package main

import (
	"fmt"
	"regexp"
	"sort"
	"strings"
)

type Recognizer struct {
	EntityType string
	Pattern    *regexp.Regexp
	Score      func(string) float64
	MinScore   float64
}

func luhnValid(number string) bool {
	digits := []int{}
	for _, r := range number {
		if r >= '0' && r <= '9' {
			digits = append(digits, int(r-'0'))
		}
	}
	if len(digits) < 12 {
		return false
	}
	checksum, parity := 0, len(digits)%2
	for i, d := range digits {
		if i%2 == parity {
			d *= 2
			if d > 9 {
				d -= 9
			}
		}
		checksum += d
	}
	return checksum%10 == 0
}

var recognizers = []Recognizer{
	{"EMAIL", regexp.MustCompile(`[\w.+-]+@[\w-]+\.[\w.-]+`), func(string) float64 { return 0.95 }, 0.5},
	{"CREDIT_CARD", regexp.MustCompile(`(?:\d[ -]*?){13,16}`), func(m string) float64 {
		if luhnValid(m) {
			return 0.95
		}
		return 0.3
	}, 0.85},
	{"PHONE", regexp.MustCompile(`\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}`), func(string) float64 { return 0.6 }, 0.5},
}

type Span struct {
	Start, End int
	EntityType string
	Text       string
	Score      float64
}

func detect(text string) []Span {
	var spans []Span
	for _, r := range recognizers {
		for _, loc := range r.Pattern.FindAllStringIndex(text, -1) {
			match := text[loc[0]:loc[1]]
			score := r.Score(match)
			if score >= r.MinScore {
				spans = append(spans, Span{loc[0], loc[1], r.EntityType, match, score})
			}
		}
	}
	sort.Slice(spans, func(i, j int) bool { return spans[i].Start < spans[j].Start })
	var merged []Span
	for _, s := range spans {
		if len(merged) > 0 && s.Start < merged[len(merged)-1].End {
			if s.Score > merged[len(merged)-1].Score {
				merged[len(merged)-1] = s
			}
			continue
		}
		merged = append(merged, s)
	}
	return merged
}

func redact(text string, spans []Span, vault map[string]string) string {
	var b strings.Builder
	cursor := 0
	for _, s := range spans {
		b.WriteString(text[cursor:s.Start])
		token := fmt.Sprintf("[%s_%d_%d]", s.EntityType, s.Start, s.End)
		vault[token] = s.Text
		b.WriteString(token)
		cursor = s.End
	}
	b.WriteString(text[cursor:])
	return b.String()
}

func restore(redacted string, vault map[string]string) string {
	for token, original := range vault {
		redacted = strings.ReplaceAll(redacted, token, original)
	}
	return redacted
}

func main() {
	sample := "Hi, this is Jordan. My email is jordan.k@example.com and my card " +
		"is 4111 1111 1111 1111. Call me at 415-555-0199."
	vault := map[string]string{}
	redacted := redact(sample, detect(sample), vault)
	fmt.Println("REDACTED :", redacted)
	if restore(redacted, vault) != sample {
		panic("round trip failed")
	}
}
```

Run with `go run main.go`, output confirmed.

```
REDACTED : Hi, this is Jordan. My email is [EMAIL_32_52] and my card is [CREDIT_CARD_68_87]. Call me at [PHONE_100_112].
```

Java, Rust, and Swift are omitted from this entry. the pattern is a data
transformation shape, not a language-idiom shape, so a fourth or fifth
language would repeat the same regex, checksum, and map-based vault
structure shown above without demonstrating a materially different
implementation technique.
