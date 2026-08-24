---
name: Parameterized Query
slug: parameterized-query
family: 15-security
category: Injection Defense
aliases: [Prepared Statement, Bind Variables, Query Parameters, Bound Parameters]
first_described: "Established in database APIs and SQL interface practice"
maturity: canonical
related: [input-validation, output-encoding, least-privilege, defense-in-depth]
incompatible_with: [string-concatenated-sql, client-side-sql-escaping]
verified: 2026-08-02
---

# Parameterized Query

## 1. Name, aliases, and lineage

The canonical name in this catalog is **Parameterized Query**. The same design
is also called **prepared statement**, **bind variables**, **query parameters**,
**bound parameters**, and **parameter substitution**, depending on the database,
driver, or language API. OWASP uses the combined phrase "Prepared Statements
(with Parameterized Queries)" as its first listed defense against SQL injection
in the SQL Injection Prevention Cheat Sheet, and describes the coding style as
placing SQL code in the statement first and supplying parameter values later
(https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html,
verified 2026-08-02).

This is not a Gang of Four object pattern. It is a security and data-access
pattern at the boundary between application code and an interpreter. The name
comes from the database programming model rather than from a single design
patterns book. JDBC names the concrete interface `PreparedStatement`, describes
it as an object representing a precompiled SQL statement, and exposes setter
methods such as `setString` and `setInt` for input parameters (Oracle Java SE 17
API, `java.sql.PreparedStatement`,
https://docs.oracle.com/en/java/javase/17/docs/api/java.sql/java/sql/PreparedStatement.html,
verified 2026-08-02). Python's `sqlite3` documentation calls the same operation
"parameter substitution" and supports qmark and named placeholder styles
(https://docs.python.org/3/library/sqlite3.html, verified 2026-08-02). Go's
`database/sql` package uses the term placeholder parameters for the variadic
arguments passed to `Query`, `QueryContext`, and prepared statements
(https://pkg.go.dev/database/sql, verified 2026-08-02).

The lineage is older than most web frameworks because it follows from a basic
database interface decision. Keep the command text and the value list as
different pieces of data. PostgreSQL's extended query protocol makes the split
explicit. The frontend sends a `Parse` message containing query text for a
prepared statement, and later sends a `Bind` message containing parameter
format codes and parameter values for that prepared statement
(https://www.postgresql.org/docs/current/protocol-message-formats.html,
verified 2026-08-02). The exact client API varies, but the boundary is the
same. The SQL grammar is parsed from trusted statement text. Runtime values are
bound into the evaluated expression positions the statement already declared.

The name is sometimes confused with three related ideas.

- **Prepared statement.** Often the concrete mechanism underneath a
  parameterized query. A prepared statement can also be used for performance by
  parsing once and executing many times. Parameterized Query, as a pattern,
  focuses on separating code from values. Performance is a possible benefit, not
  the reason to adopt it.
- **Escaping.** A string transformation applied before concatenating text into a
  command. OWASP lists escaping all user input as strongly discouraged for SQL
  injection defense, compared with prepared statements, stored procedures, and
  allow-list validation
  (https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html,
  verified 2026-08-02). Escaping tries to make a dangerous operation less
  dangerous. Parameter binding changes the operation.
- **Input validation.** Validation decides whether a value is acceptable for the
  business operation. It does not decide how SQL syntax is built. A valid last
  name can contain an apostrophe. A valid search term can contain percent signs.
  Parameterized Query remains needed after validation because valid data can
  still be syntactically meaningful to SQL when inserted as text.

Judgement. Treat the aliases as evidence of adoption rather than as separate
patterns. A team that treats "prepared statements" as a performance feature and
"parameterized queries" as a security feature will often create two coding
rules for one boundary. That split makes review harder than it needs to be.

## 2. Problem and context

An application must issue a query whose predicate values come from runtime
state: a user id, tenant id, search term, date range, account status, cursor, or
authorization scope. SQL is an interpreter language. If the application creates
the command by joining trusted SQL fragments with untrusted strings, the
database receives one flat command. At that point the database cannot infer
which characters were intended as values and which characters were intended as
operators, comments, literals, identifiers, or statement delimiters.

The problem shows up in ordinary application code before it looks like an
attack. A developer writes:

```text
"SELECT id, email FROM users WHERE email = '" + email + "'"
```

The first user with an apostrophe in an email local part or search term breaks
the statement. A later attacker supplies characters that close the literal and
append a predicate or a second command. MITRE classifies this family as CWE-89,
Improper Neutralization of Special Elements used in an SQL Command, and
recommends parameterization with prepared statements, parameterized queries, or
stored procedures where available
(https://cwe.mitre.org/data/definitions/89.html, verified 2026-08-02).

Parameterized Query solves the problem by changing the representation passed
across the database boundary. The application sends a statement template with
placeholders in value positions, and sends the values through a separate binding
API. The driver and database then treat the values as typed data for those
positions. A value containing `' OR 1=1` is no longer a fragment of the SQL
grammar. It is a string value that may or may not equal a column value.

The context that makes this pattern the right answer has five parts.

- The application is constructing commands for an interpreter such as SQL, HQL,
  or a database-specific query interface.
- Some values in the command come from outside the trusted code path, including
  HTTP input, queue messages, file imports, admin consoles, partner feeds,
  feature flags, or data already stored by another user.
- The variable parts occupy value positions, such as predicates, inserted
  values, updated values, limit counts, and function arguments.
- The database driver exposes a real binding API. Examples include JDBC
  `PreparedStatement`, Python DB-API parameter substitution, Go `database/sql`
  arguments, Prisma raw query variables, SQLx `.bind`, and Node's SQLite
  `StatementSync` parameters (sources listed in dimension 18).
- Reviewers need a local rule they can check in code review. SQL text and
  values cross the database boundary through different parameters or different
  method calls.

Outside that context, the pattern does not answer the whole problem. Table
names, column names, sort directions, and SQL keywords are not values. Prisma's
raw query documentation states that variables cannot be used for identifiers
such as column names, table names, database names, or SQL keywords
(https://www.prisma.io/docs/orm/prisma-client/using-raw-sql/raw-queries,
verified 2026-08-02). When the variable part is an identifier, the pattern must
be paired with allow-list selection from known identifiers.

## 3. Forces

Judgement. The forces below describe engineering pressure around this pattern.
They are not claims that a source can measure across all systems.

- **Security.** Favoured. The pattern removes the main injection path where
  value text changes command structure. It narrows the review question from
  "was this string escaped correctly for this dialect" to "did this value cross
  through a binding API".
- **Correctness.** Favoured. Values containing quotes, comment markers,
  backslashes, percent signs, Unicode characters, or binary bytes remain data
  instead of syntax. This matters for ordinary users, not only for attackers.
- **Coupling.** Favoured at the call site. The caller does not need to know the
  database's quoting rules for each type. Coupling moves to the driver, which is
  the component with the dialect contract.
- **Consistency.** Favoured when all data access follows the same rule. Mixed
  query construction styles weaken the pattern because reviewers must reason
  about the exception path.
- **Latency.** Usually neutral to favourable. A prepared statement may reduce
  repeated parse work, as JDBC and SQLx documentation describe prepared
  statements as reusable or cached. It may also add a prepare round trip when a
  driver does not cache or when each statement text is unique. Treat latency as
  database and driver dependent.
- **Operability.** Mixed. Stable statement text makes aggregation and query
  fingerprinting easier, because values are not embedded into the command.
  Debugging can become harder if logs hide bound values, so the system needs a
  policy for safe redaction and sampling.
- **Cost.** Favoured over custom escaping. The driver already owns type
  conversion and protocol details. The cost appears when retrofitting a large
  codebase where SQL strings are assembled in many layers.
- **Team topology.** Favoured. A platform or security team can publish a narrow
  database access wrapper that accepts SQL text plus values. Application teams
  can use it without becoming experts in every database escape rule.
- **Cognitive load.** Mixed. The simple case reads clearly. Dynamic query
  builders with optional predicates now need to keep two artifacts aligned, the
  SQL fragments and the parameter list. Named parameters or typed query builders
  reduce that load.

The pattern favours security, correctness, and reviewability. It sacrifices
some freedom in dynamic SQL construction. That sacrifice is the point. Code
that can concatenate any text can express more commands, including unsafe ones.

## 4. Applicability and non-applicability

Reach for Parameterized Query when the following hold.

- A SQL predicate, inserted value, updated value, comparison operand, limit, or
  function argument comes from runtime data.
- The input has already been validated for business meaning, but can still
  contain characters with SQL meaning.
- The same statement shape executes many times with different values.
- The codebase needs a rule that static analysis and review can check.
- Raw SQL is necessary because an ORM query API cannot express the needed query.
- A query builder emits placeholders and a separate values list.
- The system must support multiple database dialects through a driver or ORM
  that already maps placeholder syntax.
- The team wants query logs grouped by statement shape rather than polluted with
  per-user literal values.

Do NOT reach for Parameterized Query as the whole solution in these cases.

- **Dynamic identifiers.** Placeholders bind values, not table names, column
  names, schema names, index hints, or sort keywords. Use an allow-list that maps
  a small application enum to fixed SQL fragments.
- **Whole query chosen by a user.** If an admin console accepts arbitrary SQL,
  binding values does not constrain the command. Use authorization, separate
  database roles, read-only transactions, auditing, and query limits.
- **Search syntax interpreted by another engine.** A value passed safely to SQL
  may still be interpreted by full-text search, regular expression, LIKE,
  XPath, JSONPath, or a vendor function. Bind the value, then apply the escape
  rules for that inner language where needed.
- **SQL fragments stored in the database.** A parameter can hold the fragment
  text, but if a stored procedure later executes that text, injection moved to
  the database layer. Ban or heavily review dynamic execution in stored
  routines.
- **DDL and maintenance commands that do not accept parameters.** Some database
  commands cannot be prepared or cannot bind every part. Build those commands
  from trusted constants and allow-listed identifiers.
- **Bulk load formats.** CSV, COPY streams, and vendor bulk APIs often have
  their own data framing. Use that API's field framing rather than pretending a
  parameter placeholder applies to the stream body.
- **Authorization bugs.** A parameterized query can safely ask for another
  tenant's rows if the tenant predicate is missing. Pair the pattern with access
  control and least privilege.
- **Unsafe client-side interpolation wrappers.** A helper that accepts a final
  string after interpolation is not this pattern, even if the function name says
  `query`. Review the call boundary, not the name.
- **Values need syntactic composition.** Lists for `IN`, optional predicates,
  sort direction, and conditional joins require a query builder that emits both
  SQL and values. Do not pass a comma-separated string as one parameter and
  expect SQL to treat it as a list.
- **The driver emulates binding by quoting strings client-side.** Some drivers
  or modes may emulate prepares. That can still be acceptable when the driver is
  correct for the dialect, but it is weaker than server-side binding and should
  be treated as a driver contract to verify.

## 5. Structure

The participants are named by the role they play in a data-access boundary.

- **Trusted statement text.** SQL written by application code, migrations, or a
  vetted query builder. It contains placeholders only where values are allowed.
  It does not contain raw user input.
- **Placeholder.** A marker in the trusted statement text. The marker syntax
  depends on the API and database. Examples include `?`, `$1`, `$2`, `:name`,
  or named placeholders supported by a driver.
- **Parameter value.** Runtime data bound to a placeholder. It may be a string,
  number, timestamp, binary value, Boolean, null, array type, or database
  specific value supported by the driver.
- **Binding API.** The method or object that pairs placeholders with values.
  JDBC uses setter methods on `PreparedStatement`. Python `sqlite3` passes a
  tuple or dictionary as the second argument to `execute`. Go `database/sql`
  passes variadic arguments after the query string. SQLx uses `.bind`.
- **Driver or client library.** The component that validates arity, maps
  language values to database types, and sends the request using the database
  protocol or safe client-side escaping contract.
- **Database parser and executor.** The database component that parses the
  statement shape and evaluates bound values in the already parsed expression
  positions.
- **Policy wrapper.** Optional. A local abstraction that rejects raw
  interpolation, centralizes logging, applies timeouts, redacts parameters, and
  can be searched for enforcement.

Relationships. Application code owns statement intent. The driver owns type
conversion and placeholder binding. The database owns parsing and execution.
Untrusted data may flow into Parameter Value, but not into Trusted Statement
Text. The policy wrapper exists to keep that rule from becoming a social
convention scattered across the repository.

## 6. ASCII structure diagram

```text
  Application service
  +--------------------------------------------------------------+
  | email = request.form["email"]                                |
  | sql = "select id from users where email = ?"                 |
  | db.query(sql, [email])                                       |
  +---------------------------+----------------------------------+
                              |
                              v
  Data access boundary
  +--------------------------------------------------------------+
  | Trusted statement text          Parameter values             |
  | "select ... where email = ?"    ["a' or 1=1"]                |
  |             |                         |                      |
  |             v                         v                      |
  |       placeholders              typed values                  |
  +-------------+-------------------+----------------------------+
                |
                v
  Driver or client library
  +--------------------------------------------------------------+
  | validates count, maps types, sends parse and bind data        |
  +-------------+------------------------------------------------+
                |
                v
  Database
  +--------------------------------------------------------------+
  | parse trusted SQL shape, then evaluate bound values as data   |
  +--------------------------------------------------------------+
```

## 7. Dynamics

At runtime the important event is not "escape the string." The important event
is "the value never becomes part of the command text." In a server-side prepared
path, the flow often looks like this.

```text
Client code       Driver              Database parser       Executor
    |                |                       |                  |
    | prepare(sql)   |                       |                  |
    |--------------->|  parse statement      |                  |
    |                |---------------------->|                  |
    |                |  statement handle     |                  |
    |                |<----------------------|                  |
    |                |                       |                  |
    | execute(vals)  |                       |                  |
    |--------------->|  bind values          |                  |
    |                |----------------------------------------->|
    |                |                       |  run with data   |
    |                |                       |<---------------->|
    | rows           |                       |                  |
    |<---------------|<-----------------------------------------|
```

Some drivers combine prepare and execute in one public call. That does not
change the pattern when the public call still accepts statement text and values
as separate inputs. Other drivers maintain a client-side statement cache. SQLx
documents that `query` executes a single SQL query as a prepared statement and
transparently caches it, with an option to disable persistence for environments
that have trouble with prepared statement caching
(https://docs.rs/sqlx/latest/sqlx/fn.query.html, verified 2026-08-02).

There are four dynamics to watch in real systems.

First, placeholder arity is part of the contract. Too few values, too many
values, or names that do not match should fail before the database changes data.
Python `sqlite3` documents that qmark parameters must match placeholder count
and named parameters must supply the required keys
(https://docs.python.org/3/library/sqlite3.html, verified 2026-08-02).

Second, parameter type is part of the contract. JDBC setter methods map Java
types to SQL types, such as `setString` to character types and `setInt` to an
integer type (Oracle Java SE 17 API, `PreparedStatement`, verified 2026-08-02).
Type mismatch is a correctness problem and sometimes a performance problem
because it can change casts and index use.

Third, statement identity affects caches. If the code interpolates values into
the SQL string, every value can produce a distinct statement. If the code binds
values, the statement shape is stable. Node's SQLite tag store documentation
states that tagged statements with the same query strings and bound placeholder
positions can match the cache, while literal interpolation changes the query
string (https://nodejs.org/api/sqlite.html, verified 2026-08-02).

Fourth, binding does not sanitize the result. The database may return data that
is later placed in HTML, JSON, a shell command, a log line, or another query.
That later sink needs its own output encoding or parameterization pattern.

## 8. Implementation variants

**Positional placeholders.** The SQL text contains anonymous markers such as `?`.
The value list is ordered. JDBC examples use question mark placeholders, and Go
examples show `?` for some drivers while noting that PostgreSQL drivers may use
`$1` instead (Oracle JDBC tutorial,
https://docs.oracle.com/javase/tutorial/jdbc/basics/prepared.html, verified
2026-08-02; Go querying documentation, https://go.dev/doc/database/querying,
verified 2026-08-02). Positional binding is compact and common. Its risk is
parameter drift when optional predicates are assembled across many branches.

**Numbered placeholders.** PostgreSQL-style `$1`, `$2`, and similar markers
make the value position explicit in the SQL text. SQLx documents `$1`, `$2`,
and later numbered placeholders for Postgres and SQLite, while MySQL and
MariaDB use `?` (https://docs.rs/sqlx/latest/sqlx/fn.query.html, verified
2026-08-02). Numbered placeholders reduce ambiguity during query assembly. They
can still be misordered when the code builds the values array separately.

**Named placeholders.** The SQL text contains names such as `:email` or
`$email`, and the binding API accepts a dictionary or object. Python `sqlite3`
documents named placeholder style using a dictionary
(https://docs.python.org/3/library/sqlite3.html, verified 2026-08-02). Named
binding reads well and tolerates predicate reordering. The cost is API and
driver variation around prefixes, duplicate names, and extra dictionary keys.

**Prepared object reused across executions.** Code prepares once, then executes
many times. JDBC documents that a `PreparedStatement` can be executed many
times after setting parameter values, and Go `database/sql` documents `Stmt`
methods that execute a prepared query with given arguments (Oracle JDBC
tutorial, verified 2026-08-02; Go `database/sql`, verified 2026-08-02). This
variant can reduce parse overhead for hot statements. It also creates lifecycle
work: close statements, watch server resources, and understand pool behaviour.

**One-shot parameterized call.** Code calls `query(sql, values)` without holding
a statement object. The driver may prepare, execute, and release, or may use a
cache. This is often the best default for application code. It gives the
security property without spreading statement lifecycle management through
business logic.

**Tagged template binding.** A language feature captures literal SQL fragments
separately from interpolated values. Prisma's `$queryRaw` uses a tagged
template and says Prisma Client creates prepared statements for variables in
that form (https://www.prisma.io/docs/orm/prisma-client/using-raw-sql/raw-queries,
verified 2026-08-02). Node's SQLite SQL tag store similarly treats `${value}`
in a tagged statement as a bound parameter, unlike an untagged template string
(https://nodejs.org/api/sqlite.html, verified 2026-08-02). This variant is
ergonomic in TypeScript and JavaScript, but reviewers must reject wrapper code
that builds an unsafe string before passing it to the tag.

**ORM query API.** Many ORMs parameterize values in generated SQL when the
developer uses expression APIs instead of raw SQL. This is still the same
boundary pattern, hidden behind a higher-level model. The risk is escape hatches
named "raw", "unsafe", or "literal" that accept already-built SQL text.

**Query builder with value accumulator.** A builder constructs SQL fragments
from trusted constants and accumulates bound values in the same operation. This
variant is the right answer for optional filters and dynamic `IN` lists. The
builder must generate placeholders for each value, not place a comma-joined
string into one placeholder.

**Stored procedure with parameters.** A stored procedure call can give the same
separation when the application binds procedure arguments and the procedure does
not construct dynamic SQL internally. OWASP states that stored procedures can
have the same effect as parameterized queries when implemented safely, while
also warning that stored procedures are not automatically safe
(https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html,
verified 2026-08-02).

**Compile-time checked query macro.** Rust SQLx provides a `query!` macro that
checks query arguments and database-specific placeholder syntax against a
database URL or offline metadata at build time
(https://docs.rs/sqlx/latest/sqlx/macro.query.html, verified 2026-08-02).
This variant catches missing arguments and some type mismatches earlier. It
costs build setup and may tie compilation to schema metadata.

## 9. Known production uses

**Java JDBC, `PreparedStatement`.** JDBC exposes `PreparedStatement` as a
standard Java SQL interface. The Oracle API describes it as a precompiled SQL
statement object, and its setter methods bind typed input parameter values
(https://docs.oracle.com/en/java/javase/17/docs/api/java.sql/java/sql/PreparedStatement.html,
verified 2026-08-02). This is a named production API used by Java applications
and frameworks on top of JDBC.

**Python standard library, `sqlite3`.** Python's `sqlite3` module documents
qmark and named placeholder styles for binding Python values to SQL statements,
and tells developers to use placeholders instead of string formatting to avoid
SQL injection (https://docs.python.org/3/library/sqlite3.html, verified
2026-08-02). This is a production use in the Python standard library.

**Go standard library, `database/sql`.** Go's `database/sql` package exposes
`Query`, `QueryContext`, `Stmt.Query`, `Stmt.Exec`, and related methods that
take query text plus arguments for placeholder parameters
(https://pkg.go.dev/database/sql, verified 2026-08-02). The Go database
querying guide shows values passed separately to a query and notes that
placeholder syntax varies by DBMS and driver
(https://go.dev/doc/database/querying, verified 2026-08-02).

**Prisma Client raw SQL.** Prisma Client's `$queryRaw` uses tagged templates and
documents that variables are turned into prepared statements, while
`$queryRawUnsafe` and `$executeRawUnsafe` carry injection risk when used with
user input. The same documentation also states that variables cannot stand in
for identifiers such as table names or SQL keywords
(https://www.prisma.io/docs/orm/prisma-client/using-raw-sql/raw-queries,
verified 2026-08-02).

**Rust SQLx.** SQLx documents `query` as executing a prepared statement with
transparent caching, and documents `.bind()` for dynamic input so the bound
value remains separate from query syntax (https://docs.rs/sqlx/latest/sqlx/fn.query.html,
verified 2026-08-02). Its `query!` macro adds compile-time checking for bind
parameters in supported setups (https://docs.rs/sqlx/latest/sqlx/macro.query.html,
verified 2026-08-02).

**Node.js SQLite.** Node's built-in `node:sqlite` module documents
`database.prepare` returning a prepared statement, `StatementSync` methods that
bind named and anonymous parameters, and a tag store where `${value}` binds a
parameter rather than interpolating it into SQL text (https://nodejs.org/api/sqlite.html,
verified 2026-08-02).

## 10. Consequences

Judgement. The consequences below are the practical effects a team should plan
for when adopting the pattern across a codebase.

Positive.

- SQL command structure no longer changes when a value contains quotes,
  comments, Boolean operators, semicolons, or other syntax characters.
- Review becomes simpler. A reviewer can look for values passed through the
  binding channel rather than evaluating dialect-specific escaping.
- Query logs and database statistics can group work by stable statement shape.
- Type conversion moves to the driver, which already has the database dialect
  contract.
- Repeated statements may benefit from prepared statement reuse or caching.
- Handling of null and binary values becomes explicit through the binding API.
- The pattern composes with least privilege, row-level authorization, and
  validation without mixing their responsibilities.
- A data-access wrapper can enforce the rule centrally and make violations easy
  to search for.

Negative.

- Dynamic SQL becomes more structured work. Optional filters, `IN` lists, and
  dynamic ordering need a builder that keeps SQL and values aligned.
- Placeholders cannot represent identifiers or syntax. Developers still need an
  allow-list path for those cases.
- Statement caches can consume database or proxy resources when query text has
  high cardinality.
- Logs that omit parameter values can slow debugging. Logs that include raw
  parameter values can leak personal or secret data.
- Type mismatches can change query plans, especially when the driver sends a
  wider type than the column or function expects.
- Some operations cannot be expressed through prepared statements in a given
  database or driver, which leaves a smaller but sharper reviewed escape path.
- A false sense of completion can appear. SQL injection risk drops, but
  authorization, output encoding, and second-order dynamic SQL still need
  separate controls.

## 11. Failure modes and misuse

Judgement. These failure modes are written as observable production and review
symptoms so a team can detect them.

**String interpolation before the safe API.** Symptom. A call appears to use
`query(sql, values)` or a tagged template, but the `sql` variable was assembled
earlier with `${userInput}`, `%s`, `format`, or concatenation. Cause. The team
checks the final database call name rather than tracing where the command text
was built. Fix. Make the wrapper accept a literal or query object, ban raw
strings from untrusted layers, and add static checks for interpolation in SQL
construction.

**Identifier binding attempted as a value.** Symptom. A developer tries
`ORDER BY ?` or `SELECT ? FROM users`, gets a syntax error, then falls back to
concatenating the request parameter. Cause. Placeholders were expected to bind
SQL syntax, but the API binds values. Fix. Map user choices to fixed fragments,
for example `{created: "created_at", email: "email"}`, and reject unknown keys.

**Parameter order drift.** Symptom. Search results are empty or strangely broad
only when certain optional filters are present. Logs show the statement has
three placeholders, but the second and third values are swapped. Cause.
Conditional SQL fragments and values are appended in different branches. Fix.
Use named parameters or a builder method that appends fragment and value in one
call.

**One value used as a fake list.** Symptom. A query `where id in (?)` returns no
rows for `"1,2,3"` or returns too many rows after a developer concatenates the
list directly. Cause. The code treats a single bound string as SQL list syntax.
Fix. Generate one placeholder per list item, bind each item, and set an upper
bound on list length.

**LIKE wildcard confusion.** Symptom. A search for `%` or `_` returns many
unexpected rows even though the query is parameterized. Cause. Parameterization
protects SQL syntax, but `%` and `_` still have meaning inside the LIKE
operator. Fix. Bind the value and escape LIKE metacharacters according to the
database's LIKE escape syntax, or use a search API with explicit query parsing.

**Unsafe stored procedure internals.** Symptom. The application binds procedure
arguments, but injection still occurs when a procedure executes concatenated
dynamic SQL. Cause. The boundary moved into the database routine. Fix. Use
database-side parameter binding in dynamic SQL, or replace dynamic execution
with fixed statements and allow-listed fragments.

**Prepared statement cache pressure.** Symptom. Database memory rises, proxy
logs show statement cache churn, or latency spikes after deploying a feature
with many unique statement texts. Cause. The code interpolates structural
fragments with high cardinality, or prepares many one-off statements without
closing them. Fix. Normalize statement shapes, cap cache sizes, close explicit
statements, and avoid preparing commands that will not repeat.

**Missing tenant predicate.** Symptom. A query is injection-safe but returns
another tenant's rows. Cause. The pattern was treated as a complete security
control. Fix. Add authorization predicates, database roles, row-level security
where appropriate, and tests that assert tenant isolation.

**Sensitive value logging.** Symptom. Password reset tokens, email addresses,
session ids, or access tokens appear in SQL logs or traces attached to bind
parameter arrays. Cause. Observability copied full bound values to aid
debugging. Fix. Log statement fingerprints, parameter count, coarse types, and
approved low-risk fields. Redact or hash the rest.

**Driver placeholder mismatch.** Symptom. The same query works in SQLite tests
with `?` but fails in PostgreSQL production, or values bind to different
positions after a driver change. Cause. Placeholder syntax was assumed to be
portable. Fix. Keep dialect-specific SQL close to the driver adapter, and test
against the production dialect for raw SQL paths.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Parameterized Query | Manual Escaping | Allow-list Identifier Mapping | ORM Expression API | Stored Procedure Parameters | Query Builder With Bindings |
|---|---|---|---|---|---|---|
| Security against value injection | Strong for value positions | Fragile, dialect specific | Not for values | Strong when used correctly | Strong when internals avoid dynamic SQL | Strong when builder keeps values separate |
| Dynamic identifiers | Not supported | Dangerous | Strong for small fixed sets | Usually limited | Possible inside procedure with care | Supported through trusted fragments |
| Correct handling of quotes and binary data | Driver-owned | Developer-owned | Not the concern | ORM-owned | Database-owned | Driver-owned |
| Review cost | Low at call boundary | High | Low for enum maps | Low until raw escape hatches | Medium, procedure body must be reviewed | Medium, builder correctness matters |
| Latency | Neutral to favourable | Neutral | Neutral | ORM dependent | May reduce round trips, may hide cost | Neutral |
| Operability | Stable statement fingerprints | Literal-heavy logs | Stable fragments | ORM generated names may be noisy | Work visible inside database | Stable when normalized |
| Team topology | Good shared rule | Poor, expert knowledge needed everywhere | Good for platform-owned options | Good for product teams | DBA and app teams share ownership | Good if wrapper is owned centrally |
| Cognitive load | Low for simple queries | High | Low for small choices | Low for common cases | Medium, logic split across tiers | Medium for dynamic queries |
| Data access portability | Driver dependent | Poor | Good if fragments vary by dialect | ORM dependent | Low to medium | Medium |
| Failure mode | Unsafe escape hatch for syntax | Missed escaping edge case | Missing default rejection | Raw SQL bypass | Dynamic SQL inside routine | SQL and value list drift |

Reading of the table. Parameterized Query is the default for runtime values.
Allow-list Identifier Mapping is the companion for runtime choices that select
syntax. ORM Expression API replaces hand-written parameterization when it can
express the query. Stored Procedure Parameters are a deployment and ownership
choice, not an automatic security upgrade. Manual Escaping is a retrofit option
when no binding API exists, and should be isolated behind a reviewed adapter.

## 13. Related and incompatible patterns

- **Input Validation.** Composes before it. Validation decides whether a value
  is allowed for the business action. Parameterized Query decides how that
  value crosses into SQL. Neither replaces the other.
- **Output Encoding.** Composes after it. Data safely read from the database can
  still cause cross-site scripting, log injection, command injection, or another
  SQL injection if placed into a later interpreter without the right encoding or
  binding.
- **Least Privilege.** Composes below it. If a query path is compromised through
  a missed raw string, least privilege limits what the database account can
  read or change. Parameterization reduces entry points. Least privilege limits
  blast radius.
- **Defense in Depth.** Hosts it as one layer. Parameterized Query should sit
  beside validation, authorization, database roles, safe error handling, and
  monitoring.
- **Secure by Default.** A data-access wrapper that exposes only parameterized
  calls is Secure by Default applied to SQL. Raw execution should be noisy in
  the type name, permission model, or code owner review.
- **Repository or Data Mapper.** Often hosts it. A repository method can hide
  database detail from domain code while still binding values internally. The
  repository must not accept raw SQL from callers unless it is a special reviewed
  abstraction.
- **Query Object.** Composes with it. A query object can carry trusted SQL
  fragments and a value list as one typed value, reducing parameter order drift.
- **Specification.** In domain code, specifications can describe predicates.
  The SQL adapter then translates those predicates into placeholders and bound
  values.
- **Client-side SQL escaping.** Conflicts as a default strategy. It keeps the
  unsafe representation, a single command string, and relies on every caller to
  remember dialect rules.
- **String-concatenated SQL.** Actively conflicts when it includes runtime data.
  Concatenation is acceptable only for trusted constants or allow-listed syntax
  fragments handled by a builder that still binds values.
- **Service Locator for database access.** Often conflicts in practice. If any
  code can grab a raw connection and run arbitrary strings, the parameterized
  wrapper becomes optional. The safer design makes the approved query API the
  ordinary dependency.

## 14. Refactoring path in and out

Introducing the pattern into a codebase with concatenated SQL.

1. Inventory database call sites. Search for `execute`, `query`, `raw`,
   `Statement`, `createQuery`, string interpolation, and concatenation near SQL
   keywords. Classify each call as fixed SQL, value injection risk, dynamic
   identifier, or raw admin feature.
2. Add characterization tests around the highest-risk queries. Include values
   containing apostrophes, comment markers, semicolons, percent signs, null, and
   tenant boundary cases. These tests should assert behaviour, not internal SQL
   strings.
3. Extract the SQL text into a local variable with placeholders. Move each
   runtime value into the binding API. Run the tests after each query.
4. For optional predicates, introduce a small builder that has one method per
   predicate and appends SQL plus value together. Do not let callers append SQL
   text and values through separate public methods.
5. Replace dynamic identifiers with enum or constant maps. The map values are
   trusted SQL fragments owned by code, not request values.
6. Centralize raw escape hatches behind an intentionally named API such as
   `unsafeQueryReviewed`. Require a reason, code owner review, and tests for
   every use.
7. Add static checks. Depending on the stack, use Semgrep, CodeQL, linter
   rules, or custom grep gates to reject string interpolation in SQL call sites.
8. Add observability for statement fingerprints, parameter counts, database
   errors, and rejected raw calls.
9. Remove old escaping helpers after the last caller is gone. If an escaping
   helper remains, developers will eventually use it as the easy path.

Named refactorings that often apply. Replace Magic Literal with Symbolic
Constant helps convert dynamic sort strings into named choices. Extract
Function helps isolate query construction. Replace Conditional with
Polymorphism can help when different query shapes correspond to different
business operations. Introduce Parameter Object can carry filters into a query
builder without passing a long list of nullable arguments.

Refactoring out when the pattern no longer belongs.

1. Confirm the query no longer has runtime values. A migration statement or a
   fixed health check may not need a binding API.
2. Keep the safe wrapper if it adds timeouts, logging, or policy. Removing
   parameters does not require bypassing the wrapper.
3. If raw SQL has become too hard to maintain, move up to an ORM expression API
   or a typed query builder. Verify that the generated SQL still binds values.
4. If a stored procedure now owns the operation, keep application arguments
   bound in the procedure call and review the procedure body for dynamic SQL.
5. Delete compatibility helpers that accepted both raw strings and parameterized
   forms. A dual API usually drifts back toward strings.

## 15. Testing and verification

Judgement. Tests should prove both security behaviour and ordinary correctness.
They should also prevent future contributors from reintroducing string-built
queries.

What becomes easier.

- Values with quotes, comments, and Boolean-looking text can be tested as
  ordinary data. The expected result is either one literal match or no match,
  not a syntax error and not a widened predicate.
- The SQL shape is stable, so tests can assert the statement text contains
  placeholders and the values array contains the untrusted data.
- Query builder tests can inspect the generated statement and bindings without
  opening a database connection.
- Contract tests can run the same injection payload corpus through every
  repository method that accepts user-controlled filters.

What becomes harder.

- Tests must know the target dialect's placeholder syntax. A query that compiles
  in SQLite may not be valid PostgreSQL raw SQL.
- Exact SQL string assertions can become brittle when a builder reorders
  predicates. Prefer normalized statement shape, parameter count, and behaviour
  assertions.
- Database logs may not contain raw parameter values, so integration test
  diagnostics need a safe way to expose values under test.

Techniques that apply.

- **Payload corpus.** Maintain a small suite of values such as `O'Brien`,
  `x' OR '1'='1`, `%`, `_`, `; select 1`, null, long strings, and Unicode
  strings. These are not magic attack strings. They are regression values that
  prove the command structure is stable.
- **Statement object test.** For builder code, assert that user-controlled data
  appears only in the values list, never in SQL text.
- **Dialect integration test.** Run raw SQL paths against the same database
  family used in production. Placeholder syntax and type inference differ.
- **Negative static test.** Add a fixture that intentionally interpolates a
  value into SQL and assert the linter or repository gate rejects it.
- **Tenant isolation test.** Pair parameterization tests with access-control
  tests. A query can be injection-safe and still overbroad.
- **Statement cache test.** For systems with explicit prepared statement
  caches, execute representative traffic and assert cache cardinality stays
  bounded.

The code examples below were compiled or run locally with the installed tools.
They are small by design. They demonstrate the boundary shape, not a full
database adapter.

## 16. Observability signals

Judgement. The pattern should be visible in telemetry without leaking sensitive
values.

Record these signals at the data-access boundary.

- Statement fingerprint or normalized SQL shape, with placeholders retained and
  values removed.
- Parameter count and coarse parameter types, such as string, integer, Boolean,
  timestamp, null, or bytes.
- Query duration, rows returned, rows affected, and error class.
- Whether the call used the approved parameterized path or a reviewed raw escape
  hatch.
- Prepared statement cache size, hit count, miss count, eviction count, and
  prepare errors where the driver exposes them.
- Rejected query construction events from static or runtime guards.
- For multi-tenant systems, tenant id as a separately authorized trace
  attribute, subject to the product's privacy rules.

A healthy dashboard shows a small set of stable statement fingerprints for a
given route or job, parameter counts matching expected query shapes, and no raw
escape hatch calls outside known maintenance paths. Query errors are dominated
by ordinary constraint and timeout errors, not syntax errors caused by broken
strings. Cache cardinality grows slowly after deploy and then levels off.

A failing dashboard looks different. A route emits many unique statement
fingerprints because values are embedded in SQL text. Syntax errors spike after
new search input reaches production. A raw escape hatch appears on a public
request route. Prepared statement cache entries grow with tenant count, search
terms, or request ids. Query logs include emails, tokens, or other values that
should have been redacted.

Logging policy matters. Log values only when a field has been classified for
that purpose, and prefer short hashes, value length, or type names over raw
content. Do not log secrets to prove parameterization works. The safer proof is
that the statement text has placeholders and the values are handled by the
binding channel.

## 17. Security and privacy implications

Parameterized Query closes one major class of injection path. OWASP lists
prepared statements with parameterized queries as a primary SQL injection
defense, and MITRE CWE-89 recommends parameterization where available
(https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html,
verified 2026-08-02; https://cwe.mitre.org/data/definitions/89.html, verified
2026-08-02). That does not make the database access layer safe by itself.

Security effects.

- It separates SQL code from data values, which prevents value text from
  becoming SQL grammar in supported value positions.
- It reduces reliance on hand-written escaping, a practice OWASP discourages as
  a primary SQL injection defense.
- It gives code review and static analysis a concrete boundary to inspect.
- It makes least privilege more valuable because missed raw paths become
  exceptions rather than the normal access style.

Security limits.

- It does not validate business meaning. A parameterized `amount = -100` can
  still be a business bug.
- It does not authorize access. A parameterized query can still omit the current
  user's scope.
- It does not bind identifiers or SQL keywords.
- It does not protect a stored procedure that concatenates its parameters into
  dynamic SQL and executes them.
- It does not encode output for HTML, JSON, shell commands, LDAP, or another
  interpreter.
- It does not neutralize wildcard semantics in LIKE or separate query languages
  embedded inside SQL functions.

Privacy effects.

- Stable statement text can reduce accidental leakage in SQL logs because
  values are not embedded in the command string.
- Bound values can still leak through driver debug logs, tracing middleware,
  database audit logs, or exception messages.
- Parameter names can reveal personal data categories, such as `ssn` or
  `reset_token`, even when values are redacted.
- Query fingerprints and row counts can become sensitive in small populations.
  A rare medical code or tenant-specific table choice can identify a person or
  organization even without raw parameter values.

Judgement. The safest policy is to treat SQL text, parameter metadata, and raw
parameter values as three different data classes. SQL text can usually be
logged. Parameter metadata often can be logged. Raw values need field-level
approval.

## 18. References

1. OWASP Cheat Sheet Series. "SQL Injection Prevention Cheat Sheet", sections
   "Primary Defenses" and "Defense Option 1: Prepared Statements (with
   Parameterized Queries)".
   https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
   Verified 2026-08-02. Source for the primary defense framing, prepared
   statement guidance, and warning against escaping as the main defense.
2. MITRE. CWE-89, "Improper Neutralization of Special Elements used in an SQL
   Command ('SQL Injection')", architecture and design mitigation section.
   https://cwe.mitre.org/data/definitions/89.html
   Verified 2026-08-02. Source for the CWE classification and parameterization
   mitigation guidance.
3. Oracle. Java SE 17 API Specification, `java.sql.PreparedStatement`.
   https://docs.oracle.com/en/java/javase/17/docs/api/java.sql/java/sql/PreparedStatement.html
   Verified 2026-08-02. Source for JDBC `PreparedStatement`, typed setter
   methods, and parameter marker behaviour.
4. Oracle. The Java Tutorials, "Using Prepared Statements", sections "Creating a
   PreparedStatement Object" and "Supplying Values for PreparedStatement
   Parameters".
   https://docs.oracle.com/javase/tutorial/jdbc/basics/prepared.html
   Verified 2026-08-02. Source for question mark placeholders, setting values,
   and repeated execution examples.
5. Python Software Foundation. Python 3 standard library documentation,
   `sqlite3`, section "How to use placeholders to bind values in SQL queries".
   https://docs.python.org/3/library/sqlite3.html
   Verified 2026-08-02. Source for qmark and named placeholder styles,
   parameter substitution, and arity behaviour.
6. The Go Authors. `database/sql` package documentation.
   https://pkg.go.dev/database/sql
   Verified 2026-08-02. Source for Go query methods, prepared statements, and
   placeholder parameter arguments.
7. The Go Authors. "Querying for data", Go database documentation.
   https://go.dev/doc/database/querying
   Verified 2026-08-02. Source for Go examples and DBMS-specific placeholder
   syntax notes.
8. PostgreSQL Global Development Group. PostgreSQL documentation, "Message
   Formats", `Parse` and `Bind` messages.
   https://www.postgresql.org/docs/current/protocol-message-formats.html
   Verified 2026-08-02. Source for protocol-level separation of statement text
   and parameter values.
9. Prisma. Prisma ORM documentation, "Raw queries".
   https://www.prisma.io/docs/orm/prisma-client/using-raw-sql/raw-queries
   Verified 2026-08-02. Source for tagged raw queries, unsafe raw methods, and
   the limit that variables cannot replace identifiers or SQL keywords.
10. SQLx project. Rust SQLx documentation, `sqlx::query`.
    https://docs.rs/sqlx/latest/sqlx/fn.query.html
    Verified 2026-08-02. Source for SQLx prepared execution, transparent
    caching, `.bind`, and database-specific placeholder syntax.
11. SQLx project. Rust SQLx documentation, `query!` macro.
    https://docs.rs/sqlx/latest/sqlx/macro.query.html
    Verified 2026-08-02. Source for compile-time checked bind parameters.
12. Node.js project. Node.js API documentation, `node:sqlite`.
    https://nodejs.org/api/sqlite.html
    Verified 2026-08-02. Source for `database.prepare`, `StatementSync`
    parameter binding, and tagged SQLite statement behaviour.

## Code examples

Three languages are shown because they represent different common shapes.
TypeScript shows a query object without a database dependency. Python uses the
standard `sqlite3` module against an in-memory database. Swift shows a typed
command value that keeps SQL text and values separate. Java is omitted from the
sample set because `javac` could not run in this environment, reporting that no
Java Runtime was available.

### TypeScript

```typescript
type SqlValue = string | number | boolean | null;

type Query = {
  text: string;
  values: SqlValue[];
};

function userByEmail(email: string): Query {
  return {
    text: "select id, email from users where email = ?",
    values: [email],
  };
}

function activeUsersByRole(role: string, limit: number): Query {
  return {
    text: "select id from users where role = ? and active = ? limit ?",
    values: [role, true, limit],
  };
}

const attack = "x' or '1'='1";
const query = userByEmail(attack);

console.log(query.text);
console.log(JSON.stringify(query.values));
console.log(activeUsersByRole("admin", 10).values.length);
```

### Python

```python
import sqlite3


def find_user(con: sqlite3.Connection, email: str) -> list[tuple[int, str]]:
    sql = "select id, email from users where email = ?"
    return list(con.execute(sql, (email,)))


con = sqlite3.connect(":memory:")
con.execute("create table users(id integer primary key, email text)")
con.execute("insert into users(email) values (?)", ("a@example.com",))
con.execute("insert into users(email) values (?)", ("x' or '1'='1",))

print(find_user(con, "a@example.com"))
print(find_user(con, "missing' or '1'='1"))
print(find_user(con, "x' or '1'='1"))
```

### Swift

```swift
enum SqlValue: CustomStringConvertible {
    case text(String)
    case int(Int)
    case bool(Bool)

    var description: String {
        switch self {
        case .text(let value): return value
        case .int(let value): return String(value)
        case .bool(let value): return String(value)
        }
    }
}

struct BoundQuery {
    let sql: String
    let values: [SqlValue]
}

func userByEmail(_ email: String) -> BoundQuery {
    BoundQuery(
        sql: "select id, email from users where email = ?",
        values: [.text(email)]
    )
}

func activeUsersByRole(_ role: String, limit: Int) -> BoundQuery {
    BoundQuery(
        sql: "select id from users where role = ? and active = ? limit ?",
        values: [.text(role), .bool(true), .int(limit)]
    )
}

let attack = "x' or '1'='1"
let query = userByEmail(attack)
print(query.sql)
print(query.values.map(\.description))
print(activeUsersByRole("admin", limit: 10).values.count)
```
