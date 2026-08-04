# Family 14. Testing

Origin. Meszaros, xUnit Test Patterns

23 entries, 165,889 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Test Data

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Derived Value](derived-value.md) | canonical | 5,157 | A test needs data. Every object under test, and every collaborator it talks to, has fields that must be filled in before the test can run, and the overwhelming majority of those ... |
| [Generated Value](generated-value.md) | canonical | 6,233 | A fixture object almost always has more fields than the test actually cares about. |

## Test Double

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Dummy](dummy.md) | canonical | 6,531 | A constructor, a factory function, or a method signature requires an argument of a particular type, but the code path being exercised by a specific test does not use that argument ... |
| [Fake](fake.md) | canonical | 6,405 | A piece of code depends on a collaborator that is real, correct, and slow, or real, correct, and hard to set up. |
| [Mock](mock.md) | canonical | 6,117 | A unit of code under test calls a method on a collaborator, and the whole reason the test exists is to prove that call happens, with the right arguments, in the right ... |
| [Stub](stub.md) | canonical | 9,016 | Code under test frequently depends on something the test cannot, or should not, use as it really behaves. |

## Test Structure

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Four-Phase Test](four-phase-test.md) | canonical | 7,168 | A test method's job is to answer one question unambiguously, did the behaviour under test do the right thing. |

## Testing

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Approval Test](approval-test.md) | established | 7,682 | Consider a function that renders an invoice as HTML, a compiler pass that lowers an abstract syntax tree to bytecode, a report generator that produces a multi-page PDF summary, or ... |
| [Arrange-Act-Assert](arrange-act-assert.md) | canonical | 6,255 | A test that has no imposed shape tends to accrete in whatever order the writer thought of things. |
| [Characterization Test](characterization-test.md) | canonical | 6,420 | A team inherits a module, a service, or a whole codebase with no tests, or with tests too sparse to trust. |
| [Contract Test](contract-test.md) | canonical | 8,408 | A team splits a monolith into services, or simply has two teams shipping two deployables that talk over HTTP, gRPC, or a message queue. |
| [Fresh Fixture](fresh-fixture.md) | canonical | 7,305 | A test needs an environment in which to run its assertions, objects to act on, data in a database, files on disk, a running process. |
| [Given-When-Then](given-when-then.md) | canonical | 7,476 | A test file with no shape reads as an undifferentiated block of setup calls, one action, and a pile of assertions, and a reader cannot tell at a glance which lines are ... |
| [Golden Master](golden-master.md) | established | 7,989 | A piece of code produces output that is expensive or awkward to specify by hand, one field at a time, and a person needs confidence that a change to the code did not alter that ... |
| [Humble Object](humble-object.md) | canonical | 7,022 | Some classes are hard to unit test not because their logic is hard, but because constructing or invoking them at all requires something a fast, isolated test cannot or should not ... |
| [Mutation Test](mutation-test.md) | canonical | 8,102 | A test suite that exercises every line and every branch of a program can still fail to notice when the program is wrong. |
| [Object Mother](object-mother.md) | established | 6,582 | A test needs an object in a known, valid state before it can exercise the behavior under test. |
| [Prebuilt Fixture](prebuilt-fixture.md) | canonical | 7,102 | A test needs the system under test to start from a known state before its assertions can mean anything. |
| [Property-Based Test](property-based-test.md) | canonical | 7,086 | A function or a module has a genuine algebraic or structural invariant, and an author trying to test it by hand can only ever write down the handful of inputs they personally ... |
| [Shared Fixture](shared-fixture.md) | canonical | 8,501 | A test needs a fixture. The object under test needs collaborators wired up, a database needs rows in it that match the scenario, a file needs to exist on disk, an external service ... |
| [Snapshot Test](snapshot-test.md) | established | 9,149 | A function, a component, or an API endpoint produces an output that is correct today, and the author knows it is correct today because they looked at it, ran it, or eyeballed a ... |
| [Spy](spy.md) | canonical | 7,242 | A unit under test collaborates with something outside itself, a payment gateway, an email service, a logger, an event bus, a cache. |
| [Test Data Builder](test-data-builder.md) | canonical | 6,941 | A domain object has enough constructor parameters, or enough invariants, that constructing one directly in a test is either impossible without a long argument list or actively ... |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
