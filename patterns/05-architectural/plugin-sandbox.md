---
name: Plugin Sandbox
slug: plugin-sandbox
family: 05-architectural
category: Architectural
aliases: [Extension Sandbox, Addon Isolation, Untrusted Plugin Boundary, Capability-Based Extension Isolation]
first_described: "Emerged from practice across browser, editor, and platform engineering rather than a single catalog; theoretical grounding in Jack B. Dennis and Earl C. Van Horn, Programming Semantics for Multiprogrammed Computations, Communications of the ACM 9(3), 1966"
maturity: established
related: [plugin-architecture, microkernel, broker-architecture, proxy, facade, bulkhead, circuit-breaker, dependency-injection, mediator, command]
incompatible_with: [singleton, god-object]
verified: 2026-08-02
---

# Plugin Sandbox

## 1. Name, aliases, and lineage

The name used across this catalog is Plugin Sandbox. It does not come from a
single book the way Factory Method comes from the Gang of Four or Microkernel
comes from Pattern-Oriented Software Architecture. It is a pattern the
industry converged on independently, in browsers, in editors, in cloud
runtimes, and in game engines, because the same shape of problem, running
someone else's code without trusting them, showed up in each of those places
and produced structurally the same answer. Names in production use for the
same idea include Extension Sandbox (Chrome, Firefox extension
documentation), Addon Isolation (Mozilla's add-on security writing), Untrusted
Plugin Boundary, and Capability-Based Extension Isolation (used in platform
teams that build their sandbox around an explicit capability object rather
than a coarse permission string).

Two separate lineages feed the pattern and it helps to keep them apart,
because conflating them is the single most common design mistake in this
space.

The first lineage is theoretical and comes from operating systems research.
Jack B. Dennis and Earl C. Van Horn's 1966 paper, Programming Semantics for
Multiprogrammed Computations, published in Communications of the ACM volume
9, issue 3, pages 143 to 155
([ACM Digital Library, DOI 10.1145/365230.365252](https://dl.acm.org/doi/10.1145/365230.365252),
verified 2026-08-02), introduced capabilities as unforgeable tokens that both
name a resource and carry the rights to act on it. A capability is not a
password checked against an access-control list at the moment of use. It is
the permission itself, held by the caller, and a caller that never received
the capability has no path to the resource at all. This idea, no ambient
authority, only what you were explicitly handed, is the security theory
underneath every serious plugin sandbox built since, whether the
implementers cite Dennis and Van Horn by name or arrived at the same shape by
trial and error.

The second lineage is practical and comes from the extension-point
architectures this pattern is almost always paired with. Plugin Architecture
and Microkernel, both traced in Frank Buschmann, Regine Meunier, Hans
Rohnert, Peter Sommerlad, and Michael Stal, Pattern-Oriented Software
Architecture Volume 1, Wiley, 1996, describe how a host application defines
extension points that third-party code fills in. Neither of those catalog
entries addresses what happens when the third party filling in the extension
point cannot be trusted, and the growth of plugin marketplaces (browser
extension stores, editor marketplaces, CMS plugin directories) turned that
gap from a theoretical concern into the largest attack surface most of these
platforms have. Plugin Sandbox is the answer that emerged. keep the
extension-point structure from Plugin Architecture, and wrap the actual
execution of the plugin's code in a boundary derived from capability theory.

A separate, well-documented mechanism sometimes gets called a sandbox and
is worth naming here so it is not confused with this pattern. The Java
platform once offered a SecurityManager, a runtime access-control mechanism
that could restrict what a piece of loaded code was allowed to do. It has
been deprecated for removal since Java 17 under JEP 411, on the stated
grounds that it "has not been the primary means of securing client-side Java
code for many years, has rarely been used to secure server-side code, and is
costly to maintain" ([OpenJDK, JEP 411. Deprecate the Security Manager for
Removal](https://openjdk.org/jeps/411), verified 2026-08-02), and JEP 486
proposes disabling it entirely so it can no longer be enabled at all
([OpenJDK, JEP 486. Permanently Disable the Security Manager](https://openjdk.org/jeps/486),
verified 2026-08-02). The SecurityManager approach, a global, ambient policy
checked at the point of a dangerous operation, is the opposite design
philosophy from a capability object handed to the plugin at the point of
creation, and its industry-wide retirement is itself evidence for which
approach the field settled on.

## 2. Problem and context

A host application defines an extension point, using Plugin Architecture or
Microkernel, so that its behavior can grow without every new feature being
merged into the core codebase. That decision solves a modularity problem. It
does not solve a trust problem, and the trust problem is where most of the
damage in real systems happens.

The concrete situation looks like this. A code editor lets anyone publish an
extension to a public marketplace. A note-taking application lets anyone
publish a community plugin. A design tool lets anyone publish a plugin that
runs when a designer opens a file. A serverless platform lets any customer
upload a function that runs on shared infrastructure. In every one of these
cases, the party whose code is about to run is not the same party who owns
the runtime, and the runtime owner has no way to fully review every line of
every submission before it ships, because the whole value of an open
ecosystem is that submissions arrive faster than any review team can read
them.

If the plugin is simply loaded into the same process, given the same
privileges as the host, and invoked, then a single malicious or careless
plugin author has everything the host has. It can read the file system the
host can read, including other users' data if the host process holds it. It
can make network calls the host can make, including calls to internal
services the host talks to. It can crash the host process, taking down every
other plugin that happened to be running alongside it. It can read memory
belonging to other plugins if they share the same address space. None of
this requires a bug in the host. It requires only that the plugin author had
a reason, malicious or accidental, to do one of these things, and nothing in
the architecture stopped them.

The context that calls for Plugin Sandbox has three parts that need to hold
together.

- Code from an author the host does not fully control is going to execute,
  and the host cannot review every submission before it runs, whether
  because the ecosystem is open, because the volume is too high, or because
  the code is generated at runtime rather than published in advance (a
  formula in a spreadsheet, a webhook handler written by an end user, code
  an AI agent produced a moment earlier).
- The host has something worth protecting that the plugin should not get
  by default, whether that is other users' data, other plugins' state, the
  host's own credentials, or simply the stability of the process.
- The plugin still needs to do real work. A sandbox that grants nothing is
  not a sandbox, it is a refusal to have a plugin system at all, so the
  pattern only earns its cost when there is a genuine, useful, narrower set
  of operations the plugin can be given instead of everything.

## 3. Forces

The forces below are largely a matter of engineering judgement drawn from
building and operating these systems, not a single citable theorem, though
several of the specific tensions are documented in the production sources
cited throughout this entry.

- Functionality against confinement. A plugin that can do nothing is safe
  and useless at the same time. Every capability the host adds to make the
  plugin more useful is also a capability that a malicious plugin could
  misuse, so the design work is not "add security" as a separate step, it is
  choosing, deliberately, which specific operations earn their place in the
  capability surface.
- Isolation strength against performance. A boundary that is only a
  message-passing contract between two objects in the same process is
  nearly free to cross and easy to escape by a determined attacker. A
  boundary that is a full virtual machine per plugin is close to
  unescapable and correspondingly expensive to spin up, to communicate
  across, and to run at scale. Real systems sit at different points on this
  line depending on how untrusted the code actually is, and the correct
  point is not the same for a first-party feature flag and for
  arbitrary user-uploaded code.
- Compatibility against restriction. The narrower the capability surface, the
  more legitimate use cases it accidentally blocks, and the pressure that
  creates is not abstract, it shows up as plugin authors asking users to
  disable the sandbox, or as a platform quietly widening its own API surface
  under demand until the sandbox stops meaning much. Obsidian's own
  documentation states plainly that a user should only disable its
  Restricted Mode, the setting that gates whether community plugins can run
  at all, "if you trust the authors of the plugins that you install"
  ([Obsidian, Plugin security](https://obsidian.md/help/plugin-security),
  verified 2026-08-02), which is an honest admission that once the mode is
  off, trust rather than the sandbox is doing the protecting.
- Debuggability against isolation. The stronger the boundary, the harder it
  is to get a stack trace, a heap snapshot, or a step-through debugger
  across it, because those tools were built assuming shared memory and a
  single process. A team that adopts a strong sandbox is also signing up
  for a harder debugging story, and underestimating that cost is a common
  reason sandboxes get watered down later.
- Blast-radius reduction against build and operating cost. Every additional
  layer, a broker process, a manifest review step, a permission-prompt UI, a
  supervisor that restarts crashed plugin instances, is more code the host
  team has to write, test, and keep working, and it is code that exists
  purely to contain a threat that, for any single plugin, may never
  materialize. The cost is certain and paid up front. The benefit is
  probabilistic and paid, if ever, much later.
- Usability against least privilege. The theoretically correct move, per
  Dennis and Van Horn's original framing, is to hand a plugin exactly the
  capabilities it needs and nothing more, checked once at grant time rather
  than repeatedly at use time. In practice, asking a human to approve each
  narrow capability one at a time produces prompt fatigue, and the practical
  answer, seen in Deno's model, is to group capabilities coarsely enough
  that a person will actually read the prompt rather than reflexively
  clicking through it
  ([Deno, Security](https://docs.deno.com/runtime/fundamentals/security/),
  verified 2026-08-02).

## 4. Applicability and non-applicability

Reach for Plugin Sandbox when most of the following hold at once.

- The code about to run was authored by a party the host does not fully
  control, and the host cannot read and approve every submission before it
  runs, whether because the ecosystem is open (a public marketplace), the
  volume is too high (a multi-tenant platform), or the code did not exist
  until moments before execution (an AI agent's generated function, a
  user's spreadsheet formula, a webhook body).
- The host has data, credentials, or other tenants' state that a compromised
  or careless plugin should not be able to reach, and the cost of one
  plugin reaching it is high enough to justify the sandbox's overhead.
- A useful, narrower set of operations exists that the plugin can be handed
  instead of full host privileges, so the sandbox is actually confining
  something rather than being a formality that wraps an API surface which
  is already as wide as the host itself.
- The host needs to survive an individual plugin crashing, hanging, or
  consuming unbounded resources, independent of whether that plugin is
  actively malicious.

Do not reach for Plugin Sandbox, and this non-applicability list is the part
most catalog entries skip, when any of the following hold.

- All extension code is first-party, written by the same team, reviewed
  through the same code review process, and shipped through the same
  release pipeline as the host itself. In that case the trust boundary the
  sandbox exists to enforce has already collapsed to zero, because the
  people who could misuse the plugin's access are the same people who could
  have introduced the same misuse directly into the host. Plugin
  Architecture alone, without a runtime sandbox, is the right amount of
  structure here, and adding a sandbox only buys latency and debugging pain
  for a threat that does not exist in this configuration.
- The extension needs low-latency, fine-grained access to host internals
  that cannot be expressed through any coarse, stable API, the kind of
  access a compiler optimization pass or a database storage engine plugin
  needs into internal data structures on every call. Forcing that access
  through a message-passing boundary either makes the boundary so
  permissive it stops meaning anything, or makes it too slow to be usable,
  and in both outcomes the sandbox has failed at its actual job while still
  charging its full cost.
- The workload is hard real-time or otherwise cannot tolerate the added
  latency of a boundary crossing at all. Audio plugin hosts built on formats
  such as VST are the clearest example of this outside the software-only
  world. those plugins are loaded as shared libraries directly into the
  host's own process and audio thread specifically because an inter-process
  message hop, on the order of microseconds of budget per audio buffer,
  cannot be afforded, and the entire ecosystem instead relies on plugin
  vendor reputation and manual host-side vetting rather than a runtime
  boundary.
- The plugin count is small, single-digit, and every plugin author is known,
  vetted, and contractually accountable to the platform operator. Code
  signing plus a manual review at publish time is cheaper than building and
  operating sandbox infrastructure, and it closes the same gap for this
  narrower case, though it does not scale to an open marketplace the way a
  runtime boundary does.
- The "plugin" is a personal automation that never leaves the author's own
  account and data, such as a private macro a single user writes for their
  own document, and no other user or system resource is reachable through
  it even in the worst case. This is a weaker exclusion than the others,
  because defense in depth is still a reasonable argument for a lightweight
  boundary even here, but the cost-benefit case for a full sandbox is
  markedly thinner when the blast radius was already limited to one
  person's own data before the sandbox existed.

## 5. Structure

- Host. The trusted application. It owns the real data, the real network
  access, and the real file system, and it is the only participant with
  ambient authority over any of it.
- Plugin. Code supplied by a party the host does not fully control. It may
  be fully untrusted, semi-trusted with a declared publisher identity, or
  trusted but fallible, and the strength of the boundary should track which
  of those three it actually is.
- Sandbox boundary. The mechanism that actually enforces separation between
  host and plugin. an operating system process, a V8 isolate, a WebAssembly
  instance, a restricted interpreter, or a full virtual machine. This is the
  one participant whose identity varies the most across implementations,
  and dimension 8 works through the real choices.
- Capability object, or host API. The deliberately narrow set of operations
  the host exposes to the plugin, expressed as concrete functions or
  message types rather than as a general-purpose interpreter of host
  internals. This is the mediation layer that turns Dennis and Van Horn's
  abstract capability into something an engineer actually builds.
- Bridge, or message channel. The marshaling and transport layer that
  carries a capability call across the boundary and carries its result
  back. a pipe, a WebSocket, `postMessage`, a gRPC connection, a shared
  message queue. Every value that crosses this channel is copied or
  proxied, never a live reference into host memory, and dimension 17
  returns to why that specific rule matters.
- Manifest, or policy. A declaration, checked before or at the moment a
  boundary is created, of which capabilities a given plugin is asking for.
  The manifest is what turns "we built a sandbox" into "we can reason about
  what any given plugin can do without reading its code."
- Broker, or supervisor. The component that creates the boundary, injects
  only the granted capabilities into it, watches it for crashes, hangs, or
  resource exhaustion, and tears it down or restarts it. In a subprocess
  design this is literally the parent process managing a child; in a
  browser it is the extension platform managing an isolated world or an
  iframe.
- Result channel. The path by which the plugin's output, not its capability
  calls but its actual return value or emitted effect, re-enters the host.
  This channel deserves the same scrutiny as the capability channel,
  because a plugin that cannot read a secret directly can sometimes still
  leak it by encoding it into an otherwise innocuous return value.

## 6. ASCII structure diagram

```
+----------------------------------------------------------------------+
|                              Host                                    |
|                                                                       |
|   +---------------+        +----------------+       +-------------+ |
|   |   Manifest /   |------->|    Broker /    |------>|  Capability | |
|   |    Policy      |        |   Supervisor   |       |    Object   | |
|   +---------------+        +--------+-------+       +------+------+ |
|                                      |                       ^        |
|                                      | creates                |        |
|                                      v                       |        |
+----------------------------------------------------------------------+
                                       |                       |
                              Sandbox boundary          injected at
                          (process / isolate / VM)      creation time
                                       |                       |
+----------------------------------------------------------------------+
|                             Plugin                                    |
|                                                                        |
|   +-----------------------------------------------------------+       |
|   |             Plugin code (untrusted / semi-trusted)         |       |
|   |                                                             |       |
|   |    caps.readSetting("theme") ---------------+               |       |
|   |                                              |               |       |
|   +----------------------------------------------|---------------+       |
|                                                    |                     |
+----------------------------------------------------------------------+
                                                     |
                                            Message / RPC channel
                                                     |
                                                     v
                                         (crosses back to Broker,
                                          validated against Manifest,
                                          result returned via same
                                          channel, never a live
                                          reference into Host memory)
```

## 7. Dynamics

The lifecycle of a single plugin instance runs through five distinct phases,
and most of the security-relevant bugs in real sandboxes trace back to one
phase being skipped or done out of order.

```
1. Registration
   Plugin declares required capabilities in its manifest.
   Host (or the end user) reviews and approves the manifest,
   once, before any plugin code runs.

2. Boundary creation
   Broker spawns the sandbox boundary. a new OS process,
   a new isolate, a new WASM instance, a new VM.
   No plugin code has executed yet.

3. Capability injection
   Broker constructs a capability object containing only
   the operations the approved manifest allows, and hands
   it to the plugin as the ONLY channel back to the host.
   The plugin receives no ambient reference to host state.

4. Invocation loop
   Host calls into the plugin's entry point across the
   boundary.
   Plugin runs; when it needs a host operation, it sends a
   capability call across the message channel.
   Broker receives the call, checks it against the granted
   manifest (defense in depth even though the capability
   object should already prevent unauthorized calls),
   executes it on the plugin's behalf, marshals the result,
   sends it back.
   Loop continues for the life of the plugin invocation.

5. Teardown
   Plugin invocation completes, times out, crashes, or is
   explicitly killed by the broker for misbehavior.
   Broker destroys the boundary and reclaims its resources.
   Broker logs the grant, deny, and lifecycle events from
   this run for later audit (dimension 16).
```

The invocation loop in phase 4 is where the pattern earns its keep or
fails, because it is the only phase that repeats many times per plugin run.
Figma's plugin platform is a clean illustration of the shape. plugin code
runs in a sandboxed main-thread environment with no direct browser API
access, and if the plugin needs a browser API or wants to render a custom
interface, it must explicitly create an `<iframe>`, at which point "the main
thread and the iframe can communicate with each other through message
passing," which is exactly the bridge described in dimension 5
([Figma, How plugins run](https://developers.figma.com/docs/plugins/how-plugins-run/),
verified 2026-08-02). Network access in that same platform is checked at the
capability boundary rather than left to the plugin's own discretion. "If
your plugin attempts to access a domain that isn't specified in your
plugin's manifest, Figma blocks that attempt and returns a content-security
policy error" (same source), which is the manifest-time declaration from
phase 1 being enforced again at call time in phase 4, a second check that
costs little and catches the case where a bug in the capability object
itself would otherwise have let a call through.

## 8. Implementation variants

No single mechanism defines this pattern. What varies across the real
production systems below is which layer of the stack actually enforces the
boundary, and that choice determines both the isolation strength and the
performance cost from dimension 3.

- Operating system process isolation. The broker spawns the plugin as a
  child process and communicates over a pipe, a socket, or an RPC library.
  HashiCorp's go-plugin is the clearest documented example. it works "by
  launching subprocesses and communicating over RPC," and because each
  plugin is its own process, "a panic in a plugin doesn't panic the plugin
  user," and "the plugin only has access to the interfaces and args given to
  it, not to the entire memory space of the process"
  ([HashiCorp, go-plugin README](https://github.com/hashicorp/go-plugin),
  verified 2026-08-02). This is the pattern behind Terraform's provider
  model, Vault's secrets and auth plugins, Packer, Nomad, Boundary, and
  Waypoint, per the same source. It is also the shape of the Language
  Server Protocol, where an editor spawns a language server as a child
  process and talks to it over stdio. It gives real memory isolation and
  crash containment cheaply, but it does not by itself restrict what the
  child process can do at the operating system level, an important
  distinction returned to in dimension 11.
- Restricted process privileges layered on top of a subprocess. The same
  subprocess boundary above, hardened further with operating-system
  mechanisms that drop what the child process is allowed to do even if its
  code is fully malicious. seccomp filters restricting which system calls
  are available, Linux namespaces restricting what filesystem and network
  paths are visible, and dropped capabilities restricting privileged
  operations. Cloudflare layers exactly this on top of its isolate boundary
  for one class of Workers, using "Linux namespaces and seccomp to prohibit
  all access to the filesystem and network," so that a sandboxed process
  "can only communicate via local UNIX domain sockets"
  ([Cloudflare, Security model](https://developers.cloudflare.com/workers/reference/security-model/),
  verified 2026-08-02).
- In-process execution-context isolation. The plugin runs in the same operating
  system process as the host, but in a separate JavaScript execution context,
  global object, or V8 isolate, so it does not share memory or global state
  with the host's
  own code even though it shares an address space. Cloudflare Workers is
  the production-scale example. "V8 executes code inside isolates, which
  prevent that code from accessing memory outside the isolate, even within
  the same process," which is what lets a single machine run "thousands of
  tenant applications" (same source above). Chrome content scripts use a
  related idea called an isolated world, "a private execution environment
  that isn't accessible to the page or other extensions," where "JavaScript
  variables in an extension's content scripts are not visible to the host
  page or other extensions' content scripts"
  ([Chrome for Developers, Content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts),
  verified 2026-08-02).
- Custom restricted interpreter with no browser or Node bindings. Rather
  than reuse a general-purpose JavaScript engine and try to strip its
  ambient authority after the fact, the host runs plugin code inside a
  minimal engine that never had filesystem, network, or `require` access to
  begin with. Figma's plugin main thread runs exactly this shape, described
  as "a minimal JavaScript environment without direct browser API access"
  (Figma source above). The advantage over stripping a general engine is
  that there is no ambient capability to accidentally leave reachable,
  because it was never implemented in the first place.
- Iframe or Worker separation for any code that does need real browser
  APIs. When a plugin genuinely needs the DOM, `fetch`, or other browser
  capabilities that a minimal engine deliberately omits, the host isolates
  that code inside its own browsing context, an `<iframe>` or a Worker,
  which the browser itself keeps in a separate execution context from the host page and
  which can only communicate back through explicit message passing. This is
  the second half of Figma's architecture, paired with the restricted
  main-thread interpreter above.
- WebAssembly with a capability-based system interface. The plugin is
  compiled to WebAssembly, which by design "starts with no ambient
  authority and can only do what the host explicitly grants"
  ([WASI, wasi.dev](https://wasi.dev/), verified 2026-08-02). This is
  distinct from the language-level restriction above, because the
  restriction is enforced by the instruction set itself, a WASM module has
  no instruction that reaches outside its own linear memory except through
  imported functions the host chose to provide, which makes the capability
  surface an explicit, auditable list of imports rather than something that
  has to be verified by reading every line of interpreter source.
- Compile-time capability types, for trusted-but-fallible code compiled into
  the same binary. Where the concern is a well-intentioned bug rather than
  active malice, and the plugin is statically linked rather than loaded at
  runtime, a language's own type system can enforce the same
  no-ambient-authority discipline at compile time. Rust's cap-std project is
  explicit about both the technique and its limit. it is "a capability-based
  version of the Rust standard library" where a function that receives a
  `Dir` capability "declares its intent to only open files underneath that
  Dir," and the library itself states plainly that it "is not a sandbox for
  untrusted Rust code, as untrusted Rust code could use unsafe or the
  unsandboxed APIs in std.fs"
  ([bytecodealliance/cap-std README, GitHub](https://github.com/bytecodealliance/cap-std),
  verified 2026-08-02). This variant belongs in the trusted-but-fallible
  cell of the matrix, never the adversarial one, and cap-std's own
  documentation is unusually direct about saying so.
- Hardware-assisted virtual machine per tenant, for the strongest isolation
  the pattern offers. AWS Lambda's newer per-invocation isolation runs each
  tenant's code in its "own dedicated MicroVM with no shared kernel and no
  shared resources between users," built on Firecracker, described as
  purpose-built "for creating and managing secure, multi-tenant container
  and function-based services"
  ([AWS, Run isolated sandboxes with full lifecycle control. AWS Lambda
  introduces MicroVMs](https://aws.amazon.com/blogs/aws/run-isolated-sandboxes-with-full-lifecycle-control-aws-lambda-introduces-microvms/),
  verified 2026-08-02;
  [Firecracker project site](https://firecracker-microvm.github.io/),
  verified 2026-08-02). AWS names AI coding assistants and interactive code
  environments explicitly as the target use case, which places
  agent-generated code squarely inside the applicability list from
  dimension 4.
- Subprocess plus scoped, string-level capability grants. Deno runs plugin
  or script code as an ordinary operating system process with none of the
  execution-context or virtualization tricks above, and instead relies entirely on a
  runtime permission check before any sensitive system call. by default "a
  program run with Deno has no access to sensitive APIs, such as file
  system access, network connectivity, or environment access," and every
  permission can be scoped to a specific resource, `--allow-net=example.com`
  rather than blanket network access
  ([Deno, Security](https://docs.deno.com/runtime/fundamentals/security/),
  verified 2026-08-02). This is the cheapest variant to build, because it
  needs no separate execution context or virtualization layer, at the cost of relying
  on the runtime's own interpreter having no escape hatch that bypasses the
  permission check, which is a materially weaker guarantee than a
  hardware- or instruction-set-enforced boundary.

## 9. Known production uses

- **Visual Studio Code's Extension Host.** VS Code runs extensions in a
  process separate from the main editor UI process specifically so that
  extensions "cannot impact startup performance, slow down UI operations,
  or modify the UI" directly, with local, web, and remote variants of the
  host process depending on where the extension needs to run
  ([Microsoft, VS Code Extension Host](https://code.visualstudio.com/api/advanced-topics/extension-host),
  verified 2026-08-02). This is a process-separation variant primarily
  aimed at stability and performance containment rather than a fully
  adversarial security boundary, and it is a useful reference point for how
  far a host can get with process isolation alone before adding stronger
  guarantees.
- **Figma's plugin runtime.** Plugin logic runs in a restricted main-thread
  interpreter with no browser API access, and any code that needs the DOM
  or network beyond a manifest-declared allowlist runs in a separate
  `<iframe>` reached only through message passing
  ([Figma, How plugins run](https://developers.figma.com/docs/plugins/how-plugins-run/),
  verified 2026-08-02).
- **Google Chrome's extension content scripts.** Every extension's content
  script executes in its own isolated world, a private JavaScript
  environment invisible to the host page and to other extensions, sharing
  only the DOM, with all cross-context communication routed through
  `postMessage` or explicit message passing
  ([Chrome for Developers, Content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts),
  verified 2026-08-02).
- **Cloudflare Workers.** Each Worker executes inside its own V8 isolate,
  memory-isolated from every other tenant's isolate even within a shared
  process, with an additional layer of Linux namespace and seccomp
  restriction for one class of Workers, and workers further grouped into
  trust-level cordons that separate free-tier from enterprise workloads on
  different hosts
  ([Cloudflare, Security model](https://developers.cloudflare.com/workers/reference/security-model/),
  verified 2026-08-02).
- **AWS Lambda MicroVMs.** Each execution session for user- or AI-supplied
  code runs in a dedicated Firecracker microVM with no shared kernel and no
  shared resources between tenants, aimed explicitly at multi-tenant
  applications that need to hand each end user their own execution
  environment
  ([AWS Lambda MicroVMs launch blog](https://aws.amazon.com/blogs/aws/run-isolated-sandboxes-with-full-lifecycle-control-aws-lambda-introduces-microvms/),
  verified 2026-08-02).
- **HashiCorp's plugin ecosystem.** Terraform, Vault, Packer, Nomad,
  Boundary, and Waypoint all load their respective plugins as separate
  subprocesses communicating over RPC or gRPC through the shared go-plugin
  library, so that a plugin panic cannot crash the host and a plugin has
  access only to the interfaces and arguments it was explicitly handed
  ([HashiCorp go-plugin README](https://github.com/hashicorp/go-plugin),
  verified 2026-08-02).
- **Deno's script and permission model.** Any Deno-run script, including
  scripts used as plugins or extension points inside a larger Deno-based
  tool, starts with zero access to the filesystem, network, environment
  variables, or subprocess execution until a specific, scopeable permission
  is granted
  ([Deno, Security](https://docs.deno.com/runtime/fundamentals/security/),
  verified 2026-08-02).

## 10. Consequences

**Positive.**

- Blast-radius containment. A single compromised or defective plugin is
  confined to the capabilities it was actually granted, so a marketplace of
  thousands of unreviewed submissions does not require thousands of
  security audits, only one correctly implemented boundary and one review
  per manifest.
- Least privilege becomes structural rather than aspirational. A plugin
  cannot exceed its granted capabilities by accident, because there is no
  path to do so, which is a materially stronger property than a code
  review process that hopes reviewers caught every misuse.
- Crash and resource containment travels with the same boundary that
  provides the security isolation, in most of the process- and
  isolate-based variants, so a plugin that hangs, leaks memory, or throws
  an unhandled exception degrades only itself rather than the host or
  sibling plugins.
- The same plugin binary can be run at different trust levels on different
  installs, granting a broader capability set to a plugin the operator has
  personally vetted and a narrower one to the same plugin downloaded from
  an anonymous marketplace listing, without changing a line of the
  plugin's own code.
- Revocable, auditable grants. Because every capability crossing is
  mediated by the broker, every grant and every denial can be logged with
  the plugin's identity attached, turning "what can this plugin do" from a
  question that requires reading its source into a question answered by a
  log query, which dimension 16 returns to.

**Negative.**

- Latency and throughput cost. Every boundary crossing pays for
  serialization, a context switch or an inter-process hop, and, in the
  strongest variants, a full virtual machine's scheduling overhead. A
  plugin call pattern designed for in-process latencies, one call per
  keystroke, becomes a real performance problem once it crosses a
  process or VM boundary on every call.
- The host API surface becomes a long-lived compatibility liability. Once a
  capability is exposed to plugins, removing it later breaks every plugin
  that depends on it, an instance of the same forces behind Hyrum's Law,
  and the practical effect is that a host's capability surface tends to
  only grow over time even when individual capabilities turn out to have
  been mistakes.
- Debugging and observability across the boundary is materially harder than
  in-process debugging, because stack traces, breakpoints, and profilers
  built for a single process do not follow execution across a process,
  isolate, or VM boundary without deliberate tooling investment.
- A partially implemented boundary is worse than an honestly absent one,
  because it creates a false sense of security. Code that looks isolated,
  because it runs "in a sandbox" by name, but still shares a mutable object
  reference, a global variable, or an unfiltered system call with the host,
  gives the host team the confidence of a real boundary without its
  guarantees, and dimension 11 works through exactly this failure mode.
- Sandbox implementations themselves become a security-critical component
  and therefore a target, and history across browsers, JavaScript engines,
  and container runtimes shows that boundary implementations accumulate
  their own vulnerability history over time, meaning the sandbox is not a
  one-time cost but an ongoing maintenance and patching obligation for as
  long as the platform runs untrusted code.
- Development and operational cost. A broker, a manifest schema and review
  workflow, a capability object, a marshaling layer, and, in many designs, a
  permission-prompt user interface are all new components the host team
  must build, test, and keep working, on top of whatever the plugin system
  would have cost without the sandbox.

## 11. Failure modes and misuse

This dimension draws heavily on documented practice and known escape
techniques rather than a single citable source, though several of the
specific symptoms below are grounded in the production sources cited
elsewhere in this entry.

- Symptom. A plugin marked as "sandboxed" is found, sometimes years after
  launch, to have full access to the host's filesystem, network, or
  process control the entire time. Cause. The implementers mistook a
  generic scripting engine feature, module-level code separation, a
  restricted global object, an `eval`-based sub-context, for an actual
  security boundary. Node's own documentation is explicit about exactly
  this trap for one such mechanism. "The `node.vm` module is not a security
  mechanism. Do not use it to run untrusted code"
  ([Node.js, VM (executing JavaScript)](https://nodejs.org/api/vm.html),
  verified 2026-08-02). Obsidian's own security page names the same gap
  honestly rather than papering over it, stating that "Due to technical
  limitations, Obsidian cannot reliably restrict plugins to specific
  permissions or access levels," so that community plugins "inherit
  Obsidian's access levels" including the ability to "access files on your
  computer," "connect to internet," and "install additional programs"
  ([Obsidian, Plugin security](https://obsidian.md/help/plugin-security),
  verified 2026-08-02). Fix. Treat "runs in a Worker" or "runs in a vm
  context" as necessary but not sufficient. Verify the boundary against the
  specific mechanism's own documented guarantees, not against its name, and
  where the runtime's own documentation says a mechanism is not a security
  boundary, believe it.
- Symptom. A boundary that passed every functional and security test during
  development is escaped in production by a plugin walking a chain of
  object references it was never explicitly handed. Cause. A live host
  object, rather than a copy or a scoped proxy, was passed across the
  boundary at some point, often unintentionally through a closure or a
  shared mutable data structure, and the plugin followed a reference chain,
  a classic example in JavaScript sandboxes being `constructor.constructor`
  reached from an apparently inert object, until it recovered access to a
  global or a host function it should never have reached. Fix. Never pass a
  live reference into host memory across the boundary. Marshal by value or
  hand across a narrowly typed proxy object that exposes only the specific
  methods the capability grants, and treat any object crossing the boundary
  as an adversarial input that must be validated on the far side regardless
  of which side sent it.
- Symptom. Users click through every permission prompt without reading them,
  so the runtime-level permission checks stop functioning as a real control
  even though they are technically still enforced. Cause. Permissions were
  requested too granularly, too frequently, or at the wrong moment (mid-task
  rather than at install or first use), producing the well-documented human
  factor of prompt fatigue. Fix. Group related capabilities into a single,
  readable manifest-time declaration rather than many runtime prompts, the
  approach Figma and most marketplace-based platforms take with an
  install-time manifest, and reserve interactive, per-call prompts for the
  genuinely rare, high-stakes operation rather than for routine calls.
- Symptom. The platform's plugin ecosystem stagnates, or a large share of
  users end up disabling the sandbox entirely to use popular plugins. Cause.
  The capability surface was designed too narrowly for what real plugin
  authors actually needed, so the path of least resistance became routing
  around the sandbox rather than working within it, which is precisely the
  dynamic Obsidian's documentation is describing when it tells users that
  turning off Restricted Mode is sometimes necessary and should be done
  only when the user personally trusts the plugin author. Fix. Expand the
  capability catalog deliberately, based on telemetry of what legitimate
  plugins are actually trying and failing to do (dimension 16), rather than
  leaving a full-bypass escape hatch as the only relief valve for a
  capability surface that is too tight.
- Symptom. A plugin causes severe host slowdown, or exhausts host memory,
  despite the security sandbox reporting no policy violations at all.
  Cause. The security boundary and the resource boundary are two separate
  concerns that got conflated. A capability check answers "was this
  operation allowed," not "how much CPU, memory, or wall-clock time has
  this plugin consumed so far," and a sandbox that only implements the
  former leaves the host exposed to a plugin that is fully within its
  granted capabilities and simultaneously a noisy neighbor to everyone
  else. Fix. Pair the capability boundary with an explicit resource
  boundary, timeouts, memory caps, CPU quotas, at the same layer that
  creates the sandbox instance, the way a Firecracker microVM or a
  container's cgroup limits are configured alongside, not instead of, the
  isolation boundary itself.
- Symptom. Data the plugin was never explicitly granted access to still
  ends up leaving the sandbox. Cause. A capability was scoped too broadly,
  most commonly an all-or-nothing network permission that lets the plugin
  reach any host rather than the specific hosts it declared a need for, so
  the plugin exfiltrates data to an attacker-controlled endpoint using a
  capability it was, technically, granted. Fix. Scope every capability to
  the narrowest resource that satisfies the plugin's stated need, the way
  Deno's `--allow-net=example.com` restricts to a specific host rather than
  granting blanket network access, and the way Figma's manifest-declared
  domain allowlist causes an out-of-scope network attempt to be blocked
  with a content-security-policy error rather than silently allowed.

## 12. Trade-off matrix

The comparison is against three concretely different, named alternative
strategies for the same underlying problem, running code the host does not
fully control, rather than against an unnamed naive baseline.

| Force | Plugin Sandbox | Trust and review (code signing, manual audit, no runtime boundary) | In-process extension via Dependency Injection or Strategy (first-party plugins only) | Full VM per tenant for every workload (Firecracker/gVisor-class isolation applied uniformly) |
|---|---|---|---|---|
| Security isolation strength | Strong, scales to fully untrusted authors; strength depends on the specific variant chosen from dimension 8 | Weak at runtime; entirely dependent on the review catching the issue before publish, and on the plugin never being updated to something malicious afterward | None; assumes the code is already trusted, so provides no protection if that assumption is wrong | Strongest available; near-total isolation even against kernel-level exploits |
| Performance overhead | Moderate to significant, concentrated at boundary crossings; near-free for process isolation with rare calls, costly for chatty call patterns across a VM boundary | Effectively zero at runtime; all the cost is paid once, at review time | Effectively zero; ordinary in-process function calls | Highest; VM boot and per-call virtualization overhead even for trivial, low-risk plugins |
| Suitable trust level | Untrusted to semi-trusted third-party code | Semi-trusted, identifiable publishers willing to be held accountable | Fully trusted, first-party code only | Any, but its cost is wasted on code that was already trusted |
| Development and operational complexity | High; a broker, manifest schema, capability object, and marshaling layer are new, ongoing components to build and maintain | Low at runtime; moderate at process level (review workflow, signing infrastructure) | Lowest; reuses ordinary application architecture with no new isolation infrastructure | High; VM lifecycle management, image or snapshot management, per-tenant scheduling |
| Debuggability | Reduced; requires cross-boundary tooling | Unaffected; the code runs exactly as written, in-process | Best; ordinary in-process debugging tools apply directly | Most reduced; full VM boundary is the hardest to instrument |
| Resistance to plugin updates turning malicious post-publish | Strong; the boundary is enforced every time the plugin runs, regardless of when it was last reviewed | Weak; a review at publish time says nothing about a later, unreviewed update unless every update is re-reviewed | Not applicable; there is no separate publish or update event, the code ships with the host | Strong, for the same structural reason as Plugin Sandbox |

## 13. Related and incompatible patterns

- Plugin Architecture and Microkernel. Both define the extension point, the
  structural seam where third-party code attaches, that Plugin Sandbox
  secures at runtime. Plugin Sandbox is almost never used alone; it is the
  security layer wrapped around one of these two structural patterns, and
  an entry describing either of them without addressing trust is describing
  half of a real system.
- Broker Architecture. The broker participant in dimension 5 is, in effect,
  an instance of Broker Architecture specialized to mediate between one
  trusted party and one untrusted party rather than between arbitrary
  peers, and the same request-forwarding, response-marshaling shape applies.
- Proxy. The capability object handed to the plugin is structurally a Proxy,
  standing in for the real host resource and controlling access to it,
  though it differs from the classic Proxy in that it is deliberately
  narrower than the interface of the thing it stands in for, exposing only
  a subset of operations rather than the full interface with access checks
  layered on top.
- Facade. The host API surface, the specific set of functions a plugin can
  call, is a Facade over the host's much larger internal surface, and the
  discipline of keeping that facade small is exactly the discipline this
  pattern depends on for the functionality-against-confinement force in
  dimension 3 to resolve in the sandbox's favor.
- Bulkhead. Nygard's bulkhead concept, isolating resource pools so that
  exhaustion in one does not exhaust another, is the natural companion to
  the resource-boundary half of dimension 11's noisy-neighbor failure mode.
  Plugin Sandbox alone secures against unauthorized operations; pairing it
  with a bulkhead secures against authorized operations consuming
  unbounded resources.
- Circuit Breaker. When the broker's supervisor detects a plugin repeatedly
  crashing, hanging, or exceeding its resource bulkhead, the natural
  response, stop invoking it and fail fast rather than repeatedly paying
  the cost of spinning up a doomed boundary, is a direct application of
  Circuit Breaker at the plugin-invocation level.
- Mediator and Observer. Event delivery across the boundary, notifying a
  plugin that something happened in the host, or notifying the host that a
  plugin produced a result, commonly reuses the structure of Mediator, with
  the broker as the mediator, or Observer, with the plugin subscribing to a
  narrow, host-defined set of events rather than an unrestricted event bus.
- Command. Capability calls that cross the message channel are frequently
  implemented as serialized Command objects, a method name and its
  arguments, precisely because a Command is easy to marshal, easy to
  validate against a manifest before execution, and easy to log for
  dimension 16's audit trail.
- Dependency Injection. Capability injection, handing the plugin only the
  specific functions it needs at construction time rather than letting it
  reach for ambient globals, is Dependency Injection applied with a
  security objective rather than a testability objective, and the same
  discipline, construct dependencies explicitly, inject them, never let the
  consumer reach past what it was given, underlies both.
- Incompatible with Singleton. A live reference to a host-side Singleton
  cannot be handed across the boundary without leaking ambient authority to
  every method that Singleton exposes, which is exactly the mistake
  described in dimension 11's second failure mode. A Singleton the plugin
  needs to interact with must be wrapped in a narrow, purpose-built
  capability proxy rather than passed through directly.
- Incompatible with God Object. A host API surface that has grown into a
  God Object, one interface exposing most of the host's functionality,
  defeats the purpose of the sandbox even if a real process or isolate
  boundary is technically in place, because the capability surface itself
  has become as broad as ambient access would have been. The sandbox is
  only as narrow as its capability object, never narrower.

## 14. Refactoring path in and out

Introducing a sandbox into a plugin system that currently grants full,
ambient access is a migration, not a flag flip, and skipping steps is the
most common way these migrations either stall indefinitely or break every
existing plugin on cutover day.

1. Inventory actual capability usage before designing the new boundary.
   Instrument the current, unsandboxed plugin API and log which host
   functions and globals plugins are actually calling in production, for a
   representative window of real traffic across the real plugin ecosystem,
   not just the plugins the host team happens to know about.
2. Define a minimal capability interface from that inventory, wrapping each
   currently-ambient global or function behind a named, host-owned function
   with an explicit signature. This step, replacing direct access to a
   shared resource with calls through an explicit seam, is the same move
   described in refactoring literature as Branch by Abstraction, introduce
   the abstraction first, migrate call sites to go through it, while the
   old direct access path still technically exists underneath
   ([Martin Fowler, Refactoring glossary, Branch by Abstraction](https://martinfowler.com/bliki/BranchByAbstraction.html),
   verified 2026-08-02).
3. Ship the new capability interface in shadow mode. Route plugin calls
   through the new, named functions, but do not yet enforce a manifest or
   move plugin code across a real boundary. Log every call that would have
   been denied under a proposed manifest, without actually denying it, so
   the host team can see how many false positives, legitimate calls the
   proposed manifest is too narrow to permit, a hard cutover would produce.
4. Move plugin invocation across a real boundary, one of the variants from
   dimension 8 chosen to match the actual trust level of the plugin
   population, once shadow-mode telemetry shows the proposed capability set
   is stable and the false-positive rate has dropped to an acceptable
   level. This is the step equivalent to the Expand-Contract, or Parallel
   Change, refactoring technique's final contraction, the old, wide access
   path is removed only after the new, narrow path has been running
   alongside it long enough to be trusted
   ([Martin Fowler, Refactoring glossary, Parallel Change](https://martinfowler.com/bliki/ParallelChange.html),
   verified 2026-08-02).
5. Revoke ambient access last, and only after a burn-in window with zero
   unexpected denials from real, previously-working plugins. Revoking too
   early, before the capability inventory is genuinely complete, is what
   turns a security migration into an incident.

The path out, removing a sandbox once it exists, is rare and should be
treated with more suspicion than the path in, because the conditions that
justified it in dimension 4 (an untrusted authorship population) tend to
persist rather than resolve. The one legitimate case is when the plugin
ecosystem itself has genuinely collapsed to first-party, fully-reviewed code
shipped through the same pipeline as the host, at which point the sandbox
may be providing only crash containment rather than security isolation, and
a narrower mechanism, a bulkhead without the full capability-mediation
machinery, may suffice on its own. Even then, removing the boundary should
be a deliberate, reviewed decision rather than something that happens by
attrition as capability checks are individually loosened over time.

## 15. Testing and verification

Verifying a sandbox is a testing task that draws heavily on general adversarial
and property-based testing practice rather than a single named technique,
and it needs two structurally different test suites because it is answering
two different questions.

The first suite tests the host's business logic against a fake capability
object, the ordinary test-double substitution familiar from any
Dependency-Injection-based design. swap the real, boundary-crossing
capability implementation for an in-process fake that returns
programmable results, and use it to test the host's own behavior quickly
and deterministically, without paying the cost of spinning up a real
process, isolate, or VM for every unit test. This suite answers "does the
host correctly use the capabilities it has," and it should be the large
majority of the test count by volume, the same shape as any other
fast, in-process unit test suite.

The second suite is smaller, slower, and adversarial by design, and it
answers a different question entirely. "does the real boundary actually
hold." This suite should include, at minimum, a positive case for every
declared capability (confirming a granted operation actually succeeds
through the real boundary, not just the fake), a negative case for every
capability the manifest did not grant (confirming the real boundary denies
it, not merely that the fake would have), and a regression test for every
known escape technique relevant to the chosen implementation variant, the
prototype-chain walk for a JavaScript-based boundary, a path traversal or
symlink attack for a filesystem capability, an over-broad domain match for a
network capability. Each entry in dimension 11's failure-mode table is a
candidate for exactly this kind of permanent regression test once it has
been found once, the same discipline behind treating any discovered bug as
a test that must never pass again.

Beyond the capability boundary itself, the sandbox's failure behavior needs
its own explicit tests. a plugin that hangs forever should be killed by the
supervisor within its declared timeout and the host should continue serving
other plugins and other requests without degradation; a plugin that
allocates unbounded memory should be terminated by its resource bulkhead
rather than taking down the host process; a plugin that crashes mid-call
should return a clean error to the host caller rather than corrupting the
state of the broker or leaving the boundary in an unrecoverable state.
These are chaos-style tests, deliberately injecting the failure and
asserting the host survives it, rather than tests of the happy path, and a
sandbox that has never been tested this way should be assumed to fail this
way in production the first time it matters.

Finally, the message-channel schema between host and plugin, the shape of a
capability call and its result, deserves its own contract tests,
independent of both suites above, so that the host and the plugin runtime
can evolve their respective implementations without silently drifting apart
on what a given capability call actually means.

## 16. Observability signals

The single most useful signal a sandbox can emit is a structured log of
every capability grant and every capability denial, tagged with the
plugin's identity, the specific capability requested, and a timestamp. This
is the record a security team actually reads after an incident, and it is
also the record that turns the too-narrow-capability-surface failure mode
from dimension 11 from a support ticket into a data point. a capability
that is denied often, for the same plugin or across many plugins, is either
a sign of a plugin trying something it should not be allowed to do, or a
sign that the capability surface is missing something legitimate plugins
genuinely need, and distinguishing the two requires looking at which
plugins are triggering the denial and how, not just counting denials.

A healthy sandbox, observed over time, should show a low, roughly steady
rate of denials relative to grants for the plugin population as a whole,
concentrated in a small number of specific plugins or capabilities rather
than spread evenly, because an evenly spread denial rate across the whole
population usually means the manifest process itself is broken rather than
that many independent plugin authors are simultaneously misbehaving. A
sudden spike in denials for one previously well-behaved plugin, correlated
with a version update, is the signature of either a bug introduced in that
update or, in the more serious case, a compromise of the plugin's publishing
account.

Boundary-crossing latency, measured as p50, p95, and p99 for a single
capability call round trip, is the second core signal, because it is the
direct, measurable proxy for the performance-against-isolation-strength
force from dimension 3, and it is the metric most likely to catch the
common real-world bug where a plugin's call pattern, one round trip per
keystroke or per frame, was designed assuming in-process latency and is now
paying process- or VM-boundary latency on every call.

Per-plugin resource usage, CPU time, memory high-water mark, and wall-clock
duration, attributed at the level of the individual boundary instance
rather than aggregated across the whole host, is what makes the
noisy-neighbor failure mode from dimension 11 attributable to a specific
plugin rather than showing up only as an unexplained overall host slowdown.

Sandbox lifecycle events, boundary created, boundary destroyed cleanly,
boundary killed by the supervisor for a timeout or crash, are a stability
signal in their own right. A rising rate of supervisor-initiated kills for
one specific plugin, tracked over successive versions of that plugin, is
frequently the earliest available signal of a memory leak or a crash loop,
often visible in this metric well before it would otherwise surface as a
user-facing complaint.

Finally, capability usage counts, which specific capabilities are actually
being called in production and how often, feed directly back into
dimension 14's refactoring path. they are the evidence base for both
tightening a capability that turns out to be unused by any real plugin, and
for deliberately widening one that legitimate plugins are consistently
denied on.

## 17. Security and privacy implications

Everything in this dimension is, in a real sense, what the whole pattern
exists to address, so the discussion here is narrower. the specific things
that go wrong even when the boundary itself is implemented correctly.

What crosses the boundary matters as much as whether the boundary exists.
A capability call that returns a live reference into host memory, rather
than a copy or a narrowly scoped proxy, defeats the boundary regardless of
how strong the underlying isolation mechanism is, because the plugin now
holds a path back into host state that the capability object was supposed
to prevent, the exact mechanism behind the second failure mode in dimension
11. Every value crossing the channel in either direction should be treated
as if it were being sent to a fully adversarial party, marshaled by value
or wrapped in a purpose-built proxy, never handed across as a live object
graph.

Side channels are a residual risk even when the capability check itself is
correct. Two pieces of code sharing a physical CPU core, a cache, or a
branch predictor can, in principle, leak information to each other through
timing differences that have nothing to do with any capability the sandbox
explicitly granted or denied, the general class of concern behind
speculative-execution vulnerabilities such as Spectre. This is precisely
why Cloudflare layers Linux namespace and seccomp restrictions, and its
own trust-level cordoning of different customer tiers onto separate
physical hosts, on top of its V8 isolate boundary rather than relying on the
isolate boundary alone. the isolate correctly enforces memory-access
capability rules, and the additional layers exist specifically to reduce
the residual, harder-to-eliminate side-channel risk that remains even when
the primary boundary is functioning exactly as designed.

Data minimization at the capability-design level is a privacy control, not
only a security one, and it is easy to get wrong even with a technically
sound boundary. A capability that returns a user's entire profile object
when the plugin's declared, legitimate need was only the user's display
name is over-broad by design, and the sandbox's technical correctness does
not protect the rest of that profile once it has already crossed into the
plugin's hands. The discipline of scoping a capability to the minimum data
it needs to return, not merely the minimum operation it needs to permit, is
the same principle underlying data protection regulation's general data
minimization requirement, applied one layer earlier, at API design time,
rather than only at the storage or retention layer where it is more
commonly discussed.

The sandbox reduces blast radius; it does not eliminate harm within the
capabilities a plugin was legitimately granted. A plugin that was correctly
granted read access to a user's notes, because that is genuinely what it
needs to do its job, can still misuse that access, copying, summarizing,
or transmitting the notes somewhere the user never intended, entirely
within the bounds of what the sandbox allowed. This is why capability
scoping at install or update time, ideally paired with a signed publisher
identity and, for higher-risk capabilities, a manual review comparable to
an app-store review process, remains necessary alongside the runtime
boundary rather than being replaced by it. The runtime boundary answers
"can this code exceed what it was granted." It does not, and cannot,
answer "should this code have been granted this in the first place."

Finally, the audit log described in dimension 16 is itself a security
control in the accountability sense, not merely an operational one. the
ability to reconstruct, after the fact, exactly which capability a specific
plugin used, when, and with what result, is frequently what turns an
otherwise unattributable incident into one that can be traced to a specific
plugin, a specific version, and a specific capability that may then be
revoked or tightened.

## 18. References

- Jack B. Dennis and Earl C. Van Horn, "Programming Semantics for
  Multiprogrammed Computations," Communications of the ACM, volume 9, issue
  3, 1966, pages 143 to 155.
  [https://dl.acm.org/doi/10.1145/365230.365252](https://dl.acm.org/doi/10.1145/365230.365252),
  verified 2026-08-02.
- Frank Buschmann, Regine Meunier, Hans Rohnert, Peter Sommerlad, and
  Michael Stal, Pattern-Oriented Software Architecture Volume 1, Wiley,
  1996, chapters on Microkernel and the related structural patterns.
- OpenJDK, "JEP 411. Deprecate the Security Manager for Removal."
  [https://openjdk.org/jeps/411](https://openjdk.org/jeps/411),
  verified 2026-08-02.
- OpenJDK, "JEP 486. Permanently Disable the Security Manager."
  [https://openjdk.org/jeps/486](https://openjdk.org/jeps/486),
  verified 2026-08-02.
- Microsoft, "VS Code Extension Host."
  [https://code.visualstudio.com/api/advanced-topics/extension-host](https://code.visualstudio.com/api/advanced-topics/extension-host),
  verified 2026-08-02.
- Figma, "How plugins run."
  [https://developers.figma.com/docs/plugins/how-plugins-run/](https://developers.figma.com/docs/plugins/how-plugins-run/),
  verified 2026-08-02.
- Chrome for Developers, "Content scripts."
  [https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts),
  verified 2026-08-02.
- Cloudflare, "Security model."
  [https://developers.cloudflare.com/workers/reference/security-model/](https://developers.cloudflare.com/workers/reference/security-model/),
  verified 2026-08-02.
- Amazon Web Services, "Run isolated sandboxes with full lifecycle control.
  AWS Lambda introduces MicroVMs."
  [https://aws.amazon.com/blogs/aws/run-isolated-sandboxes-with-full-lifecycle-control-aws-lambda-introduces-microvms/](https://aws.amazon.com/blogs/aws/run-isolated-sandboxes-with-full-lifecycle-control-aws-lambda-introduces-microvms/),
  verified 2026-08-02.
- Firecracker project, project homepage.
  [https://firecracker-microvm.github.io/](https://firecracker-microvm.github.io/),
  verified 2026-08-02.
- HashiCorp, "go-plugin" README.
  [https://github.com/hashicorp/go-plugin](https://github.com/hashicorp/go-plugin),
  verified 2026-08-02.
- Bytecode Alliance, "cap-std" README.
  [https://github.com/bytecodealliance/cap-std](https://github.com/bytecodealliance/cap-std),
  verified 2026-08-02.
- Deno, "Security."
  [https://docs.deno.com/runtime/fundamentals/security/](https://docs.deno.com/runtime/fundamentals/security/),
  verified 2026-08-02.
- WASI, project homepage.
  [https://wasi.dev/](https://wasi.dev/), verified 2026-08-02.
- Node.js, "VM (executing JavaScript)."
  [https://nodejs.org/api/vm.html](https://nodejs.org/api/vm.html),
  verified 2026-08-02.
- Obsidian, "Plugin security."
  [https://obsidian.md/help/plugin-security](https://obsidian.md/help/plugin-security),
  verified 2026-08-02.
- Martin Fowler, Refactoring glossary, "Branch by Abstraction."
  [https://martinfowler.com/bliki/BranchByAbstraction.html](https://martinfowler.com/bliki/BranchByAbstraction.html),
  verified 2026-08-02.
- Martin Fowler, Refactoring glossary, "Parallel Change."
  [https://martinfowler.com/bliki/ParallelChange.html](https://martinfowler.com/bliki/ParallelChange.html),
  verified 2026-08-02.

## Code examples

Every entry carries working code across at least three languages. This one
carries four. TypeScript, Python, Go, and Rust, each demonstrating a
different, honest slice of the pattern rather than the same design repeated
four times, because no single mechanism is faithful to the whole pattern in
every language. Java is omitted from the runnable set on this machine
because no Java runtime is installed to execute against, though `javac`
itself is present; the language-idiomatic mechanism worth knowing about for
the JVM, a SecurityManager-based runtime policy, is precisely the approach
that has been deprecated for removal since Java 17, discussed in dimension
1, so a modern JVM example would need to rely on the same subprocess or
class-loader-and-module boundary shown in the Go example below rather than
on a mechanism the platform itself is retiring.

The TypeScript example demonstrates the capability-injection contract from
dimension 5. the plugin receives only an explicit `HostCapabilities` object
and has no lexical closure over the host's internal state, which is the
half of the pattern that is genuinely a language-portable design discipline.
It is deliberately honest that this alone, without a real process, isolate,
or WASM boundary layered underneath it in a genuine deployment, secures the
API surface but not the runtime, which is exactly the caveat dimension 11's
first failure mode is about.

```typescript
type LogFn = (message: string) => void;
type ReadFn = (key: string) => string | undefined;

interface HostCapabilities {
  readonly log: LogFn;
  readonly readSetting: ReadFn;
}

type SandboxPlugin = (caps: HostCapabilities) => void;

function loadPlugin(source: string): SandboxPlugin {
  const factory = new Function("caps", `"use strict";\n${source}`);
  return (caps: HostCapabilities) => factory(caps);
}

function runPlugin(plugin: SandboxPlugin, caps: HostCapabilities): void {
  const frozen = Object.freeze({ ...caps });
  plugin(frozen);
}

const settings = new Map<string, string>([["theme", "dark"]]);
const capabilities: HostCapabilities = {
  log: (message) => console.log(`[plugin] ${message}`),
  readSetting: (key) => settings.get(key),
};

const untrustedSource = `
  caps.log("theme is " + caps.readSetting("theme"));
  caps.log("closure over settings map. " + (typeof settings !== "undefined"));
`;

const plugin = loadPlugin(untrustedSource);
runPlugin(plugin, capabilities);
```

The Python example shows a real process boundary, using `multiprocessing`
in spawn mode so the plugin never inherits the host's memory, combined with
an explicit, allowlisted request-response protocol so the plugin can call
only the two host handlers it was given, `log` and `read_setting`, and
nothing else, even though the plugin process is running arbitrary `exec`'d
code. The restricted `__builtins__` shown here is a partial mitigation, not
a complete one; Python's own dynamic introspection surface has a long
history of restricted-execution bypasses, which is exactly why the real
boundary doing the enforcing here is the separate operating system process,
not the builtins restriction.

```python
import multiprocessing as mp
from typing import Callable

def plugin_entry(request_q: mp.Queue, response_q: mp.Queue, plugin_code: str) -> None:
    def call_host(method: str, *args):
        request_q.put((method, args))
        return response_q.get()

    safe_builtins = {"str": str, "len": len}
    plugin_globals = {"call_host": call_host, "__builtins__": safe_builtins}
    exec(compile(plugin_code, "<plugin>", "exec"), plugin_globals)

class PluginHost:
    def __init__(self) -> None:
        self._settings = {"theme": "dark"}
        self._handlers: dict[str, Callable] = {
            "read_setting": lambda key: self._settings.get(key),
            "log": lambda msg: print(f"[plugin] {msg}"),
        }

    def run(self, plugin_code: str) -> None:
        ctx = mp.get_context("spawn")
        request_q: mp.Queue = ctx.Queue()
        response_q: mp.Queue = ctx.Queue()
        proc = ctx.Process(target=plugin_entry, args=(request_q, response_q, plugin_code))
        proc.start()
        while proc.is_alive() or not request_q.empty():
            try:
                method, args = request_q.get(timeout=0.5)
            except Exception:
                if not proc.is_alive():
                    break
                continue
            if method not in self._handlers:
                response_q.put(None)
                continue
            response_q.put(self._handlers[method](*args))
        proc.join(timeout=2)

if __name__ == "__main__":
    untrusted_plugin = """
call_host("log", "theme is " + str(call_host("read_setting", "theme")))
"""
    PluginHost().run(untrusted_plugin)
```

The Go example shows the HashiCorp go-plugin shape from dimension 8 in
miniature. a single binary that re-executes itself as a subprocess with a
minimal, explicitly set environment, communicating over stdin and stdout
using a small JSON-RPC protocol where the host checks every incoming
request against an explicit capability map before executing it, and denies,
rather than silently ignoring, anything outside that map.

```go
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
)

type rpcRequest struct {
	Method string   `json:"method"`
	Args   []string `json:"args"`
}

type rpcResponse struct {
	Result string `json:"result"`
	Denied bool   `json:"denied"`
}

func callHost(w *bufio.Writer, r *bufio.Reader, method string, args ...string) string {
	payload, _ := json.Marshal(rpcRequest{Method: method, Args: args})
	w.WriteString(string(payload) + "\n")
	w.Flush()
	line, _ := r.ReadString('\n')
	var resp rpcResponse
	json.Unmarshal([]byte(line), &resp)
	return resp.Result
}

func runPluginBody() {
	w := bufio.NewWriter(os.Stdout)
	r := bufio.NewReader(os.Stdin)
	theme := callHost(w, r, "read_setting", "theme")
	fmt.Fprintf(os.Stderr, "[plugin] theme is %s\n", theme)
	callHost(w, r, "delete_all_settings")
}

type capability func(args []string) string

func servePlugin(caps map[string]capability, stdin *bufio.Reader, stdout *bufio.Writer) {
	for {
		line, err := stdin.ReadString('\n')
		if err != nil {
			return
		}
		var req rpcRequest
		json.Unmarshal([]byte(line), &req)
		handler, allowed := caps[req.Method]
		resp := rpcResponse{Denied: true}
		if allowed {
			resp = rpcResponse{Result: handler(req.Args)}
		} else {
			fmt.Fprintf(os.Stderr, "[host] denied capability. %s\n", req.Method)
		}
		out, _ := json.Marshal(resp)
		stdout.WriteString(string(out) + "\n")
		stdout.Flush()
	}
}

func main() {
	if os.Getenv("PLUGIN_MODE") == "1" {
		runPluginBody()
		return
	}

	settings := map[string]string{"theme": "dark"}
	caps := map[string]capability{
		"read_setting": func(args []string) string { return settings[args[0]] },
	}

	self, _ := os.Executable()
	cmd := exec.Command(self)
	cmd.Env = []string{"PLUGIN_MODE=1"}
	stdinPipe, _ := cmd.StdinPipe()
	stdoutPipe, _ := cmd.StdoutPipe()
	cmd.Stderr = os.Stderr

	if err := cmd.Start(); err != nil {
		panic(err)
	}
	servePlugin(caps, bufio.NewReader(stdoutPipe), bufio.NewWriter(stdinPipe))
	cmd.Wait()
}
```

The Rust example shows the compile-time capability-token variant from
dimension 8, in the spirit of cap-std, meant for trusted-but-fallible code
compiled into the same binary rather than for adversarial isolation.
`SettingsCapability` can only be constructed inside `PluginHost`, and every
`Plugin` implementation can only reach settings through the narrow `read`
method it was handed by reference, so a plugin author who never intended
harm cannot accidentally reach a capability they were not given, enforced
by the borrow checker rather than by a runtime check.

```rust
struct SettingsCapability<'a> {
    settings: &'a std::collections::HashMap<String, String>,
}

impl<'a> SettingsCapability<'a> {
    fn read(&self, key: &str) -> Option<&String> {
        self.settings.get(key)
    }
}

struct LogCapability;

impl LogCapability {
    fn log(&self, message: &str) {
        println!("[plugin] {message}");
    }
}

trait Plugin {
    fn run(&self, settings: &SettingsCapability, log: &LogCapability);
}

struct ThemeReporter;

impl Plugin for ThemeReporter {
    fn run(&self, settings: &SettingsCapability, log: &LogCapability) {
        match settings.read("theme") {
            Some(theme) => log.log(&format!("theme is {theme}")),
            None => log.log("no theme configured"),
        }
    }
}

struct PluginHost {
    settings: std::collections::HashMap<String, String>,
}

impl PluginHost {
    fn new() -> Self {
        let mut settings = std::collections::HashMap::new();
        settings.insert("theme".to_string(), "dark".to_string());
        PluginHost { settings }
    }

    fn run_plugin(&self, plugin: &dyn Plugin) {
        let settings_cap = SettingsCapability {
            settings: &self.settings,
        };
        let log_cap = LogCapability;
        plugin.run(&settings_cap, &log_cap);
    }
}

fn main() {
    let host = PluginHost::new();
    let plugin = ThemeReporter;
    host.run_plugin(&plugin);
}
```
