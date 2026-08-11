---
name: Transaction Script
slug: transaction-script
family: 06-enterprise-application-architecture
category: Domain Logic
aliases: [Script, Procedural Domain Logic]
first_described: "Fowler 2002"
maturity: canonical
related: [table-module, active-record, service-layer, gateway, template-method]
incompatible_with: [domain-model]
verified: 2026-08-02
---

# Transaction Script

## 1. Name, aliases, and lineage

The canonical name is Transaction Script. Martin Fowler names and describes it
in *Patterns of Enterprise Application Architecture*, Addison-Wesley, 2002,
chapter 9, "Domain Logic Patterns," in the section titled "Transaction Script"
(Martin Fowler, *Patterns of Enterprise Application Architecture*, verified
against the Transaction Script catalog page at
https://martinfowler.com/eaaCatalog/transactionScript.html, verified
2026-08-02). Fowler's own catalog page states the pattern's intent in one
sentence, that it "organizes business logic by procedures where each
procedure handles a single request from the presentation." The word
"transaction" in the name does not mean a database transaction in the
ACID sense, although a Transaction Script commonly wraps one. It means a
business transaction, a single interaction a user or another system has with
the application, such as placing an order, transferring money between two
accounts, or checking a passenger into a flight. Fowler's own text is explicit
that the name borrows the word from that everyday business sense rather than
from the database sense, and warns readers to keep the two meanings apart.

The pattern rarely appears under another name in professional conversation,
but the two aliases used above are worth naming because they surface in
adjacent literature. "Script" alone appears as shorthand once a codebase has
already established Transaction Script as its house style, the way a team
might say "add a script for refunds" rather than spelling out the full
pattern name every time. "Procedural Domain Logic" appears in comparative
treatments that group Transaction Script, Table Module, and Domain Model
together as the three ways Fowler catalogs to organize business rules, since
Transaction Script is the one member of that trio that keeps the logic in
ordinary procedures rather than attaching it to objects that model the domain
(Fowler, *Patterns of Enterprise Application Architecture*, chapter 9
introduction, same verified page above, which frames all three under the
shared heading "Organizing Domain Logic").

Transaction Script predates its formal name by decades in practice. The shape
it describes, one procedure per business operation, calling the database
directly or through a thin wrapper, is how transaction processing monitors
such as IBM CICS structured COBOL application programs on mainframes from the
1970s onward, where each CICS transaction was conventionally implemented as
one program invoked by a four-character transaction code (IBM, "CICS
transaction processing environment," IBM CICS Transaction Server for z/OS
documentation, https://www.ibm.com/docs/en/cics-ts/6.x, verified 2026-08-02,
and IBM, "How COBOL Programs Connect to CICS, IMS, and DB2," DBzTech
Technology Dossier, https://dbztech.blog/cics-ims-and-db2-connecting-cobol-programs-in-z-os/,
verified 2026-08-02, describing embedded EXEC SQL statements inside COBOL
programs that read, update, or insert rows directly). Fowler's contribution in
2002 was not inventing this shape, it was giving it a name, a place in a
catalog next to its two competitors, and an honest account of when it is the
right choice and when it collapses under its own weight.

## 2. Problem and context

A team is building a business application, an order system, a billing
system, a claims processor, anything where the software's job is to carry
out operations that a business analyst would recognize and name, place an
order, transfer funds, calculate a bonus, recognize revenue on a contract.
Each of those operations reads a request, applies some rules, touches a
database, and returns a result. The question the team faces before writing a
line of code is where the logic for "transfer funds" should live.

The context in which Transaction Script becomes the obvious answer has a
specific shape. The team is working against deadline pressure that makes an
elaborate object model expensive to justify up front. The business rules,
while real, are not deeply entangled with each other, meaning that "transfer
funds" and "close the month" do not need to share much beyond a database
connection and some common validation. The data underneath maps closely to
the database schema, so there is little payoff in building a rich network of
objects that mirror business concepts, because the concepts do not have much
independent behavior beyond what a straight-line procedure already expresses.
And, often decisively, most of the people writing and maintaining the code
think procedurally by training or preference, so a design that keeps a
one-to-one mapping between "the business operation named X" and "the
function named X" is easier for the team to hold in their heads.

Fowler frames this problem with a running example he returns to across three
chapters of the same book, revenue recognition, the accounting question of
when a company is allowed to count money it has been paid as revenue on its
books rather than as a liability (Martin Fowler, *Patterns of Enterprise
Application Architecture*, Addison-Wesley, 2002, chapter 9, "The Revenue
Recognition Problem," page 112, cited via the excerpted case description at
https://lorenzo-dee.blogspot.com/2015/08/domain-logic-patterns.html which
quotes the page number directly from Fowler's text, verified 2026-08-02). A
software contract might specify three products delivered over time, each
recognized on a different schedule, word processing software recognized in
full on delivery, a database product recognized a third at a time over three
milestones, a spreadsheet product recognized on a delayed one-third, one-third,
one-third schedule after a waiting period. The two operations a system needs
are "calculate the recognitions for a contract" and "tell me the total
recognized revenue as of a date." Both are naturally expressed as a straight
procedure, fetch the contract, loop over its line items, apply the product's
recognition rule, write the resulting recognition rows, done. Nothing about
that procedure needs an object model of "recognition strategies" polymorphic
over product types, at least not until the number of distinct recognition
schedules and their interactions grows past what a team can hold in a
readable function.

The deeper context is a genuine, honest trade-off that the whole pattern
family in chapter 9 exists to resolve. domain logic has to live somewhere,
and every place it can live carries a cost. Transaction Script's answer is to
put it in procedures shaped exactly like the business operations a person
would name, and to accept the cost that shape brings as line count and
business rule complexity grow.

## 3. Forces

Complexity versus ceremony is the central tension. A rich Domain Model
distributes behavior across many small, focused objects, each responsible
for one concept, which pays off once the same behavior is reused across many
operations and once the rules interact in ways that a straight procedure
would tangle into nested conditionals. Building that model has a fixed cost,
in design time, in learning curve for new team members, and in the extra
indirection a reader must trace to find where a rule actually executes.
Transaction Script sacrifices reuse and rule composability to avoid paying
that fixed cost. It favors low ceremony over long-term flexibility.

Team topology and cognitive load pull the same direction as complexity. A
team where developers primarily think in terms of "what happens when this
request comes in" rather than "what is the responsibility of this class"
will produce cleaner Transaction Scripts than Domain Model code, because the
procedure matches how they already reason about the problem. Fowler is
explicit in the book that this is not a purely technical judgment, staffing
and the team's existing habits legitimately shape which pattern produces
better code in practice, not only which pattern is more elegant on paper.

Duplication versus coupling is the second major force. Two Transaction
Scripts that both need to validate an account balance will, left unchecked,
each carry their own copy of that validation, because each script is
self-contained by design. The alternative, extracting a shared subroutine,
reduces duplication but creates a coupling point between scripts that
previously had none, and if that shared subroutine grows enough logic it
starts to look like the beginning of a Domain Model in disguise. Fowler's own
guidance is that a team should freely extract common subprocedures for
housekeeping such as data access, but should watch for the point where those
subprocedures start encoding independent business rules rather than pure
mechanics, because that is the signal the team is drifting toward a
different pattern without having decided to.

Consistency and operability matter because a Transaction Script commonly
wraps a single database transaction around itself, so the operation either
fully commits or fully rolls back. That gives an operability property that
is easy to reason about, a single procedure is a single unit of work, easy
to time, easy to log, easy to retry. The cost is that a Transaction Script
which needs to coordinate two operations, say "transfer funds and then
notify a downstream ledger," has no natural place to put the coordination
except inside the script itself or a caller above it, whereas a Domain Model
with proper aggregate boundaries has a clearer answer for where cross-cutting
coordination belongs.

Cost and latency to first working feature favor Transaction Script sharply.
A straight procedure that validates, computes, and persists in one pass has
fewer moving parts to design, fewer layers to traverse at runtime, and fewer
places a bug can hide behind an interface. This is why Fowler recommends it
as often the right starting choice for small to medium systems, and why the
pattern remains common in the first version of a system even when the team
knows the domain will eventually need a richer model.

## 4. Applicability and non-applicability

Reach for Transaction Script when the following hold.

- The business logic is genuinely simple per operation, meaning a single
  procedure can express the whole rule set for that operation without
  ballooning past what a reader can hold in view, roughly the length of a
  page or two of code.
- The operations do not share much behavior beyond straightforward data
  access, so the absence of a shared object model costs little in
  duplication.
- The team is building against real time pressure and needs a working
  system quickly, where the fixed cost of a Domain Model has not yet paid
  for itself.
- The application's data maps closely onto its persistent schema, so there
  is little independent behavior for domain objects to carry beyond what
  a direct database call already expresses.
- The team's skill and preference lean procedural, and forcing an
  object-oriented Domain Model onto that team would produce worse code
  than a well-organized set of scripts, not better.
- The system genuinely is, or is expected to remain, small to medium in the
  size and interconnectedness of its business rules. Fowler's own framing
  treats this pattern as well suited to that scale and explicitly flags
  that it stops paying off as the rule set grows.

Do NOT reach for Transaction Script when the following hold, and this list
is the more consequential of the two because it names where teams get hurt
after having reached for the pattern out of habit rather than fit. This is
the non-applicability list.

- The business rules are deeply interrelated, so that the same rule needs
  to be checked, in slightly different phrasing, from many different
  operations. Duplicated logic across scripts drifts out of sync silently,
  because nothing forces the two copies to change together, and the failure
  mode is a bug report that only reproduces from one of the two entry
  points.
- The domain has rich behavior that genuinely belongs to a concept rather
  than to an operation, for example an account that must enforce its own
  invariants regardless of which script touches it. Modeling that as a
  script per operation means every script that touches the account must
  independently remember and re-enforce the same invariant, and eventually
  one of them will not.
- The team anticipates significant reuse of the same rules across many
  request types, which a script, being tied to a single request by
  definition, resists sharing by its own shape without informal cut and paste.
- The system is expected to grow past the point where a single reader can
  trace the rules for an operation by reading one procedure top to bottom.
  Fowler names this directly as the trigger to migrate toward Domain Model
  or, as a smaller step, to introduce a Service Layer over an emerging
  Domain Model.
- Testing needs to isolate business rules from database access for fast,
  numerous unit tests. A Transaction Script that calls the database
  directly, rather than through an injected Gateway, is difficult to test
  without a real or heavily faked database, which slows the test suite down
  exactly as the team most needs speed to catch regressions confidently.
- The organization needs the same business rule enforced consistently
  regardless of which channel triggers it, web request, batch job,
  message queue consumer, because a rule embedded in one script by
  definition does not automatically apply anywhere else it is needed.

## 5. Structure

Transaction Script has a small structure because most of what it eliminates
is structure. The participants are as follows.

- **The Script.** A single method or function, one per business transaction,
  named for the operation it performs. It receives whatever input the
  presentation layer or another caller supplies, and it is responsible for
  the entire lifecycle of that operation, validating input, applying
  business rules, reading and writing persistent state, and producing a
  result or raising an error.
- **The Gateway (optional but strongly recommended).** A thin wrapper around
  the database or another external resource that the Script calls through
  rather than embedding raw SQL or a raw client call inline. The Gateway
  does not know any business rules, it only knows how to translate a simple
  request, such as "load the account with this id," into the concrete call
  the resource requires. Fowler treats the presence of a Gateway as the
  single biggest factor in whether a Transaction Script codebase stays
  testable and maintainable as it grows.
- **A Grouper class (optional).** Where a language does not allow free
  functions, or where a team wants a namespace for a related set of scripts,
  the scripts are grouped as methods on a class that exists purely to hold
  them. The class carries no state of its own beyond what a single method
  invocation needs, and the grouping is organizational, not behavioral, so
  the class does not itself represent a domain concept.
- **The caller.** A controller, a request handler, a message consumer,
  anything that receives the triggering event and invokes exactly one
  Script to handle it. The caller does not itself contain business logic,
  its job ends at marshaling input and dispatching to the right Script.

Two structural properties distinguish a well-formed Transaction Script
codebase from a badly formed one. First, each Script is a peer of every
other Script. There is no inheritance hierarchy among Scripts and no shared
mutable state between them beyond what the Gateway and the database
represent, so a bug in one Script has no direct mechanism to reach into
another. Second, the Script owns the transaction boundary. It is common,
though not required by the pattern's name alone, for the Script to begin a
database transaction on entry and commit or roll it back on exit, which is
where the pattern's name draws its second and more literal meaning.

## 6. ASCII structure diagram

```
+------------------+       +-----------------------+
|     Caller        |       |      Gateway            |
| (controller /      |------>| loadAccount(id)         |
|  request handler)  |       | saveTransfer(t)          |
+------------------+       +-----------------------+
        |                              ^
        | invokes one script            |
        v                              |
+-------------------------------------------+
|          TransferFundsScript                |
|  1. validate input                            |
|  2. load source and target accounts             |
|  3. apply business rule (sufficient funds)        |
|  4. mutate balances, write a transfer record        |
|  5. commit or roll back                                |
+-------------------------------------------+
        |
        v
+------------------+
|     Database       |
+------------------+

  (a sibling script, e.g. CloseMonthScript, is a peer with
   no shared state or inheritance relationship to the one above,
   only a shared Gateway.)
```

## 7. Dynamics

The runtime flow of a Transaction Script is a straight sequence with no
polymorphic dispatch to another object's method for the core logic. A single
transfer operation moves through the following steps.

```
Caller                Script                  Gateway              Database
  |                      |                        |                     |
  |--invoke(request)---->|                        |                     |
  |                      |--validate(request)      |                     |
  |                      |  (in process, no I/O)   |                     |
  |                      |--loadAccount(fromId)--->|                     |
  |                      |                        |--SELECT...--------->|
  |                      |                        |<--row----------------|
  |                      |<--Account--------------|                     |
  |                      |--loadAccount(toId)----->|                     |
  |                      |                        |--SELECT...--------->|
  |                      |                        |<--row----------------|
  |                      |<--Account--------------|                     |
  |                      |--(apply rule. balance   |                     |
  |                      |   check, compute new    |                     |
  |                      |   balances in memory)   |                     |
  |                      |--saveTransfer(t)------->|                     |
  |                      |                        |--BEGIN; UPDATE x2;  |
  |                      |                        |  INSERT; COMMIT---->|
  |                      |                        |<--ok-----------------|
  |                      |<--ok-------------------|                     |
  |<--Result-------------|                        |                     |
```

Two properties of this flow matter for how the pattern is built. First, there is no
step where the Script calls back into a domain object to ask it to enforce
its own invariant, because in Transaction Script the invariant enforcement,
here the sufficient-funds check, is written inline in the Script itself
rather than delegated. Second, the transaction boundary, shown as the
Gateway's BEGIN through COMMIT, usually spans only the persistence step at
the end, though some implementations open the transaction earlier, before
the reads, when the operation must guard against another script mutating the
same rows mid-flight, which trades a longer lock hold time for stronger
isolation.

## 8. Implementation variants

The most consequential implementation choice inside the pattern is whether
the Script talks to the database directly or through a Gateway. Fowler
describes both as legitimate Transaction Script implementations, but the
direct variant is the one that ages badly, because every place the Script
touches the database becomes a place a unit test must either provide a real
database or accept skipping that logic entirely. The Gateway variant, where
the Script calls a narrow interface such as `AccountGateway.load(id)` rather
than issuing SQL inline, is the variant that stays testable, because the
Gateway can be substituted with an in-memory fake for tests that only need
to exercise the business rule.

A second axis is grouping. In a language with free functions, such as Go or
JavaScript, Scripts are ordinary functions and the Grouper participant does
not exist as a distinct concept, the module or package itself is the group.
In a language that requires everything to live inside a class, such as Java
or C#, Scripts commonly become static methods or methods on a stateless
service class, and the class name is chosen to describe the group of related
operations, such as `TransferService` holding `transferFunds` alongside
`reverseTransfer`.

A third axis is transaction scope. Some implementations open the database
transaction as the very first statement in the Script and hold it for the
Script's entire duration, guaranteeing that even the reads are isolated from
concurrent writers. Others open it only around the final write, accepting
the risk that a concurrent writer changes state between the read and the
write, and compensating with an optimistic concurrency check, usually a
version column compared at write time, rather than a long-held lock. This
choice trades throughput against isolation guarantees and is orthogonal to
the pattern's shape, both are still Transaction Script.

A fourth, language-idiomatic variant is worth naming for teams working in
Go or in functional-leaning TypeScript. Because these languages do not
require an object to hold a method, a Transaction Script is often written as
a pure function that takes its dependencies, including the Gateway, as
explicit parameters or as an injected struct, rather than as a method on a
stateful service object constructed once and reused. This is functionally
identical to the class-based variant, the difference is purely how the
language expresses "one procedure per business operation" and how
dependencies reach that procedure.

## 9. Known production uses

- **IBM CICS transaction processing on mainframes.** CICS, the Customer
  Information Control System, structures each unit of online business work,
  its "transaction," as a single application program, historically written
  in COBOL, that is invoked by a short transaction code and that embeds SQL
  or file access calls directly to read and write persistent data as part of
  running the transaction end to end (IBM, "CICS transaction processing
  environment," CICS Transaction Server for z/OS documentation,
  https://www.ibm.com/docs/en/cics-ts/6.x, verified 2026-08-02, and IBM,
  "How COBOL Programs Connect to CICS, IMS, and DB2," DBzTech Technology
  Dossier, https://dbztech.blog/cics-ims-and-db2-connecting-cobol-programs-in-z-os/,
  verified 2026-08-02, describing COBOL programs that use embedded EXEC SQL
  statements to access database tables directly inside the transaction
  program). This is the shape Fowler's own pattern name gestures back to,
  and it remains in daily production use across banking, insurance, and
  airline reservation systems running on IBM Z hardware today.
- **SAP function modules and BAPIs.** SAP's ABAP application layer organizes
  a large share of its business logic as function modules, and the subset
  exposed as stable, documented external entry points, BAPIs, each implement
  one business operation, such as creating a sales order or a business
  partner, as a single callable unit that performs validation and writes
  directly against SAP's database tables within its own logical unit of
  work (SAP, "Types of Function Modules in SAP ABAP" and "Describing Remote
  Function Calls and BAPIs," SAP Learning and SAP Help documentation,
  https://learning.sap.com/courses/technical-implementation-and-operation-i-of-sap-s-4hana-and-sap-business-suite/describing-remote-function-calls-and-bapis,
  verified 2026-08-02, describing BAPIs as function modules offering a
  standard interface to a single business object operation, and noting that
  `CALL FUNCTION ... IN UPDATE TASK` bundles a function module's database
  changes into a single logical unit of work). A BAPI such as
  `BAPI_SALESORDER_CREATEFROMDAT2` has the shape of a Transaction Script.
  it validates the order data it is given, applies SAP's order creation
  rules, and writes the resulting order rows, as one callable procedure per
  business operation.
- **The revenue recognition case study in Fowler's own book.** Fowler
  presents Transaction Script, alongside Table Module and Domain Model, as
  three competing implementations of a real recognition problem he
  encountered in consulting work, using two scripts, one to calculate a
  contract's revenue recognitions and one to report the total recognized as
  of a date, each implemented as a self-contained procedure over a Gateway
  (Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, chapter 9, "The Revenue Recognition Problem," page
  112 as cited at
  https://lorenzo-dee.blogspot.com/2015/08/domain-logic-patterns.html,
  verified 2026-08-02). This is not a third-party report of production use,
  it is the pattern's own originating case study, and it is listed here
  because it is the single most cited concrete instance of the pattern in
  the software engineering literature that followed the book.
- **The iluwatar/java-design-patterns open source reference implementation.**
  This widely used, MIT-licensed catalog of Java pattern implementations, a
  project maintained on GitHub and cited across dozens of independent
  engineering blogs and tutorials as the de facto Java reference for the
  Gang of Four and enterprise pattern catalogs, implements Transaction
  Script as a `Hotel` class whose `bookRoom` and `cancelRoomBooking` methods
  each validate input, apply a business rule such as refusing a double
  booking, and persist the change through a `HotelDaoImpl` data access
  object in a single method call (iluwatar, "Transaction Script Pattern in
  Java," Java Design Patterns documentation,
  https://java-design-patterns.com/patterns/transaction-script/, verified
  2026-08-02, confirmed to be sourced from the iluwatar/java-design-patterns
  GitHub project). It is cited here as a concrete, inspectable, real
  implementation rather than as a paper description of the pattern.

## 10. Consequences

Positive consequences.

- Low up-front design cost. A team can start writing working code on day
  one without first designing an object model, which shortens the time to a
  first working feature meaningfully compared to Domain Model.
- Easy to understand in isolation. A developer can open one Script, read it
  top to bottom, and understand the entire business rule for that operation
  without tracing through a web of collaborating objects. This is a genuine
  readability win for small systems.
- A natural fit for procedural, script-oriented, or SQL-comfortable teams,
  who write clearer code in this style than they would in an imposed object
  model.
- A clean, obvious transaction boundary. Because the Script usually owns
  the database transaction from start to finish, operability concerns such
  as timeout tuning, retry logic, and logging have one place to live per
  operation.
- Low indirection overhead at runtime and in the debugger. There is no
  virtual dispatch to trace through multiple objects to find where a
  computation happens, which shortens debugging sessions for simple bugs.

Negative consequences.

- Duplication across scripts grows as the number of operations grows,
  because each Script is self-contained by design and nothing in the pattern
  forces two scripts that both validate an account to share that
  validation. Fowler's own guidance is to extract shared subprocedures for
  pure mechanics, but that guidance requires ongoing discipline, it is not
  enforced by the pattern.
- The pattern does not scale gracefully as business rules grow more
  interconnected. A codebase that starts with ten simple scripts and grows
  to two hundred, where many of those two hundred need overlapping rule
  checks, tends to accumulate copy-pasted logic that drifts out of sync,
  which is the single most cited failure mode in dimension 11 below.
- Testing business logic in isolation from the database is difficult unless
  the team disciplines itself to route all persistence through a Gateway.
  Without that discipline, unit tests either require a real database or do
  not exist, and the team loses fast feedback on regressions.
- The pattern offers no natural home for behavior that belongs to a domain
  concept rather than to an operation, so invariants that should hold for
  an account "no matter what touches it" have to be re-implemented in every
  Script that touches an account, and this is where correctness bugs
  concentrate as a system grows.
- Migration cost. A codebase built entirely as Transaction Scripts that
  later needs the reuse and consistency benefits of a Domain Model faces a
  genuine rewrite, not a mechanical refactor, because the logic scattered
  across many procedures has to be identified, extracted, and reorganized
  around the concepts it actually concerns.

## 11. Failure modes and misuse

**Symptom.** The same business rule, phrased slightly differently, is fixed
in one place after a bug report, and the identical bug resurfaces weeks
later from a different entry point that a customer or another team uses.
**Cause.** The rule was duplicated across two or more Scripts rather than
extracted into a shared subprocedure, because Transaction Script has no
structural mechanism that forces or even signals duplication, the team has
to notice it by discipline alone. **Fix.** Extract the duplicated check into
a shared subprocedure or a small validation function called from every
Script that needs it, and add a single test against that shared function so
future duplication is caught before merge rather than after a second bug
report. If duplication keeps recurring across a growing surface of
operations, this is the concrete signal Fowler names as the trigger to
consider migrating the affected area toward Domain Model.

**Symptom.** Unit tests for business rules are slow, flaky, or simply do not
exist, and the team relies almost entirely on manual QA or full-system tests
to catch regressions in core logic. **Cause.** The Script talks to the
database directly, embedding SQL or ORM calls inline rather than routing
through a Gateway, so exercising the business rule in a test requires either
a real database connection or an elaborate mock of the database library
itself. **Fix.** Introduce a Gateway interface between the Script and the
database, with a real implementation for production and an in-memory fake
for tests. This is a mechanical refactor that does not change the Script's
external behavior, and Fowler treats its presence as the deciding factor
between a Transaction Script codebase that stays maintainable and one that
does not.

**Symptom.** A single Script has grown past several hundred lines, contains
deeply nested conditionals for what were originally a handful of edge cases,
and new developers report that they cannot safely change it without
understanding every branch. **Cause.** The business rule set for that one
operation genuinely outgrew what a linear procedure can express clearly,
often because the operation accreted special cases over time, one customer
segment at a time, one regulatory exception at a time, without anyone
stepping back to notice the growth. **Fix.** Extract the distinct policies
inside the Script into small, separately named, separately testable
functions or objects, even without adopting a full Domain Model. This is
the smallest possible step toward Table Module or Domain Model, and it is
frequently sufficient on its own. If the growth continues, treat it as
evidence the operation belongs to a richer model and plan the migration
described in dimension 14.

**Symptom.** Two operations that run concurrently against the same account
occasionally produce a balance that does not match the sum of all recorded
transfers, and the bug is intermittent and hard to reproduce locally.
**Cause.** The Script's transaction boundary was scoped too narrowly, for
example wrapping only the final write rather than the read-modify-write
sequence, so a second Script's write lands between the first Script's read
and its own write, a classic lost-update race. **Fix.** Either widen the
transaction boundary to cover the full read-modify-write sequence with an
appropriate isolation level, or add optimistic concurrency control, a
version column checked and incremented atomically at write time, so a
conflicting concurrent write fails loudly and can be retried rather than
silently corrupting the balance.

**Symptom.** A new caller, for example a batch import job, needs to perform
"the same" operation that an existing Script already performs from a web
request, and a developer copies the Script's body into the new caller with
small adjustments rather than reusing it. **Cause.** The Script was written
as, or tightly coupled to, a single entry point, for example accepting a web
request object directly rather than a plain input value, so it cannot be
called cleanly from a different context. **Fix.** Separate the Script's
signature from any single caller's input shape. accept plain values or a
small input object, and let each caller, whether a web handler or a batch
job, translate its own input into that shape before invoking the same
Script. This keeps the pattern's per-operation shape intact while allowing
genuine reuse across entry points.

## 12. Trade-off matrix

| Force | Transaction Script | Table Module | Active Record | Domain Model |
|---|---|---|---|---|
| Up-front design cost | Lowest. one procedure per operation, no model to design first. | Low-moderate. one class per database table, still schema-driven. | Low. one class per table with behavior attached, minimal extra design. | Highest. requires deliberate modeling of concepts and their relationships. |
| Handling of complex, interrelated rules | Poor. duplication grows as rules interact across many scripts. | Moderate. logic per table, but cross-table rules still awkward. | Poor. rules attached to a record fight with rules that span several records. | Strong. built to express rules that involve multiple collaborating objects. |
| Testability of business logic alone | Poor unless a Gateway is used, then good. | Good, business logic in table classes is separable from persistence. | Poor. persistence and behavior are fused in the same object by design. | Good. objects are naturally isolable with a Repository or Gateway boundary. |
| Reuse of a rule across operations | Poor by default, requires disciplined extraction. | Moderate, shared per table but not automatically per operation. | Moderate, shared per record type. | Strong, behavior lives on the concept and every caller gets it for free. |
| Fit for a small or short-lived system | Excellent, matches the low ceremony the situation needs. | Good, similar ceremony, better fit when the tabular structure carries most of the weight. | Good for simple CRUD-shaped systems. | Poor, the fixed modeling cost rarely pays off before the project ends. |
| Fit for a large, long-lived system with growing rules | Poor, the pattern's own author names this as the point to migrate away. | Moderate, better than Transaction Script but still schema-bound. | Poor, the same fusion of persistence and behavior that helps small systems hurts large ones. | Excellent, the pattern this trio exists to lead a team toward. |
| Team fit for a procedural-leaning team | Excellent. | Good. | Good. | Poor unless the team is already comfortable with object modeling. |

Table Module organizes logic around each database table as a whole rather
than around each row or each operation, and is the middle option Fowler
places between Transaction Script and Domain Model for teams whose data is
strongly relational but whose logic still benefits from more structure than
a bag of independent scripts. Active Record fuses persistence and a small
amount of per-row behavior into a single class per table, and is a distinct
pattern in the same catalog family covered separately. Domain Model is the
pattern Transaction Script is most directly positioned against, since both
answer the same question, where does business logic live, with opposite
answers.

## 13. Related and incompatible patterns

**Gateway** is the pattern that makes a well-formed Transaction Script
codebase possible. A Gateway wraps access to an external resource, most
often the database, behind a narrow interface, and every failure mode in
dimension 11 that concerns testability traces back to a Script that talks to
the database directly instead of through one. The two patterns are commonly
adopted together, and a Transaction Script without a Gateway is, in
practice, a weaker version of the pattern than one built with it.

**Table Module** and **Domain Model** are Transaction Script's two named
alternatives in the same chapter of Fowler's book, and the trade-off matrix
above compares all three directly. A team choosing among the three is not
choosing a technical detail, it is choosing where domain logic is allowed to
live, and that choice shapes nearly everything else in the application's
architecture.

**Active Record** composes uneasily with Transaction Script within the same
layer of a system, because both patterns want to own where an operation's
logic lives, Active Record on the record's own class, Transaction Script in
a separate procedure that treats the record as passive data. A codebase can
use Active Record for simple per-row CRUD and Transaction Script for
multi-record business operations, and this combination is common in
practice, but the two are not meant to both own the same operation.

**Template Method** frequently appears inside individual Scripts that share
a skeleton, for example "validate, then compute, then persist," where the
skeleton is factored into a base method and the variable step, the
computation, is supplied by each concrete Script. This is a legitimate way
to reduce duplication among Scripts without adopting a full Domain Model,
and it is the pattern most often reached for as an intermediate step
described in dimension 14.

**Service Layer** sits above a set of Transaction Scripts, or above a
Domain Model, as a coarse-grained facade that presentation code calls into.
Introducing a Service Layer does not by itself change whether the logic
underneath is organized as scripts or as a rich model, it changes how that
logic is exposed to callers, and it is a common first step teams take when
migrating away from Transaction Script, because it lets them relocate logic
underneath the facade incrementally without breaking every caller at once.

**Domain Model is incompatible with Transaction Script at the level of a
single operation.** An operation's logic either lives in a procedure named
for that operation, or it lives distributed across the objects it concerns,
and a codebase that tries to do both for the same operation produces the
worst of each, duplicated validation in the script and half-enforced
invariants in the objects. The two patterns coexist fine at the level of a
whole system during a migration, described next, but not for one operation
at one time.

## 14. Refactoring path in and out

Introducing Transaction Script into a codebase that does not yet have it
usually means introducing it as the default shape for new operations rather
than converting existing code. When a new business operation is needed, the
first questions to ask are whether it is simple enough, self-contained
enough, and low-reuse enough to fit the applicability list in dimension 4.
If so, the concrete steps are as follows. write a single function or method
named for the operation, write or reuse a Gateway for the data it needs to
read and write, put validation first, business rules second, and the
Gateway calls last inside that one procedure, and wrap the persistence
step, or the whole procedure if concurrent writers are a concern, in a
single database transaction. Where the codebase already has other
operations built as Transaction Scripts, follow their existing conventions
for Gateway naming and transaction handling rather than inventing new ones,
consistency across Scripts is worth more than any individual Script's local
elegance.

Removing Transaction Script, migrating a script-based area of a system
toward a richer model, is the more consequential direction and the one
Fowler devotes explicit attention to, because it is the direction real
systems most often need over time. The path is incremental, not a rewrite,
and proceeds roughly as follows.

1. Identify the operations whose Scripts have grown the failure-mode
   symptoms in dimension 11, duplicated rules, hard-to-test logic tangled
   with database calls, or accreting special-case conditionals, rather than
   attempting to migrate every Script in the system at once.
2. Introduce a Gateway in front of the affected Scripts first if one does
   not already exist, since this is a pure refactor with no behavior change
   and it is a prerequisite for safely testing the steps that follow.
3. Extract the domain concept the duplicated logic actually concerns, for
   example an `Account`, as a small object that owns the invariant, such as
   "balance cannot go negative," that was previously re-checked inside every
   Script that touched an account. This step is closely related to the
   refactoring technique Extract Class, and it should be done with tests in
   place before and after, per the testing discipline in dimension 15.
4. Move the previously duplicated checks into that new object's methods, one
   Script at a time, and update each Script to call the object rather than
   re-implementing the check inline. After each Script is updated, its
   behavior should be provably unchanged by the existing tests, which is
   the safety property that makes this an incremental migration rather than
   a rewrite.
5. Once several such objects exist and several Scripts have been reduced to
   thin orchestration over them, calling the objects in the right order and
   handling the transaction boundary, the system has effectively grown a
   Domain Model in the areas that needed it while leaving genuinely simple
   operations as Transaction Scripts, which is a legitimate, permanent end
   state, not merely a waypoint. Fowler's own position is that most real
   systems end up as a mix, not as a pure instance of any one pattern in the
   chapter.

## 15. Testing and verification

Transaction Script is easy to test at the integration level and hard to
test at the unit level unless the Gateway discipline from dimension 8 is in
place. An integration test that spins up a real or containerized database,
calls the Script, and asserts on the resulting rows exercises the whole
pattern honestly, because the pattern's whole point is that the procedure,
the validation, and the persistence are meant to be understood together as
one unit. This kind of test is genuinely valuable for Transaction Script in
a way it is less central for Domain Model, where the unit tests around
individual domain objects carry more of the confidence.

Where a Gateway exists, unit testing the business rule in isolation becomes
straightforward. construct the Script with an in-memory fake Gateway
pre-loaded with known data, invoke the Script, and assert on both the
returned result and the calls made to the fake Gateway, such as asserting
that `saveTransfer` was called with the expected new balances. This test
double is a plain Fake, per Fowler's own terminology for test doubles in the
same book (Martin Fowler, "Mocks Aren't Stubs,"
https://martinfowler.com/articles/mocksArentStubs.html, verified 2026-08-02,
for the vocabulary of stubs, fakes, and mocks used here), not a Mock in the
strict interaction-verifying sense, because for most Transaction Script
tests what matters is the state the fake ends up holding, not the exact
sequence of calls made to reach it.

What becomes harder to test as a direct consequence of the pattern is
anything that spans multiple Scripts, since there is no shared object whose
state a test can inspect across two operations, only the database rows both
Scripts touch. Testing a multi-step business process implemented as two or
more Scripts called in sequence usually means testing the sequence at the
integration level, against the database, rather than at the unit level,
because the coordination between the Scripts lives in whatever caller
invokes them in order, and that coordination has no natural home to be
tested in isolation the way a Domain Model's aggregate would provide.

Regression protection for the failure modes in dimension 11 specifically
benefits from a small number of targeted tests. one test per shared
validation rule, run against every Script that is supposed to enforce it,
catches the duplication-drift failure mode directly, and one concurrency
test, using two threads or two database connections against the same
account, catches the lost-update failure mode directly, well before it
would otherwise surface as an intermittent production bug.

## 16. Observability signals

Because a Transaction Script usually owns a single database transaction
from start to finish, the transaction's duration is the single most
informative metric to log per Script, tagged by the Script's name. A
healthy Transaction Script system shows tight, consistent duration
distributions per operation, since each Script does a fixed, small amount of
work. A widening distribution or a growing tail for one specific Script is
the first observable sign that the operation has accreted complexity beyond
what a straight procedure comfortably handles, well before a developer
notices the source code has grown unwieldy.

Log the outcome of every Script invocation, success, business rule
rejection, or unexpected error, each as a distinct outcome rather than
collapsing rejections and errors into one bucket. Business rule rejections,
such as "insufficient funds," are expected, common, and not a signal of a
problem, while unexpected errors, a database timeout, a null where valid
data was expected, are a genuine signal. A dashboard that conflates the two
under a single "failure rate" metric will alarm constantly on ordinary
business rejections and desensitize the team to the errors that matter.

Trace context should follow the Script from its caller through its Gateway
calls to completion as one span per operation, since the Script is the
natural unit of work to trace, matching the pattern's own transaction
boundary. Where a system has multiple Scripts that are known to be called in
sequence for a larger business process, the caller that sequences them
should propagate a single correlation identifier across that sequence, so
that a failure partway through the process can be traced back to exactly
which Script in the sequence produced it.

Concurrency conflicts, whether caught by a database-level lock timeout or
by an application-level optimistic concurrency check, should be counted and
alerted on per account or per resource, not only logged, because a rising
rate of concurrency conflicts on the same resource is the earliest
observable warning of the lost-update failure mode described in dimension
11, well before it produces an incorrect balance a customer notices.

## 17. Security and privacy implications

A Transaction Script that builds SQL by string concatenation rather than
through parameterized queries in its Gateway is exactly as vulnerable to SQL
injection as any other code that does the same thing, and the pattern
carries no inherent protection against this. Because the pattern encourages
direct, close-to-the-metal database access, teams should hold the same
parameterized-query discipline for a Transaction Script's Gateway as they
would for any other data access code, and code review for new Scripts should
specifically check that user-supplied values never reach a query string
directly.

Because business rules, including authorization checks such as "can this
caller transfer funds out of this account," are written inline inside each
Script rather than enforced centrally by an object that every path must go
through, a Transaction Script codebase carries a specific privilege
escalation risk. a new Script added later, or an existing Script modified in
haste, can omit an authorization check that every other Script correctly
performs, and nothing in the pattern's structure catches that omission
automatically. This is the security-flavored instance of the same
duplication failure mode described in dimension 11, and the same fix
applies, extract the shared check into one place every relevant Script calls
through, so a missing check fails loudly at review time rather than silently
in production.

Personal or sensitive data handled inside a Script is exposed to whatever
logging the Script or its caller performs, and because a Script commonly
receives its entire request payload as input, a broad or unfiltered request
log at the caller level risks logging sensitive fields, account numbers,
personal identifiers, that a more layered architecture might have kept
further from the logging boundary. Teams adopting Transaction Script should
apply field-level redaction at the logging boundary explicitly rather than
relying on the pattern's structure to keep sensitive data away from logs,
since it does not.

## Code examples

The three languages below were chosen because Transaction Script is
genuinely idiomatic in each without needing framework scaffolding. Python
and Go both allow a Script to be a plain function taking its Gateway as a
parameter, which matches the pattern's shape directly, and TypeScript shows
the class-and-interface variant common in Node.js backend codebases. Java
was intentionally left out of this entry because a working JDK was not
available in the environment used to write it, and a Java sample that could
not be compiled here is not included rather than presented as verified when
it was not.

### Python

```python
from dataclasses import dataclass


class InsufficientFundsError(Exception):
    pass


@dataclass
class Account:
    id: str
    balance_cents: int


class AccountGateway:
    """Thin wrapper around persistence. Real implementation talks to a
    database, this in-memory version exists so the script is testable
    without one."""

    def __init__(self) -> None:
        self._accounts: dict[str, Account] = {}

    def stock(self, account: Account) -> None:
        self._accounts[account.id] = account

    def load(self, account_id: str) -> Account:
        return self._accounts[account_id]

    def save(self, account: Account) -> None:
        self._accounts[account.id] = account


def transfer_funds_script(
    gateway: AccountGateway, from_id: str, to_id: str, amount_cents: int
) -> None:
    """One procedure, one business transaction. Validate, apply the
    rule, persist. This is the whole Transaction Script."""
    if amount_cents <= 0:
        raise ValueError("amount must be positive")

    source = gateway.load(from_id)
    target = gateway.load(to_id)

    if source.balance_cents < amount_cents:
        raise InsufficientFundsError(
            f"account {from_id} has {source.balance_cents}, needs {amount_cents}"
        )

    source.balance_cents -= amount_cents
    target.balance_cents += amount_cents

    gateway.save(source)
    gateway.save(target)


if __name__ == "__main__":
    gw = AccountGateway()
    gw.stock(Account("alice", 10_000))
    gw.stock(Account("bob", 500))

    transfer_funds_script(gw, "alice", "bob", 2_500)

    print(gw.load("alice").balance_cents, gw.load("bob").balance_cents)

    try:
        transfer_funds_script(gw, "bob", "alice", 999_999)
    except InsufficientFundsError as e:
        print("rejected", e)
```

### TypeScript

```typescript
interface Account {
  id: string;
  balanceCents: number;
}

class InsufficientFundsError extends Error {}

interface AccountGateway {
  load(id: string): Promise<Account>;
  save(account: Account): Promise<void>;
}

class InMemoryAccountGateway implements AccountGateway {
  private readonly accounts = new Map<string, Account>();

  stock(account: Account): void {
    this.accounts.set(account.id, { ...account });
  }

  async load(id: string): Promise<Account> {
    const found = this.accounts.get(id);
    if (!found) {
      throw new Error(`no such account ${id}`);
    }
    return { ...found };
  }

  async save(account: Account): Promise<void> {
    this.accounts.set(account.id, { ...account });
  }
}

// One procedure named for the business operation. Validate, apply the
// rule, persist, all in one place, which is the pattern's whole shape.
async function transferFundsScript(
  gateway: AccountGateway,
  fromId: string,
  toId: string,
  amountCents: number
): Promise<void> {
  if (amountCents <= 0) {
    throw new Error("amount must be positive");
  }

  const source = await gateway.load(fromId);
  const target = await gateway.load(toId);

  if (source.balanceCents < amountCents) {
    throw new InsufficientFundsError(
      `account ${fromId} has ${source.balanceCents}, needs ${amountCents}`
    );
  }

  source.balanceCents -= amountCents;
  target.balanceCents += amountCents;

  await gateway.save(source);
  await gateway.save(target);
}

async function main(): Promise<void> {
  const gateway = new InMemoryAccountGateway();
  gateway.stock({ id: "alice", balanceCents: 10_000 });
  gateway.stock({ id: "bob", balanceCents: 500 });

  await transferFundsScript(gateway, "alice", "bob", 2_500);

  const alice = await gateway.load("alice");
  const bob = await gateway.load("bob");
  console.log(alice.balanceCents, bob.balanceCents);

  try {
    await transferFundsScript(gateway, "bob", "alice", 999_999);
  } catch (err) {
    if (err instanceof InsufficientFundsError) {
      console.log("rejected", err.message);
    } else {
      throw err;
    }
  }
}

main();
```

### Go

```go
package transactionscript

import "fmt"

type Account struct {
	ID           string
	BalanceCents int64
}

type InsufficientFundsError struct {
	AccountID string
	Have      int64
	Need      int64
}

func (e *InsufficientFundsError) Error() string {
	return fmt.Sprintf("account %s has %d, needs %d", e.AccountID, e.Have, e.Need)
}

// AccountGateway is the thin persistence boundary. A real implementation
// wraps a SQL database, this one is an in-memory fake used both in
// production-shaped code and directly in tests.
type AccountGateway struct {
	accounts map[string]*Account
}

func NewAccountGateway() *AccountGateway {
	return &AccountGateway{accounts: make(map[string]*Account)}
}

func (g *AccountGateway) Stock(a Account) {
	acc := a
	g.accounts[a.ID] = &acc
}

func (g *AccountGateway) Load(id string) (*Account, error) {
	a, ok := g.accounts[id]
	if !ok {
		return nil, fmt.Errorf("no such account %s", id)
	}
	return a, nil
}

func (g *AccountGateway) Save(a *Account) error {
	g.accounts[a.ID] = a
	return nil
}

// TransferFundsScript is one procedure per business operation. Validate,
// apply the rule, persist. There is no separate object that owns the
// sufficient-funds invariant, the script itself enforces it inline.
func TransferFundsScript(g *AccountGateway, fromID, toID string, amountCents int64) error {
	if amountCents <= 0 {
		return fmt.Errorf("amount must be positive")
	}

	source, err := g.Load(fromID)
	if err != nil {
		return err
	}
	target, err := g.Load(toID)
	if err != nil {
		return err
	}

	if source.BalanceCents < amountCents {
		return &InsufficientFundsError{AccountID: fromID, Have: source.BalanceCents, Need: amountCents}
	}

	source.BalanceCents -= amountCents
	target.BalanceCents += amountCents

	if err := g.Save(source); err != nil {
		return err
	}
	return g.Save(target)
}

func Example() {
	gw := NewAccountGateway()
	gw.Stock(Account{ID: "alice", BalanceCents: 10_000})
	gw.Stock(Account{ID: "bob", BalanceCents: 500})

	if err := TransferFundsScript(gw, "alice", "bob", 2_500); err != nil {
		panic(err)
	}

	alice, _ := gw.Load("alice")
	bob, _ := gw.Load("bob")
	fmt.Println(alice.BalanceCents, bob.BalanceCents)

	err := TransferFundsScript(gw, "bob", "alice", 999_999)
	fmt.Println("rejected", err)
}
```

## 18. References

1. Martin Fowler. *Patterns of Enterprise Application Architecture*.
   Addison-Wesley, 2002. ISBN 0-321-12742-0. Chapter 9, "Domain Logic
   Patterns," section "Transaction Script," and "The Revenue Recognition
   Problem," page 112. Source of the pattern's name, intent, structure, and
   the originating case study. Page number confirmed via the excerpted quote
   at https://lorenzo-dee.blogspot.com/2015/08/domain-logic-patterns.html,
   verified 2026-08-02.
2. Martin Fowler. "Transaction Script." Catalog of Patterns of Enterprise
   Application Architecture. https://martinfowler.com/eaaCatalog/transactionScript.html
   Verified 2026-08-02. Source of the one-sentence pattern intent quoted in
   dimension 1.
3. Martin Fowler. "AnemicDomainModel." Bliki.
   https://martinfowler.com/bliki/AnemicDomainModel.html Verified 2026-08-02.
   Source for Fowler's own statement that an anemic Domain Model degenerates
   into Transaction Script in practice, used in dimension 10's discussion of
   the boundary between the two patterns.
4. Martin Fowler. "Mocks Aren't Stubs."
   https://martinfowler.com/articles/mocksArentStubs.html Verified
   2026-08-02. Source of the Fake versus Mock test-double vocabulary used in
   dimension 15.
5. IBM. "CICS transaction processing environment." CICS Transaction Server
   for z/OS documentation. https://www.ibm.com/docs/en/cics-ts/6.x Verified
   2026-08-02. Source for the CICS production use in dimension 9.
6. IBM, via DBzTech. "How COBOL Programs Connect to CICS, IMS, and DB2."
   https://dbztech.blog/cics-ims-and-db2-connecting-cobol-programs-in-z-os/
   Verified 2026-08-02. Source for the description of embedded EXEC SQL
   inside CICS COBOL transaction programs in dimensions 1 and 9.
7. SAP. "Describing Remote Function Calls and BAPIs." SAP Learning,
   technical implementation and operation of SAP S/4HANA and SAP Business
   Suite course documentation.
   https://learning.sap.com/courses/technical-implementation-and-operation-i-of-sap-s-4hana-and-sap-business-suite/describing-remote-function-calls-and-bapis
   Verified 2026-08-02. Source for the BAPI and function module production
   use in dimension 9.
8. iluwatar. "Transaction Script Pattern in Java." Java Design Patterns.
   https://java-design-patterns.com/patterns/transaction-script/ Verified
   2026-08-02. Confirmed to be published from the iluwatar/java-design-patterns
   open source GitHub project. Source for the `Hotel` and `HotelDaoImpl`
   reference implementation cited in dimension 9.
