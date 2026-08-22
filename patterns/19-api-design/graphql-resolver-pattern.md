---
name: GraphQL Resolver Pattern
slug: graphql-resolver-pattern
family: 19-api-design
category: Data Fetching
aliases: [Field Resolver, Resolver Function]
first_described: 'GraphQL specification and graphql.org execution documentation'
maturity: canonical
related: [rest-resource-modeling, graphql-dataloader]
incompatible_with: []
verified: 2026-08-22
---

# GraphQL Resolver Pattern

## 1. Name, aliases, and lineage

GraphQL Resolver Pattern. Also called Field Resolver or Resolver Function. The pattern is the practice of attaching a single, independent function to each field of a GraphQL schema, where that function alone is responsible for producing the value for that field when a query asks for it. The official GraphQL documentation states the mechanism directly. this is exactly how GraphQL works, each field on each type is backed by a resolver function that is written by the GraphQL server developer, and when a field is executed, the corresponding resolver is called to produce the next value (https://graphql.org/learn/execution/).

The lineage runs from that core per-field execution model directly into the concrete shape server implementations give it. Apollo Server's own documentation states the per-field contract plainly. a resolver is a function that is responsible for populating the data for a single field in your schema (https://www.apollographql.com/docs/apollo-server/data/resolvers). That single sentence is the whole pattern. one function, one field, one job.

## 2. Problem and context

A client asking for data over an API rarely wants an entire, fixed record shape. It wants exactly the fields it needs, sometimes reaching across several related entities in one request, and rarely in the same shape two different clients would ask for. A server built around fixed endpoints returning fixed payloads forces either an ever-growing set of bespoke endpoints, one per client shape, or a single endpoint that always returns more data than most callers need.

The problem this pattern solves is letting a client describe the exact shape of data it wants in a single request, while the server still resolves each requested field independently, without the server author writing a bespoke handler for every possible combination of fields a client might ask for. Because each field on each type is backed by its own resolver function (https://graphql.org/learn/execution/), the server author writes exactly one function per field, and the query engine assembles whatever shape the client actually asked for out of those independent functions at execution time.

## 3. Forces

- A field that depends on a related type's own fields creates a graph of resolver calls that must be traced correctly, since a parent resolver's return value becomes the input to every child field's resolver.
- Resolvers for sibling fields on the same object commonly need the same underlying data, which risks duplicate work unless the underlying data source is fetched once and shared.
- A resolver that issues its own database or network call independently, for every instance of a field across a list of parent objects, creates one call per instance rather than one call for the whole list.
- Not defining a resolver for a field is a legitimate choice for a field the server can already answer trivially, and the server has to know when to fall back to a sensible default rather than require an explicit function for every single field.
- Authorization and validation concerns naturally want to live close to the data they guard, which pulls them toward living inside individual resolvers, at the cost of repeating the same check across every resolver that touches sensitive data.

## 4. Applicability and non-applicability

Use the GraphQL Resolver Pattern for an API where different clients need meaningfully different shapes of the same underlying data, especially when a single client screen commonly needs to traverse several related entities in one round trip, and where the server has a single, well understood schema that can describe the whole space of data clients are allowed to ask for.

This pattern is a non-applicability fit for a server that only ever returns one fixed shape per operation, or where every client genuinely needs the same complete payload every time, since the overhead of writing and maintaining a resolver per field buys nothing over a simpler, fixed response. It is also a poor fit for a server whose operations are fundamentally actions or commands rather than data retrieval, since forcing a command through a field-resolution model does not make it any clearer.

## 5. Structure

- Schema. the type definitions that describe every field a client is allowed to request, and the contract every resolver is written against.
- Resolver function. the single function attached to one field of one type, responsible for producing that field's value.
- Parent value. the value returned by the resolver for the enclosing field, passed as the first argument into every one of its child fields' own resolvers.
- Default resolver. the fallback the server uses for a field with no explicit resolver function defined, per Apollo Server's own documented behavior (https://www.apollographql.com/docs/apollo-server/data/resolvers).
- Execution engine. the part of the server that walks the requested selection set and calls the correct resolver for each requested field, in the correct order.

## 6. ASCII structure diagram

```

  query {                        Client selection set
    author(id: 42) {
      name                       -> Author.name resolver
      books {                    -> Author.books resolver
        title                    -> Book.title resolver (per item)
      }
    }
  }

  Query.author  -> returns an Author value (the parent value)
  Author.name   -> reads a field off the parent value directly
  Author.books  -> fetches a list, becomes the parent value for Book fields
  Book.title    -> reads a field off each item in that list

```

## 7. Dynamics

1. A client sends a query naming exactly the fields it wants, nested to match the shape of the related entities it wants to traverse.
2. The execution engine begins at the root type and calls the resolver for the first requested field, since each field on each type is backed by a resolver function (https://graphql.org/learn/execution/).
3. That resolver's return value becomes the parent value passed into the resolvers for every field the client requested beneath it, because a resolver is responsible for populating the data for a single field in the schema (https://www.apollographql.com/docs/apollo-server/data/resolvers).
4. The engine repeats this for every nested field the client asked for, walking the selection set exactly as the client wrote it, never touching a field the client did not request.
5. For any field with no explicit resolver defined, the server automatically defines a default resolver for it (https://www.apollographql.com/docs/apollo-server/data/resolvers), so a trivial field needs no author-written function at all.
6. The engine assembles every resolved value back into a single response shaped exactly like the client's original selection set.

## 8. Implementation variants

- Field-level resolvers on every field. the most explicit variant, where every field, including trivial ones, has an author-written function.
- Default resolver fallback. trivial fields that simply read a same-named property off the parent value rely entirely on the server's automatic default resolver, and only fields needing real logic get an explicit function.
- Batched resolver via a loader. a resolver that would otherwise issue one call per parent instance instead defers to a shared batching layer, collapsing many calls into one.
- Resolver chain with a service layer. the resolver itself stays a thin adapter, and all real business logic lives in a separate service the resolver calls into, keeping the resolver function itself simple to read.

## 9. Known production uses

- GitHub's public GraphQL API resolves every field of its schema, including deeply nested traversals across repositories, issues, and pull requests, through this per-field resolver model.
- Shopify's Admin API and Storefront API are both built on this same field-resolver execution model, letting merchant-facing and customer-facing clients each request only the product and order fields they need.
- Netflix's internal API gateway historically used a GraphQL layer with per-field resolvers to let different device teams request differently shaped views of the same underlying content catalog.

## 10. Consequences

Benefits.

- A client can request exactly the fields it needs in a single round trip, across related entities, without the server author writing a bespoke endpoint for that combination.
- Adding a new field to a type is a small, local change, one new resolver function, rather than a change to every existing endpoint that might want to expose it.
- Fields the client never asks for never execute their resolver at all, so the server does no wasted work computing data nobody requested.

Costs.

- A naive resolver that issues its own data-source call independently for every instance of a field, across a list of parents, produces one call per instance rather than one call for the whole list, degrading badly as list size grows.
- Authorization logic repeated inside many independent resolvers is easy to get inconsistent, since there is no single choke point every request must pass through the way a single fixed endpoint would provide.
- A deeply nested query can still be expensive for the server to resolve even when it looks small on the wire, since nesting multiplies the number of resolver calls executed.

## 11. Failure modes

- The N-plus-one problem. a resolver on a field that appears inside a list issues its own independent data fetch once per list item, turning what should be one query into one query per item.
- Unbounded query depth. a client nests a query deeply enough, especially against a resolver whose field returns objects of the same type it started from, that the server spends unbounded resolver calls answering one request.
- Inconsistent authorization. a check applied in one resolver but forgotten in a sibling resolver over the same underlying sensitive data leaves a path a client can use to bypass the intended access control.
- Silent default-resolver mismatch. a field with no explicit resolver falls back to the default, which reads a same-named property off the parent value, and if that property is named or shaped differently than the field, the field silently returns null instead of failing loudly.

## 12. Trade-off matrix

| Dimension | With this pattern | Without this pattern |

|---|---|---|

| Client flexibility | High. one query shapes exactly the fields needed | Low. fixed endpoint shapes force over- or under-fetching |
| Server-side call efficiency | Depends entirely on batching discipline per resolver | Predictable. one handler, one known set of calls |
| New-field cost | Low. one new resolver function | Higher. every consuming endpoint may need updating |
| Authorization consistency | Requires deliberate cross-resolver discipline | Naturally centralized in one endpoint handler |
| Query cost predictability | Low without depth or complexity limits | High. request shape is fixed in advance |

## 13. Related and incompatible patterns

Related to REST Resource Modeling, which solves the same underlying problem, letting a client retrieve exactly the entities it needs, through a different mechanism, a fixed set of nameable resource endpoints rather than a single schema of independently resolved fields. Related to GraphQL DataLoader, the standard answer to the N-plus-one failure mode this pattern is most prone to, batching and caching resolver calls that would otherwise run once per parent instance. Not incompatible with REST. many production systems expose both a REST surface and a GraphQL surface backed by resolvers over the same underlying data.

## 14. Refactoring path in and out

Introducing it.

1. Define the schema's types and fields first, describing the complete shape of data clients are allowed to request, independent of how any field's value will actually be produced.
2. Write an explicit resolver function only for the fields that need real logic, a computed value, a call to a data source, or a transformation, and rely on the default resolver for fields that simply read a same-named property off the parent value.
3. Identify every field that will appear inside a list and route its resolver through a batching layer from the start, rather than retrofitting batching after the N-plus-one problem is already in production.
4. Centralize authorization checks into a small number of shared functions that every sensitive resolver calls, instead of writing the check inline in each resolver.

Removing it.

1. Enumerate every field currently backed by a resolver and record what data source or computation each one actually performs, since this is the map of what a replacement endpoint set has to reproduce.
2. Identify the actual query shapes real clients send today, since these become the candidate fixed endpoints in a resource-oriented replacement.
3. Replace the schema and its resolvers with a fixed set of endpoints matching those real shapes, migrating clients one at a time behind a compatibility layer.
4. Remove the schema and resolver layer only once every client has migrated off it, since an intermediate compatibility layer typically has to serve both shapes for a transition period.

## 15. Testing and verification

- Unit test each resolver function in isolation, supplying a fixed parent value and arguments, and asserting the field's return value, independent of the rest of the schema.
- Run an integration test that executes a real nested query against the full schema, asserting the assembled response shape matches the client's selection set exactly.
- Add a specific regression test for every field that resolves against a list, asserting the number of underlying data-source calls does not scale linearly with list size.
- Test the default-resolver fallback path explicitly for any field intentionally left without its own function, confirming it reads the correct same-named property rather than silently returning null.

## 16. Observability signals

- Per-resolver execution time, so a single slow field inside an otherwise fast query is visible rather than hidden inside one aggregate request duration.
- Resolver call count per request, the direct signal for catching an N-plus-one pattern before it reaches production traffic at scale.
- Query depth and query complexity per request, tracked against a configured limit, since an unbounded nested query is invisible in request-count metrics alone.
- Rate of default-resolver fallbacks returning null, which surfaces a field whose schema name and underlying property name have silently drifted apart.

## 17. Security and privacy implications

Because a single query can traverse many resolvers across many types in one request, an authorization check written into only one resolver along a path does not protect the same sensitive data if it is also reachable through a different field path that skips that resolver. A field that returns a computed cost proportional to a client-controlled argument, without a depth or complexity limit enforced ahead of resolver execution, gives an unauthenticated or lightly authenticated client a lever to consume disproportionate server resources with a single request. Any resolver that reads sensitive data must enforce its own access check rather than assuming a check performed earlier in the resolver chain already covers it.

## 18. Code examples

### Swift

```swift

struct Author {
    let id: String
    let name: String
}

struct Book {
    let title: String
    let authorId: String
}

final class BookResolver {
    let books: [Book]

    init(books: [Book]) {
        self.books = books
    }

    // Resolves the books field on Author, one call for the whole list.
    func resolveBooks(forAuthor author: Author) -> [Book] {
        books.filter { $0.authorId == author.id }
    }
}

```

### Kotlin

```kotlin

data class Author(val id: String, val name: String)
data class Book(val title: String, val authorId: String)

class BookResolver(private val books: List<Book>) {
    // Resolves the books field on Author, one call for the whole list.
    fun resolveBooks(author: Author): List<Book> {
        return books.filter { it.authorId == author.id }
    }
}

```

### Python

```python

from dataclasses import dataclass

@dataclass
class Author:
    id: str
    name: str

@dataclass
class Book:
    title: str
    author_id: str

class BookResolver:
    """Resolves the books field on Author, one call for the whole list."""

    def __init__(self, books):
        self.books = books

    def resolve_books(self, author):
        return [b for b in self.books if b.author_id == author.id]

```

## 19. References

- GraphQL Foundation, Execution, https://graphql.org/learn/execution/
- Apollo Server documentation, Resolvers, https://www.apollographql.com/docs/apollo-server/data/resolvers
