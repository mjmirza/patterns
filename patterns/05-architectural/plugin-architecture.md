---
name: Plugin Architecture
slug: plugin-architecture
family: 05-architectural
category: Architectural
aliases: [Extension Point Architecture, Hook-Based Extensibility, Microkernel Plugin Model]
first_described: "Marc-Thomas Schmidt and coauthors, Microkernel Architecture Pattern, in Frank Buschmann, Regine Meunier, Hans Rohnert, Peter Sommerlad, Michael Stal, Pattern-Oriented Software Architecture Volume 1, Wiley, 1996"
maturity: canonical
related: [strategy, observer, template-method, chain-of-responsibility, dependency-injection, service-locator]
incompatible_with: [singleton]
verified: 2026-08-02
---

# Plugin Architecture

## 1. Name, aliases, and lineage

Plugin Architecture is the name in day-to-day industry use for a design where a
host application ships a small, stable core and defers most of its behaviour to
separately deployable units, called plugins, extensions, or add-ins depending
on the ecosystem, that are discovered and loaded at run time rather than
compiled into the host. The pattern does not have a single canonical academic
citation the way a Gang of Four pattern does. Its closest formal ancestor is
the **Microkernel** architectural pattern, described by Marc-Thomas Schmidt in
Frank Buschmann, Regine Meunier, Hans Rohnert, Peter Sommerlad, and Michael
Stal, *Pattern-Oriented Software Architecture, Volume 1, A System of Patterns*,
Wiley, 1996, chapter 2. The book frames the microkernel as separating a minimal
functional core from extended functionality and custom parts, with the core
providing mechanisms for internal and external components to cooperate and
communicate. Plugin Architecture is the practical, less formal name that took
hold once the pattern moved out of operating system kernels and into
application software, and it is the name developers actually search for and
use in code review, so this entry uses it as the primary heading while treating
Microkernel as its academic parent.

The alias **Extension Point Architecture** comes from the Eclipse platform,
whose own documentation describes plugins contributing to and consuming named
extension points, with the platform runtime discovering and wiring them together
([Eclipse Platform Plug-in Developer Guide, extension point concepts](https://help.eclipse.org/latest/index.jsp?topic=%2Forg.eclipse.platform.doc.isv%2Fguide%2Fextension_point.htm),
verified 2026-08-02). **Hook-Based Extensibility** is the name used in the
WordPress ecosystem, where the entire plugin and theme system is built on two
primitives, actions and filters, that WordPress core and other plugins can
attach callback functions to at named points in execution
([WordPress Developer Resources, Plugin Hooks](https://developer.wordpress.org/plugins/hooks/),
verified 2026-08-02). **Microkernel Plugin Model** is used interchangeably with
plain Microkernel in enterprise architecture literature when the emphasis is on
the runtime plugin mechanism rather than the kernel's internal minimalism.

A separate but frequently conflated idea is the GoF Bridge pattern combined
with Abstract Factory to swap implementations at compile time. Plugin
Architecture is distinguished by run-time discovery, independent deployability,
and typically a stable public contract that plugin authors outside the host's
own codebase can implement without access to the host's source, which none of
those object-level patterns require on their own.

## 2. Problem and context

An application needs to support a set of behaviours that is open-ended,
unknown at the time the core is built, and likely to be supplied by parties who
are not the core's own maintainers. The behaviours share the same host runtime,
the same overall lifecycle, and the same audience, but each one is variable
enough that hard-coding all of them into the core produces a monolith that
recompiles, redeploys, and re-tests on every unrelated addition.

The situation reads like this in a real codebase. A code editor needs to
support dozens of programming languages, linters, formatters, and version
control systems, and the core maintainers cannot write, test, or even
anticipate every one of them. A build tool needs to transform assets in ways
that differ per project, from image compression to service worker generation,
and baking every transform into the core bloats the default install for users
who need none of them. An infrastructure-as-code tool needs to talk to dozens
of cloud providers, each with its own authentication, resource model, and API
surface, and none of that provider-specific logic belongs in the tool's own
release cycle. In every one of these cases the honest shape of the problem is
that the SET of extensions is unbounded and changes on a schedule the core
cannot control, while the MECHANISM by which an extension participates is
bounded and can be designed once.

Plugin Architecture answers this by drawing a hard boundary. The host defines
a small number of extension points and a contract for what a plugin must
implement to attach to one. Plugins are discovered, loaded, and given
controlled access to host services, but the host never depends on any specific
plugin at compile time. The context that makes this the right answer, not
merely a possible one, has three parts, the extension space is genuinely open
and growing, the party writing an extension is frequently not the party
maintaining the core, and the cost of a broken or malicious extension can be
contained without threatening the whole host process, or the project has
explicitly decided that trade-off is acceptable, which is discussed in
dimension 17.

## 3. Forces

Plugin Architecture balances the following competing pressures. Every entry
here reflects reasoning about the trade-off rather than a citable external
fact, so it is stated as engineering judgement, not sourced claim.

- **Extensibility.** Strongly favoured. New behaviour is added by shipping a
  new plugin, with zero changes to the host's own source or release cadence.
  This is the entire reason the pattern exists.
- **Coupling.** Favoured at the boundary, sacrificed inside it. The host and
  plugin depend only on the shared contract, which is good coupling discipline
  externally, but the contract itself becomes an extremely high-stakes
  dependency, because every plugin that has ever shipped now depends on it.
- **Stability of the core.** Favoured. Core code changes rarely, because
  behaviour that would otherwise live in the core lives in plugins instead.
  This is the trade the microkernel literature makes explicit, keep the kernel
  minimal, push variability outward.
- **Deployability.** Favoured. Plugins ship, version, and roll back
  independently of the host and of each other, in a system that supports it.
- **Cognitive load for a reader.** Sacrificed. Tracing what actually happens
  when the host runs requires knowing which plugins are installed and enabled
  in this specific instance, information that does not live in the source tree
  a reader has open.
- **Performance and startup latency.** Sacrificed, in proportion to plugin
  count. Discovery, loading, and per-hook dispatch all cost time and memory
  that a monolithic build does not pay. Extension host isolation, discussed in
  dimension 8, adds further overhead when it is present.
- **Testability of the whole system.** Sacrificed for integration testing,
  favoured for the core in isolation. The core can be tested against a
  contract and a small set of reference plugins, but the combinatorial space of
  real-world plugin combinations a user might have installed is not something
  any core team can exhaustively test.
- **Security surface.** Sacrificed, unless deliberately closed by process or
  language-level sandboxing, discussed at length in dimension 17. A plugin
  typically runs with some or all of the host's privileges.
- **Backward compatibility burden.** Sacrificed over time. Every extension
  point, once published, becomes something the host must either support
  forever or deliberately deprecate with a migration path, because breaking it
  breaks every plugin that targets it, not just code the host team controls.

A pattern that gave up nothing would not need a name. The price here is paid
in contract stewardship, security surface, and the loss of whole-system static
analysis.

## 4. Applicability and non-applicability

Reach for Plugin Architecture when the following hold.

- The set of behaviours the application must support is open-ended and grows
  on a schedule the core team does not control, for example third-party
  integrations, language support, or theming.
- Different parties, inside or outside the maintaining organisation, need to
  add behaviour without access to the host's source repository or its release
  process.
- The behaviours are largely independent of each other, so that most plugins
  do not need to coordinate directly with most other plugins.
- The host has, or is willing to build, a stable enough core abstraction that
  an extension point published today will still make sense in two years.
- The cost of an unbounded core, in build time, binary size, or blast radius of
  an unrelated change, has become a measured problem, not a hypothetical one.

Do NOT reach for Plugin Architecture in these cases, and the reason matters
more than the rule.

- **The variation is small, closed, and known up front.** If there are three
  payment providers and the fourth is not expected this decade, a Strategy
  pattern with three concrete classes selected by configuration gives the same
  flexibility with none of the discovery machinery, the versioned contract
  risk, or the security surface. Plugin Architecture pays a large fixed cost in
  infrastructure that only earns itself back when the extension count and
  extension velocity are genuinely large.
- **The extensions must interact tightly and constantly with each other.**
  Plugin systems isolate extensions from each other by design. A domain where
  every extension needs deep, synchronous knowledge of every other extension's
  internal state degrades into a system where the plugin boundary is fought
  against on every feature, not one that benefits from it.
- **The team cannot commit to a stable contract.** A host whose internal data
  model is still churning weekly will break every plugin on every release if
  that churn is exposed as the extension contract. Publishing an extension
  point is a promise. A team not ready to keep that promise should keep the
  variability internal until the abstraction has settled, and use Strategy or
  Template Method internally in the meantime.
- **Startup latency and memory footprint are hard constraints.** A plugin
  system's discovery and loading overhead is real cost, not free flexibility.
  An embedded system, a CLI tool that must start in single-digit milliseconds,
  or a serverless function with a cold-start budget is frequently better served
  by compiling the needed behaviour in directly.
- **The trust model cannot tolerate arbitrary code from third parties, and the
  team is not prepared to build the isolation to make it safe.** Loading and
  running untrusted code inside the host process without a real sandbox is a
  security decision, not an architecture decision, and it should be made
  explicitly, not inherited silently from choosing this pattern. See dimension
  17.
- **A simpler pattern already solves the actual variability.** If the real
  need is one algorithm swapped for another at a single call site, that is
  Strategy. If it is a pipeline of transformations applied in sequence, that is
  Chain of Responsibility or Decorator. Plugin Architecture is frequently
  reached for because it sounds more impressive than these, and the honest test
  is whether the variability crosses a deployment boundary, not merely a class
  boundary.

## 5. Structure

Five participants, named by the role they play. Not every plugin system uses
every participant, and dimension 8 covers the real variation, but a full
system has all five.

- **Core (or Kernel, or Host).** The minimal part of the application that is
  always present, defines the extension contract, and provides the mechanisms
  a plugin needs to participate, discovery, loading, lifecycle management, and
  a way to reach host services. The core does not know the identity of any
  specific plugin at compile time.
- **Extension Point (or Hook, or Contribution Point).** A named location or
  named contract the core exposes, where a plugin can attach behaviour. An
  extension point is either imperative, a named event the core fires that
  plugins subscribe to, such as WordPress actions, or declarative, a schema the
  plugin fills in without writing code that runs at that exact moment, such as
  a VS Code `contributes` block in a plugin's manifest.
- **Plugin (or Extension, or Add-in).** An independently packaged unit that
  implements one or more extension points. A plugin typically ships its own
  manifest describing which extension points it participates in, what
  permissions it requires, and its own version and dependency constraints.
- **Plugin Manager (or Registry, or Loader).** The part of the core responsible
  for discovering available plugins, resolving their dependencies and version
  constraints, loading them in the correct order, and exposing a lookup by
  extension point so the core can invoke the plugins registered against it.
- **Host Services (or Internal Server, or Context).** The bounded surface of
  host functionality a plugin is permitted to call, deliberately narrower than
  the host's full internal API, so that the host retains freedom to change its
  own internals without breaking every plugin, as long as the exposed service
  surface stays stable.

Relationships. Core depends on Extension Point definitions, never on any
Plugin. Plugin depends on Extension Point and on Host Services, never on Core
internals directly. Plugin Manager depends on both Core and the mechanism for
locating installed Plugins, whether that is a filesystem directory, a package
registry, a manifest file, or an operating-system-level dynamic library search
path. This is the same dependency inversion shape as Factory Method, generalised
from a single creation decision to an entire surface of host behaviour, and it
is why the two patterns are frequently composed, with individual extension
points implemented as Factory Methods or Strategy objects that a Plugin Manager
constructs.

## 6. ASCII structure diagram

```
                     +----------------------------+
                     |            Core            |
                     |----------------------------|
                     | defines Extension Points    |
                     | never references a Plugin   |
                     +--------------+--------------+
                                    |
                                    | exposes
                                    v
        +---------------------------------------------------+
        |                  Plugin Manager                    |
        |------------------------------------------------------|
        | discover()   resolve()   load()   lookup(point)      |
        +---------------+---------------------+------------------+
                        |                     |
              discovers |                     | loads and registers
                        v                     v
             +--------------------+  +--------------------+
             |   Plugin Registry   |  |   Loaded Plugin A   |
             |  (filesystem / npm  |  |----------------------|
             |   / manifest scan)  |  | implements Point X   |
             +--------------------+  | implements Point Y   |
                                       +----------+-----------+
                                                  |
                                                  | calls into
                                                  v
                                       +----------------------+
                                       |    Host Services      |
                                       |------------------------|
                                       | narrow, stable surface |
                                       | the Core exposes       |
                                       +----------------------+

                          (a second, independent plugin)
                                       +----------------------+
                                       |   Loaded Plugin B     |
                                       |----------------------  |
                                       | implements Point X     |
                                       +----------------------+
```

Both Plugin A and Plugin B implement Extension Point X without knowing about
each other. The Core, at the moment it fires Point X, has no compile-time
reference to either.

## 7. Dynamics

The runtime flow separates cleanly into a one-time setup phase and a repeated
invocation phase.

```
Startup and discovery phase (runs once per process, or on plugin change)

  Core                Plugin Manager           Filesystem / Registry
   |                        |                            |
   |-- start() ------------>|                            |
   |                        |-- discover() -------------->|
   |                        |<-- list of plugin manifests-|
   |                        |
   |                        |-- for each manifest,
   |                        |     resolve version and dependency constraints
   |                        |     load plugin code (import, dlopen, spawn)
   |                        |     call plugin.apply(hostServices)
   |                        |       plugin registers itself against
   |                        |       one or more Extension Points
   |                        |
   |<-- ready --------------|

Invocation phase (repeats on every relevant event, for the life of the process)

  Caller (host code)     Core / Extension Point       Registered Plugins
   |                            |                             |
   |-- triggers Point X ------->|                             |
   |                            |-- for each plugin at X, --->|
   |                            |                             |-- runs callback
   |                            |                             |-- may mutate payload
   |                            |                             |   or may return a value
   |                            |<-- result or mutated payload |
   |                            |
   |<-- final result -----------|
```

Two shapes of dispatch are both real. The imperative event shape, seen in
WordPress actions and webpack's Tapable-based hooks, runs every registered
callback in registration order and either ignores return values, an action or
a synchronous tap, or threads a value through each callback in turn, a filter
or a waterfall hook. The declarative contribution shape, seen in VS Code's
`contributes` manifest entries, does not run plugin code at the point of
declaration at all, the manifest is read once at activation time and the
plugin's actual code only runs when the specific contributed command, view, or
language feature is invoked by the user, which is why VS Code can install
thousands of extensions and defer most of their code from ever executing during
a session that never touches them.

## 8. Implementation variants

- **In-process, same-language plugins (webpack, WordPress, Fastify).**
  Plugins are loaded into the same process and language runtime as the host,
  typically via the language's own module system. Webpack's plugin system is
  built on the Tapable library, where plugins call `compiler.hooks.<name>.tap`
  or `.tapAsync` to register a callback against a named lifecycle hook, and
  the compiler invokes every tapped callback at that point during a build
  ([webpack documentation, Writing a Plugin](https://webpack.js.org/contribute/plugin-patterns/),
  verified 2026-08-02). Fastify uses a related but distinct in-process model
  built on encapsulation rather than a flat hook list. Each call to
  `fastify.register(plugin)` creates a new child context that inherits every
  decorator, hook, and route from its parent, but nothing a parent registers
  after that point can see into the child, and nothing the child registers is
  visible to siblings or to the parent, unless the plugin is explicitly wrapped
  with `fastify-plugin` to break out of its own scope and register at the
  parent level instead
  ([Fastify documentation, Plugins and Encapsulation](https://fastify.dev/docs/latest/Reference/Encapsulation/),
  verified 2026-08-02). This variant is the cheapest to build and the fastest
  at runtime, because there is no process boundary or serialisation cost, but
  it offers the weakest isolation, a misbehaving plugin can corrupt host state
  directly, since it shares memory and can catch or suppress exceptions from
  the host and vice versa.

- **Out-of-process plugins over RPC (Terraform providers).** Each plugin is a
  separate executable, started as a child process by the host, communicating
  over a local RPC or gRPC channel rather than direct function calls. Terraform
  Core spawns each provider plugin as its own process and every operation, plan,
  apply, read, crosses that RPC boundary
  ([HashiCorp Terraform documentation, How Terraform Works](https://developer.hashicorp.com/terraform/plugin/how-terraform-works),
  verified 2026-08-02). This buys real process isolation, a crashing or
  hanging provider does not crash Terraform Core, and it buys language
  independence, a provider can be written in any language that can speak the
  RPC protocol, at the cost of serialisation overhead on every call and a much
  larger amount of plumbing code to build and maintain the RPC contract itself.

- **Manifest-driven contribution with a separate execution host (VS Code
  extensions).** A plugin declares its capabilities in a static JSON manifest,
  under the `contributes` key of `package.json`, listing commands, menus,
  languages, debuggers, and dozens of other named contribution point kinds,
  without executing any code at declaration time
  ([Visual Studio Code documentation, Contribution Points](https://code.visualstudio.com/api/references/contribution-points),
  verified 2026-08-02). VS Code activates an extension's actual JavaScript
  only when one of its declared activation events fires, and runs every
  extension inside a dedicated Extension Host process, separate from the
  renderer process that draws the editor UI, so that a slow or crashing
  extension degrades or kills that host process without freezing the editor
  window itself. This is a hybrid of the two prior variants, static
  declaration for cheap discovery at scale, combined with process isolation for
  the code that actually runs.

- **Kernel-level bundle and service model (OSGi).** OSGi structures an
  application as a set of bundles, each an independently versioned, installable,
  startable, and stoppable unit of Java code, cooperating through a shared
  service registry that a bundle publishes objects into and other bundles look
  services up from dynamically, entirely inside one JVM. The framework
  specification separates a Module Layer, which governs how bundles share and
  hide Java packages from each other, from a Life Cycle Layer, which governs
  how bundles install, start, stop, update, and uninstall independently of the
  JVM's own lifecycle, from a Service Layer, which provides the actual
  cooperation model where a bundle registers a service object with the
  framework's service registry so other bundles can discover and bind to it at
  run time
  ([OSGi Core Release 8, chapter 4, Life Cycle Layer](https://osgi.github.io/osgi/core/framework.lifecycle.html)
  and
  ([OSGi Core Release 7, chapter 5, Service Layer](https://docs.osgi.org/specification/osgi.core/7.0.0/framework.service.html),
  both verified 2026-08-02). This is the most formally specified variant in
  wide production use, with explicit versioned package import and export
  declarations per bundle, which is what lets multiple versions of the same
  library coexist in one JVM without classpath conflicts, a problem the
  in-process JavaScript and manifest-driven variants above do not solve at all.

- **OS-process boundary with browser sandboxing (Chrome extensions).**
  Extensions declare a background service worker and content scripts in a
  `manifest.json`, and permissions the extension needs are declared statically
  and either granted at install time or requested optionally at run time
  ([Chrome for Developers, Manifest file format](https://developer.chrome.com/docs/extensions/reference/manifest),
  verified 2026-08-02). The content script that touches page content runs in an
  isolated JavaScript world in the page's own process, separate from both the
  page's own script and the extension's background worker, so a page cannot
  directly call into extension code or vice versa without an explicit message
  passing API, which is a variant of the process-isolation idea applied inside
  a single browser process model rather than across OS processes.

## 9. Known production uses

- **webpack**, the JavaScript module bundler, whose plugin system is built on
  the Tapable hook library and documented in webpack's own contributor guide
  for writing plugins that tap into compiler lifecycle events such as `emit`
  ([webpack, Writing a Plugin](https://webpack.js.org/contribute/plugin-patterns/),
  verified 2026-08-02).
- **WordPress**, whose entire theme and plugin ecosystem, tens of thousands of
  public plugins, is built on the actions and filters hook system described in
  its own developer documentation
  ([WordPress Developer Resources, Plugin Hooks](https://developer.wordpress.org/plugins/hooks/),
  verified 2026-08-02).
- **HashiCorp Terraform**, whose provider ecosystem runs every cloud, SaaS, and
  infrastructure integration as an out-of-process RPC plugin discovered during
  `terraform init`
  ([HashiCorp, How Terraform Works](https://developer.hashicorp.com/terraform/plugin/how-terraform-works),
  verified 2026-08-02).
- **Visual Studio Code**, whose extension marketplace is built on the manifest
  contribution point model and a dedicated Extension Host process
  ([VS Code, Contribution Points](https://code.visualstudio.com/api/references/contribution-points),
  verified 2026-08-02).
- **The Eclipse Platform**, one of the original large-scale mainstream
  adopters of the extension point model, built on top of an OSGi runtime and
  documented in the Eclipse Platform Plug-in Developer Guide's extension point
  chapter
  ([Eclipse Platform Plug-in Developer Guide](https://help.eclipse.org/latest/index.jsp?topic=%2Forg.eclipse.platform.doc.isv%2Fguide%2Fextension_point.htm),
  verified 2026-08-02).
- **The OSGi framework itself**, in production inside Eclipse, Apache Karaf,
  and numerous industrial and telecom Java systems, specified formally with a
  Module Layer, Life Cycle Layer, and Service Layer
  ([OSGi Core specification, chapters 4 and 5](https://osgi.github.io/osgi/core/framework.lifecycle.html),
  verified 2026-08-02).
- **Google Chrome and Chromium-based browsers**, whose extension platform is
  specified through `manifest.json` with declared permissions, background
  service workers, and content scripts
  ([Chrome for Developers, Manifest reference](https://developer.chrome.com/docs/extensions/reference/manifest),
  verified 2026-08-02).
- **Fastify**, the Node.js web framework, whose entire feature set beyond a
  bare HTTP server, routing, validation, serialisation, and the rest, is built
  on its own encapsulated plugin registration model
  ([Fastify, Plugins and Encapsulation](https://fastify.dev/docs/latest/Reference/Encapsulation/),
  verified 2026-08-02).

## 10. Consequences

Positive.

- New capability ships as an independent artefact, with its own version, its
  own release schedule, and no required change to the host's own source tree.
- The core can stay small, auditable, and fast to build, because variability
  that would otherwise bloat it lives outside it.
- Third parties, including people outside the maintaining organisation, can
  extend the system without needing commit access or even source access to the
  host.
- Failure and resource usage can be scoped to the specific plugin that causes
  them, in any variant that gives plugins their own process or a strongly
  isolated in-process context, limiting blast radius.
- The ecosystem effect compounds. A healthy plugin marketplace becomes a
  competitive advantage the host itself did not have to build, seen concretely
  in the tens of thousands of WordPress plugins and VS Code extensions cited
  above.

Negative.

- The published extension contract becomes an API the team must support for as
  long as any plugin author depends on it, which is frequently longer and more
  strictly than the team's own internal APIs, because a breaking change fans
  out to every third-party plugin at once rather than to code the team itself
  controls.
- A reader of the host's source code cannot fully know what the running system
  actually does without also knowing the installed plugin set, which
  undermines the value of reading the source as a way to understand behaviour.
- Debugging crosses a boundary the debugger and the stack trace frequently do
  not represent well, especially in the out-of-process RPC variant, where a
  failure surfaces as a serialised error crossing a socket rather than a
  Java-style stack frame the host can walk.
- Discovery, loading, and dispatch cost real startup time and memory,
  proportional to plugin count, which is why editors and build tools with large
  plugin ecosystems invest heavily in lazy activation, as VS Code does with
  activation events.
- Without deliberate isolation, a plugin runs with some or all of the host's
  ambient authority, which converts every installed plugin into part of the
  application's trust boundary, discussed fully in dimension 17.

## 11. Failure modes and misuse

- **Symptom.** The host application slows down or crashes only for certain
  users, and the crash never reproduces on the core team's machine.
  **Cause.** A plugin installed by that user has a bug, a version
  incompatibility with the current host release, or an unbounded loop in a
  hook it registered.
  **Fix.** Add plugin identification to every crash report and log line
  crossing the extension boundary, per dimension 16, and build a mechanism to
  disable a plugin that is suspected of causing instability without disabling
  the whole application, the way both VS Code and WordPress let a user safe-mode
  disable extensions.

- **Symptom.** A minor host release breaks a large fraction of installed
  plugins simultaneously.
  **Cause.** The extension contract was treated as an internal implementation
  detail and changed without a deprecation path, because the team that changed
  it did not think of it as a public API even though hundreds of external
  plugins depended on it.
  **Fix.** Version the extension contract explicitly, separately from the
  host's own release version, and apply real semantic versioning discipline and
  a deprecation window to it, the same discipline the host would apply to a
  published library.

- **Symptom.** Two independently written, individually reasonable plugins,
  each of which passes its own tests, produce corrupted output or a crash only
  when both are installed together.
  **Cause.** Both plugins register against the same extension point and mutate
  a shared payload in an order-dependent way, or both plugins hold an assumption
  about being the only one modifying some piece of host state, an assumption
  that was true when each was tested in isolation.
  **Fix.** Make hook execution order either explicit and documented, or design
  the extension point contract to be commutative, so that the order two
  plugins run in cannot change the result, and add integration tests that run
  combinations of the reference plugins together, not only each in isolation.

- **Symptom.** The application takes several extra seconds to start every time
  a user adds one more plugin, and the delay is present even for plugins the
  user never actually invokes in a session.
  **Cause.** The plugin system discovers and eagerly loads every installed
  plugin's full code at startup, rather than deferring loading until the
  specific capability that plugin provides is actually requested.
  **Fix.** Move to a declarative, lazily activated contribution model, the
  pattern VS Code uses with activation events, where the manifest is read
  cheaply at startup and a plugin's real code is only imported and run the
  first time one of its declared contributions is actually triggered.

- **Symptom.** A plugin, once installed, is discovered to be reading or
  transmitting data far outside what its stated purpose implies, and nothing
  in the host's architecture had prevented it.
  **Cause.** The plugin system was built with no permission model at all, so
  every plugin runs with the full ambient authority of the host process by
  default, which is the in-process variant's default posture unless the team
  deliberately adds constraints.
  **Fix.** Adopt an explicit, declared permission model, the way the Chrome
  extension manifest requires listing `permissions` and `host_permissions`
  up front, so both the platform and the installing user can see and reason
  about what a plugin is entitled to before it runs, per dimension 17.

## 12. Trade-off matrix

Compared against the two most common alternatives a team actually considers
instead of building a full plugin system, Strategy pattern with compile-time
selection, and a monolithic core with feature flags. All three columns share
the same forces from dimension 3.

| Force | Plugin Architecture | Strategy (compile-time) | Monolith with feature flags |
|---|---|---|---|
| Third parties can extend without host source access | Yes, this is the point | No, requires the codebase and a build | No |
| New capability requires a host release | No, in most variants | Yes | Yes, the flag itself ships with a release even if dormant |
| Startup cost | Real, grows with plugin count | Effectively none | Effectively none |
| Failure isolation | Depends on variant, strong in out-of-process, weak in in-process | Whole process, same as monolith | Whole process |
| Contract stability burden | High, contract is a public, versioned promise | Low, an internal interface the team controls end to end | Low, a flag the team controls end to end |
| Best fit | Open-ended, externally driven extension space | Small, closed, known set of variants | Variability the team fully owns and can coordinate internally |
| Debuggability | Crosses a boundary, harder to trace | Ordinary in-process call | Ordinary in-process call, extra branch |

## 13. Related and incompatible patterns

- **Strategy.** Frequently the mechanism by which a single extension point is
  implemented internally. A plugin that provides "the formatter for language
  X" is, structurally, one strategy object being registered into a strategy
  selection map at run time instead of compile time. Plugin Architecture is
  what you get when you generalise Strategy's selection mechanism from a
  single compile-time-known set of choices to an open-ended, dynamically
  discovered set.
- **Observer.** The imperative hook dispatch shape in dimension 7, where the
  core fires a named event and every registered plugin callback runs, is a
  multi-subscriber Observer relationship, with the added
  requirement that subscription happens through a formal, independently
  packaged unit rather than a direct object reference.
- **Template Method.** A host that defines a fixed overall algorithm with
  specific steps left open for plugins to fill in, common in build tools where
  the overall build pipeline is fixed but individual transform steps are
  pluggable, is Template Method applied at the architectural rather than the
  class level.
- **Chain of Responsibility.** Filter-style hooks, where a value passes through
  every registered plugin callback in sequence, each free to transform it
  before passing it on, is structurally a Chain of Responsibility where the
  chain membership is determined by plugin installation rather than a fixed,
  compiled list.
- **Dependency Injection.** Host Services, the narrow surface a plugin is
  permitted to call, is frequently implemented by injecting a services object
  or context into the plugin's registration function, the same mechanism
  dependency injection containers use to hand collaborators to a component
  without that component constructing them itself.
- **Service Locator.** Where a plugin looks up a host capability by name at the
  moment it needs it, rather than having it injected up front, the host is
  acting as a Service Locator for that plugin, with the accompanying trade-off
  that dependencies become implicit and harder to statically verify, the
  standard criticism levelled at Service Locator versus Dependency Injection.
- **Singleton, incompatible in intent.** A plugin system's entire purpose is to
  allow multiple independent, dynamically discovered implementations of a
  capability to coexist. A Singleton enforced at the extension point itself,
  the rule that there can only ever be one active formatter plugin, works
  against the pattern's own value proposition and should instead be handled as
  a policy the Plugin Manager enforces at registration time, such as taking the
  last registered plugin or requiring explicit priority ordering, rather than
  by baking a single-instance constraint into the extension point's type itself.

## 14. Refactoring path in and out

Introducing Plugin Architecture into a codebase that does not have it, step by
step.

1. Identify the specific behaviour that is genuinely open-ended and externally
   driven, not merely "this branches on a type," using the applicability test
   in dimension 4. Resist the temptation to generalise more surface area than
   the actual evidence supports.
2. Extract the current, hard-coded implementations of that behaviour behind a
   single interface, without yet introducing any discovery mechanism. This step
   alone is often a Strategy or Template Method extraction, and it is where the
   real design work of naming the contract correctly happens.
3. Build the narrowest possible Host Services surface the new interface's
   implementations actually need, resisting the urge to expose the host's full
   internal API. Every method added here is a method the host must keep stable
   going forward.
4. Introduce a Plugin Manager that can load implementations of the interface
   from a fixed, known location first, for example a directory the team
   controls, before opening discovery to arbitrary third-party locations. This
   proves the mechanism works with a controlled blast radius.
5. Version the extension point contract explicitly, separately from the host's
   own release version, before publishing it externally, and write down the
   deprecation policy before the first external plugin author depends on it,
   not after.
6. Open discovery to external plugin sources only once the contract has proven
   stable across at least one full deprecation cycle internally, and add the
   permission and isolation model from dimension 17 at this point, before any
   untrusted code is loaded, not as a later hardening pass.

Removing Plugin Architecture when it stops earning its place, which happens
when the extension space turns out to be small and closed after all, or when
the team decides the security and compatibility burden outweighs the
flexibility gained.

1. Inventory every plugin actually in production use. Extension points with
   zero real-world implementations besides the ones the host team itself wrote
   are the cheapest to fold back in first.
2. For each extension point being retired, convert its remaining
   implementations back into an internal Strategy selection, compiled directly
   into the host, preserving the interface shape so the change is a mechanical
   dependency inversion in reverse rather than a rewrite.
3. Communicate the deprecation and removal of the extension point itself on
   the same public timeline the team used to publish it, since external plugin
   authors relied on a promise, not merely on convenience.
4. Remove the discovery, loading, and isolation machinery only after the last
   supported version that still honours the old contract has reached its own
   end of support, not immediately when the last internal usage disappears.

## 15. Testing and verification

Plugin Architecture makes the core easier to test in isolation and makes the
integrated system harder to test exhaustively, and both halves of that
statement matter.

Testing the core becomes cleaner because the core can be tested against a
small number of reference or mock plugins that implement the contract
minimally, verifying that the Plugin Manager discovers, loads, and dispatches
correctly, without needing every real-world plugin present. A fake plugin that
records every call it receives, a classic test double in the spy shape, is
usually sufficient to verify dispatch order, error handling when a plugin
throws, and that Host Services are passed correctly.

Testing an individual plugin becomes cleaner too, because a well-designed
Host Services surface is itself a natural seam. A plugin author can write unit
tests against a fake or in-memory implementation of Host Services, without
needing the real host application running at all, the same benefit dependency
injection gives any component that receives its collaborators rather than
constructing them.

What becomes genuinely harder is verifying the combined system. The
combinatorial space of which plugins a real user has installed, in which
versions, in which order, is not something a core team can exhaustively test,
and this is the honest limitation of the pattern rather than a solvable testing
gap. The practical response used across the production systems in dimension 9
is a tiered strategy, contract tests that every plugin, official or
third-party, must pass to be listed or trusted, a small curated set of
representative real-world plugins run together in CI as an integration
smoke test, and telemetry from production, discussed in dimension 16, that
surfaces which real combinations are actually breaking for real users, since
that data cannot be fully anticipated in a test lab.

## 16. Observability signals

- **Per-plugin identification on every log line and error that crosses the
  extension boundary.** A stack trace or error message that does not name
  which plugin produced it is close to useless in a system with more than a
  handful of plugins installed, because the failure modes in dimension 11 are
  overwhelmingly plugin-attributable, not core-attributable.
- **Plugin load time and load success or failure, per plugin, at startup.**
  A healthy instance shows every declared plugin loading within an expected
  time budget. A degrading instance shows load time creeping upward as plugin
  count grows, or an increasing rate of load failures, both signals worth
  alerting on independently of any user-visible symptom.
- **Hook or extension point invocation count and latency, per plugin, per
  extension point.** This is the signal that answers which installed plugin is
  actually slowing this operation down, and without it, a slow build or a slow
  editor action is a mystery the operator has no way to decompose.
- **Per-plugin resource usage, memory and, in an out-of-process variant, CPU
  and process count.** A leaking or runaway plugin is otherwise
  indistinguishable from a leak in the host's own core, which sends
  investigation in the wrong direction.
- **Extension point contract version in use per plugin.** As the contract
  evolves per dimension 14, a dashboard that shows how many installed plugins
  still target a deprecated contract version is the operational signal that
  tells the team when it is actually safe to remove backward compatibility
  shims, rather than guessing.

## 17. Security and privacy implications

This dimension is largely analytical judgement about attack surface, applied
to the specific mechanics documented in the sourced claims above about how
each real system actually isolates, or does not isolate, plugin code.

Plugin Architecture, by default, in the plain in-process variant described
first in dimension 8, gives every loaded plugin the full ambient authority of
the host process, the same filesystem access, network access, and memory space
the host itself has, unless the team deliberately builds a narrower boundary.
This makes the trust model, who is allowed to author a plugin, the single most
important security decision in the whole system, more important than any
code-level review of the plugin mechanism itself, because a plugin author with
malicious or merely careless intent inherits everything the host process can
do.

The production systems cited in dimension 9 make visibly different choices on
this axis, and the differences are instructive. Terraform isolates every
provider in its own OS process communicating over RPC, which contains a
crashing or hanging provider but does not, by itself, prevent a malicious
provider from exfiltrating credentials it is handed for legitimate
authentication purposes, since the RPC boundary constrains crash propagation
and API shape, not data flow. Chrome extensions declare permissions and host
match patterns statically in the manifest, which the platform and, for
sensitive permissions, the user can inspect and approve before the extension
is even installed, and the content script isolated world specifically prevents
a compromised web page from reaching directly into extension code, a threat
model distinct from a malicious extension itself. VS Code runs extensions in a
dedicated Extension Host process, which is genuine process isolation from the
renderer that draws the UI, but is not, as of the documentation reviewed here,
a sandbox that limits what an extension's own code can do with the filesystem
or network from inside that host process, so the practical trust boundary for
VS Code extensions is closer to trusting what is let into the marketplace than
to a hard technical sandbox. OSGi's Module Layer can enforce which Java
packages a bundle exports and imports, which limits accidental coupling and
classpath collisions, but package visibility control is not the same claim as
a security sandbox, and OSGi does not, by itself, prevent a bundle with a
service reference from calling any method that service exposes.

The privacy implication follows directly from the trust model. Any data a
plugin's registered hook or extension point receives as part of its call
signature is data that plugin, and everything that plugin's own dependencies
can do, has access to. A design decision in dimension 5, keeping Host Services
deliberately narrow, is therefore also a privacy decision, not merely an API
cleanliness one, because every field included in a payload passed to a hook is
a field every installed plugin targeting that hook can read, log, or transmit
elsewhere, whether or not the plugin's stated purpose has any legitimate need
for it.

Where this dimension is silent, plainly. This entry does not make a claim
about which specific sandboxing technology, a WebAssembly runtime, a container,
a language-level capability system, is the correct choice for a new system,
because that decision depends on the host's language, deployment target, and
threat model in ways too specific to generalise here, and none of the sources
reviewed for this entry made a settled cross-ecosystem recommendation on that
point.

## 18. References

- Frank Buschmann, Regine Meunier, Hans Rohnert, Peter Sommerlad, Michael Stal,
  *Pattern-Oriented Software Architecture, Volume 1, A System of Patterns*,
  Wiley, 1996, chapter 2, Microkernel.
- Eclipse Platform Plug-in Developer Guide, extension point concepts,
  https://help.eclipse.org/latest/index.jsp?topic=%2Forg.eclipse.platform.doc.isv%2Fguide%2Fextension_point.htm,
  verified 2026-08-02.
- WordPress Developer Resources, Plugin Handbook, Hooks,
  https://developer.wordpress.org/plugins/hooks/, verified 2026-08-02.
- webpack documentation, Writing a Plugin, plugin patterns,
  https://webpack.js.org/contribute/plugin-patterns/, verified 2026-08-02.
- HashiCorp Developer, Terraform Plugin documentation, How Terraform Works,
  https://developer.hashicorp.com/terraform/plugin/how-terraform-works,
  verified 2026-08-02.
- Visual Studio Code API documentation, Contribution Points,
  https://code.visualstudio.com/api/references/contribution-points,
  verified 2026-08-02.
- OSGi Alliance, OSGi Core Release 8, chapter 4, Life Cycle Layer,
  https://osgi.github.io/osgi/core/framework.lifecycle.html, verified
  2026-08-02.
- OSGi Alliance, OSGi Core Release 7, chapter 5, Service Layer,
  https://docs.osgi.org/specification/osgi.core/7.0.0/framework.service.html,
  verified 2026-08-02.
- Chrome for Developers, Extensions, Manifest file format,
  https://developer.chrome.com/docs/extensions/reference/manifest, verified
  2026-08-02.
- Fastify documentation, Reference, Encapsulation,
  https://fastify.dev/docs/latest/Reference/Encapsulation/, verified
  2026-08-02.

## Code examples

Four implementations of the same minimal host, a two-plugin pipeline that
uppercases text and then appends an exclamation mark, chosen because they
show the pattern's essential shape, a Host that owns a hook registry, and
Plugins that receive the host and register callbacks against a named hook,
without any framework scaffolding. All four were compiled or run directly on
this machine and produced the expected output, `HELLO PLUGIN ARCHITECTURE!`.
Java was omitted because no Java runtime was available on this machine to
compile or run it against, not because the pattern does not translate, Java is
in fact the language OSGi itself is specified for. Swift and Kotlin were
omitted because verifying them here would require hand-checking without a
compiler, which the template explicitly allows but this entry did not need,
given four other languages already verified.

### TypeScript

```typescript
type HookFn = (payload: { text: string }) => void;

class HookRegistry {
  private hooks = new Map<string, HookFn[]>();

  tap(name: string, fn: HookFn): void {
    const list = this.hooks.get(name) ?? [];
    list.push(fn);
    this.hooks.set(name, list);
  }

  call(name: string, payload: { text: string }): void {
    for (const fn of this.hooks.get(name) ?? []) {
      fn(payload);
    }
  }
}

interface PluginModule {
  apply(hooks: HookRegistry): void;
}

class UpperCasePlugin implements PluginModule {
  apply(hooks: HookRegistry): void {
    hooks.tap("beforeEmit", (payload) => {
      payload.text = payload.text.toUpperCase();
    });
  }
}

class ExclaimPlugin implements PluginModule {
  apply(hooks: HookRegistry): void {
    hooks.tap("beforeEmit", (payload) => {
      payload.text = payload.text + "!";
    });
  }
}

class Host {
  private hooks = new HookRegistry();

  use(plugin: PluginModule): this {
    plugin.apply(this.hooks);
    return this;
  }

  emit(text: string): string {
    const payload = { text };
    this.hooks.call("beforeEmit", payload);
    return payload.text;
  }
}

const host = new Host().use(new UpperCasePlugin()).use(new ExclaimPlugin());
console.log(host.emit("hello plugin architecture"));
```

Compiled with `npx tsc host.ts --target es2020 --module commonjs --strict`
and run with `node host.js`. Zero errors, output
`HELLO PLUGIN ARCHITECTURE!`. The interface is named `PluginModule` rather than
`Plugin` because the DOM library ships a global type named `Plugin`, and this
turned into a genuine compile error the first time this sample was written,
worth knowing as a real-world gotcha, not only a naming preference.

### Python

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Payload:
    text: str


class Plugin(ABC):
    @abstractmethod
    def apply(self, host: "Host") -> None:
        raise NotImplementedError


class UpperCasePlugin(Plugin):
    def apply(self, host: "Host") -> None:
        host.tap("before_emit", lambda p: setattr(p, "text", p.text.upper()))


class ExclaimPlugin(Plugin):
    def apply(self, host: "Host") -> None:
        host.tap("before_emit", lambda p: setattr(p, "text", p.text + "!"))


class Host:
    def __init__(self) -> None:
        self._hooks: dict[str, list] = {}

    def tap(self, name: str, fn) -> None:
        self._hooks.setdefault(name, []).append(fn)

    def use(self, plugin: Plugin) -> "Host":
        plugin.apply(self)
        return self

    def emit(self, text: str) -> str:
        payload = Payload(text)
        for fn in self._hooks.get("before_emit", []):
            fn(payload)
        return payload.text


if __name__ == "__main__":
    host = Host().use(UpperCasePlugin()).use(ExclaimPlugin())
    print(host.emit("hello plugin architecture"))
```

Run with `python3 host.py`. Output `HELLO PLUGIN ARCHITECTURE!`.

### Go

```go
package main

import (
	"fmt"
	"strings"
)

type Payload struct {
	Text string
}

type HookFn func(*Payload)

type Host struct {
	hooks map[string][]HookFn
}

func NewHost() *Host {
	return &Host{hooks: make(map[string][]HookFn)}
}

func (h *Host) Tap(name string, fn HookFn) {
	h.hooks[name] = append(h.hooks[name], fn)
}

func (h *Host) Emit(text string) string {
	p := &Payload{Text: text}
	for _, fn := range h.hooks["beforeEmit"] {
		fn(p)
	}
	return p.Text
}

type Plugin interface {
	Apply(h *Host)
}

type UpperCasePlugin struct{}

func (UpperCasePlugin) Apply(h *Host) {
	h.Tap("beforeEmit", func(p *Payload) {
		p.Text = strings.ToUpper(p.Text)
	})
}

type ExclaimPlugin struct{}

func (ExclaimPlugin) Apply(h *Host) {
	h.Tap("beforeEmit", func(p *Payload) {
		p.Text = p.Text + "!"
	})
}

func Use(h *Host, plugins ...Plugin) *Host {
	for _, p := range plugins {
		p.Apply(h)
	}
	return h
}

func main() {
	h := Use(NewHost(), UpperCasePlugin{}, ExclaimPlugin{})
	fmt.Println(h.Emit("hello plugin architecture"))
}
```

Run with `go run main.go`. Output `HELLO PLUGIN ARCHITECTURE!`.

### Rust

```rust
struct Payload {
    text: String,
}

type HookFn = Box<dyn Fn(&mut Payload)>;

struct Host {
    hooks: Vec<HookFn>,
}

impl Host {
    fn new() -> Self {
        Host { hooks: Vec::new() }
    }

    fn tap(&mut self, fn_: HookFn) {
        self.hooks.push(fn_);
    }

    fn emit(&self, text: &str) -> String {
        let mut payload = Payload { text: text.to_string() };
        for hook in &self.hooks {
            hook(&mut payload);
        }
        payload.text
    }
}

trait Plugin {
    fn apply(&self, host: &mut Host);
}

struct UpperCasePlugin;
impl Plugin for UpperCasePlugin {
    fn apply(&self, host: &mut Host) {
        host.tap(Box::new(|p: &mut Payload| {
            p.text = p.text.to_uppercase();
        }));
    }
}

struct ExclaimPlugin;
impl Plugin for ExclaimPlugin {
    fn apply(&self, host: &mut Host) {
        host.tap(Box::new(|p: &mut Payload| {
            p.text.push('!');
        }));
    }
}

fn use_plugin(host: &mut Host, plugin: &dyn Plugin) {
    plugin.apply(host);
}

fn main() {
    let mut host = Host::new();
    use_plugin(&mut host, &UpperCasePlugin);
    use_plugin(&mut host, &ExclaimPlugin);
    println!("{}", host.emit("hello plugin architecture"));
}
```

Compiled with `rustc main.rs -o main` and run with `./main`. Output
`HELLO PLUGIN ARCHITECTURE!`.

These four samples deliberately show the same in-process, direct-dispatch
variant from dimension 8, because that variant is the one that translates
cleanly into a short, dependency-free sample in every language. The
out-of-process RPC variant, the manifest-driven declarative variant, and the
OSGi service-registry variant are all real and all documented in dimension 8
with their production sources, but each requires either a second process, a
serialisation library, or a full OSGi framework to demonstrate honestly, which
would no longer be a minimal sample and was left as prose rather than
padded into a misleadingly small code listing.
