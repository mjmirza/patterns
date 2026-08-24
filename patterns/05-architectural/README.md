# Family 05. Architectural Patterns

Origin. Buschmann POSA 1, Bass SEI

31 entries, 248,931 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Architectural

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Blackboard Architecture](blackboard-architecture.md) | established | 7,034 | A recognizable class of problems has no known algorithm that transforms input directly into output. |
| [Broker](broker-architecture.md) | canonical | 8,041 | A distributed system is made of components running in separate processes, often on separate machines, that need to call on each other's services. |
| [Cell-Based Architecture](cell-based-architecture.md) | established | 8,424 | A service that runs as one shared, horizontally-scaled deployment behind one load balancer has a property that is invisible on a calm day and catastrophic on a bad one. |
| [Clean Architecture](clean-architecture.md) | canonical | 7,521 | A non-trivial application accumulates business rules that answer questions no framework, database, or user interface technology can answer for it. |
| [Client-Server](client-server.md) | canonical | 8,189 | An application needs to let more than one user, device, or process operate on data or capability that must be shared, kept consistent, and protected from direct, uncoordinated ... |
| [Event-Carried State Transfer](event-carried-state-transfer.md) | established | 7,462 | A system grows a second consumer that needs data owned by a first system. |
| [Event-Driven Architecture](event-driven-architecture.md) | canonical | 9,420 | A system built from several independently deployable components needs to react to things that happen elsewhere in the system, without each component knowing the internal state ... |
| [Hexagonal Architecture](hexagonal-architecture.md) | canonical | 10,373 | A codebase reaches a specific, recognizable moment. |
| [Interpreter Architecture](interpreter-architecture.md) | canonical | 8,034 | A system needs to accept a piece of behaviour, a rule, a query, a formula, a policy, that was not known when the system was compiled, and that behaviour must be safe to run inside ... |
| [Layered Architecture](layered-architecture.md) | canonical | 7,640 | A non-trivial application has at least three concerns that change for different reasons and at different rates. |
| [Leader-Follower Architecture](leader-follower-architecture.md) | canonical | 10,195 | A distributed system frequently needs some class of decision made exactly once and in a single agreed order, even though the work of making that decision is spread across several ... |
| [Microkernel](microkernel.md) | canonical | 8,103 | A team is building a system whose core purpose is settled and small, but whose surrounding behavior is not. |
| [Microservices Architecture](microservices-architecture.md) | established | 7,028 | A single deployable application, however well factored internally, eventually runs into three problems that module boundaries inside one process cannot solve. |
| [Model View ViewModel](model-view-viewmodel.md) | canonical | 6,834 | A user interface has three kinds of code tangled together whenever it is built without a discipline. |
| [Model-View-Controller](model-view-controller.md) | canonical | 6,733 | The problem MVC solves is separation of concerns in a system where a person is directly manipulating a live data structure through a graphical interface, and the interface must ... |
| [Model-View-Intent](model-view-intent.md) | established | 7,956 | A View that mutates its own local, mutable fields in response to individual events accumulates state that nobody can reconstruct from a single snapshot. |
| [Model-View-Presenter](model-view-presenter.md) | established | 7,710 | A screen, form, or activity has to do three jobs at once. |
| [Modular Monolith](modular-monolith.md) | established | 7,918 | A team is building a system that will run as one process, or one small cluster of identical processes behind a load balancer, and deploys as one unit. |
| [Multi-Tenant Architecture](multi-tenant-architecture.md) | canonical | 5,015 | A SaaS provider serves many customers, called tenants, from one running application. |
| [Onion Architecture](onion-architecture.md) | canonical | 8,637 | A team builds a business application against a specific database, a specific web framework, and a specific set of third party integrations, because those are the concrete ... |
| [Peer-to-Peer](peer-to-peer.md) | canonical | 8,950 | A system needs many participants to exchange data or share work, and at least one of the following forces makes a single, dedicated server the wrong place to put that coordination. |
| [Pipeline Architecture](pipeline-architecture.md) | canonical | 8,741 | A system needs to transform a stream of data through a sequence of independent processing steps, and the set of steps, their order, or their implementation is expected to change ... |
| [Pipes and Filters](pipes-filters.md) | canonical | 7,870 | A system must transform a stream of data through several independent processing steps, and the set of steps, their order, or the data source itself is expected to change over the ... |
| [Plugin Architecture](plugin-architecture.md) | canonical | 7,823 | An application needs to support a set of behaviours that is open-ended, unknown at the time the core is built, and likely to be supplied by parties who are not the core's own ... |
| [Plugin Sandbox](plugin-sandbox.md) | established | 10,826 | A host application defines an extension point, using Plugin Architecture or Microkernel, so that its behavior can grow without every new feature being merged into the core ... |
| [Primary-Replica](primary-replica.md) | canonical | 7,665 | A single database instance handling both writes and reads eventually hits a ceiling on at least one of three axes, read throughput, availability, and geographic latency. |
| [Serverless Architecture](serverless-architecture.md) | established | 8,872 | A team owns a backend that must handle a workload with two properties that are hard to satisfy at once with a conventional server fleet, the load is spiky or unpredictable, and ... |
| [Service-Oriented Architecture](service-oriented-architecture.md) | contested | 6,727 | A monolithic application starts as the fastest way to ship. |
| [Shared Nothing](shared-nothing.md) | canonical | 7,785 | A system needs to handle more work than one machine can handle, whether that work is transaction throughput, storage volume, or concurrent connections. |
| [Space-Based Architecture](space-based-architecture.md) | established | 7,002 | A system built as a stateless application tier in front of a single relational database scales the application tier easily and the database tier badly. |
| [VIPER](viper.md) | established | 8,403 | A screen in a UIKit or AppKit application tends to accumulate three kinds of code inside one view controller, code that lays out and updates the user interface, code that decides ... |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
