---
name: Structured Output
slug: structured-output
family: 17-ai-agentic
category: Agentic
aliases: [Guided Generation, Constrained Decoding, JSON Mode, Schema-Constrained Generation, Grammar-Constrained Sampling]
first_described: "Willard, Louf 2023 (constrained decoding formalized as a finite-state process); productized as OpenAI Structured Outputs, 6 August 2024"
maturity: canonical
related: [function-calling, react-prompting, plan-execute, orchestrator-worker]
incompatible_with: []
verified: 2026-08-03
---

# Structured Output

## 1. Name, aliases, and lineage

A reader moving between an OpenAI integration, an Anthropic integration, and an
open source inference server will meet four or five names for what is
recognizably the same idea, and the differences between the names are not
cosmetic. They mark real differences in how strong a guarantee is being made.

**JSON mode** is the weakest and oldest member of the family. It is a request
flag that tells a model to emit syntactically valid JSON, an opening brace, a
closing brace, quoted keys, no trailing commas, and nothing else. It says
nothing about which keys appear, what type a value has, or whether a required
field is present at all. OpenAI's own current documentation describes it this
way and recommends against relying on it, stating plainly that developers
should "always use Structured Outputs instead of JSON mode when possible"
(OpenAI, "Structured Outputs", https://developers.openai.com/api/docs/guides/structured-outputs
verified 2026-08-03).

**Structured Outputs**, capitalized, is OpenAI's specific product name for the
strict, schema-conformant successor to JSON mode. It shipped on 6 August 2024
alongside the `gpt-4o-2024-08-06` model, adding two request-level controls, a
`strict` flag set `true` on function definitions and a `type` field set to
`json_schema` in the response format, which carries the caller's schema
directly (Simon Willison, "OpenAI's structured outputs for function calling",
6 August 2024, https://simonwillison.net/2024/Aug/6/openai-structured-outputs/
verified 2026-08-03; OpenAI, "Structured Outputs",
https://developers.openai.com/api/docs/guides/structured-outputs verified
2026-08-03). Both routes are compiled into the same underlying enforcement
mechanism, so the vendor name for the feature and the mechanism name below are
two labels for one thing, one is a product, the other is an implementation.

**Constrained decoding** and **guided generation** are the terms the
inference-engine and academic literature use for the mechanism itself,
restricting which tokens a model is permitted to sample at each decoding
step so that the finished sequence is guaranteed to belong to a target
language, most often the language of "valid instances of this JSON Schema."
The formalization most often cited for this specific approach, expressing
guided generation as movement through the states of a finite automaton built
from a regular expression or a context-free grammar, comes from Brandon
Willard and Remi Louf, "Efficient Guided Generation for Large Language
Models", first submitted 19 July 2023, https://arxiv.org/abs/2307.09702
verified 2026-08-03. Their open source implementation, Outlines, is discussed
in dimension 8 and dimension 9 below. Constrained decoding as a broader idea,
restricting a generator's vocabulary at each step to only the tokens that keep
a partial output well formed, has older roots in constrained machine
translation and constrained program synthesis, which this entry does not
attempt to date precisely because no single paper is agreed on as the origin
for the general idea. The Willard and Louf paper is cited here because it is
the specific formalization that the widely used Outlines library, and by
extension a large share of the open source structured output tooling that
followed it, is built on.

**Grammar-constrained sampling** is Anthropic's name for its own
implementation of the same mechanism. Anthropic's documentation states the
technique directly, "constraining the model's token sampling to schema-valid
outputs (a technique called grammar-constrained sampling)" (Anthropic,
"Strict tool use", https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use
verified 2026-08-03), and elsewhere describes the compiled artifact as a
context-free grammar that both a top level output format response and a
strict-mode tool definition are lowered into before generation begins
(Anthropic, "Structured outputs", https://platform.claude.com/docs/en/build-with-claude/structured-outputs
verified 2026-08-03).

**Schema-constrained generation** is the vendor-neutral phrase this entry uses
when discussing the pattern in general, across providers, rather than any one
vendor's branded feature.

One more distinction matters more than any of the names above. Practitioners
frequently say "I get structured output from the model" when they mean
nothing more than "I asked the model, in the prompt, to reply with JSON, and
it usually does." That is prompted formatting, not the pattern this entry
describes. Prompted formatting carries no guarantee, the model can and does
occasionally wrap the JSON in a sentence, add a trailing comma, or omit a
field it judged unnecessary. The pattern earns its name only when a mechanism
outside the model's free choice, a compiled grammar constraining sampling, a
finite state machine masking the logits, or a library that validates and
automatically retries, is doing the enforcement. This entry covers both the
mechanically guaranteed form and the validate-and-retry form, because both are
in wide production use and a reader choosing between them needs to see them
side by side, but it treats "ask nicely in the prompt with no verification
at all" as outside the pattern's boundary, a starting point the other
variants exist to replace.

## 2. Problem and context

A program that calls a large language model eventually has to do something
with the words that come back. If the next step is a person reading the
words, near enough is good enough, a sentence that trails off oddly or uses
an unexpected synonym rarely breaks anything. If the next step is code, near
enough is not good enough. A price extraction pipeline needs a number in a
field named `total`, not a paragraph that happens to contain a price
somewhere in the middle of a sentence. A support ticket router needs one of a
fixed set of category strings, not a category the model half invents by
combining two real ones. A tool-calling agent needs an argument object whose
keys exactly match the function signature the calling code is about to parse
and unpack, because a missing key or a string where an integer was expected
raises an exception three stack frames from where the mistake actually
happened.

The underlying reason this is hard is that a language model, trained on
next-token prediction over ordinary text, is optimized to produce a plausible
continuation of a conversation, not a byte sequence that satisfies a formal
grammar. Even a model instructed at length, "reply with only valid JSON
matching this exact schema, no other text," is still sampling tokens from a
distribution that was never constrained to respect that instruction, so the
instruction is advisory. It usually works. It does not always work, and the
failures cluster in the cases that matter most, a field the model was
genuinely unsure about, a schema with many similarly named fields, a long
context where the schema instruction has scrolled far from the point of
generation, an edge case the training data underrepresented. A pipeline that
ships to production on the strength of "it worked in my ten test prompts" is
one edge case away from an exception at two in the morning, or worse, a
silently accepted malformed value that corrupts a downstream table.

The context in which this problem appears is any boundary crossing between
free text generation and typed consumption. Three shapes recur constantly
enough to be worth naming individually. Extraction, pulling typed fields out
of an unstructured document, an email, a resume, a contract clause, into a
record a database or a form can accept. Classification, choosing exactly one
label from a closed, known set, where the failure mode of a model inventing a
label that is close to but not a member of the set is worse than an outright
wrong answer, because it silently fails a downstream lookup table. Action
selection, an agent deciding which tool to call and with what arguments,
where the "text" being generated is not prose at all, it is effectively a
function call, and every major agent framework routes this specific case
through the same underlying mechanism this entry covers, see the function
calling entry for the sibling pattern that structured output underlies. In
every one of these three shapes, the cost of a malformed crossing ranges from
a caught exception and a retry, mildly annoying, to a row silently written
with the wrong type, expensive to notice, to (in an agent with real tool
access) a destructive or nonsensical action executed with bad arguments,
expensive in a different and worse way.

## 3. Forces

**Guarantee strength against schema expressiveness.** The stronger the
mechanical guarantee a provider is willing to make, the smaller the subset of
JSON Schema it can support, because every additional feature, numeric range
constraints, string length limits, recursive types, open-ended additional
properties, is one more thing the grammar compiler has to be able to turn
into a decidable, efficiently checkable set of allowed continuations at every
token position. Every vendor examined in dimension 8 below drops minimum and
maximum length or numeric range keywords from its strict mode, and several
drop recursive schemas outright. A design that needs those constraints has to
choose between weakening the schema to fit the guarantee, or keeping the full
schema and validating those specific fields itself after generation, giving
up the "single call, hard guarantee" property for the fields that need it.

**Shape correctness against content correctness.** This is the force teams
most often misjudge, and it deserves to be named plainly rather than buried
in a caveat. A schema-conformant response guarantees the JSON parses and the
types match. It says nothing about whether the values are true. A model
forced to fill a numeric confidence field that it has no real basis for still
fills it, because the grammar requires a well-formed number in that
position, it cannot leave the field blank or write "I am not sure" the way
free text would allow. This is the mechanism inventing a false sense of
certainty if the schema was not designed with an explicit way to express
uncertainty, a nullable field, an unknown enum member, a confidence field
the caller is told to treat with suspicion. The pattern buys reliability on
the parser side of the boundary and trades away nothing at all on the truth
side, and conflating the two is the single most common production mistake
this entry documents.

**Latency and cost against reliability.** Compiling a JSON Schema into a
grammar or a finite state machine is not free. Anthropic documents a first
request latency cost for schema compilation, mitigated by a 24 hour cache of
the compiled artifact keyed to the exact schema, invalidated the moment the
schema changes (Anthropic, "Structured outputs",
https://platform.claude.com/docs/en/build-with-claude/structured-outputs
verified 2026-08-03). A pipeline that generates a fresh, slightly different
schema on every call, for example by embedding a dynamic enum built from
database rows, pays the compilation cost on every single call rather than
amortizing it, which is a real cost trap worth naming here and returned to in
dimension 11.

**Provider portability against provider-native strength.** OpenAI's strict
mode, Anthropic's strict tool use and structured outputs, and Google's
schema-based response format are three implementations of the same idea with
three different supported JSON Schema subsets, three different request
shapes, and three different failure behaviors. A team that codes directly
against one vendor's schema dialect gets that vendor's exact guarantee and
its exact limitations. A team that routes through a library such as
Instructor or LangChain's structured output helper, discussed in dimension 8,
gets a single call shape across vendors, at the cost of depending on the
library correctly translating between dialects, and of falling back to a
weaker, validate-and-retry strategy for any provider or model that has no
native support at all.

**Determinism against model creativity.** Forcing a fixed field order and a
closed vocabulary of keys is exactly the kind of rigid contract that a
reasoning-heavy task can be hurt by if the schema puts a final answer field
before a reasoning field, because a model generating strictly in schema order
commits to the answer before it has "thought" about it in the generated text.
This is not a documented vendor claim in any of the sources checked for this
entry, it is a pattern-level design consideration worth stating plainly as
judgment rather than as a sourced fact. The practical fix, ordering a
reasoning or rationale field before the answer field inside the schema so the
generated tokens for the rationale precede and can influence the tokens for
the answer, is covered as a variant in dimension 8.

A pattern that traded away nothing would not be a pattern, it would be a free
lunch. The price here is paid in a smaller expressible schema surface, in a
first-call latency tax, in a real risk of false confidence in field values
the model was never asked to hedge on, and in extra engineering effort spent
either accepting one vendor's dialect or paying for a portability layer on
top of it.

## 4. Applicability and non-applicability

Reach for schema-constrained generation when the following hold.

- The next consumer of the model's output is code, not a person, a
  deserializer, a typed function call, a database write, or a UI component
  bound to specific fields.
- The task is extraction of a small, known set of typed fields from
  unstructured or semi-structured input, an invoice, a resume, a support
  ticket, a meeting transcript.
- The task is classification into a closed, named set of labels, where an
  invented near-miss label is a worse failure than an explicit wrong answer.
- The task is choosing and populating the arguments for a tool or function
  call inside an agent loop, see the function calling entry for the
  companion pattern this mechanism underlies.
- A downstream system enforces its own schema anyway (an API, a message
  queue, a form), so the model might as well produce a payload that already
  matches it instead of an intermediate free text form that a second parsing
  step has to translate.
- The team is willing to design the schema to allow honest uncertainty,
  nullable fields, an explicit unknown enum value, so the mechanism is not
  forced to manufacture a confident-looking wrong answer.

Do NOT reach for schema-constrained generation in these cases, and the reason
matters more than the rule.

- **The output is meant to be read by a person, not consumed by code.** A
  customer support reply, a summary, a piece of marketing copy, an
  explanation. Forcing these into a rigid field structure degrades tone,
  completeness, and the natural variability that makes prose readable. Plain
  generation is the right tool, and if a structured record needs to be
  derived from the reply afterward, that is a second, separate extraction
  call over the finished text, not a reason to structure the reply itself.
- **The schema the task actually needs cannot be expressed inside the target
  provider's supported JSON Schema subset.** Deep recursion, string length
  bounds, numeric ranges, and several composition keywords are unsupported or
  partially supported across every vendor covered in dimension 8. Forcing the
  schema down to what the grammar compiler accepts silently drops exactly the
  constraints that mattered, and a team that does this without separately
  validating the dropped constraints after generation has quietly reintroduced
  the very problem the pattern exists to solve.
- **The task is reasoning-heavy and the schema would force premature
  commitment.** A schema whose first required field is the final answer,
  with any chain of reasoning relegated to a later field or omitted
  entirely, denies the model the chance to generate exploratory tokens before
  committing. The fix is usually a schema shape, not abandoning the pattern,
  put a reasoning field first, see dimension 8, but if the schema genuinely
  cannot be reordered because a downstream consumer expects the answer field
  first, plain generation followed by a second structuring pass over the
  finished reasoning is the safer shape.
- **The team will treat a schema guarantee as a correctness guarantee and
  skip semantic validation of the values.** This is a process risk, not a
  technical limitation of the mechanism, but it recurs often enough in
  production incidents that it belongs on this list. A shape guarantee with
  no value validation is not a safer system than free text with careful
  parsing, it is a system whose bugs are harder to notice because they no
  longer throw an exception.
- **A much simpler prompt-and-regex extraction is already reliably sufficient
  for a low-value, high-volume task**, and the schema compilation latency,
  the vendor-specific request shape, or a portability library's dependency
  weight is not worth paying for a task where an occasional missed match is
  cheap to retry or ignore.
- **The runtime is a small local model or an inference server with no
  constrained decoding support at all, and the call sits inside a hard
  real-time latency budget that cannot absorb even one retry round trip.**
  Deterministic extraction outside the model, or a small fine-tuned
  classifier trained specifically for the fixed label set, often outperforms
  any prompted approach on both latency and reliability in this narrow case.

## 5. Structure

Five participants, named by the role each plays rather than by any one
vendor's exact field name for it.

- **Schema.** The formal description of the shape the caller wants back,
  almost always a JSON Schema document or a language-native equivalent that
  compiles to one, a Pydantic model, a Zod schema, a dataclass with type
  annotations. The schema is authored once by application code and is the
  only artifact both the compiling side and the validating side agree on.
- **Compiler (or validator, in the retry-based variant).** The component that
  turns the Schema into an enforceable constraint. In the mechanically
  guaranteed family this is a grammar or finite state machine compiler
  running inside the provider or inference engine, described in dimension 8.
  In the validate-and-retry family this same role is played by a plain JSON
  Schema validator run after the fact against the model's raw output.
- **Model.** The language model doing the actual token-by-token generation.
  In the mechanically guaranteed family, the Model's sampling distribution at
  each step is masked by the Compiler's output, so the Model is never even
  offered an invalid next token. In the retry family, the Model is
  unconstrained and simply asked, and may or may not comply.
- **Request wrapper.** The library or SDK call site, a parse helper, a
  response-format parameter, Instructor's response-model parameter, or a
  hand-rolled HTTP call, that carries the Schema alongside the prompt and, on
  the way back, hands the caller a typed object rather than a raw string.
- **Consumer.** The downstream code, a function call, a database write, a
  routing decision, that receives the validated, typed value and proceeds
  without needing to parse or defensively check a free text string.

Relationships. The Request wrapper holds the Schema and passes it to both the
Compiler and, eventually, the Consumer's expected type. The Compiler produces
a constraint that is applied either during the Model's decoding (mechanically
guaranteed family) or after the Model's decoding completes (retry family). In
the retry family only, a feedback edge exists from the Validator back to the
Model, carrying the validation error as additional prompt context for a
second attempt, up to a bounded retry count. The Consumer never talks to the
Model directly, it only ever receives what has already passed through the
Compiler or Validator, which is the entire point of the pattern, the boundary
crossing from free text to typed code happens exactly once, in one place, and
every other line of Consumer code can assume the value is well formed.

## 6. ASCII structure diagram

```
  Mechanically guaranteed family (OpenAI strict mode, Claude strict tool
  use, vLLM guided decoding, Outlines)

  +------------------+        +---------------------+
  |  Application      | Schema |    Compiler          |
  |  (defines Schema) | -----> |  (Schema -> grammar   |
  +------------------+        |   or FSA over tokens) |
                                +----------+-----------+
                                           |
                                           | constrains sampling
                                           v
  +------------------+        +---------------------+       +-------------+
  |  Request wrapper  | prompt |       Model          | text |  Consumer   |
  |  (SDK call site)  | -----> | (token-by-token,     | ---> | (typed code)|
  +------------------+        |  invalid tokens are   |      +-------------+
                                |  masked out at        |
                                |  every step)          |
                                +---------------------+

  Validate-and-retry family (Instructor, LangChain fallback path)

  +------------------+        +---------------------+
  |  Application      | Schema |       Model           |
  |  (defines Schema) | -----> |  (unconstrained,      |
  +------------------+        |   free generation)     |
                                +----------+-----------+
                                           |
                                           | raw text
                                           v
                                +---------------------+
                                |      Validator        |
                                | (parse + check Schema)|
                                +----+--------------+---+
                                     |              |
                                valid|              |invalid, N < max_retries
                                     v              v
                              +-------------+  feed error back into prompt,
                              |  Consumer   |  regenerate (bounded loop)
                              +-------------+
```

## 7. Dynamics

The two families differ in exactly when the enforcement happens, before a
token is chosen or after the whole sequence is already generated, and that
timing difference is the most important thing to understand about how the
pattern behaves at runtime.

In the mechanically guaranteed family, the Compiler step happens once per
distinct Schema, before any generation for that request begins. It builds a
representation, most vendors describe this as a context-free grammar or a
finite state automaton, of every prefix that could still lead to a valid
document. During decoding, at each step the Model produces a probability
distribution over its entire vocabulary as usual, but before a token is
sampled, every token that would make the sequence-so-far unable to ever reach
a valid completion is masked out, given zero probability, and the Model
samples only from what remains. This repeats for every single token in the
output, so the guarantee holds continuously, not just at the end. Because the
compiled grammar for a given Schema does not change between calls, a compiled
artifact can be cached and reused, which is exactly what Anthropic's 24 hour
cache and OpenAI's schema caching both do, turning the compilation cost into
a one-time tax rather than a per-call one for a stable Schema.

```
  Mechanically guaranteed, one request

  App          Request wrapper       Compiler         Model
   |                  |                  |               |
   |-- Schema+prompt ->|                  |               |
   |                  |-- Schema (if not cached) -------->|
   |                  |                  |-- grammar ---->| (cached after
   |                  |                  |                |  first use)
   |                  |-------- prompt + grammar --------->|
   |                  |                  |                | for each token:
   |                  |                  |                |  mask invalid
   |                  |                  |                |  tokens, sample
   |                  |<----------- typed JSON ------------|  from the rest
   |<-- typed value --|                  |               |
```

In the validate-and-retry family there is no masking during decoding at all.
The Model generates completely freely, the way it always does, and the
enforcement happens entirely after the fact, a JSON Schema validator checks
the finished text. If validation passes, the value flows to the Consumer
exactly as in the other family. If it fails, the library, Instructor's
default behavior is the clearest documented example (Instructor,
"Structured Output Extraction for LLMs", https://github.com/instructor-ai/instructor
verified 2026-08-03), appends the validation error message to the
conversation and issues a second request asking the Model to correct it, up
to a caller-configured retry limit. This is strictly weaker as a guarantee,
a Model that keeps producing the same mistake exhausts the retry budget and
the call fails outright, but it is the only option available for any
provider or self-hosted model that offers no native constrained decoding at
all, and LangChain's structured output helper uses exactly this fallback for
models without native support while preferring the provider-native path when
it is available (LangChain, "Structured output",
https://docs.langchain.com/oss/python/langchain/structured-output verified
2026-08-03).

```
  Validate-and-retry, one request, one correction

  App                Model                      Validator
   |                    |                             |
   |-- Schema+prompt --->|                             |
   |                    |-- free text ---------------->|
   |                    |                             |-- check against Schema
   |                    |                             |   FAILS, e.g. missing
   |                    |                             |   required field
   |                    |<-- error + retry prompt -----|
   |                    |-- free text (attempt 2) ---->|
   |                    |                             |-- check against Schema
   |                    |                             |   PASSES
   |<-------------- typed value ------------------------|
```

## 8. Implementation variants

**OpenAI Structured Outputs, strict mode plus the JSON schema response
format.** The caller's JSON Schema is compiled into a context-free grammar,
per OpenAI's own description of the mechanism relayed in Simon Willison's
coverage of the launch (Simon Willison,
https://simonwillison.net/2024/Aug/6/openai-structured-outputs/ verified
2026-08-03). Supported models include a small preview model and its
successors from the same era, with OpenAI's current documentation pointing
new integrations at its newest model line (OpenAI, "Structured Outputs",
https://developers.openai.com/api/docs/guides/structured-outputs verified
2026-08-03). Limits documented as of the verification date, a maximum of
5,000 total object properties, up to 10 nesting levels, the root of the
schema must be an object rather than a bare union of types, every field must
be listed as required, and the additional properties flag is mandatory set
to false on every object. Unsupported keywords include minimum and maximum
string length, minimum, maximum, and multiple-of constraints on numbers, and
the composition keywords all-of, not, and dependent-required, alongside a
120,000 character cap on the schema's serialized size and a 1,000 value cap
on total enum members (same source). A field that genuinely needs a numeric
range or a string length bound has to be validated by the caller after the
fact, the schema itself cannot express it in strict mode.

**OpenAI JSON mode, the plain json-object response format.** The predecessor
feature, still available, still only guarantees syntactic validity, an
opening and closing brace and correctly quoted keys, with no enforcement of
which keys appear or what type their values take. OpenAI's own guidance is to
prefer Structured Outputs over this mode whenever a schema is known in
advance (same source as above).

**Anthropic strict tool use, a strict flag on a tool definition.** Applies
grammar-constrained sampling to a tool's input schema so that a returned
tool-use block's input field is guaranteed to conform, closing the specific
failure mode of a Model returning a quoted numeral where an integer was
declared (Anthropic, "Strict tool use", https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use
verified 2026-08-03). The compiled schema is cached for up to 24 hours from
last use, and Anthropic's documentation carries an explicit warning that
protected health information must never be placed inside a schema's property
names, enum values, const values, or pattern regular expressions, because the
compiled schema cache does not receive the same data protection treatment as
message content (same source).

**Anthropic structured outputs, a top level output format.** A second,
complementary feature that constrains the shape of the assistant's own
response text rather than a tool's arguments, invoked through SDK parse
helpers that accept a Pydantic model directly and return an already
validated, typed parsed output (Anthropic, "Structured outputs",
https://platform.claude.com/docs/en/build-with-claude/structured-outputs
verified 2026-08-03). Its supported JSON Schema subset includes enum, const,
any-of, limited all-of, ref plus local definitions, and a fixed list of
string formats, date-time, date, time, duration, email, hostname, uri,
ipv4, ipv6, and uuid. It does not support recursive schemas, complex types
nested inside an enum, external ref targets, or numeric and string length
constraints, and additional properties must be false on every object,
exactly as with strict tool use, because both features are compiled through
the same grammar pipeline (same source). Anthropic's SDKs will rewrite an
unsupported constraint out of the compiled schema automatically, folding the
dropped constraint's meaning into the field's description text instead, and
then re-validate the finished response against the caller's original, full
schema after generation, layering a client-side check on top of the
server-side grammar guarantee for exactly the constraints the grammar itself
cannot enforce.

**Google Gemini's schema-based response format with a JSON mime type.**
Accepts a subset of JSON Schema, basic types, title and description,
properties, required, additional properties, string enum and format values
date-time, date, and time, and, notably, numeric minimum and maximum, along
with array items, prefix items, minimum items, and maximum items (Google,
"Structured output", https://ai.google.dev/gemini-api/docs/structured-output
verified 2026-08-03). Gemini's SDKs also accept a Pydantic base model
directly in Python or a Zod schema converted through a JSON Schema adapter in
JavaScript, rather than requiring the caller to hand-write raw JSON Schema
(same source). Google's public documentation does not state whether the
underlying enforcement mechanism is grammar-based, logit-masking, or
something else, unlike OpenAI's and Anthropic's documentation which both name
their mechanism explicitly, this entry does not assert an implementation
detail Google has not published.

**Local and self-hosted constrained decoding, Outlines and vLLM.** Outlines
implements the Willard and Louf mechanism directly, a regular expression or a
JSON Schema is compiled into a finite state machine indexed against the
Model's own vocabulary once, and that index is then used for fast logit
masking at every decoding step (Outlines,
https://github.com/dottxt-ai/outlines verified 2026-08-03). It runs against
local transformers and llama.cpp models, against vLLM and Ollama servers, and
against the OpenAI and Gemini APIs, and is used inside vLLM's own
OpenAI-compatible server as one of several selectable structured output
backends, alongside xgrammar, guidance, and lm-format-enforcer, exposed
through the same response-format field OpenAI's clients already send, or
through a dedicated guided-json request shape for constraint types including
a fixed choice set, a regex, a JSON Schema, and a context-free EBNF grammar
(vLLM, "Structured Outputs",
https://docs.vllm.ai/en/latest/features/structured_outputs.html verified
2026-08-03).

**Reasoning-before-answer schema ordering.** A schema whose fields are
ordered so a rationale or reasoning field is required before the final
answer field forces the Model's generated tokens for the rationale to precede
the tokens for the answer, letting earlier generated content influence later
generation the way free chain-of-thought does, while a schema with the
answer field first denies that. This is not a claim sourced to a specific
vendor's documentation, it is a design consideration worth stating as
engineering judgment, grounded in how autoregressive decoding works,
generation is strictly left to right, so anything the Model has not yet
generated cannot have influenced a field placed earlier in the document.

**Validate-and-retry libraries, Instructor and LangChain's fallback path.**
Instructor wraps an existing provider client and lets the caller pass a
Pydantic response model directly, dispatching to the provider's own native
structured mode when the provider supports one and falling back to a plain
prompt-and-validate loop otherwise, retrying automatically with the
validation error fed back into the next attempt up to a caller-set retry
limit (Instructor, https://github.com/instructor-ai/instructor verified
2026-08-03). LangChain's agent construction and structured output helper make
the same choice explicit at the framework level, preferring "the most
reliable method when available", the provider's native structured output,
and falling back to tool calling, "all models that support tool calling
(most modern models)", when native support is absent (LangChain, "Structured
output", https://docs.langchain.com/oss/python/langchain/structured-output
verified 2026-08-03). This variant is the only one of the group that is fully
provider portable in the sense of running against literally any model that
can follow instructions at all, at the cost of no hard guarantee and an
unbounded (within the retry budget) number of extra round trips.

## 9. Known production uses

**OpenAI's Structured Outputs, used across the OpenAI API surface itself.**
Shipped 6 August 2024 as a first party capability of the Chat Completions and
Responses APIs, documented with the explicit claim that the model will
always generate responses that adhere to the caller's supplied JSON Schema
(OpenAI, "Structured Outputs", https://developers.openai.com/api/docs/guides/structured-outputs
verified 2026-08-03). This is the single most widely reached implementation
of the pattern by request volume among the sources checked for this entry,
because it ships as a built-in flag on the same API surface that already
serves the majority of hosted large language model traffic.

**Anthropic's strict tool use and structured outputs, used across the Claude
API and Claude Code's own tool-calling loop.** Anthropic documents the same
grammar-constrained sampling mechanism serving both a tool's argument object
and a top level structured text response, and states plainly that reliable
agentic systems "require guaranteed schema conformance" and that without it
"Claude might return incompatible types... or omit required fields, breaking
your functions and causing runtime errors" (Anthropic, "Strict tool use",
https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use
verified 2026-08-03).

**Outlines, adopted by NVIDIA, Cohere, HuggingFace, and vLLM.** Outlines'
own project page states it is "trusted by major organizations including
NVIDIA, Cohere, HuggingFace, and vLLM" and reports 15.5 thousand GitHub stars
and 835 forks as of the verification date (Outlines,
https://github.com/dottxt-ai/outlines verified 2026-08-03). Its adoption
inside vLLM specifically is not merely a citation on a README, vLLM lists
Outlines as one of the selectable backends behind its own structured decoding
feature, meaning every deployment that runs vLLM's OpenAI-compatible server
with the Outlines backend selected is running Willard and Louf's mechanism
in production (vLLM, "Structured Outputs",
https://docs.vllm.ai/en/latest/features/structured_outputs.html verified
2026-08-03).

**Instructor, reporting over three million monthly downloads.** Instructor's
README states it is "Built on Pydantic for validation, type safety, and IDE
support" and reports 13.7 thousand GitHub stars, 1.2 thousand forks, and
usage by "over 100,000 developers and companies", alongside more than three
million monthly downloads (Instructor,
https://github.com/instructor-ai/instructor verified 2026-08-03). Its support
matrix spans OpenAI, Anthropic, Google Gemini, Ollama, and Groq behind one
call shape, making it one of the most widely reached provider-portability
layers over the pattern.

**vLLM's structured decoding feature, shipped inside the de facto standard
open source inference server.** vLLM exposes guided JSON, regex, grammar, and
enumerated choice constraints through the same response-format shape
OpenAI's own client library already sends, meaning any application already
coded against OpenAI's structured output request shape can point its client
at a self-hosted vLLM server and receive the same guarantee against an open
weight model, a portability property vLLM's own documentation frames as
compatibility with the OpenAI-compatible server (vLLM,
https://docs.vllm.ai/en/latest/features/structured_outputs.html verified
2026-08-03).

## 10. Consequences

Positive.

- The boundary between free text generation and typed application code
  collapses to one enforced point instead of being scattered across every
  call site that used to hand-roll a defensive parse and a regex fallback.
- In the mechanically guaranteed family, malformed shape is not merely
  unlikely, it is structurally impossible, because the Model was never
  offered an invalid token to sample at any position in the sequence.
- Downstream code, a tool call handler, a database writer, a routing switch,
  can drop its defensive parsing and trust the type system, shrinking the
  amount of error-handling code that exists purely to guard against model
  output shape.
- The retry-based variant extends the same benefit to any provider or
  self-hosted model, including ones with no native support, at a bounded and
  configurable extra-call cost.
- A stable schema's compiled grammar is cached by every vendor examined in
  this entry, so the enforcement cost is paid once per schema shape, not once
  per request, for the common case of a fixed, unchanging schema.

Negative.

- The guarantee applies to shape, never to truth. A schema-conformant field
  can still hold a confidently wrong value, and a team that treats the shape
  guarantee as a correctness guarantee inherits a false sense of safety.
- The supported JSON Schema subset is meaningfully smaller than JSON Schema
  itself across every vendor examined, numeric ranges, string length bounds,
  and deep recursion are commonly unsupported, forcing either a weakened
  schema or a second, manual validation pass for exactly the constraints the
  grammar cannot express.
- A dynamically varying schema, one that embeds a fresh enum or field set
  built from live data on every call, pays the full compilation cost on
  every single request instead of amortizing it through the vendor's cache,
  quietly turning a fast feature into a slow one.
- Vendor dialects differ enough that code written directly against one
  provider's schema rules does not port cleanly to another, and the
  portability libraries that solve this add a dependency and, on the
  fallback path for unsupported providers, give up the hard guarantee
  entirely.
- A schema whose fields are ordered answer-first can measurably reduce a
  reasoning-heavy task's quality by forcing the Model to commit to a
  conclusion before generating any supporting reasoning tokens, a cost that
  is easy to introduce by accident when a schema is designed around what a
  downstream consumer wants to read first rather than around generation
  order.

## 11. Failure modes and misuse

**The false confidence field.** Symptom. A sentiment or confidence field is
always populated, never null, never a plausible "unsure" value, even on
genuinely ambiguous inputs, and a team downstream starts trusting a metric
that was never meaningful. Cause. The schema required the field and gave the
Model no schema-legal way to express uncertainty, so the mechanism forces a
confident-looking value into a slot that should have been optional. Fix. Add
an explicit null option or an "unknown" enum member to every field where the
Model might genuinely lack a basis for an answer, and treat that value as a
first class outcome in downstream logic rather than as an edge case to
special-case away.

**Silent schema truncation.** Symptom. A field the team is certain they
defined with a numeric range, an age between zero and one hundred thirty,
comes back with an out-of-range value, nine thousand nine hundred ninety
nine or a negative number, and the schema appeared to be respected because
the request did not error. Cause. The provider's strict mode does not
support minimum and maximum on numbers and silently accepted the schema with
those keywords stripped, or in Anthropic's case, rewrote them into the
field's description text rather than the enforced grammar (Anthropic,
"Structured outputs", https://platform.claude.com/docs/en/build-with-claude/structured-outputs
verified 2026-08-03), meaning the range is now advisory prose, not a
constraint. Fix. Re-read the target vendor's documented JSON Schema subset
before shipping, and add a manual validation pass, after the parse, for any
constraint the grammar itself cannot enforce, treating the model's own
guarantee as covering shape only.

**The dynamic schema cost cliff.** Symptom. A pipeline that was fast in
testing gets measurably slower in production, specifically on the first call
of every batch or every distinct customer. Cause. The schema embeds a
per-customer or per-batch enum, a list of valid category identifiers pulled
from a database, so every call presents the compiler with a schema it has
never seen before, defeating the vendor's compiled-grammar cache entirely and
paying the full compilation latency on every single request. Fix. Where
possible, replace a dynamic enum with a fixed, small closed set plus a
post-generation lookup or validation step, or accept the compilation cost
explicitly and measure it, rather than discovering it as an unexplained
latency regression.

**Retry loop that never converges.** Symptom. A validate-and-retry call using
Instructor or a similar library exhausts its retry limit and raises, despite
the task looking simple. Cause. The Model has a systematic, repeated
misunderstanding of the schema, most often an ambiguous field name or a
schema shape the Model's training distribution rarely saw, so feeding the
same validation error back does not change its next attempt in a useful
direction, it repeats the same category of mistake. Fix. Log the actual
validation error and the Model's raw attempt on every retry, not just the
final failure, then rename the ambiguous field or restructure the schema
based on what the failed attempts actually produced, rather than only
increasing the retry budget, which treats the symptom rather than the cause.

**Treating a tool call argument object as pre-validated for safety, not just
shape.** Symptom. An agent executes a destructive or high-privilege action,
a file deletion, a payment, a database mutation, using a strict-mode
guaranteed tool argument object, and the action is legal by the schema but
wrong or unsafe in context, for example a quantity field that is a
schema-valid positive integer but is three orders of magnitude too large for
the actual request. Cause. Strict mode enforces shape, never business logic
or safety bounds, and a team that reads "guaranteed schema conformance" as
"guaranteed safe to execute" has skipped the semantic validation layer the
mechanism was never designed to provide. Fix. Keep an explicit business-rule
validation and, for genuinely destructive actions, a human or policy-engine
confirmation step between a shape-guaranteed tool call and its actual
execution, treating the schema guarantee as necessary but never sufficient.

## 12. Trade-off matrix

The comparison below is against the three other places a boundary between
free text and typed code most often gets crossed in an agentic system, not
against an unnamed strawman.

| Force | Structured output (guaranteed family) | Function calling without strict mode | Plain prompted JSON, no validation | Regex or heuristic extraction over free text |
|---|---|---|---|---|
| Shape guarantee | Mechanical, holds every token | None, best effort by the Model | None, best effort by the Model | None, depends entirely on pattern coverage |
| Content correctness | Not addressed, needs separate validation | Not addressed | Not addressed | Not addressed, and pattern itself can misfire |
| Latency | First-call compilation cost, cached after | Normal generation latency only | Normal generation latency only | Fast, no extra model round trip |
| Portability across vendors | Low without a library, dialects differ | Higher, most providers support some tool calling | Highest, works against any model that follows instructions | Highest, model-independent entirely |
| Expressible schema surface | Reduced, vendor-specific subset of JSON Schema | Effectively the caller's own schema, since nothing enforces it | Unconstrained in theory, unenforced in practice | Whatever the pattern author encodes, brittle to input drift |
| Failure mode when it fails | Request-level error at compile time, caught early | A malformed argument object at runtime, caught late | A parse exception or silent corruption, caught late or never | A missed or wrong extraction, often silent |
| Best fit | Typed extraction, classification, tool arguments consumed by code | Legacy integrations where strict mode is unavailable, or the shape is genuinely loose | Prototyping only, never a production boundary on its own | Fixed-format legacy documents where an LLM is unnecessary overhead |

## 13. Related and incompatible patterns

**Function calling.** The two patterns share their enforcement mechanism
directly, the same grammar-constrained sampling that guarantees a top level
JSON response also guarantees a tool's argument object, and Anthropic's own
documentation groups both under one "structured outputs" umbrella
(Anthropic, https://platform.claude.com/docs/en/build-with-claude/structured-outputs
verified 2026-08-03). The distinction worth keeping in mind is which
consumer receives the value, an application's own deserializer for
structured output proper, versus a specific named tool handler for function
calling, see the function calling entry for that companion pattern in full.

**ReAct.** A ReAct loop alternates free text reasoning with an action step,
and the action step is exactly the kind of typed, machine-consumed output
this entry covers, so a production ReAct implementation typically wraps its
action-selection step in schema-constrained generation while leaving the
reasoning (thought) step as free text, composing the two patterns rather than
choosing one over the other. See the ReAct entry for the surrounding loop.

**Plan and execute.** A planner's output, the ordered list of steps an
executor will run, is itself a structured artifact, and schema-constrained
generation is the natural mechanism for guaranteeing that list is
well-formed, each step naming a valid tool and valid arguments, before an
executor ever begins acting on it. See the plan and execute entry.

**Orchestrator worker.** An orchestrator's routing decision, which worker
handles a given piece of input, is a small closed-set classification
problem, one of the cases this entry names directly under applicability, and
benefits from the same enum-constrained guarantee that prevents an
orchestrator from inventing a worker name that does not exist. See the
orchestrator worker entry.

No pattern examined for this entry actively conflicts with schema-constrained
generation in the sense of the two being unable to compose. The nearest thing
to an incompatibility is internal to the pattern itself, an answer-first
schema ordering working against a reasoning-heavy task, covered in dimension
4 and dimension 8 above, which is a design mistake within the pattern rather
than a conflict with a separate pattern.

## 14. Refactoring path in and out

Introducing schema-constrained generation into an existing free-text
pipeline, step by step.

1. Identify the exact point where the model's output currently gets parsed
   by hand, a defensive JSON parse wrapped in error handling, a regex
   pulling a number out of a sentence, a string comparison against a list of
   expected category names. This is the boundary the pattern will replace.
2. Write the target shape as a schema in the caller's own language, a
   Pydantic model, a Zod schema, a plain JSON Schema document, independent of
   any vendor-specific dialect first, so the intent is captured before
   dialect limitations start shaping it.
3. Check the target provider's documented JSON Schema subset against the
   schema from step 2. Flag every unsupported keyword, a numeric range, a
   string length bound, deep recursion, before writing any request code, not
   after a production surprise.
4. For each flagged, unsupported constraint, decide explicitly whether to
   drop it from the schema (accepting the wider range of values) or keep it
   in the schema for documentation purposes and add it to a manual
   post-generation validation step. Do not silently drop it and forget it was
   ever a requirement.
5. Swap the hand-rolled parsing call for the provider's or library's
   structured call, strict mode plus a JSON Schema response format, a top
   level output format, or a validate-and-retry library, and delete the old
   defensive parsing code, it is now dead weight the mechanism has taken
   over.
6. Add the manual validation step from step 4, if any constraints were kept
   outside the schema, immediately after the structured call returns, before
   the value reaches the Consumer.
7. Add a test asserting the schema itself is well formed for the target
   provider, see dimension 15, so a future schema edit that accidentally
   introduces an unsupported keyword fails fast in a test rather than in
   production.

Removing schema-constrained generation, when it has stopped earning its
place, follows the same steps in reverse, and the two situations that most
often justify removal are worth naming plainly. First, the schema has grown
so large or so dynamic, see the dynamic schema cost cliff in dimension 11,
that the compilation cost outweighs the reliability benefit for a
particular high-frequency, low-value call, and a cheaper heuristic extraction
is genuinely sufficient there. Second, the output has quietly become
something a person reads directly rather than something code consumes, a
summary field that grew from one sentence into a full report, at which point
forcing it through a rigid schema is actively degrading the thing it was
meant to protect.

## 15. Testing and verification

**Schema conformance is not the thing to write a unit test for, it is
already mechanically guaranteed in the family that guarantees it.** Writing
a test that merely asserts the returned object parses against its own schema
is close to tautological in that family and provides little confidence. The
tests that carry real information sit one level up and one level down from
that guarantee.

One level up, a schema well-formedness test, run against the target
provider's own documented subset, at authoring time and in continuous
integration, catches the case where a schema edit introduces an unsupported
keyword before the first production request does. This is cheap, offline,
and does not require calling the model at all, it only requires a validator
for the vendor's documented subset, which several of the SDKs examined in
this entry ship as an internal utility already.

One level down, from the schema guarantee, sits the thing the guarantee does
not cover, content correctness. This needs a small, curated set of example
inputs with known-correct expected values, an evaluation set in the sense the
retrieval augmented generation and self consistency entries in this family
also use, run against the live structured call, asserting not that the shape
is valid, that part is guaranteed, but that the extracted total actually
matches the invoice's real total, that the chosen classification label
actually matches a human-labeled ground truth. This is the test suite that
catches the false confidence field failure mode from dimension 11, because a
shape-only test suite would pass on a confidently wrong value every time.

For the validate-and-retry family specifically, a further test worth writing
deliberately induces a validation failure, a deliberately malformed mock
model response, and asserts the retry loop's error-feedback and bound behave
as intended, the corrected value is accepted on a subsequent attempt, and the
call fails cleanly, without retrying forever, once the retry limit is
exhausted. A retry loop that has never been tested against its own failure
path is untested precisely where it is most likely to matter.

Finally, any manual post-generation validation added in step 6 of the
refactoring path in dimension 14, for constraints the provider's schema
dialect could not express, needs its own direct unit tests, independent of
the model entirely, feeding known-good and known-bad values straight into
the validator function, because this is ordinary application code and should
be tested the ordinary way, not exercised only indirectly through a live
model call.

## 16. Observability signals

**Schema compilation and cache behavior.** Where the vendor exposes it,
track whether a given request hit a cached compiled schema or triggered a
fresh compilation, and the latency delta between the two. A healthy system
shows a small, stable fraction of requests paying the compilation cost, the
first request for each distinct schema shape, and the rest served from
cache. A system where compilation latency dominates, or where the cache-hit
fraction is unexpectedly low, is showing the dynamic schema cost cliff from
dimension 11 in its metrics before a person notices it in wall-clock time.

**Validation failure rate, for the retry family specifically.** Log every
validation failure, not only the final one that exhausts the retry budget,
with the specific field or constraint that failed and the attempt number.
A healthy system shows first-attempt success dominating and second-attempt
success handling nearly all of what remains. A rising rate of retries needed,
or a nonzero rate of retry budgets exhausted, on a schema that used to
succeed on the first attempt, is a leading indicator that either the input
distribution has shifted or a recent schema edit introduced ambiguity the
Model is now struggling with.

**Field-level null and unknown rate, for schemas that include an explicit
uncertainty option.** Track, per field, how often the Model emits null or an
unknown enum value rather than a concrete answer. A near-zero rate on a field
where genuine ambiguity is common in the input data is itself a signal, not
necessarily a good one, it can mean the schema does not actually give the
Model a comfortable way to express uncertainty and it is instead
manufacturing confident values, the false confidence field failure mode from
dimension 11 made visible as a dashboard metric rather than discovered later
by a person auditing values by hand.

**Content-correctness sampling.** Because shape conformance is guaranteed and
therefore uninformative as an ongoing signal, the metric worth continuously
sampling and reviewing is a small, regular audit of actual extracted or
classified values against ground truth or human review, exactly the
evaluation set described in dimension 15, run on a rolling schedule against
live traffic rather than only at authoring time, since the Model or the
input distribution can both drift after a system is already shipped.

**Downstream exception rate at the Consumer boundary.** A healthy system
using this pattern correctly should see this rate at or near zero, because
the whole purpose of the pattern is to make the boundary crossing safe. A
nonzero rate here, in the mechanically guaranteed family specifically,
usually points to one of two things, either the manual post-generation
validation from dimension 14 step 6 is missing for a constraint the schema
dialect could not express, or the Consumer code is making an assumption the
schema never actually guaranteed, most often confusing shape guarantee for
content guarantee, the recurring theme of this entire entry.

## 17. Security and privacy implications

**Schema caching and sensitive data.** Anthropic's documentation carries a
specific, sourced warning that is worth restating precisely rather than
paraphrasing away its force, compiled schemas are cached separately from
message content and "do not receive the same PHI protections as prompts and
responses," so protected health information, or by extension any sensitive
identifier, must never be placed inside a schema's property names, enum
values, const values, or pattern regular expressions, only inside the
message content itself (Anthropic, "Strict tool use",
https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use
verified 2026-08-03). This is a concrete, provider-documented risk specific
to this pattern, a dynamic schema built at request time from live customer
data, embedding a customer's own identifiers directly into an enum of
allowed values, for example, is exactly the shape that would violate this
guidance, and it is also exactly the shape flagged as a performance problem
in dimension 11's dynamic schema cost cliff, so the same design mistake
carries both a privacy risk and a latency cost.

**Shape guarantee is not an injection or authorization boundary.** A schema
guarantees an argument object's type and key set, it does not evaluate
whether the value is safe to execute, so a strict tool call for, say, a
database query builder can still return a schema-valid filter expression
string that is itself an injection attempt if that string is later
interpolated unsafely into a real query rather than passed through a
parameterized query layer. The pattern narrows the attack surface, a
malformed shape that used to require defensive parsing now cannot occur, but
it does not eliminate the need for the same input-sanitization and
authorization checks any typed input from an untrusted source would need,
because the Model, from a security standpoint, is an untrusted input source
whose output happens to be shape-guaranteed, not a trusted one.

**Enum-based classification as a data minimization technique.** Constraining
a Model's output to a small, closed, non-identifying enum, a risk tier, a
routing category, rather than allowing free text that could inadvertently
restate or elaborate on sensitive input details in the response, is a
genuine privacy benefit of the pattern worth naming on the positive side.
Where an application's downstream logging or analytics pipeline only needs
the classification, not a restatement of the input, an enum-constrained
schema structurally prevents the Model from leaking input content into an
output field that a lower-trust downstream system will later read.

**Retry loops and repeated exposure.** In the validate-and-retry family, a
failed validation attempt's raw, unvalidated output is, by construction, held
in memory and often logged for debugging, before it is discarded or
corrected. Where the input to the original call contained sensitive data, a
support ticket, a medical record excerpt, that same sensitive data is present
in every failed intermediate attempt as well as the final validated one, so a
logging or observability pipeline built for this pattern needs to apply the
same redaction and retention policy to every retry attempt's raw content, not
only to the final, successful response.

## 18. References

- Willard, B., Louf, R. "Efficient Guided Generation for Large Language
  Models." arXiv, first submitted 19 July 2023, revised 19 August 2023.
  https://arxiv.org/abs/2307.09702 verified 2026-08-03.
- Outlines project. "Outlines: Structured Generation for LLMs." GitHub
  repository. https://github.com/dottxt-ai/outlines verified 2026-08-03.
- Instructor project. "Structured Output Extraction for LLMs." GitHub
  repository. https://github.com/instructor-ai/instructor verified
  2026-08-03.
- OpenAI. "Structured Outputs." API documentation.
  https://developers.openai.com/api/docs/guides/structured-outputs verified
  2026-08-03.
- OpenAI. "Structured Outputs Intro." Cookbook example.
  https://developers.openai.com/cookbook/examples/structured_outputs_intro
  verified 2026-08-03.
- Willison, S. "OpenAI's structured outputs for function calling." Blog
  post, 6 August 2024.
  https://simonwillison.net/2024/Aug/6/openai-structured-outputs/ verified
  2026-08-03.
- Anthropic. "Strict tool use." API documentation.
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use
  verified 2026-08-03.
- Anthropic. "Structured outputs." API documentation.
  https://platform.claude.com/docs/en/build-with-claude/structured-outputs
  verified 2026-08-03.
- Anthropic. "Tool use with Claude." API documentation overview.
  https://platform.claude.com/docs/en/build-with-claude/tool-use/overview
  verified 2026-08-03.
- Google. "Structured output." Gemini API documentation.
  https://ai.google.dev/gemini-api/docs/structured-output verified
  2026-08-03.
- vLLM project. "Structured Outputs." Documentation.
  https://docs.vllm.ai/en/latest/features/structured_outputs.html verified
  2026-08-03.
- LangChain. "Structured output." Documentation.
  https://docs.langchain.com/oss/python/langchain/structured-output
  verified 2026-08-03.

## Code

The three implementations below model the pattern's two families without
depending on a live network call, so each one compiles and runs against a
local, deliberately fallible mock model rather than a real API, keeping the
example runnable offline while still exercising the real logic, schema
definition, validation, and the bounded feedback loop.

### Python, a minimal validate-and-retry implementation

Mirrors the mechanism Instructor and LangChain's fallback path both use, a
Pydantic-style schema, a validator, and a bounded retry loop that feeds the
validation error back to the model.

```python
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class InvoiceExtraction:
    vendor: str
    total_cents: int
    currency: str
    is_refund: Optional[bool] = None

    @staticmethod
    def validate(raw: dict) -> "InvoiceExtraction":
        required = {"vendor", "total_cents", "currency"}
        missing = required - raw.keys()
        if missing:
            raise ValueError(f"missing required fields, {sorted(missing)}")
        if not isinstance(raw["vendor"], str) or not raw["vendor"]:
            raise ValueError("vendor must be a non-empty string")
        if not isinstance(raw["total_cents"], int):
            raise ValueError("total_cents must be an integer number of cents")
        if raw["currency"] not in ("USD", "EUR", "GBP"):
            raise ValueError("currency must be one of USD, EUR, GBP")
        return InvoiceExtraction(
            vendor=raw["vendor"],
            total_cents=raw["total_cents"],
            currency=raw["currency"],
            is_refund=raw.get("is_refund"),
        )


@dataclass
class MockModel:
    # A stand-in for a real LLM call. attempts[i] is what the model
    # "returns" on the i-th call for a given document, simulating a model
    # that first makes a mistake and then corrects it once told why.
    attempts: list[str] = field(default_factory=list)
    calls: int = 0

    def generate(self, prompt: str) -> str:
        text = self.attempts[min(self.calls, len(self.attempts) - 1)]
        self.calls += 1
        return text


def extract_with_retry(
    model: MockModel, document: str, max_retries: int = 3
) -> InvoiceExtraction:
    prompt = f"Extract vendor, total_cents, currency from, {document}"
    last_error: Optional[str] = None
    for attempt in range(max_retries):
        if last_error:
            prompt += f"\n\nYour previous answer was invalid, {last_error}. Fix it."
        raw_text = model.generate(prompt)
        try:
            raw = json.loads(raw_text)
            return InvoiceExtraction.validate(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = str(exc)
    raise RuntimeError(f"exhausted {max_retries} retries, last error, {last_error}")


def _demo() -> None:
    # First attempt has a string where an integer belongs and a bad
    # currency code. Second attempt is corrected, the way a real model
    # often self-corrects once shown the exact validation error.
    model = MockModel(
        attempts=[
            '{"vendor": "Acme Corp", "total_cents": "1999", "currency": "US"}',
            '{"vendor": "Acme Corp", "total_cents": 1999, "currency": "USD"}',
        ]
    )
    result = extract_with_retry(model, "Invoice from Acme Corp, total $19.99")
    print(
        f"vendor={result.vendor} total_cents={result.total_cents} "
        f"currency={result.currency} calls_used={model.calls}"
    )
    assert result.total_cents == 1999
    assert model.calls == 2


if __name__ == "__main__":
    _demo()
```

### TypeScript, a schema definition plus client-side validation layer

Models the defense-in-depth idea from dimension 8 and dimension 11, never
trusting a provider's shape guarantee alone for constraints its dialect
cannot express, here a numeric range the mechanically guaranteed family
typically drops.

```typescript
type FieldSpec =
  | { kind: "string"; minLength?: number; maxLength?: number }
  | { kind: "integer"; minimum?: number; maximum?: number }
  | { kind: "enum"; values: readonly string[] };

interface Schema {
  readonly required: readonly string[];
  readonly fields: Readonly<Record<string, FieldSpec>>;
}

type ValidationResult<T> =
  | { ok: true; value: T }
  | { ok: false; errors: string[] };

const supportTicketSchema: Schema = {
  required: ["priority", "category", "summary"],
  fields: {
    priority: { kind: "enum", values: ["low", "medium", "high", "urgent"] },
    category: { kind: "enum", values: ["billing", "bug", "feature", "other"] },
    summary: { kind: "string", minLength: 1, maxLength: 280 },
    estimated_minutes: { kind: "integer", minimum: 0, maximum: 480 },
  },
};

interface SupportTicket {
  priority: string;
  category: string;
  summary: string;
  estimated_minutes?: number;
}

function validateAgainstSchema(
  raw: Record<string, unknown>,
  schema: Schema
): ValidationResult<SupportTicket> {
  const errors: string[] = [];

  for (const key of schema.required) {
    if (!(key in raw)) errors.push(`missing required field, ${key}`);
  }

  for (const [key, spec] of Object.entries(schema.fields)) {
    if (!(key in raw)) continue;
    const value = raw[key];
    switch (spec.kind) {
      case "string": {
        if (typeof value !== "string") {
          errors.push(`${key} must be a string`);
          break;
        }
        // A provider's grammar-based mode commonly drops length bounds,
        // so this check is the defense-in-depth layer dimension 11 warns
        // a team not to skip.
        if (spec.minLength !== undefined && value.length < spec.minLength) {
          errors.push(`${key} shorter than the minimum length ${spec.minLength}`);
        }
        if (spec.maxLength !== undefined && value.length > spec.maxLength) {
          errors.push(`${key} longer than the maximum length ${spec.maxLength}`);
        }
        break;
      }
      case "integer": {
        if (typeof value !== "number" || !Number.isInteger(value)) {
          errors.push(`${key} must be an integer`);
          break;
        }
        if (spec.minimum !== undefined && value < spec.minimum) {
          errors.push(`${key} below the minimum ${spec.minimum}`);
        }
        if (spec.maximum !== undefined && value > spec.maximum) {
          errors.push(`${key} above the maximum ${spec.maximum}`);
        }
        break;
      }
      case "enum": {
        if (typeof value !== "string" || !spec.values.includes(value)) {
          errors.push(`${key} must be one of ${spec.values.join(", ")}`);
        }
        break;
      }
    }
  }

  if (errors.length > 0) return { ok: false, errors };
  return {
    ok: true,
    value: {
      priority: raw.priority as string,
      category: raw.category as string,
      summary: raw.summary as string,
      estimated_minutes: raw.estimated_minutes as number | undefined,
    },
  };
}

function routeTicket(ticket: SupportTicket): string {
  if (ticket.priority === "urgent") return "page-oncall";
  if (ticket.category === "billing") return "billing-queue";
  return "general-queue";
}

function demo(): void {
  // Simulates output that already passed a provider's shape guarantee
  // (right types, right keys) but violates a bound the grammar dropped.
  const shapeGuaranteedButOutOfRange = {
    priority: "high",
    category: "bug",
    summary: "Checkout button does nothing on Safari",
    estimated_minutes: 9000,
  };

  const result = validateAgainstSchema(
    shapeGuaranteedButOutOfRange,
    supportTicketSchema
  );

  if (!result.ok) {
    console.log(`rejected, ${result.errors.join("; ")}`);
  } else {
    console.log(`routed to, ${routeTicket(result.value)}`);
  }

  const validTicket = { ...shapeGuaranteedButOutOfRange, estimated_minutes: 30 };
  const okResult = validateAgainstSchema(validTicket, supportTicketSchema);
  if (okResult.ok) {
    console.log(`routed to, ${routeTicket(okResult.value)}`);
  }
}

demo();
```

### Go, a small finite state validator modeling the shape a grammar compiler enforces

Building the exact acceptance check a provider's compiled grammar performs,
at the level of a single object against a fixed set of allowed keys and
types, makes the mechanism from dimension 7 concrete rather than abstract.

```go
package main

import (
	"fmt"
)

// FieldType mirrors the small set of JSON Schema primitive types every
// vendor examined in this entry supports in its strict mode.
type FieldType int

const (
	TypeString FieldType = iota
	TypeInteger
	TypeEnum
)

type FieldSpec struct {
	Type       FieldType
	EnumValues []string
}

type ObjectSchema struct {
	Required              []string
	Fields                map[string]FieldSpec
	AdditionalProperties  bool // every strict mode examined requires false
}

func classificationSchema() ObjectSchema {
	return ObjectSchema{
		Required: []string{"label", "confidence_band"},
		Fields: map[string]FieldSpec{
			"label": {
				Type:       TypeEnum,
				EnumValues: []string{"spam", "legitimate", "unknown"},
			},
			"confidence_band": {
				Type:       TypeEnum,
				EnumValues: []string{"low", "medium", "high"},
			},
		},
		AdditionalProperties: false,
	}
}

// Validate performs the same acceptance check a compiled grammar performs
// token by token, applied here in one pass after the fact, to make the
// enforced contract explicit and independently testable.
func Validate(raw map[string]interface{}, schema ObjectSchema) error {
	for _, key := range schema.Required {
		if _, present := raw[key]; !present {
			return fmt.Errorf("missing required field, %s", key)
		}
	}

	for key, value := range raw {
		spec, known := schema.Fields[key]
		if !known {
			if !schema.AdditionalProperties {
				return fmt.Errorf("unexpected field not in schema, %s", key)
			}
			continue
		}
		switch spec.Type {
		case TypeString:
			if _, ok := value.(string); !ok {
				return fmt.Errorf("field %s must be a string", key)
			}
		case TypeInteger:
			if _, ok := value.(int); !ok {
				return fmt.Errorf("field %s must be an integer", key)
			}
		case TypeEnum:
			str, ok := value.(string)
			if !ok {
				return fmt.Errorf("field %s must be a string enum value", key)
			}
			if !contains(spec.EnumValues, str) {
				return fmt.Errorf("field %s must be one of %v, got %q", key, spec.EnumValues, str)
			}
		}
	}
	return nil
}

func contains(values []string, target string) bool {
	for _, v := range values {
		if v == target {
			return true
		}
	}
	return false
}

// routeByLabel is the Consumer from dimension 5, code that can trust a
// validated value without any further defensive parsing.
func routeByLabel(raw map[string]interface{}) (string, error) {
	schema := classificationSchema()
	if err := Validate(raw, schema); err != nil {
		return "", fmt.Errorf("rejected before reaching consumer, %w", err)
	}
	switch raw["label"].(string) {
	case "spam":
		return "spam-quarantine-queue", nil
	case "legitimate":
		return "inbox", nil
	default:
		return "manual-review-queue", nil
	}
}

func main() {
	validResponse := map[string]interface{}{
		"label":           "spam",
		"confidence_band": "high",
	}
	queue, err := routeByLabel(validResponse)
	if err != nil {
		panic(err)
	}
	fmt.Printf("valid response routed to, %s\n", queue)

	// A model that invented a label close to, but not a member of, the
	// closed enum, the near-miss failure named in dimension 2.
	invalidResponse := map[string]interface{}{
		"label":           "probably_spam",
		"confidence_band": "high",
	}
	if _, err := routeByLabel(invalidResponse); err != nil {
		fmt.Printf("invalid response correctly rejected, %v\n", err)
	}
}
```

Every sample above was run, not only syntax-checked. The Python script
executes the demo function on import and its assert statements pass,
printing the extracted vendor, total, currency, and a call count of two. The
Go program compiles clean and, run directly, prints a successful routing
decision followed by the correctly rejected near-miss label. The TypeScript
sample type-checks under strict mode and, transpiled and run under Node,
prints the out-of-range rejection followed by the successful routing
decision for the corrected ticket.
