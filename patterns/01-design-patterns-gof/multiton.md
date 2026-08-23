---
name: Multiton
slug: multiton
family: 01-design-patterns-gof
category: Creational
aliases: [Registry of Singletons, Parameterized Singleton]
first_described: "O'Docherty 2005, generalizing a technique the 1994 GoF book itself describes without naming"
maturity: contested
related: [singleton, singleton-abuse, flyweight, dependency-injection]
incompatible_with: []
verified: 2026-08-23
---

## 1. Name, aliases, and lineage

Multiton is not a Gang of Four pattern, and Wikipedia's own article on it states this directly. "The multiton pattern does not explicitly appear as a pattern in the highly regarded object-oriented programming textbook Design Patterns." What the 1994 book does contain, and what Wikipedia cites as its closest precursor, is a discussion in a later printing (Addison-Wesley, 2011 reprint, ISBN 0-201-63361-2, page 130) of "using a registry of singletons to allow subclassing of singletons, which is essentially the multiton pattern," without the GoF authors ever using the word Multiton themselves. Registry of Singletons is therefore a genuinely sourced alternate name, traced to the GoF book's own later discussion rather than invented for this entry.

The earliest credible dated source treating the idea as its own named pattern is O'Docherty, Object-oriented analysis and design, understanding system development with UML 2.0, Wiley, 2005, page 341, cited by Wikipedia's own bibliography. A second, independently dated source worth recording is Paul Houle's 2008 article on gen5.info, which states plainly that "many people have independently discovered a new design pattern, the Multiton," and that the author himself had used the identical idea under a different name, Parameterized Singletons, in a project the previous year. So the pattern has no single, universally credited coiner, and this entry states that honestly rather than assigning one.

Neither Java's standard library nor any mainstream language's standard library documents the literal word Multiton. java.util.ResourceBundle, the JDK's own closest Multiton-shaped real example, describes its own caching behaviour in its own vocabulary, cache management and cached instances, without ever calling itself a Multiton.

## 2. Problem and context

Sometimes an application needs at most one instance of a class per distinct key value, never a single global instance and never unrestricted instantiation. Wikipedia's own framing states the distinction directly. "Whereas the singleton allows only one instance of a class to be created, the multiton pattern allows for the controlled creation of multiple instances, which it manages through the use of a map," guaranteeing "a single instance per key" rather than a single instance total, which "enables indexed storage of shared objects while maintaining centralized access to what functions as a unified directory."

The single best documented real instance of this problem in the JDK is java.util.ResourceBundle, keyed by base name and locale. Its own javadoc states the caching behaviour precisely. "Resource bundle instances created by the getBundle factory methods are cached by default, and the factory methods return the same resource bundle instance multiple times if it has been cached," with the three-argument overload's own documentation repeating the same guarantee. "getBundle caches instantiated resource bundles and might return the same resource bundle instance multiple times." The exact factory signature is `getBundle(String baseName, Locale locale)`.

A second, independently sourced motivating example comes from Paul Houle's 2008 article, whose worked example is `BlogPosting.GetInstance(int key)`, one in-memory object per database row key. The author's own words frame the shape's usefulness directly, that "the Multiton pattern can be used to maintain a set of objects are mapped to objects (rows) in a persistent store," where "it applies obviously to object-relational mapping systems, and is also useful in asynchronous RIA's, which need to keep track of user interface elements that are interested in information from the server."

## 3. Forces

The dominant force in the pattern's favour is controlled, guaranteed uniqueness per key with no extra ceremony at the call site, matching Wikipedia's own claim that the pattern "simplifies retrieval of shared objects in an application."

Pulling against it are Singleton's own well documented criticisms, inherited and multiplied across a registry. Wikipedia's own Drawbacks section states the first directly, citing Misko Hevery's dated 2008 Google Testing Blog post as its source. "This pattern, like the Singleton pattern, makes unit testing far more difficult, as it introduces global state into an application." Its second stated drawback is distinct to a garbage collected environment. "With garbage collected languages it may become a source of memory leaks as it introduces global strong references to the objects."

That memory concern is a real, sourced force Singleton simply does not share, since a Singleton holds exactly one reference forever while a Multiton's registry can grow without bound if the key space is unbounded. Paul Houle's own article states the mechanism and the scaling danger plainly. "Multitons, unfortunately, don't interact well with garbage collectors. Once a Multiton is created, the static _Instances array will maintain a reference to every Multiton in the system, so that Multitons won't be collected, even if no active references exist," and that "an application that works fine when it creates 50 Multitons could break down when it creates 50,000."

A further, structural force is that the registry cannot be selectively pruned by ordinary client code. Wikipedia's own account of the pattern's structure states that unlike a plain hash table, "clients cannot directly add mappings themselves," and that the registry "never returns a null or empty reference, instead, it creates and stores a multiton instance on the first request with the associated key," meaning every distinct key ever requested leaves a permanent entry unless the implementation deliberately builds in eviction.

## 4. Applicability and non-applicability

Reach for a Multiton when the key space is genuinely small, bounded, or well understood at compile time or close to it, one instance per day of the week, one per supported locale, one per named environment, and when exactly one instance per key is a real domain requirement rather than a convenience.

Do not reach for it when the key space is unbounded or driven by external input, for the exact reason named in dimension 3, unbounded memory growth. And weigh a modern dependency-injection container's own scoped-instance mechanism before hand-rolling a static registry. Spring's own reference documentation is explicit that even its baseline singleton scope is a narrower, container-managed idea than the GoF Singleton. "Spring's concept of a singleton bean differs from the singleton pattern as defined in the Gang of Four, GoF, patterns book. The GoF singleton hard-codes the scope of an object such that one and only one instance of a particular class is created per ClassLoader. The scope of the Spring singleton is best described as being per-container and per-bean." Spring additionally ships request, session, and application web scopes, each genuinely a per-identifier scoped instance, and a general custom-scope registration API, `registerScope(String scopeName, Scope scope)`, whose Scope interface exposes a `getConversationId()` keyed exactly the way a hand-rolled Multiton's key would be, with `SimpleThreadScope` shipping as a concrete, thread-keyed example. A container that already owns lifecycle and thread safety for a keyed instance is a strong, sourced alternative to writing that bookkeeping by hand.

## 5. Structure

**The Multiton class itself.** Holds a private static registry, a map from key to instance, and a private constructor so instances can only be created through the factory method. Wikipedia's own worked example names the class `Multiton` directly, with a registry field `instances` of type `Dictionary<MultitonType, Multiton>`.

**The Key type.** Whatever type indexes the registry, an enum in Wikipedia's own example, `MultitonType`, holding three member values.

**The static factory method.** `GetInstance(MultitonType type)` in Wikipedia's example, checking the registry for an existing entry under the given key and, if absent, constructing, registering, and returning a new one. Wikipedia's own account draws a precise structural line against an ordinary hash table here, stating the registry "differs from standard hash tables in two important ways. First, clients cannot directly add mappings themselves. Second, it never returns a null or empty reference, instead, it creates and stores a multiton instance on the first request with the associated key."

**Client code.** Calls the factory method rather than the constructor directly. A second, independently sourced worked example, Paul Houle's `BlogPosting` class, shows the same shape guarded by an explicit lock around the whole check-then-act sequence, confirming the structural pattern across two independent sources.

## 6. ASCII structure diagram

```
+---------------------------+
|         Multiton           |
|-----------------------------|
| - instances: Map<Key,      |
|              Multiton>      |
| - Multiton(key)  (private)  |
|-----------------------------|
| + GetInstance(key): Multiton|
+---------------^-------------+
                |
    on first request for a key
                |
       +--------+--------+
       |                 |
  registry miss     registry hit
       |                 |
  construct new    return the
  instance, add     existing
  to registry,      instance,
  return it         no construction

+-------------------------------------+
| java.util.ResourceBundle              |
| getBundle(String baseName, Locale)    |
|                                        |
| "return the same resource bundle      |
|  instance multiple times if it has    |
|  been cached" (Oracle's own javadoc)  |
+-------------------------------------+
```

## 7. Dynamics

On the first call to getInstance for a given key, the registry lookup misses, an instance is constructed, registered, and returned, exactly the never-null behaviour Wikipedia's own account describes. On a subsequent call with the same key, the registry hits and the stored instance is returned directly, with no construction. On a call with a different key, the registry misses for that specific key alone, and a separate, additional instance is constructed and coexists with every instance already registered, which is the core runtime behaviour distinguishing this pattern from Singleton.

A naive, unsynchronized registry check-then-act is a real, well documented race. Wikipedia's own article on double checked locking, the general lazy-initialization hazard this pattern shares, states it plainly. "A lock must be obtained in case two threads call bar simultaneously. Otherwise, either they may both try to create the object at the same time, or one may wind up getting a reference to an incompletely initialized object." Applied to a keyed registry, two threads calling getInstance for the same key concurrently can both observe a miss and each independently construct and insert an instance under that key, corrupting or duplicating the entry.

The modern, correct fix in Java is `java.util.concurrent.ConcurrentHashMap.computeIfAbsent`, whose own current javadoc states its atomicity guarantee directly. "If the specified key is not already associated with a value, attempts to compute its value using the given mapping function and enters it into this map unless null. The entire method invocation is performed atomically. The supplied function is invoked exactly once per invocation of this method if the key is absent, else not at all." This collapses the check, construct, and register sequence into one atomic operation with respect to other threads, eliminating the race without requiring a lock across the whole registry.

## 8. Implementation variants

**A classic synchronized-method registry.** The naive shape closes the race from dimension 7 with a coarse lock over the whole registry. No Java-specific Multiton tutorial could be located showing this exact code, so this entry states that gap plainly and generalizes it honestly from GeeksforGeeks's own documented Singleton shape, `public static synchronized Singleton getInstance() { if (single_instance == null) single_instance = new Singleton(); return single_instance; }`, extended to a keyed map. Paul Houle's independently sourced `BlogPosting` example takes this same coarse-lock approach explicitly, wrapping its whole check, construct, and insert sequence in a single lock block.

**ConcurrentHashMap.computeIfAbsent, the modern, correct technique.** Already quoted in full in dimension 7. its atomic, invoked-at-most-once guarantee is the standard current answer to the classic implementation's race, at the cost of the javadoc's own stated caveat that "some attempted update operations on this map by other threads may be blocked while computation is in progress, so the computation should be short and simple," a narrower, per-key blocking window than a whole-registry lock.

**An enum-based variant for a fixed, compile-time-known key space.** Wikipedia's own article states this directly as a real Java implementation technique. "In Java, the multiton pattern can be implemented using an enumerated type, with the values of the type corresponding to the instances," extending the well known single-element-enum Singleton idiom to a multi-constant enum where each constant is its own instance, guaranteed thread-safe by the JVM's own enum initialization semantics rather than by any manual locking.

**A dependency-injection-container alternative.** Spring's own documentation on autowiring states a genuine, container-managed equivalent of a keyed registry directly. "Even typed Map instances can be autowired as long as the expected key type is String. The map values are all beans of the expected type, and the keys are the corresponding bean names," meaning a `Map<String, MovieCatalog>` field populated declaratively by the container functions as the registry a hand-rolled Multiton would otherwise maintain by hand, with lifecycle and thread safety owned by the container.

A dated, current caveat worth recording against the classic synchronized variant. Oracle's own JDK 21 virtual threads documentation states that "a virtual thread is pinned" while "the virtual thread runs code inside a synchronized block or method," and that although "pinning does not make an application incorrect, it might hinder its scalability," with the concrete guidance that "guarding short-lived operations, such as in-memory operations... with synchronized blocks or methods should have no adverse effect," but that a long-lived or frequent synchronized block on a high-throughput virtual-thread server is a genuine scalability risk. A synchronized registry lookup is short lived and low risk by this guidance, but the moment a Multiton's constructor does any blocking work inside the lock, computeIfAbsent's narrower blocking window becomes the meaningfully safer choice on a virtual-thread-based server.

## 9. Known production uses

java.util.ResourceBundle remains the clearest, current, standard-library-level production use of the pattern's shape, caching and returning the same instance per base name and locale key, confirmed directly from Oracle's own javadoc in dimension 2.

Spring Framework's own Map-of-named-beans autowiring, quoted in dimension 8, is a second, large-scale, actively maintained production use of the identical idea, container-managed rather than hand-rolled.

A real, dated, and directly on-topic Java framework CVE confirms the pattern's registry shape is genuinely deployed in production code today, and that getting the bounding wrong is a real, current, exploitable defect rather than a theoretical concern. CVE-2026-33012, published 2026-03-20 against the Micronaut Framework, CVSS 7.5, describes exactly this failure mode. "Versions 4.7.0 through 4.10.16 used an unbounded ConcurrentHashMap cache with no eviction policy in its DefaultHtmlErrorResponseBodyProvider. If the application throws an exception whose message may be influenced by an attacker, for example, including request query value parameters, it could be used by remote attackers to cause an unbounded heap growth and OutOfMemoryError, leading to DoS." This is the exact ConcurrentHashMap-backed keyed registry recommended in dimension 8, deployed with attacker-influenced keys and no bound, in a real, current, widely used JVM framework.

## 10. Consequences

Positive. Guaranteed, controlled uniqueness per key with a single, centralized lookup point, and, per Wikipedia's own words, a simplified way to retrieve shared objects across an application without every caller re-deriving how to build one.

Negative. Every one of Singleton's own well documented criticisms, global mutable state and hidden coupling between unrelated parts of a codebase that all reach the same registry, applies here too, and, per dimension 3's sourced quotes, is joined by a concern Singleton does not share, unbounded memory growth in a garbage collected runtime when the key space is large or attacker influenced. A naive implementation also carries the real concurrency race described in dimension 7, and the registry's own permanence, per Wikipedia's own account that "clients cannot directly add mappings themselves" and every key ever requested is retained, means nothing is evicted unless the implementation deliberately builds that in.

## 11. Failure modes and misuse

**Unbounded key space driving unbounded memory growth.** The pattern's own most serious, most concretely documented failure mode. CVE-2026-33012, quoted in full in dimension 9, is a real, dated, CVSS 7.5 instance of precisely this. an unbounded ConcurrentHashMap-backed registry keyed by attacker-influenceable input, with no eviction policy, leading to an OutOfMemoryError and denial of service. This is formally classified under CWE-770, Allocation of Resources Without Limits or Throttling, a documented child of CWE-400, whose own description states plainly. "The product does not properly control the allocation and maintenance of a limited resource." OWASP's own Denial of Service Cheat Sheet names the standard mitigation directly. "Prevent input based resource allocation," meaning a key derived from untrusted input must never be allowed to grow a Multiton's registry without a bound.

**A naive check-then-act race under concurrent access.** Described in full in dimension 7, two threads racing to create an instance for the same key in an unsynchronized registry, producing a duplicated or corrupted entry. The symptom an engineer actually observes is two logically distinct objects both believed to be "the" instance for one key, with client code silently operating on different instances depending on which one it happened to receive.

**Treating the static registry as invisible in tests.** Because the registry is static and persists across test methods within the same run unless explicitly reset, a test that populates a given key can leak state into a later, unrelated test that reuses that key. Baeldung's own treatment of the closely related Singleton case states the mechanism directly, that when a class is "used as global objects, it becomes difficult to choose the configuration for the test environment. Therefore, when we run the tests, the production database gets spoiled with the test data, which is hardly acceptable," a criticism that transfers to Multiton unchanged, and in fact compounds, since an entire map of keyed state must be isolated between tests rather than one field.

## 12. Trade-off matrix

| Force | Multiton | Plain Singleton | DI container, keyed or scoped bean |
|---|---|---|---|
| Instance count | One per distinct key | Exactly one, globally | One per key or scope, container-managed |
| Compile-time key space | Best suited to a small, bounded, or enum-backed key space | Not applicable, no key at all | Any key space the container's bean names or qualifiers can express |
| Testability | Hard, static registry persists across tests unless reset | Hard, same global-state criticism | Easier, the container's own instance can be swapped for a test double per test |
| Memory growth risk | Real, unbounded if the key space is unbounded, see CVE-2026-33012 | None, one instance forever | Bounded by the container's own bean definitions, not by external input |
| Thread safety of creation | Must be engineered explicitly, see dimension 7 | Must be engineered explicitly, the same well known problem at a smaller scale | Owned by the container |
| Best fit | A genuinely small, bounded, well understood key space needing enforced uniqueness | A true, single, application-wide resource | Most real-world cases where a DI container is already in use |

## 13. Related and incompatible patterns

**Singleton.** The direct generalization this pattern extends from. Wikipedia's own words state it precisely, "the multiton pattern generalizes the singleton pattern," restricting a class to one instance per key rather than one instance per application. This repository's own Singleton entry, in this same family, and its Singleton Abuse entry, in the anti-patterns family, cover the base pattern and its well documented misuse in depth, and every criticism named there about global state and testability applies to Multiton as its keyed generalization.

**Flyweight.** The closest structural sibling in the whole catalogue, since both patterns maintain a keyed registry of shared instances to avoid duplicate object creation. Flyweight's own documented mechanism, per refactoring.guru, is that "the factory looks over previously created flyweights and either returns an existing one that matches search criteria or creates a new one if nothing is found," and per sourcemaking.com, "the client restrains herself from creating Flyweights directly, and requests them from the Factory," language that describes the identical registry shape as Multiton's own GetInstance. Despite checking both of those sources directly for an explicit comparison, neither draws one. The distinction offered here, that Flyweight exists for memory optimization across a large number of fine-grained objects sharing common intrinsic state, while Multiton exists to enforce identity and uniqueness per key regardless of scale, is this entry's own reasoned framing rather than a sourced claim, and is stated as such.

**Object Pool.** No credible source was found comparing Multiton to Object Pool directly. The two are structurally different in an important way worth naming honestly even without a citation. Object Pool manages a set of interchangeable instances of one resource, checked out and returned by callers, while Multiton's instances are permanently keyed and distinct, never checked out or recycled. This is offered as engineering judgement, not a sourced relationship.

**Dependency injection.** Covered in depth in dimension 4 and dimension 8. a DI container's own scoped or keyed bean mechanism is the most credibly sourced modern alternative to hand-rolling a Multiton's registry, with Spring's own documentation providing the concrete evidence. Martin Fowler's own writing on dependency injection adds a genuinely useful, somewhat counterintuitive nuance to the testability comparison specifically, arguing that the testability gap people commonly attribute to a static registry is not inherent to the pattern itself but to whether the registry was designed to be substitutable in the first place, and that the fix, in his own words, is making the effort to keep a service locator easily substitutable, rather than assuming dependency injection wins on testability by default.

## 14. Refactoring path in and out

**Refactoring in, from a set of unrelated ad hoc factory functions each producing a distinct keyed object.** When a codebase has grown several independent lazy-initialization helpers, one per resource key, each with its own private static field and its own null-check-then-create logic, the first symptom noticed is usually duplicated locking or duplicated null-check code across those helpers. Consolidating them behind a single keyed registry, following the structure in dimension 5, replaces N separate half-correct implementations of the same lazy-singleton-per-key idea with one implementation whose correctness only needs to be verified once.

**Refactoring out, toward a DI container's scoped or keyed bean mechanism.** When a project already uses a dependency injection container, Spring's own documented `Map<String, T>` autowiring, quoted in full in dimension 8, or a custom `Scope` implementation registered via `registerScope`, both directly quoted in dimension 4, replace a hand-rolled registry with a mechanism the container itself owns, tests, and manages the lifecycle of. Martin Fowler's own framing of the underlying trade-off, quoted in dimension 13, that testability depends on whether a locator was designed to be substitutable rather than being inherently worse, is the honest lens for judging whether this refactor is actually necessary or whether the existing hand-rolled registry could simply be made substitutable in place, for instance by injecting the registry itself as a dependency rather than reaching it through a static field.

## 15. Testing and verification

Three concerns, following directly from the forces and failure modes named in dimensions 3 and 11.

**Verifying per-key uniqueness.** A test creates the same key twice, through two separate calls to the factory method, and asserts reference equality between the two returned instances, following the identical shape as the standard Singleton unit test, applied once per distinct key under test.

**Verifying concurrent creation safety.** A test that spawns multiple threads, all requesting the SAME key simultaneously, and asserts that every thread received the identical instance, is the only way to actually exercise the race condition named in dimension 7 rather than merely assume the locking or the atomic map operation is correct. `ConcurrentHashMap.computeIfAbsent`'s own documented atomicity guarantee, quoted in full in dimension 7, is exactly the property such a test verifies empirically rather than takes on faith.

**Test isolation from the static registry.** Because the registry is static, per dimension 11's own named failure mode, a test suite must either reset the registry between tests, through a package-visible clear method invoked in a setup or teardown hook, or the registry must itself be made a non-static, injectable dependency so a fresh instance can be constructed per test. Baeldung's own quoted criticism of Singleton's testability, cited in full in dimension 11, "when we run the tests, the production database gets spoiled with the test data," is precisely the failure a missing reset step would allow, scaled up to however many keys a test suite happens to populate.

## 16. Observability signals

**Registry size as a direct proxy for the unbounded-growth risk named in dimensions 3 and 11.** `ConcurrentHashMap` exposes two distinct methods worth distinguishing here, quoted directly from Oracle's own current javadoc. `size()`, "Returns the number of key-value mappings in this map... If the map contains more than Integer.MAX_VALUE elements, returns Integer.MAX_VALUE," and `mappingCount()`, whose own javadoc recommends it specifically "when the map can contain more than Integer.MAX_VALUE mappings" since it "returns the number of mappings" as a long rather than saturating at an int's maximum. A production system exposing a Multiton's registry size as a metric, sampled on a fixed interval, converts the abstract memory-growth force into a concrete, alertable number.

**Per-key creation counts as a way to detect the specific attack shape behind CVE-2026-33012.** Because that CVE, quoted in full in dimension 9, was caused specifically by an attacker able to influence the key, a metric tracking distinct-keys-created-per-time-window, rather than only total registry size, would have surfaced the anomaly earlier, since a legitimate application's own bounded key space should produce a roughly flat distinct-key count over time while an attack producing fresh keys on every request would show it climbing without bound.

**Cache and eviction statistics, when a bounded cache library replaces a raw map.** Caffeine, the modern successor library to Guava's own cache, ships a documented `recordStats()` feature exposing hit rate, eviction count, and load time directly as a `CacheStats` object, giving an operator a direct, sourced way to observe whether a bounded eviction policy, rather than an unbounded `ConcurrentHashMap`, is correctly keeping a Multiton-shaped registry's memory footprint under control. Adopting an eviction-capable cache in place of a raw unbounded map is also the most direct structural fix to the memory-growth failure mode itself, not merely a way to observe it.

## 17. Security and privacy implications

**Denial of service via unbounded key-driven memory growth.** Formally CWE-770, Allocation of Resources Without Limits or Throttling, and CWE-400, Uncontrolled Resource Consumption, both quoted directly in dimension 11, with CVE-2026-33012 as a real, dated instance. OWASP's own Denial of Service Cheat Sheet names the specific, general mitigation directly, "Prevent input based resource allocation," meaning any Multiton whose key can be influenced, even indirectly, by an external actor must bound the registry, whether through a maximum-size eviction policy, a rate limit on distinct-key creation, or an allowlist restricting the key space to a known-safe, finite set.

**No credible source ties Multiton itself to a data-privacy concern distinct from the memory-exhaustion angle above.** Because the pattern's registry holds application objects rather than personal data by design, and because neither Wikipedia's own article nor either research pass located any documented privacy-specific concern beyond the resource-exhaustion risk already covered, this dimension is limited to the denial of service angle rather than padded with an unsourced privacy claim.

## 18. References

1. Wikipedia, Multiton pattern, https://en.wikipedia.org/wiki/Multiton_pattern, verified 2026-08-23.
2. Wikipedia, Singleton pattern, https://en.wikipedia.org/wiki/Singleton_pattern, verified 2026-08-23.
3. Wikipedia, Double-checked locking, https://en.wikipedia.org/wiki/Double-checked_locking, verified 2026-08-23.
4. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, Design Patterns, Elements of Reusable Object-Oriented Software, Addison-Wesley, 2011 reprint, ISBN 0-201-63361-2, page 130.
5. Michael O'Docherty, Object-Oriented Analysis and Design, Understanding System Development with UML 2.0, Wiley, 2005, ISBN 978-0-470-09240-8, page 341.
6. Paul Houle, gen5.info, The Multiton Design Pattern, https://gen5.info/q/2008/07/25/the-multiton-design-pattern/, verified 2026-08-23.
7. Oracle, java.util.ResourceBundle javadoc, https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/ResourceBundle.html, verified 2026-08-23.
8. Oracle, java.util.concurrent.ConcurrentHashMap javadoc, https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html, verified 2026-08-23.
9. Spring Framework reference, IoC container, Bean scopes, https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html, verified 2026-08-23.
10. Spring Framework reference, IoC container, Custom scopes, https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html#beans-factory-scopes-custom, verified 2026-08-23.
11. Spring Framework reference, Autowiring collaborators, https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-autowire.html, verified 2026-08-23.
12. Misko Hevery, Google Testing Blog, Root Cause of Singletons, https://testing.googleblog.com/2008/08/root-cause-of-singletons.html, verified 2026-08-23.
13. Baeldung, Introduction to the Singleton Pattern in Java, https://www.baeldung.com/java-singleton, verified 2026-08-23.
14. Martin Fowler, Inversion of Control Containers and the Dependency Injection pattern, https://martinfowler.com/articles/injection.html, verified 2026-08-23.
15. refactoring.guru, Flyweight, https://refactoring.guru/design-patterns/flyweight, verified 2026-08-23.
16. sourcemaking.com, Flyweight design pattern, https://sourcemaking.com/design_patterns/flyweight, verified 2026-08-23.
17. Oracle, Java Platform, Standard Edition, Virtual Threads Guide, Pinned Virtual Threads, https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html, verified 2026-08-23.
18. OWASP Cheat Sheet Series, Denial of Service Cheat Sheet, https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html, verified 2026-08-23.
19. NVD, CVE-2026-33012, Micronaut Framework unbounded cache denial of service, https://nvd.nist.gov/vuln/detail/CVE-2026-33012, verified 2026-08-23.
20. MITRE, CWE-770, Allocation of Resources Without Limits or Throttling, https://cwe.mitre.org/data/definitions/770.html, verified 2026-08-23.
21. MITRE, CWE-400, Uncontrolled Resource Consumption, https://cwe.mitre.org/data/definitions/400.html, verified 2026-08-23.
22. Ben Manes, Caffeine, GitHub, statistics documentation, https://github.com/ben-manes/caffeine/wiki/API#statistics, verified 2026-08-23.
23. Baeldung, Guide to Caffeine, https://www.baeldung.com/java-caching-caffeine, verified 2026-08-23.

**Evidence grade.** mixed

**Most solid findings.** The GoF book's own 2011-reprint precursor discussion, O'Docherty's 2005 named-source attribution, Paul Houle's original gen5.info article, ResourceBundle's own javadoc caching language, ConcurrentHashMap's own documented atomicity and blocking-scope guarantees, Spring's own scoped-bean and Map-autowiring documentation, Misko Hevery's own dated blog post on Singleton's testing cost, the JDK 21 virtual-thread pinning caveat, and CVE-2026-33012 against Micronaut are each drawn directly from a primary or near-primary source and quoted verbatim.

**Unverified or unclear.** No source directly compares Multiton to Object Pool, and this entry states that gap plainly rather than inventing a relationship. The Multiton-to-Flyweight comparison in dimension 13 is this entry's own reasoned framing, not a sourced claim, despite both refactoring.guru and sourcemaking.com being checked directly for such a comparison and neither drawing one. No source was found showing a Java-specific classic synchronized-method Multiton tutorial; the implementation in dimension 8 generalizes from Singleton and Multiton examples in other languages rather than quoting a single canonical Java source. Caffeine's own statistics feature is documented and cited directly, but no source was found benchmarking its overhead specifically in a Multiton-shaped registry, and none is asserted.

## Code

```typescript
// A keyed logger registry. one Logger instance per distinct name, created
// lazily and reused, following the same shape as log4j's own well known
// Logger.getInstance(name) API.
class Logger {
  private static readonly registry = new Map<string, Logger>();

  private constructor(private readonly name: string) {}

  static getInstance(name: string): Logger {
    let instance = Logger.registry.get(name);
    if (!instance) {
      instance = new Logger(name);
      Logger.registry.set(name, instance);
    }
    return instance;
  }

  static registrySize(): number {
    return Logger.registry.size;
  }

  info(message: string): void {
    console.log(`[${this.name}] ${message}`);
  }
}

const orderLogger = Logger.getInstance("orders");
const sameOrderLogger = Logger.getInstance("orders");
const paymentLogger = Logger.getInstance("payments");

orderLogger.info("order placed");
paymentLogger.info("payment captured");

console.log(orderLogger === sameOrderLogger); // true, same key, same instance
console.log(orderLogger === paymentLogger); // false, distinct keys
console.log(Logger.registrySize()); // 2
```

```python
# The same keyed-logger registry, using a class-level dict as the shared
# registry and a threading.Lock to close the check-then-act race described
# in the Dynamics section. Python's own logging module ships an equivalent,
# undocumented-as-Multiton internal registry inside logging.Logger.manager.
import threading


class Logger:
    _registry: dict[str, "Logger"] = {}
    _lock = threading.Lock()

    def __init__(self, name: str) -> None:
        self.name = name

    @classmethod
    def get_instance(cls, name: str) -> "Logger":
        instance = cls._registry.get(name)
        if instance is None:
            with cls._lock:
                # Re-check inside the lock. another thread may have created
                # this key while the current thread was waiting to acquire it.
                instance = cls._registry.get(name)
                if instance is None:
                    instance = cls(name)
                    cls._registry[name] = instance
        return instance

    @classmethod
    def registry_size(cls) -> int:
        return len(cls._registry)

    def info(self, message: str) -> None:
        print(f"[{self.name}] {message}")


order_logger = Logger.get_instance("orders")
same_order_logger = Logger.get_instance("orders")
payment_logger = Logger.get_instance("payments")

order_logger.info("order placed")
payment_logger.info("payment captured")

assert order_logger is same_order_logger
assert order_logger is not payment_logger
assert Logger.registry_size() == 2
```

```go
package main

import (
	"fmt"
	"sync"
)

// The same keyed-logger registry in Go, using sync.Map, whose own documented
// LoadOrStore method provides the identical atomic-per-key creation
// guarantee as Java's ConcurrentHashMap.computeIfAbsent, cited in the
// Dynamics section.
type Logger struct {
	name string
}

func (l *Logger) Info(message string) {
	fmt.Println("[" + l.name + "] " + message)
}

var registry sync.Map // map[string]*Logger

func GetLogger(name string) *Logger {
	if existing, ok := registry.Load(name); ok {
		return existing.(*Logger)
	}
	actual, _ := registry.LoadOrStore(name, &Logger{name: name})
	return actual.(*Logger)
}

func registrySize() int {
	count := 0
	registry.Range(func(key, value interface{}) bool {
		count++
		return true
	})
	return count
}

func main() {
	orderLogger := GetLogger("orders")
	sameOrderLogger := GetLogger("orders")
	paymentLogger := GetLogger("payments")

	orderLogger.Info("order placed")
	paymentLogger.Info("payment captured")

	fmt.Println(orderLogger == sameOrderLogger)
	fmt.Println(orderLogger == paymentLogger)
	fmt.Println(registrySize())
}
```
