---
name: Inheritance Mappers
slug: inheritance-mappers
family: 06-enterprise-application-architecture
category: Object-Relational Structural Patterns
aliases: [Mapper Hierarchy, Polymorphic Mapper]
first_described: "Fowler 2002"
maturity: canonical
related: [single-table-inheritance, class-table-inheritance, concrete-table-inheritance, data-mapper, template-method, identity-field, layer-supertype]
incompatible_with: []
verified: 2026-08-02
---

# Inheritance Mappers

## 1. Name, aliases, and lineage

The canonical name is Inheritance Mappers, catalogued by Martin Fowler in
*Patterns of Enterprise Application Architecture*, Addison-Wesley, 2002,
ISBN 0-321-12742-0, in the Object-Relational Structural Patterns group. The
online catalog entry states the intent in one sentence, "A structure to
organize database mappers that handle inheritance hierarchies" (Fowler,
*Patterns of Enterprise Application Architecture*, online catalog page,
https://martinfowler.com/eaaCatalog/inheritanceMappers.html verified
2026-08-02). The same page groups the pattern alongside its three siblings,
Single Table Inheritance, Class Table Inheritance, and Concrete Table
Inheritance, and its full worked example lives in Chapter 12 of the printed
book and in the O'Reilly online edition of the same text (Fowler,
*Patterns of Enterprise Application Architecture*, Chapter 12, "Object-
Relational Structural Patterns," Addison-Wesley, 2002).

The name is easy to confuse with its three siblings because all four patterns
answer the question "how does an object hierarchy meet a relational
database", and most engineering conversation collapses them into a single
topic, "ORM inheritance". They are not the same decision. Single Table,
Class Table, and Concrete Table Inheritance each answer a schema-shape
question, how many tables exist and how the columns are distributed across
them. Inheritance Mappers answers a code-shape question, how the mapper
classes that move rows into objects and back are organized once a schema
shape has been chosen. A team can pick any one of the three schema shapes
and still face the separate decision this pattern addresses, whether to
write one enormous mapper class that contains a branch for every subtype,
or a small hierarchy of mapper classes, one per domain class, each
responsible only for the fields introduced at that level.

No alias for this pattern is as entrenched as "STI" is for Single Table
Inheritance, because most teams reach for an ORM before they reach for a
hand-written mapper hierarchy and the ORM hides the decision entirely.
Where the term does surface outside Fowler's own text, it is usually as
**mapper hierarchy** or **polymorphic mapper**, both used descriptively
rather than as a fixed proper noun, for example in discussions of how an
object-relational mapping library resolves the concrete Python, Java, or
Ruby class for a loaded row (SQLAlchemy documentation, "Mapping Class
Inheritance Hierarchies," https://docs.sqlalchemy.org/en/20/orm/inheritance.html
verified 2026-08-02). This entry uses Inheritance Mappers throughout because
it is the name a reader will find if they go back to the primary source.

## 2. Problem and context

A domain model with an inheritance hierarchy, a base `Employee` class with
`SalariedEmployee`, `CommissionedEmployee`, and `HourlyEmployee` subclasses,
needs a persistence layer that can load any employee by identifier without
the caller knowing which concrete subtype the row represents, and that can
save any of the three subtypes without duplicating the logic that is common
to all employees. Data Mapper already solves the general shape of this
problem for a single class, one mapper object per persistent class,
responsible for translating between the in-memory object and the database
row (see the related Data Mapper entry). Inheritance introduces a second
question Data Mapper alone does not answer, whether that "one mapper per
persistent class" rule should hold for every level of a hierarchy or
collapse into one mapper that branches internally on type.

The naive first attempt is a single `EmployeeMapper` class with an `if` or
`switch` on a type field inside every method, `find`, `insert`, `update`,
and `delete` each carrying a branch per subtype. This compiles and runs, and
for a two-level, two-subtype hierarchy it is often the pragmatic choice
(dimension 4 covers exactly when it remains pragmatic). It degrades as the
hierarchy grows. Every method grows a new branch for every new subtype,
the branches interleave subtype-specific SQL fragments with the shared
identifier and audit-column handling that every subtype needs, and a
programmer adding a fourth subtype has to read and safely modify four
methods that were never designed with a fourth branch in mind. The
`Employee` example is small enough that this is survivable; a payroll,
billing, or claims system with a dozen employee, invoice-line, or claim
subtypes is not, because the branching mapper accretes the same
cyclomatic complexity that the domain model itself was refactored away
from by introducing the class hierarchy in the first place.

The context in which Inheritance Mappers becomes the right answer is
specifically this. A domain hierarchy exists, a Data Mapper style
persistence layer exists or is being introduced, and the number of
subtypes, or the rate at which subtypes are added, is large enough that a
single branching mapper class becomes a maintenance liability. The pattern
does not require a particular schema shape underneath. It has been applied
against Single Table, Class Table, and Concrete Table Inheritance layouts,
and the shape of the mapper hierarchy is nearly identical in all three
cases, only the SQL each concrete mapper generates differs.

## 3. Forces

**Code duplication versus indirection depth.** A single branching mapper
duplicates nothing structurally, everything lives in one file, but the
`if` chains inside each method duplicate the discriminator logic itself,
once per method. A mapper hierarchy removes that duplication by letting
each concrete mapper own exactly the fields and SQL fragments for its
level, at the cost of a reader now needing to open several files and
understand a template method call sequence to see the full behavior for
one subtype. This entry favors the hierarchy once the subtype count passes
roughly three to five, and treats the indirection cost as acceptable only
past that threshold, a judgement drawn from how quickly branching mappers
in payroll and billing systems become unreadable in practice rather than
from a source that states a number.

**Shared behavior versus per-subtype behavior.** Loading the identifier,
opening a connection, and running the base `SELECT` are identical for
every subtype. Loading the commission rate on a `CommissionedEmployee` is
not shared with anything. The pattern's central mechanism, an abstract
mapper base class implementing Template Method (Gamma, Helm, Johnson,
Vlissides, *Design Patterns*, Addison-Wesley, 1994, ISBN 0-201-63361-2,
pages 325 to 330) for the shared steps and delegating the per-subtype
steps to abstract hook methods, exists precisely to let both forces be
satisfied at once without either duplicating the shared logic or
cramming per-subtype logic into a shared method.

**Polymorphic finding versus static typing.** A caller that asks "give me
the employee with id 42" does not know in advance which concrete class
will come back, so something in the system has to resolve a discriminator
value to a concrete mapper class before the object can be constructed.
Every statically typed language in dimension 8's examples solves this
with some form of registry, a map from discriminator value to mapper
instance or mapper type, which is itself a small instance of Registry, and
which becomes the one place in the codebase a new subtype must be wired in.
A dynamically typed language can sometimes skip an explicit registry by
using the language's own type introspection, at the cost of losing the
one-file inventory of every registered subtype that an explicit registry
gives a reader for free.

**Schema-shape independence versus leaking that independence.** The
pattern is deliberately silent about whether the underlying tables use
Single Table, Class Table, or Concrete Table Inheritance, and that
silence is a genuine strength, the mapper hierarchy can be introduced or
kept stable while the schema shape underneath is changed. In practice the
independence leaks a little, a Class Table Inheritance schema needs each
concrete mapper's insert path to write to two tables inside one
transaction and needs the abstract mapper's find path to join rather than
filter, while a Concrete Table Inheritance schema needs each concrete
mapper to know its own table name outright with no shared base table at
all. The mapper hierarchy shape stays constant, the SQL each hook method
issues does not.

## 4. Applicability and non-applicability

Use Inheritance Mappers when a persistent class hierarchy has enough
subtypes, or grows subtypes often enough, that a single mapper's internal
branching has become, or is expected to become, the largest and most
frequently touched method in the mapping layer. Use it when different
subtypes genuinely need different SQL, different tables, or different
column sets, so that the per-subtype logic is substantial rather than a
single extra column. Use it when the team already has, or is willing to
introduce, a Data Mapper layer, since Inheritance Mappers is an extension
of that pattern's one-mapper-per-class rule to a hierarchy rather than a
persistence strategy on its own. Use it when polymorphic finding, loading
an object by identifier without the caller stating its concrete type in
advance, is a requirement rather than an edge case, because the pattern's
registry mechanism exists specifically to answer that requirement cleanly.

Do not use it under the following conditions, and treat each as a real
reason rather than a lesser variant of the pattern.

**The hierarchy has two levels and one subtype.** A base class with a
single subclass does not need a hierarchy of mapper classes, one plain
mapper with a single `if` is clearer than an abstract base and one
concrete subclass, and introducing the pattern here adds two files and a
registry entry to save nothing.

**An ORM already owns the mapping layer.** Hibernate, Doctrine, SQLAlchemy,
and Entity Framework each implement an internal mapper hierarchy for
exactly this problem (dimension 9), and hand-rolling a second one
alongside a mature ORM is either redundant work or, worse, a
misunderstanding of where the boundary between hand-written and generated
code should sit. The right move is to configure the ORM's own inheritance
mapping, not to write Inheritance Mappers by hand underneath it.

**The subtypes differ by a flag, not by structure.** A `SalariedEmployee`
that only differs from an `HourlyEmployee` by which of two columns is
populated, with no distinct behavior, is often better modelled as one
class with an optional field than as a class hierarchy at all. Introducing
Inheritance Mappers here is treating a data-shape difference as if it were
a behavioral difference, and the mapper hierarchy will not fix that
modelling mistake, it will encode it more elaborately.

**The hierarchy is read-heavy and the schema is Concrete Table
Inheritance with no shared base table.** A polymorphic `find` across
concrete tables that share no common table needs a `UNION` query or one
query per concrete type merged in application code, and dimension 11
covers the operational cost of that. When this cost dominates the access
pattern, a materialized reporting view or a search index built for
read-heavy polymorphic queries is frequently the better answer, with the
mapper hierarchy demoted to the write path only.

**A single team member owns the entire hierarchy and it changes rarely.**
The pattern's payoff is proportional to how often new subtypes are added
and how many people touch the mapping code. A hierarchy with three
subtypes that has not changed in two years and is maintained by one person
does not need the added ceremony; the branching mapper it already has is
not actively causing pain, and refactoring it purely for symmetry with
"the textbook shape" is churn without benefit.

## 5. Structure

**Domain hierarchy.** The persistent classes themselves, an abstract or
concrete base class and one or more subclasses, exactly as they exist in
the domain model independent of persistence.

**Abstract Mapper.** One class per level of the domain hierarchy that
introduces new persistent state, implementing the operations common to
every subtype, opening a connection, running the identifier lookup,
coordinating the transaction, as concrete methods, and declaring the
operations that differ per subtype, translating the subtype's own fields
to and from a row, as abstract hook methods following Template Method.
This is a Layer Supertype for the mapper hierarchy specifically (see the
related Layer Supertype entry), distinct from any Layer Supertype the
domain classes themselves might share.

**Concrete Mappers.** One class per concrete, instantiable domain class,
subclassing the Abstract Mapper and implementing only the hook methods for
the fields introduced at that level. A concrete mapper never re-implements
the shared connection or transaction handling; it inherits that from the
abstract mapper and supplies only what is unique to its own subtype.

**Mapper Registry or Factory.** A lookup, keyed by a discriminator value
read from the row, or by the runtime type of an in-memory object being
saved, that resolves the correct concrete mapper. This is the mechanism
that answers dimension 3's polymorphic-finding force, and it is the one
piece of the structure that must be updated whenever a subtype is added
or removed.

**Client.** Code that asks for an employee, a shape, or a claim by
identifier, or hands a domain object to be saved, without needing to know
or state the concrete subtype in advance. The client interacts with the
registry or with the base mapper's public entry points and never
constructs a concrete mapper directly.

## 6. ASCII structure diagram

```
+---------------------+
|      Client         |
+----------+-----------+
           | find(id) / insert(obj)
           v
+----------------------------+
|     MapperRegistry         |
|  discriminator -> mapper   |
+-------------+---------------+
              |
              v
+----------------------------------------+
|         AbstractEmployeeMapper         |  <-- Template Method base
|  + find(id)            [concrete]      |
|  + insert(employee)    [concrete]      |
|  # loadCommonFields()  [concrete]      |
|  # insertCommonRow()   [concrete]      |
|  # loadSubclassFields()  [abstract]    |
|  # insertSubclassRow()   [abstract]    |
+-------------------+---------------------+
                    ^  ^  ^
      +-------------+  |  +-------------+
      |                |                |
+-----------------+ +---------------------+ +------------------+
| SalariedMapper  | | CommissionedMapper   | | HourlyMapper     |
| loadSubclass..  | | loadSubclass..       | | loadSubclass..   |
| insertSubclass..| | insertSubclass..     | | insertSubclass.. |
+-----------------+ +---------------------+ +------------------+
      |                       |                       |
      v                       v                       v
+-----------------+ +---------------------+ +------------------+
| salaried table   | | commissioned table  | | hourly table     |
| (or shared row   | | (or shared row      | | (or shared row   |
|  in STI schema)  | |  in STI schema)      | |  in STI schema)  |
+-----------------+ +---------------------+ +------------------+
```

## 7. Dynamics

The two operations that matter are a polymorphic find by identifier and an
insert of a new domain object, and each follows the same template method
shape in reverse.

**Find by identifier, discriminator known only at runtime.**

```
Client -> MapperRegistry.mapperFor(id)
MapperRegistry -> AbstractEmployeeMapper.readDiscriminator(id)
    reads only the base row, or the base row's discriminator column
AbstractEmployeeMapper --> MapperRegistry: discriminator value "commissioned"
MapperRegistry -> ConcreteMapper lookup by discriminator
MapperRegistry --> Client: CommissionedEmployeeMapper instance
Client -> CommissionedEmployeeMapper.find(id)
CommissionedEmployeeMapper -> AbstractEmployeeMapper.find(id)  [inherited]
    AbstractEmployeeMapper -> DB: SELECT common columns WHERE id = ?
    AbstractEmployeeMapper -> self.loadSubclassFields(row, commonFields)
        [dispatches to CommissionedEmployeeMapper's override]
    CommissionedEmployeeMapper -> DB: SELECT commission_rate WHERE id = ?
        (Class Table Inheritance shape; a join or extra column read in
         Single Table Inheritance; a full row in Concrete Table
         Inheritance)
    CommissionedEmployeeMapper --> AbstractEmployeeMapper: fully built object
AbstractEmployeeMapper --> Client: CommissionedEmployee instance
```

**Insert of a new domain object, subtype known statically at the call
site.**

```
Client -> MapperRegistry.mapperForClass(employee.getClass())
MapperRegistry --> Client: matching concrete mapper
Client -> ConcreteMapper.insert(employee)
ConcreteMapper -> AbstractEmployeeMapper.insert(employee)  [inherited]
    AbstractEmployeeMapper -> DB: INSERT common columns, get generated id
    AbstractEmployeeMapper -> self.insertSubclassRow(employee, id)
        [dispatches to the concrete mapper's override]
    ConcreteMapper -> DB: INSERT subtype-specific columns / row
AbstractEmployeeMapper --> Client: assigned identifier
```

Two details matter and are easy to get wrong when implementing this from
the diagram alone. First, the abstract mapper's `find` and `insert` are
the methods a client calls, and they are template methods, not the
override points; the override points, `loadSubclassFields` and
`insertSubclassRow`, are protected or package-private and are never
called directly by a client. Second, resolving which concrete mapper to
use happens exactly once per operation, at the registry, and the concrete
mapper it returns is then trusted for the remainder of that operation; the
abstract mapper does not re-check the discriminator mid-operation, which
is what makes the dynamic dispatch inside `find` and `insert` correct
without a second lookup.

## 8. Implementation variants

**Template Method with a shared abstract base, one concrete mapper per
persistent class.** This is the textbook shape, shown in full in the code
examples below, and is the right default in Java, C#, TypeScript, or any
language with single-implementation inheritance for classes. The abstract
mapper implements `find` and `insert` as template methods and declares
`loadSubclassFields` and `insertSubclassRow` as abstract hooks. Every
concrete class in the domain hierarchy that is directly instantiable gets
exactly one concrete mapper.

**Composition over inheritance in languages without class inheritance.**
Go has no implementation inheritance for structs. The equivalent shape
embeds a shared base struct, or holds a reference to shared mapping
helpers, inside each concrete mapper, and expresses the template method
relationship as an interface the base logic calls back into rather than
as an overridden method. The code example below shows this concretely.
The resulting shape is behaviorally identical to the class-based version,
an abstract dispatch point plus concrete implementations, achieved through
composition and an interface instead of subclassing.

**Discriminator-driven registry, resolved once at startup.** The most
common registry shape is a `Map<String, Mapper>` or an equivalent
dictionary built once when the application starts, keyed by the exact
discriminator value stored in the database. This is the shape used in the
code examples. It requires every new subtype to add one registry entry,
which is a deliberate design property, not an oversight, because it makes
the full inventory of subtypes visible in one place rather than scattered
across a codebase relying on reflection or dynamic class loading.

**Reflection-driven registry, resolved from a naming convention.** Some
implementations avoid the explicit registry entirely by deriving the
concrete mapper class name from the discriminator value through a naming
convention, for example a discriminator of `commissioned` resolving to a
class literally named `CommissionedEmployeeMapper` via reflection or
dynamic import. Ruby on Rails's Single Table Inheritance support resolves
the concrete domain class this way, from the `type` column value directly
to a Ruby constant of the same name (Ruby on Rails API documentation,
`ActiveRecord::Inheritance`,
https://api.rubyonrails.org/classes/ActiveRecord/Inheritance.html verified
2026-08-02). This trades the registry's one-file inventory for less
boilerplate, and fails at runtime with a class-not-found error rather than
at compile time or at registry-build time when a discriminator value and a
class name drift apart, for example after a rename that forgot to update
stored data.

**ORM-internal inheritance mappers, hidden behind configuration.**
Hibernate's persistence layer implements this pattern internally as its
mechanism for supporting all three inheritance schema strategies from one
configuration surface. `AbstractEntityPersister` supplies the shared
persistence mechanics, and `SingleTableEntityPersister`,
`JoinedSubclassEntityPersister`, and `UnionSubclassEntityPersister` are its
three direct known subclasses, one per schema strategy (Hibernate ORM
Javadoc, `AbstractEntityPersister`,
https://docs.hibernate.org/orm/6.2/javadocs/org/hibernate/persister/entity/AbstractEntityPersister.html
verified 2026-08-02). SQLAlchemy's `Mapper` class exposes the same idea
directly as public API, an `inherits` parameter that links a subclass's
`Mapper` to its parent's `Mapper`, and a `polymorphic_identity` that plays
the discriminator role (SQLAlchemy API documentation, "Mapping API,"
https://docs.sqlalchemy.org/en/20/orm/mapping_api.html verified
2026-08-02). A team that adopts either ORM is, whether the term is used or
not, configuring an instance of Inheritance Mappers rather than writing
one from scratch, and dimension 4 already names this as the reason to
prefer configuration over a hand-written hierarchy once a mature ORM is in
the stack.

**Flattened hook methods for a shallow hierarchy.** When a hierarchy is
exactly two levels deep with a small, fixed number of subtypes, some
implementations skip a separate abstract mapper class and instead give
each concrete mapper a shared static or module-level helper function for
the common steps, called explicitly rather than through inheritance. This
keeps the file count down for a hierarchy unlikely to grow, at the cost
of losing the compiler-enforced guarantee that every concrete mapper
implements every required hook, which the abstract base class's abstract
methods provide for free.

## 9. Known production uses

**Hibernate's entity persister hierarchy.** `AbstractEntityPersister`
implements the mechanics common to persisting any entity via JDBC, and its
three direct known subclasses, `SingleTableEntityPersister`,
`JoinedSubclassEntityPersister`, and `UnionSubclassEntityPersister`,
supply the SQL generation specific to each of the three inheritance
strategies Hibernate supports (Hibernate ORM Javadoc,
`AbstractEntityPersister`,
https://docs.hibernate.org/orm/6.2/javadocs/org/hibernate/persister/entity/AbstractEntityPersister.html
verified 2026-08-02). This is Inheritance Mappers used at the framework
level to let one configuration annotation, `@Inheritance`, switch schema
strategy while the object-loading contract callers depend on stays fixed.

**SQLAlchemy's Mapper class with the `inherits` and `polymorphic_identity`
parameters.** Every mapped class in SQLAlchemy's ORM gets its own `Mapper`
instance, and a subclass's `Mapper` is explicitly linked to its parent's
`Mapper` through the `inherits` configuration parameter, with
`polymorphic_identity` supplying the discriminator value SQLAlchemy uses
to resolve which mapper, and therefore which Python class, applies to a
loaded row (SQLAlchemy API documentation, "Mapping API,"
https://docs.sqlalchemy.org/en/20/orm/mapping_api.html verified
2026-08-02; SQLAlchemy documentation, "Mapping Class Inheritance
Hierarchies,"
https://docs.sqlalchemy.org/en/20/orm/inheritance.html verified
2026-08-02). The `Mapper` hierarchy SQLAlchemy builds internally mirrors
the Python class hierarchy one for one, exactly the structural
relationship this pattern names.

**Doctrine ORM's mapped superclasses and discriminator-driven class
resolution.** Doctrine documents a mapped superclass as "an abstract or
concrete class that provides persistent entity state and mapping
information for its subclasses, but which is not itself an entity," and
resolves the concrete entity class for a loaded row through a
`DiscriminatorColumn` and `DiscriminatorMap` pair configured on the root
entity (Doctrine ORM documentation, "Inheritance Mapping,"
https://www.doctrine-project.org/projects/doctrine-orm/en/3.6/reference/inheritance-mapping.html
verified 2026-08-02). Doctrine's internal `ClassMetadata` objects, one
per entity class in a hierarchy, play the same structural role the
concrete mappers play in this pattern, each carrying only the mapping
information introduced at its own level.

**Ruby on Rails ActiveRecord's Single Table Inheritance class
resolution.** Rails resolves the Ruby class to instantiate for a loaded
row directly from the value stored in the `type` column, using the stored
string as a class name looked up through Ruby's own constant resolution
rather than through an explicit registry object (Ruby on Rails API
documentation, `ActiveRecord::Inheritance`,
https://api.rubyonrails.org/classes/ActiveRecord/Inheritance.html verified
2026-08-02). This is the reflection-driven registry variant from
dimension 8, and it is the production system most engineers encounter
this pattern through without ever seeing the term Inheritance Mappers
used explicitly.

## 10. Consequences

Positive.

- Each mapper class carries only the mapping logic for the fields
  introduced at its own level of the domain hierarchy, so adding a new
  subtype means adding a new class rather than editing every existing
  mapping method to add a branch.
- The shared connection, transaction, and identifier-handling logic lives
  in exactly one place, the abstract mapper, so a bug fix or a
  cross-cutting change, adding a soft-delete flag to every load, needs
  one edit rather than one edit per subtype.
- The schema shape underneath, Single Table, Class Table, or Concrete
  Table Inheritance, can change without changing the mapper hierarchy's
  public shape, because the schema-specific work is isolated inside the
  concrete hook method implementations.
- Polymorphic finding is expressed once, in the registry and the
  abstract mapper's `find`, rather than reimplemented per subtype, which
  removes an entire class of copy-paste bugs where one subtype's find
  path forgets a filter the others apply.

Negative.

- The number of classes grows linearly with the number of subtypes, one
  concrete mapper plus one domain class per subtype, which for a large
  hierarchy is a real increase in file count and navigation cost compared
  to a single branching mapper.
- The registry becomes a second place, alongside the domain class
  hierarchy itself, that must be kept in sync whenever a subtype is
  added, removed, or renamed; a registry entry that drifts from the
  stored discriminator value fails at runtime, often on the read path for
  data that predates the drift.
- Debugging a load or save requires following a call through the
  abstract mapper's template method into whichever concrete mapper the
  registry resolved, which is one more hop than a single branching mapper
  with an inline `if` at the point a debugger would already be sitting.
- In languages without single-implementation class inheritance, the
  pattern's shared-base-class mechanism has to be re-expressed through
  composition and an interface, which is a genuine implementation cost
  the textbook Java or C# shape does not carry.

## 11. Failure modes and misuse

**Symptom.** A newly added subtype loads correctly by identifier but never
appears in polymorphic queries that return a mixed list of employees.
**Cause.** The concrete mapper class was written and the domain subclass
was added, but the discriminator-to-mapper registry entry was never
added, or a batch-loading query that predates the new subtype still
enumerates only the discriminator values it knew about at the time it was
written. **Fix.** Make the registry the single source of truth any
batch-loading or list query iterates over, rather than letting a separate
hand-maintained list of discriminator values exist in a second location,
and add a test that asserts every concrete domain class has a
corresponding registry entry, which turns a silent omission into a
build-time failure.

**Symptom.** Two engineers add subtypes in parallel feature branches, both
choosing the discriminator value `"contract"` for what turn out to be two
different concepts, and the merge conflict in the registry file is
resolved by keeping one branch's entry and silently dropping the other's.
**Cause.** The discriminator value space has no enforced uniqueness check
outside the registry itself, so the collision is invisible until the
dropped subtype's rows fail to resolve to any mapper at read time.
**Fix.** Enforce uniqueness of discriminator values at the schema level, a
`CHECK` constraint or an enumerated column type where the database
supports one, or at minimum a startup-time assertion that the registry's
key set has no duplicates, so the collision surfaces at deploy time rather
than the first time an affected row is read in production.

**Symptom.** The abstract mapper's `find` method is edited to add a new
step, for example populating an audit-log entry on every load, and every
concrete mapper's tests start failing because the new step assumes a
field that only some subtypes populate. **Cause.** The abstract mapper is
being treated as a place to add subtype-specific logic conditionally,
which reintroduces the branching-on-type problem the pattern exists to
remove, just moved from a single mapper class into the shared base class
instead of into a concrete mapper. **Fix.** Any logic that only applies to
some subtypes belongs in the relevant concrete mapper's hook method
override, never in the abstract mapper's template method body; if several
but not all subtypes need the same additional step, introduce an
intermediate abstract mapper for exactly that subset rather than adding a
conditional to the top-level abstract mapper.

**Symptom.** A polymorphic find across a Concrete Table Inheritance schema
with no shared base table becomes measurably slower as new subtypes are
added, even though each individual concrete mapper's own query is fast.
**Cause.** The registry-driven polymorphic find is implemented as one
query per concrete mapper, executed sequentially and merged in
application code, so total latency grows linearly with the subtype count
rather than staying flat, which is an inherent cost of Concrete Table
Inheritance rather than a defect in the mapper hierarchy itself.
**Fix.** Either issue the per-subtype queries concurrently rather than
sequentially, which bounds latency by the slowest single query instead of
their sum, or, if polymorphic reads dominate the access pattern, move the
schema decision from Concrete Table Inheritance to Class Table or Single
Table Inheritance, where a polymorphic find is a single query against a
shared base table, and keep the mapper hierarchy's shape unchanged while
only the concrete mappers' internals are rewritten.

**Symptom.** A concrete mapper's `insertSubclassRow` writes its row before
the abstract mapper's `insertCommonRow` has committed the base row's
generated identifier, and the subtype-specific row ends up referencing a
stale or null foreign key. **Cause.** The template method's step ordering
was changed, or a concrete mapper was implemented to call the database
directly rather than through the identifier the abstract mapper's insert
step already generated and passed down, breaking the sequencing the
Template Method pattern depends on. **Fix.** The abstract mapper's insert
template method must generate and commit, or at minimum flush within the
same transaction, the base identifier before invoking
`insertSubclassRow`, and must pass that identifier explicitly as a
parameter to the hook method rather than relying on the concrete mapper
to re-fetch it, so the ordering dependency is enforced by the method
signature rather than by convention.

## 12. Trade-off matrix

| Concern | Inheritance Mappers | Single branching mapper | ORM-managed inheritance (Hibernate style) |
|---|---|---|---|
| Adding a new subtype | New class plus one registry entry | Edit every existing method's branch logic | Add an entity class plus one annotation |
| Code locality for one subtype's logic | One concrete mapper file | Scattered across every branching method | Scattered across annotations and generated SQL |
| Shared cross-cutting changes | One edit in the abstract mapper | One edit, but interleaved with branch logic | One edit in framework configuration, if the framework exposes a hook |
| Compile-time enforcement of complete coverage | Yes, via abstract methods | No, a missed branch fails silently at runtime | Partially, depends on the framework's validation |
| Learning curve for a new engineer | Must learn the mapper hierarchy and registry | Must read one file, but that file grows unbounded | Must learn the framework's inheritance configuration surface |
| Runtime debugging hop count | One extra hop through the registry and template method | Zero extra hops | One or more hops through framework internals, often opaque |
| Schema-shape independence | High, hook methods isolate schema specifics | Low, schema specifics interleave with everything else | High, but only within what the framework supports |
| Appropriate hierarchy size | Roughly three or more subtypes, or a growing count | One or two subtypes, stable count | Any size, once the team has adopted the framework |

## 13. Related and incompatible patterns

**Single Table Inheritance, Class Table Inheritance, Concrete Table
Inheritance.** These three patterns decide the schema shape underneath;
Inheritance Mappers decides the mapper class shape on top. They compose
with any one of the three, which is why this entry's
`incompatible_with` list is empty. Choosing Inheritance Mappers does not
rule out any schema-shape choice, and choosing a schema shape does not
determine whether the mapper code above it is one branching class or a
hierarchy.

**Data Mapper.** Inheritance Mappers is Data Mapper's one-mapper-per-class
rule extended across an entire hierarchy rather than applied to a single
class. A codebase that has not adopted Data Mapper at all, for example one
using Active Record, does not have a natural place to introduce
Inheritance Mappers, because Active Record's premise is that each object
knows how to persist itself rather than delegating to a separate mapper
object (see the related Active Record entry).

**Template Method.** The abstract mapper's `find` and `insert` methods are
a direct application of the GoF Template Method pattern (Gamma, Helm,
Johnson, Vlissides, *Design Patterns*, Addison-Wesley, 1994, ISBN
0-201-63361-2, pages 325 to 330). Inheritance Mappers is, structurally,
Template Method applied specifically to the persistence layer of a domain
hierarchy, with the registry added on top to resolve which subclass's
overrides apply to a given row.

**Layer Supertype.** The abstract mapper functions as a Layer Supertype
for the mapping layer, the same relationship Fowler's Layer Supertype
pattern names for a shared base class across a layer of an application,
here scoped narrowly to the mappers rather than to the domain classes
themselves.

**Identity Field.** Every mapper in the hierarchy, abstract and concrete
alike, relies on Identity Field to have already established how a
domain object's database identifier is stored and compared, since the
registry's discriminator lookup and the abstract mapper's `find` both key
off that identifier.

**Metadata Mapping.** An alternative to hand-writing an inheritance
mapper hierarchy is to describe the hierarchy's mapping declaratively and
let a generic engine interpret that metadata at runtime, which is the
approach SQLAlchemy's and Doctrine's configuration surfaces expose to
application code even though the frameworks implement Inheritance Mappers
internally underneath that metadata layer.

## 14. Refactoring path in and out

Refactoring into the pattern from a single branching mapper follows the
Extract Subclass style of refactoring, applied to the mapper rather than
to the domain class, in a sequence that keeps the system working at every
step.

1. Introduce an abstract mapper class that extends the existing branching
   mapper's public interface exactly, with every existing method still
   implemented on the original class, so no caller notices a change yet.
2. Pick the subtype with the smallest branch in the existing mapper's
   methods, and extract a concrete mapper subclass for it, moving only
   that subtype's branch logic into an override of a newly introduced
   hook method, leaving every other subtype's branch in place on the
   base class for now.
3. Add the corresponding registry entry, pointing that subtype's
   discriminator value at the new concrete mapper, and add or run tests
   that exercise find and insert for that one subtype specifically before
   moving on.
4. Repeat step 2 and step 3 for the remaining subtypes, one at a time,
   verifying the existing test suite stays green after each extraction,
   until the original branching methods on the base class contain no
   subtype-specific logic left.
5. Turn the remaining base-class methods, now free of branches, into
   proper Template Method implementations with explicit abstract hook
   declarations, so the compiler enforces that every concrete mapper
   implements what it needs, and delete the now-empty branch scaffolding.

Refactoring out of the pattern, back toward a single mapper or toward
adopting an ORM's built-in inheritance support, follows the reverse
sequence and is warranted when dimension 4's non-applicability conditions
start to hold, most often when the team introduces a mature ORM and the
hand-written hierarchy becomes redundant with the framework's own.

1. Confirm the target, either collapsing back to one branching mapper
   because the subtype count has shrunk, or migrating to an ORM's
   configuration-driven inheritance mapping because the framework now
   owns the mapping layer.
2. If migrating to an ORM, configure the framework's inheritance mapping
   for one subtype at a time, running both the hand-written concrete
   mapper and the framework's mapping in parallel against the same table
   in a staging environment, and compare loaded objects field for field
   before removing the hand-written mapper for that subtype.
3. If collapsing back to a single mapper, work in the opposite order from
   the introduction sequence, folding one concrete mapper's hook method
   bodies back into a branch on the base class at a time, keeping the
   registry in place until every subtype has been folded so that
   in-flight code paths still resolve correctly during the migration.
4. Remove the registry and the abstract mapper only after every subtype
   has been migrated, never partway through, because a registry with
   some entries pointing at removed concrete mappers is a defect waiting
   to be hit by the next find call for that discriminator value.

## 15. Testing and verification

What the pattern makes easy to test is exactly what its structure
isolates, each concrete mapper's own field mapping can be tested in
isolation, with a real or in-memory table populated for that one subtype
only, and the assertion checks that the loaded object has the correct
concrete type and the correct subtype-specific field values. This is a
narrower, faster test than one that has to set up rows for every subtype
just to exercise one branch of a single mapper class, because the
concrete mapper under test has no dependency on any sibling mapper's
schema.

The abstract mapper's shared logic, connection handling, transaction
boundaries, and the template method sequencing itself, deserves its own
test suite written once against a minimal concrete subclass created
specifically for the test, often called a test double subtype, rather
than against one of the real domain subtypes, so that a change to a real
subtype's fields never has to touch the abstract mapper's own tests.

What becomes harder to test is the registry's completeness, since a
missing registry entry is a runtime failure rather than a compile-time
one in most of the languages this pattern is implemented in. The
mitigation is a single test, run once per test suite execution, that
enumerates every concrete domain class reachable via reflection or an
explicit registry-independent list, and asserts the registry has an
entry for each one; this converts the failure mode from dimension 11's
first symptom into a build-time check rather than a production surprise.

Polymorphic find behavior across the whole hierarchy is best tested with
one integration-style test that inserts one instance of every subtype,
issues a single polymorphic find across all of them, and asserts both
that every instance came back and that each came back as the correct
concrete class; this is the one test in the suite that genuinely exercises
the registry, the abstract mapper's dispatch, and every concrete mapper
together, and it is the test most likely to catch an integration mistake
that per-mapper unit tests, by design, cannot see.

## 16. Observability signals

Log or emit a metric on every registry miss, an attempt to resolve a
discriminator value with no matching concrete mapper, at error severity
rather than silently returning null or throwing an unhandled exception,
because a registry miss almost always means either corrupted data or a
mapper that failed to register at startup, and either cause needs a human
looking at it quickly rather than surfacing only as a downstream null
pointer error several call frames away from the actual cause.

Emit a counter, tagged by discriminator value, for every successful find
and every insert routed through the abstract mapper's template methods.
A healthy system shows a distribution across discriminator values that
roughly matches the known proportion of subtypes in the domain, a
payroll system with far more `SalariedEmployee` rows than
`CommissionedEmployee` rows should show that same skew in its find and
insert counters; a sudden shift in that distribution, or a discriminator
value that stops appearing entirely, is a signal worth investigating
before it becomes a support ticket.

Trace the time spent inside the abstract mapper's shared steps
separately from the time spent inside each concrete mapper's hook method
overrides, using a span or timer boundary at the template method's call
into the hook method. This separation answers, without guessing, whether
a slow find or insert is a shared-infrastructure problem, a slow
connection pool, a slow transaction commit, affecting every subtype
uniformly, or a specific concrete mapper's own query that has grown slow,
which is the single most useful piece of information for triaging a
latency regression in a mapper hierarchy of any real size.

For a polymorphic find implemented as multiple queries merged in
application code, per dimension 11's fourth failure mode, instrument the
per-subtype query count and the merge step's own duration as distinct
measurements, since the two failure modes, "one subtype's query is slow"
and "the merge itself is slow because of how many subtypes there are",
require different fixes and are otherwise invisible inside a single
combined latency number.

## 17. Security and privacy implications

The registry is a discriminator-to-mapper lookup driven by a value stored
in the database, and if that discriminator value is ever taken from user
input directly rather than from a value already validated on write, an
attacker who can influence the discriminator column could attempt to
force resolution to an unintended concrete mapper. In every production
system reviewed for dimension 9, the discriminator value is written once
at insert time by trusted application code and treated as read-only data
thereafter, never re-derived from a request parameter at read time, and
that write-once discipline is the actual control that prevents this
class of confusion; the pattern itself carries no built-in defense
against a discriminator value that is allowed to be attacker-controlled.

Each concrete mapper owns exactly the columns for its own subtype, which
is a genuine privacy benefit over a single branching mapper. A
`SalariedEmployee`'s mapper has no code path that ever touches a
`CommissionedEmployee`'s commission-rate column, so a bug in one
subtype's mapping logic cannot accidentally read or leak a field that
belongs to a different subtype the way a single mapper's shared row
buffer sometimes can when a branch is written carelessly.

Audit logging, when required across an entire hierarchy, for example
recording who read or modified any employee record regardless of
subtype, is best implemented as one step inside the abstract mapper's
template method rather than duplicated inside every concrete mapper,
both because it guarantees no subtype is accidentally exempted from the
audit trail and because it keeps the audit logic in the one place a
compliance reviewer needs to inspect rather than scattered across every
concrete mapper file.

Where different subtypes carry different sensitivity levels, for
example a `CommissionedEmployee`'s bank routing details for commission
payouts versus an `HourlyEmployee`'s timesheet data, the mapper
hierarchy is a convenient place to apply subtype-specific field
redaction or encryption-at-rest handling inside that subtype's own
concrete mapper, rather than adding a conditional to a shared method
that redacts fields it should never have needed to know existed.

## 18. References

1. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002, ISBN 0-321-12742-0, Chapter 12, "Object-Relational
   Structural Patterns."
2. Fowler, "Inheritance Mappers," online catalog page,
   https://martinfowler.com/eaaCatalog/inheritanceMappers.html verified
   2026-08-02.
3. Fowler, "Single Table Inheritance," online catalog page,
   https://martinfowler.com/eaaCatalog/singleTableInheritance.html verified
   2026-08-02.
4. Gamma, Helm, Johnson, Vlissides, *Design Patterns, Elements of Reusable
   Object-Oriented Software*, Addison-Wesley, 1994, ISBN 0-201-63361-2,
   "Template Method," pages 325 to 330.
5. Hibernate ORM Javadoc, `AbstractEntityPersister`,
   https://docs.hibernate.org/orm/6.2/javadocs/org/hibernate/persister/entity/AbstractEntityPersister.html
   verified 2026-08-02.
6. Hibernate ORM User Guide, section 3.14, "Entity inheritance," MappedSuperclass,
   https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html#entity-inheritance
   verified 2026-08-02.
7. SQLAlchemy documentation, "Mapping Class Inheritance Hierarchies,"
   https://docs.sqlalchemy.org/en/20/orm/inheritance.html verified
   2026-08-02.
8. SQLAlchemy API documentation, "Mapping API," `Mapper.inherits` and
   `Mapper.polymorphic_identity`,
   https://docs.sqlalchemy.org/en/20/orm/mapping_api.html verified
   2026-08-02.
9. Doctrine ORM documentation, "Inheritance Mapping,"
   https://www.doctrine-project.org/projects/doctrine-orm/en/3.6/reference/inheritance-mapping.html
   verified 2026-08-02.
10. Ruby on Rails API documentation, `ActiveRecord::Inheritance`,
    https://api.rubyonrails.org/classes/ActiveRecord/Inheritance.html
    verified 2026-08-02.
11. Baeldung, "Hibernate Inheritance Mapping,"
    https://www.baeldung.com/hibernate-inheritance verified 2026-08-02.

## Code examples

The three examples below implement the same domain, a `SalariedEmployee`,
a `CommissionedEmployee`, and an `HourlyEmployee` sharing a base
`Employee`, against an in-memory table structure that mirrors a Class
Table Inheritance schema, one base table plus one table per concrete
subtype, so the examples run with no database dependency. Java is omitted
because no JDK was available in this environment at write time; the
shape in Java is the closest of the four to the ASCII diagram in
dimension 6 and follows the TypeScript example almost line for line,
substituting `abstract class` and `protected abstract` for TypeScript's
equivalent keywords.

### TypeScript

```typescript
abstract class Employee {
  constructor(public readonly id: number, public readonly name: string) {}
}

class SalariedEmployee extends Employee {
  constructor(id: number, name: string, public readonly annualSalary: number) {
    super(id, name);
  }
}

class CommissionedEmployee extends Employee {
  constructor(id: number, name: string, public readonly commissionRate: number) {
    super(id, name);
  }
}

class HourlyEmployee extends Employee {
  constructor(id: number, name: string, public readonly hourlyRate: number) {
    super(id, name);
  }
}

interface BaseRow {
  id: number;
  name: string;
  type: string;
}

const baseTable = new Map<number, BaseRow>();
const salariedTable = new Map<number, { annualSalary: number }>();
const commissionedTable = new Map<number, { commissionRate: number }>();
const hourlyTable = new Map<number, { hourlyRate: number }>();
let nextId = 1;

abstract class AbstractEmployeeMapper<T extends Employee> {
  abstract readonly discriminator: string;

  protected abstract loadSubclassFields(id: number, base: BaseRow): T;
  protected abstract insertSubclassRow(id: number, employee: T): void;

  find(id: number): T {
    const base = baseTable.get(id);
    if (!base) throw new Error(`no employee with id ${id}`);
    if (base.type !== this.discriminator) {
      throw new Error(`mapper for ${this.discriminator} cannot load a ${base.type} row`);
    }
    return this.loadSubclassFields(id, base);
  }

  insert(employee: T): number {
    const id = nextId++;
    baseTable.set(id, { id, name: employee.name, type: this.discriminator });
    (employee as { id: number }).id = id;
    this.insertSubclassRow(id, employee);
    return id;
  }
}

class SalariedEmployeeMapper extends AbstractEmployeeMapper<SalariedEmployee> {
  readonly discriminator = "salaried";

  protected loadSubclassFields(id: number, base: BaseRow): SalariedEmployee {
    const row = salariedTable.get(id);
    if (!row) throw new Error(`salaried row missing for id ${id}`);
    return new SalariedEmployee(id, base.name, row.annualSalary);
  }

  protected insertSubclassRow(id: number, employee: SalariedEmployee): void {
    salariedTable.set(id, { annualSalary: employee.annualSalary });
  }
}

class CommissionedEmployeeMapper extends AbstractEmployeeMapper<CommissionedEmployee> {
  readonly discriminator = "commissioned";

  protected loadSubclassFields(id: number, base: BaseRow): CommissionedEmployee {
    const row = commissionedTable.get(id);
    if (!row) throw new Error(`commissioned row missing for id ${id}`);
    return new CommissionedEmployee(id, base.name, row.commissionRate);
  }

  protected insertSubclassRow(id: number, employee: CommissionedEmployee): void {
    commissionedTable.set(id, { commissionRate: employee.commissionRate });
  }
}

class HourlyEmployeeMapper extends AbstractEmployeeMapper<HourlyEmployee> {
  readonly discriminator = "hourly";

  protected loadSubclassFields(id: number, base: BaseRow): HourlyEmployee {
    const row = hourlyTable.get(id);
    if (!row) throw new Error(`hourly row missing for id ${id}`);
    return new HourlyEmployee(id, base.name, row.hourlyRate);
  }

  protected insertSubclassRow(id: number, employee: HourlyEmployee): void {
    hourlyTable.set(id, { hourlyRate: employee.hourlyRate });
  }
}

class MapperRegistry {
  private readonly byDiscriminator = new Map<string, AbstractEmployeeMapper<Employee>>();

  register(mapper: AbstractEmployeeMapper<Employee>): void {
    this.byDiscriminator.set(mapper.discriminator, mapper);
  }

  find(id: number): Employee {
    const base = baseTable.get(id);
    if (!base) throw new Error(`no employee with id ${id}`);
    const mapper = this.byDiscriminator.get(base.type);
    if (!mapper) throw new Error(`no mapper registered for type ${base.type}`);
    return mapper.find(id);
  }
}

const registry = new MapperRegistry();
registry.register(new SalariedEmployeeMapper());
registry.register(new CommissionedEmployeeMapper());
registry.register(new HourlyEmployeeMapper());

const salariedMapper = new SalariedEmployeeMapper();
const commissionedMapper = new CommissionedEmployeeMapper();
const salariedId = salariedMapper.insert(new SalariedEmployee(0, "Aisha", 82000));
const commissionedId = commissionedMapper.insert(
  new CommissionedEmployee(0, "Devon", 0.08),
);

const loadedSalaried = registry.find(salariedId);
const loadedCommissioned = registry.find(commissionedId);
console.log(loadedSalaried instanceof SalariedEmployee, loadedSalaried);
console.log(loadedCommissioned instanceof CommissionedEmployee, loadedCommissioned);
```

### Python

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Employee:
    id: int
    name: str


@dataclass
class SalariedEmployee(Employee):
    annual_salary: float


@dataclass
class CommissionedEmployee(Employee):
    commission_rate: float


@dataclass
class HourlyEmployee(Employee):
    hourly_rate: float


base_table: dict[int, dict] = {}
salaried_table: dict[int, dict] = {}
commissioned_table: dict[int, dict] = {}
hourly_table: dict[int, dict] = {}
_next_id = [1]


class AbstractEmployeeMapper(ABC):
    discriminator: str

    @abstractmethod
    def load_subclass_fields(self, employee_id: int, base_row: dict) -> Employee:
        raise NotImplementedError

    @abstractmethod
    def insert_subclass_row(self, employee_id: int, employee: Employee) -> None:
        raise NotImplementedError

    def find(self, employee_id: int) -> Employee:
        base_row = base_table.get(employee_id)
        if base_row is None:
            raise KeyError(f"no employee with id {employee_id}")
        if base_row["type"] != self.discriminator:
            raise ValueError(
                f"mapper for {self.discriminator} cannot load a "
                f"{base_row['type']} row"
            )
        return self.load_subclass_fields(employee_id, base_row)

    def insert(self, employee: Employee) -> int:
        employee_id = _next_id[0]
        _next_id[0] += 1
        base_table[employee_id] = {"name": employee.name, "type": self.discriminator}
        employee.id = employee_id
        self.insert_subclass_row(employee_id, employee)
        return employee_id


class SalariedEmployeeMapper(AbstractEmployeeMapper):
    discriminator = "salaried"

    def load_subclass_fields(self, employee_id: int, base_row: dict) -> SalariedEmployee:
        row = salaried_table[employee_id]
        return SalariedEmployee(employee_id, base_row["name"], row["annual_salary"])

    def insert_subclass_row(self, employee_id: int, employee: Employee) -> None:
        assert isinstance(employee, SalariedEmployee)
        salaried_table[employee_id] = {"annual_salary": employee.annual_salary}


class CommissionedEmployeeMapper(AbstractEmployeeMapper):
    discriminator = "commissioned"

    def load_subclass_fields(self, employee_id: int, base_row: dict) -> CommissionedEmployee:
        row = commissioned_table[employee_id]
        return CommissionedEmployee(employee_id, base_row["name"], row["commission_rate"])

    def insert_subclass_row(self, employee_id: int, employee: Employee) -> None:
        assert isinstance(employee, CommissionedEmployee)
        commissioned_table[employee_id] = {"commission_rate": employee.commission_rate}


class HourlyEmployeeMapper(AbstractEmployeeMapper):
    discriminator = "hourly"

    def load_subclass_fields(self, employee_id: int, base_row: dict) -> HourlyEmployee:
        row = hourly_table[employee_id]
        return HourlyEmployee(employee_id, base_row["name"], row["hourly_rate"])

    def insert_subclass_row(self, employee_id: int, employee: Employee) -> None:
        assert isinstance(employee, HourlyEmployee)
        hourly_table[employee_id] = {"hourly_rate": employee.hourly_rate}


class MapperRegistry:
    def __init__(self) -> None:
        self._by_discriminator: dict[str, AbstractEmployeeMapper] = {}

    def register(self, mapper: AbstractEmployeeMapper) -> None:
        self._by_discriminator[mapper.discriminator] = mapper

    def find(self, employee_id: int) -> Employee:
        base_row = base_table.get(employee_id)
        if base_row is None:
            raise KeyError(f"no employee with id {employee_id}")
        mapper = self._by_discriminator.get(base_row["type"])
        if mapper is None:
            raise ValueError(f"no mapper registered for type {base_row['type']}")
        return mapper.find(employee_id)


if __name__ == "__main__":
    registry = MapperRegistry()
    registry.register(SalariedEmployeeMapper())
    registry.register(CommissionedEmployeeMapper())
    registry.register(HourlyEmployeeMapper())

    salaried_id = SalariedEmployeeMapper().insert(SalariedEmployee(0, "Aisha", 82000.0))
    commissioned_id = CommissionedEmployeeMapper().insert(
        CommissionedEmployee(0, "Devon", 0.08)
    )

    loaded_salaried = registry.find(salaried_id)
    loaded_commissioned = registry.find(commissioned_id)
    print(type(loaded_salaried).__name__, loaded_salaried)
    print(type(loaded_commissioned).__name__, loaded_commissioned)
```

### Go

Go has no implementation inheritance for structs, so the abstract
mapper's shared logic is expressed as a set of free functions the
concrete mapper types call into, and the hook methods are expressed as an
interface, `subclassOps`, that each concrete mapper implements. The
dispatch shape, shared steps calling into type-specific overrides, is the
same as the class-based examples; only the mechanism, an interface value
instead of a subclassed method, differs.

```go
package main

import "fmt"

type Employee interface {
	EmployeeID() int
	EmployeeName() string
}

type BaseEmployee struct {
	ID   int
	Name string
}

func (b BaseEmployee) EmployeeID() int      { return b.ID }
func (b BaseEmployee) EmployeeName() string { return b.Name }

type SalariedEmployee struct {
	BaseEmployee
	AnnualSalary float64
}

type CommissionedEmployee struct {
	BaseEmployee
	CommissionRate float64
}

type HourlyEmployee struct {
	BaseEmployee
	HourlyRate float64
}

type baseRow struct {
	name string
	kind string
}

var (
	baseTable         = map[int]baseRow{}
	salariedTable     = map[int]float64{}
	commissionedTable = map[int]float64{}
	hourlyTable       = map[int]float64{}
	nextID            = 1
)

// subclassOps is the hook interface every concrete mapper implements.
// It plays the role of the abstract methods in the class-based examples.
type subclassOps interface {
	discriminator() string
	loadSubclassFields(id int, base baseRow) Employee
	insertSubclassRow(id int, employee Employee)
}

// abstractFind and abstractInsert are the shared Template Method steps,
// expressed as free functions since Go has no shared base class to hold them.
func abstractFind(id int, ops subclassOps) (Employee, error) {
	base, ok := baseTable[id]
	if !ok {
		return nil, fmt.Errorf("no employee with id %d", id)
	}
	if base.kind != ops.discriminator() {
		return nil, fmt.Errorf("mapper for %s cannot load a %s row", ops.discriminator(), base.kind)
	}
	return ops.loadSubclassFields(id, base), nil
}

func abstractInsert(employee Employee, discriminator string, ops subclassOps) int {
	id := nextID
	nextID++
	baseTable[id] = baseRow{name: employee.EmployeeName(), kind: discriminator}
	ops.insertSubclassRow(id, employee)
	return id
}

type salariedMapper struct{}

func (salariedMapper) discriminator() string { return "salaried" }

func (salariedMapper) loadSubclassFields(id int, base baseRow) Employee {
	return SalariedEmployee{
		BaseEmployee: BaseEmployee{ID: id, Name: base.name},
		AnnualSalary: salariedTable[id],
	}
}

func (salariedMapper) insertSubclassRow(id int, employee Employee) {
	salariedTable[id] = employee.(SalariedEmployee).AnnualSalary
}

func (m salariedMapper) find(id int) (SalariedEmployee, error) {
	e, err := abstractFind(id, m)
	if err != nil {
		return SalariedEmployee{}, err
	}
	return e.(SalariedEmployee), nil
}

func (m salariedMapper) insert(e SalariedEmployee) int {
	return abstractInsert(e, m.discriminator(), m)
}

type commissionedMapper struct{}

func (commissionedMapper) discriminator() string { return "commissioned" }

func (commissionedMapper) loadSubclassFields(id int, base baseRow) Employee {
	return CommissionedEmployee{
		BaseEmployee:   BaseEmployee{ID: id, Name: base.name},
		CommissionRate: commissionedTable[id],
	}
}

func (commissionedMapper) insertSubclassRow(id int, employee Employee) {
	commissionedTable[id] = employee.(CommissionedEmployee).CommissionRate
}

func (m commissionedMapper) find(id int) (CommissionedEmployee, error) {
	e, err := abstractFind(id, m)
	if err != nil {
		return CommissionedEmployee{}, err
	}
	return e.(CommissionedEmployee), nil
}

func (m commissionedMapper) insert(e CommissionedEmployee) int {
	return abstractInsert(e, m.discriminator(), m)
}

type mapperRegistry struct {
	byDiscriminator map[string]subclassOps
}

func newMapperRegistry() *mapperRegistry {
	r := &mapperRegistry{byDiscriminator: map[string]subclassOps{}}
	r.byDiscriminator["salaried"] = salariedMapper{}
	r.byDiscriminator["commissioned"] = commissionedMapper{}
	return r
}

func (r *mapperRegistry) find(id int) (Employee, error) {
	base, ok := baseTable[id]
	if !ok {
		return nil, fmt.Errorf("no employee with id %d", id)
	}
	ops, ok := r.byDiscriminator[base.kind]
	if !ok {
		return nil, fmt.Errorf("no mapper registered for type %s", base.kind)
	}
	return abstractFind(id, ops)
}

func main() {
	var sm salariedMapper
	var cm commissionedMapper

	salariedID := sm.insert(SalariedEmployee{
		BaseEmployee: BaseEmployee{Name: "Aisha"},
		AnnualSalary: 82000,
	})
	commissionedID := cm.insert(CommissionedEmployee{
		BaseEmployee:   BaseEmployee{Name: "Devon"},
		CommissionRate: 0.08,
	})

	registry := newMapperRegistry()

	loadedSalaried, err := registry.find(salariedID)
	if err != nil {
		panic(err)
	}
	loadedCommissioned, err := registry.find(commissionedID)
	if err != nil {
		panic(err)
	}
	fmt.Printf("%T %+v\n", loadedSalaried, loadedSalaried)
	fmt.Printf("%T %+v\n", loadedCommissioned, loadedCommissioned)
}
```
