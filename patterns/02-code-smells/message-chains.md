---
name: Message Chains
slug: message-chains
family: 02-code-smells
category: Coupling
aliases: [Law of Demeter Violation, Train Wreck]
first_described: "Fowler and Beck 1999"
maturity: canonical
related: [feature-envy, middle-man, inappropriate-intimacy, data-clumps, builder]
incompatible_with: []
verified: 2026-08-02
---

# Message Chains

## 1. Name, aliases, and lineage

The canonical name is Message Chains. It is one of the original smells
catalogued in Martin Fowler, *Refactoring. Improving the Design of Existing
Code*, Addison-Wesley, 1st edition, 1999, in the chapter "Bad Smells in Code",
with Kent Beck credited as co-author of that chapter's smell catalog. The
refactoring that resolves it, Hide Delegate, and its inverse, Remove Middle
Man, both survive into the 2nd edition (Addison-Wesley, 2018) and are listed on
Fowler's public catalog site under the "moving features" and "organizing data"
groupings respectively (https://refactoring.com/catalog/hideDelegate.html,
verified 2026-08-02, which shows the canonical worked example
`aPerson.department.manager` collapsing to `aPerson.manager`).

The term "code smell" itself was coined by Kent Beck while helping Fowler
write the first edition, not by Fowler alone. Fowler records this directly.
"The term was first coined by Kent Beck while helping me with my Refactoring
book" (https://martinfowler.com/bliki/CodeSmell.html, verified 2026-08-02).
This entry follows the same attribution as the sibling entry Feature Envy for
that fact, since both smells come from the same chapter of the same source.

The most durable alias is Law of Demeter Violation. The underlying design
rule the smell violates, "only talk to your friends", was proposed by Ian
Holland in the fall of 1987 while working on the Demeter Project at
Northeastern University (https://www.ccs.neu.edu/home/lieber/LoD.html,
verified 2026-08-02, which states plainly "Only talk to your friends" as the
motto and names the Demeter Project as the origin of the name). The rule was
later formalized and popularized in academic and practitioner circles by Karl
Lieberherr and Ian Holland jointly, and the same page is maintained by
Lieberherr's group as the long-running reference for the rule. A message
chain is the code shape a reader observes when the Law of Demeter has been
broken. the smell is the symptom, the law is the principle it violates, and
the two names are used almost interchangeably in practice, which is why
static analysis tools name their detector after the law rather than the
smell. Apache PMD, for instance, ships a rule literally named `LawOfDemeter`
under its Design category, described as forbidding "fetching data from too
far away, for some definition of distance, in order to reduce coupling
between classes or objects of different levels of abstraction"
(https://docs.pmd-code.org/latest/pmd_rules_java_design.html, verified
2026-08-02).

Casual engineering conversation sometimes calls a long chain a train wreck,
because the successive dots resemble a derailed line of railcars when a call
spans a wide screen. This entry treats that phrase as informal shop talk
rather than a sourced alias, since no citable primary source for its
coinage was confirmed during verification, and it is left out of the
frontmatter aliases list for that reason.

No serious source disputes the name Message Chains or claims a rival name for
the specific code shape. The only real naming friction is the one this entry
spends dimension 4 on directly. a chain of method calls is not automatically
this smell, and confusing the two is the single most common misdiagnosis a
reader will make.

## 2. Problem and context

A client asks one object for a second object, then immediately asks that
second object for a third, and continues down the line until it finally reads
or calls the field it actually wanted. In code this reads as a run of dots.
`order.getCustomer().getAddress().getZipCode()`, or in a language with public
fields instead of accessors, `order.customer.address.zipCode`. The client
never wanted the customer object or the address object for their own sake. it
wanted the zip code, and the customer and the address were merely the road it
had to travel to reach it.

The context in which this arises is almost always an object graph that
mirrors a real-world containment relationship and is reachable step by step
from the client's starting point. an order belongs to a customer, a customer
has an address, an address has a zip code. Object models built directly from
an entity-relationship diagram or from a database schema tend to expose
exactly this shape, because the schema designer's job was to represent
containment correctly, not to think about who would later need to read a
leaf value from three hops away. The problem surfaces the moment a second
piece of client code needs the same leaf value. that code repeats the same
three-step traversal, and now two places in the codebase depend on the full
path from Order through Customer through Address to ZipCode, rather than on
the single fact that an order has a shipping zip code.

The chain length that triggers concern is not fixed by any formal count. Two
hops through a well-understood, stable relationship rarely bothers anyone in
practice. Three or more hops through classes that belong to different layers
or different teams is where the smell earns its name, because at that point
the client has stopped depending on its collaborators and started depending
on its collaborators' collaborators, which is precisely the coupling the Law
of Demeter's "friends, not strangers" framing warns against.

## 3. Forces

**Reachability versus encapsulation.** An object graph that exposes every
contained object lets any client reach any data with a direct, honest path.
That same reachability means any client can reach past the object that
should have owned the behavior, straight to its internals, which is the
essence of what encapsulation was supposed to prevent.

**Convenience today versus coupling tomorrow.** Writing
`order.getCustomer().getAddress().getZipCode()` at the call site is the
fastest thing to type the first time a developer needs a zip code. Every
subsequent caller who copies that same three-hop expression multiplies the
number of places that must change if the shape of Customer or Address ever
changes, for example when an order gains multiple shipping addresses.

**Reading depth versus reading width.** A chain concentrates a lot of
information into one line. a reader who already knows the domain can often
parse `order.customer.address.zipCode` faster than they could parse three
separate accessor methods spread across a class. The same density is exactly
what makes the chain brittle. one intermediate step returning null, or one
intermediate class being refactored away, breaks every reader who relied on
the shape staying stable.

**Test setup cost versus test directness.** Testing code that reads a chain
usually means constructing every intermediate object in the chain just to
reach the leaf value the test actually cares about. a hidden delegate method
that returns the zip code directly needs only the leaf value itself to be
faked or stubbed, which is a materially cheaper test to write and a cheaper
test to keep passing when unrelated intermediate classes change shape.

**Deliberate fluency versus accidental traversal.** Some chains are
intentional, carefully designed sequences of calls that each return the same
kind of thing so a caller can compose a small domain-specific language, the
way JMock's expectation-setting API does
(https://martinfowler.com/bliki/FluentInterface.html, verified 2026-08-02,
where Fowler names JMock directly as a well thought out fluent example). Those
chains favor readability at the API design layer and are a completely
different force balance from an accidental chain that merely follows a
containment hierarchy because nobody stopped to hide it. Dimension 4 draws
this line precisely, because collapsing the two into one judgement is the
single most common mistake a reviewer makes when flagging this smell.

This entry favors reducing coupling and reducing the blast radius of a future
structural change over the small convenience of a shorter line at the call
site, on the reasoning that the convenience is paid once by the author and the
coupling cost is paid repeatedly by every future maintainer who has to touch
any link in the chain.

## 4. Applicability and non-applicability

Reach for the Message Chains diagnosis, and its fix, when the following hold.

- A client walks through two or more intermediate objects purely to reach a
  value or a behavior on the object at the far end, and the intermediate
  objects themselves are never otherwise used by that client.
- The same multi-hop expression appears at more than one call site, so a
  structural change to any link in the chain (renaming a field, splitting a
  class, adding a null intermediate step) would require editing every one of
  those call sites.
- The intermediate classes belong to a different layer, module, or team than
  the client, so the client's code is now implicitly aware of an internal
  structure it does not own and was never asked to depend on.
- The chain crosses an abstraction boundary that is meant to be opaque, for
  example a client outside a persistence layer reaching through a lazily
  loaded entity's associations to read a value two hops deep.

Do NOT apply the Hide Delegate fix, and do not flag the code as this smell, in
these situations.

- The chain is a genuinely fluent interface, deliberately designed so each
  call returns an object of the same kind for the purpose of composing a
  small domain-specific language, such as a query builder, a test expectation
  builder like JMock, or a string formatter. Collapsing a fluent chain into a
  single delegate call destroys the readability the API was built to provide,
  and Fowler explicitly separates this case from an accidental chain
  (https://martinfowler.com/bliki/FluentInterface.html, verified 2026-08-02).
- The chain is exactly two hops through a relationship that is stable, owned
  by the same module as the client, and unlikely to change shape. adding a
  delegate method for every two-hop read in a small, cohesive module can add
  more indirection than it removes coupling.
- The intermediate object is a value object or a data transfer object whose
  entire purpose is to be read through by many different clients, such as a
  configuration object or a parsed response body. those objects are meant to
  be read through, and hiding every field behind a delegate on the parent
  simply moves the same reads to a longer list of forwarding methods with no
  coupling reduction.
- The language or library idiom already treats the chain as the correct
  interface, for example a standard library builder pattern like Java's
  `StringBuilder`, or a monadic pipeline in a functional language where each
  link transforms the same kind of container rather than descending into an
  unrelated object's internals.
- The client genuinely needs the intermediate object for its own sake later in
  the same method, not only as a stepping stone to the final value. in that
  case the client legitimately depends on the intermediate object, and hiding
  it behind a delegate would just force the client to fetch it a second time
  through a different path.

## 5. Structure

**Client.** The object or function that needs a value or a behavior that
lives several hops away from something it already holds a reference to. It is
the object paying the coupling cost.

**Head object.** The object the client already has a direct, legitimate
reference to, and the starting point of the chain, for example an `Order`.

**Intermediate objects.** One or more objects returned along the way, each
reached only to call the next accessor on it, for example a `Customer`
returned by the order and an `Address` returned by the customer. These
objects are never used by the client for anything other than continuing the
chain.

**Target.** The value or behavior the client actually wanted, sitting at the
far end of the chain, for example the `zipCode` field on the `Address`.

**Delegate method** (post-fix). A method placed on the head object, or on
whichever intermediate object the client's true collaborator should be, that
performs the same lookup internally and returns the target directly, so the
client calls one method instead of walking the chain itself.

## 6. ASCII structure diagram

```
BEFORE, message chain

+--------+
| Client |
+--------+
     | .customer
     v
+--------------+
| Head (Order) |
+--------------+
     | .address
     v
+-------------------------+
| Intermediate (Customer) |
+-------------------------+
     | .address
     v
+------------------------+
| Intermediate (Address) |
+------------------------+
     | .zipCode
     v
target

Client reaches through Order and Customer to touch
Address directly, one accessor call per hop.

AFTER, Hide Delegate applied

+--------+
| Client |
+--------+
     | .shippingZip()
     v
+--------------+
| Head (Order) |
+--------------+
     | internally walks customer.address.zipCode
     v
+----------+
| Customer |
+----------+
     |
     v
+---------+
| Address |
+---------+

Client now depends on Order alone. Customer and Address
are private implementation detail of how Order answers
the question.
```

## 7. Dynamics

**Before the fix, at read time.** The client calls the head object's accessor
and receives a reference to the first intermediate object. The client then
calls an accessor on that returned reference and receives a second
intermediate object, and repeats this for however many hops the chain has.
Only the final call returns the target value or invokes the target behavior.
Every intermediate call is a real method invocation, real object identity
lookup, and in a language with nullable references, a real opportunity for a
null pointer exception if any intermediate step legitimately has no
downstream object yet, for example a customer who has not yet supplied a
shipping address.

**Before the fix, at change time.** A developer renames a field on the
intermediate class, or replaces the intermediate class with a different
representation, for example moving from a single `Address` to a list of
addresses with a designated default. Every call site that walked the old
chain now fails to compile, or worse, in a dynamically typed language,
fails silently at runtime the next time that code path executes. The dynamics
here are the actual cost the smell imposes. it is invisible during normal
execution and only becomes visible, expensively, the moment something
upstream changes shape.

**After the fix, at read time.** The client calls one method on the head
object. That method performs the same internal lookup the client used to
perform, but it does so inside the head object's own implementation, where it
has the right to know its own collaborators' shapes. If any intermediate step
can legitimately be absent, the delegate method is the single place that
decides what to do about it, a sensible default, a documented exception, or an
optional return type, rather than every call site independently reinventing
that decision or forgetting to handle it at all.

**After the fix, at change time.** The same structural change, renaming a
field or replacing an intermediate class, is now made once, inside the
delegate method's implementation. Every client that called the delegate
method continues to compile and continues to behave correctly, because the
client's contract with the head object, "give me the shipping zip", never
changed even though the internal path to answer that question did.

## 8. Implementation variants

**Straight Hide Delegate.** The most direct fix. add a method to the head
object that performs the full lookup internally and returns the target. This
is the canonical shape Fowler's catalog shows, `aPerson.department` and
`aPerson.manager` replacing `aPerson.department.manager`
(https://refactoring.com/catalog/hideDelegate.html, verified 2026-08-02). Use
this when the head object is the natural place for client code to ask the
question, and when only one or two delegate methods are needed.

**Delegate placed on the nearest owner, not always the head.** When the chain
is long, placing every delegate on the head object can turn the head into a
Large Class stuffed with forwarding methods for every possible downstream
field, which is this entry's sibling smell in a different shape. an
alternative is to add a delegate one hop at a time, so `Order` exposes
`getShippingAddress()` returning the `Address`, and `Address` itself exposes
`getZipCode()` as its own accessor, collapsing what was a three-hop chain into
a two-hop chain the client walks through one legitimate intermediate object it
actually needs, the address, rather than a stranger, the customer.

**Extract a query object or a specification.** When several different pieces
of client code each need a different derived fact from the same object graph,
adding one delegate method per fact can bloat the head object. an alternative
used in domain-driven designs is to introduce a small, purpose-built object
that is handed the head object once and exposes the several derived facts as
its own methods, so the coupling to the internal graph is concentrated in one
place, the query object, rather than spread as a growing list of forwarding
methods on the head object itself.

**Law of Demeter enforcement via static analysis, as a preventative variant
rather than a curative one.** Instead of fixing chains after the fact, teams
that want to prevent the smell from entering the codebase at all wire a
static check into their build. Apache PMD's `LawOfDemeter` rule is a direct
implementation of this. it flags a method call chained off the return value
of another method call, so a reviewer sees the violation at pull request time
rather than discovering it during a later refactor
(https://docs.pmd-code.org/latest/pmd_rules_java_design.html, verified
2026-08-02). This variant does not fix existing chains, it stops new ones from
being written.

**Formatting mitigation, not a structural fix.** Some teams choose to leave a
long chain in place but make it easier to read and to diff, by putting each
link on its own line. The formatting rule `newline-per-chained-call` began as
a core ESLint rule and now continues in the `@stylistic/eslint-plugin`
ecosystem (https://eslint.org/docs/latest/rules/, verified 2026-08-02, which
records the migration and confirms the rule still exists under that
successor package). This variant is worth naming precisely because it is
sometimes mistaken for a fix. formatting a chain across multiple lines makes
it easier to read at the point it is written, but it does nothing to reduce
the coupling described in dimension 3, and the same call sites still break
the same way when an intermediate class changes shape.

## 9. Known production uses

**Apache PMD's `LawOfDemeter` rule, under its Java Design ruleset.** PMD is a
widely deployed static analysis tool integrated into build pipelines across
the Java ecosystem, and it ships this rule specifically to detect chained
method calls that reach past a client's immediate collaborators
(https://docs.pmd-code.org/latest/pmd_rules_java_design.html, verified
2026-08-02). This is a direct, named, real-world implementation of automated
Message Chains detection, distinct from the manual code review process most
other smells rely on.

**ESLint's `newline-per-chained-call` rule and its successor in
`@stylistic/eslint-plugin`.** This is a real, shipped rule in one of the most
widely used JavaScript and TypeScript linting toolchains, and its existence
is direct evidence that long method chains are common enough in real
production JavaScript codebases to warrant a dedicated formatting rule
(https://eslint.org/docs/latest/rules/, verified 2026-08-02).

**Martin Fowler's refactoring catalog itself, `refactoring.com`, and its
worked Hide Delegate example.** The catalog is maintained as a public,
continuously referenced resource used across the software industry as the
canonical description of this exact refactoring, and its worked example,
`aPerson.department.manager` collapsing to `aPerson.manager`, is the same
shape this entry uses throughout
(https://refactoring.com/catalog/hideDelegate.html, verified 2026-08-02).

**JMock, named directly by Fowler as a deliberately designed fluent chain.**
JMock is cited here for the opposite reason from the first three entries. it
is a real, named library whose chained API is a deliberate fluent interface,
not an accidental Message Chains violation, and its existence is what makes
dimension 4's non-applicability list concrete rather than theoretical
(https://martinfowler.com/bliki/FluentInterface.html, verified 2026-08-02,
where Fowler writes "If you want a much more thought out example of a fluent
API take a look at JMock").

## 10. Consequences

**Positive, when the fix is applied.**

- The client's dependency surface shrinks from the whole chain of classes to
  the single head object, so a structural change anywhere else in the chain
  no longer requires editing the client.
- The decision about how to handle an absent intermediate object, for example
  a customer with no address on file, moves to one place, the delegate
  method, instead of being reinvented or forgotten at every call site.
- Tests that exercise the client's behavior need to construct or stub only
  the head object's delegate method, not the full graph of intermediate
  objects, which lowers test setup cost, discussed further in dimension 15.
- The intermediate classes are free to change their own internal shape,
  including replacing a single associated object with a collection or a
  different representation, without breaking any client that only ever asked
  the head object the higher-level question.

**Negative, when the fix is applied without judgement.**

- Adding a delegate method for every possible derived fact can turn the head
  object into a Large Class full of forwarding methods, trading one smell for
  another, discussed directly in dimension 11.
- An extra layer of indirection is added between the client and the target,
  which costs one additional method call at runtime, and one additional place
  a reader has to look to trace how the value is actually produced.
- If the delegate method is added mechanically without considering whether
  the head object is really the right owner of the question being asked, the
  fix can misplace responsibility just as badly as the original chain
  misplaced the lookup, particularly when the true answer belongs to neither
  end of the original chain but to a new concept the team has not yet named.

**Negative, when the chain is left in place.**

- Every call site that repeats the same multi-hop lookup is a place a future
  structural change must also be made, and a codebase with dozens of
  scattered chains through the same object graph turns what should be a
  one-line change into a multi-file, error-prone hunt.
- Null handling for intermediate steps is duplicated, or worse, inconsistently
  handled, at every call site, since nothing forces the two call sites that
  both walk `customer.address.zipCode` to treat a missing address the same
  way.

## 11. Failure modes and misuse

| Symptom | Cause | Fix |
|---|---|---|
| A change to how customers store their address, for example moving from a single address field to a list with a default flag, breaks compilation or silently returns wrong data in a dozen unrelated files. | Every one of those files walked `order.customer.address.zipCode` directly instead of asking the order for its shipping zip, so the internal representation of address leaked into every consumer of it. | Apply Hide Delegate on the head object each chain actually starts from, then update every call site to call the new delegate method instead of repeating the lookup, so the representation change is made in one place. |
| A `NullPointerException`, or its equivalent in another language, appears in production from a chain like `order.getCustomer().getAddress().getZipCode()` when a specific customer genuinely has no address on file yet. | The chain assumes every intermediate step is always present, and nothing at the call site, or anywhere else, decided what should happen for the legitimately empty case. | Move the lookup into a delegate method that makes an explicit, single decision about the missing case, for example returning an optional or a documented default, so every caller gets the same, deliberate behavior instead of an unhandled exception. |
| After a Hide Delegate refactor, the head object accumulates dozens of one-line forwarding methods, one for nearly every field reachable in the object graph, and the class becomes harder to work with than the chains it replaced. | The fix was applied mechanically to every chain found by a linter or a search, without asking whether the head object was really the natural place client code should be asking each of those questions. | Group related forwarding methods behind a single query object or specification, per dimension 8's third variant, rather than letting the head object absorb every derived fact anyone has ever asked it for. |
| A code reviewer flags a fluent builder call, for example a query builder chain like `query.where(x).orderBy(y).limit(z)`, as a Message Chains violation and asks the author to collapse it into one call. | The reviewer is pattern matching on the presence of chained dots rather than checking whether the chain crosses into unrelated objects' internals, which dimension 4's non-applicability list exists specifically to prevent. | Check whether each link in the chain returns the same kind of thing for the purpose of composing a small domain-specific language, as JMock and query builders do, rather than descending through unrelated collaborators, and if so, leave the chain exactly as written. |
| A static analysis rule like PMD's `LawOfDemeter` is enabled project-wide and immediately produces hundreds of findings on a legacy codebase, so the team disables the rule entirely rather than working through the backlog. | The rule was turned on globally with no baseline suppression for existing code, so genuinely new violations are drowned out by the pre-existing backlog and the signal becomes noise. | Enable the rule in an incremental or diff-only mode so it fires only on newly introduced chains, and work through the existing backlog separately and deliberately, the same triage pattern this entry's sibling, Feature Envy, recommends for its own detector false-positive problem. |

## 12. Trade-off matrix

| Force | Chain left as-is | Hide Delegate on head object | Delegate placed one hop at a time | Extract a query object |
|---|---|---|---|---|
| Coupling shape | Client depends on every class in the full path | Client depends on the head object alone | Client depends on the head and its immediate, legitimate collaborator | Client depends on the query object alone, which absorbs the graph knowledge |
| Risk of a bloated head class | None, no methods are added anywhere | Present if many unrelated facts are all forwarded through one class | Lower, forwarding is distributed one hop at a time across owning classes | Lowest for the head object, since the growth lands on the new query object instead |
| Null-handling consistency | Poor, each call site decides independently, or forgets to | Good, one place decides for that specific fact | Good for each hop's owner, but multiple decision points across the chain | Good, one place decides for every derived fact the query object exposes |
| Change locality when an intermediate class's shape changes | Poor, every call site that repeats the chain must be found and fixed | Good, only the delegate method's implementation changes | Moderate, the hop nearest the change must update, and possibly its caller | Good, only the query object's implementation changes |
| Appropriate for a deliberately designed fluent interface | Correct choice, this is not the smell described here | Wrong choice, destroys the intended readability of the fluent API | Wrong choice, same reason | Wrong choice, same reason |
| Test setup cost for client code | High, must construct or stub the full intermediate graph | Low, stub the one delegate method | Moderate, stub the one legitimate intermediate collaborator | Low, stub the query object's methods directly |

## 13. Related and incompatible patterns

**Feature Envy**, this family's sibling entry, and Message Chains are close
cousins that are sometimes confused with one another. Feature Envy is about a
method that reads mostly from one other object's data. Message Chains is
about a method that reads through several other objects in sequence to reach
a distant value. A long message chain often ends in a feature-envious read,
where the final call pulls raw data out of the target object rather than
asking it a question, and fixing the chain with Hide Delegate frequently also
resolves the feature envy at the same time, since the new delegate method now
lives next to the data it reads.

**Middle Man**, another sibling entry in this family, is the smell the Hide
Delegate fix can accidentally produce if it is applied too aggressively.
Remove Middle Man, the inverse refactoring on Fowler's catalog, is the tool
for undoing an over-applied Hide Delegate, when a class ends up doing nothing
but forwarding calls to another object it holds a reference to. The
relationship is direct. Hide Delegate resolves a Message Chain by introducing
forwarding, and Remove Middle Man is applied when that forwarding has itself
become excessive, so the two refactorings act as a pair a team cycles between
as a codebase evolves.

**Inappropriate Intimacy**, a further sibling entry, is closely related
because a message chain is frequently the visible symptom of two classes
that already know far too much about each other's internal structure. where
Inappropriate Intimacy describes the relationship between the classes
themselves, Message Chains describes the specific syntactic shape that
relationship produces at the call site of a third, unrelated client.

**Data Clumps**, another sibling entry, sometimes shows up alongside Message
Chains when the same group of fields, for example a street, a city, and a
zip code, are read together through the same chain at multiple call sites. In
that case introducing a small value object for the data clump, rather than or
in addition to a delegate method, can resolve both smells at once, since the
value object gives the group of fields a name and a single place to be read
from.

**Builder**, a creational pattern outside this family, is the primary source
of intentional chains that must not be mistaken for this smell. A builder's
entire purpose is a sequence of calls that each return the same builder
instance so a caller can compose a construction step by step. dimension 4's
first non-applicability entry and dimension 9's JMock citation both point at
this same distinction. this entry's fix, Hide Delegate, is never appropriate
against a genuine Builder chain, because collapsing it would remove the exact
readability the pattern was chosen to provide.

**Law of Demeter**, the underlying design principle rather than a pattern in
its own right, is what this smell is diagnosed against. Every dimension in
this entry that talks about coupling is really talking about adherence to, or
violation of, that principle, and the principle's own primary source
(https://www.ccs.neu.edu/home/lieber/LoD.html, verified 2026-08-02) is worth
reading directly for a reader who wants the rule stated in its original,
un-summarized form.

## 14. Refactoring path in and out

**Introducing the fix, step by step.**

1. Find the chain. search for a call expression with two or more chained
   accessor calls, either by eye during review or with a static tool like
   PMD's `LawOfDemeter` rule (https://docs.pmd-code.org/latest/pmd_rules_java_design.html,
   verified 2026-08-02), and confirm it is a genuine lookup-only chain rather
   than a deliberate fluent interface, per dimension 4.
2. Name the question the client is actually asking. not "give me the
   customer, then the address, then the zip code" but "what is the shipping
   zip code for this order". The name of the delegate method should read as
   that question's answer, for example `shippingZip()`, not as a description
   of the path taken to answer it.
3. Add the delegate method to the object that should own the answer, usually
   the head object the client already holds a reference to, and move the
   chain's exact lookup logic into that method's body.
4. Decide, once, inside the new delegate method, what happens when an
   intermediate step is legitimately absent, rather than leaving that
   decision unmade or duplicated across call sites.
5. Update every call site that repeated the original chain to call the new
   delegate method instead, verifying with a test per dimension 15 that the
   behavior at each call site is unchanged.
6. Once every call site has been migrated, consider whether the intermediate
   accessor that exposed the first hop of the old chain can be narrowed in
   visibility, since client code should no longer need to reach through it
   directly.

**Removing the fix, when it has been over-applied.**

1. Identify a head object whose only remaining methods are one-line
   forwarding calls to another object it holds a reference to, which is this
   entry's sibling smell, Middle Man.
2. Confirm that no client actually depends on the head object's own identity
   or behavior beyond that forwarding, only on the values the forwarding
   methods return.
3. Apply Remove Middle Man, the inverse refactoring listed on Fowler's
   catalog alongside Hide Delegate
   (https://refactoring.com/catalog/hideDelegate.html, verified 2026-08-02, by
   way of its stated inverse relationship), so clients call the delegate's
   underlying object directly again for that specific fact, restoring a short,
   deliberate chain in place of the excessive forwarding.
4. Re-check dimension 4's applicability list against the newly restored short
   chain, since removing a middle man is only correct when the resulting
   chain is short and stable, not when it reintroduces the original, longer
   lookup this entry exists to prevent.

## 15. Testing and verification

Testing code that still contains an unfixed message chain requires
constructing, or test-doubling, every intermediate object in the chain even
though the test's actual concern is only the final value or behavior. A test
for `order.getCustomer().getAddress().getZipCode()` needs a real or fake
`Customer` holding a real or fake `Address` holding the specific zip code
under test, which means the test is coupled to the shape of two classes it
does not conceptually care about. A refactor to any of those intermediate
classes' constructors then breaks tests that were never really testing that
class in the first place.

Testing code after Hide Delegate is applied is materially cheaper. a test
that exercises the client only needs to stub or fake the head object's
delegate method, `shippingZip()`, returning the value under test directly.
The intermediate classes, `Customer` and `Address`, no longer need to be
constructed at all for that test, which is precisely the setup-cost reduction
described in dimension 3's forces and dimension 10's positive consequences.

For the delegate method itself, a focused unit test on the head object should
cover the case where every intermediate step is present, and separately, the
case where an intermediate step is legitimately absent, since that is the
single decision point dimension 11's second failure mode calls out. a test
suite that only covers the happy path through the chain will not catch a
regression in how the code now handles a customer with no address on file.

Mock-object-heavy test suites are a useful early warning sign for this smell.
if setting up a mock or a fake for a single test requires stubbing three
levels of nested collaborators just to satisfy one chained call inside the
code under test, that is often the first place a developer notices the
underlying Message Chains problem, well before a static analysis tool or a
code reviewer flags it directly.

## 16. Observability signals

This smell is primarily a static, structural concern rather than a runtime
one, so the most direct observability signal is a static analysis finding
count rather than a production metric. Tracking the trend of a rule like
PMD's `LawOfDemeter` (https://docs.pmd-code.org/latest/pmd_rules_java_design.html,
verified 2026-08-02) across successive commits or releases shows whether new
message chains are accumulating faster than existing ones are fixed, the same
diff-scoped triage pattern discussed in dimension 11's fifth failure mode.

At runtime, the clearest indirect signal is a spike in null-pointer or
attribute-error exceptions whose stack trace originates from deep inside a
chained accessor expression rather than from a single, named method. a
delegate method that has centralized the null-handling decision produces a
single, identifiable line in a stack trace and, ideally, a single log message
naming the specific missing precondition, for example "order 4821 has no
address on file", rather than an anonymous null pointer exception three
frames deep in generated bytecode or in an unnamed lambda.

A slower-moving but useful signal is churn correlation. if a version control
history shows that every time a particular intermediate class's shape
changes, commits touch a wide, otherwise unrelated set of files across the
codebase, that pattern of correlated, cross-cutting churn is a strong
indirect indicator that many of those files were walking a chain through the
class that changed, rather than depending on a narrower, hidden interface.

## 17. Security and privacy implications

Message Chains does not open a distinct attack surface on its own, and this
entry states that plainly rather than inventing a concern where the primary
mechanism is structural coupling, not data exposure by itself. The indirect
implication worth naming is that a chain frequently exposes a wider surface
of an object's internal structure to client code than the object's author
intended, and in a codebase handling sensitive data, that wider surface can
mean client code far from the data's origin gains direct read access to
fields, such as a full postal address or a customer identifier, that a more
disciplined interface would have kept behind a narrower, purpose-specific
accessor. Hiding the delegate does not itself add access control, but it does
create the single choke point where an access check, an audit log entry, or a
redaction rule could later be added without having to find and modify every
scattered call site that previously walked the chain directly.

## 18. References

1. Martin Fowler, *Refactoring. Improving the Design of Existing Code*,
   Addison-Wesley, 1st edition, 1999, chapter "Bad Smells in Code", the smell
   Message Chains and its paired refactoring Hide Delegate. 2nd edition,
   Addison-Wesley, 2018, restructures the catalog but keeps the same smell and
   refactoring pairing.
2. Martin Fowler, Refactoring catalog, "Hide Delegate",
   https://refactoring.com/catalog/hideDelegate.html, verified 2026-08-02.
3. Martin Fowler, "CodeSmell", https://martinfowler.com/bliki/CodeSmell.html,
   verified 2026-08-02.
4. Martin Fowler, "FluentInterface",
   https://martinfowler.com/bliki/FluentInterface.html, verified 2026-08-02.
5. Ian Holland and Karl Lieberherr, Law of Demeter reference page, Northeastern
   University, https://www.ccs.neu.edu/home/lieber/LoD.html, verified
   2026-08-02.
6. Apache PMD, `LawOfDemeter` rule, Java Design ruleset,
   https://docs.pmd-code.org/latest/pmd_rules_java_design.html, verified
   2026-08-02.
7. ESLint, rules reference and the migration note for
   `newline-per-chained-call` into `@stylistic/eslint-plugin`,
   https://eslint.org/docs/latest/rules/, verified 2026-08-02.

## Code examples

Every sample models the same scenario. an `Order` holds a `Customer`, who
holds an `Address`, who holds a `zipCode`. The chained read is shown first,
followed by the head object's hidden delegate method that a client should
call instead. All four samples below were compiled or run directly against
the toolchain on this machine before this entry was written. Java was not
available in the local environment (`javac` resolves to the macOS stub with
no JDK installed) and is omitted for that reason, per this repository's
policy of never silently implying a sample was verified when it was not.

### TypeScript

```typescript
class Address {
  constructor(public zipCode: string) {}
}

class Customer {
  constructor(public address: Address) {}
}

class Order {
  constructor(private customer: Customer) {}

  // Hides the chain. clients ask the order, not the graph beneath it.
  shippingZip(): string {
    return this.customer.address.zipCode;
  }
}

const order = new Order(new Customer(new Address("94107")));

// Before, the message chain a client would otherwise repeat everywhere.
// order.getCustomer().getAddress().zipCode

console.log(order.shippingZip());
```

### Python

```python
class Address:
    def __init__(self, zip_code):
        self.zip_code = zip_code


class Customer:
    def __init__(self, address):
        self.address = address


class Order:
    def __init__(self, customer):
        self.customer = customer

    def shipping_zip(self):
        # Hides the chain. one place decides how to read a distant field.
        return self.customer.address.zip_code


order = Order(Customer(Address("94107")))

# Before, the chain a client would otherwise repeat at every call site.
# order.customer.address.zip_code

print(order.shipping_zip())
```

### Go

```go
package main

import "fmt"

type Address struct{ ZipCode string }
type Customer struct{ Address Address }
type Order struct{ Customer Customer }

// ShippingZip hides the chain behind one method on the head object.
func (o Order) ShippingZip() string {
	return o.Customer.Address.ZipCode
}

func main() {
	order := Order{Customer{Address{ZipCode: "94107"}}}

	// Before, the chain a client would otherwise repeat everywhere.
	// order.Customer.Address.ZipCode

	fmt.Println(order.ShippingZip())
}
```

### Rust

```rust
struct Address { zip_code: String }
struct Customer { address: Address }
struct Order { customer: Customer }

impl Order {
    // Hides the chain behind one method the client calls instead.
    fn shipping_zip(&self) -> &str {
        &self.customer.address.zip_code
    }
}

fn main() {
    let order = Order {
        customer: Customer {
            address: Address { zip_code: String::from("94107") },
        },
    };

    // Before, the chain a client would otherwise repeat everywhere.
    // order.customer.address.zip_code

    println!("{}", order.shipping_zip());
}
```
