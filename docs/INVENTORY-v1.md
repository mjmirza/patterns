# Master Pattern Inventory

Coverage checklist for `mjmirza/patterns`. Every entry is a slot to be **originally authored**.
refactoring.guru is used ONLY to establish which slots exist (names and structure), never as source text.

Counts verified from the live sitemap (2026-08-02) where marked SITEMAP.

## Family 01. GoF Design Patterns (23)

SITEMAP: refactoring.guru covers 22. It omits **Interpreter**. We cover all 23.

### Creational (5)

abstract-factory, builder, factory-method, prototype, singleton

### Structural (7)

adapter, bridge, composite, decorator, facade, flyweight, proxy

### Behavioral (11)

chain-of-responsibility, command, interpreter, iterator, mediator, memento,
observer, state, strategy, template-method, visitor

## Family 02. Code Smells (23 SITEMAP plus extensions)

alternative-classes-with-different-interfaces, comments, data-class, data-clumps,
dead-code, divergent-change, duplicate-code, feature-envy, inappropriate-intimacy,
incomplete-library-class, large-class, lazy-class, long-method, long-parameter-list,
message-chains, middle-man, parallel-inheritance-hierarchies, primitive-obsession,
refused-bequest, shotgun-surgery, speculative-generality, switch-statements,
temporary-field

Extensions (Fowler 2nd ed and community): global-data, mutable-data, loops,
insider-trading, repeated-switches

## Family 03. Refactoring Techniques (66 SITEMAP plus Fowler 2nd ed additions)

Composing Methods, Moving Features Between Objects, Organizing Data,
Simplifying Conditional Expressions, Simplifying Method Calls,
Dealing with Generalization. Full 66-slug list in `refactoring-techniques.txt`.

## Family 04. Design Principles

SOLID (5), GRASP (9), DRY, KISS, YAGNI, Law of Demeter, Composition over Inheritance,
Tell Don't Ask, Separation of Concerns, Single Source of Truth,
Principle of Least Astonishment, Fail Fast, CUPID (5),
Package principles (REP, CCP, CRP, ADP, SDP, SAP),
CAP, PACELC, ACID, BASE, Conway's Law, Postel's Law

## Family 05. Architectural Patterns

Layered, Hexagonal (Ports and Adapters), Clean Architecture, Onion Architecture,
MVC, MVP, MVVM, MVI, VIPER, Microkernel/Plugin, Pipes and Filters, Event-Driven,
SOA, Microservices, Modular Monolith, Serverless, Space-Based, Broker, Blackboard,
Peer-to-Peer, Client-Server, Leader-Follower, Interpreter/VM,
Strangler Fig, Sidecar, Ambassador, Anti-Corruption Layer

## Family 06. Enterprise Application Architecture (PoEAA, Fowler)

Domain Logic: Transaction Script, Domain Model, Table Module, Service Layer
Data Source: Table Data Gateway, Row Data Gateway, Active Record, Data Mapper
OR Behavioral: Unit of Work, Identity Map, Lazy Load
OR Structural: Identity Field, Foreign Key Mapping, Association Table Mapping,
  Dependent Mapping, Embedded Value, Serialized LOB, Single Table Inheritance,
  Class Table Inheritance, Concrete Table Inheritance, Inheritance Mappers
OR Metadata: Metadata Mapping, Query Object, Repository
Web Presentation: Model View Controller, Page Controller, Front Controller,
  Template View, Transform View, Two Step View, Application Controller
Distribution: Remote Facade, Data Transfer Object
Offline Concurrency: Optimistic Offline Lock, Pessimistic Offline Lock,
  Coarse-Grained Lock, Implicit Lock
Session State: Client Session State, Server Session State, Database Session State
Base: Gateway, Mapper, Layer Supertype, Separated Interface, Registry,
  Value Object, Money, Special Case, Plugin, Service Stub, Record Set

## Family 07. Enterprise Integration Patterns (Hohpe and Woolf)

Channels: Message Channel, Point-to-Point, Publish-Subscribe, Datatype Channel,
  Invalid Message Channel, Dead Letter Channel, Guaranteed Delivery,
  Channel Adapter, Messaging Bridge, Message Bus
Construction: Message, Command Message, Document Message, Event Message,
  Request-Reply, Return Address, Correlation Identifier, Message Sequence,
  Message Expiration, Format Indicator
Routing: Content-Based Router, Message Filter, Dynamic Router, Recipient List,
  Splitter, Aggregator, Resequencer, Composed Message Processor, Scatter-Gather,
  Routing Slip, Process Manager, Message Broker
Transformation: Envelope Wrapper, Content Enricher, Content Filter, Claim Check,
  Normalizer, Canonical Data Model
Endpoints: Messaging Gateway, Messaging Mapper, Transactional Client,
  Polling Consumer, Event-Driven Consumer, Competing Consumers,
  Message Dispatcher, Selective Consumer, Durable Subscriber,
  Idempotent Receiver, Service Activator
Management: Control Bus, Detour, Wire Tap, Message History, Message Store,
  Smart Proxy, Test Message, Channel Purger

## Family 08. Cloud and Distributed Design Patterns

Ambassador, Anti-Corruption Layer, Asynchronous Request-Reply,
Backends for Frontends, Bulkhead, Cache-Aside, Choreography, Circuit Breaker,
Claim Check, Compensating Transaction, Competing Consumers,
Compute Resource Consolidation, CQRS, Deployment Stamps, Event Sourcing,
External Configuration Store, Federated Identity, Gatekeeper,
Gateway Aggregation, Gateway Offloading, Gateway Routing, Geode,
Health Endpoint Monitoring, Index Table, Leader Election, Materialized View,
Messaging Bridge, Pipes and Filters, Priority Queue, Publisher-Subscriber,
Queue-Based Load Leveling, Rate Limiting, Retry, Saga,
Scheduler Agent Supervisor, Sequential Convoy, Sharding, Sidecar,
Static Content Hosting, Strangler Fig, Throttling, Valet Key

## Family 09. Concurrency and Parallelism Patterns

Reactor, Proactor, Half-Sync/Half-Async, Leader/Followers, Active Object,
Monitor Object, Thread-Specific Storage, Scoped Locking, Strategized Locking,
Thread-Safe Interface, Double-Checked Locking, Producer-Consumer, Thread Pool,
Fork-Join, Barrier, Future/Promise, Actor Model, CSP, Read-Write Lock, Balking,
Guarded Suspension, Immutable Object, Copy-on-Write, Disruptor,
Work Stealing, Pipeline Parallelism, Map-Reduce, Parallel Scatter-Gather

## Family 10. Microservices Patterns (Richardson)

Decomposition: by Business Capability, by Subdomain, Self-contained Service,
  Service per Team, Strangler Application
Data: Database per Service, Shared Database, Saga, API Composition, CQRS,
  Domain Event, Event Sourcing, Aggregate, Transactional Outbox,
  Polling Publisher, Transaction Log Tailing
Communication: Remote Procedure Invocation, Messaging, Domain-specific protocol,
  Idempotent Consumer, Circuit Breaker, API Gateway, Backends for Frontends
Discovery: Client-side Discovery, Server-side Discovery, Service Registry,
  Self Registration, Third-party Registration
Deployment: Multiple Service Instances per Host, Service Instance per Host,
  per VM, per Container, Serverless Deployment, Service Deployment Platform,
  Sidecar, Service Mesh
Cross-cutting: Microservice Chassis, Externalized Configuration
Observability: Log Aggregation, Application Metrics, Audit Logging,
  Distributed Tracing, Exception Tracking, Health Check API,
  Log Deployments and Changes
Testing: Service Component Test, Consumer-Driven Contract Test,
  Consumer-Side Contract Test
Security: Access Token

## Family 11. Domain-Driven Design Patterns

Strategic: Ubiquitous Language, Bounded Context, Context Map, Core Domain,
  Generic Subdomain, Supporting Subdomain, Shared Kernel, Customer/Supplier,
  Conformist, Anticorruption Layer, Open Host Service, Published Language,
  Separate Ways, Big Ball of Mud
Tactical: Entity, Value Object, Aggregate, Aggregate Root, Domain Event,
  Repository, Factory, Domain Service, Application Service, Module,
  Specification, Layered Architecture, Event Sourcing, CQRS, Process Manager

## Family 12. Data and Storage Patterns

Medallion Architecture, Lambda Architecture, Kappa Architecture, Data Mesh,
Data Vault, Star Schema, Snowflake Schema, Slowly Changing Dimensions (types 1 to 6),
ETL, ELT, Change Data Capture, Outbox, Materialized View, Write-Ahead Log,
LSM Tree, B-Tree, Sharding, Consistent Hashing, Quorum,
Leader-Follower Replication, Multi-Leader Replication, Leaderless Replication,
CRDT, Vector Clock, Lamport Clock, Two-Phase Commit, Three-Phase Commit,
Paxos, Raft, Gossip Protocol, Bloom Filter, HyperLogLog, Merkle Tree,
Read Repair, Hinted Handoff, Anti-Entropy

## Family 13. Frontend and UI Patterns

Container/Presentational, Compound Components, Render Props,
Higher-Order Component, Hooks, Provider, Observer/Signals, Flux, Redux,
State Machine UI, Atomic Design, Islands Architecture, Micro Frontends,
Server Components, Progressive Enhancement, Optimistic UI, Skeleton/Suspense,
Virtual List, Infinite Scroll, PRPL, Resource Hints, Code Splitting,
Route-based Lazy Loading, Debounce and Throttle, Controlled/Uncontrolled Components

## Family 14. Testing Patterns (xUnit Test Patterns, Meszaros)

Test Doubles: Dummy, Stub, Spy, Mock, Fake
Structure: Four-Phase Test, Arrange-Act-Assert, Given-When-Then,
  Test Fixture (Fresh, Shared, Prebuilt),
  Testcase Class per Class/Feature/Fixture
Data: Object Mother, Test Data Builder, Derived Value, Generated Value,
  Dummy Object, Literal Value
Strategy: Humble Object, Golden Master, Characterization Test, Contract Test,
  Property-Based Test, Mutation Test, Approval Test, Snapshot Test,
  Testcontainers, Fault Injection

## Family 15. Security Patterns

Secure by Default, Least Privilege, Defense in Depth, Zero Trust,
Fail Securely, Complete Mediation, Separation of Duties,
Token-based Auth, OAuth 2.1 flows, OIDC, JWT, Session Management,
CSRF Token, Content Security Policy, Rate Limiting, Input Validation,
Output Encoding, Parameterized Query, Secrets Management, Envelope Encryption,
mTLS, Gatekeeper, Valet Key, Federated Identity, RBAC, ABAC, ReBAC,
Audit Log, Idempotency Key, Webhook Signature Verification

## Family 16. Functional Programming Patterns

Functor, Applicative, Monad, Monoid, Semigroup, Foldable, Traversable,
Lens, Prism, Optics, Currying, Partial Application, Function Composition,
Point-free Style, Immutability, Persistent Data Structures, Structural Sharing,
Trampolining, Tail Call Optimization, Memoization, Lazy Evaluation,
Continuation, Continuation-Passing Style, Free Monad, Tagless Final,
Railway-Oriented Programming, Result/Either, Option/Maybe,
Reader, Writer, State, Transducer, Algebraic Data Type, Pattern Matching

## Family 17. AI and Agentic Patterns (2023 to 2026)

Scope note: this family is why the repo is not another GoF mirror.
Sources come from the last30days sweep plus primary vendor engineering docs.

Reasoning: Chain-of-Thought, Self-Consistency, Tree-of-Thought,
  Graph-of-Thought, ReAct, Reflexion, Plan-and-Execute, Least-to-Most
Workflow: Prompt Chaining, Routing, Parallelization (sectioning and voting),
  Orchestrator-Worker, Evaluator-Optimizer, Autonomous Agent Loop
Retrieval: Naive RAG, Advanced RAG, Modular RAG, GraphRAG, Agentic RAG,
  Corrective RAG, Self-RAG, HyDE, Chunking Strategies, Hybrid Search,
  Reranking, Contextual Retrieval, Late Chunking
Memory: Short-term, Long-term, Episodic, Semantic, Procedural,
  Memory Compaction, Context Engineering, Sub-agent Context Isolation
Tools: Function Calling, Structured Output, Model Context Protocol,
  Tool Result Caching, Computer Use, Code Execution as Tool
Multi-agent: Supervisor, Hierarchical, Network/Swarm, Handoff, Debate,
  Agentic Blackboard, Society of Mind
Safety and Ops: Input Guardrails, Output Guardrails, LLM-as-Judge,
  Human-in-the-Loop, LLM Circuit Breaker, Fallback Chain, Cost Guard,
  Token Budget, Semantic Caching, Prompt Injection Defense, PII Redaction,
  Constitutional AI, Evaluation Suite, Golden Dataset, Tracing

## Family 18. Anti-Patterns

Architectural: Big Ball of Mud, Distributed Monolith, Nanoservices,
  Entity Service, Anemic Domain Model, Golden Hammer, Vendor Lock-in,
  Inner-Platform Effect, Stovepipe System
Code: God Object, Spaghetti Code, Lava Flow, Boat Anchor, Poltergeist,
  Magic Numbers, Copy-Paste Programming, Yo-yo Problem, Circular Dependency,
  Singleton Abuse, Service Locator, Sequential Coupling, Call Super
Performance: N+1 Query, Chatty I/O, Busy Database, Busy Front End,
  Extraneous Fetching, Improper Instantiation, Monolithic Persistence,
  No Caching, Retry Storm, Synchronous I/O, Premature Optimization
Process: Cargo Cult Programming, Analysis Paralysis, Death March,
  Bikeshedding, Not Invented Here, Reinventing the Wheel

## Volume Estimate

| Family | Entries |
|---|---|
| 01 GoF | 23 |
| 02 Smells | 28 |
| 03 Refactorings | 66 |
| 04 Principles | 35 |
| 05 Architectural | 27 |
| 06 PoEAA | 51 |
| 07 EIP | 65 |
| 08 Cloud | 42 |
| 09 Concurrency | 28 |
| 10 Microservices | 44 |
| 11 DDD | 29 |
| 12 Data | 37 |
| 13 Frontend | 25 |
| 14 Testing | 30 |
| 15 Security | 30 |
| 16 Functional | 34 |
| 17 AI and Agentic | 55 |
| 18 Anti-Patterns | 34 |
| TOTAL | ~683 |
