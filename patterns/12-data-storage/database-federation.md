---
name: Database Federation
slug: database-federation
family: 12-data-storage
category: Data and Storage
aliases: [Federated Query, Foreign Data Wrapper]
first_described: "PostgreSQL's own postgres_fdw and Trino's own connector architecture, current documentation"
maturity: established
related: []
incompatible_with: []
verified: 2026-08-23
---

# Database Federation

## 1. Name, aliases, and lineage

Database federation lets a single query reach across more than one
underlying data store, treating remote tables, or entirely different
systems, as if they were local, without first copying all the data into
one place.

This entry sources it directly from two current, live implementations.
PostgreSQL's own foreign data wrapper, fetched live. "the postgres_fdw
module provides the foreign-data wrapper postgres_fdw, which can be used
to access data stored in external PostgreSQL servers" (PostgreSQL,
"postgres_fdw," PostgreSQL documentation,
https://www.postgresql.org/docs/current/postgres-fdw.html, verified
2026-08-23). Trino's own connector-based federation, fetched live. "you
can configure two catalogs in a single Trino cluster that both use the
Hive connector, allowing you to query data from both clusters, even
within the same SQL query" (Trino, "Trino Concepts," Trino documentation,
https://trino.io/docs/current/overview/concepts.html, verified
2026-08-23).

## 2. Problem and context

Data that a person or an application needs often lives in more than one
system, a transactional database here, an analytical warehouse there, a
data lake elsewhere, and copying all of it into one place before every
query is slow, stale by the time it finishes, and duplicates storage.
PostgreSQL's own text names the direct alternative. "you need only SELECT
from a foreign table to access the data stored in its underlying remote
table" (PostgreSQL, "postgres_fdw," verified 2026-08-23), querying the
remote data in place instead of copying it first.

## 3. Forces

The direct tension is between query correctness and query performance
when part of the work must happen on a remote system this side does not
fully control. PostgreSQL's own text names the exact trade-off directly.
"to reduce the risk of misexecution of queries, WHERE clauses are not
sent to the remote server unless they use only data types, operators, and
functions that are built-in or belong to an extension that's listed in
the foreign server's extensions option" (PostgreSQL, "postgres_fdw,"
verified 2026-08-23), choosing correctness (never mis-execute a filter
remotely) over always pushing every possible operation down for maximum
speed.

## 4. Applicability and non-applicability

PostgreSQL's own text names several explicit, concrete non-applicability
cases directly. "postgres_fdw currently lacks support for INSERT
statements with an ON CONFLICT DO UPDATE clause," and for an UPDATE or
DELETE query, full push-down to the remote server only happens "if there
are no query WHERE clauses that cannot be sent to the remote server, no
local joins for the query, no row-level local BEFORE or AFTER triggers or
stored generated columns on the target table, and no CHECK OPTION
constraints from parent views" (PostgreSQL, "postgres_fdw," verified
2026-08-23), a precise, named boundary on when the remote work can be
pushed down versus pulled back and executed locally.

## 5. Structure

Trino's own text names its own structural unit directly. a connector is
"an implementation of Trino's service provider interface (SPI), which
allows Trino to interact with a resource using a standard API" (Trino,
"Trino Concepts," verified 2026-08-23), an adapter between Trino's own
standard query interface and whatever protocol a specific underlying
system actually speaks. PostgreSQL's own structure is narrower and more
specific, a single foreign-data-wrapper extension speaking Postgres's own
wire protocol to another Postgres server, per dimension 1.

## 6. ASCII structure diagram

```
  Trino, connector-based federation, one query, many systems:

  +------------------------------------------------+
  |                Trino query engine                |
  +------------------------------------------------+
        |               |                |
        v               v                v
  +----------+    +----------+    +----------+
  | Hive       |    | Iceberg    |    | another    |
  | connector  |    | connector  |    | connector  |
  +----------+    +----------+    +----------+
        |               |                |
        v               v                v
  data lake       lakehouse        a third system

  one SQL query joins across all three, per dimension 1.

  PostgreSQL, foreign data wrapper, narrower scope:

  local PostgreSQL server  --postgres_fdw-->  remote PostgreSQL server
  a foreign table looks and queries like a local one, per dimension 1.
```

## 7. Dynamics

PostgreSQL's own text describes the write path directly, not only reads.
"you can also modify the remote table using INSERT, UPDATE, DELETE, COPY,
or TRUNCATE" (PostgreSQL, "postgres_fdw," verified 2026-08-23), and the
partitioned-table dynamic carries its own named limitation. "postgres_fdw
supports row movement invoked by UPDATE statements executed on
partitioned tables, but it currently does not handle the case where a
remote partition chosen to insert a moved row into is also an UPDATE
target partition that will be updated elsewhere in the same command"
(same source), a concrete, sourced edge case in how a write actually
executes across the federation boundary.

## 8. Implementation variants

This entry confirmed two genuinely distinct implementation variants
directly. PostgreSQL's postgres_fdw, a narrow, protocol-specific wrapper
for talking to another PostgreSQL server, per dimension 1 and 5. Trino's
connector architecture, a general-purpose SPI that can federate across
"traditional relational databases and other data sources such as
Cassandra" (Trino, "Trino Use Cases," Trino documentation,
https://trino.io/docs/current/overview/use-cases.html, verified
2026-08-23), a broader, engine-level federation layer rather than a
single-database extension.

## 9. Known production uses

PostgreSQL's postgres_fdw and Trino's connector-based query engine are
each real, currently shipping, widely deployed open-source projects,
confirmed directly against each project's own live documentation under
dimensions 1, 5, and 8.

## 10. Consequences

The benefit is stated directly, already implied under dimension 2, a
query reaches remote data without a separate copy-and-load step first,
avoiding both the storage duplication and the staleness a full copy would
introduce. the cost is the named correctness-vs-performance trade under
dimension 3 and 4, not every operation can be safely pushed down to the
remote system, so some work falls back to slower, local execution to stay
correct.

## 11. Failure modes and misuse

PostgreSQL's own text names the sharpest, most directly sourced failure
mode as the partitioned-table edge case already quoted in full under
dimension 7, a row moved into a remote partition that is simultaneously
an UPDATE target elsewhere in the same command is a case
postgres_fdw does not currently handle, a real, named gap rather than a
hypothetical one.

## 12. Trade-off matrix

| Dimension | Database federation | A full ETL copy into one store |
|---|---|---|
| Data freshness | Live, queried in place, dimension 2 | As stale as the last load |
| Storage duplication | None, dimension 2 | A full second copy |
| Operations safely pushed down | Bounded, explicit rules, dimension 3 and 4 | Not applicable, all data is local |
| Write support across the boundary | Yes, with named edge cases, dimension 7 and 11 | Not applicable |
| Cross-system query in one statement | Yes, Trino's connector model, dimension 6 | Only after the copy completes |

## 13. Related and incompatible patterns

This entry explicitly checked the fetched sources for a comparison to
ETL or ELT pipelines by name, the copy-first alternative named directly
in dimension 2 and 12, and did not find either fetched documentation
page drawing that comparison explicitly, though the trade-off is implicit
in the very reason a foreign-data wrapper or a connector exists, querying
in place instead of copying first. this entry reports that the
comparison is this entry's own reasoned framing rather than a claim
either source states directly.

## 14. Refactoring path in and out

Trino's own text names the concrete lever for adding a new federated
source directly, already quoted in dimension 6, configuring a new catalog
with the appropriate connector. PostgreSQL's own equivalent lever, per
dimension 1, is creating a new foreign server and foreign table
definition pointing at the remote database, neither of which the fetched
sources describe as a staged migration, both are direct configuration
steps.

## 15. Testing and verification

This entry explicitly checked the fetched sources for a documented test
methodology specific to federation correctness and did not find one
described as a formal process. the closest verifiable behavior is
PostgreSQL's own stated push-down rules, per dimension 3 and 4, which a
test would exercise by confirming a query with a disallowed WHERE clause
or trigger condition falls back to local execution rather than silently
mis-executing on the remote server.

## 16. Observability signals

This entry explicitly checked the fetched sources for a named metric or
dashboard specific to federation health and did not find one described on
the specific pages fetched. the closest directly sourced signal is
whether a given query's WHERE, JOIN, UPDATE, or DELETE clause qualifies
for push-down under the named rules in dimension 3 and 4, which an
operator could inspect via the query plan to judge how much work is
actually happening remotely versus locally.

## 17. Security and privacy implications

This entry explicitly checked the fetched sources for a security or
privacy discussion and did not find one addressed on the specific pages
fetched. this entry reports that absence directly rather than asserting a
security property neither source states.

## 18. References

1. PostgreSQL, "postgres_fdw," PostgreSQL documentation,
   https://www.postgresql.org/docs/current/postgres-fdw.html, verified
   2026-08-23.
2. Trino, "Trino Concepts," Trino documentation,
   https://trino.io/docs/current/overview/concepts.html, verified
   2026-08-23.
3. Trino, "Trino Use Cases," Trino documentation,
   https://trino.io/docs/current/overview/use-cases.html, verified
   2026-08-23.

## Code

TypeScript, Python, and Go implementations of a minimal federation router
following the mechanism from dimensions 5 and 6, dispatching a query to
the correct named connector based on which catalog it targets.

```typescript
type QueryFn = (query: string) => string[];

class FederationRouter {
  private connectors = new Map<string, QueryFn>();

  registerConnector(catalog: string, fn: QueryFn): void {
    this.connectors.set(catalog, fn);
  }

  query(catalog: string, sql: string): string[] {
    const fn = this.connectors.get(catalog);
    if (!fn) {
      throw new Error("no connector registered for catalog: " + catalog);
    }
    return fn(sql);
  }
}
```

```python
from typing import Callable, Dict, List

QueryFn = Callable[[str], List[str]]


class FederationRouter:
    def __init__(self) -> None:
        self._connectors: Dict[str, QueryFn] = {}

    def register_connector(self, catalog: str, fn: QueryFn) -> None:
        self._connectors[catalog] = fn

    def query(self, catalog: str, sql: str) -> List[str]:
        fn = self._connectors.get(catalog)
        if fn is None:
            raise ValueError("no connector registered for catalog: " + catalog)
        return fn(sql)
```

```go
package federation

import "fmt"

type QueryFn func(sql string) []string

type FederationRouter struct {
	connectors map[string]QueryFn
}

func NewFederationRouter() *FederationRouter {
	return &FederationRouter{connectors: make(map[string]QueryFn)}
}

func (r *FederationRouter) RegisterConnector(catalog string, fn QueryFn) {
	r.connectors[catalog] = fn
}

func (r *FederationRouter) Query(catalog string, sql string) ([]string, error) {
	fn, ok := r.connectors[catalog]
	if !ok {
		return nil, fmt.Errorf("no connector registered for catalog: %s", catalog)
	}
	return fn(sql), nil
}
```
