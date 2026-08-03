---
name: Function Calling
slug: function-calling
family: 17-ai-agentic
category: Agentic
aliases: [Tool Calling, Tool Use, Structured Tool Invocation]
first_described: "Schick, Dwivedi-Yu, Dessi, Raileanu, Lomeli, Zettlemoyer, Cancedda, Scialom 2023 (Toolformer, academic precursor); productized as vendor APIs later the same year"
maturity: canonical
related: [react-prompting, orchestrator-worker, plan-execute, retrieval-augmented-generation, chain-of-thought]
incompatible_with: []
verified: 2026-08-03
---

# Function Calling

## 1. Name, aliases, and lineage

Three names circulate for the same underlying mechanism, and a reader moving
between vendor documentation runs into all three without warning. OpenAI's
developer documentation calls it function calling, describing it as the
model returning "a special kind of response" that names one of the functions
the caller made available and supplies arguments for it, rather than the
model executing anything itself (OpenAI, "Function calling", developer
platform documentation, https://developers.openai.com/api/docs/guides/function-calling,
verified 2026-08-03). Anthropic calls the identical mechanism tool use, with
the model emitting a `tool_use` content block and the caller's code returning
a matching `tool_result` block on the next turn (Anthropic, "Tool use with
Claude", https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview,
verified 2026-08-03). Google's Gemini documentation uses function calling
again, structured around a `FunctionDeclaration` that follows a subset of the
OpenAPI schema (Google, "Function calling with the Gemini API",
https://ai.google.dev/gemini-api/docs/function-calling, verified 2026-08-03).
This entry treats function calling as the canonical name because it is the
term that appears in the widest set of vendor and academic writing, and
treats tool use and tool calling as aliases for the same mechanism rather
than as a distinct pattern.

The mechanism has an academic precursor that predates any vendor product.
Timo Schick and coauthors at Meta AI published Toolformer, a language model
trained to decide for itself when to insert a call to a calculator, a search
engine, a calendar, or a machine translation system into its own generated
text, and to condition its next tokens on the returned result. The paper was
submitted to arXiv as `2302.04761` on 9 February 2023 (Timo Schick, Jane
Dwivedi-Yu, Roberto Dessi, Roberta Raileanu, Maria Lomeli, Luke Zettlemoyer,
Nicola Cancedda, Thomas Scialom, "Toolformer. Language Models Can Teach
Themselves to Use Tools", arXiv `2302.04761`, https://arxiv.org/abs/2302.04761,
verified 2026-08-03). Toolformer trained the calling behavior into the model
weights through self-supervised fine-tuning on examples the model generated
and filtered for itself. The vendor mechanism this entry describes takes a
different, cheaper path to the same behavior. The tool schemas are supplied
at inference time as part of the request, and the calling behavior comes from
instruction tuning the base model to recognize when a supplied schema matches
the request, not from training a model against one fixed toolset. Toolformer
proved the model-decides-when-to-call idea could work at all. The vendor
mechanism made it a request-time API property that any caller can attach a
new tool to without retraining anything.

A second, closely related research thread names the opposite failure mode.
Shishir Patil and coauthors at UC Berkeley published Gorilla in May 2023,
documenting that general-purpose language models "hallucinate the wrong
usage of an API call" when asked to invoke a large, real API surface from a
description alone, and fine-tuned a model retrieval-augmented against live
API documentation to cut that failure rate (Shishir G. Patil, Tianjun Zhang,
Xin Wang, Joseph E. Gonzalez, "Gorilla. Large Language Model Connected with
Massive APIs", arXiv `2305.15334`, https://arxiv.org/abs/2305.15334, verified
2026-08-03, submitted 24 May 2023). Gorilla's research group went on to
maintain the Berkeley Function-Calling Leaderboard, a benchmark that scores
model tool-calling accuracy across single, multi-turn, and multi-step call
scenarios and is the closest thing the field has to a shared cross-vendor
scorecard for the pattern (UC Berkeley Gorilla project, "Berkeley
Function-Calling Leaderboard", https://gorilla.cs.berkeley.edu/leaderboard.html,
verified 2026-08-03). The naming history is worth carrying forward, because a
reader who only knows the name function calling from OpenAI's API and reads
Anthropic's tool use documentation without knowing it is the same idea, or
who reads Toolformer expecting the vendor API and finds a fine-tuning paper
instead, loses time reconciling three descriptions of one mechanism.

## 2. Problem and context

A language model generates text by predicting the next token from everything
that came before it in its context window. That is the entirety of what
inference does. A model has no built in way to look up today's exchange
rate, to read a row from a production database, to send an email, or to run
a calculation it cannot do reliably in its own arithmetic. Left to itself,
the model either states plainly that it cannot do the thing, which is honest
but not useful when the caller needed the answer, or it produces a plausible
sounding number or fact from its training data, which is confident and
frequently wrong, because the model's knowledge is frozen at training time
and its arithmetic is approximate by construction.

The situation reads like this in a real system. A support assistant is asked
"what is the status of order 48213". The order status lives in a database row
that changes by the minute, and no amount of prompting will make the model's
frozen weights aware of it. Before function calling existed, the practical
answer was either to inject the row into the prompt on every single turn,
which means the caller has to guess in advance which rows the conversation
will need and pay to include all of them whether they are used or not, or to
parse the model's free text output looking for an intent like "order lookup"
and then run a lookup outside the model entirely, discarding the model's own
judgment about when a lookup is warranted. Neither approach lets the model
itself decide, mid conversation, that a particular fact needs fetching, name
which fact, and receive the answer back into its own reasoning before it
finishes replying.

The context that makes function calling the right tool has three parts,
mirrored across every vendor implementation surveyed for this entry. First,
the caller can describe a capability as a small set of named, typed
arguments, the shape a JSON Schema object naturally expresses, rather than as
free form natural language. Second, the decision of whether and when to
invoke that capability benefits from being made by the model reading the
actual user request, rather than by a fixed rule written in advance,
because the same conversation might or might not need the lookup depending
on what the person actually asked. Third, the caller, not the model, must
remain the only party that executes anything with a real side effect,
because the model's output is untrusted structured data until the calling
application validates and runs it. Outside that context the mechanism adds a
round trip and a large amount of accounting for no return, as dimension 4
sets out.

## 3. Forces

- **Structure versus latitude.** Favored toward structure. The model's
  latitude to answer in prose is deliberately narrowed to a JSON object that
  matches a declared schema, which is exactly what makes the output usable by
  a program without a natural-language parser standing between the model and
  the caller's code.
- **Latency.** Sacrificed for anything beyond a single call. Every tool
  invocation costs a full additional model turn, because the model must see
  the result before it can continue, so a chain of three sequential lookups
  costs three round trips of model latency on top of the time the tools
  themselves take.
- **Token cost and context budget.** Sacrificed steadily as the toolset
  grows. Every declared tool's name, description, and schema is counted as
  input tokens on every single request that includes it, whether the model
  calls that tool or not. Anthropic's own pricing documentation lists a fixed
  system prompt overhead added purely for having any tools attached at all,
  separate from the schema tokens themselves, ranging from roughly 260 to
  around 700 tokens depending on the model and whether tool choice is
  restricted (Anthropic, "Tool use with Claude", pricing section,
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview,
  verified 2026-08-03). A toolset of a hundred schemas is a real, recurring
  line item on every request, whether or not any of the hundred gets used.
- **Reliability.** Favored relative to free-text parsing, sacrificed
  relative to a hand written rule engine. A model trained specifically on
  schema-constrained tool output is far more likely to produce a
  syntactically valid call than a model asked to write a plain-text action
  line in prose and have that string regex-parsed afterward, which is the
  pre-function-calling ReAct style this pattern displaced for the calling
  step (see dimension 13). It is not perfectly reliable against a
  hand-authored deterministic branch, because the choice of whether to call
  at all is still a probabilistic decision the model makes.
- **Security surface.** Sacrificed the moment a tool has any side effect
  beyond a read. The model's decision to call a tool, and the argument
  values it fills in, are influenced by whatever text sits in its context,
  including text the model read rather than text the user typed. That opens
  the confused-deputy attack surface covered in full in dimension 17.
- **Operability.** Favored, when the caller instruments it, because every
  call and its result are structured events with a name and a payload,
  unlike a free-text answer that only a human or another model call can
  interpret after the fact.
- **Portability across vendors.** Sacrificed in the classical form. Each
  vendor's request and response shape for tool calls differs at the field
  level, `input_schema` versus `parameters`, `tool_use` versus a
  `function_call` part, `tool_result` versus a role-tagged message, so code
  written against one vendor's function-calling shape does not run against
  another without an adapter. The Model Context Protocol exists in large
  part to give that adapter a standard shape, discussed in dimension 13.

No pattern here gives up nothing. The structure the caller gains over free
text is paid for in latency, in a standing token bill proportional to the
size of the declared toolset, and in a new class of security exposure that a
plain text-only completion never carried.

## 4. Applicability and non-applicability

Reach for function calling when the following hold together.

- The task needs a real external effect, a lookup, a write, a calculation
  beyond what the model does reliably in its own weights, or an action
  against a system the model has no other way to reach.
- The decision to trigger that effect genuinely depends on the content of
  the conversation, so a fixed, always-run pre-fetch would either run the
  lookup when it was not needed or miss cases a rule writer did not
  anticipate.
- The capability's inputs can be described as a small, typed, mostly flat
  set of named arguments. A capability that needs paragraphs of free-form
  natural-language configuration to describe correctly is fighting the
  schema rather than being served by it.
- The caller can and will validate every returned argument against the
  schema and run the call under its own privilege boundary, never under an
  assumption that a schema-shaped object is a safe object.
- The number of distinct tools the model must choose between at any one
  time stays small enough that the schema list itself does not become the
  dominant cost or the dominant source of wrong selections, or the caller is
  willing to add retrieval-gated tool discovery once it does not (dimension
  8).

Do NOT reach for function calling in the following cases, and the reason
behind each matters more than the rule itself.

- **The action must always happen, regardless of what the model decides.**
  If a step runs on every single turn unconditionally, the model's judgment
  is not buying anything, and a plain deterministic call in the calling code
  before the model is ever invoked removes both the round trip and the
  standing per-request schema cost. This is the single most common misuse
  this entry's failure modes describe, and dimension 14 gives the exact
  refactor out of it.
- **The goal is a shaped JSON answer with no external effect.** When the
  point is only to force the model's reply into a fixed object shape,
  structured output or JSON mode, which most of the same vendors ship as a
  separate feature, gets the schema-conformance benefit with no tool choice
  negotiation, no execution step, and none of the security surface, because
  nothing is ever run against the returned object beyond parsing it.
- **The toolset is enormous and mostly irrelevant to any single request.**
  Declaring thousands of schemas on every call both burns the standing token
  overhead on almost every one of them for nothing and measurably degrades
  the accuracy of the model's selection among the ones it does need, which is
  exactly the motivation behind the retrieval-gated tool discovery variant
  in dimension 8. A flat declared toolset in the low tens is comfortable; a
  flat declared toolset in the thousands is a defect waiting for a bug
  report.
- **Correctness is a compliance or safety requirement that cannot tolerate a
  probabilistic decision to call or not call.** A financial approval step, a
  medication dosage calculation, or anything where a missed or malformed
  call has a cost the business is unwilling to accept even occasionally
  belongs behind a deterministic rule engine that the model can inform but
  must not gate. Function calling makes calling likely and well formed. It
  does not make calling certain.
- **Latency budget forbids a round trip.** A sub-second, single-turn
  completion path with no external need should stay a single model call. A
  tool declaration attached in case it is needed adds token cost to every
  request in that path for a capability the vast majority of requests never
  touch, which is a straightforward cost regression for a benefit almost
  nobody gets.
- **The interaction is genuinely conversational and creative, with no
  external fact or action involved.** Writing assistance, brainstorming, and
  free-form dialogue have no schema-shaped decision to make, and attaching
  tools to that path is pure overhead.

## 5. Structure

Six participants, named by the role each plays rather than by any one
vendor's field names.

- **Model.** The party that reads the conversation plus every declared Tool
  Declaration and decides, on each turn, whether to answer in ordinary text
  or to emit one or more calls. The model never executes anything itself.
  Its entire output is a piece of structured data naming a tool and filling
  in arguments for it.
- **Tool Declaration.** A schema, conventionally JSON Schema, carrying a
  unique name, a natural-language description the model reads to decide
  relevance, and a typed `properties` object with a `required` list. The
  declaration is the only thing the model ever sees of the underlying
  capability. It never sees the implementation.
- **Tool Choice.** A request-level setting the caller controls that narrows
  or widens the model's latitude to call. Common settings across vendors are
  an automatic mode where the model decides freely, a forced mode where a
  specific named tool must be called, a required mode where some tool must
  be called but the model still picks which, and a disabled mode where no
  tool may be called on that turn.
- **Tool Call.** The model's structured output for a single invocation, a
  name plus a filled-in arguments object plus an identifier the caller uses
  to correlate the eventual result back to this specific call. A single
  model turn may emit more than one Tool Call when parallel calling is
  enabled, discussed in dimension 8.
- **Executor.** The calling application's own code. It owns every step
  after the model emits a Tool Call, validating the arguments against the
  declared schema, running the underlying capability under its own
  privilege, and never trusting the returned identity of the tool or the
  shape of its arguments without checking them first.
- **Tool Result.** A structured value the Executor sends back into the
  conversation on the next request, carrying the same correlation identifier
  as the Tool Call it answers, the outcome, and an explicit success or
  failure marker so the model can tell the two apart and, on failure, adjust
  its next attempt rather than treat a rejected call as if it had succeeded.

The External System the Executor ultimately talks to, a database, an HTTP
API, a shell, a calendar, is outside the pattern's own structure. It is
whatever the Executor decides to call once it has validated arguments, and
the pattern's contract with the model ends the moment the Executor takes over.

## 6. ASCII structure diagram

```
+----------------------+   declares (name,     +------------------------+
|      Application      |   description,        |    Tool Declaration    |
|  owns the conversation | --------------------> |  name / description /  |
|  and the Executor      |                       |  JSON Schema params    |
+-----------+------------+                       +------------------------+
            |
            | sends prompt + declared tools + tool_choice
            v
   +--------------------+
   |       Model         |
   |  decides call or     |
   |  plain text reply    |
   +---------+-----------+
             |
             | emits a Tool Call (name, arguments, call id)
             v
   +--------------------+     validates, then    +-----------------------+
   |      Executor        |   executes under its   |    External System   |
   |  (part of the same   | ----------------------> |  database, API, file, |
   |   Application)       | <---------------------- |  shell, calendar ...  |
   +---------+-----------+          raw result      +-----------------------+
             |
             | builds a Tool Result (call id, content, is_error)
             v
   +--------------------+
   |       Model         |
   |  continues, calls    |
   |  another tool, or     |
   |  answers in text      |
   +----------------------+

   The dashed accounting boundary is the Tool Call and Tool Result pair.
   Only that pair crosses between the Model and the Application. Nothing
   the Model emits is executed until the Executor decides to run it.
```

## 7. Dynamics

```
User         Application          Model            Executor       External System
 |               |                  |                  |                 |
 |-- prompt ---->|                  |                  |                 |
 |               |-- prompt + tool declarations ------>|                  |
 |               |                  |                  |                 |
 |               |                  |-- emits Tool     |                 |
 |               |                  |   Call(get_weather,               |
 |               |                  |   {location: "Munich"}) ---------->|
 |               |<-- response with Tool Call ----------|                  |
 |               |                  |                  |                 |
 |               |-- validate arguments against schema-->|                 |
 |               |                  |                  |-- run lookup -->|
 |               |                  |                  |<-- raw result --|
 |               |<-- Tool Result(call id, "18C, rain")-|                 |
 |               |                  |                  |                 |
 |               |-- prompt + Tool Result appended ---->|                  |
 |               |                  |                  |                 |
 |               |                  |-- emits final     |                 |
 |               |                  |   text answer      |                 |
 |               |<-- text answer --|                  |                 |
 |<-- reply -----|                  |                  |                 |
 |               |                  |                  |                 |
```

Two properties are easy to miss reading a single example and matter in
production. First, the Tool Call always originates from the model reading
the caller's declared tools, never from the user's raw text directly. A user
typing a question about what a tool call looks like produces a plain text
answer describing the tool, not a Tool Call, because the model is reasoning
about whether the current request needs the capability, not pattern-matching
on the tool's name appearing in the conversation. Second, when a turn emits
several Tool Calls at once under a parallel-calling mode, every one of them
needs exactly one Tool Result before the next model turn can proceed. A
caller that executes three calls, sends back two results, and drops the
third because it failed silently breaks the conversation's accounting and
the next model request is rejected or, worse, silently misinterprets the
missing result. Failure mode 7 in dimension 11 covers the exact shape of
that bug.

## 8. Implementation variants

**Automatic, multi-turn agentic loop.** The default and most common shape.
Tool choice is set to automatic, the model decides on every turn whether to
call, and the Application repeats the request-execute-append cycle until the
model produces a plain text answer instead of another call. This is the
shape ReAct-style agents run on top of, and it is the variant every
multi-step tool-using agent in production is built from.

**Forced or required single call for structured extraction.** Tool choice
is narrowed to a specific named tool, or to any-tool-must-be-called, and
the interaction is not agentic at all, it is a single request whose whole
purpose is to make the model fill in one schema reliably. This is the
correct shape for extracting a fixed set of fields from a block of text, and
it skips the auto-decide negotiation entirely because the caller already
knows a call is wanted.

**Parallel tool calls in one turn.** The model emits more than one Tool Call
in a single response when the calls are independent of each other, for
example fetching weather for two different cities in the same request. Both
OpenAI and Google document this explicitly, with Google's documentation
stating the model can "Call multiple functions at once when they are
independent" and reserving a separate compositional mode, discussed next,
for calls that must run in sequence (Google, "Function calling with the
Gemini API", https://ai.google.dev/gemini-api/docs/function-calling,
verified 2026-08-03). Anthropic's request shape offers a
`disable_parallel_tool_use` flag on its tool-choice object for callers that
want the simpler one-call-per-turn accounting instead (Anthropic, "Tool use
with Claude", https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview,
verified 2026-08-03).

**Compositional, chained calling.** Several calls run across turns where a
later call's arguments depend on an earlier call's result, for example
resolving a place name to coordinates before calling a weather lookup that
needs coordinates. Google's documentation names this pattern directly as
chaining "multiple function calls together for complex requests" (Google,
"Function calling with the Gemini API", https://ai.google.dev/gemini-api/docs/function-calling,
verified 2026-08-03). Structurally it is nothing more than the automatic
multi-turn loop running for more than one iteration, but it is worth naming
separately because the failure modes differ from a single-call turn, in
particular the runaway-loop risk in dimension 11.

**Strict, grammar-constrained schema conformance.** Some vendors offer a
stricter mode that guarantees, at the token-generation level rather than
as best effort, that a Tool Call's arguments satisfy the declared schema exactly.
OpenAI's strict mode requires every property to be listed as required, with
optional fields expressed as a nullable type instead of an absent key, and
`additionalProperties` set to false on every object in the schema, in
exchange for a call that the API states will reliably "adhere to the
function schema, instead of being best effort" (OpenAI, "Function calling",
https://developers.openai.com/api/docs/guides/function-calling, verified
2026-08-03). This trades a small amount of schema-authoring flexibility for
removing an entire class of the argument-validation failures in dimension 11.

**Server-executed versus client-executed tools.** A genuinely different
execution locus rather than a different calling shape. Anthropic
distinguishes tools your own code executes, called client tools, from
server tools such as web search or code execution, which "run on
Anthropic's infrastructure" and return their result in the same response
without the caller ever handling execution (Anthropic, "Tool use with
Claude", https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview,
verified 2026-08-03). The Tool Call and Tool Result shapes look identical
from the outside, but a server tool never crosses into the caller's own
process, which changes the security calculus in dimension 17 substantially.

**Retrieval-gated tool discovery for large toolsets.** Rather than declaring
every available tool on every request, the caller exposes a small,
always-present meta-tool that lets the model search or browse a large
catalog and load only the schemas relevant to the current request. Anthropic
ships this as a dedicated tool search capability, described as letting a
caller "work with thousands of tools by discovering and loading them on
demand" (Anthropic, "Tool use with Claude", tool search tool card,
https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview,
verified 2026-08-03). This is the direct answer to the non-applicability
case in dimension 4 about enormous toolsets, and it turns an otherwise
linear per-request token cost into a bounded one.

**Fine-tuned native format versus prompt-simulated calling.** Not every
model that appears to support tool calling has a dedicated training format
for it. The Berkeley Function-Calling Leaderboard scores models separately
by whether they use a native, purpose-trained function-calling interface or
a prompt-based approach where the model is instructed to emit a specific
text format that the caller then parses itself, noting format sensitivity as
a distinct scored dimension for the latter group (UC Berkeley Gorilla
project, "Berkeley Function-Calling Leaderboard",
https://gorilla.cs.berkeley.edu/leaderboard.html, verified 2026-08-03). The
prompt-simulated form is structurally closer to the original ReAct free-text
parsing this pattern displaced than to the trained, schema-native form the
major vendors ship, and it inherits more of ReAct's parsing fragility as a
result.

## 9. Known production uses

**OpenAI API, function calling.** The mechanism ships as a first-class
parameter on OpenAI's chat and responses endpoints, with the platform
documentation stating plainly that the model "does not execute functions
itself" and that the caller's application must run the corresponding logic
and return the result. OpenAI's documentation also states that on models
beginning with GPT-5, functions "can be called in parallel when built-in
tools are also available", with a `parallel_tool_calls` flag to restrict
that to zero or one call per turn (OpenAI, "Function calling", developer
platform documentation, https://developers.openai.com/api/docs/guides/function-calling,
verified 2026-08-03).

**Anthropic Claude API, tool use.** Every Claude model from the Messages API
onward accepts a `tools` array of JSON-Schema-shaped `input_schema`
declarations, and Claude's response carries `tool_use` content blocks the
caller executes and answers with `tool_result` blocks. Anthropic documents
the exact per-model token overhead the `tools` parameter adds to every
request, a concrete production cost line rather than a theoretical one
(Anthropic, "Tool use with Claude", https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview,
verified 2026-08-03).

**Google Gemini API, function calling.** Gemini's `FunctionDeclaration`
objects use a documented subset of the OpenAPI schema, and the API supports
parallel calling of independent functions in one turn plus compositional,
multi-step chaining of dependent calls across turns, both described directly
in Google's own documentation (Google, "Function calling with the Gemini
API", https://ai.google.dev/gemini-api/docs/function-calling, verified
2026-08-03).

**Model Context Protocol tool servers.** MCP, published and maintained by
Anthropic with broad cross-vendor adoption, standardizes the caller side of
this pattern into a `tools/list` discovery call and a `tools/call`
invocation call that any MCP-speaking host, including Claude Desktop and
Claude Code, issues against any MCP server regardless of which vendor built
the server. The specification requires every tool's `inputSchema` to be "a
valid JSON Schema object" and documents the full request and response
envelope for both discovery and invocation (Model Context Protocol
specification, "Tools", https://modelcontextprotocol.io/docs/concepts/tools,
verified 2026-08-03). MCP does not replace function calling. It standardizes
the plumbing a host application uses to turn a remote server's tool catalog
into the same Tool Declaration and Tool Call shapes this entry describes,
so a single host implementation can call tools from any compliant server
without a custom adapter per server.

**Berkeley Function-Calling Leaderboard as the cross-vendor evaluation
benchmark.** Beyond any one vendor's own product, the open-source model
community has converged on BFCL as the shared benchmark for certifying that
a model's function-calling fine-tune actually produces well formed,
correctly selected calls across single-turn, multi-turn, and multi-step
scenarios, maintained by the same UC Berkeley group behind Gorilla (UC
Berkeley Gorilla project, "Berkeley Function-Calling Leaderboard",
https://gorilla.cs.berkeley.edu/leaderboard.html, verified 2026-08-03). Its
existence as an independent, widely cited scorecard is itself evidence that
the mechanism has moved from a single vendor's product feature to an
industry-wide interface every serious model provider is expected to support.

## 10. Consequences

Positive.

- A model gains the ability to act on live, external, or computed
  information without that information ever needing to sit in its training
  data or be pasted into every prompt whether it is needed or not.
- The interface between the model's judgment and the caller's code is
  structured data with a name and typed fields, not free text a second
  parser has to interpret, which removes an entire class of brittle
  regex-based intent parsing that predates the pattern.
- New capabilities are added by declaring a new schema, not by retraining
  or fine-tuning anything, so the set of things a deployed model can do
  grows at the speed the caller writes new tool declarations.
- Execution stays entirely inside the caller's own code, so every safety,
  validation, rate-limiting, and auditing control the caller already applies
  to its own API surface applies to a Tool Call the same way it applies to
  any other inbound request, because from the Executor's point of view a
  Tool Call is another request to validate, nothing more.
- Call and result pairs are a natural place to hang observability, because
  every action the model takes is now a discrete, named, structured event
  rather than a sentence buried in free text.

Negative.

- Every declared tool costs input tokens on every request that includes it,
  whether it is called or not, and the fixed per-request tool-use overhead
  documented by at least one major vendor is paid purely for having any
  tools attached, independent of how many.
- A multi-step task now costs one full model round trip per step, which is
  latency a single, larger completion would not have paid.
- The model's decision to call, and what arguments it fills in, are
  probabilistic outputs conditioned on its full context, including any text
  it read that the caller did not author, which is the root of the security
  concerns in dimension 17 and cannot be fixed purely by better prompting.
- A large toolset degrades both cost and call-selection accuracy at once, so
  the pattern does not scale for free as the number of available
  capabilities grows, and requires the retrieval-gated variant from
  dimension 8 once it does not.
- Vendor request and response shapes differ at the field level, so code
  built directly against one vendor's calling convention does not run
  against another without an adapter layer, which the Model Context Protocol
  exists to reduce but which the underlying model-facing mechanism still
  has, one layer down.

## 11. Failure modes and misuse

**Hallucinated or absent tool.** Symptom. The model's response names a tool
that was never declared in the current request, or invents an argument key
that appears nowhere in the schema. Cause. The tool the request actually
needs is missing from the declared set, or the model confuses two
similarly-named or similarly-described tools it has seen in unrelated
contexts. Fix. Treat an unknown-tool response as a normal Tool Result error,
never a crash, so the model receives a message specific enough to adjust to
on the next turn, which is exactly the guidance the Model Context Protocol
specification gives for tool execution errors, distinguishing them from
protocol errors precisely because execution errors give the model specific,
usable feedback it "can use to self-correct and retry with adjusted
parameters" (Model Context Protocol specification, "Tools", error handling
section, https://modelcontextprotocol.io/docs/concepts/tools, verified
2026-08-03).

**Missing-argument fabrication.** Symptom. A tool that requires a location
argument gets called with a plausible-sounding but never-supplied city name
when the user's actual message never named one. Cause. The model infers a
reasonable-looking default rather than asking the user for the missing
value, a behavior Anthropic's own documentation warns is model-dependent and
"not guaranteed, especially for more ambiguous prompts and for less capable
models" (Anthropic, "Tool use with Claude", required-parameters accordion,
https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview,
verified 2026-08-03). Fix. Mark the parameter required with a description
precise enough to discourage guessing, and add an explicit system
instruction telling the model to ask rather than infer when a required value
is absent from the conversation, and validate the value's plausibility in
the Executor rather than trusting it at face value.

**Confused deputy through untrusted context.** Symptom. A tool with a real
side effect, sending a message, deleting a record, executes an action
nobody explicitly asked for, traceable back to text the model read from a
fetched document, a previous tool's result, or another party's message
rather than from the user's own request. Cause. The model treats content it
merely read as if it were an instruction, and no human confirmation step
stood between the model's decision and execution. Fix. Follow the Model
Context Protocol's explicit guidance that applications "SHOULD prompt for
user confirmation on sensitive operations" and "insert clear visual
indicators when tools are invoked" (Model Context Protocol specification,
"Tools", user interaction model, https://modelcontextprotocol.io/docs/concepts/tools,
verified 2026-08-03), and gate any tool with a real side effect behind an
explicit approval step rather than automatic execution.

**Runaway or repeated-call loop.** Symptom. An agentic loop calls the same
tool with identical or near-identical arguments turn after turn, burning
tokens and time without making progress toward an answer, until an external
budget or step cap finally stops it. Cause. A tool that consistently returns
an error the model cannot interpret as a reason to change strategy, or a
loop with no cap and no repeated-call detection at all. Fix. Cap the number
of loop iterations, detect an identical call repeated back to back and
refuse to run it a second time, and make sure every Tool Result the Executor
returns on failure is specific enough for the model to try something
different rather than the same call again.

**Schema drift from the real backend.** Symptom. A tool executes without a
validation error, because its arguments genuinely satisfy the declared
schema, but the underlying system's behavior for those arguments changed
since the schema was authored, so the model reports a confidently wrong
result as fact. Cause. The JSON Schema is a contract with the model only. It
is never automatically synchronized with the real API, database, or service
it wraps. Fix. Generate the schema from the authoritative API specification
where one exists rather than hand-authoring it from memory, and add a
contract test that fails when the underlying system's real interface
changes shape.

**Token-cost blowup from an oversized standing toolset.** Symptom. Cost and
latency degrade steadily as more tools are declared, even for requests that
end up using only one or two of them, and the effect compounds because the
full schema list is resent on every single turn of every conversation. Cause.
The complete toolset is declared on every request regardless of relevance,
paying its full token cost each time. Fix. Move to retrieval-gated tool
discovery once the toolset passes a size where most requests use a small
fraction of it, per the variant in dimension 8, so the standing cost stops
growing linearly with the size of the catalog.

**Dropped or mismatched Tool Result in a parallel batch.** Symptom. The
model's next turn errors or behaves as if a call it made was never
answered, in a conversation that used parallel tool calling. Cause. The
Executor ran several Tool Calls concurrently, one of them failed, and the
caller's code dropped that one result instead of returning an explicit error
Tool Result for it, so the conversation state no longer has a matching
answer for every call the model made in that turn. Fix. Always return
exactly one Tool Result per Tool Call, including a clearly marked error
result for a call that failed, never a silently missing one, matched by the
correlation identifier every vendor's calling shape carries for this exact
purpose.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3.

| Force | Function calling (native) | Free-text ReAct-style parsing | Structured output / JSON mode | Deterministic rule engine / RPA | Plan-and-execute upfront planning |
|---|---|---|---|---|---|
| Reliability of the call's syntax | High, purpose-trained toward the schema | Low, depends on a regex catching an exact text format | High, schema is enforced or grammar-constrained | Perfect, no model involved in the branch | Depends on the underlying call mechanism, usually function calling per step |
| Latency per decision | One model round trip per call | One model round trip per action, plus parsing time | One round trip, no execution loop at all | No model latency for the decision itself | Front-loaded, one planning call, then one call per step |
| Adding a new capability | Declare a new schema, no retraining | Add a new prompt example and hope the format is followed | Change the target schema | Write new deterministic branch code | Declare a new schema the plan can reference |
| Standing token cost | Grows with toolset size, paid every request | Grows with prompt examples, paid every request | Fixed, one schema, no tool-choice negotiation | None | Plan step plus per-tool cost of function calling |
| Ability to handle ambiguous or novel requests | Good, model judges relevance from a description | Fair, same judgment but fragile parsing on the way out | Poor, no decision step, always produces the shape | Poor, only what the rule author anticipated | Good, planning step reasons about novelty first |
| Security surface for actions with side effects | Real, confused-deputy risk from untrusted context | Same risk, plus injection into the parsed text itself | None, nothing is executed | Low, only what the deterministic code allows | Same as function calling, inherited per step |
| Determinism of whether the action happens | Probabilistic, model decides | Probabilistic, model decides | Not applicable, no action | Certain | Probabilistic at the planning step, then per call |
| Debuggability | Good, structured call and result events | Poor, requires re-parsing free text to see what happened | Good, one shaped object to inspect | Excellent, ordinary code path | Good, plan is itself inspectable before execution |

Reading of the table. Function calling wins over free-text parsing on every
row except standing token cost, where the two are close, because a trained,
schema-constrained output format is strictly more reliable to parse than a
hoped-for text convention. It loses to a deterministic rule engine on
determinism and security whenever the underlying action genuinely does not
need judgment, which is exactly dimension 4's non-applicability case. It
loses to structured output whenever nothing needs to be executed at all. It
composes with, rather than competes against, plan-and-execute, because a
plan's individual steps are usually themselves ordinary function calls,
discussed further in dimension 13.

## 13. Related and incompatible patterns

- **ReAct.** The historical predecessor for the calling step. ReAct's
  original Thought-Action-Observation loop expressed the Action step as
  free text the caller's code had to parse with a regular expression against
  a hoped-for format. Function calling replaces that one step with a
  trained, schema-constrained output while keeping the same overall loop
  shape, reason, act, observe, repeat. A ReAct-style agent built today
  almost always implements its Action step as a function call rather than a
  parsed text action, which is why this entry treats the two as composing
  tightly rather than as competitors.
- **Model Context Protocol.** Composes above it, one layer removed from the
  model. MCP standardizes how a host application discovers and invokes tools
  that live on a separate server process, using its own `tools/list` and
  `tools/call` methods, and then maps that server's tools into the ordinary
  Tool Declaration and Tool Call shapes described in this entry before ever
  presenting them to the model. The model still only ever sees a Tool
  Declaration and emits a Tool Call in the vendor's own format. MCP moves
  where the tool's implementation lives, out of the calling application and
  into an independent server, without changing the model-facing mechanism at
  all.
- **Orchestrator-Worker.** Composes cleanly. A worker in that pattern is
  frequently exposed to the orchestrator as a callable tool with its own
  schema, so an orchestrator's single decision of which worker handles a
  subtask is, mechanically, a function call choosing among several declared
  workers.
- **Plan and Execute.** Complementary rather than competing, as the trade-off
  table notes. Plan-and-execute separates the reasoning about what steps are
  needed from the reasoning about how to fill in each step's arguments, which
  reduces the amount of full-context reasoning the model redoes on every
  single step compared to a pure automatic multi-turn function-calling loop
  with no upfront plan. Each planned step is very often itself executed as
  one function call.
- **Retrieval-Augmented Generation.** A retrieval lookup can be exposed as
  an ordinary callable tool, a document search, rather than run
  unconditionally on every turn. That reframing, retrieval as one tool among
  several rather than a fixed pipeline stage, is what the agentic and
  corrective RAG variants in this same family build on, and it is a direct
  instance of function calling's core value, letting the model decide when a
  capability is actually needed rather than paying for it on every turn.
- **Chain of Thought.** Sits underneath it, not beside it. The reasoning
  that decides which tool to call, and what values to fill into its
  arguments, is itself a chain-of-thought step, whether the caller can see
  that reasoning in the response or not. A model that reasons poorly reasons
  poorly about tool selection the same way it reasons poorly about anything
  else.
- **Structured Outputs / JSON mode.** A sibling mechanism sharing the same
  JSON-Schema-constrained generation machinery underneath, but with no
  execution step and no tool-choice negotiation at all, described directly
  as the correct substitute in dimension 4 for any case where nothing
  actually needs to run.
- **Service Locator.** Loosely analogous and worth flagging as a caution
  rather than a composition. A model choosing a tool by name at request time
  resembles a locator resolving a named service at runtime rather than a
  caller wiring in a dependency explicitly ahead of time. The analogy turns
  into a genuine risk in exactly the way it does for the software pattern.
  a tool whose description or provenance is not trusted, invoked implicitly
  because the model matched it by name, hides exactly the dependency the
  Executor needs visibility into to validate safely, which is the same
  hidden-dependency objection the Factory Method entry in this repository
  raises against Service Locator in its own dimension 13.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently only produces free text.

1. Find one crisp capability the model currently either refuses to help
   with, or fakes an answer for, a live lookup, a calculation the model gets
   wrong often enough to matter, or an action a person currently has to do
   by hand after reading the model's reply.
2. Write that capability's JSON Schema against the real, underlying system
   it wraps, with the smallest set of properties that actually distinguishes
   one valid call from another, and mark every property that is not
   genuinely optional as required.
3. Wire exactly one tool with tool choice set to automatic, and run the
   round trip by hand first, a single request, a single Tool Call, a single
   Tool Result, a single follow-up request, before opening any loop to the
   model unattended.
4. Add argument validation against the schema in the Executor before any
   handler code runs, and return a Tool Result error rather than raising an
   exception the caller has to remember to catch, so a malformed call is a
   normal, inspectable event rather than a crash.
5. Open the multi-turn loop, with a hard iteration cap and a repeated
   identical call detector installed from the first day it runs unattended,
   per failure mode 4.
6. Once more than a handful of tools exist and most requests only need one
   or two of them, move from a flat declared toolset to retrieval-gated tool
   discovery, per the variant in dimension 8, before the standing token cost
   and the selection-accuracy degradation from an oversized toolset become
   visible in production.

Removing the pattern once it stops earning its place. The signal is one of
two shapes, the tool is called on effectively every single turn with no
real variance in whether it is needed, or the tool never does anything a
plain formatting step could not do.

1. Confirm from call logs that the tool in question fires on nearly every
   request regardless of content, or that its handler has no external
   dependency and no branch, only a fixed transform of its arguments.
2. If the tool is unconditional, move its underlying call into the
   Application's own code, run before the model is invoked at all, and
   inject the result directly into the prompt as context instead of
   declaring it as a tool. This removes both the round trip and its share of
   the standing token overhead in one step.
3. If the tool never had a real side effect and existed only to shape the
   model's output, replace it with structured output or JSON mode, which
   drops the tool-choice negotiation and the Tool Call and Tool Result
   accounting entirely.
4. Remove the now-unused Tool Declaration from every request that carried
   it, and confirm no remaining code path still branches on that tool's
   name before deleting its Executor handler.

## 15. Testing and verification

Easier because of the pattern.

- The Executor's argument-validation and dispatch code is entirely
  decoupled from the model itself by the Tool Call and Tool Result boundary,
  so it can be exercised with hand-constructed Tool Call payloads and no
  live model call at all, which is both faster and free of the model's
  turn-to-turn variance.
- A schema-conformance test can assert, once, that a declared tool's
  `inputSchema` actually matches the real API or function it wraps, catching
  the schema-drift failure from dimension 11 in a fast unit test rather than
  waiting for a wrong production answer to surface it.
- Recorded Tool Call payloads from real traffic become golden replay
  fixtures for the deterministic Executor path, letting a caller re-run a
  known-tricky argument set through validation and dispatch on every change
  without paying for another model call.

Harder because of the pattern.

- Whether the model decides to call the right tool at all, given a natural
  language prompt, is a probabilistic property of the model itself, and it
  shifts across model versions and prompt changes in ways a single fixed
  assertion cannot capture. This needs an evaluation set scored for a
  pass-rate threshold rather than a single test that must always pass, the
  same category of evaluation the Berkeley Function-Calling Leaderboard runs
  at model-provider scale.
- A full multi-turn agentic loop is difficult to snapshot-test end to end,
  because a Tool Result that comes from a real external system, a network
  call, a database read, can legitimately differ run to run even when the
  Executor code itself is correct.
- Mocking the model's own tool-selection behavior in a unit test risks
  testing the mock's assumptions about when the model calls a tool rather
  than the real model's actual behavior, which drifts silently the moment
  the underlying model is updated.

Techniques that apply.

- **Golden-transcript replay for the Executor.** Store a fixed set of Tool
  Call payloads, run them through validation and dispatch, and assert the
  Tool Result each produces, entirely without a model in the loop.
- **Property-based fuzzing of argument validation.** Generate malformed,
  missing, extra, and boundary-value arguments against a tool's schema and
  assert the validator rejects every one of them with a clear, specific
  Tool Result error rather than either crashing or silently accepting bad
  input.
- **Forced tool-choice tests for extraction paths.** Any flow that relies on
  a forced or required call, dimension 8's structured-extraction variant, is
  tested by forcing that same tool choice in the test, removing the
  model's decide-to-call variance from exactly the paths where the caller
  already made that decision for it.
- **A small held-out evaluation set scored against the live model.** For the
  genuinely automatic, model-decides paths, run a fixed set of prompts
  against the real model on every change to the prompt template or the
  declared toolset, and track the pass rate over time rather than expecting
  a single deterministic green or red result.

## 16. Observability signals

What to record. Every Tool Call, its tool name, its filled-in arguments, and
a correlation identifier tying it to the conversation and to the eventual
Tool Result, alongside a per-tool counter of how often each declared tool is
actually invoked, since a declared tool that is never called is a candidate
for removal per dimension 14, purely wasted token cost otherwise. A counter
of how often each call's arguments fail schema validation, broken out by
tool name, points to the argument-hallucination failure from dimension 11
early. A histogram of iteration count per multi-turn loop or session,
because the shape of that distribution is the earliest signal of a runaway
or repeated-call loop, dimension 11's fourth failure mode. Wherever the
model vendor reports it, the token overhead specifically attributable to the
declared `tools` parameter, tracked as its own line, so a growing toolset's
cost is visible before it appears as an unexplained bill increase.

A healthy instance on a dashboard. The per-tool call-rate distribution
matches the mix of requests actually being handled, and shifts only when a
deploy or an intentional toolset change explains the shift. Validation-error
rate is low and flat. Iteration count is clustered at one or two calls with
a short, thin tail. Tool-schema token overhead is flat over time unless a
tool was deliberately added or removed.

A failing instance. A declared tool with a call count near zero over a
reasonably long window, quietly costing its schema's tokens on every request for
no return. A validation-error rate that jumps after an unrelated deploy,
pointing at schema drift from the real backend rather than at the model's
behavior changing. The identical-call-repeated signal climbing, the direct
symptom of a runaway loop. A sudden shift in the ratio of turns that call a
tool versus turns that answer in plain text with no prompt or toolset
change on the caller's side, which usually means the underlying model was
updated and its calling threshold moved with it.

## 17. Security and privacy implications

Function calling is one of the few patterns in this family that is loud
about security rather than quiet, precisely because it is the first point
in most LLM systems where a probabilistic, context-influenced decision turns
into a real side effect.

**Confused-deputy risk from untrusted context.** The model's decision to
call a tool, and the arguments it fills in, are conditioned on everything in
its context window, not only on the user's own words. Text a fetched
document contains, a previous tool's result, or another party's message can
read as an instruction to the model and steer it into calling a tool nobody
who owns the conversation actually asked for. This is the primary new attack
surface function calling opens compared with plain text generation, and it
is exactly why the Model Context Protocol specification requires human
confirmation for sensitive operations and instructs implementations to
"validate tool results before passing to LLM" (Model Context Protocol
specification, "Tools", security considerations,
https://modelcontextprotocol.io/docs/concepts/tools, verified 2026-08-03).

**Ambient privilege of the Executor, not the model.** Because the calling
application, never the model, actually runs the call, every tool inherits
whatever privilege the Executor process already holds, filesystem access,
network reach, stored credentials. A schema that declares a narrow
read-one-file capability provides no protection at all if the handler
behind it is implemented with a broad filesystem handle and adversarial path
arguments are not validated by the Executor itself. The schema constrains
the shape of the request. It does not constrain what the handler is
actually allowed to do with it.

**Tool descriptions and results as attacker-influenceable content.** When
tool declarations come from a source outside the caller's own trusted code,
an MCP server built by a third party for example, the tool's name,
description, and any annotations attached to it are themselves content an
attacker could shape, which is exactly why the Model Context Protocol
specification states clients "MUST consider tool annotations to be
untrusted unless they come from trusted servers" (Model Context Protocol
specification, "Tools", data types section,
https://modelcontextprotocol.io/docs/concepts/tools, verified 2026-08-03).
Sensitive argument values deserve the same caution about where they end up
visible. The specification separately warns servers against mirroring a
password, token, or personal identifier into an HTTP header, since header
values are readable by any network intermediary between the client and the
server (Model Context Protocol specification, "Tools", x-mcp-header section,
https://modelcontextprotocol.io/docs/concepts/tools, verified 2026-08-03).

**Different blast radius for server-executed versus client-executed
tools.** The two variants from dimension 8 look identical from the model's
side of the wire, the same shape of Tool Call, the same shape of Tool
Result, but they carry materially different consequences if abused. A
server-executed tool runs on the vendor's own infrastructure with the
vendor's own sandboxing and never touches the caller's process at all. A
client-executed tool runs inside the caller's own application with the
caller's own privileges. A code review asking whether a given tool is safe
needs to know which of the two it is looking at before the question can be
answered at all.

On privacy specifically the pattern is neutral in its shape, with one
concrete practical point. Arguments and results routinely carry the same
personal data the surrounding conversation already carries, a location, an
account identifier, a search string, and because dimension 16 recommends
logging them as structured fields, they become more machine-queryable after
the fact than the equivalent detail buried in free-form prose would have
been, not less. The same retention and access rules the caller already
applies to the conversation transcript apply to the Tool Call and Tool
Result log the same way, never a looser one, purely because the data is now
easier to search.

## Code examples

Three languages, each showing a different genuinely idiomatic angle of the
same Executor-side dispatcher, since the model-facing wire format is nearly
identical across vendors and the interesting engineering lives entirely on
the caller's side of the boundary. TypeScript shows the core validate,
dispatch, and bounded-loop shape from dimension 5 and failure mode 4. Python
shows the forced single-call structured-extraction variant from dimension 8.
Go shows the parallel-call variant from dimension 8 and its one-result-per-call
discipline from failure mode 7, using goroutines, the idiomatic Go shape for
running several independent calls at once. Java and Kotlin are omitted for
space, not because the pattern translates poorly to either.

### TypeScript

```typescript
type JSONType = "string" | "number" | "boolean";

interface ParamSpec {
  type: JSONType;
  description: string;
}

interface JSONSchema {
  type: "object";
  properties: Record<string, ParamSpec>;
  required: string[];
}

interface ToolDeclaration {
  name: string;
  description: string;
  inputSchema: JSONSchema;
}

interface ToolUseBlock {
  id: string;
  name: string;
  input: Record<string, unknown>;
}

interface ToolResultBlock {
  toolUseId: string;
  content: string;
  isError: boolean;
}

function validateArguments(
  schema: JSONSchema,
  input: Record<string, unknown>
): string | null {
  for (const key of schema.required) {
    if (!(key in input)) return `missing required argument: ${key}`;
  }
  for (const key of Object.keys(input)) {
    const spec = schema.properties[key];
    if (!spec) return `unexpected argument: ${key}`;
    if (typeof input[key] !== spec.type) {
      return `argument ${key} expected ${spec.type}, got ${typeof input[key]}`;
    }
  }
  return null;
}

type ToolHandler = (input: Record<string, unknown>) => string;

class ToolRegistry {
  private readonly tools = new Map<
    string,
    { decl: ToolDeclaration; handler: ToolHandler }
  >();

  register(decl: ToolDeclaration, handler: ToolHandler): void {
    this.tools.set(decl.name, { decl, handler });
  }

  declarations(): ToolDeclaration[] {
    return [...this.tools.values()].map((t) => t.decl);
  }

  // The Executor owns every side effect. Arguments are validated against
  // the declared schema before a single line of handler code runs.
  execute(call: ToolUseBlock): ToolResultBlock {
    const entry = this.tools.get(call.name);
    if (!entry) {
      return { toolUseId: call.id, content: `unknown tool: ${call.name}`, isError: true };
    }
    const problem = validateArguments(entry.decl.inputSchema, call.input);
    if (problem) {
      return { toolUseId: call.id, content: problem, isError: true };
    }
    try {
      return { toolUseId: call.id, content: entry.handler(call.input), isError: false };
    } catch (err) {
      return { toolUseId: call.id, content: String(err), isError: true };
    }
  }
}

// A bounded agentic loop. An identical call repeated back to back stops
// the loop rather than spinning, per the runaway-loop failure mode.
function runLoop(
  registry: ToolRegistry,
  calls: ToolUseBlock[],
  maxSteps = 4
): ToolResultBlock[] {
  const results: ToolResultBlock[] = [];
  let lastSignature = "";
  for (const call of calls.slice(0, maxSteps)) {
    const signature = `${call.name}:${JSON.stringify(call.input)}`;
    if (signature === lastSignature) {
      results.push({
        toolUseId: call.id,
        content: "refused: identical call repeated, likely a runaway loop",
        isError: true,
      });
      break;
    }
    lastSignature = signature;
    results.push(registry.execute(call));
  }
  return results;
}

const weatherSchema: JSONSchema = {
  type: "object",
  properties: {
    location: { type: "string", description: "City and country" },
  },
  required: ["location"],
};

const registry = new ToolRegistry();
registry.register(
  {
    name: "get_weather",
    description: "Return the current weather for a named location.",
    inputSchema: weatherSchema,
  },
  (input) => `18C, light rain in ${input.location as string}`
);

const modelTurns: ToolUseBlock[] = [
  { id: "call_1", name: "get_weather", input: { location: "Munich, DE" } },
  { id: "call_2", name: "get_weather", input: {} },
];

for (const result of runLoop(registry, modelTurns)) {
  console.log(result.toolUseId, result.isError ? "ERROR" : "OK", result.content);
}
```

### Python

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ParamSpec:
    type: type
    description: str


@dataclass(frozen=True)
class ToolDeclaration:
    name: str
    description: str
    properties: dict[str, ParamSpec]
    required: tuple[str, ...]


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    content: str
    is_error: bool


def validate(decl: ToolDeclaration, arguments: dict[str, Any]) -> str | None:
    for key in decl.required:
        if key not in arguments:
            return f"missing required argument: {key}"
    for key, value in arguments.items():
        spec = decl.properties.get(key)
        if spec is None:
            return f"unexpected argument: {key}"
        if not isinstance(value, spec.type):
            return f"argument {key} expected {spec.type.__name__}, got {type(value).__name__}"
    return None


class ToolRegistry:
    def __init__(self) -> None:
        self._declarations: dict[str, ToolDeclaration] = {}
        self._handlers: dict[str, Callable[[dict[str, Any]], str]] = {}

    def register(self, decl: ToolDeclaration, handler: Callable[[dict[str, Any]], str]) -> None:
        self._declarations[decl.name] = decl
        self._handlers[decl.name] = handler

    def execute(self, call: ToolCall) -> ToolResult:
        decl = self._declarations.get(call.name)
        if decl is None:
            return ToolResult(call.call_id, f"unknown tool: {call.name}", True)
        problem = validate(decl, call.arguments)
        if problem is not None:
            return ToolResult(call.call_id, problem, True)
        handler = self._handlers[call.name]
        try:
            return ToolResult(call.call_id, handler(call.arguments), False)
        except Exception as exc:  # a tool's own failure becomes a result, never a crash
            return ToolResult(call.call_id, str(exc), True)


def forced_extraction(registry: ToolRegistry, decl_name: str, arguments: dict[str, Any]) -> ToolResult:
    """The forced tool_choice variant from dimension 8. The model is not
    asked whether to call the tool, only how to fill its arguments, so this
    path serves structured extraction rather than an agentic loop."""
    return registry.execute(ToolCall("forced_1", decl_name, arguments))


if __name__ == "__main__":
    weather = ToolDeclaration(
        name="get_weather",
        description="Return the current weather for a named location.",
        properties={"location": ParamSpec(str, "City and country")},
        required=("location",),
    )
    registry = ToolRegistry()
    registry.register(weather, lambda args: f"18C, light rain in {args['location']}")

    ok = registry.execute(ToolCall("call_1", "get_weather", {"location": "Munich, DE"}))
    missing = registry.execute(ToolCall("call_2", "get_weather", {}))
    forced = forced_extraction(registry, "get_weather", {"location": "Berlin, DE"})

    for result in (ok, missing, forced):
        status = "ERROR" if result.is_error else "OK"
        print(result.call_id, status, result.content)
```

### Go

```go
package main

import (
	"fmt"
	"reflect"
	"sort"
	"sync"
)

type ParamSpec struct {
	Kind        reflect.Kind
	Description string
}

type ToolDeclaration struct {
	Name        string
	Description string
	Properties  map[string]ParamSpec
	Required    []string
}

type ToolCall struct {
	ID        string
	Name      string
	Arguments map[string]any
}

type ToolResult struct {
	ToolUseID string
	Content   string
	IsError   bool
}

type ToolHandler func(map[string]any) (string, error)

func validate(decl ToolDeclaration, args map[string]any) error {
	for _, key := range decl.Required {
		if _, ok := args[key]; !ok {
			return fmt.Errorf("missing required argument: %s", key)
		}
	}
	for key, value := range args {
		spec, ok := decl.Properties[key]
		if !ok {
			return fmt.Errorf("unexpected argument: %s", key)
		}
		if reflect.TypeOf(value).Kind() != spec.Kind {
			return fmt.Errorf("argument %s expected %s, got %s", key, spec.Kind, reflect.TypeOf(value).Kind())
		}
	}
	return nil
}

type ToolRegistry struct {
	declarations map[string]ToolDeclaration
	handlers     map[string]ToolHandler
}

func NewToolRegistry() *ToolRegistry {
	return &ToolRegistry{
		declarations: make(map[string]ToolDeclaration),
		handlers:     make(map[string]ToolHandler),
	}
}

func (r *ToolRegistry) Register(decl ToolDeclaration, handler ToolHandler) {
	r.declarations[decl.Name] = decl
	r.handlers[decl.Name] = handler
}

func (r *ToolRegistry) Execute(call ToolCall) ToolResult {
	decl, ok := r.declarations[call.Name]
	if !ok {
		return ToolResult{call.ID, fmt.Sprintf("unknown tool: %s", call.Name), true}
	}
	if err := validate(decl, call.Arguments); err != nil {
		return ToolResult{call.ID, err.Error(), true}
	}
	content, err := r.handlers[call.Name](call.Arguments)
	if err != nil {
		return ToolResult{call.ID, err.Error(), true}
	}
	return ToolResult{call.ID, content, false}
}

// RunParallel executes several tool calls from one model turn concurrently.
// Every call gets exactly one result, in call order, so a caller that
// appends results to the conversation never drops one, per the
// dropped-parallel-result failure mode.
func (r *ToolRegistry) RunParallel(calls []ToolCall) []ToolResult {
	results := make([]ToolResult, len(calls))
	var wg sync.WaitGroup
	for i, call := range calls {
		wg.Add(1)
		go func(i int, call ToolCall) {
			defer wg.Done()
			results[i] = r.Execute(call)
		}(i, call)
	}
	wg.Wait()
	return results
}

func main() {
	registry := NewToolRegistry()
	registry.Register(
		ToolDeclaration{
			Name:        "get_weather",
			Description: "Return the current weather for a named location.",
			Properties:  map[string]ParamSpec{"location": {reflect.String, "City and country"}},
			Required:    []string{"location"},
		},
		func(args map[string]any) (string, error) {
			return fmt.Sprintf("18C, light rain in %s", args["location"]), nil
		},
	)

	calls := []ToolCall{
		{ID: "call_1", Name: "get_weather", Arguments: map[string]any{"location": "Munich, DE"}},
		{ID: "call_2", Name: "get_weather", Arguments: map[string]any{}},
		{ID: "call_3", Name: "get_weather", Arguments: map[string]any{"location": "Berlin, DE"}},
	}

	results := registry.RunParallel(calls)
	sort.Slice(results, func(i, j int) bool { return results[i].ToolUseID < results[j].ToolUseID })
	for _, r := range results {
		status := "OK"
		if r.IsError {
			status = "ERROR"
		}
		fmt.Println(r.ToolUseID, status, r.Content)
	}
}
```

## 18. References

1. OpenAI. "Function calling", developer platform documentation.
   https://developers.openai.com/api/docs/guides/function-calling
   Verified 2026-08-03. Source for the model-does-not-execute description,
   the parallel tool call behavior, and the strict-mode schema-conformance
   requirements described in dimensions 1, 8, and 9. Redirected from
   platform.openai.com/docs/guides/function-calling at fetch time.
2. Anthropic. "Tool use with Claude", API documentation.
   https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
   Verified 2026-08-03. Source for the tool_use and tool_result round
   trip, the client-tool versus server-tool distinction, the
   disable_parallel_tool_use option, the per-model token overhead table,
   the required-parameter inference caveat, and the tool search capability
   description used across dimensions 3, 5, 8, 9, 11, and 16. Redirected
   from docs.claude.com/en/docs/agents-and-tools/tool-use/overview at fetch
   time.
3. Google. "Function calling with the Gemini API", Gemini API documentation.
   https://ai.google.dev/gemini-api/docs/function-calling
   Verified 2026-08-03. Source for the FunctionDeclaration and OpenAPI
   schema subset, the parallel function calling behavior, and the
   compositional multi-step calling description in dimensions 8 and 9.
4. Model Context Protocol. "Tools", protocol specification.
   https://modelcontextprotocol.io/docs/concepts/tools
   Verified 2026-08-03. Source for the tools/list and tools/call
   methods, the JSON Schema requirement on inputSchema, the
   protocol-error versus tool-execution-error distinction, the
   human-confirmation and untrusted-annotation security guidance, and the
   x-mcp-header sensitive-value warning used across dimensions 9, 11, and
   17.
5. Timo Schick, Jane Dwivedi-Yu, Roberto Dessi, Roberta Raileanu, Maria
   Lomeli, Luke Zettlemoyer, Nicola Cancedda, Thomas Scialom. "Toolformer.
   Language Models Can Teach Themselves to Use Tools." arXiv `2302.04761`,
   submitted 9 February 2023. https://arxiv.org/abs/2302.04761
   Verified 2026-08-03. Source for the self-supervised, fine-tuning-based
   academic precursor described in dimension 1.
6. Shishir G. Patil, Tianjun Zhang, Xin Wang, Joseph E. Gonzalez. "Gorilla.
   Large Language Model Connected with Massive APIs." arXiv `2305.15334`,
   submitted 24 May 2023. https://arxiv.org/abs/2305.15334
   Verified 2026-08-03. Source for the documented hallucinated-API-call
   failure motivating dimension 1 and dimension 11's first failure mode.
7. UC Berkeley Gorilla project. "Berkeley Function-Calling Leaderboard."
   https://gorilla.cs.berkeley.edu/leaderboard.html
   Verified 2026-08-03. Source for the cross-vendor evaluation benchmark and
   the native-versus-prompt-based scoring distinction described in
   dimensions 1, 8, 9, and 15.
