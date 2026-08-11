---
name: Plugin
slug: plugin
family: 06-enterprise-application-architecture
category: Structural
aliases: [Extension Point, Provider, Add-in, Loadable Module]
first_described: "Fowler 2002"
maturity: canonical
related: [separated-interface, service-locator, dependency-injection, factory-method, observer, strategy]
incompatible_with: []
verified: 2026-08-02
---

# Plugin

## 1. Name, aliases, and lineage

The canonical name in enterprise application architecture is Plugin. Martin
Fowler catalogued it in *Patterns of Enterprise Application Architecture*,
Addison-Wesley, 2002, in the chapter on base patterns, stating the pattern's
intent as "links classes during configuration rather than compilation"
([martinfowler.com/eaaCatalog/plugin.html](https://martinfowler.com/eaaCatalog/plugin.html),
verified 2026-08-02). Fowler's problem statement is that a system needs to run
in more than one deployment environment (an in-memory fake in tests, a real
gateway to an external system in production, a different vendor database
across customers) and that scattering conditional logic to pick the right
implementation throughout the codebase produces exactly the kind of mess a
Factory is meant to prevent, if the Factory itself has to run that same
conditional every time it is called (Fowler, EAA, 2002, same page).

The word "plugin" is older and broader than Fowler's catalog entry, and the
industry uses it for a family of closely related ideas that this entry
separates carefully, because conflating them is the most common source of
confusion in code review.

- **Fowler's Plugin (configuration-time binding).** A specific technique for
  resolving which concrete implementation of an interface a factory returns,
  decided once at application start-up from an external configuration file,
  never recompiled to change the answer. This is a corollary of Separated
  Interface. The interface lives in one package, several implementations live
  in separate packages, and a plugin factory reads configuration to decide
  which implementation package to instantiate for this deployment (Fowler,
  EAA, 2002, Plugin and Separated Interface entries).
- **Plugin architecture (extensibility framework).** A host application ships
  a stable extension mechanism, and third parties author independently
  deployed modules that extend the host's behavior without modifying or
  recompiling the host. Eclipse, WordPress, Webpack, browsers, and IDEs all use
  this shape. The host does not merely pick between two known implementations
  of one interface at start-up, it discovers an open-ended, unknown-at-build-time
  set of extensions, often supplied by parties the host's authors never met.
- **Language-level service provider mechanism.** A standard library facility,
  such as `java.util.ServiceLoader`, that discovers implementations of a
  service interface at runtime from declarative provider files, without either
  side depending on the other's concrete package
  ([Oracle Java 17 API docs for `java.util.ServiceLoader`](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/ServiceLoader.html),
  verified 2026-08-02).

These three sit on a scale from narrowest to broadest. Fowler's Plugin picks
one implementation from a small, known set. A plugin architecture accepts an
open set of extensions the host never enumerates. A service provider mechanism
is the language-level plumbing that both of the other two are commonly built
on top of. This entry treats all three as one family because they share the
same structural shape, an interface the host depends on, one or more
implementations the host does not depend on, and a resolution step that
connects them without a compile-time reference. Production systems routinely
combine all three in one deployment, as the known-uses section shows.

## 2. Problem and context

An application has a piece of behavior that legitimately differs across
deployments, and the difference is not a business rule that changes with
input, it is a difference in which implementation runs at all. A payment
service uses a real gateway in production and an in-memory fake in the test
suite. A CMS runs with a MySQL adapter for one customer and a Postgres adapter
for another. An IDE ships a syntax highlighter for the languages its authors
anticipated, and needs a path for a third party to add support for a language
they did not.

The naive fix is a conditional such as `if (environment == "test") return new
FakeGateway(); else return new RealGateway();`. This works until a third
environment appears, and it works until the class that holds the conditional
needs to be compiled against every implementation it might return, which means
a test-only fake ships inside the production artifact and a vendor-specific
adapter ships inside every customer's build whether or not that customer uses
that vendor. Fowler's specific framing is that this conditional logic tends to
migrate into the Factory that is supposed to hide it, and the Factory itself
then needs the same recompile-per-environment cycle it was meant to remove
(Fowler, EAA, 2002, Plugin entry).

The broader plugin-architecture problem is different in degree, not kind. A
host application wants to be extensible by parties who will never see its
source tree, who ship on their own schedule, and whose combined feature set
the host's authors cannot enumerate at build time. Eclipse describes this
directly, a plugin is "a component that provides a certain type of service
within the context of the Eclipse workbench," and the workbench itself is
assembled almost entirely out of plugins, including the parts a newcomer would
assume are core
([eclipse.org, Eclipse plugin architecture article](https://www.eclipse.org/articles/Article-Plug-in-architecture/plugin_architecture.html),
verified 2026-08-02). The context that creates the need is always the same
shape. A stable core that must not know, at compile time, the full list of
things that will eventually plug into it, because that list grows after the
core ships.

## 3. Forces

**Decoupling versus discoverability.** The whole point of the pattern is that
the host does not depend on the plugin's package. That decoupling has a cost.
The host must discover the plugin some other way, at a point that is later
than compile time and therefore slower, more error-prone, and harder to debug
than a direct reference. Every implementation variant in this entry is really
a different answer to how the host finds out this plugin exists.

**Stability of the extension contract versus the freedom to evolve it.** Once
third parties build against an extension point, the host cannot change that
interface's shape without breaking every plugin built against the old shape.
Eclipse's extension-point mechanism versions extension-point schemas
explicitly for exactly this reason. A tightly coupled Strategy interface
inside one team's codebase can be refactored freely, a published plugin
contract cannot, because the host no longer controls the call sites.

**Isolation versus performance.** A plugin that can crash, hang, or corrupt
the host's memory defeats the purpose of isolating it in the first place, but
process-level isolation (a separate process, a sandbox, a WebAssembly module)
costs a serialization boundary on every call across it. In-process plugins
(a loaded class, a `.so`, a dynamically imported module) are fast but share a
fault domain with the host, so a segfaulting plugin can take the host process
down with it.

**Trust versus openness.** A host that lets anyone install a plugin is more
useful and more dangerous. A browser extension, an npm postinstall script, and
a WordPress plugin from an unaudited repository can all run arbitrary code
with the host's ambient privileges. The wider the host opens its extension
mechanism, the more its own security posture depends on code it did not
write and cannot fully review.

**Configuration cost versus flexibility.** Fowler's narrow Plugin trades a
small amount of start-up configuration parsing for the ability to swap an
entire implementation without touching source. That trade is close to free
when there are two or three implementations. It stops being free when the
configuration format itself becomes a second, informally typed programming
language that nobody remembers how to debug, which is the standard failure
mode of large XML-configured plugin systems from the 2000s.

## 4. Applicability and non-applicability

Reach for Plugin when the following hold.

- The application must run in genuinely different environments (test versus
  production, on-premise versus SaaS, vendor A versus vendor B) where the
  difference is a whole implementation, not a parameter.
- Third parties, including a future version of the same team, need to extend
  behavior without recompiling or redeploying the host, and the set of
  extensions is not fully known when the host ships.
- The interface being varied is stable enough to publish as a contract other
  parties will build against, because every plugin built against it becomes a
  compatibility obligation.
- The cost of a discovery mechanism (a configuration file, a manifest, a
  registry) is justified by the number of swap points or the number of
  external contributors, not by a single call site that will only ever have
  one implementation.

Do NOT reach for Plugin when any of these hold.

- There is exactly one implementation today and no credible plan for a second.
  Plugin adds an indirection layer, a discovery mechanism, and a configuration
  surface for a variability that does not exist yet. This is the textbook case
  of speculative generality, and the fix, when the second implementation
  actually appears, is a small refactor to introduce the interface then, not a
  pre-built extension point that sits unused.
- The variation is a parameter, not an implementation. If two behaviors differ
  by a threshold, a feature flag, or a strategy object chosen from a small
  closed set known at compile time, a plain Strategy or a conditional is
  cheaper and easier to trace than a plugin discovery mechanism.
- The team controls every caller and every callee, and both live in the same
  deployable artifact with the same release cadence. Plugin earns its cost
  specifically when the caller and callee are compiled, tested, and shipped on
  independent schedules. When they are not, ordinary polymorphism gives the
  same decoupling with none of the discovery machinery.
- The extension needs to run with less trust than the host, or the host cannot
  afford the availability risk of a third-party module crashing the host
  process, and the team is not prepared to build the process or sandbox
  isolation that trust boundary requires. A plugin architecture with no
  isolation story is a security and reliability liability, not a feature.
- Startup latency is on a tight budget and the plugin set is large. Discovery
  by directory scan, classpath scan, or reflection has a real and sometimes
  substantial cost that grows with the number of installed plugins. Eclipse's
  own architecture addresses this directly with lazy plugin activation rather
  than eager scanning at every start-up (eclipse.org, Eclipse plugin
  architecture article, verified 2026-08-02).

## 5. Structure

**Host (Application Kernel).** The stable core that defines the extension
point and drives the application's main control flow. It depends only on the
Plugin Interface, never on any concrete plugin.

**Plugin Interface (Extension Point or Service Interface).** The contract a
plugin must satisfy to participate. This is Separated Interface applied at the
package or module boundary. The interface's compilation unit does not depend
on any implementation's compilation unit (Fowler, EAA, 2002, Separated
Interface entry).

**Plugin (Extension or Provider).** A concrete implementation of the Plugin
Interface, packaged and deployed independently of the Host. A production
system usually has zero, one, or many plugins active for a given extension
point, and the Host must handle all three counts correctly.

**Plugin Descriptor (Manifest or Provider-Configuration File).** A declarative
artifact, external to compiled code, that names which class implements which
interface. Eclipse's `plugin.xml` and Java's `META-INF/services/<interface>`
file are the same idea in different formats, a text file the Host reads at
runtime instead of a symbol the compiler resolves at build time (Oracle
ServiceLoader docs, verified 2026-08-02; eclipse.org, Eclipse plugin
architecture article, verified 2026-08-02).

**Plugin Registry (Loader or Locator).** The component that reads the
Descriptor, resolves the named classes (via reflection, dynamic import,
classpath scan, or dynamic library load), instantiates them, and hands the
Host a collection of live Plugin instances or a lazy handle to them.

**Extension Point (in the wider plugin-architecture sense).** A named slot the
Host publishes, with its own schema describing what a plugin registering
against that slot must supply. Eclipse allows "multiple plug-ins" to extend
one extension point, and allows "a given plug-in" to extend the same extension
point more than once, which is why the Registry returns a collection, not a
single instance (eclipse.org, Eclipse plugin architecture article, verified
2026-08-02).

## 6. ASCII structure diagram

```
+-----------------------------------------------------------+
|                            Host                            |
|  depends on -->  PluginInterface (Separated Interface)     |
|                         ^        ^        ^                |
+-------------------------|--------|--------|-----------------+
                           |        |        |
              implements  |        |        |  implements
                           |        |        |
                 +---------+--+  +--+---------+  +-----------+
                 | PluginA    |  | PluginB    |  | PluginC    |
                 | (compiled  |  | (compiled  |  | (compiled  |
                 |  and       |  |  and       |  |  and       |
                 |  deployed  |  |  deployed  |  |  deployed  |
                 |  separate  |  |  separate  |  |  separate  |
                 |  from      |  |  from      |  |  from      |
                 |  Host)     |  |  Host)     |  |  Host)     |
                 +------------+  +------------+  +------------+

  Descriptor (config, manifest, or META-INF/services file)
  +---------------------------------------------------------+
  |  extensionPoint = "com.acme.storage"                     |
  |    -> com.vendorA.S3Storage                               |
  |    -> com.vendorB.GcsStorage                               |
  +---------------------------------------------------------+
                           |
                           v
                 +-------------------+
                 |  PluginRegistry   |  reads Descriptor,
                 |  (discovery +     |  resolves classes,
                 |   instantiation)  |  returns instances
                 +---------+---------+
                           |
                           v
                    Host holds a
                 List<PluginInterface>
                 or Map<key, PluginInterface>,
                 never a concrete class name
```

Note that the Host's dependency arrow points only at `PluginInterface`. No
arrow runs from the Host box to any of PluginA, PluginB, or PluginC. That
missing arrow is the entire pattern, every mechanism below exists solely to
let the Host acquire an instance it does not, and structurally cannot,
reference by name.

## 7. Dynamics

```
Startup sequence (configuration-time binding, Fowler's narrow Plugin)
-----------------------------------------------------------------
Host.start()
  -> PluginRegistry.discover()
       -> read descriptor file(s) from a known location
       -> for each entry: resolve class by fully qualified name
            -> Class.forName(name) / import(path) / dlopen(path)
       -> for each resolved class: instantiate (no-arg constructor
          or a documented factory method)
       -> validate: does the instance satisfy PluginInterface?
            -> no  : fail fast, name the bad entry, do not silently skip
            -> yes : add to registry
  -> Host receives collection of PluginInterface instances
  -> Host proceeds to serve requests using only PluginInterface calls

Request-time sequence (extension-point invocation, Eclipse/WordPress shape)
-----------------------------------------------------------------
Host reaches ExtensionPoint("acme.storage.save")
  -> Registry.lookup("acme.storage.save")
       returns [ PluginA, PluginB ]     (zero, one, or many)
  -> for each Plugin in that list, in a defined order:
       Host invokes Plugin.handle(context)
       Plugin may:
         (a) act and return, unmodified context flows to the next plugin
             (action-style, side-effecting, WordPress "action" hooks)
         (b) transform the context and return the new value, which
             becomes the input to the next plugin in the chain
             (filter-style, WordPress "filter" hooks)
  -> Host proceeds with the (possibly transformed) result

WordPress states the same two shapes directly. an action "takes the info
it receives, does something with it, and returns nothing," while a filter
"takes the info it receives, modifies it somehow, and returns it"
(developer.wordpress.org, Plugin Hooks documentation, verified 2026-08-02).
```

## 8. Implementation variants

**Configuration-file binding (Fowler's canonical Plugin).** A properties,
YAML, or JSON file maps an interface's fully qualified name to the concrete
class to instantiate. A small factory reads the file once at start-up,
resolves the class by reflection, and caches the singleton. This is the
cheapest variant to build and the right default for the narrow case of one of
a small known set of implementations, chosen per deployment.

**Provider-configuration file, language-native (Java `ServiceLoader`).** The
JDK standard library formalizes the same idea. A text file at
`META-INF/services/<fully.qualified.ServiceInterface>` lists implementation
class names, one per line, and `ServiceLoader.load(ServiceInterface.class)`
returns a lazily instantiated iterator over them (Oracle ServiceLoader docs,
verified 2026-08-02). Since Java 9, the same registration can be declared in a
module's `module-info.java` with a `provides ... with ...` directive instead
of the text file. This variant needs no third-party dependency and composes
naturally with a build that already produces a JAR per plugin.

**Manifest-driven extension points (Eclipse OSGi model).** Each plugin ships
its own `plugin.xml` declaring both the extension points it publishes and the
extensions it contributes to other plugins' extension points. The platform
maintains a central plugin registry built by parsing every manifest at
start-up, and defers actual class loading until an extension is genuinely
invoked, which Eclipse's own article calls out as a deliberate lazy
instantiation strategy to keep start-up fast even with hundreds of installed
plugins (eclipse.org, Eclipse plugin architecture article, verified
2026-08-02). This variant is the right shape when extension points are
plentiful, plugin counts are large, and eager instantiation of everything
would make start-up unacceptably slow.

**Hook chain, in-process (WordPress actions and filters).** Rather than one
plugin per interface, a single named hook accepts any number of registered
callbacks, invoked in priority order. Actions run for side effects and ignore
return values, filters thread a value through the chain, each callback
transforming the value handed to the next (developer.wordpress.org, Plugin
Hooks documentation, verified 2026-08-02). This variant trades interface
discipline for extreme flexibility. A hook is just a name and a callable
signature, so adding a new extension point costs a single function call
(`add_action` or `apply_filters`) with no manifest, no interface declaration,
and no registry to update.

**Build-pipeline plugin, `apply(host)` contract (Webpack's Tapable model).** A
plugin is any object exposing an `apply(compiler)` method, the compiler passes
itself in, and the plugin registers callbacks (`tap`, `tapAsync`, or
`tapPromise`) against named lifecycle hooks the compiler exposes
(webpack.js.org, Plugin API documentation, verified 2026-08-02). Unlike the
Eclipse or `ServiceLoader` variants, discovery here is explicit and
programmatic. The host application's own configuration file lists plugin
instances directly (`plugins: [new MyPlugin()]`), so there is no manifest
scan, but the plugin still never appears in the compiler's own compiled
dependency graph, which is what keeps this a Plugin and not a hard-coded call.

**Dynamic library loading (native `.so`, `.dll`, or `.dylib`).** The host
calls `dlopen`/`LoadLibrary` on a path resolved at runtime, then looks up a
well-known exported symbol (often a factory function with a fixed C ABI
signature, because C++ name mangling and object layout are not
ABI-stable across compilers). This is the lowest-level and highest-performance
variant, used when the plugin boundary must cross a language or compiler
boundary, and it forgoes almost all of the type safety the other variants
retain, because the compiler cannot check that the loaded symbol actually
matches the expected signature.

**Out-of-process or sandboxed plugin (browser extensions, WebAssembly
modules).** The plugin runs in a separate process or a sandboxed runtime with
a narrow, capability-scoped API surface, and every call across the boundary is
serialized (message passing, RPC, or a WASM host-function import table). This
variant answers the isolation-versus-performance force in dimension 3 by
paying a serialization cost on every call in exchange for a fault and
trust boundary a crashing or malicious plugin cannot cross.

## 9. Known production uses

**Eclipse IDE and OSGi-based platforms.** The Eclipse workbench itself is
built almost entirely as a set of plugins communicating through extension
points. The platform's own article states plainly that non-core plugins
activate only when transitively required by another plugin, and that
extension processing instantiates provider objects lazily rather than at
platform start-up (eclipse.org, Eclipse plugin architecture article, verified
2026-08-02). Extension points are versioned, schema-checked slots, and "a
given plug-in may extend a given extension-point multiple times," which is
why any faithful implementation of this pattern returns a collection from the
registry lookup, never a single instance (same source).

**WordPress.** WordPress core exposes named hooks throughout its request
lifecycle. Plugin and theme authors register callbacks against those hooks
using `add_action` (for side-effecting extensions) and `add_filter` (for
value-transforming extensions), and WordPress's own developer documentation
states the action and filter distinction plainly, an action "returns
nothing," a filter "modifies it somehow, and returns it"
(developer.wordpress.org, Plugin Hooks documentation, verified 2026-08-02).
This is the hook-chain variant from dimension 8, running at population scale.
WordPress powers a large share of the web's content management systems, and
essentially none of that ecosystem's plugin code is compiled against
WordPress core.

**Webpack.** The Webpack module bundler's entire build pipeline is built
around Tapable, a small hook library. A plugin is any object with an
`apply(compiler)` method, and it registers itself against named compiler
lifecycle hooks using `tap`, `tapAsync`, or `tapPromise`, depending on whether
the hook is synchronous, callback-based, or promise-based
(webpack.js.org, Plugin API documentation, verified 2026-08-02). The bundler
ships with a large first-party plugin set and an even larger third-party
ecosystem, none of which Webpack's own compiler package depends on.

**The Java platform's `ServiceLoader` mechanism, and everything built on it.**
`ServiceLoader` is the JDK's own answer to service-provider discovery, using
either `META-INF/services/<interface>` files on the classpath or `provides
... with ...` directives in a module descriptor (Oracle ServiceLoader docs,
verified 2026-08-02). JDBC driver discovery, `java.nio.file` filesystem
providers, and the JAX-P XML parser factory mechanism are all built on top of
this same facility, which is why a Java application can add a new JDBC driver
to its classpath and have it discovered automatically, with zero source
changes to the application that uses it.

## 10. Consequences

Positive.

- The host can be compiled, tested, and shipped without knowing every
  implementation that will eventually exist, which is the precondition for a
  genuine plugin ecosystem authored by parties the host's team never meets.
- Swapping an implementation, adding a new one, or removing one is a
  configuration or deployment change, not a source change to the host, which
  shortens the change cycle for exactly the code that needs to vary fastest
  (test doubles, per-customer adapters, per-environment gateways).
- The Separated Interface the pattern requires is a forcing function toward a
  cleaner boundary. A team that has to publish a stable interface for third
  parties tends to design that interface more carefully than one that only
  ever has a single internal caller.
- Independent build and release cycles for host and plugin become possible,
  which matters at the scale where a monolithic release train for every
  extension is no longer viable.

Negative.

- A discovery failure (a misspelled class name in a descriptor, a plugin JAR
  missing from the classpath, a version mismatch between the plugin's
  compiled interface and the host's current one) surfaces at runtime, often at
  start-up but sometimes only when the specific extension point is first
  reached, which is strictly later and strictly less informative than a
  compiler error at the same mistake.
- The Plugin Interface becomes an externally consumed contract the moment the
  first third-party plugin ships against it, and every subsequent change to
  that interface is now a breaking-change decision with a compatibility
  policy, not a free internal refactor.
- Debugging crosses a boundary the IDE's find-usages feature and the
  compiler's type checker cannot see through. Nothing in the host's source
  tree references `PluginA` by name, so tracing which code actually ran
  requires reading the descriptor or registry, not the call graph.
- An open plugin ecosystem inherits the security posture of its least
  trustworthy plugin unless the host pays for real isolation, and most
  in-process plugin systems (reflection-loaded classes, dynamically loaded
  native libraries, `require()`'d modules) do not provide that isolation by
  default.

## 11. Failure modes and misuse

**Symptom.** The application throws a class-not-found or no-implementation-found
error in production that never showed up in any test run. **Cause.** The
descriptor references a class that exists in the developer's local classpath
but was never added to the packaged deployment artifact, because nothing in
the build enforces that every descriptor entry corresponds to a class that
actually ships. **Fix.** Add a build-time or start-up-time validation step
that resolves every descriptor entry and fails the build, not just logs a
warning, if any entry cannot be loaded and instantiated.

**Symptom.** Adding a new extension point becomes a multi-day task involving
three teams. **Cause.** The interface has grown so large, and so many
unrelated concerns have been folded into one Plugin contract, that touching it
requires coordinating every existing implementer. This is Interface
Segregation violated at the plugin boundary, one fat `Plugin` interface should
have been several narrow ones, each with its own extension point. **Fix.**
Split the interface along the seams of what different plugin authors actually
implement, and let a plugin register against only the extension points it
cares about.

**Symptom.** Two plugins silently fight over the same piece of state, and the
outcome depends on load order. **Cause.** A hook chain (action or filter
style) lets every registered callback mutate shared, ambient state (a global
request context, a shared DOM, a shared in-memory cache) rather than
receiving and returning an explicit value. WordPress's filter shape avoids
this for data transforms specifically because the value is threaded explicitly
through the chain rather than mutated in place, systems that skip that
discipline and let actions reach into shared mutable state reproduce the
classic order-of-registration bug. **Fix.** Prefer filter-style explicit value
threading over action-style ambient mutation wherever the extension point is
meant to produce a result, and document and enforce a deterministic priority
order when mutation cannot be avoided.

**Symptom.** Start-up time grows linearly, then worse, with the number of
installed plugins, even though most of them are never actually used in a
given session. **Cause.** The registry eagerly instantiates every discovered
plugin at start-up instead of deferring instantiation until the extension
point is first reached. Eclipse's own architecture calls this out directly as
the reason its extension mechanism uses proxy objects and lazy instantiation
rather than eager loading (eclipse.org, Eclipse plugin architecture article,
verified 2026-08-02). **Fix.** Register a lightweight descriptor or proxy at
start-up, and defer the actual `Class.forName`, import, or instantiation
until the plugin's extension point is genuinely invoked.

**Symptom.** A plugin update breaks the host, or the host's update breaks
every installed plugin, with no compiler error anywhere in either codebase.
**Cause.** The Plugin Interface changed shape (a method signature changed, a
new required method was added, a semantic contract shifted) without a
versioning or compatibility story, and nothing enforced that the change was
backward compatible for existing binaries built against the old interface.
**Fix.** Treat the Plugin Interface as a published API from the day the first
external plugin ships against it. Version it explicitly, add methods only as
optional or default-implemented, and never remove or change the meaning of an
existing method without a major version bump and a migration path.

**Symptom.** An npm postinstall script, a WordPress plugin, or a browser
extension exfiltrates data or mines cryptocurrency after a routine update.
**Cause.** The plugin mechanism grants ambient, unscoped access to the host's
full runtime privileges (filesystem, network, DOM, environment variables)
with no capability model, so a plugin author's compromised account or a
malicious package can act with the same authority as the host application
itself. **Fix.** Scope what a plugin can do to an explicit, minimal
capability set the host grants per extension point, and where the plugin's
origin cannot be fully trusted, run it out-of-process or in a sandbox rather
than in-process with full host privileges.

## 12. Trade-off matrix

Judgement. The ratings below reflect typical production experience with each
alternative rather than a single sourced benchmark, because the comparison
depends heavily on team size, ecosystem openness, and language runtime.

| Force | Plugin (config or manifest binding) | Strategy (compile-time selection) | Dependency Injection container | Service Locator |
|---|---|---|---|---|
| Decoupling from concrete implementation | High, host never references the class by name | High for the call site, but the composition root still names every strategy | High, container wires the graph, application code depends only on interfaces | High for the consumer, but every lookup site depends on the locator itself |
| Discoverability of unknown-at-build-time extensions | Native fit, this is the pattern's reason to exist | Poor, every strategy must be known and referenced somewhere at compile time | Moderate, most containers still require explicit registration or a classpath scan configured in advance | Moderate, locator can scan a registry, but callers must know the lookup key |
| Compile-time safety | Low, a bad descriptor entry fails at runtime | High, the compiler verifies every reference | Moderate, wiring mistakes are usually caught at container start-up, not compile time | Low, a missing or mistyped key fails at runtime, often deep in a call stack |
| Independent deployment of host and extension | Native fit | Poor, requires recompiling the host to add a strategy | Possible with container-level plugin scanning, otherwise poor | Possible if the registry itself supports late registration |
| Debuggability, can you find usages from the host to the implementation | Low, the reference exists only in the descriptor, not in code | High, a normal call graph the IDE can trace | Moderate, modern IDEs can often trace DI wiring, but not always across modules | Low, the locator call site gives no static hint which implementation will answer |
| Cost to add a new extension point | Moderate, requires publishing a stable interface and a discovery mechanism | Low, add a new implementing class and a new call site | Moderate, requires registering a new binding | Low, but each new lookup key is another stringly typed contract |

## 13. Related and incompatible patterns

**Separated Interface.** Plugin depends on Separated Interface as a
precondition, not a peer. The Plugin Interface must live where neither the
Host nor any implementation's package needs to depend on the other's package,
which is exactly what Separated Interface describes (Fowler, EAA, 2002,
Separated Interface entry). Without Separated Interface, the guarantee that
the host depends only on the interface is not achievable, because the
interface would live inside one implementation's package and drag that
implementation's dependencies along with it.

**Factory Method and Abstract Factory.** A Plugin Registry is almost always
implemented as a Factory internally, it takes a descriptor entry and produces
an instance. The difference from a plain Factory Method is where the mapping
of which class to instantiate is decided. Factory Method decides it in code
(usually via subclassing or a parameter), Plugin decides it in external
configuration read at runtime. A codebase can, and often does, use Factory
Method inside the Registry to actually construct the resolved class once its
name is known.

**Service Locator.** Both patterns decouple a consumer from a concrete
implementation, but Service Locator centralizes lookup behind a single global
(or scoped) locator object that callers query by name or type at the point of
use, while Plugin resolves the binding once, typically at start-up, and hands
the Host a ready collection or singleton. Service Locator tends to hide
dependencies inside method bodies, Plugin tends to make the dependency
explicit in the Host's constructor or initialization sequence, even though the
concrete class is not named there.

**Dependency Injection.** A DI container is frequently the mechanism that
performs Plugin's discovery step in modern frameworks, container-based
component scanning that picks up every class annotated as an implementation of
a given interface is a Plugin Registry with a different discovery mechanism
(annotation and classpath scan instead of a manifest file). Where DI usually
assumes the full dependency graph is knowable and assembled once per process,
Plugin architectures more often support adding and removing extensions across
the lifetime of a running process, such as installing a browser extension
without restarting the browser.

**Observer.** The hook-chain variant of Plugin (WordPress actions, and any
event-bus-based extension mechanism) is structurally an Observer, the Host is
the subject, each registered plugin callback is an observer, and the hook
firing is the notification. The distinction is intent and packaging. Observer
usually describes in-process, same-deployment notification between objects
that were compiled together, while a Plugin hook chain specifically expects
observers authored, compiled, and deployed independently of the subject.

**Strategy.** Strategy and Plugin solve the same shape of problem
(interchangeable behavior behind one interface) at different points on the
compile-time-versus-runtime-versus-deployment-time scale. A Strategy is
chosen from a closed, compile-time-known set, usually by a parameter passed at
construction. A Plugin is chosen from an open, not-necessarily-known-at-build-time
set, resolved through external configuration. A codebase migrating from
Strategy to Plugin is usually reacting to the set of implementations having
grown from closed and small to open and externally contributed.

No pattern in this catalog is structurally incompatible with Plugin, the
pattern's whole purpose is to be a connective seam other patterns can sit on
either side of.

## 14. Refactoring path in and out

**Introducing Plugin into code that currently branches on environment or
vendor.** The trigger is a Factory, or worse a scattered set of conditionals,
that switches on an environment flag or a vendor identifier to decide which
concrete class to construct. First, extract the common behavior into an
interface, this is Extract Interface, feeding directly into Separated
Interface if the implementations do not already live in independent packages.
Second, move each branch's construction logic into its own class implementing
that interface, one class per branch, each in its own package if independent
deployability matters. Third, replace the conditional inside the Factory with
a single lookup against a small map or a configuration read, built once at
start-up from a descriptor file (properties, YAML, or a language-native
mechanism like `ServiceLoader`'s provider file). Fourth, delete the
conditional. If any test exercised the conditional branches directly,
redirect those tests to exercise the configuration-driven path instead,
verifying that each configuration value resolves to the expected
implementation.

**Introducing an open extension point (the wider plugin-architecture case).**
This is a larger, riskier refactor because it changes a promise, not just an
internal structure. The moment an extension point ships, third parties may
build against it. Before publishing anything, freeze the interface's shape
deliberately, favoring default-implemented or optional methods over required
ones so future additions do not break existing implementers. Ship a reference
implementation and, ideally, a compliance test suite third parties can run
against their own plugin to verify they satisfy the contract before they ship
it. Only after the interface is stable does it make sense to build the
discovery mechanism (manifest format, classpath scan, or hook-registration
API) that turns the interface into a genuine extension point.

**Removing a plugin mechanism that no longer earns its cost.** The signal that
Plugin should be retired is that the extension point now has exactly one
implementation, that implementation has not changed independently of the host
in a long time, and no third party has ever shipped a second one. Inline the
single remaining implementation directly into the Host, delete the interface,
delete the descriptor, and delete the registry. This is the reverse of the
introduction path, Inline Class followed by removing the now-pointless
indirection. Do this deliberately rather than by attrition, an unused
extension point left in place is a maintenance cost (a stable-contract
obligation and a discovery mechanism) with no offsetting benefit.

## 15. Testing and verification

Plugin makes one thing genuinely easier to test. The Host can be tested
against a trivial in-memory fake implementation of the Plugin Interface,
wired in through the exact same discovery mechanism production uses (a
test-scoped descriptor entry, a test-scoped `META-INF/services` file, or a
directly registered in-memory instance for the Tapable-style explicit-registration
variant), which means the test exercises the real discovery path rather than
bypassing it. This is a genuine advantage over hard-wired dependencies, the
interface boundary the pattern forces is exactly the seam a test double needs.

What becomes harder is verifying the discovery mechanism itself,
independently of any particular plugin's behavior. A test suite for a plugin
system needs its own dedicated coverage for the failure modes in dimension
11, a descriptor entry naming a class that does not exist, a class that
exists but does not implement the required interface, a class whose no-arg
constructor throws, and a descriptor listing the same implementation twice.
None of these are exercised by testing whether one real plugin works, and all
of them are exactly the failures that show up in production the first time an
operator edits the descriptor by hand.

Contract or compliance tests are the standard technique for verifying a
third-party or independently deployed plugin actually satisfies the Plugin
Interface's behavioral contract, not merely its type signature. A shared test
suite, parameterized over the plugin under test, asserts the semantic
guarantees the interface promises (idempotency, exception behavior on invalid
input, thread-safety expectations) so every implementer, including future ones
the Host's authors never meet, runs the same verification before shipping.

For the hook-chain variant, order-dependence is the specific thing to test.
Register two or more callbacks against the same hook in each possible order
and assert the final state or return value is the same, or, where order does
legitimately matter, assert the documented priority mechanism actually
produces the documented order.

## 16. Observability signals

A healthy plugin system logs, at start-up, exactly which plugins it
discovered, from which descriptor entry or source, and which extension point
each one registered against, at a level an operator can read without turning
on debug logging. This single log block is what makes tracing which code
actually ran answerable without reading the registry's source, which
dimension 10 names as one of the pattern's structural costs.

Each discovery failure (a missing class, a class that fails to implement the
interface, a constructor exception) should be logged as a distinct, named
error naming the offending descriptor entry, never swallowed into a generic
count of failed plugins with no names attached, which is useless to the
person who has to fix it.

Per-plugin invocation metrics (call count, latency, and error rate, tagged by
plugin identity) let an operator see which specific extension is slow,
failing, or being invoked far more or less often than expected, which matters
specifically because the Host's own instrumentation cannot see inside a
plugin's implementation the way it can see inside its own code.

Version and compatibility metadata (which version of the Plugin Interface a
given plugin was compiled against) should be surfaced, not just checked at
load time and discarded, because a host upgrade that silently stops calling
three plugins compiled against an older interface version has no other
visible symptom until a downstream feature quietly stops working.

## 17. Security and privacy implications

A plugin loaded in-process runs with the Host's full ambient privileges by
default, the same filesystem access, the same network access, the same
process memory, and, in a managed runtime, the same reflection capabilities
the Host itself has. Every in-process variant in dimension 8 (reflection-based
class loading, `ServiceLoader`, dynamically loaded native libraries,
explicitly registered JavaScript plugin objects) shares this property unless
the Host deliberately narrows it, and none of the sourced mechanisms in this
entry narrow it by default.

Judgement. The specific risk profile scales with how open the plugin
ecosystem is. A small, internally authored set of implementations chosen from
a configuration file (Fowler's narrow Plugin) carries roughly the same trust
level as any other internal code, because the team that writes the Host also
writes, reviews, and ships every implementation. A wide-open ecosystem where
anyone can publish a plugin (a browser extension store, a public npm registry
consumed by a plugin loader, a WordPress plugin repository) inherits the trust
level of its least-vetted publisher, and the Host's own security posture is
only as strong as its weakest installed extension, regardless of how carefully
the Host's own code is written.

Where the plugin's origin is not fully trusted, the mitigation is isolation,
not review alone, out-of-process execution with a narrow, capability-scoped
IPC surface, or a sandboxed runtime (a WebAssembly module with an explicit
host-function import table, or an OS-level sandbox), so a compromised or
malicious plugin's blast radius is bounded by what the Host explicitly
exposed to it rather than by the Host's own full privilege set.

A descriptor or manifest file that is itself writable by a lower-privilege
account than the one running the Host is a privilege-escalation path. An
attacker who can write to that file can point a legitimate extension point at
an attacker-controlled class or path, and the Host will load and run it with
the Host's own privileges. File permissions on the descriptor deserve the same
scrutiny as file permissions on the Host's own binary.

Data handling deserves explicit thought too. A plugin that receives the
Host's request or document context (the WordPress filter chain, an Eclipse
extension processing a workspace resource) has, by construction, access to
whatever data the Host passes through that hook, which may include personal
data, credentials in transit, or business-sensitive content. An extension
point contract should state explicitly what data crosses the boundary, so
plugin authors and auditors can reason about exposure without reading the
Host's full source.

## 18. References

1. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002, "Plugin" catalog entry,
   [martinfowler.com/eaaCatalog/plugin.html](https://martinfowler.com/eaaCatalog/plugin.html),
   verified 2026-08-02.
2. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002, "Separated Interface" catalog entry, referenced for
   the interface-location precondition the Plugin entry itself states,
   verified against the same catalog page 2026-08-02.
3. Eclipse Foundation, "The Architecture of Eclipse Plug-ins" (Eclipse Corner
   Article),
   [eclipse.org/articles/Article-Plug-in-architecture/plugin_architecture.html](https://www.eclipse.org/articles/Article-Plug-in-architecture/plugin_architecture.html),
   verified 2026-08-02.
4. WordPress Developer Resources, "Plugin Hooks, Actions and Filters,"
   [developer.wordpress.org/plugins/hooks/](https://developer.wordpress.org/plugins/hooks/),
   verified 2026-08-02.
5. Webpack documentation, "Plugin API,"
   [webpack.js.org/api/plugins/](https://webpack.js.org/api/plugins/), verified
   2026-08-02.
6. Oracle, Java SE 17 API documentation, `java.util.ServiceLoader`,
   [docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/ServiceLoader.html](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/ServiceLoader.html),
   verified 2026-08-02.

## Code examples

Three languages, each showing the configuration-time binding variant
(dimension 8) with a small, in-memory descriptor standing in for a real file
so the sample stays self-contained and runnable without external files.

### TypeScript

```typescript
interface StoragePlugin {
  readonly name: string;
  save(key: string, value: string): void;
  load(key: string): string | undefined;
}

class InMemoryStorage implements StoragePlugin {
  readonly name = "in-memory";
  private data = new Map<string, string>();
  save(key: string, value: string): void {
    this.data.set(key, value);
  }
  load(key: string): string | undefined {
    return this.data.get(key);
  }
}

class UppercaseEchoStorage implements StoragePlugin {
  readonly name = "uppercase-echo";
  save(_key: string, _value: string): void {}
  load(key: string): string | undefined {
    return key.toUpperCase();
  }
}

type PluginFactory = () => StoragePlugin;

// The descriptor, in a real deployment this map is built from a
// config file read at start-up, never hard-coded like this.
const descriptor: Record<string, PluginFactory> = {
  "in-memory": () => new InMemoryStorage(),
  "uppercase-echo": () => new UppercaseEchoStorage(),
};

class PluginRegistry {
  private cache = new Map<string, StoragePlugin>();
  constructor(private readonly desc: Record<string, PluginFactory>) {}

  resolve(name: string): StoragePlugin {
    const cached = this.cache.get(name);
    if (cached) return cached;
    const factory = this.desc[name];
    if (!factory) {
      throw new Error(`no plugin registered for "${name}"`);
    }
    const instance = factory();
    this.cache.set(name, instance);
    return instance;
  }
}

class Host {
  constructor(private readonly storage: StoragePlugin) {}
  handleWrite(key: string, value: string): void {
    this.storage.save(key, value);
  }
  handleRead(key: string): string | undefined {
    return this.storage.load(key);
  }
}

function boot(pluginName: string): Host {
  const registry = new PluginRegistry(descriptor);
  const plugin = registry.resolve(pluginName);
  return new Host(plugin);
}

const host = boot("in-memory");
host.handleWrite("a", "1");
if (host.handleRead("a") !== "1") {
  throw new Error("plugin did not round-trip a value");
}
```

### Python

```python
from abc import ABC, abstractmethod
from typing import Callable, Dict, Optional


class StoragePlugin(ABC):
    name: str

    @abstractmethod
    def save(self, key: str, value: str) -> None: ...

    @abstractmethod
    def load(self, key: str) -> Optional[str]: ...


class InMemoryStorage(StoragePlugin):
    name = "in-memory"

    def __init__(self) -> None:
        self._data: Dict[str, str] = {}

    def save(self, key: str, value: str) -> None:
        self._data[key] = value

    def load(self, key: str) -> Optional[str]:
        return self._data.get(key)


class UppercaseEchoStorage(StoragePlugin):
    name = "uppercase-echo"

    def save(self, key: str, value: str) -> None:
        return None

    def load(self, key: str) -> Optional[str]:
        return key.upper()


# The descriptor, in a real deployment this dict is built by reading
# entry_points metadata or a config file, never hard-coded like this.
DESCRIPTOR: Dict[str, Callable[[], StoragePlugin]] = {
    "in-memory": InMemoryStorage,
    "uppercase-echo": UppercaseEchoStorage,
}


class PluginRegistry:
    def __init__(self, descriptor: Dict[str, Callable[[], StoragePlugin]]) -> None:
        self._descriptor = descriptor
        self._cache: Dict[str, StoragePlugin] = {}

    def resolve(self, name: str) -> StoragePlugin:
        if name in self._cache:
            return self._cache[name]
        factory = self._descriptor.get(name)
        if factory is None:
            raise LookupError(f'no plugin registered for "{name}"')
        instance = factory()
        self._cache[name] = instance
        return instance


class Host:
    def __init__(self, storage: StoragePlugin) -> None:
        self._storage = storage

    def handle_write(self, key: str, value: str) -> None:
        self._storage.save(key, value)

    def handle_read(self, key: str) -> Optional[str]:
        return self._storage.load(key)


def boot(plugin_name: str) -> Host:
    registry = PluginRegistry(DESCRIPTOR)
    plugin = registry.resolve(plugin_name)
    return Host(plugin)


if __name__ == "__main__":
    host = boot("in-memory")
    host.handle_write("a", "1")
    assert host.handle_read("a") == "1", "plugin did not round-trip a value"
```

### Go

```go
package plugin

import "fmt"

// StoragePlugin is the Separated Interface the Host depends on.
// No implementation package is imported here.
type StoragePlugin interface {
	Name() string
	Save(key, value string) error
	Load(key string) (string, bool)
}

type inMemoryStorage struct {
	data map[string]string
}

func newInMemoryStorage() StoragePlugin {
	return &inMemoryStorage{data: make(map[string]string)}
}

func (s *inMemoryStorage) Name() string { return "in-memory" }

func (s *inMemoryStorage) Save(key, value string) error {
	s.data[key] = value
	return nil
}

func (s *inMemoryStorage) Load(key string) (string, bool) {
	v, ok := s.data[key]
	return v, ok
}

type uppercaseEchoStorage struct{}

func newUppercaseEchoStorage() StoragePlugin {
	return &uppercaseEchoStorage{}
}

func (s *uppercaseEchoStorage) Name() string { return "uppercase-echo" }

func (s *uppercaseEchoStorage) Save(_, _ string) error { return nil }

func (s *uppercaseEchoStorage) Load(key string) (string, bool) {
	upper := ""
	for _, r := range key {
		if r >= 'a' && r <= 'z' {
			r = r - 'a' + 'A'
		}
		upper += string(r)
	}
	return upper, true
}

type factory func() StoragePlugin

// descriptor stands in for a config file or a registered init() call
// read once at process start-up in a real deployment.
var descriptor = map[string]factory{
	"in-memory":      newInMemoryStorage,
	"uppercase-echo": newUppercaseEchoStorage,
}

type Registry struct {
	cache map[string]StoragePlugin
}

func NewRegistry() *Registry {
	return &Registry{cache: make(map[string]StoragePlugin)}
}

func (r *Registry) Resolve(name string) (StoragePlugin, error) {
	if p, ok := r.cache[name]; ok {
		return p, nil
	}
	f, ok := descriptor[name]
	if !ok {
		return nil, fmt.Errorf("no plugin registered for %q", name)
	}
	p := f()
	r.cache[name] = p
	return p, nil
}

type Host struct {
	storage StoragePlugin
}

func NewHost(storage StoragePlugin) *Host {
	return &Host{storage: storage}
}

func (h *Host) HandleWrite(key, value string) error {
	return h.storage.Save(key, value)
}

func (h *Host) HandleRead(key string) (string, bool) {
	return h.storage.Load(key)
}

func Boot(pluginName string) (*Host, error) {
	registry := NewRegistry()
	p, err := registry.Resolve(pluginName)
	if err != nil {
		return nil, err
	}
	return NewHost(p), nil
}
```

A fourth language was considered and skipped. Rust's idiomatic equivalent of
this pattern (a `dyn Trait` object resolved by name from a `HashMap<String,
fn() -> Box<dyn Trait>>`) is structurally identical to the Go sample above
with ownership annotations added, and would not show a genuinely different
technique, so it was left out rather than padded in.
