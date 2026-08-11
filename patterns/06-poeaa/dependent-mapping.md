---
name: Dependent Mapping
slug: dependent-mapping
family: 06-poeaa
category: Object-Relational Structural
aliases: [Owned Entity Mapping, Privately Owned Association]
first_described: "Fowler 2003"
maturity: canonical
related: [data-mapper, identity-field, foreign-key-mapping, embedded-value, serialized-lob, unit-of-work]
incompatible_with: []
verified: 2026-08-02
---

# Dependent Mapping

## 1. Name, aliases, and lineage

The canonical name is Dependent Mapping. It is one of the ten Object-Relational Structural Patterns catalogued in Martin Fowler, *Patterns of Enterprise Application Architecture*, Addison-Wesley, 2003, chapter 12, in the section titled "Dependent Mapping." The book states the intent in one line, "Has one class perform the database mapping for a child class" (<https://martinfowler.com/eaaCatalog/dependentMapping.html>, verified 2026-08-02, the online catalog entry mirroring the book text). Fowler builds the pattern around a worked example of an Album that owns a list of Track objects, where the AlbumMapper, not a TrackMapper, is responsible for every piece of SQL that reads or writes a track row.

The name in the catalog is a noun phrase describing a relationship between two mapping responsibilities, not a class or interface a reader will find declared anywhere. This is worth stating plainly because a reader coming from the Gang of Four catalog expects a pattern name to correspond to a participant class, a Factory, a Visitor, a Decorator. Dependent Mapping corresponds to no such class. It names a decision about which mapper owns which persistence responsibility, and the code that results looks like an ordinary mapper class with a wider job.

Two aliases are in use in the wild rather than in the book itself. **Owned Entity Mapping** is the phrase that shows up in object-relational mapping tooling documentation for the equivalent mechanism, because those tools describe the child as an entity the parent "owns" rather than as a dependent of a mapper. **Privately Owned Association** is Doctrine ORM's own term for the same idea, used in its documentation when describing the `orphanRemoval` option on a `OneToMany` association (<https://www.doctrine-project.org/projects/doctrine-orm/en/latest/reference/working-with-associations.html>, verified 2026-08-02). Neither alias is Fowler's own wording, and this entry treats them as pointers to the same catalog pattern under a tool's local vocabulary rather than as separate patterns.

The pattern sits inside the Data Mapper family that Fowler describes earlier in the same book, chapter 10 (<https://martinfowler.com/eaaCatalog/dataMapper.html>, verified 2026-08-02, cited for the chapter number). Data Mapper says nothing about how many mapper classes an application should have. Dependent Mapping is the specific answer to the question of what to do when a naive one-mapper-per-domain-class rule would produce a mapper for a class that has no independent meaning outside another object, and it is this narrowing of scope, rather than a new mechanism, that earns it a separate catalog entry.

## 2. Problem and context

Data Mapper separates the in-memory domain model from the database schema by giving each persistent class a mapper responsible for moving its state to and from rows. Applied literally and uniformly, that rule produces one mapper class per domain class, each with its own find, insert, update and delete methods, and, for classes that need one, its own Identity Field.

Some domain classes exist only inside the context of another object. A `Track` never appears on its own in the application's domain model, it is always a member of an `Album`'s track list. An `OrderLine` is always a line on an `Order`. An `Address` is often only meaningful attached to a `Contact` or a `Customer`. In each case, no part of the application ever asks the persistence layer "load me track number 42" independently of its album, and no other row in the database ever refers to the track by its own identity. The child is part of the parent's data, arranged in a separate table only because the parent has a variable-length collection of them, which a single row with a fixed set of columns cannot represent.

Giving that kind of class a full independent mapper is not wrong in the sense that the code will not work. It is wasteful and it creates a place for bugs to hide. A `TrackMapper` with its own find, insert, update and delete methods implies that a track can be looked up, saved and deleted on its own, when nothing in the domain wants that. Once that mapper exists, two code paths can touch the same row, the `AlbumMapper` when it saves the whole album, and the `TrackMapper` when some other part of the code reaches for a track directly. Keeping those two paths consistent, especially under concurrent writes, becomes an ongoing tax that the domain never asked for.

Dependent Mapping names the alternative. Collapse the child's persistence responsibility into the parent's mapper. The `AlbumMapper` gains the job of loading, inserting, updating and deleting track rows as a side effect of loading, inserting, updating and deleting the album itself. There is exactly one place in the codebase, the album mapper, where SQL against the tracks table is written, and the domain's `Track` class carries no persistence knowledge and, usually, no database-visible identity of its own.

The problem the pattern solves, restated precisely. An application built with Data Mapper has more domain classes than it needs independent mappers for, and the excess mappers cost more in duplicated boilerplate, inconsistent write paths and accidental independent access than they return in structural uniformity.

## 3. Forces

**Simplicity of the mapper inventory against uniformity of design.** A mapper-per-class rule is simple to explain and simple to generate. Dependent Mapping breaks that uniformity on purpose, in exchange for fewer classes that exist only to satisfy the rule rather than a real requirement. The judgement call is where that exchange stops paying off, a parent with a dozen kinds of dependent, each with its own reconciliation logic folded into one mapper, can recreate the "god class" problem the uniform rule was avoiding, only moved one level up.

**Encapsulation of the aggregate boundary against future flexibility.** Removing the child's independent mapper is a structural way of saying "this object is not addressable from outside its parent," which the compiler and the schema then help enforce. That same removal is exactly the cost incurred if a later requirement needs to reference the child from elsewhere, the whole mapping has to be reworked, not merely extended.

**Transactional simplicity against write volume.** Because the owner mapper issues all writes for both the owner and its dependents inside one call, it is natural to keep the owner and every dependent inside a single database transaction, which removes an entire class of partial-write bugs that a separate child mapper would need external coordination to avoid. The most direct implementation of that simplicity, deleting every dependent row and reinserting the current set on every save, pays for the safety with I/O that scales with the size of the collection regardless of how much actually changed. This is a judgement about typical implementations, not a property forced by the pattern itself, a diff-based save avoids the cost at the price of more code in the owner mapper.

**Query flexibility against collection size.** A dependent with no mapper of its own has no dedicated finder either. If a requirement appears to query dependents directly, filter them across owners, or page through a very large collection without loading the whole thing, Dependent Mapping is the wrong tool for that dependent, because its central promise, that the dependent is loaded and saved only as part of its owner, is precisely what blocks independent querying.

**Identity cost against referential need.** A dependent mapped this way usually needs no domain-visible Identity Field, because nothing outside the owner ever needs to name it. Skipping Identity Field removes real bookkeeping, generated key round trips, and object-identity-map entries for the child. The saving disappears the moment something external does need to reference the dependent, which then requires introducing an identity the design had deliberately avoided.

**Cognitive load against mapper size.** Reviewing an owner's mapper shows a reader everything about how that aggregate is persisted, including its dependents, in one file. That same concentration is a liability once the owner mapper accumulates the persistence logic for several kinds of dependent, each with different reconciliation rules, the single file that used to be easy to read becomes the file nobody wants to touch.

## 4. Applicability and non-applicability

Reach for Dependent Mapping when the following hold together.

- The child object has no identity that matters outside its parent. Two tracks with the same title and duration on two different albums are, from the domain's point of view, unrelated facts that happen to look alike, not the same object referenced twice.
- The child is always loaded and saved together with its parent. No part of the application ever asks for a child on its own, by its own key, outside the context of loading the parent.
- The child's entire lifecycle is owned by the parent. It is created when attached to the parent, and removed when detached from the parent or when the parent itself is removed. There is no scenario where a child outlives its parent in the domain's rules.
- The parent-to-child relationship is a simple composition, a has-many or a has-one, not a reference shared with, or pointed at by, some other aggregate.
- The child collection is bounded to a size the application is comfortable loading in full alongside the parent on every read. A handful to a few hundred rows is typical, an unbounded, ever-growing collection is not, and is addressed under non-applicability below.

Do not reach for Dependent Mapping, and use Foreign Key Mapping or a first-class mapper for the child instead, when any of the following hold.

- **The child is, or might soon be, referenced by more than one parent, or by a table outside the aggregate.** Dependent Mapping assumes exclusive private ownership, the moment a second reference exists, deleting the "owning" parent's row would orphan or corrupt the second reference, because the pattern's delete step assumes it is the only writer of that row's lifecycle.
- **The child collection is large or must be paged or filtered independently.** Dependent Mapping typically loads the entire collection whenever the parent is loaded. A collection with tens of thousands of rows, or one that a screen needs to page through ten at a time, defeats that assumption and belongs to a pattern that supports querying the child directly, most often Foreign Key Mapping paired with its own finder.
- **The child carries real domain behavior and invariants that deserve independent testing, reuse, or a first-class repository of their own.** Folding such a class into the owner's mapper to save a small amount of mapper boilerplate can smuggle a genuine Entity into behaving like a Value Object at the persistence layer, which then has to be undone once the behavior grows.
- **Writers of the child need independent transactional concurrency.** If many transactions update different children of the same parent at the same time and those updates should not contend with each other, routing every write through the owner's row, and, in the naive strategy, through a delete-and-reinsert of the whole collection, manufactures lock contention the domain does not actually require.
- **The persistence layer is not built on the Data Mapper family at all.** A system built on the Active Record pattern, in Fowler's specific sense of an object that carries its own persistence methods, does not have a separate mapper class to assign this responsibility to. The underlying idea of parent-owned child persistence still shows up there, for example in Ruby on Rails' `accepts_nested_attributes_for` mechanism described in dimension 9, but it is implemented as a feature of Active Record rather than as literal Dependent Mapping.

## 5. Structure

- **Owner.** The parent domain object, for example `Album`. Holds a collection of Dependent instances as an ordinary in-memory field and knows nothing about how that collection reaches the database.
- **Owner Mapper.** The single mapper class, for example `AlbumMapper`, responsible for every database operation touching both the owner's own columns and every Dependent's rows. It is the only participant with SQL or query-building knowledge for either table.
- **Dependent.** The child domain object, for example `Track`. A plain domain object with no reference to any mapper, no database connection, and typically no field the domain treats as a database primary key. If the underlying table has a technical primary key for the database's own bookkeeping, that key is private to the Owner Mapper and never exposed on the Dependent's public interface.
- **Dependent Table.** The relational table holding one row per Dependent instance, carrying a foreign key back to the Owner's identity, for example `tracks.album_id`. Nothing outside the Owner Mapper issues SQL against this table.
- **Identity Field, on the Owner only.** The Owner typically carries an Identity Field, in Fowler's sense from chapter 10 of the same book, used both to identify the owner row and to serve as the foreign key value the Owner Mapper writes into every Dependent row it inserts.

The relationship between these participants is asymmetric by design. The Owner Mapper depends on both the Owner's and the Dependent's shape. The Dependent depends on nothing in the persistence layer at all. No participant outside the Owner Mapper is permitted to depend on the Dependent Table.

## 6. ASCII structure diagram

```
+-----------------------+          +----------------------+
|         Album         |  1     * |         Track        |
|-----------------------|<>--------|----------------------|
| - id AlbumId          |          | - title string       |
| - title string        |          | - seconds int         |
| - tracks Track array  |          |  (no persistence      |
+-----------------------+          |   knowledge at all)   |
                                    +----------------------+

          owns and mediates all persistence for
                          |
                          v
+---------------------------------------------------------+
|                      AlbumMapper                        |
|-----------------------------------------------------------|
| + find(id) -> Album or null                              |
| + insert(album Album) -> void                             |
| + update(album Album) -> void                             |
| + delete(id) -> void                                     |
|-----------------------------------------------------------|
| - loadTracks(albumId)      # SELECT ... FROM tracks       |
| - insertTracks(album)      # INSERT ... INTO tracks       |
| - deleteTracksFor(albumId) # DELETE ... FROM tracks       |
+---------------------------------------------------------+
        |                                       |
        v                                       v
+------------------+                    +--------------------+
|   albums table     |                    |    tracks table    |
|--------------------|                    |---------------------|
| id, PK              |                    | id, PK, private     |
| title               |                    | album_id, FK        |
+------------------+                    | title                |
                                          | seconds               |
                                          +--------------------+

No TrackMapper exists. No code path outside AlbumMapper reads or
writes the tracks table.
```

## 7. Dynamics

Loading an owner and its dependents together, the delete-and-reinsert save variant, and deleting an owner, are the three sequences that matter.

```
CLIENT              ALBUM MAPPER              ALBUMS TABLE     TRACKS TABLE
  |  find(albumId)       |                          |                |
  |---------------------->  SELECT * FROM albums    |                |
  |                       |  WHERE id = albumId ---->                |
  |                       |<---------- row ----------                |
  |                       |  SELECT * FROM tracks                    |
  |                       |  WHERE album_id = albumId ---------------->
  |                       |<---------------------- rows --------------
  |                       |  reconstitute Album, attach Track array  |
  |<------- Album --------|                          |                |

  |  update(album)        |                          |                |
  |---------------------->  UPDATE albums SET ...    |                |
  |                       |  WHERE id = album.id ---->                |
  |                       |  DELETE FROM tracks                      |
  |                       |  WHERE album_id = album.id --------------->
  |                       |  for each track in album.tracks          |
  |                       |    INSERT INTO tracks (...) -------------->
  |<------- done ---------|      (all inside one transaction)         |

  |  delete(albumId)      |                          |                |
  |---------------------->  DELETE FROM tracks                       |
  |                       |  WHERE album_id = albumId ----------------->
  |                       |  DELETE FROM albums                      |
  |                       |  WHERE id = albumId ------>                |
  |<------- done ---------|                          |                |
```

Two properties of this sequence carry the pattern's contract. First, the owner mapper never returns control to the caller between the owner-row operation and the dependent-rows operation, both happen inside the same call, normally wrapped in the same transaction by a surrounding Unit of Work, because a caller who saw the owner committed but the dependents not yet written would observe an inconsistent aggregate. Second, the delete step for dependents in the update sequence removes every existing dependent row for that owner before reinserting the current set, which is the simplest correct strategy and also the one whose cost dimension 8 and dimension 11 discuss in depth.

## 8. Implementation variants

**Delete all and reinsert.** On every update, the owner mapper deletes every existing dependent row for the owner and reinserts the current in-memory collection. This is the baseline Fowler describes for the pattern's worked example, chosen for its simplicity. There is no need to compare the old collection against the new one, and there is no risk of a stale row surviving an update by accident. The cost is that a single-field change on one dependent among a hundred still issues a hundred deletes and a hundred inserts.

**Diff-based reconciliation.** The owner mapper compares the dependent rows already in the database against the in-memory collection by a stable key, commonly the private technical id read back at load time, and issues only the inserts, updates and deletes the difference actually requires. This is more code inside the owner mapper, and it needs the private key to be preserved on the loaded objects so the mapper can tell "this is track row 17, edited" from "this is a brand new track." Mature ORM implementations of the pattern, discussed in dimension 9, perform this diff automatically through dirty checking rather than asking the application author to hand-write it.

**Two separate selects versus one joined select.** The load sequence in dimension 7 shows two round trips, one for the owner row and one for the dependent rows filtered by foreign key. An alternative issues a single SQL statement that joins the owner table to the dependent table, at the cost of the owner's own columns repeating once per dependent row in the result set, which the mapper must then de-duplicate while reconstituting the owner. The two-select variant is simpler to reason about and is the one shown in the code examples below, the single joined select removes a round trip and matters more as the number of owners loaded in one request grows, at which point dimension 11's batching fix generally dominates either single-owner variant.

**Embedding the dependents as a serialized blob instead of a child table.** When the collection of dependents is complex, deeply nested, or not worth querying at the SQL level under any circumstance, some mappers give up on a relational child table entirely and store the whole graph as JSON or another serialized form in a single column of the owner's row. This is not Dependent Mapping proper, it is Fowler's sibling pattern Serialized LOB (<https://martinfowler.com/eaaCatalog/serializedLOB.html>, verified 2026-08-02). The boundary between the two is worth stating precisely because implementations drift across it without anyone deciding to. Dependent Mapping keeps the dependents as real rows the owner mapper can still filter, join, or report against with ordinary SQL if it ever needs to, Serialized LOB gives up that ability entirely in exchange for a single write.

**Framework-automated variants.** Jakarta Persistence's `orphanRemoval` element on a `OneToMany` or `OneToOne` association, implemented by Hibernate and other providers, has the persistence provider generate exactly the delete-and-reconcile logic an owner mapper would hand-write, driven by annotations rather than SQL the application author writes. Doctrine ORM offers the equivalent through `orphanRemoval=true` combined with `cascade=["persist"]`. Ruby on Rails' Active Record offers `accepts_nested_attributes_for` with `:autosave`, which persists and destroys nested child records as part of saving the parent inside one transaction. Each of these is the same idea Fowler describes, expressed as a configuration surface rather than as a hand-written mapper class, and dimension 9 cites each with a source.

## 9. Known production uses

- **Jakarta Persistence 3.1 Specification, Section 2.10, "Entity Relationships."** The `orphanRemoval` element on `@OneToOne` and `@OneToMany` is specified so that "if an entity that is the target of the relationship is removed from the relationship (by setting the relationship to null or removing the entity from the relationship collection), the remove operation will be applied to the entity being orphaned" (<https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1.html>, verified 2026-08-02). The specification explicitly scopes this feature to entities that are privately owned by their parent, which is the same scoping condition dimension 4 lists for Dependent Mapping. Hibernate and EclipseLink both implement this section of the specification and are the two most widely deployed Jakarta Persistence providers.
- **Doctrine ORM, PHP, "Working with Associations" reference documentation.** The documentation instructs that `orphanRemoval=true` should be used together with `cascade=["persist"]` on a `OneToMany` mapping and illustrates the technique with an Order-and-OrderItems example, stating that this configuration suits "domain objects like Orders with OrderItems, scenarios where child entities have no independent existence apart from their parent" (<https://www.doctrine-project.org/projects/doctrine-orm/en/latest/reference/working-with-associations.html>, verified 2026-08-02). This is a direct, named production description of Dependent Mapping's applicability condition from dimension 4, expressed in a different ORM's own vocabulary.
- **Ruby on Rails, Active Record `accepts_nested_attributes_for`.** The Rails API documentation states that "all changes to models, including the destruction of those marked for destruction, are saved and destroyed automatically and atomically when the parent model is saved" (<https://api.rubyonrails.org/classes/ActiveRecord/NestedAttributes/ClassMethods.html>, verified 2026-08-02), and that enabling the `:allow_destroy` option permits a nested child record to be removed through the parent's own save call using the `_destroy` key. Rails is built on the Active Record pattern rather than Data Mapper, so there is no separate mapper class for this feature to occupy, but the persistence contract, one call that owns the full lifecycle of the child rows, is the same contract Dependent Mapping describes, applied at the framework level to every model that declares it.

## 10. Consequences

Positive.

- One fewer mapper class per dependent kind, and a smaller total surface of find, insert, update and delete methods to review, test and keep consistent across a codebase.
- The aggregate's persistence boundary is enforced by the code's structure, not only by a naming convention or a comment, since there is no `TrackMapper` for a second code path to reach for, so the temptation to bypass the owner does not present itself as an available option.
- Writing the owner and every dependent inside one mapper call makes it natural to keep them inside one transaction, removing an entire class of partial-write inconsistency that a separate child mapper would need external coordination to prevent.
- Dependents frequently need no Identity Field of their own, which removes generated-key round trips and identity-map bookkeeping the domain never asked for.

Negative.

- The owner mapper grows with every kind of dependent folded into it. Applied past the point where a dependent genuinely has no independent meaning, the owner mapper accumulates unrelated reconciliation logic and becomes the file every change to persistence has to pass through.
- The straightforward delete-and-reinsert save strategy issues writes proportional to the size of the whole collection on every save, even when only one field on one dependent changed, which is a real and sometimes large cost on big collections or high write frequency.
- The dependent loses independent identity and independent addressability by design. If a later requirement needs to reference, query, or page through the dependent on its own, the whole mapping has to migrate to Foreign Key Mapping, a change that touches the schema, the owner mapper, and every caller that had assumed the dependent could not be looked up alone.
- Testing a dependent's persistence behavior in isolation from its owner has no natural entry point, because the mapper that would provide one does not exist, dimension 15 covers the resulting testing shape in detail.
- A delete-then-reinsert save that is not wrapped in a transaction, or that spans two separate database calls without one, can lose dependent rows entirely if the delete succeeds and the reinsert then fails.

## 11. Failure modes and misuse

| Symptom | Cause | Fix |
|---|---|---|
| Dependent rows for an owner intermittently disappear after an otherwise successful update. | The delete-and-reinsert sequence for dependents is not wrapped in the same transaction as the owner's update, or the two run over separate database connections, so a failure between the delete and the reinsert leaves the dependents gone. | Wrap the owner row write and every dependent row write in one transaction, coordinated by a surrounding Unit of Work, so either all of them commit or none do. |
| A save that changes one field on one dependent among many issues hundreds of DELETE and INSERT statements and dominates request latency. | The delete-all-and-reinsert strategy scales with the size of the whole collection on every save, regardless of how little actually changed. | Move to diff-based reconciliation that issues only the insert, update and delete statements the actual change requires, or adopt an ORM's dirty-checking implementation of the same idea. |
| Two rows in the dependent table carry what should be the same logical child, with duplicated data under one owner. | The reinsert step ran without the delete step having succeeded first, often because the owner's Identity Field had not been assigned and flushed yet, so the delete filtered on a value that did not match any existing row. | Assign and flush the owner's Identity Field before issuing any dependent delete or insert, and add a database constraint on the dependent's natural key as a backstop against the same class of bug recurring. |
| A report or a second feature queries the dependent table directly and returns results that silently drift out of step with what the owner mapper's reconciliation logic would produce. | Dependent Mapping is enforced by code organization and convention, not by database privilege, and nothing stops a second code path from issuing SQL against the dependent table. | Restrict direct access to the dependent table through a database view, a schema permission, or a code-review convention naming the owner mapper as the sole writer, or, if a second legitimate consumer genuinely exists, promote the dependent to Foreign Key Mapping with its own mapper. |
| Loading a list of owners issues one extra query per owner to fetch that owner's dependents, and the query count grows linearly with the list size. | The two-select load variant is implemented per owner rather than batched across the whole result set being loaded. | Batch-load dependents for every owner in the current result set with one query filtered by album ids IN a list, or switch to the single joined-select variant when the result set is small. |
| Dependent rows remain in the table pointing at an owner id that no longer exists. | The owner mapper's delete method removes only the owner's own row and omits the corresponding dependent cleanup, a gap that is easy to introduce when the delete method is added or modified after the insert and update methods were already written. | Make the owner mapper's delete method symmetric with insert and update, always removing dependents first, and add a foreign key constraint with a cascading delete as a database-level backstop, checking first that the cascade does not skip any domain-level side effect the application expects to run per removed dependent. |

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3.

| Force | Dependent Mapping | Foreign Key Mapping | Association Table Mapping | Embedded Value | Serialized LOB |
|---|---|---|---|---|---|
| Mapper classes needed | One, shared with the owner | One per referenced class | One per side, plus the link table | None, folded into the owner's own columns | One, shared with the owner |
| Independent query on the child | Not supported | Supported directly | Supported directly | Not applicable, no independent object | Not supported at all, not even by the owner |
| Cardinality it targets | A collection of child rows | A single reference or a collection of references | A many-to-many collection | A single embedded object | A whole graph of arbitrary shape |
| Identity Field on the child | Usually none exposed | Required | Required on both sides | None, not a row of its own | None, not a row of its own |
| Write cost on save, delete-reinsert baseline | O(n) in collection size per save | O(1) per changed reference | O(n) in the link rows changed | O(1), part of the owner's own row | O(1), one blob write |
| Suitable for a large or unbounded collection | Poor | Good | Good | Not applicable | Poor, and worsens with size |
| Referential integrity from outside the aggregate | Not supported by design | Native, via the foreign key | Native, via two foreign keys | Not applicable | Not supported |
| Reporting or ad hoc SQL against the child data | Possible, still real rows | Possible, still real rows | Possible, still real rows | Possible, columns on the owner's row | Not possible without deserializing the blob |
| Suitability when the child has no independent meaning | Strong fit | Overkill, extra mapper for nothing addressable | Wrong shape, no shared reference exists | Fits only a single object, not a collection | Fits when the shape is too irregular to model relationally |

Reading of the table. Dependent Mapping and Embedded Value both assume the child has no independent identity, and differ on cardinality, one embedded object versus a collection of child rows. Foreign Key Mapping and Association Table Mapping both assume the opposite, that the referenced object does have independent identity, and differ on whether the relationship is single-owner or shared between many. Serialized LOB gives up on relational modeling of the child entirely, trading every one of the query-related forces for a single write, and is the pattern to reach for only once Dependent Mapping's own child-table approach has already been rejected as too rigid for the shape of the data.

## 13. Related and incompatible patterns

- **Data Mapper.** The parent pattern. Data Mapper says a persistent class has a mapper, Dependent Mapping is the specific decision about how many mapper classes an aggregate actually needs, folding a dependent's responsibility into its owner's mapper rather than giving it one of its own.
- **Identity Field.** Usually absent from the domain-visible side of the dependent under this pattern. The owner still carries an Identity Field, and that same value becomes the foreign key the owner mapper writes into every dependent row.
- **Foreign Key Mapping.** The pattern a dependent graduates to once it needs independent identity or independent querying. The two are mutually exclusive for a given class at a given time. A class is mapped by exactly one of the two strategies, though a codebase migrates a class from one to the other as requirements change, and dimension 14 walks through that migration in both directions.
- **Embedded Value.** The sibling pattern for a single embedded object rather than a collection. Embedded Value maps one object into extra columns of the owner's own row, while Dependent Mapping maps a collection of objects into rows of a separate child table. A field that starts as one embedded value and later needs to become a repeatable collection is a common trigger for moving from Embedded Value to Dependent Mapping.
- **Serialized LOB.** An alternative for the same private-ownership situation, chosen instead of Dependent Mapping when the child graph is too irregular or too deeply nested to model as rows and columns at all. Choosing between the two is a trade of queryability for simplicity, in Serialized LOB's favor, that goes further than Dependent Mapping already goes.
- **Unit of Work.** Composes directly underneath Dependent Mapping's save logic. A mature implementation defers the owner's and every dependent's writes to a Unit of Work that commits them together, rather than issuing the delete-and-reinsert calls directly inside the mapper's own method body, which is how the transactional guarantee described in dimension 7 and dimension 11 is actually delivered in practice.
- **Aggregate, Domain-Driven Design.** The domain-modeling vocabulary for the same ownership boundary Dependent Mapping encodes at the persistence layer. Aggregate, as described in Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003, part III, chapter 6, is a domain-level rule about which objects change together under one transactional boundary, Dependent Mapping is one concrete way to make a persistence layer respect that rule once it has already been decided at the domain level.
- **Composite, Gang of Four.** Structurally similar at the object-modeling level, an owner holding a tree or list of parts, but addresses a different problem entirely, Composite is about treating individual objects and compositions of objects uniformly through a shared interface, with no persistence concern at all. The two frequently appear together because the same has-a-collection-of-parts shape that motivates reaching for Composite in the domain model is often exactly the shape that motivates reaching for Dependent Mapping once that model needs to be persisted.

## 14. Refactoring path in and out

Introducing Dependent Mapping into a codebase that does not yet have it.

1. Identify the candidate child class and check it against every item in the applicability list in dimension 4. If any non-applicability condition holds, stop, this refactoring is the wrong direction for that class.
2. Confirm the dependent table already carries, or add, a foreign key column back to the owner's Identity Field. This column is the only structural change the schema needs.
3. If the child currently has its own mapper, move its find-by-owner logic into the owner mapper as a private helper method, and delete the public finder methods that allowed the child to be looked up on its own.
4. Write the owner mapper's save logic for the dependent collection, starting with the delete-and-reinsert baseline from dimension 8, inside the same transaction as the owner's own save.
5. Remove any domain code that constructs or holds a reference to the child's own mapper, and delete that mapper class once nothing references it.
6. Add a test, described in dimension 15, that asserts the dependent table cannot be reached through any code path except the owner mapper.

Migrating a dependent out to Foreign Key Mapping once it has outgrown private ownership.

1. Confirm the trigger condition. Something outside the current owner now needs to reference the dependent by its own identity, query it independently, or the collection has grown past what the owner mapper can comfortably load in full.
2. Add a domain-visible Identity Field to the dependent if it does not already expose one, the technical primary key the owner mapper was using privately is the natural candidate to promote.
3. Extract a first-class mapper for the dependent, giving it its own find, insert, update and delete methods, following Foreign Key Mapping.
4. Change the owner mapper to compose the new dependent mapper for its own load and save operations, rather than issuing SQL against the dependent table directly.
5. Publish a repository or finder API for the dependent's new mapper so the new consumer can reach it without going through the owner.
6. Migrate existing callers gradually if there are several, keeping the owner-mediated path functioning throughout the transition, following the strangler approach of running both paths side by side before removing the old one, then remove the owner mapper's direct SQL against the dependent table once every caller has moved.

## 15. Testing and verification

This pattern makes aggregate-level consistency easy to test directly. A single test that saves an owner with its dependents, reloads it through the owner mapper, and asserts the reloaded graph matches the original, exercises the entire persistence contract for that aggregate in one pass. There is no separate dependent repository to fake, mock, or keep in sync with the owner's own test setup, because none exists.

This pattern makes two things harder as a direct consequence, isolating a failure to the exact layer that caused it, and testing the dependent's persistence behavior on its own. Because there is no independent entry point for the dependent, every test of dependent persistence necessarily goes through the owner's full save and load cycle, which means a bug specific to how one dependent field is written surfaces as a failure of the owner's round-trip test rather than as a focused, dependent-only test failure. This is a practice-level observation rather than a sourced claim.

Two techniques address the harder half directly. First, prefer an in-process real database over a mocked SQL layer for mapper-level tests. The delete-and-reinsert reconciliation, the extra-query batching behaviour, and orphaned row prevention discussed in dimension 11 all live at the exact boundary a mock hides, so a test suite that fakes the database at the mapper's SQL boundary can pass while the real reconciliation logic is broken. An in-memory table abstraction, of the kind shown in the code examples below, or an embedded database engine, keeps this class of test fast while still exercising real select, insert and delete operations rather than a hand-waved fake. Second, keep pure in-memory fakes for domain-level tests that never touch persistence at all, such as tests of the `Album` and `Track` classes' own behavior, those tests gain nothing from a real database and should not pay its cost.

One assertion worth writing once per dependent kind is a test that attempts to reach the dependent table through any means other than the owner mapper and asserts that no such path exists in the codebase, whether by a static check of imports and SQL literals, or, more simply, by keeping the dependent's mapping details, including its table name, private to the owner mapper's own module so no other module can even reference them.

## 16. Observability signals

- **Statement count per owner save.** A count, or a histogram, of the number of DELETE and INSERT statements the owner mapper issues per save call. A sudden or sustained rise signals either a growing dependent collection or the O(n) rewrite cost from the delete-and-reinsert baseline becoming visible at scale, and is the earliest warning that a diff-based reconciliation is due.
- **Dependent row count distribution per owner, over time.** A metric tracking how many dependent rows exist per owner, watched for its distribution drifting upward. This is the signal that a dependent thought to be bounded, per the applicability condition in dimension 4, has stopped being bounded, and should prompt a review of whether the class still belongs to Dependent Mapping.
- **A trace span around the owner mapper's save and load calls**, with the owner-row query and the dependent-row query or queries nested underneath it. Because both operations happen inside one call by design, a slow save or load is directly attributable to which of the two, owner or dependents, dominated the latency, without needing to correlate across separate spans the way two independent mappers would require.
- **A periodic integrity check counting orphaned dependent rows**, meaning rows whose foreign key points at an owner id that no longer exists in the owner table. This is the direct, mechanical canary for the failure mode described in the last row of dimension 11's table, and it is inexpensive to run as a scheduled query because it touches only the two tables involved.
- **An alert on the dependent table's row count or partition size approaching a database-imposed or operationally chosen limit.** Dependent Mapping is not designed for a child table that needs to scale independently of its owner, and an approaching size limit is the concrete, measurable version of the non-applicability condition about unbounded collections.

## 17. Security and privacy implications

Because every code path that touches the dependent table passes through the owner mapper, row-level authorization for the dependent naturally centralizes at one gate rather than needing to be re-implemented at a second mapper. This is a real, if modest, benefit for access control, stated as engineering judgement rather than as a property the pattern's authors set out to guarantee.

Where the dependent holds personal or otherwise sensitive data, for example an `Address` mapped as a Dependent of a `Contact`, the delete-and-reinsert save strategy rewrites the physical row on every save regardless of whether the sensitive field itself changed. This interacts with data-protection obligations in two directions worth naming plainly, both stated as engineering judgement rather than as sourced legal claims. An erasure request against the dependent is, in one sense, simpler to satisfy correctly, because the whole row-set for that owner is already routinely replaced rather than mutated in place, which reduces the chance of a stray untouched copy surviving elsewhere. At the same time, an audit trail of exactly which value changed on which date is not produced automatically by a delete-and-reinsert save, since the old row and the new row are, from the database's point of view, unrelated inserts rather than an update with a diff, so any change-history requirement has to be built separately, commonly by the owner mapper writing an explicit audit record alongside the reconciliation rather than the reconciliation itself supplying one.

Any encryption, masking, or column-level protection a sensitive dependent requires applies identically to the way it would apply on a first-class mapped entity, Dependent Mapping changes nothing about that underlying requirement. What does change is the ease of forgetting the dependent table exists during a data-protection audit, precisely because it has no dedicated mapper class or repository for an auditor searching the codebase to find, a codebase adopting Dependent Mapping for a sensitive dependent should record that table explicitly wherever the application otherwise catalogs which tables hold personal data, since the pattern's own structure will not surface it on its own.

## Code examples

Three languages where the Data Mapper family is genuinely idiomatic. Each example implements the same Album-and-Track aggregate from Fowler's own worked example, backed by an in-memory table abstraction that mimics the select, insert and delete operations a real SQL database would perform, so the mapper's reconciliation logic is exercised the same way it would be against a real schema without requiring a database driver to run the sample. The delete-and-reinsert strategy from dimension 8 is the one shown, because it is the baseline the catalog entry itself describes.

### TypeScript

```typescript
interface AlbumRow {
  id: number;
  title: string;
}

interface TrackRow {
  id: number;
  albumId: number;
  title: string;
  seconds: number;
}

class InMemoryTable<T extends { id: number }> {
  private rows: T[] = [];
  private nextId = 1;

  insert(row: Omit<T, "id">): T {
    const withId = { ...row, id: this.nextId } as T;
    this.nextId += 1;
    this.rows.push(withId);
    return withId;
  }

  updateOne(id: number, patch: Partial<T>): void {
    this.rows = this.rows.map((r) => (r.id === id ? { ...r, ...patch } : r));
  }

  selectWhere(predicate: (row: T) => boolean): T[] {
    return this.rows.filter(predicate);
  }

  deleteWhere(predicate: (row: T) => boolean): number {
    const before = this.rows.length;
    this.rows = this.rows.filter((r) => !predicate(r));
    return before - this.rows.length;
  }
}

class Track {
  constructor(public title: string, public seconds: number) {}
}

class Album {
  id: number | null = null;
  constructor(public title: string, public tracks: Track[] = []) {}
}
```

The owner mapper. `TrackMapper` does not exist anywhere in this file.

```typescript
class AlbumMapper {
  constructor(
    private readonly albums: InMemoryTable<AlbumRow>,
    private readonly tracks: InMemoryTable<TrackRow>
  ) {}

  insert(album: Album): void {
    const row = this.albums.insert({ title: album.title });
    album.id = row.id;
    this.insertTracks(album);
  }

  update(album: Album): void {
    if (album.id === null) {
      throw new Error("cannot update an album that was never saved");
    }
    this.albums.updateOne(album.id, { title: album.title });
    this.tracks.deleteWhere((t) => t.albumId === album.id);
    this.insertTracks(album);
  }

  find(id: number): Album | null {
    const rows = this.albums.selectWhere((a) => a.id === id);
    if (rows.length === 0) return null;
    const row = rows[0];
    const trackRows = this.tracks.selectWhere((t) => t.albumId === id);
    const album = new Album(
      row.title,
      trackRows.map((t) => new Track(t.title, t.seconds))
    );
    album.id = row.id;
    return album;
  }

  delete(id: number): void {
    this.tracks.deleteWhere((t) => t.albumId === id);
    this.albums.deleteWhere((a) => a.id === id);
  }

  private insertTracks(album: Album): void {
    for (const track of album.tracks) {
      this.tracks.insert({
        albumId: album.id as number,
        title: track.title,
        seconds: track.seconds,
      });
    }
  }
}

function demo(): void {
  const mapper = new AlbumMapper(
    new InMemoryTable<AlbumRow>(),
    new InMemoryTable<TrackRow>()
  );

  const album = new Album("Kind of Blue", [
    new Track("So What", 545),
    new Track("Freddie Freeloader", 590),
  ]);
  mapper.insert(album);

  const reloaded = mapper.find(album.id as number);
  console.log(reloaded?.title, reloaded?.tracks.length);

  reloaded!.tracks.push(new Track("Blue in Green", 337));
  mapper.update(reloaded!);

  const afterUpdate = mapper.find(album.id as number);
  console.log(afterUpdate!.tracks.map((t) => t.title));

  mapper.delete(album.id as number);
  console.log(mapper.find(album.id as number));
}

demo();
```

### Python

```python
from dataclasses import dataclass


@dataclass
class AlbumRow:
    id: int
    title: str


@dataclass
class TrackRow:
    id: int
    album_id: int
    title: str
    seconds: int


class InMemoryTable:
    def __init__(self) -> None:
        self._rows: dict[int, object] = {}
        self._next_id = 1

    def insert(self, factory) -> object:
        row = factory(self._next_id)
        self._rows[self._next_id] = row
        self._next_id += 1
        return row

    def update_one(self, row_id: int, **patch) -> None:
        row = self._rows[row_id]
        for key, value in patch.items():
            setattr(row, key, value)

    def select_where(self, predicate) -> list:
        return [r for r in self._rows.values() if predicate(r)]

    def delete_where(self, predicate) -> int:
        to_remove = [rid for rid, r in self._rows.items() if predicate(r)]
        for rid in to_remove:
            del self._rows[rid]
        return len(to_remove)


class Track:
    def __init__(self, title: str, seconds: int) -> None:
        self.title = title
        self.seconds = seconds


class Album:
    def __init__(self, title: str, tracks: list[Track] | None = None) -> None:
        self.id: int | None = None
        self.title = title
        self.tracks: list[Track] = tracks or []
```

The owner mapper. No `TrackMapper` class exists in this module.

```python
class AlbumMapper:
    def __init__(self, albums: InMemoryTable, tracks: InMemoryTable) -> None:
        self._albums = albums
        self._tracks = tracks

    def insert(self, album: Album) -> None:
        row = self._albums.insert(
            lambda new_id: AlbumRow(id=new_id, title=album.title)
        )
        album.id = row.id
        self._insert_tracks(album)

    def update(self, album: Album) -> None:
        if album.id is None:
            raise ValueError("cannot update an album that was never saved")
        self._albums.update_one(album.id, title=album.title)
        self._tracks.delete_where(lambda t: t.album_id == album.id)
        self._insert_tracks(album)

    def find(self, album_id: int) -> Album | None:
        rows = self._albums.select_where(lambda a: a.id == album_id)
        if not rows:
            return None
        row = rows[0]
        track_rows = self._tracks.select_where(lambda t: t.album_id == album_id)
        album = Album(row.title, [Track(t.title, t.seconds) for t in track_rows])
        album.id = row.id
        return album

    def delete(self, album_id: int) -> None:
        self._tracks.delete_where(lambda t: t.album_id == album_id)
        self._albums.delete_where(lambda a: a.id == album_id)

    def _insert_tracks(self, album: Album) -> None:
        for track in album.tracks:
            self._tracks.insert(
                lambda new_id, t=track: TrackRow(
                    id=new_id, album_id=album.id, title=t.title, seconds=t.seconds
                )
            )


def demo() -> None:
    mapper = AlbumMapper(InMemoryTable(), InMemoryTable())

    album = Album(
        "Kind of Blue",
        [Track("So What", 545), Track("Freddie Freeloader", 590)],
    )
    mapper.insert(album)

    reloaded = mapper.find(album.id)
    print(reloaded.title, len(reloaded.tracks))

    reloaded.tracks.append(Track("Blue in Green", 337))
    mapper.update(reloaded)

    after_update = mapper.find(album.id)
    print([t.title for t in after_update.tracks])

    mapper.delete(album.id)
    print(mapper.find(album.id))


if __name__ == "__main__":
    demo()
```

### Go

Go has no inheritance and no exceptions, so the owner mapper's contract is expressed as ordinary methods on a struct returning an error value, and the in-memory table uses a slice guarded by the mapper's own single-threaded usage in this example rather than an interface hierarchy.

```go
package dependentmapping

type Track struct {
	Title   string
	Seconds int
}

type Album struct {
	ID     int
	Tracks []Track
	Title  string
}

type albumRow struct {
	id    int
	title string
}

type trackRow struct {
	id      int
	albumID int
	title   string
	seconds int
}

type albumTable struct {
	rows   []albumRow
	nextID int
}

func newAlbumTable() *albumTable {
	return &albumTable{nextID: 1}
}

func (t *albumTable) insert(title string) albumRow {
	row := albumRow{id: t.nextID, title: title}
	t.nextID++
	t.rows = append(t.rows, row)
	return row
}

func (t *albumTable) updateTitle(id int, title string) {
	for i := range t.rows {
		if t.rows[i].id == id {
			t.rows[i].title = title
		}
	}
}

func (t *albumTable) findByID(id int) (albumRow, bool) {
	for _, r := range t.rows {
		if r.id == id {
			return r, true
		}
	}
	return albumRow{}, false
}

func (t *albumTable) deleteByID(id int) {
	kept := t.rows[:0]
	for _, r := range t.rows {
		if r.id != id {
			kept = append(kept, r)
		}
	}
	t.rows = kept
}

type trackTable struct {
	rows   []trackRow
	nextID int
}

func newTrackTable() *trackTable {
	return &trackTable{nextID: 1}
}

func (t *trackTable) insert(albumID int, title string, seconds int) trackRow {
	row := trackRow{id: t.nextID, albumID: albumID, title: title, seconds: seconds}
	t.nextID++
	t.rows = append(t.rows, row)
	return row
}

func (t *trackTable) selectByAlbum(albumID int) []trackRow {
	var out []trackRow
	for _, r := range t.rows {
		if r.albumID == albumID {
			out = append(out, r)
		}
	}
	return out
}

func (t *trackTable) deleteByAlbum(albumID int) {
	kept := t.rows[:0]
	for _, r := range t.rows {
		if r.albumID != albumID {
			kept = append(kept, r)
		}
	}
	t.rows = kept
}
```

The owner mapper. No `trackMapper` type exists in this package.

```go
type AlbumMapper struct {
	albums *albumTable
	tracks *trackTable
}

func NewAlbumMapper(albums *albumTable, tracks *trackTable) *AlbumMapper {
	return &AlbumMapper{albums: albums, tracks: tracks}
}

func (m *AlbumMapper) Insert(album *Album) {
	row := m.albums.insert(album.Title)
	album.ID = row.id
	m.insertTracks(album)
}

func (m *AlbumMapper) Update(album *Album) bool {
	if album.ID == 0 {
		return false
	}
	m.albums.updateTitle(album.ID, album.Title)
	m.tracks.deleteByAlbum(album.ID)
	m.insertTracks(album)
	return true
}

func (m *AlbumMapper) Find(id int) (*Album, bool) {
	row, ok := m.albums.findByID(id)
	if !ok {
		return nil, false
	}
	trackRows := m.tracks.selectByAlbum(id)
	tracks := make([]Track, 0, len(trackRows))
	for _, tr := range trackRows {
		tracks = append(tracks, Track{Title: tr.title, Seconds: tr.seconds})
	}
	return &Album{ID: row.id, Title: row.title, Tracks: tracks}, true
}

func (m *AlbumMapper) Delete(id int) {
	m.tracks.deleteByAlbum(id)
	m.albums.deleteByID(id)
}

func (m *AlbumMapper) insertTracks(album *Album) {
	for _, track := range album.Tracks {
		m.tracks.insert(album.ID, track.Title, track.Seconds)
	}
}
```

## 18. References

- Martin Fowler, *Patterns of Enterprise Application Architecture*, Addison-Wesley, 2003, chapter 12, "Dependent Mapping."
- Martin Fowler, "Dependent Mapping," the online catalog entry for the same chapter, <https://martinfowler.com/eaaCatalog/dependentMapping.html>, verified 2026-08-02. Cited for the pattern's one-line intent and the Album-and-Track worked example.
- Martin Fowler, "Data Mapper," the online catalog entry, <https://martinfowler.com/eaaCatalog/dataMapper.html>, verified 2026-08-02. Cited for the chapter 10 reference to the parent pattern.
- Martin Fowler, "Catalog of Patterns of Enterprise Application Architecture," <https://martinfowler.com/eaaCatalog/>, verified 2026-08-02. Cited for the chapter 12 structural-pattern grouping and the one-line intents of Identity Field, Foreign Key Mapping, Association Table Mapping, Embedded Value and Serialized LOB referenced throughout this entry.
- Martin Fowler, "Serialized LOB," <https://martinfowler.com/eaaCatalog/serializedLOB.html>, verified 2026-08-02. Cited for the boundary between Dependent Mapping and its sibling pattern in dimension 8.
- Eclipse Foundation, "Jakarta Persistence Specification, Version 3.1," <https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1.html>, verified 2026-08-02. Cited in dimension 9 for the `orphanRemoval` wording in Section 2.10, "Entity Relationships."
- Doctrine Project, "Working with Associations," <https://www.doctrine-project.org/projects/doctrine-orm/en/latest/reference/working-with-associations.html>, verified 2026-08-02. Cited in dimension 1 and dimension 9 for Doctrine's own "privately owned" terminology and its Order-and-OrderItems example.
- Ruby on Rails, "ActiveRecord::NestedAttributes::ClassMethods" API documentation, <https://api.rubyonrails.org/classes/ActiveRecord/NestedAttributes/ClassMethods.html>, verified 2026-08-02. Cited in dimension 9 for the atomic parent-save behaviour of `accepts_nested_attributes_for` and the `:allow_destroy` option.
- Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003, part III, chapter 6. Cited in dimension 13 for the Aggregate concept as the domain-modeling counterpart of the ownership boundary this pattern implements at the persistence layer.
