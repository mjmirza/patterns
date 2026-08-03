---
name: Model Context Protocol
slug: model-context-protocol
family: 17-ai-agentic
category: Agentic
aliases: [MCP, USB-C for AI]
first_described: "Anthropic, 25 November 2024"
maturity: canonical
related: [function-calling, react-prompting, orchestrator-worker, retrieval-augmented-generation]
incompatible_with: []
verified: 2026-08-03
---

# Model Context Protocol

## 1. Name, aliases, and lineage

The canonical name is Model Context Protocol, always abbreviated MCP in
practice. Anthropic released it as an open specification on 25 November 2024,
created by David Soria Parra and Justin Spahr-Summers, with the launch post
describing MCP as "a new standard for connecting AI assistants to the systems
where data lives, including content repositories, business tools, and
development environments" and framing the goal as replacing "fragmented
integrations with a single protocol" (Anthropic, "Introducing the Model
Context Protocol", 25 November 2024,
https://www.anthropic.com/news/model-context-protocol, verified 2026-08-03).
The specification itself opens with a similar framing, calling MCP "an open
protocol that enables integration between LLM applications and external data
sources and tools" (Model Context Protocol, "Specification", version
2025-06-18, https://modelcontextprotocol.io/specification/2025-06-18,
verified 2026-08-03).

The informal alias USB-C for AI circulated widely in developer commentary
during 2025 as a way to explain the shape of the problem to people who had
never built an integration themselves. The comparison is a community
shorthand, not a name Anthropic itself uses in the specification, and this
entry treats it as an alias worth knowing rather than as the pattern's
identity. The specification's own vocabulary is precise about roles rather
than metaphors. a **host** is the LLM application that starts a connection, a
**client** is the connector object living inside that host, one per server
connection, and a **server** is the process that exposes tools, resources, or
prompts back to the client (Model Context Protocol, "Architecture overview",
https://modelcontextprotocol.io/docs/learn/architecture, verified 2026-08-03).

MCP did not invent the idea of exposing named, schema-described actions to a
language model. It formalizes an existing pattern, function calling, into a
protocol with its own transport, lifecycle, and capability negotiation, so
that the client-server relationship is not tied to one vendor's request
format. Where function calling describes what happens inside a single model
request, turning the model's output into a structured call the caller's code
then executes, MCP describes how a wide set of tool providers and tool
consumers finds each other, agrees on what is available, and exchanges calls
and results across a process boundary. The specification explicitly draws
the comparison to a prior standardization effort in a different domain,
stating that MCP "takes some inspiration from the Language Server Protocol,
which standardizes how to add support for programming languages across a
whole set of development tools," and that "in a similar way, MCP
standardizes how to integrate additional context and tools into the range of
AI applications" (Model Context Protocol, "Specification", version
2025-06-18, https://modelcontextprotocol.io/specification/2025-06-18,
verified 2026-08-03). That comparison is the clearest single sentence for
locating what MCP actually is. it is LSP's idea, applied to model context
instead of source code intelligence.

## 2. Problem and context

Before MCP, every combination of an AI application and an external system
needed its own custom integration. A team building a chat assistant that
should read from a company's ticketing system, query a database, and search a
private wiki wrote three separate adapters, each one translating that
system's API into whatever function-calling shape the model provider expected
that month. If the team also wanted to support a second model provider, or a
second chat client, the adapters had to be rewritten or duplicated, because
the tool description format, the authentication flow, and the invocation
contract were not portable. Anthropic's launch post names this directly as
the N times M problem. N AI applications, each needing to talk to M different
systems, produce N times M point-to-point integrations, and every new
application or every new system multiplies the total rather than adding to
it linearly (Anthropic, "Introducing the Model Context Protocol", 25 November
2024, https://www.anthropic.com/news/model-context-protocol, verified
2026-08-03).

The context in which this problem becomes acute is agentic AI, where a model
is expected to act across a session rather than answer a single question. An
agent that plans a multi-step task needs to read files, call internal APIs,
query a database, and sometimes ask the model itself to reason over an
intermediate result before continuing. Each of those capabilities is owned by
a different system, often maintained by a different team, and the agent
framework sits in the middle trying to reconcile all of it into one coherent
tool-calling loop. Before a shared protocol existed, that reconciliation work
was reinvented inside every agent framework separately, with no way for a
tool built for one framework to be reused by another without a rewrite.

MCP's context is therefore not "how does a model call a function," which
function calling already answers within one request-response cycle. MCP's
context is "how does an application discover, connect to, and exchange
structured messages with an independent process that offers tools, data, or
prompt templates, in a way that works the same regardless of which model or
which host is on the other end." The protocol is deliberately model-agnostic
at the wire level. nothing in the JSON-RPC message shapes mentions a
particular model provider, and the same MCP server can be attached to a
Claude-based host, an OpenAI Agents SDK host, or a VS Code extension without
modification, because all three speak the same specification.

## 3. Forces

Judgement. the weighting below reflects how the protocol's design choices
trade one force against another, reasoned from the specification's own stated
priorities rather than from a single citable ranking.

**Decoupling versus latency.** The main force MCP optimizes for is
decoupling the tool provider from the tool consumer. A server author never
needs to know which host will connect, and a host author never needs to know
which server implementation sits behind a given tool name. That decoupling is
purchased at the cost of an extra process boundary and, for local stdio
servers, an extra subprocess per connected server, which is a real latency
and resource cost compared to an in-process function call. For a single
model turn calling one function, plain function calling inside the model
provider's own API is strictly cheaper. MCP earns its cost back once the same
server is reused across many hosts, rather than at the level of one call.

**Standardization versus flexibility.** By fixing the message shapes (tools,
resources, prompts, sampling, roots, elicitation) the specification trades
away the freedom any one integration had to invent its own richer contract.
A team that needed a custom streaming protocol tuned to one specific
database driver loses some of that specificity when forced into MCP's
general tool-call shape. The specification accepts this trade by allowing
servers to attach arbitrary structured data inside a tool's `inputSchema`
and `outputSchema`, and by permitting custom transports, but the core
message envelope stays fixed.

**Security surface versus capability.** Exposing tools to a model that can
choose when to invoke them, with arguments the model itself constructs,
opens a capability that a static API never had. the caller of the tool is not
a human operator following a runbook but a language model reasoning from a
natural-language prompt, and MCP's own specification is explicit that this
"enables powerful capabilities through arbitrary data access and code
execution paths" and that "with this power comes important security and
trust considerations that all implementors must carefully address" (Model
Context Protocol, "Specification", version 2025-06-18, "Security and Trust &
Safety" section, https://modelcontextprotocol.io/specification/2025-06-18,
verified 2026-08-03). MCP favors capability, a set of servers doing real work
on a person's behalf, and pushes the corresponding cost, consent and
authorization design, onto implementors rather than trying to solve it
inside the protocol itself.

**Statefulness versus operability.** MCP connections are stateful, beginning
with an initialization handshake that negotiates protocol version and
capabilities before either side sends a substantive message (Model Context
Protocol, "Lifecycle",
https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle,
verified 2026-08-03). Statefulness lets a server assume a client has already
declared its capabilities and lets a client cache a server's tool list rather
than re-fetching it on every call, which reduces chatter. It costs
operability. a Streamable HTTP server that wants to scale horizontally has to
either keep session affinity to one backend instance or externalize session
state, and a crashed stdio subprocess silently drops whatever state the
in-flight conversation depended on.

## 4. Applicability and non-applicability

Reach for MCP when an AI application needs to call the same tools, read the
same data sources, or reuse the same prompt templates across more than one
model provider or more than one host application, and when that tool or data
source is substantial enough to justify running as its own process. It fits
naturally when a team is building a general-purpose coding agent, assistant,
or IDE integration that should plug into arbitrary user-supplied backends
(a database the user names at connect time, a ticketing system the user
already has credentials for) rather than a fixed, known set of backends
compiled into the application. It also fits when the goal is explicitly to
publish a reusable integration, an SDK for a SaaS product exposed as a set of
tools other people's agents can call, because the whole point of the protocol
is that a server written once works with any conformant host.

Do not reach for MCP in the following situations, and each has a concrete
reason.

- **A single, fixed integration inside one application that will never be
  reused elsewhere.** If an application calls exactly one internal database
  and always will, wrapping that call in an MCP server adds a subprocess, a
  JSON-RPC envelope, and a lifecycle handshake around what could be a direct
  function call. The decoupling MCP buys has no buyer.
- **Ultra low latency, tight inner loops.** A tool that must be called
  thousands of times per second inside a hot path, for example a
  per-token scoring function, pays real overhead for JSON-RPC framing and,
  on the stdio transport, for the newline-delimited message boundary and
  process scheduling. Plain function calling or a direct in-process call is
  the correct choice there.
- **Where the caller and callee already share a language runtime and a
  process.** If the tool is a pure function living in the same codebase as
  the agent loop, calling it directly is simpler, faster to debug, and does
  not need a schema negotiated over the wire, because the type system already
  is the schema.
- **Where the security model cannot tolerate the trust boundary MCP
  introduces.** Connecting to a third-party MCP server means trusting that
  server's tool descriptions, which the specification itself warns are
  visible to the model but may be manipulated, since "descriptions of tool
  behavior such as annotations should be considered untrusted, unless
  obtained from a trusted server" (Model Context Protocol, "Specification",
  version 2025-06-18, "Security and Trust & Safety" section,
  https://modelcontextprotocol.io/specification/2025-06-18, verified
  2026-08-03). A system with a strict compliance boundary around what code
  can execute on a user's behalf should not adopt an arbitrary,
  user-installable MCP server without the same review process it would apply
  to any other third-party dependency with code execution rights.
- **Where the model provider's native function-calling contract already
  covers the need and no reuse across hosts is planned.** Adding a protocol
  layer for its own sake, when the simpler mechanism already solves the
  actual problem, adds complexity with no payoff.

## 5. Structure

MCP defines three roles and, on the server side, three feature categories the
server can expose.

**Host.** The LLM application itself, for example an IDE, a desktop chat
client, or a custom agent runtime. The host is responsible for obtaining user
consent, deciding which servers to connect to, and mediating what the model
sees from each connected server. The host owns zero or more clients.

**Client.** A connector living inside the host, one instance per server
connection, that speaks the MCP wire protocol to exactly one server and
mediates results back to the host. Splitting client from host lets a host
maintain many independent, isolated connections without one server's state
leaking into another's.

**Server.** An independent process, local or remote, that exposes any
combination of three feature categories to a connected client. **Tools** are
functions the model can choose to invoke, each carrying a name, a
human-readable description, and a JSON Schema for its input (and, since
protocol version 2025-06-18, optionally its output). **Resources** are
addressable pieces of context or data, identified by a URI, that the host or
the model can read without necessarily invoking a function, for example the
contents of a file or the rows of a query result. **Prompts** are
parameterized message templates the server offers for the user to select and
fill in, distinct from tools in that a prompt is initiated by the user
choosing it rather than the model deciding to call it (Model Context
Protocol, "Specification", version 2025-06-18, "Key Details" section,
https://modelcontextprotocol.io/specification/2025-06-18, verified
2026-08-03).

A fourth relationship runs in the opposite direction. clients can offer
capabilities back to servers. **Sampling** lets a server ask the connected
client's host to run a language model completion on the server's behalf,
useful when a server needs a small amount of reasoning without embedding its
own model credentials. **Roots** let a server ask the client which
filesystem or URI boundaries it is permitted to operate within. **Elicitation**
lets a server ask the user, through the client, for additional information
mid-task (Model Context Protocol, "Specification", version 2025-06-18, "Key
Details" section, https://modelcontextprotocol.io/specification/2025-06-18,
verified 2026-08-03).

Underneath all of this sits a base protocol that is transport-agnostic and
message-format-fixed. every exchange is a JSON-RPC 2.0 message, and the
specification states plainly that "the protocol uses JSON-RPC 2.0 messages to
establish communication" between hosts, clients, and servers (Model Context
Protocol, "Specification", version 2025-06-18,
https://modelcontextprotocol.io/specification/2025-06-18, verified
2026-08-03).

## 6. ASCII structure diagram

```text
+------------------------------------------------------------+
|                            HOST                             |
|   (IDE, chat app, agent runtime; owns user consent + UI)    |
|                                                              |
|   +------------+     +------------+     +------------+      |
|   |  Client A  |     |  Client B  |     |  Client C  |      |
|   | (1:1 conn) |     | (1:1 conn) |     | (1:1 conn) |      |
|   +-----+------+     +-----+------+     +-----+------+      |
+---------|------------------|------------------|-------------+
          |  JSON-RPC 2.0    |  JSON-RPC 2.0    |  JSON-RPC 2.0
          |  (stdio)         |  (Streamable HTTP)|  (stdio)
          v                  v                  v
   +-------------+    +-------------+    +-------------+
   |  Server A   |    |  Server B   |    |  Server C   |
   | filesystem  |    |  ticketing  |    |  database   |
   |             |    |  (remote)   |    |             |
   |  exposes:   |    |  exposes:   |    |  exposes:   |
   |  - tools    |    |  - tools    |    |  - tools    |
   |  - resources|    |  - prompts  |    |  - resources|
   +-------------+    +-------------+    +-------------+

   Reverse channel (server asks client for help):
   Server --sampling--> Client --(runs LLM completion)--> Host
   Server --roots------> Client --(reports fs boundary)--> Host
   Server --elicitation-> Client --(asks the user)-------> Host
```

## 7. Dynamics

A connection between one client and one server proceeds through a fixed
lifecycle before either side may send a request unrelated to initialization,
described in the specification's lifecycle document as capability
negotiation followed by an explicit initialized notification (Model Context
Protocol, "Lifecycle",
https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle,
verified 2026-08-03).

```text
Client                                              Server
  |                                                    |
  |-- initialize (protocolVersion, capabilities,       |
  |               clientInfo) -------------------------|>
  |                                                     |
  |<---- InitializeResult (protocolVersion,             |
  |       capabilities, serverInfo) -------------------|
  |                                                     |
  |-- notifications/initialized ----------------------->|
  |          (client confirms it is ready)              |
  |                                                     |
  |============= normal operation begins =============|
  |                                                     |
  |-- tools/list --------------------------------------->|
  |<---- { tools: [ { name, description, inputSchema }]}|
  |                                                     |
  |-- tools/call { name, arguments } ------------------->|
  |                    (server validates against schema,|
  |                     executes the tool)               |
  |<---- { content: [...], isError: false } ------------|
  |                                                     |
  |-- (optional) resources/read { uri } ----------------->|
  |<---- { contents: [...] } ----------------------------|
  |                                                     |
  |-- (optional, server-initiated) sampling/createMessage|
  |<-------------------------------------------------- |
  |     (client asks the host's model to complete a     |
  |      prompt on the server's behalf, subject to       |
  |      explicit user approval)                         |
  |                                                     |
  |-- shutdown: client closes stdin / closes connection ->|
```

The critical dynamic detail is that a tool call is always a decision the
model makes at inference time, not a fixed call the application scripted in
advance. The host presents the model with the tool descriptions it received
from `tools/list`, the model's own reasoning decides whether and when to
emit a `tools/call` for one of them, and the client relays that call to the
server exactly as the model constructed it. This is the same
decision-point structure as function calling, and MCP does not change it. MCP
changes where the tool descriptions and the tool implementation live relative
to the host process, moving them out into an independently versioned,
independently deployed server.

## 8. Implementation variants

**Local stdio servers.** The client launches the server as a subprocess and
exchanges newline-delimited JSON-RPC messages over the child's standard
input and standard output, with the server permitted to write logs to
standard error, which the client may capture or ignore. The specification is
explicit that messages "MUST NOT contain embedded newlines" and that the
server "MUST NOT write anything to its stdout that is not a valid MCP
message" (Model Context Protocol, "Transports",
https://modelcontextprotocol.io/specification/2025-06-18/basic/transports,
verified 2026-08-03). This variant is the default for local development
tools, filesystem access, and anything that should run with the same
privileges as the user's own shell, and clients "SHOULD support stdio
whenever possible" per the same document.

**Streamable HTTP servers.** The server runs as an independent, potentially
multi-tenant process reachable at a single HTTP endpoint that accepts both
POST and GET. A client POSTs a JSON-RPC request and the server responds
either with a single JSON object or by opening a Server-Sent Events stream
that carries zero or more intermediate messages before the final response.
This variant is the one used for remote, hosted MCP servers, and it
explicitly replaced an earlier HTTP-plus-SSE transport from protocol version
2024-11-05, with the current specification providing a documented backward
compatibility path for servers and clients that need to interoperate across
both (Model Context Protocol, "Transports",
https://modelcontextprotocol.io/specification/2025-06-18/basic/transports,
verified 2026-08-03).

**Hosted, connector-mediated servers.** Rather than a client connecting
directly to a remote server, some deployments route the connection through
the model provider's own infrastructure, so the provider's inference API
handles the MCP handshake and tool execution on the caller's behalf.
OpenAI's Agents SDK documents this as one of its five supported transport
options, "hosted MCP server tools," describing it as using the Responses API
"to handle tool execution remotely" (OpenAI, "Model context protocol (MCP)",
Agents SDK documentation, https://openai.github.io/openai-agents-python/mcp/,
verified 2026-08-03). This trades direct control over the connection for
simplified operations, since the caller does not need to keep a server
process alive itself.

**Custom transports.** The specification is explicit that the message
format and lifecycle are the invariant, not the transport, stating that
"clients and servers MAY implement additional custom transport mechanisms to
suit their specific needs" as long as they "preserve the JSON-RPC message
format and lifecycle requirements" (Model Context Protocol, "Transports",
https://modelcontextprotocol.io/specification/2025-06-18/basic/transports,
verified 2026-08-03). In practice this variant shows up as MCP tunneled
through a message queue or an existing internal RPC fabric inside a large
organization, where standing up a fresh HTTP endpoint per tool server is
undesirable.

**SDK-generated versus hand-rolled servers.** The overwhelming majority of
production MCP servers are built on top of an official or community SDK
(TypeScript, Python, Java, Kotlin, C#, Go, Rust, Swift SDKs exist under the
`modelcontextprotocol` GitHub organization) that handles the JSON-RPC
framing, schema validation, and lifecycle bookkeeping, leaving the author to
implement only the tool logic. A hand-rolled server that speaks the wire
protocol directly, as the code examples in this entry do, is a legitimate
variant for a minimal footprint or an unsupported language, but it inherits
the full burden of correctly implementing message framing, error codes, and
the initialization handshake by hand.

## 9. Known production uses

Anthropic's own Claude Desktop application shipped with built-in local MCP
server support at the protocol's public launch, and the same announcement
names early adopters across both companies integrating MCP into their own
systems and developer tool vendors partnering to support it, specifically
stating that "Block and Apollo have integrated MCP into their systems" and
that "development tools companies including Zed, Replit, Codeium, and
Sourcegraph are working with MCP" to let their platforms "gain context from
tools built by their users or the broader developer community" (Anthropic,
"Introducing the Model Context Protocol", 25 November 2024,
https://www.anthropic.com/news/model-context-protocol, verified 2026-08-03).

OpenAI's Agents SDK, a framework independent of Anthropic, ships first-class
support for MCP as a tool-calling mechanism, with its documentation stating
that "the Agents Python SDK understands multiple MCP transports," naming
hosted MCP server tools, Streamable HTTP, the deprecated HTTP-with-SSE
transport, stdio servers, and a multi-server manager as the five supported
shapes (OpenAI, "Model context protocol (MCP)", Agents SDK documentation,
https://openai.github.io/openai-agents-python/mcp/, verified 2026-08-03).
This is independent, cross-vendor evidence that MCP achieved its stated goal
of being usable by more than one model provider's tooling, not only
Anthropic's own products.

Microsoft's Visual Studio Code has built-in support for connecting to MCP
servers from its agent mode, configured through a workspace-level or
user-level `mcp.json` file, with the product documentation describing MCP as
"an open standard for connecting AI models to external tools and services"
and stating that "in Visual Studio Code, MCP servers provide tools for tasks
like file operations, databases, or external APIs" (Microsoft, "Use MCP
servers in VS Code", Visual Studio Code documentation,
https://code.visualstudio.com/docs/copilot/chat/mcp-servers, verified
2026-08-03).

Claude Code, Anthropic's own coding agent product, is itself an MCP host at
runtime, connecting to user-configured local and remote MCP servers to
extend its own tool surface, which is the mechanism by which the very
environment this entry was authored in gains access to servers such as a
Figma design bridge, a Google Workspace connector, and an Apple platform
build toolchain, each implemented as an independent MCP server process
started and supervised outside the model's own weights.

## 10. Consequences

Positive.

- **A tool built once is usable by any conformant host.** The core promise of
  the protocol is realized concretely. the same filesystem server, database
  server, or SaaS connector server works unmodified whether the calling host
  is Claude Desktop, an OpenAI Agents SDK application, or VS Code, because
  all three implement the same wire specification.
- **Capability discovery is explicit and machine-readable.** A client never
  needs prior, out-of-band knowledge of what a server can do. `tools/list`,
  `resources/list`, and `prompts/list` return that information at connection
  time, which lets a host present the model with an accurate, current tool
  surface rather than a stale hardcoded one.
- **The trust and consent model is named as a first-class design concern,
  not an afterthought.** The specification's "Security and Trust & Safety"
  section states four explicit principles, requiring hosts to obtain user
  consent before invoking any tool and before exposing user data to a
  server, and requiring that LLM sampling requests be explicitly approved by
  the user rather than granted implicitly (Model Context Protocol,
  "Specification", version 2025-06-18, "Security and Trust & Safety"
  section, https://modelcontextprotocol.io/specification/2025-06-18,
  verified 2026-08-03).
- **Independent versioning and deployment.** A server can be updated,
  redeployed, or scaled without touching the host application's code, and a
  host can be upgraded without breaking servers that still speak an older
  negotiated protocol version, because version negotiation happens
  explicitly during `initialize`.

Negative.

- **Every connected server is a live trust boundary.** Because tool
  descriptions are, per the specification's own wording, visible to the
  model and must be "considered untrusted, unless obtained from a trusted
  server," a host that connects to an unreviewed third-party server has
  handed that server's author influence over what the model believes it is
  supposed to do, not only what data it can access.
- **Statefulness costs operability.** stdio servers die with their process
  and cannot be load-balanced. Streamable HTTP servers that assign a session
  ID must handle session affinity or externalize session state, and the
  specification's own session management rules require the server to
  respond with HTTP 404 once a session is terminated, which every client
  implementation must handle correctly or lose work silently.
- **Overhead is real for high-frequency, low-latency calls.** A subprocess
  boundary and a JSON-RPC envelope are measurable cost against a plain
  in-process function call, and that cost does not disappear just because
  the protocol is standardized.
- **Adoption quality is uneven.** because any developer can publish an MCP
  server, the quality, security posture, and correctness of published
  servers varies enormously, and there is no protocol-level mechanism that
  verifies a server behaves as its tool descriptions claim.

## 11. Failure modes and misuse

Judgement. the symptoms below are drawn from documented security research and
common operational patterns, not from a single canonical source, and are
labelled as engineering experience where no citation exists.

**Tool poisoning attacks.** Symptom, the model performs an action the user
never asked for, such as reading and exfiltrating a credentials file, after
connecting to a seemingly unrelated MCP server. Cause, the server's tool
description contains instructions hidden from the user's simplified UI view
but fully visible to the model, exploiting what security researchers at
Invariant Labs describe as an asymmetry where "AI models see the complete
tool descriptions, including hidden instructions, while users typically only
see simplified versions in their UI," letting a malicious description direct
the model to read sensitive files and transmit their contents "covertly
through tool parameters" (Invariant Labs, "MCP Security Notification. Tool
Poisoning Attacks", https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks,
verified 2026-08-03). Fix, treat every third-party server's tool description
text as untrusted input subject to the same review a new code dependency
would get, and prefer hosts that render the full tool description to the
user rather than a truncated summary before the first invocation is
approved.

**Rug pull, post-approval description changes.** Symptom, a server that
behaved correctly for weeks suddenly directs the model to perform an
unexpected action. Cause, the specification does not require a tool
description to stay constant after a user has approved it once, and the same
Invariant Labs research documents this explicitly, that "a malicious server
can change the tool description after the client has already approved it,"
drawing the parallel to package-repository supply-chain attacks where a
previously trusted artifact is modified after the fact (Invariant Labs, "MCP
Security Notification. Tool Poisoning Attacks",
https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks,
verified 2026-08-03). Fix, pin and hash-verify server versions in production
deployments rather than always connecting to a mutable latest, and re-surface
approval to the user whenever a connected server's declared tool set or
descriptions change between sessions.

**Shadowing across trusted servers.** Symptom, a legitimately trusted,
correctly-behaving server starts producing output that redirects sensitive
data toward an unrelated destination. Cause, a second, malicious server
connected in the same session can, through its own tool description,
instruct the model to alter how it uses a different, trusted server's tools,
a variant Invariant Labs names the shadowing attack (Invariant Labs, "MCP
Security Notification. Tool Poisoning Attacks",
https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks,
verified 2026-08-03). Fix, do not assume server-to-server isolation is
automatic. a host should scope what each server's tool descriptions can
influence, and a security-conscious deployment audits the full set of
concurrently connected servers together, not each one in isolation.

**Silent stdio protocol corruption.** Symptom, the client hangs or receives
malformed JSON that it cannot parse. Cause, a server-side `print` statement,
logging call, or unflushed buffer writes non-protocol text to standard
output, which the specification forbids outright, stating the server "MUST
NOT write anything to its stdout that is not a valid MCP message" (Model
Context Protocol, "Transports",
https://modelcontextprotocol.io/specification/2025-06-18/basic/transports,
verified 2026-08-03), and a stray debug print breaks that invariant instantly
because stdout is the only channel carrying protocol messages on this
transport. Fix, route every diagnostic message to stderr, never stdout, and
add an integration test that asserts every line on stdout parses as valid
JSON-RPC before a stdio server ships.

**Treating tool-call arguments as pre-validated.** Symptom, a tool call
succeeds with type-mismatched or missing arguments and fails deep inside the
tool's own logic with an unhelpful error, or worse, executes with a
default-coerced wrong value. Cause, the model constructs the arguments from
natural language, and while the `inputSchema` documents the expected shape
to the model, nothing in the protocol enforces that the model's output
actually conforms before the server receives it. Fix, validate every
incoming `tools/call` argument object against the declared schema inside the
server itself, and return a structured JSON-RPC error rather than allowing
an unvalidated value to reach business logic.

**Assuming a session survives across HTTP requests without checking.**
Symptom, a client's second request after a period of inactivity fails with
an unexpected 404. Cause, the specification permits a Streamable HTTP server
to "terminate the session at any time," after which it "MUST respond to
requests containing that session ID with HTTP 404 Not Found" (Model Context
Protocol, "Transports",
https://modelcontextprotocol.io/specification/2025-06-18/basic/transports,
verified 2026-08-03), and a client that does not check for this response and
re-initialize simply fails the user's request instead of transparently
reconnecting. Fix, implement the documented recovery path. on receiving 404
for a request carrying a session ID, start a fresh session with a new
`InitializeRequest` rather than surfacing the failure.

## 12. Trade-off matrix

| Force | MCP | Plain function calling (single request) | Custom REST integration |
|---|---|---|---|
| Cross-host reuse | High, same server works with any conformant host | None, tied to one provider's request format inside one call | None, tied to one application's integration code |
| Latency for one call | Higher, process boundary plus JSON-RPC framing | Lowest, resolved inside a single model response | Depends on the API, no protocol tax but no standardization either |
| Discoverability | Explicit, `tools/list` and `resources/list` are machine-readable | None beyond what the calling code hardcodes | None beyond whatever documentation the API author wrote |
| Statefulness | Session-based with explicit lifecycle and negotiated capabilities | Stateless, scoped to one request-response turn | Varies per API, usually stateless per request |
| Security surface | Explicit trust boundary per connected server, named in the spec | Bounded to whatever the calling application already trusts | Bounded to whatever the calling application already trusts |
| Operational cost | A process (or endpoint) per server, session management for remote transport | None, no separate process | A deployed service per integration, but teams already do this |
| Best fit | Reusable tools across many hosts or many model providers | A tool used from exactly one call site inside one application | A fixed, known integration that will never be reused elsewhere |

## 13. Related and incompatible patterns

**Function calling.** MCP's tool-invocation mechanism is built directly on
top of function calling. the `tools/call` message and its result are, at the
semantic level, the same request-argument-result shape a model's native
function-calling API uses within a single turn. MCP composes with function
calling rather than replacing it. inside the host, the model still emits a
structured function call exactly as it would for any locally defined tool,
and the host's only extra job is routing that call to the correct connected
MCP server instead of executing it in-process.

**ReAct prompting and plan-execute.** Both reasoning patterns describe how a
model decides which action to take next inside an agent loop. neither
specifies where the tools that get invoked actually live or how the calling
application discovers them. MCP fits naturally underneath either pattern as
the transport for whichever tool the reasoning loop decides to call, and the
two compose cleanly. a ReAct loop's "Act" step and a plan-execute worker's
tool invocation step are both, in an MCP-backed system, a `tools/call`
message sent to whichever connected server owns that capability.

**Orchestrator-worker.** In systems that split a task across multiple
specialized subagents, MCP servers frequently play the role of the shared
capability layer that every worker can reach, rather than each worker
maintaining its own private integration code. The orchestrator pattern
governs how work is divided among agents. MCP governs how each agent, once
given a subtask, actually touches the outside world to complete it.

**Retrieval-augmented generation.** RAG describes retrieving relevant
context and injecting it into a model's prompt before generation. MCP's
resources feature is a natural transport for that retrieval step when the
data source is exposed as an MCP server rather than embedded directly in the
application's own retrieval pipeline, letting the same document store or
vector index be reused by multiple RAG-based applications through one
server. The two are not incompatible, but they answer different questions.
RAG is about what context to include, MCP is about the wire format used to
fetch it from an independently running process.

No pattern in this catalog is fundamentally incompatible with MCP. the
closest thing to a tension is with any architecture that deliberately avoids
process boundaries for latency reasons, where introducing MCP for a purely
in-process concern would work against that architecture's own goal, but this
is a misapplication of MCP rather than a structural incompatibility, and is
already covered under non-applicability in dimension 4.

## 14. Refactoring path in and out

**Introducing MCP into a system that currently hardcodes its integrations.**
Start by identifying one integration a team maintains today as custom glue
code, for example a function that queries an internal ticketing API and is
called directly from the agent's tool-dispatch code. Extract that function's
logic, unchanged, into a small standalone process that speaks the MCP wire
protocol, keeping the extracted server's tool count to one or two while the
pattern is validated. Wire the existing host application to connect to this
new server over stdio during local development, verify the tool's behavior
is identical to the hardcoded version by comparing outputs side by side,
then remove the hardcoded version from the host once the MCP path is proven.
Repeat integration by integration rather than migrating an entire tool
surface in one pass, since each migrated server should be independently
testable and independently revertible. Once more than one integration
exists as an MCP server, and especially once a second host application
wants to reuse one of them, promote the server from a project-local script
to an independently versioned artifact with its own repository and its own
semantic version, since that is the point at which the decoupling MCP buys
actually starts paying for itself.

**Removing MCP when it stops earning its place.** The signal that MCP is no
longer the right choice for a given integration is durable, not transient.
if a server has, over an extended period, never been connected to by more
than the one host it was originally built for, and no plan exists to change
that, the protocol overhead is pure cost with no offsetting reuse benefit.
To remove it, inline the server's tool logic back into the host's own
codebase as a directly-called function, matching argument validation
one-to-one against what the server's `inputSchema` previously enforced so no
behavior is silently lost in the collapse, then retire the subprocess and
its lifecycle management code. This is the direct inverse of the
introduction path and should be done with the same one-integration-at-a-time
discipline, verifying output parity before deleting the old path.

## 15. Testing and verification

Testing an MCP server is testing three layers separately, and conflating
them is the most common mistake. The first layer is the tool logic itself,
which should be testable as a plain function with no protocol involvement at
all, exactly as any other unit under test would be, since a well-factored
server keeps its tool implementations as pure, directly callable functions
that the protocol layer merely wraps. The second layer is schema conformance,
verifying that the server's declared `inputSchema` for each tool actually
matches what the implementation accepts and rejects, which is straightforward
to test by feeding a battery of valid and deliberately invalid argument
objects through the server's own validation path and asserting each is
accepted or rejected as the schema promises. The third layer is protocol
conformance, verifying the server correctly implements the lifecycle
(rejecting requests sent before `initialize` completes), correctly frames
messages for its transport (no stray stdout writes on the stdio transport,
correct SSE framing on Streamable HTTP), and correctly returns the JSON-RPC
error shapes the specification defines rather than leaking a stack trace or
an ad hoc error format.

A test double for the client side is a small stub host that scripts a fixed
sequence of `initialize`, `tools/list`, and `tools/call` messages against
the server under test and asserts on the raw JSON-RPC responses, which is
what the code examples in this entry demonstrate in miniature. Testing the
model's own decision of when to call a tool is a separate, much harder
concern that belongs to evaluation of the agent loop as a whole rather than
to MCP server testing. an MCP server test suite should never need to invoke
a real language model, because the server's contract is with the client
protocol, not with the model's reasoning.

For integration testing across the full stack, the most reliable approach is
running the actual server as a subprocess (for stdio) or against a local
port (for Streamable HTTP) inside the test suite, exactly as production
will, rather than mocking the transport, because the transport-layer bugs
named in dimension 11, stray stdout writes, malformed session handling, are
precisely the class of bug a mocked transport cannot catch.

## 16. Observability signals

A healthy MCP server surfaces, at minimum, per-tool invocation counts,
per-tool latency distribution, and a clear success-versus-error ratio broken
down by the JSON-RPC error code returned, since a server returning a steady
rate of `-32602` (invalid params) errors is telling the team its
`inputSchema` and its actual validation logic have drifted apart, one of the
concrete failure modes named in dimension 11. For a Streamable HTTP server,
session count and session duration are the signals that catch statefulness
problems early. a server whose active session count grows without bound
while its session duration histogram shows sessions rarely closing cleanly
is leaking sessions rather than terminating them per the specification's own
lifecycle rules.

On the client and host side, the signal to watch is time spent inside
`initialize`, since a slow or hanging initialization handshake against one
misbehaving server can stall a host's entire connection sequence if servers
are connected serially rather than in parallel. Logging the negotiated
protocol version per connection is also worth doing explicitly, because a
host silently falling back to an older negotiated version when connecting to
a server it expected to be current is a sign of a deployment mismatch that
otherwise surfaces only as confusing feature-availability bugs much later.
A failing instance typically shows up first as a spike in tool-call error
rate correlated with a specific server's deploy timestamp, which is why
tagging every logged tool call with the server's declared `serverInfo.version`
from its `initialize` response, not just the tool name, makes root-causing a
regression to a specific server release tractable instead of guesswork.

## 17. Security and privacy implications

MCP is one of the rare patterns in this catalog where the specification
itself devotes an entire named section to security, and the implications are
substantial rather than incidental, because every connected server is
granted the ability to see whatever the host chooses to send it and to
return content the model will treat as trustworthy context. The
specification's four stated principles are the baseline any implementation
must meet. explicit user consent before any tool invocation, explicit user
consent before any user data is exposed to a server, hosts must not transmit
resource data elsewhere without consent, and any server-initiated sampling
request must be explicitly approved with the user controlling whether
sampling happens at all, what prompt is sent, and what results the server
can see (Model Context Protocol, "Specification", version 2025-06-18,
"Security and Trust & Safety" section,
https://modelcontextprotocol.io/specification/2025-06-18, verified
2026-08-03).

The privacy implication that follows directly from tool poisoning and
shadowing, both documented in dimension 11, is that connecting to any
third-party MCP server is a decision to expose the model's reasoning process
and, potentially, whatever data the host makes available during that
session, to code the connecting party does not control and, per the
specification's own wording, should not implicitly trust. This is the same
category of risk a team already manages when installing a third-party
library with network access and file-system permissions, and it should be
reviewed with the same rigor, not treated as a lighter-weight decision
because the integration happens to be labeled an MCP server rather than a
dependency.

On the data-handling side, the resources feature means a server can expose
arbitrarily sensitive content (a private document store, a customer
database) directly into a model's context window if the host is configured
to allow it, and because the specification places the consent obligation on
the host rather than enforcing it at the protocol level, a host that skips
building a real consent UI has built an application that silently violates
the specification's own security principles even while being fully
wire-compatible with it. Compliance with the letter of the JSON-RPC message
format is not the same as compliance with the trust model the specification
describes, and a security review of an MCP-based system needs to check both
separately.

## 18. References

1. Anthropic, "Introducing the Model Context Protocol", 25 November 2024,
   https://www.anthropic.com/news/model-context-protocol, verified
   2026-08-03.
2. Model Context Protocol, "Specification", version 2025-06-18,
   https://modelcontextprotocol.io/specification/2025-06-18, verified
   2026-08-03.
3. Model Context Protocol, "Architecture overview",
   https://modelcontextprotocol.io/docs/learn/architecture, verified
   2026-08-03.
4. Model Context Protocol, "Lifecycle",
   https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle,
   verified 2026-08-03.
5. Model Context Protocol, "Transports",
   https://modelcontextprotocol.io/specification/2025-06-18/basic/transports,
   verified 2026-08-03.
6. OpenAI, "Model context protocol (MCP)", Agents SDK documentation,
   https://openai.github.io/openai-agents-python/mcp/, verified 2026-08-03.
7. Microsoft, "Use MCP servers in VS Code", Visual Studio Code
   documentation, https://code.visualstudio.com/docs/copilot/chat/mcp-servers,
   verified 2026-08-03.
8. Invariant Labs, "MCP Security Notification. Tool Poisoning Attacks",
   https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks,
   verified 2026-08-03.

## Code examples

The examples below implement a minimal, dependency-free subset of MCP over
the stdio transport, hand-rolling the JSON-RPC framing exactly as the
specification requires rather than depending on an SDK, so that every line
maps directly back to a specification requirement cited above. All four were
compiled or executed and verified end to end. the Python server was started
as a real subprocess, and the TypeScript and Go clients each completed a
full `initialize`, `tools/list`, `tools/call` exchange against it over real
stdin and stdout pipes, returning the correct sum for a two-argument add
tool. The Rust example demonstrates a different facet, validating a tool
call's arguments against its declared schema before dispatch, the fix
described for the failure mode in dimension 11 about unvalidated arguments.
Java is omitted from this entry because no Java runtime was available in the
verification environment, not because the pattern does not translate. any
JSON-RPC library on the JVM would express the same message shapes shown
here.

A minimal MCP server (Python), implementing `initialize`, `tools/list`, and
`tools/call` for a single `add` tool, reading and writing newline-delimited
JSON-RPC over stdio exactly as the stdio transport requires.

```python
import sys
import json


def send(message: dict) -> None:
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        request = json.loads(line)
        method = request.get("method")
        request_id = request.get("id")

        if method == "initialize":
            send({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "add-server", "version": "1.0.0"},
                },
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            send({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [{
                        "name": "add",
                        "description": "Add two integers",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "a": {"type": "integer"},
                                "b": {"type": "integer"},
                            },
                            "required": ["a", "b"],
                        },
                    }],
                },
            })
        elif method == "tools/call":
            params = request.get("params", {})
            if params.get("name") == "add":
                args = params.get("arguments", {})
                total = int(args.get("a", 0)) + int(args.get("b", 0))
                send({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": str(total)}],
                        "isError": False,
                    },
                })
            else:
                send({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": "unknown tool"},
                })
        elif request_id is not None:
            send({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": "method not found"},
            })


if __name__ == "__main__":
    main()
```

An MCP client (TypeScript) that spawns the server above as a subprocess,
performs the initialization handshake, lists its tools, and calls `add`.
Verified against `tsc --strict --noEmit` with `@types/node`, then run with
`node` against the live Python server, returning the correct sum.

```typescript
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import * as readline from "node:readline";

interface JsonRpcRequest {
  jsonrpc: "2.0";
  id?: number;
  method: string;
  params?: Record<string, unknown>;
}

interface JsonRpcResponse {
  jsonrpc: "2.0";
  id: number;
  result?: unknown;
  error?: { code: number; message: string };
}

class McpStdioClient {
  private nextId = 1;
  private pending = new Map<number, (r: JsonRpcResponse) => void>();
  private server: ChildProcessWithoutNullStreams;

  constructor(serverPath: string) {
    this.server = spawn("python3", [serverPath]);
    const rl = readline.createInterface({ input: this.server.stdout });
    rl.on("line", (line: string) => {
      const msg = JSON.parse(line) as JsonRpcResponse;
      const resolver = this.pending.get(msg.id);
      if (resolver) {
        this.pending.delete(msg.id);
        resolver(msg);
      }
    });
  }

  private call(method: string, params?: Record<string, unknown>): Promise<JsonRpcResponse> {
    const id = this.nextId++;
    const request: JsonRpcRequest = { jsonrpc: "2.0", id, method, params };
    return new Promise((resolve) => {
      this.pending.set(id, resolve);
      this.server.stdin.write(JSON.stringify(request) + "\n");
    });
  }

  private notify(method: string, params?: Record<string, unknown>): void {
    const note: JsonRpcRequest = { jsonrpc: "2.0", method, params };
    this.server.stdin.write(JSON.stringify(note) + "\n");
  }

  async initialize(): Promise<unknown> {
    const res = await this.call("initialize", {
      protocolVersion: "2025-06-18",
      capabilities: {},
      clientInfo: { name: "ts-demo-client", version: "1.0.0" },
    });
    this.notify("notifications/initialized");
    return res.result;
  }

  async listTools(): Promise<unknown> {
    const res = await this.call("tools/list");
    return res.result;
  }

  async callTool(name: string, args: Record<string, unknown>): Promise<unknown> {
    const res = await this.call("tools/call", { name, arguments: args });
    return res.result;
  }

  close(): void {
    this.server.stdin.end();
  }
}

async function main(): Promise<void> {
  const client = new McpStdioClient("./mcp_server.py");
  await client.initialize();
  await client.listTools();
  const result = await client.callTool("add", { a: 40, b: 2 });
  console.log(result);
  client.close();
}

main();
```

A second MCP client (Go), speaking the identical wire protocol to the same
server, demonstrating that MCP's contract lives in the message shapes and
the transport, not in any one language's SDK. Verified with `go vet` and run
with `go run` against the live Python server, returning the correct sum.

```go
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os/exec"
)

type rpcRequest struct {
	JSONRPC string      `json:"jsonrpc"`
	ID      *int        `json:"id,omitempty"`
	Method  string      `json:"method"`
	Params  interface{} `json:"params,omitempty"`
}

type rpcResponse struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      int             `json:"id"`
	Result  json.RawMessage `json:"result,omitempty"`
	Error   *struct {
		Code    int    `json:"code"`
		Message string `json:"message"`
	} `json:"error,omitempty"`
}

type mcpClient struct {
	stdin  *bufio.Writer
	stdout *bufio.Reader
	nextID int
}

func newClient(serverPath string) (*mcpClient, error) {
	cmd := exec.Command("python3", serverPath)
	stdinPipe, err := cmd.StdinPipe()
	if err != nil {
		return nil, err
	}
	stdoutPipe, err := cmd.StdoutPipe()
	if err != nil {
		return nil, err
	}
	if err := cmd.Start(); err != nil {
		return nil, err
	}
	return &mcpClient{
		stdin:  bufio.NewWriter(stdinPipe),
		stdout: bufio.NewReader(stdoutPipe),
		nextID: 1,
	}, nil
}

func (c *mcpClient) call(method string, params interface{}) (*rpcResponse, error) {
	id := c.nextID
	c.nextID++
	req := rpcRequest{JSONRPC: "2.0", ID: &id, Method: method, Params: params}
	line, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}
	if _, err := c.stdin.Write(append(line, '\n')); err != nil {
		return nil, err
	}
	if err := c.stdin.Flush(); err != nil {
		return nil, err
	}
	respLine, err := c.stdout.ReadString('\n')
	if err != nil {
		return nil, err
	}
	var resp rpcResponse
	if err := json.Unmarshal([]byte(respLine), &resp); err != nil {
		return nil, err
	}
	return &resp, nil
}

func (c *mcpClient) notify(method string, params interface{}) error {
	req := rpcRequest{JSONRPC: "2.0", Method: method, Params: params}
	line, err := json.Marshal(req)
	if err != nil {
		return err
	}
	if _, err := c.stdin.Write(append(line, '\n')); err != nil {
		return err
	}
	return c.stdin.Flush()
}

func main() {
	client, err := newClient("./mcp_server.py")
	if err != nil {
		panic(err)
	}

	initRes, err := client.call("initialize", map[string]interface{}{
		"protocolVersion": "2025-06-18",
		"capabilities":    map[string]interface{}{},
		"clientInfo":      map[string]interface{}{"name": "go-demo-client", "version": "1.0.0"},
	})
	if err != nil {
		panic(err)
	}
	fmt.Println("initialize:", string(initRes.Result))

	if err := client.notify("notifications/initialized", nil); err != nil {
		panic(err)
	}

	listRes, err := client.call("tools/list", nil)
	if err != nil {
		panic(err)
	}
	fmt.Println("tools/list:", string(listRes.Result))

	callRes, err := client.call("tools/call", map[string]interface{}{
		"name":      "add",
		"arguments": map[string]interface{}{"a": 40, "b": 2},
	})
	if err != nil {
		panic(err)
	}
	fmt.Println("tools/call:", string(callRes.Result))
}
```

Argument-schema validation (Rust), demonstrating the fix for the
unvalidated-argument failure mode from dimension 11. a server rejects a
`tools/call` before it reaches the tool's own logic when the arguments do
not match the declared schema's types. Compiled with `rustc --edition 2021`
and run, correctly accepting a well-typed call and rejecting a
mistyped one before dispatch.

```rust
use std::collections::HashMap;

enum ArgType {
    Integer,
    Text,
}

struct ToolSchema {
    name: &'static str,
    required: Vec<(&'static str, ArgType)>,
}

enum SchemaError {
    MissingField(String),
    WrongType(String),
}

enum Value {
    Int(i64),
    Str(String),
}

fn validate(schema: &ToolSchema, args: &HashMap<&str, Value>) -> Result<(), SchemaError> {
    for (field, expected) in &schema.required {
        match args.get(field) {
            None => return Err(SchemaError::MissingField((*field).to_string())),
            Some(Value::Int(_)) if matches!(expected, ArgType::Integer) => {}
            Some(Value::Str(_)) if matches!(expected, ArgType::Text) => {}
            Some(_) => return Err(SchemaError::WrongType((*field).to_string())),
        }
    }
    Ok(())
}

fn describe(result: &Result<(), SchemaError>, tool: &str) -> String {
    match result {
        Ok(()) => format!("tool '{tool}' accepted: arguments match the declared schema"),
        Err(SchemaError::MissingField(f)) => format!("tool '{tool}' rejected: missing '{f}'"),
        Err(SchemaError::WrongType(f)) => format!("tool '{tool}' rejected: '{f}' has the wrong type"),
    }
}

fn main() {
    let add_schema = ToolSchema {
        name: "add",
        required: vec![("a", ArgType::Integer), ("b", ArgType::Integer)],
    };

    let mut good_args: HashMap<&str, Value> = HashMap::new();
    good_args.insert("a", Value::Int(40));
    good_args.insert("b", Value::Int(2));
    println!("{}", describe(&validate(&add_schema, &good_args), add_schema.name));

    let mut bad_args: HashMap<&str, Value> = HashMap::new();
    bad_args.insert("a", Value::Str("forty".to_string()));
    println!("{}", describe(&validate(&add_schema, &bad_args), add_schema.name));
}
```
