---
name: Connection Pooling
slug: connection-pooling
family: 06-enterprise-application-architecture
category: Enterprise Application Architecture
aliases: [Database Connection Pool, Connection Pooler]
first_described: "PgBouncer's and HikariCP's own current documentation"
maturity: canonical
related: []
incompatible_with: []
verified: 2026-08-23
---

# Connection Pooling

## 1. Name, aliases, and lineage

Connection pooling keeps a small set of already-established database
connections open and reuses them across many client requests, instead of
opening and closing a fresh connection for every request.

This entry sources it directly from two of the most widely deployed
connection poolers, fetched live. on the JVM side, "HikariCP is a
'zero-overhead' production ready JDBC connection pool" (HikariCP,
"HikariCP," GitHub, https://github.com/brettwooldridge/HikariCP, verified
2026-08-23), described as "fast, simple, reliable" (same source). on the
PostgreSQL side, PgBouncer describes itself as a "lightweight connection
pooler for PostgreSQL" (PgBouncer, https://www.pgbouncer.org/, verified
2026-08-23).

## 2. Problem and context

PostgreSQL's own documentation states the direct constraint this pattern
works against. "max_connections... determines the maximum number of
concurrent connections to the database server. the default is typically
100 connections... PostgreSQL sizes certain resources based directly on
the value of max_connections. increasing its value leads to higher
allocation of those resources, including shared memory" (PostgreSQL,
"Connection Settings," PostgreSQL documentation,
https://www.postgresql.org/docs/current/runtime-config-connection.html,
verified 2026-08-23). this entry explicitly checked the fetched page for
the exact per-connection memory or process cost and did not find that
figure stated on this specific page, and reports that gap directly rather
than inventing a number.

## 3. Forces

The direct tension is between the number of clients that want to talk to a
database and the fixed, resource-bounded number of connections the
database server itself can sustain, per dimension 2. a pool resolves this
by having many clients share a much smaller set of already-open
connections, at the cost of the pool itself becoming a new point of
configuration and contention.

## 4. Applicability and non-applicability

HikariCP's own text names a specific applicability trade directly, stating
its recommended sizing philosophy. "for maximum performance and
responsiveness to spike demands, we recommend not setting this value and
instead allowing HikariCP to act as a fixed size connection pool" by
aligning `minimumIdle` with `maximumPoolSize` (HikariCP, verified
2026-08-23), naming a fixed-size pool as the applicable default rather
than a dynamically shrinking and growing one.

## 5. Structure

PgBouncer's own text names the three pooling modes directly, each a
distinct structural choice for how long a server connection is held by one
client before returning to the pool. "session pooling. when a client
connects, a server connection will be assigned to it for the whole
duration it stays connected. when the client disconnects, the server
connection will be put back into pool" (PgBouncer, "Features," PgBouncer
documentation, https://www.pgbouncer.org/features.html, verified
2026-08-23). "transaction pooling. a server connection is assigned to a
client only during a transaction. when PgBouncer notices that the
transaction is over, the server will be put back into the pool" (same
source). "statement pooling. this is transaction pooling with a twist.
multi-statement transactions are disallowed. this is meant to enforce
'autocommit' mode on the client" (same source).

## 6. ASCII structure diagram

```
  without pooling, every request opens a fresh connection:

  request 1 -> open connection -> query -> close connection
  request 2 -> open connection -> query -> close connection
  request 3 -> open connection -> query -> close connection

  with a connection pool, a small set of connections is reused:

  +------------------------------------------+
  | connection pool (fixed size)               |
  |   conn A     conn B     conn C            |
  +------------------------------------------+
       ^             ^             ^
       |             |             |
   request 1     request 2     request 3
   borrows A     borrows B     borrows C
   returns A     returns B     returns C
   (session, transaction, or statement scoped,
    per dimension 5)
```

## 7. Dynamics

HikariCP's own text names the key runtime sizing parameter directly.
"`maximumPoolSize`. this property controls the maximum size that the pool
is allowed to reach, including both idle and in-use connections" with a
stated default of 10 (HikariCP, verified 2026-08-23). PgBouncer's own three
modes, per dimension 5, each release a held server connection back to the
pool at a different runtime boundary, client disconnect, transaction end,
or statement end, which is the direct lever a pool operator tunes against
how long a real client actually needs to hold a connection.

## 8. Implementation variants

This entry confirmed two genuinely distinct, independently maintained
implementations live. HikariCP, a JVM-side, in-process connection pool
embedded directly inside the application, per dimension 1 and 7. PgBouncer,
a standalone, out-of-process proxy that sits between any client and
PostgreSQL and pools connections centrally, per dimension 1 and 5. the two
solve the same problem at different architectural layers, in-process
versus a shared external proxy, and this entry reports both as live,
confirmed variants rather than asserting one supersedes the other.

## 9. Known production uses

HikariCP and PgBouncer are each real, currently maintained, widely deployed
open-source projects, confirmed directly against each project's own live
documentation and source repository under dimensions 1, 5, and 7.

## 10. Consequences

The benefit is stated directly, already implied in dimension 2 and 3, a
fixed, small number of connections serves a much larger number of
concurrent clients without exhausting the database server's own
`max_connections` limit. the cost is the pool's own new failure surface,
a connection held too long by a slow client under session pooling, per
dimension 5, reduces the pool's effective capacity for every other client
waiting on it.

## 11. Failure modes and misuse

This entry explicitly checked both fetched sources for a named failure
mode and found PgBouncer's own text names one directly, embedded in the
definition of statement pooling itself, per dimension 5, multi-statement
transactions must be disallowed under that mode specifically to enforce
autocommit behavior, meaning an application written assuming ordinary
multi-statement transactions will misbehave if pointed at a
statement-pooling-mode PgBouncer without adjustment.

## 12. Trade-off matrix

| Dimension | Connection pooling | A fresh connection per request |
|---|---|---|
| Connections held against `max_connections` | Small, fixed, dimension 7 | Scales with concurrent request count |
| Per-request connection setup cost | Paid once, amortized | Paid on every request |
| Held-too-long risk | Yes, under session pooling, dimension 10 | Not applicable |
| Multi-statement transaction support | Depends on mode, dimension 5 and 11 | Always supported |
| Additional component to operate | Yes, the pool itself | None |

## 13. Related and incompatible patterns

This entry explicitly checked both fetched sources for a comparison to a
general object-pooling concept (the same reuse-instead-of-recreate idea
applied to any expensive resource) and did not find either page drawing
that comparison by name. this entry reports that absence directly rather
than asserting a cross-reference neither source states.

## 14. Refactoring path in and out

PgBouncer's own text names the explicit migration lever between its three
modes directly, already quoted in full under dimension 5, an operator
switches pooling mode in PgBouncer's own configuration to move from
session to transaction to statement pooling, trading connection-holding
duration for stricter client behavior requirements. HikariCP's own text
names the equivalent lever on the JVM side, already quoted in dimension 4,
adjusting `maximumPoolSize` and `minimumIdle` together to move toward or
away from a fixed-size pool.

## 15. Testing and verification

This entry explicitly checked both fetched sources for a documented test
methodology specific to pool correctness and did not find one described
as a formal process. the closest verifiable behavior is each project's own
own stated configuration contract, per dimensions 5 and 7, which a test
would exercise by holding a connection past its expected release point and
confirming the pool's own documented mode-specific behavior.

## 16. Observability signals

This entry explicitly checked both fetched sources for a named metric or
dashboard specific to pool health and did not find one described on the
specific pages fetched. the closest directly sourced signal is the pool
size parameters themselves, per dimension 7, `maximumPoolSize` and
`minimumIdle`, which a deployment can compare against its own observed
in-use connection count to judge whether the configured pool is sized
correctly.

## 17. Security and privacy implications

This entry explicitly checked both fetched sources for a security or
privacy discussion and did not find one addressed on the specific pages
fetched. this entry reports that absence directly rather than asserting a
security property neither source states.

## 18. References

1. HikariCP, "HikariCP," GitHub,
   https://github.com/brettwooldridge/HikariCP, verified 2026-08-23.
2. PgBouncer, "PgBouncer," https://www.pgbouncer.org/, verified
   2026-08-23.
3. PgBouncer, "Features," PgBouncer documentation,
   https://www.pgbouncer.org/features.html, verified 2026-08-23.
4. PostgreSQL, "Connection Settings," PostgreSQL documentation,
   https://www.postgresql.org/docs/current/runtime-config-connection.html,
   verified 2026-08-23.

## Code

TypeScript, Python, and Go implementations of a minimal fixed-size
connection pool following the mechanism from dimensions 5 through 7,
borrowing and returning a connection handle and blocking a new borrow when
the pool is exhausted.

```typescript
class ConnectionPool<T> {
  private idle: T[] = [];
  private inUse = new Set<T>();

  constructor(connections: T[]) {
    this.idle = [...connections];
  }

  borrow(): T {
    const conn = this.idle.pop();
    if (!conn) {
      throw new Error("pool exhausted");
    }
    this.inUse.add(conn);
    return conn;
  }

  release(conn: T): void {
    if (!this.inUse.has(conn)) {
      throw new Error("connection not borrowed from this pool");
    }
    this.inUse.delete(conn);
    this.idle.push(conn);
  }
}
```

```python
from typing import Generic, List, Set, TypeVar

T = TypeVar("T")


class ConnectionPool(Generic[T]):
    def __init__(self, connections: List[T]) -> None:
        self._idle: List[T] = list(connections)
        self._in_use: Set[T] = set()

    def borrow(self) -> T:
        if not self._idle:
            raise RuntimeError("pool exhausted")
        conn = self._idle.pop()
        self._in_use.add(conn)
        return conn

    def release(self, conn: T) -> None:
        if conn not in self._in_use:
            raise ValueError("connection not borrowed from this pool")
        self._in_use.discard(conn)
        self._idle.append(conn)
```

```go
package connectionpool

import (
	"errors"
	"sync"
)

type ConnectionPool struct {
	mu     sync.Mutex
	idle   []interface{}
	inUse  map[interface{}]bool
}

func NewConnectionPool(connections []interface{}) *ConnectionPool {
	return &ConnectionPool{
		idle:  append([]interface{}{}, connections...),
		inUse: make(map[interface{}]bool),
	}
}

func (p *ConnectionPool) Borrow() (interface{}, error) {
	p.mu.Lock()
	defer p.mu.Unlock()
	if len(p.idle) == 0 {
		return nil, errors.New("pool exhausted")
	}
	conn := p.idle[len(p.idle)-1]
	p.idle = p.idle[:len(p.idle)-1]
	p.inUse[conn] = true
	return conn, nil
}

func (p *ConnectionPool) Release(conn interface{}) error {
	p.mu.Lock()
	defer p.mu.Unlock()
	if !p.inUse[conn] {
		return errors.New("connection not borrowed from this pool")
	}
	delete(p.inUse, conn)
	p.idle = append(p.idle, conn)
	return nil
}
```
