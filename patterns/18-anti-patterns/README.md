# Family 18. Anti-Patterns

Origin. Brown et al, AntiPatterns

41 entries, 335,063 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Anti-Pattern

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Analysis Paralysis](analysis-paralysis.md) | canonical | 7,215 | A team is asked to build a feature, choose an architecture, or pick a technology. |
| [Bikeshedding](bikeshedding.md) | canonical | 7,563 | A decision needs to be made by a group, and the group contains people with very different depths of expertise on the subject. |
| [Busy Database](busy-database.md) | canonical | 8,380 | The context is any system with a client tier, an application or service tier, and a database tier, where the database engine exposes a facility for running code close to the data ... |
| [Busy Front End](busy-front-end.md) | canonical | 8,025 | The context is a server-side application built as, or converged into over time, a single deployable process that does two structurally different jobs at once, accepting and ... |
| [Cache Stampede](cache-stampede.md) | canonical | 8,736 | The shape that produces this anti-pattern is almost always the same three ingredients arriving together. |
| [Call Super](call-super.md) | canonical | 8,627 | A base class method does two things at once. |
| [Cargo Cult Programming](cargo-cult-programming.md) | canonical | 8,232 | A developer under time pressure needs code that solves a problem they do not fully understand, in a domain they have not fully learned, often on a deadline that leaves no room to ... |
| [Copy-Paste Programming](copy-paste-programming.md) | canonical | 7,082 | A developer needs behavior that is almost, but not quite, identical to behavior that already exists somewhere else in the codebase. |
| [God Object](god-object.md) | canonical | 8,493 | A system starts with a reasonable class boundary. |
| [Golden Hammer](golden-hammer.md) | canonical | 7,387 | A developer or a team becomes highly proficient with one tool, a database, a framework, a data structure, a language feature, a deployment platform, or a design pattern. |
| [Inner-Platform Effect](inner-platform-effect.md) | canonical | 9,693 | The situation always starts with a genuine and reasonable business requirement, that end users, who are not programmers, need to change how the system behaves without waiting on a ... |
| [Magic Numbers](magic-numbers.md) | canonical | 6,525 | A magic number is a numeric literal that appears directly in executable code, in a comparison, an arithmetic expression, an array size, a loop bound, or a function argument ... |
| [Monolithic Persistence](monolithic-persistence.md) | canonical | 6,491 | A system starts with one team, one codebase, and one database, and the fit is genuinely good. |
| [N+1 Query](n+1-query.md) | canonical | 8,916 | The shape appears the moment code needs to display, process, or serialize a list of parent records together with one piece of data that lives on a related table or a related ... |
| [No Caching](no-caching.md) | established | 6,450 | A system computes or fetches a value that is expensive relative to how often it is actually needed fresh, and it does that computation or fetch again, in full, on every single ... |
| [Not Invented Here](not-invented-here.md) | canonical | 7,177 | A team needs a capability another party has already built. |
| [Poltergeist](poltergeist.md) | canonical | 8,669 | A codebase accumulates classes whose entire behaviour is to be constructed, make one or two calls into a different, more permanent class, and then be discarded. |
| [Premature Optimization](premature-optimization.md) | canonical | 8,762 | The situation that produces this anti-pattern looks the same across languages, teams, and decades, because it comes from a mismatch between how programmers reason about code and ... |
| [Retry Storm](retry-storm.md) | canonical | 8,440 | A service calls a downstream dependency over the network. |
| [Sequential Coupling](sequential-coupling.md) | canonical | 8,982 | An object accumulates behavior across its public surface the way most long-lived classes do, one method added at a time as new requirements arrive. |
| [Singleton Abuse](singleton-abuse.md) | canonical | 8,029 | A codebase reaches for Singleton Abuse in a specific, recognizable moment. |
| [Spaghetti Code](spaghetti-code.md) | canonical | 9,313 | A program begins as a short, linear sequence of statements that a single author can hold entirely in their head. |
| [Synchronous I/O](synchronous-i-o.md) | established | 9,421 | Picture a request-handling process that serves many clients from a bounded number of execution contexts, whether that bound is a fixed thread pool, a single event loop thread, or ... |
| [Thundering Herd](thundering-herd.md) | canonical | 7,680 | Picture a cached product page. Ten thousand requests a second hit a CDN edge or an application cache for the same product. |
| [Yo-yo Problem](yo-yo-problem.md) | canonical | 9,233 | The situation announces itself the same way every time. |

## Anti-pattern

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Anemic Domain Model](anemic-domain-model.md) | canonical | 8,622 | A codebase reaches for persistence early. |
| [Big Ball of Mud](big-ball-of-mud.md) | canonical | 9,287 | A reader can recognize this problem without ever hearing the pattern's name. |
| [Boat Anchor](boat-anchor.md) | established | 7,077 | A team adds a piece of code, an API, a dependency, a database table, a configuration flag, or a whole service for a reason that was real at the time. |
| [Circular Dependency](circular-dependency.md) | canonical | 9,330 | A codebase grows by adding files, packages, or services, and each new unit imports whatever it needs from its neighbours. |
| [Entity Service](entity-service.md) | contested | 8,323 | A team decomposes a monolith, or designs a new distributed system from scratch, and reaches for the most obvious axis of decomposition available. |
| [Extraneous Fetching](extraneous-fetching.md) | established | 8,228 | A piece of code needs three fields from a record, a page needs the title and the thumbnail of a hundred articles, a mobile screen needs a user's display name and avatar. |
| [Improper Instantiation](improper-instantiation.md) | established | 9,564 | A type in the codebase is expensive, or moderately expensive, or genuinely expensive, to construct. |
| [Service Locator](service-locator.md) | contested | 6,102 | A component needs a collaborator to do its work, a repository, a logger, a payment gateway client, a feature-flag reader, and it does not want to be handed a concrete instance by ... |
| [Vendor Lock-in](vendor-lock-in.md) | established | 8,019 | A team building a system needs to store data, run compute, send messages, authenticate users, and observe the running system. |

## Anti-pattern (Messaging and Concurrency)

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Poison Pill](poison-pill.md) | established | 8,267 | Every worker-pool or message-consumer system faces two separate but related questions that get answered by the same mechanism if the designer is not careful. |

## Architectural

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Chatty I/O](chatty-i-o.md) | established | 8,323 | Chatty I/O appears the moment a piece of code that used to run against in-process memory starts running against something on the far side of a boundary that has real per-call cost. |
| [Distributed Monolith](distributed-monolith.md) | established | 8,553 | A team decomposes a monolith, or designs a new system, into a set of services with separate repositories, separate deployment pipelines, and separate runtime processes, expecting ... |
| [Stovepipe System](stovepipe-system.md) | canonical | 8,168 | An organization builds its second system, its second department's application, or its second bounded capability, and the fastest path to delivery is to start from a blank slate ... |

## Architectural (Distributed Systems)

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Nanoservices](nanoservices.md) | contested | 7,761 | A team adopts microservices with the correct instinct that a monolith with too many concerns bundled into one deployable is hard to change safely, and the guidance they read tells ... |

## Distributed Systems Anti-Pattern

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Split Brain](split-brain.md) | canonical | 8,750 | A system replicates state, or elects a leader, across more than one node so that it survives the failure of any single node. |

## Software Development Anti-pattern

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Lava Flow](lava-flow.md) | canonical | 7,168 | A codebase under real deadline pressure accretes exploratory code, spike solutions, feature-flagged experiments, half-finished rewrites, region-specific branches for a market the ... |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
