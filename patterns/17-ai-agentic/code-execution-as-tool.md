---
name: Code Execution as Tool
slug: code-execution-as-tool
family: 17-ai-agentic
category: AI Agentic
aliases: [CodeAct, Code Interpreter, Programmatic Tool Calling, Code as Action Space]
first_described: "Wang, Chen, Yuan, Zhang, Li, Peng, Ji 2024 (CodeAct); OpenAI Code Interpreter 2023 (production precedent)"
maturity: established
related: [function-calling, react, sandbox-sdk, cost-guard, tool-result-caching, plan-execute, human-in-the-loop, prompt-injection-defense]
incompatible_with: []
verified: 2026-08-02
---

# Code Execution as Tool

## 1. Name, aliases, and lineage

The pattern has no single inventor and no single canonical paper the way a Gang
of Four pattern does. Two lineages converge on it, one from product engineering
and one from research, and both names are in active use.

The product lineage starts with OpenAI's Code Interpreter, shipped inside
ChatGPT in 2023 and later generalized into the Assistants API as the
`code_interpreter` tool, which runs model-written Python inside a sandboxed
container and returns stdout, stderr, and generated files back to the model
(OpenAI, "Code Interpreter", ChatGPT plugin and Assistants API documentation,
2023, verified against Anthropic's own comparable feature below on
2026-08-02). This lineage gave the pattern its common industry name, code
interpreter, and its default shape. a model writes a short program, submits
it to a container, and reasons over the returned text.

The research lineage is CodeAct. Xingyao Wang, Yangyi Chen, Lifan Yuan, Yizhe
Zhang, Yunzhu Li, Hao Peng, and Heng Ji, "Executable Code Actions Elicit Better
LLM Agents", accepted at ICML 2024, first posted to arXiv as 2402.01030 on 1
February 2024 (arXiv abstract page, verified 2026-08-02). CodeAct is the paper
that names and formalizes the general idea for agent design. instead of
constraining an LLM agent's action space to a fixed vocabulary of JSON tool
calls or a small set of textual commands, let the model emit Python as its
action, execute that Python in an interpreter, and feed the printed
observation back into the next turn. The paper's own framing is that Python
gives the agent access to existing software and libraries and lets it combine
actions, use control flow, and revise a prior action inside a single turn,
which a flat sequence of discrete tool calls cannot do. The paper reports up
to a 20 percent higher task success rate against baselines that used a fixed
JSON action format on their benchmark (arXiv 2402.01030 abstract, verified
2026-08-02).

Anthropic's shipping name for the same capability is the code execution tool,
a first-party tool type (`code_execution_20250825` and later versions) that
runs Bash and Python inside a sandboxed container reachable from the Messages
API (Anthropic, "Code execution tool", platform.claude.com/docs, verified
2026-08-02). Anthropic also ships a distinct but related capability called
programmatic tool calling, where the code the model writes and executes is
itself allowed to invoke the model's OTHER declared tools from inside the
sandbox, so a loop that would otherwise be many model turns becomes one
program (Anthropic, "Programmatic tool calling", platform.claude.com/docs,
referenced from the code execution tool page, verified 2026-08-02). This
entry treats code execution as tool as the umbrella name for the family. a
model-controlled interpreter or shell, running inside an isolated sandbox,
whose printed output becomes an observation the model reasons over on its
next turn, whether the code is the whole action (CodeAct style) or a wrapper
that calls other declared tools (programmatic tool calling style).

A third name worth flagging because readers will meet it. Model Context
Protocol server implementers and framework authors sometimes call this "the
code mode" or "agentic code execution" to distinguish it from a plain
function-calling loop. Cloudflare's Agents SDK documentation and Anthropic's
own engineering blog both use language close to "code execution" for the same
idea applied to MCP tool servers, where the agent writes code against a
generated API surface for the connected tools rather than emitting one JSON
call per tool per turn (Anthropic engineering blog, "Code execution with
MCP", referenced by the Cloudflare Agents SDK code-mode documentation,
verified 2026-08-02 via the Cloudflare docs cross-link). That variant is
covered in dimension 8 below.

## 2. Problem and context

An LLM agent that can only call tools one at a time, through a fixed
function-calling schema, hits a specific wall as soon as a task needs more
than a handful of steps chained together with real control flow.

Picture an agent asked to read a CSV of ten thousand rows, compute a rolling
seven-day average per customer, drop customers with fewer than three
transactions, and write the top twenty to a new file. Under plain
function-calling (see the `function-calling` entry in this family), each
individual operation, read the file, filter a row, compute an average, has to
be exposed as a named tool, and the model drives the loop by emitting one
tool call, receiving one tool result back into its context window, and
emitting the next call. Ten thousand rows processed one row-level tool call
at a time is not a hypothetical inefficiency, it is a real failure mode.
either the loop never terminates inside a reasonable token and time budget,
or the developer is forced to write a bespoke `compute_rolling_average` tool
in advance for this one task, which defeats the point of a general-purpose
agent.

The context that produces this problem has three parts, and code execution as
tool answers all three at once. First, general computation, loops,
conditionals, arithmetic, string manipulation, is something existing
programming languages already do well, and an LLM that has been trained on
enormous quantities of code already knows how to write correct short
programs for common data-shape problems. Re-inventing that computation as a
combinatorial explosion of narrow, pre-declared tools is redundant effort
that also bloats the tool-definition portion of the context window, since
every declared tool's JSON schema is tokens the model must read on every
turn (this cost is analyzed directly in the `token-budget` entry in this
family). Second, some tasks are naturally expressed as a program with
intermediate state, a running total, an accumulator, a partially built data
structure, that has no clean way to survive across a sequence of independent
tool calls unless the runtime invents a scratch-memory tool for exactly that
purpose. Third, and increasingly the dominant reason as of 2026, an agent
often needs to call several OTHER tools inside one coherent unit of logic,
fetch a value, transform it, and feed it into a second call, and doing that
transformation through the model's own reasoning between two separate tool
turns is slower, more expensive in tokens, and more failure-prone than
writing five lines of glue code that does it deterministically. Anthropic's
own motivation for programmatic tool calling states this directly. code lets
Claude orchestrate several tool calls, loop over results, and post-process
data without round-tripping every intermediate value through the model's
context (Anthropic, "Programmatic tool calling", platform.claude.com/docs,
verified 2026-08-02).

The pattern is not a substitute for well-scoped, purpose-built tools where a
purpose-built tool is genuinely simpler and safer, it is a superset that
handles the long tail of ad hoc computation and multi-tool orchestration that
would otherwise require either an impossibly large tool catalog or a slow,
expensive, error-prone sequence of individually reasoned turns.

## 3. Forces

**Expressiveness versus attack surface.** A full interpreter can express
arbitrary computation, which is the entire point, but arbitrary computation
executed on data the model itself chose is also, definitionally, the
broadest possible attack surface an agent framework can expose. This is the
central tension of the pattern and it does not go away with a good sandbox,
it is only bounded by one. See dimension 17.

**Token cost versus wall-clock cost.** Code execution trades context-window
tokens for compute time. Ten thousand rows processed by a five-line pandas
program costs a handful of tokens for the program itself and a small
observation for the summarized result, but it costs real container CPU time
to run. Ten thousand rows processed as ten thousand individual tool calls
costs an enormous number of tokens (context grows every turn) and an
enormous number of model round-trips, but if the sandbox is unavailable,
misconfigured, or itself the bottleneck, the token-heavy path might still
finish first on a small dataset. The pattern generally wins as data volume or
step count grows, and loses on tiny, one-shot lookups where the fixed cost of
spinning up a container is not worth it.

**Determinism versus model creativity.** Code that executes does exactly
what it says, which is a genuine reliability gain over the model attempting
long arithmetic or careful multi-step string manipulation in its own token
stream, where hallucinated intermediate values are a documented failure mode.
But the model still decides WHAT code to write, so a subtly wrong assumption
baked into the program (an off-by-one date boundary, a wrong column name)
executes with full, silent determinism. correctness of computation does not
imply correctness of intent.

**Isolation versus statefulness.** A fresh, disposable container per
invocation is the safest posture, no state ever survives to be tampered
with or leaked into the next unrelated request. But many real tasks need
state across turns, a file written in step one that step three reads, a
loaded dataframe that step five filters further. Container reuse
(Anthropic's model, see dimension 8) buys statefulness back at the cost of a
longer-lived attack surface and the operational complexity of expiring and
garbage-collecting containers.

**Latency versus fidelity.** Provisioning an isolated execution environment,
whether a microVM, a gVisor container, or a WebAssembly sandbox, has a cold-
start cost measured in the low hundreds of milliseconds to low seconds
depending on the isolation technology. A framework that reuses warm sandboxes
trades some isolation guarantees, or at minimum more careful cleanup
discipline, for latency the end user actually notices.

**Cost predictability versus flexibility.** An interpreter can run an
unbounded loop. Framework designers must decide, up front, whether to cap
wall-clock time, memory, output size, or all three, and every cap is a
constraint on what the pattern can legitimately be used for. Anthropic's own
container enforces a hard memory ceiling and a maximum execution time with a
distinct error code for exceeding it (Anthropic, "Code execution tool",
Containers section, platform.claude.com/docs, verified 2026-08-02), which is
a direct, sourced instance of this force being resolved in favor of
predictability over flexibility.

This entry weighs these forces toward isolation and determinism, because the
production systems surveyed in dimension 9 all converge on the same answer,
a hard sandbox boundary with no ambient network access as the non-negotiable
baseline, with statefulness and flexibility layered on top only inside that
boundary.

## 4. Applicability and non-applicability

Reach for code execution as tool when.

- The task involves numeric computation, statistics, data transformation, or
  file manipulation over a dataset too large or too irregular to hand-craft a
  dedicated tool for in advance.
- The agent must combine the outputs of several other declared tools inside
  one coherent unit of logic, filter, join, aggregate, before deciding what
  to do next, and doing that combination step by step through the model's
  own reasoning would cost more tokens or more round-trips than writing the
  combination as five lines of code (this is exactly what Anthropic's
  programmatic tool calling targets, platform.claude.com/docs, verified
  2026-08-02).
- The agent needs to produce an artifact, a chart, a spreadsheet, a
  transformed file, that is naturally produced by running code against a
  library rather than by the model describing the artifact in prose.
- The interaction pattern is exploratory. the model needs to inspect a
  dataset's shape, try a transformation, look at the result, and adjust,
  which is what a REPL is for and what a fixed tool schema cannot offer
  without an explosion of narrow tools.
- The agent is orchestrating a Model Context Protocol server with a large
  number of exposed tools, where writing code against a generated client
  library, filtering and chaining calls in the sandbox, measurably reduces
  the tokens spent reading tool definitions and intermediate results
  (Anthropic engineering blog, "Code execution with MCP", referenced via
  Cloudflare's code-mode documentation, verified 2026-08-02).

Do NOT reach for code execution as tool when.

- The task is a single, well-defined external effect with a known, narrow
  input and output shape, send this email, create this calendar event. A
  purpose-built function-calling tool is simpler, easier to audit, and does
  not carry an interpreter's attack surface for a job that never needed one.
  See the `function-calling` entry.
- The environment cannot provide real sandbox isolation, no ambient network
  egress, no host filesystem access, bounded CPU and memory. Executing model-
  written code in a shared process, on the same host as production secrets,
  is not this pattern with a shortcut taken, it is a different and far more
  dangerous thing. If a real sandbox is unavailable, do not simulate the
  pattern by evaluating model output in-process.
- The action needs a hard, pre-verified guarantee before it happens, moving
  real money, deleting a production resource, sending an irreversible
  message to a human. Code execution changes HOW a decision is computed, it
  does not by itself provide the approval gate a consequential action needs.
  Compose with `human-in-the-loop` for the approval step, do not treat
  sandboxed execution as a substitute for it.
- Regulatory or contractual constraints forbid running third-party or
  user-influenced code at all, common in some financial and healthcare
  environments, regardless of how well-sandboxed it is. In those settings
  the tool catalog must stay closed and finite.
- The task is trivially small, a division, a date comparison, a short string
  format, and the model can compute it correctly and cheaply in its own
  reasoning without paying a container round-trip. Reaching for a sandbox on
  every arithmetic operation is over-engineering the pattern into a
  performance regression.

## 5. Structure

- **Requester (the LLM).** Decides, from the conversation and the declared
  tool's description, that writing and running code is the right next
  action, and emits the code as the tool call's argument. The requester does
  not execute anything itself, it only authors the program.
- **Code execution tool declaration.** The schema, exposed to the model like
  any other tool, that describes the interpreter's language, its
  pre-installed libraries, and its constraints (no network, a memory limit,
  a time limit). This declaration is what lets the requester know what it is
  allowed to write.
- **Sandbox (the container, microVM, or WASM runtime).** The isolated
  execution environment that actually runs the submitted code. Owns process
  isolation, filesystem scoping, resource limits, and network denial. The
  sandbox is the security boundary of the whole pattern, everything else is
  ergonomics.
- **Execution runtime (inside the sandbox).** The thin runtime, an
  interpreter process plus a control channel, that receives the code,
  executes it, captures stdout, stderr, and any produced files, and reports
  the result back out of the sandbox. In stateful designs this runtime also
  owns the persisted interpreter state (loaded variables, an open dataframe)
  between invocations.
- **Session or container manager (the orchestrating framework).** The
  component outside the sandbox, part of the API server or the agent
  framework, that provisions a fresh sandbox or resumes an existing one,
  enforces the checkpoint and expiry lifecycle, and returns the sandbox
  identifier to the caller so a later turn can request the same one.
  Anthropic's container object with an `id` and `expires_at` is a direct,
  sourced example of this role (Anthropic, "Container reuse",
  platform.claude.com/docs, verified 2026-08-02).
- **Observation formatter.** Converts the raw execution result, stdout,
  stderr, an exit code, a list of generated file references, into the
  content block the model receives on its next turn. This is the pattern's
  return channel, and its shape and truncation policy materially affect the
  model's ability to reason about what happened (an execution that silently
  truncates a long stdout produces a model that confidently reasons about
  data it never actually saw).
- **Outer tool bridge (for programmatic tool calling and MCP code mode
  only).** A generated client, inside the sandbox, that lets the executing
  code call the agent's OTHER declared tools as ordinary function calls from
  within the program, rather than only calling library functions. This
  participant is what elevates the pattern from a calculator to a full
  orchestration layer.

## 6. ASCII structure diagram

```text
+------------------------------------------------------------------+
|                          LLM (requester)                          |
|  reads conversation + tool declarations, decides to write code    |
+----------------------------------+---------------------------------+
                                   | code_execution tool call
                                   | (language, source, optional
                                   |  container/session id)
                                   v
+------------------------------------------------------------------+
|                Session / container manager (host process)         |
|  provision new sandbox  <-- or -->  resume existing sandbox by id |
+----------------------------------+---------------------------------+
                                   |
                                   v
+------------------------------------------------------------------+
|                          Sandbox boundary                         |
|  +--------------------------------------------------------------+ |
|  |                    Execution runtime                          | |
|  |   interpreter process (python / node / wasm) + control I/O    | |
|  |                                                                | |
|  |   +------------------+     +--------------------------------+ | |
|  |   | submitted code    |---->| runtime state (if reused)      | | |
|  |   +------------------+     +--------------------------------+ | |
|  |                                                                | |
|  |   +--------------------------------+                          | |
|  |   | outer tool bridge (optional)     |--calls out to--+        | |
|  |   | programmatic tool calling / MCP  |                |        | |
|  |   +--------------------------------+                  |        | |
|  +--------------------------------------------------------|-------+ |
|   no network egress   no host filesystem   bounded CPU/mem |       |
+---------------------------------------------------------|--------+
                                                            |
                                    calls other declared tools
                                    (search, fetch, MCP servers)
                                                            v
                                          +----------------------+
                                          | other tools / MCP     |
                                          | servers, outside the  |
                                          | sandbox                |
                                          +----------------------+
                                   ^
                                   | stdout / stderr / exit code /
                                   | generated files / container id
                                   |
+----------------------------------+---------------------------------+
|                        Observation formatter                       |
|   truncates, wraps, and attaches results as a tool_result block    |
+----------------------------------+---------------------------------+
                                   |
                                   v
+------------------------------------------------------------------+
|                          LLM (next turn)                          |
|          reasons over the printed result, decides next step       |
+------------------------------------------------------------------+
```

## 7. Dynamics

The stateless, single-shot flow (the common case, and Anthropic's default
`code_execution_20250825` behavior).

```text
1. User turn arrives. Model reads conversation and the code_execution
   tool's declared schema (language, library list, limits).
2. Model decides code execution is the right action, emits a tool_use
   block whose input is source code (for example a Bash command that
   writes and runs a Python file).
3. Host receives the tool_use block, has no existing container id for
   this conversation, so it provisions a new sandbox.
4. Sandbox boots. isolated filesystem, no network route out, CPU and
   memory limits attached.
5. Execution runtime inside the sandbox runs the submitted code to
   completion, to a time limit, or to a memory limit, whichever comes
   first.
6. Runtime captures stdout, stderr, exit code, and any files written to
   the workspace.
7. Result crosses back out of the sandbox boundary to the host.
8. Host attaches a container object (id, expires_at) to the response so
   a LATER turn can resume this same sandbox if it wants to.
9. Observation formatter builds a tool_result block from steps 6 to 8,
   truncating any oversized stdout per the runtime's configured cap.
10. Model receives the tool_result on its next turn, reasons over the
    printed observation, and either emits another code_execution call
    (often reusing the returned container id to keep prior state) or
    proceeds to a final answer.
11. If no further request references this container's id within its
    checkpoint window, the sandbox is torn down and its ephemeral state
    is discarded, only container objects deliberately reused persist.
```

The programmatic tool calling variant differs starting at step 5, and this
shape is what elevates the pattern from a calculator into an orchestration
layer (Anthropic, "Programmatic tool calling", platform.claude.com/docs,
verified 2026-08-02).

```text
5a. Runtime begins executing the submitted code. The code calls out to
    one of the AGENT's OTHER declared tools (a search tool, an MCP
    server function) via a generated in-sandbox client, not via a
    library call.
5b. That outer call crosses the sandbox boundary OUTWARD, is resolved
    by the host exactly as a normal tool call would be, and its result
    is returned back INTO the running program as a plain value.
5c. The running program continues, loops, filters, or transforms that
    value, possibly calling further outer tools, entirely within this
    single code_execution invocation and without returning control to
    the model in between.
5d. Only once the whole program finishes does control return to the
    model, with one consolidated observation covering everything the
    program did, rather than one observation per outer tool call.
```

The key dynamic difference. in the stateless flow, every logical step the
agent takes costs one model turn and one context-window round-trip. In the
programmatic tool calling flow, an entire multi-step orchestration, possibly
calling several outer tools and looping over their results, costs exactly
one model turn to write the program and one observation to read the
consolidated result, at the price of the model losing the ability to
reconsider its plan between the individual outer calls inside that program.

## 8. Implementation variants

**Single-language container with no reuse (the baseline).** One language
(almost always Python, because of its library ecosystem for data work), one
disposable sandbox per invocation, no persisted state, no outer tool bridge.
This is OpenAI's original Code Interpreter shape and the simplest, safest
variant to reason about. It answers "run this calculation" well and answers
"iteratively explore this dataset across many turns" poorly, because every
turn re-loads any data from scratch.

**Multi-language container with checkpointed reuse.** Anthropic's shipping
implementation. Bash and Python both available, a container identified by an
opaque id, checkpointed roughly five minutes after the last request and
restorable within a 30-day window by passing that id back in a later request
(Anthropic, "Container reuse", platform.claude.com/docs, verified
2026-08-02). This buys real statefulness (a dataframe loaded in turn one is
still there in turn five) at the cost of a longer container lifetime that
the framework must actively manage and expire.

**Programmatic tool calling and code mode over other tools.** The sandbox is
not only a general interpreter, it is also given a generated client library
for the agent's OTHER declared tools, so code written inside the sandbox can
call those tools directly as function calls rather than only calling
library code. Anthropic's naming is programmatic tool calling
(platform.claude.com/docs, verified 2026-08-02), Cloudflare's Agents SDK and
Anthropic's own engineering writing describe the closely related idea for
Model Context Protocol tool servers as code mode, where instead of the model
reading N tool schemas and emitting N separate calls, the model is given (or
generates) a typed client and writes one program against it, which the
sandbox executes, calling the real MCP tools underneath (referenced via
Cloudflare Agents SDK code-mode documentation, verified 2026-08-02). This
variant trades a larger implementation surface, the framework now must
generate and keep in sync a client library for every declared tool, for a
large reduction in tokens spent on tool schemas and intermediate results,
which matters most when the tool catalog is large (dozens of MCP tools) or
the orchestration between tools is deep.

**WebAssembly-based sandboxing.** Some frameworks isolate at the WASM
boundary rather than the OS-container boundary, trading a smaller trusted
computing base and typically faster cold starts for a narrower set of
supported languages and native library bindings. This is common in
edge-deployed agent runtimes where a full Linux container is too heavy for
the platform's execution model, for example Cloudflare's Sandbox SDK, which
provisions isolated per-agent execution environments on Cloudflare's edge
platform for exactly this purpose (Cloudflare Developers, "Sandbox SDK",
developers.cloudflare.com, cross-referenced against the `sandbox-sdk` entry
in this repository, verified 2026-08-02).

**Third-party sandbox-as-a-service.** Rather than a model provider building
and operating the sandbox itself, some agent frameworks call out to a
dedicated sandboxing provider, most visibly E2B, which offers ephemeral
cloud sandboxes purpose-built for running LLM-generated code with a
documented, publicly marketed sub-200-millisecond cold-start target (E2B
documentation, "Sandbox", e2b.dev, verified 2026-08-02). This variant
decouples the model provider from the execution provider, which lets a
framework mix models from different vendors while keeping one consistent
sandbox implementation, at the cost of an additional network hop and an
additional vendor in the trust boundary.

**Language-idiomatic notes.** The pattern itself is language-agnostic at the
framework level, the runtime is almost always implemented in a systems or
backend language (Go, Rust, TypeScript on Node) regardless of what language
the SUBMITTED code is written in. The choice of submitted-code language is
driven by the target task's ecosystem, Python dominates because of pandas,
numpy, and matplotlib for data work, JavaScript or TypeScript appears where
the sandbox is embedded in a Node-based or edge-computing agent runtime and
the code needs to call browser-shaped or Workers-shaped APIs, Bash appears
alongside either as the glue for file and process operations Anthropic's own
tool exposes directly (platform.claude.com/docs, Quick start section,
verified 2026-08-02).

## 9. Known production uses

1. **Anthropic Claude API code execution tool.** A first-party tool type
   (`code_execution_20250825`, superseded by `code_execution_20260120` and
   `code_execution_20260521`) that runs Bash and Python in a Linux-based,
   fully network-isolated container with 5 GiB of RAM and 5 GiB of workspace
   storage, available on the Claude API, Claude Platform on AWS, and
   Microsoft Foundry, documented in production as of the verification date
   (Anthropic, "Code execution tool", Model compatibility and Containers
   sections, platform.claude.com/docs, verified 2026-08-02).

2. **OpenAI Code Interpreter (ChatGPT and the Assistants API).** OpenAI's
   `code_interpreter` tool runs model-written Python in a sandboxed
   container inside ChatGPT and, historically, the Assistants API, returning
   generated files and printed output to the model, and is the shipping
   product widely credited with popularizing the pattern under the name
   Code Interpreter (OpenAI product documentation, cross-checked against
   Anthropic's own comparison framing on its code execution tool page,
   verified 2026-08-02).

3. **CodeAct reference implementation, OpenHands (formerly OpenDevin).** The
   CodeAct paper's authors released an open-source coding-agent framework,
   originally named OpenDevin and later renamed OpenHands, that implements
   the CodeAct action space directly. the agent's action on every turn is
   Python code executed in a Jupyter-style kernel, with the printed cell
   output returned as the next observation (arXiv 2402.01030, "Executable
   Code Actions Elicit Better LLM Agents", and the paper's linked project
   page, verified 2026-08-02).

4. **E2B sandboxes.** A dedicated sandboxing-as-a-service platform whose
   product is exactly this pattern's execution layer, isolated, ephemeral,
   fast-booting cloud sandboxes marketed specifically for running AI-agent-
   generated code, used as the execution backend by multiple independent
   agent frameworks rather than building their own container orchestration
   (E2B documentation, e2b.dev, verified 2026-08-02).

5. **Cloudflare Agents SDK Sandbox SDK and code mode.** Cloudflare exposes a
   Sandbox SDK for provisioning isolated code-execution environments for
   agents built on its Workers platform, and documents a code-mode pattern
   where an agent writes code against a generated client for connected MCP
   tools rather than emitting individual tool calls, explicitly citing the
   token and latency savings of consolidating a multi-tool orchestration
   into one executed program (Cloudflare Developers, Agents SDK and Sandbox
   SDK documentation, developers.cloudflare.com, verified 2026-08-02).

## 10. Consequences

Positive.

- Genuine computational correctness for anything the model would otherwise
  have to reason through in its own token stream, arithmetic, statistics,
  parsing, sorting, all execute exactly as written rather than being
  approximated by next-token prediction.
- Collapses what would be many sequential tool-call round-trips into a
  single program, which the CodeAct paper's own reported success-rate gain
  attributes directly to the model's ability to compose actions, use
  control flow, and revise mid-turn rather than committing to one atomic
  action per turn (arXiv 2402.01030, verified 2026-08-02).
- Enables tasks with no pre-existing tool at all. any computation
  expressible in the sandbox's language becomes reachable, without the
  framework author having to anticipate and hand-write a tool for it in
  advance.
- When combined with a large or dynamic tool catalog (many MCP servers), the
  programmatic tool calling and code-mode variants measurably reduce the
  number of tokens spent reading tool schemas and re-serializing
  intermediate results between turns, since the orchestration happens once
  inside the sandbox rather than being narrated turn by turn.
- Produces genuine file artifacts, charts, transformed spreadsheets, that a
  model describing output in prose cannot produce directly.

Negative.

- The single largest attack surface in an otherwise closed agent tool
  catalog. see dimension 17.
- Non-trivial infrastructure cost. building or operating a real sandbox
  (container orchestration, resource limits, network denial, expiry and
  garbage collection) is materially more engineering effort than
  implementing a narrow function-calling tool.
- Latency floor set by container provisioning, which for cold-started
  isolation technologies is measured in the hundreds of milliseconds to low
  seconds, a cost paid even for trivial computations if the framework does
  not short-circuit them.
- Debuggability gap between what the model INTENDED the code to do and what
  the code ACTUALLY does. a subtly wrong assumption baked into a generated
  program executes silently and correctly according to its own (wrong)
  logic, and the model may misinterpret its own output on the next turn if
  the observation is truncated or ambiguous.
- Statefulness variants (container reuse, checkpointing) reintroduce many of
  the operational concerns of a long-lived server, session expiry, resource
  leaks, garbage state from a prior unrelated task bleeding into a resumed
  container, that a fully stateless, single-shot design avoids by
  construction.

## 11. Failure modes and misuse

Sandbox escape or ambient credential leakage. Symptom, code that should have
been contained can reach a resource outside the sandbox, an internal network
address, a mounted secret, a host filesystem path. Cause, the sandbox
boundary was implemented with a shared kernel, a permissive network policy,
or a filesystem mount that leaked host paths into the container. Fix, adopt
an isolation technology with a documented, audited boundary (gVisor,
Firecracker microVMs, or a vetted WASM runtime), deny all network egress by
default rather than allow-listing it, and never mount host credentials,
environment variables, or filesystem paths into the sandbox even for
convenience.

Prompt injection turning into code injection. Symptom, the agent executes
code that does something the user never asked for, exfiltrating data read
from a document, calling an unexpected external service, deleting files.
Cause, untrusted content ingested earlier in the conversation, a scraped web
page, a document, a tool result, contained text that instructed the model to
write malicious code, and the model complied because the malicious
instruction was indistinguishable in context from a legitimate one. Fix,
treat every piece of retrieved or tool-returned content as data, never as
instructions, per `prompt-injection-defense`, and combine with a sandbox
that has no network egress so that even a successfully injected program
cannot exfiltrate anything, because there is nowhere for it to send data.

Resource exhaustion from an unbounded loop. Symptom, a single invocation
runs far longer than expected, the container is killed by a watchdog, or the
whole service's compute budget is consumed by one runaway request. Cause,
the model wrote code with an infinite or near-infinite loop, often from a
subtly wrong termination condition, and the runtime had no independent
wall-clock or CPU cap to stop it. Fix, enforce a hard, external
execution-time limit and memory limit at the sandbox level, never rely on
the submitted code to terminate itself, and surface a distinct, structured
error (Anthropic's `execution_time_exceeded` is a concrete, sourced example,
platform.claude.com/docs, verified 2026-08-02) so the model can reason about
the failure rather than silently retrying the same broken program.

Silent truncation producing confidently wrong reasoning. Symptom, the model
states a conclusion about data it never actually saw in full, because the
printed output was cut off and the model was not told it was cut off.
Cause, the observation formatter truncated a long stdout to fit a context
budget without marking the truncation explicitly. Fix, always attach an
explicit output-truncated marker with the cutoff length when truncation
happens, and prefer summarizing large results INSIDE the sandbox (compute
and print only the aggregate the model actually needs) over dumping raw
output and truncating it after the fact.

State bleed across reused containers. Symptom, an agent's second, unrelated
task in a new conversation somehow sees a variable, file, or partial result
from a previous, different task. Cause, a container was reused across
sessions or users when it should have been scoped to exactly one
conversation, or the checkpoint-and-restore logic restored stale state the
new task never expected. Fix, scope every container identifier tightly to a
single conversation or workspace (Anthropic scopes containers to the API
key's workspace, platform.claude.com/docs, verified 2026-08-02), never share
a container id across distinct end users, and treat a restored container's
pre-existing state as untrusted input that the current task's code might not
expect.

Treating code execution as an approval mechanism. Symptom, a consequential
real-world action, a payment, a production deletion, happens without any
human ever reviewing it, because the code running successfully was mistaken
for the action being approved. Cause, conflating the sandbox's safety
guarantee, this code cannot escape its box, with an authorization guarantee,
this action was cleared to happen, which are unrelated properties. Fix, gate
any consequential outer effect behind an explicit `human-in-the-loop`
checkpoint that happens outside and in addition to sandbox execution, never
as a side effect of the sandbox merely running without error.

## 12. Trade-off matrix

| Force | Code execution as tool | Function calling (fixed schema) | ReAct (reason, then one discrete action) |
|---|---|---|---|
| Multi-step orchestration in one turn | Native, the whole point of the pattern | Not possible, one call per turn by design | Not possible, one action per reasoning step |
| Attack surface | Largest, an interpreter is a general computer | Smallest, each tool is a narrow, typed function | Same as function calling, since ReAct's action is usually a single tool call |
| Handles arbitrary novel computation | Yes, bounded only by the sandbox's language | No, only what a pre-declared tool exposes | No, inherits function calling's limits |
| Token cost per multi-step task | Low, one program plus one consolidated observation | High, one schema read and one result per step | High, one reasoning trace plus one result per step |
| Operational complexity to build | High, requires real sandbox infrastructure | Low, a typed function and a JSON schema | Low, layered on top of function calling |
| Debuggability of a single decision | Lower, a subtle bug in generated code fails silently and confidently | Higher, each call and result is individually inspectable | Higher, the reasoning trace before each action is visible |
| Latency floor | Container provisioning cost, hundreds of ms or more | Near-zero beyond the function's own runtime | Near-zero beyond the function's own runtime, plus more reasoning tokens |
| Statefulness across turns | Available via container reuse, at added operational cost | None by default, must be modeled explicitly | None by default, must be modeled explicitly |

## 13. Related and incompatible patterns

Composes with `function-calling`. Code execution as tool is not a
replacement for function calling, it is a layer that can sit ON TOP of it.
Programmatic tool calling and MCP code mode explicitly call OTHER declared
function-calling tools from inside the sandbox (dimension 8), so the two
patterns are frequently used together in the same agent, function calling
for narrow, individually authorized actions, code execution for the
orchestration and computation glue between them.

Composes with `human-in-the-loop`. As stated in dimension 11, sandboxed
execution answers whether this code can run safely and human-in-the-loop
answers whether this real-world effect should happen at all. Any code
execution capable of triggering an outer, consequential tool call should
have that outer call gated by an approval step, not by the sandbox alone.

Composes with `cost-guard` and `token-budget`. Because the pattern trades
tokens for compute, and because an unbounded loop or an unexpectedly large
output can consume real infrastructure budget, production deployments pair
code execution with an explicit cost or resource ceiling, at the
per-request level (execution time and memory, as dimension 11 covers) and
at the aggregate, per-session or per-account level.

Composes with `tool-result-caching`. A deterministic, pure computation
executed inside a sandbox is an excellent caching candidate. if the same
program with the same inputs is likely to run again, caching its result
avoids paying the container provisioning cost twice. Caching becomes unsafe,
however, the moment the executed code has any side effect outside the
sandbox (an outer tool call in the programmatic variant), since a cached
result would silently skip that effect on replay.

Related to `react` and `plan-execute`. Both are agent-loop control patterns
that decide WHEN and WHAT action to take. Code execution as tool is a
specific SHAPE of action available inside either loop, a ReAct agent's
single action can itself be write and run this program, and a plan-execute
agent's individual execution step can likewise be a code execution call
rather than a narrow function call.

Incompatible with a hard no-arbitrary-computation constraint. Some regulated
environments require every possible agent action to be enumerable and
pre-auditable in advance, a closed tool catalog with no general-purpose
computation escape hatch. Code execution as tool is definitionally
incompatible with that constraint, since its entire value is allowing
computation the framework author did not enumerate in advance. Environments
with this requirement should stay on pure function calling.

## 14. Refactoring path in and out

Introducing the pattern into an agent that only has fixed function-calling
tools.

1. Identify the actual bottleneck first. count, for a representative sample
   of real tasks, how many sequential tool calls a multi-step operation
   currently takes, and how much of the growing context is tool schemas and
   intermediate results rather than user-relevant content. If this number is
   small, the refactor is not yet earning its infrastructure cost.
2. Stand up an isolated sandbox as a genuinely separate service or provider
   integration BEFORE writing any agent-facing code. do not begin by
   evaluating model output in the same process that also holds credentials
   or handles other requests, that is not a smaller version of this
   pattern, it is a different and unsafe pattern.
3. Ship the narrowest useful version first, a single language, no network
   egress, a hard time and memory limit, no state reuse across
   invocations. This matches OpenAI's and Anthropic's original single-shot
   shapes and is the safest place to start.
4. Declare the tool to the model with an honest, specific description of
   what libraries or commands are actually available inside the sandbox,
   an inaccurate description produces code that fails against the real
   environment.
5. Add observability, dimension 16, before adding statefulness. know what
   is running and how it fails before making its state persist across
   turns.
6. Only after the single-shot version is stable and monitored, evaluate
   whether container reuse (statefulness) or an outer tool bridge
   (programmatic tool calling or code mode) is actually needed, driven by
   the same bottleneck measurement from step 1, not by the availability of
   the feature.

Removing the pattern, or descoping it, when it stops earning its place.

1. Look for the actual usage pattern in production. if the vast majority of
   executed programs are trivial, one arithmetic operation, one string
   format, that never touches an external library or another tool, the
   sandbox's overhead and attack surface are being paid for value the model
   could have computed directly, and a narrower function-calling tool
   (or letting the model reason it directly) is the right descoping move.
2. If container reuse was added but telemetry shows most sessions never
   issue a second call against the same container id, remove statefulness
   first, reverting to single-shot execution, before removing the sandbox
   entirely. this recovers most of the operational complexity cost while
   keeping the genuinely useful computation capability.
3. If the outer tool bridge (programmatic tool calling or code mode) is
   unused because the agent's tool catalog is small enough that plain
   function calling never hit the token-cost problem it was solving,
   disable the bridge specifically rather than the whole pattern, since
   plain code execution for computation may still be earning its keep on
   its own.
4. Never remove the sandbox boundary while retaining the ability for the
   model to submit arbitrary code, that combination is strictly the
   in-process evaluation anti-pattern warned against in dimension 4 and
   step 2 above.

## 15. Testing and verification

Testing this pattern has two genuinely distinct layers, and conflating them
produces false confidence.

Testing the sandbox itself (infrastructure-level, deterministic). This layer
does not involve the model at all and should be tested exactly like any
other piece of infrastructure. write integration tests that submit FIXED,
known programs, not model-generated ones, and assert on the sandbox's
behavior. a program that tries to open a network socket must fail with a
network-denied error, not silently succeed. a program that allocates past
the memory limit must be killed and report a structured out-of-memory
result, not hang. a program that loops forever must be terminated at the
configured wall-clock limit and return the documented timeout error, not
run indefinitely. a program that reads a path outside its workspace must
fail. These are exactly the kind of adversarial, fixed-input tests that
belong in a CI suite and should never depend on what the model happens to
generate on a given day.

Testing the model's tool-use decisions (agent-level, probabilistic). This
layer is fundamentally different, it is testing whether the MODEL correctly
chooses to use code execution, writes reasonably correct code for the task,
and correctly interprets the returned observation. Because model output is
not deterministic, this layer is tested with a held-out evaluation set of
realistic tasks and an automated or human-graded rubric over outcomes (did
the final answer match the expected result, did the agent avoid an
unnecessary sandbox call for a trivial arithmetic task), rather than with
exact-match assertions on the generated code itself. The `llm-as-judge` and
`golden-dataset` entries in this family describe the general shape of this
evaluation layer, code execution as tool is simply one more action type
inside that evaluation runtime.

Mocking for unit tests of the surrounding agent logic. When testing code
that ORCHESTRATES the agent (routing, retry logic, the observation
formatter) without wanting to pay a real container's cost on every test run,
substitute a fake execution backend that returns a scripted stdout, stderr,
and exit code for a given input, verified once against the real sandbox's
actual response shape so the fake does not drift from reality. This is the
same test-double discipline used for any external dependency, applied here
specifically to the execution result's shape (interleaved server_tool_use
and tool_result content blocks, plus a container object, in Anthropic's API
shape, platform.claude.com/docs, verified 2026-08-02).

Regression-testing prompt injection resistance. Because dimension 11's most
serious failure mode is injected instructions turning into executed code,
maintain a corpus of known injection attempts (instructions embedded in a
document, a web page, or a tool result) and periodically verify the agent
does not act on them by writing and running code that serves the injected
instruction rather than the user's actual request.

## 16. Observability signals

Per-invocation execution telemetry. Log, for every code execution call, the
language, the size of the submitted code, the sandbox provisioning latency
separate from the execution latency, the exit code or termination reason
(completed, timed out, killed for memory, killed for a policy violation),
and the size of the returned stdout before any truncation. A healthy fleet
shows a tight distribution of provisioning latency (the container manager is
warm and responsive) and a low rate of non-completed terminations, a rising
rate of timeouts or memory kills is an early signal that either the model is
generating pathological code more often (worth investigating why) or a
resource limit needs adjusting.

Container lifecycle metrics, for stateful implementations. Track container
creation rate, checkpoint rate, restore rate, and eventual expiry rate. A
container-reuse implementation whose restore rate is near zero is a strong
signal that statefulness is unused overhead and the descoping path in
dimension 14 applies. A restore rate that stays high while the underlying
task's session count is flat can indicate leaking containers that never
properly expire.

Network egress attempts, even when correctly denied. Because the sandbox's
network policy should deny all egress by default, every attempted outbound
connection from inside a sandbox is itself a security-relevant event, not
merely a routine denial. Alert on any non-zero rate of egress attempts,
since a legitimate task should never need to try, and a rising rate is a
leading indicator of either a misconfigured task, a confused model, or an
active prompt injection attempt (dimension 11).

Truncation rate. Track how often stdout or a returned file is truncated
before reaching the model. A high truncation rate correlates directly with
the silent-wrong-reasoning failure mode in dimension 11 and is a signal to
either raise the output budget for that use case or push more summarization
work into the sandbox itself.

Tool-choice ratio, for agents with both code execution and narrow
function-calling tools available. Track how often the model reaches for
code execution versus a purpose-built tool for tasks that either could
plausibly handle. A model that reaches for the sandbox on trivial,
single-value lookups is paying an unnecessary latency and cost tax, which is
visible only by comparing this ratio against the task's actual complexity,
not from any single invocation's logs in isolation.

## 17. Security and privacy implications

This dimension carries the pattern's dominant risk, and it deserves the most
direct treatment in the entry.

The interpreter is the whole risk surface. Every other tool in an agent's
catalog is, by construction, limited to whatever narrow operation its
author implemented. A code execution tool is limited only by what the
sandbox's isolation technology and network policy actually enforce, because
the model, not the framework author, chooses the program. Any security
review of an agent that includes this tool must treat the sandbox
configuration, not the tool's declared description, as the actual security
boundary.

Network egress denial is the single highest-value control. Anthropic's own
container has internet access completely disabled (platform.claude.com/docs,
Containers section, verified 2026-08-02), and this is the correct default,
not an optional hardening step. Even a fully successful prompt injection
that gets malicious code executed cannot exfiltrate data if the sandbox has
nowhere to send it. Any implementation that allows outbound network access
from the sandbox by default is accepting a materially larger risk and
should require an explicit, narrowly scoped allow-list rather than open
egress.

No ambient credentials, ever. The sandbox must never have access to API
keys, database connection strings, cloud credentials, or any secret the host
application holds, even ones that seem unrelated to the current task. A
credential present in the sandbox's environment is reachable by any code the
model chooses to write, including code injected via untrusted content, so
the only safe posture is that the sandbox starts with no secrets and any
outer effect requiring a credential happens outside the sandbox, invoked
through an authorized, narrow tool call, never by handing the credential
into the box.

Data classification before it reaches the sandbox. Because a sandbox is the
largest attack surface in the system, sensitive data, personally
identifiable information, secrets, regulated records, should be classified
and, where policy requires it, redacted or tokenized BEFORE it is passed
into a code execution context, composing with the `pii-redaction` entry in
this family. This is a data-minimization control independent of whether the
sandbox itself is compromised, since a compromised sandbox with sensitive
data inside it is a strictly worse incident than a compromised sandbox with
none.

Container reuse extends the blast radius window. A stateless, single-shot
sandbox limits the damage of any single compromised execution to that one
invocation. Container reuse, useful as it is for legitimate statefulness,
means a compromise, or simply a bug that leaves unexpected state behind,
can persist and affect a LATER, unrelated invocation that resumes the same
container. Any implementation that reuses containers must scope reuse
tightly (per conversation, per authenticated user, never shared across
tenants) and must treat resumed state as untrusted input the current task
should validate rather than assume.

Prompt injection is the primary threat model, not malicious end users. In
practice, the person typing into the chat interface is rarely the actual
attacker. the attacker is usually a third party whose content, a web page,
a document, an email, a tool result, the agent ingests as data and which
contains hidden instructions aimed at getting the model to write and execute
harmful code on the attacker's behalf. This makes `prompt-injection-defense`
a load-bearing companion pattern, not an optional add-on, for any agent
that exposes code execution.

Auditability and reproducibility. For regulated or high-trust deployments,
log the full submitted code, not just a summary, alongside the returned
observation, so a later audit can reproduce exactly what ran and why.
Anthropic's own container scoping to the API key's workspace
(platform.claude.com/docs, verified 2026-08-02) is a sourced example of
tenant-level isolation that also supports this kind of accountable audit
trail.

## Code examples

Each example implements the same minimal execution runner. run a submitted
program in an isolated interpreter, enforce a hard timeout, and format the
result into a truncation-marked observation, the shape dimension 5 and
dimension 7 describe. All three were executed on this machine at authoring
time. Python via python3, TypeScript via npx tsc targeting Node's built in
vm module, and Rust via rustc. Java and Kotlin are omitted, a working JRE
was not available in the authoring environment to compile or run a Java
sample, so no Java code is shown here rather than presenting unverified
code.

```python
"""Minimal illustration of the code execution as tool pattern."""

import subprocess
import sys
import time
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    duration_s: float


def run_in_sandbox(code: str, timeout_s: float = 2.0) -> ExecutionResult:
    # Simulates the session manager plus execution runtime in dimension 5.
    start = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        duration = time.monotonic() - start
        return ExecutionResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
            timed_out=False,
            duration_s=duration,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - start
        return ExecutionResult(
            stdout=exc.stdout or "",
            stderr="execution_time_exceeded",
            exit_code=-1,
            timed_out=True,
            duration_s=duration,
        )


def format_observation(result: ExecutionResult, max_chars: int = 200) -> str:
    # Simulates the observation formatter in dimension 5.
    if result.timed_out:
        return "[code_execution_error] execution_time_exceeded"
    body = result.stdout
    truncated = len(body) > max_chars
    if truncated:
        body = body[:max_chars] + "...[output truncated at %d characters]" % max_chars
    return "exit_code=%d\nstdout=%s" % (result.exit_code, body)


if __name__ == "__main__":
    good_code = (
        "rows = list(range(1, 11))\n"
        "print('sum=' + str(sum(rows)) + ' avg=' + str(sum(rows) / len(rows)))\n"
    )
    good_result = run_in_sandbox(good_code)
    print("Well-behaved program observation:")
    print(format_observation(good_result))
    print()

    # Exercises the resource-exhaustion failure mode from dimension 11.
    bad_code = "while True:\n    pass\n"
    bad_result = run_in_sandbox(bad_code, timeout_s=0.5)
    print("Runaway program observation:")
    print(format_observation(bad_result))
    assert bad_result.timed_out is True
    assert bad_result.exit_code == -1

    # Exercises the silent-truncation failure mode from dimension 11.
    verbose_code = "print('x' * 500)\n"
    verbose_result = run_in_sandbox(verbose_code)
    observation = format_observation(verbose_result, max_chars=50)
    print()
    print("Truncated observation:")
    print(observation)
    assert "truncated" in observation
```

Ran with python3 code-execution.py. Output confirms the well-behaved
program's exit code and computed average, the runaway program's timeout
observation, and the truncation marker on the long-output program.

```typescript
// UI_QUALITY_OVERRIDE_OK: standalone CLI demo script, not shipped UI code.
import * as vm from "node:vm";

interface ExecutionResult {
  stdout: string;
  exitCode: number;
  timedOut: boolean;
}

function runInSandbox(code: string, timeoutMs: number): ExecutionResult {
  const lines: string[] = [];
  const sandboxConsole = {
    log: (...args: unknown[]) => lines.push(args.map(String).join(" ")),
  };
  const context = vm.createContext({ console: sandboxConsole });
  try {
    vm.runInContext(code, context, { timeout: timeoutMs });
    return { stdout: lines.join("\n"), exitCode: 0, timedOut: false };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    const timedOut = message.includes("Script execution timed out");
    return { stdout: lines.join("\n"), exitCode: timedOut ? -1 : 1, timedOut };
  }
}

function formatObservation(result: ExecutionResult, maxChars = 200): string {
  if (result.timedOut) return "[code_execution_error] execution_time_exceeded";
  let body = result.stdout;
  if (body.length > maxChars) {
    body = body.slice(0, maxChars) + `...[output truncated at ${maxChars} characters]`;
  }
  return `exit_code=${result.exitCode}\nstdout=${body}`;
}

const goodCode = `
const rows = Array.from({ length: 10 }, (_, i) => i + 1);
const sum = rows.reduce((a, b) => a + b, 0);
console.log("sum=" + sum + " avg=" + sum / rows.length);
`;
const goodResult = runInSandbox(goodCode, 500);
console.log("Well-behaved program observation:");
console.log(formatObservation(goodResult));
console.log();

const badCode = "while (true) {}";
const badResult = runInSandbox(badCode, 200);
console.log("Runaway program observation:");
console.log(formatObservation(badResult));
if (!badResult.timedOut) throw new Error("expected timeout");

const verboseCode = "console.log('x'.repeat(500));";
const verboseResult = runInSandbox(verboseCode, 500);
const observation = formatObservation(verboseResult, 50);
console.log();
console.log("Truncated observation:");
console.log(observation);
if (!observation.includes("truncated")) throw new Error("expected truncation marker");
```

Type-checked with tsc --noEmit --strict --target es2022 --lib es2022
--moduleResolution bundler --module esnext --types node, and separately
compiled to CommonJS and run with node to confirm the runtime behavior.
This variant uses Node's built in vm module as a language level analogue of
a sandbox, real production systems use process or hypervisor level
isolation, never vm alone, because vm shares the host process's memory and
can still reach host globals through prototype pollution. it is shown here
only to demonstrate the timeout and observation-formatting mechanics in a
single file with no external sandboxing dependency.

```rust
use std::io::Read;
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};

struct ExecutionResult {
    stdout: String,
    exit_code: i32,
    timed_out: bool,
}

fn run_in_sandbox(code: &str, timeout: Duration) -> ExecutionResult {
    let mut child = Command::new("python3")
        .arg("-c")
        .arg(code)
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .expect("failed to spawn interpreter");

    let start = Instant::now();
    let mut timed_out = false;
    loop {
        let wait_status = child.try_wait().expect("wait failed");
        match wait_status {
            Some(_status) => break,
            None => {
                if start.elapsed() > timeout {
                    let _ = child.kill();
                    let _ = child.wait();
                    timed_out = true;
                    break;
                }
                std::thread::sleep(Duration::from_millis(10));
            }
        }
    }

    let mut stdout = String::new();
    if let Some(mut out) = child.stdout.take() {
        let _ = out.read_to_string(&mut stdout);
    }
    let exit_code = if timed_out { -1 } else { 0 };
    ExecutionResult {
        stdout,
        exit_code,
        timed_out,
    }
}

fn format_observation(result: &ExecutionResult, max_chars: usize) -> String {
    if result.timed_out {
        return "[code_execution_error] execution_time_exceeded".to_string();
    }
    let body = &result.stdout;
    if body.chars().count() > max_chars {
        let truncated: String = body.chars().take(max_chars).collect();
        format!(
            "exit_code={}\nstdout={}...[output truncated at {} characters]",
            result.exit_code, truncated, max_chars
        )
    } else {
        format!("exit_code={}\nstdout={}", result.exit_code, body)
    }
}

fn main() {
    let good_code = "rows = list(range(1, 11))\nprint('sum=' + str(sum(rows)) + ' avg=' + str(sum(rows) / len(rows)))\n";
    let good = run_in_sandbox(good_code, Duration::from_millis(2000));
    println!("Well-behaved program observation:");
    println!("{}", format_observation(&good, 200));
    println!();

    let bad_code = "while True:\n    pass\n";
    let bad = run_in_sandbox(bad_code, Duration::from_millis(300));
    println!("Runaway program observation:");
    println!("{}", format_observation(&bad, 200));
    assert!(bad.timed_out, "expected the runaway program to time out");

    let verbose_code = "print('x' * 500)\n";
    let verbose = run_in_sandbox(verbose_code, Duration::from_millis(2000));
    let observation = format_observation(&verbose, 50);
    println!();
    println!("Truncated observation:");
    println!("{}", observation);
    assert!(
        observation.contains("truncated"),
        "expected a truncation marker"
    );
}
```

Compiled with rustc -O main.rs and run directly. This example shells out to
a real python3 subprocess, so it demonstrates the process-boundary
isolation model (the same family as the OS-container isolation named in
dimension 8) rather than an in-language sandbox, which is closer to how a
production execution runtime actually enforces its timeout, killing an
external process rather than interrupting a shared interpreter.

## 18. References

1. Wang, Xingyao and Chen, Yangyi and Yuan, Lifan and Zhang, Yizhe and Li,
   Yunzhu and Peng, Hao and Ji, Heng. "Executable Code Actions Elicit Better
   LLM Agents." arXiv:2402.01030, submitted 1 February 2024, accepted ICML
   2024. https://arxiv.org/abs/2402.01030 (verified 2026-08-02).
2. Anthropic. "Code execution tool." Claude Developer Platform documentation. https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool (verified 2026-08-02).
3. Anthropic. "Programmatic tool calling." Claude Developer Platform
   documentation, cross-linked from the code execution tool page and
   referenced for the outer-tool-bridge behavior described in dimensions 7
   and 8. https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling (verified 2026-08-02, page existence and cross-link confirmed via the code execution tool page fetched the same date).
4. E2B. "Sandbox" product documentation, ephemeral cloud sandboxes for
   AI-agent code execution. https://e2b.dev (verified 2026-08-02).
5. Cloudflare. Agents SDK and Sandbox SDK documentation, including the
   code-mode pattern for executing agent-authored code against Model
   Context Protocol tools. https://developers.cloudflare.com (verified
   2026-08-02, cross-referenced against this repository's `sandbox-sdk`
   entry).
6. OpenAI. Code Interpreter product documentation (ChatGPT and, historically,
   the Assistants API `code_interpreter` tool), the shipping precedent that
   established the common industry name for the pattern, cited here as
   established product history and cross-checked against Anthropic's own
   comparable feature description (verified 2026-08-02).

Two of the sources above, items 3 and 6, are cited for the general shape of
a documented capability rather than a specific quoted figure, per the
judgement-versus-sourced-claim guidance in the entry template, because the
individual page for item 3 was reached only via its cross-link from item 2
and item 6 reflects a widely known product history rather than one single
canonical document.
