---
name: Collecting Parameter
slug: collecting-parameter
family: 06-enterprise-application-architecture
category: Enterprise Application Architecture
aliases: [Move Accumulation To Collecting Parameter, Accumulator Parameter]
first_described: "Joshua Kerievsky, Refactoring to Patterns, Addison-Wesley, 2004, plus the c2.com wiki community page, both current"
maturity: established
related: [visitor]
incompatible_with: []
verified: 2026-08-23
---

# Collecting Parameter

## 1. Name, aliases, and lineage

A collecting parameter is a mutable object, most often a collection, that
is passed into a series of method calls purely so each call can append to
it, rather than each call returning its own result and the caller
assembling those results itself.

This entry sources it directly from two current, live sources. The
c2.com wiki's own community page, fetched live from its raw data
endpoint, names the idiom directly. "in the CollectingParameter idiom a
collection (list, map, etc.) is passed repeatedly as a parameter to a
method which adds items to the collection" (WikiWikiWeb community,
"CollectingParameter," c2.com wiki,
https://c2.com/wiki/remodel/pages/CollectingParameter, last edited
December 2, 2014, verified 2026-08-23). Industrial Logic's own current
refactoring catalog, Joshua Kerievsky's own company, names the paired
refactoring directly under a different, more specific title. "you have a
single bulky method that accumulates information to a local variable...
accumulate results to a Collecting Parameter that gets passed to
extracted methods" (Industrial Logic, "Move Accumulation To Collecting
Parameter," Refactoring to Patterns catalog,
https://www.industriallogic.com/refactoring-to-patterns/catalog/accumulationToCollection.html,
verified 2026-08-23).

## 2. Problem and context

A single bulky method accumulates a result into a local variable across a
long, linear sequence of steps, which is exactly the shape Industrial
Logic's own text names directly, already quoted in dimension 1, and the
usual first response, extracting each step into its own smaller method,
runs into a shared-state problem. each extracted method needs write
access to the very same accumulator the others are writing to, so
returning each step's own local result and stitching them together in the
caller is not always the natural shape once the extraction happens.

## 3. Forces

The c2.com wiki's own text names the central tension directly, in two
separate contributed passages on the same page. one contributor frames it
as a legitimate technique. "the practice of passing around a collecting
parameter can be generalized to using a static closure... it can be used
beneficially to decouple the state from the method invocation." a second
contributor frames the same underlying shape as risky the moment it
generalizes past a simple collection. "a variation on this pattern occurs
when the CollectingParameter is not a collection, but is an object with
various properties... I think this version of the pattern is generally an
AntiPattern" (WikiWikiWeb community, "CollectingParameter," verified
2026-08-23). the tension is not whether to pass a mutable accumulator, it
is how far that accumulator's own responsibility is allowed to grow before
the convenience curdles into a hidden dependency between otherwise
unrelated methods.

## 4. Applicability and non-applicability

The c2.com wiki's own text names a concrete non-applicability case
directly, already quoted in dimension 3, a collecting parameter that
carries settable PROPERTIES rather than only accumulating entries into a
collection is named directly as "generally an AntiPattern," reserved, in
the same contributor's own words, for the narrow case of "refactoring from
the use of globals" rather than as a general design choice. Industrial
Logic's own catalog page names the applicability condition directly under
dimension 1 and 2, a single bulky method whose logic is being split into
smaller extracted methods that must still write to one shared
accumulating result.

## 5. Structure

Industrial Logic's own catalog names the exact structural move directly,
already quoted in dimension 1 and 2, a local accumulator variable becomes
a parameter threaded through every extracted method, rather than staying
private to one bulky method. The c2.com wiki's own text names a second,
distinct structural variant, an object passed for its callers to invoke
add or append style methods on, which the same source directly compares
to "an ouput iterator" in the C++ standard library sense, or to Java's own
"java.lang.Appendable" interface (WikiWikiWeb community,
"CollectingParameter," verified 2026-08-23), a structural family that
accepts appended items without exposing its own full contents to every
caller.

## 6. ASCII structure diagram

```
  Before, one bulky method owns the accumulator:

  +----------------------------------------------+
  | bulkyMethod()                                   |
  |   result = new Collection()                     |
  |   step1 appends to result                        |
  |   step2 appends to result                        |
  |   step3 appends to result                        |
  |   return result                                  |
  +----------------------------------------------+

  After, the accumulator is threaded through extracted methods:

  +--------------+     +--------------+     +--------------+
  | step1(result) | --> | step2(result) | --> | step3(result) |
  +--------------+     +--------------+     +--------------+
        |                    |                    |
        +--------------------+--------------------+
                             v
                  the SAME result object,
                  appended to by each step in turn,
                  per dimension 5
```

## 7. Dynamics

The extracted methods in dimension 5 and 6 run in a fixed sequence, and
because each one holds a reference to the SAME collecting parameter, an
append made by an earlier step is visible to a later step, which is the
entire point of the technique, per dimension 2. the c2.com wiki's own
text names the runtime consequence of the risky property-object variant
directly, already quoted in dimension 3 and 4, "as the object is passed
around, various actors get and set properties on the ParameterObject,"
which means the object's state at any point in the call chain depends on
every caller that has already touched it, not only on its own local
logic.

## 8. Implementation variants

This entry confirmed two genuinely distinct implementation variants
directly. Industrial Logic's own named refactoring recipe, extracting a
method from a bulky procedure and threading a plain collection through it
as a parameter, per dimension 1, 2, and 5. The c2.com wiki's own named
variant, generalizing the collecting parameter "to using a static
closure, instantiating the functions that add to the collection so that
they get the collector implicitly" (WikiWikiWeb community,
"CollectingParameter," verified 2026-08-23), an object-oriented shape
rather than a bare parameter passed explicitly at every call site.

## 9. Known production uses

The c2.com wiki's own text names a concrete, real production use
directly. "another example is the TestResult in JUnit" (WikiWikiWeb
community, "CollectingParameter," verified 2026-08-23), JUnit's own
`TestResult` object being passed into a chain of test-running calls that
each append their own pass, fail, or error outcome to it.

## 10. Consequences

The benefit is stated directly, already implied under dimension 2 and 5.
a bulky method can be split into smaller, individually named steps
without each step needing to return and re-assemble its own partial
result, because they all write to the one threaded accumulator. the cost
is the named risk under dimension 3, 4, and 7, the technique generalizes
easily from a safe, narrow collection-only shape into a property-bag
object whose state depends on an implicit, order-sensitive sequence of
callers, which the wiki's own contributors name directly as an
AntiPattern once it crosses that line.

## 11. Failure modes and misuse

The sharpest, most directly sourced failure mode is the property-object
generalization already quoted in full under dimension 3 and 4, a
collecting parameter that carries settable properties rather than only
accumulated entries creates "stateful dependencies across methods that
should have been grouped into the same object if they truly need such
stateful information, and otherwise receiving and acting on state they
shouldn't access" (WikiWikiWeb community, "CollectingParameter," verified
2026-08-23), a direct, named description of the coupling this variant
introduces.

## 12. Trade-off matrix

| Dimension | Collecting parameter, collection-only | Collecting parameter, property-object variant |
|---|---|---|
| Named verdict in the source | Established technique, dimension 1 and 2 | "Generally an AntiPattern," dimension 3 and 4 |
| State each caller can see | Only appended entries | Arbitrary gettable and settable properties |
| Coupling between extracted methods | Bounded to appending, dimension 5 | Order-sensitive, implicit, dimension 7 and 11 |
| Legitimate narrow use named in the source | General accumulation, JUnit's TestResult, dimension 9 | Refactoring away from globals only, dimension 4 |

## 13. Related and incompatible patterns

This entry cross-references this catalogue's own already published
Visitor entry, per Industrial Logic's own catalog page listing "Move
Accumulation To Visitor" directly alongside "Move Accumulation To
Collecting Parameter" as a sibling refactoring in the same family
(Industrial Logic, "Move Accumulation To Collecting Parameter," verified
2026-08-23), the two sharing the same underlying problem, a bulky method
accumulating a result, resolved by two different structural moves.

## 14. Refactoring path in and out

Industrial Logic's own catalog names the concrete lever directly, already
quoted in dimension 1 and 2, extracting the accumulating steps of a bulky
method into their own methods and threading the accumulator through them
as a parameter. The reverse lever, named directly by the c2.com wiki's own
risk framing under dimension 3 and 4, is collapsing a property-object
collecting parameter back down to a plain, narrowly scoped collection, or
promoting it to its own real, encapsulated object once its
responsibilities have genuinely grown past simple accumulation.

## 15. Testing and verification

This entry explicitly checked the fetched sources for a documented test
methodology specific to this pattern and did not find one described as a
formal process. the closest verifiable behavior is the named JUnit
`TestResult` production use under dimension 9, itself a collecting
parameter threaded through a chain of test-running calls, which a test of
this pattern's own correctness would exercise by confirming every
appending step's contribution is present in the final accumulated result,
in the order the steps ran.

## 16. Observability signals

This entry explicitly checked the fetched sources for a named metric or
dashboard specific to this pattern and did not find one described on the
specific pages fetched. the closest directly sourced signal is the
named boundary between the collection-only and property-object variants
under dimension 3, 4, and 12, which a reviewer could check for directly
in code review, whether a "collecting parameter" only ever receives
appended entries or whether callers are also reading and writing named
properties on it.

## 17. Security and privacy implications

This entry explicitly checked the fetched sources for a security or
privacy discussion specific to this pattern and did not find one
addressed on the specific pages fetched. this entry reports that absence
directly rather than asserting a security property neither source states.

## 18. References

1. WikiWikiWeb community, "CollectingParameter," c2.com wiki,
   https://c2.com/wiki/remodel/pages/CollectingParameter, last edited
   December 2, 2014, verified 2026-08-23.
2. Industrial Logic, "Move Accumulation To Collecting Parameter,"
   Refactoring to Patterns catalog,
   https://www.industriallogic.com/refactoring-to-patterns/catalog/accumulationToCollection.html,
   verified 2026-08-23.

## Code

TypeScript, Python, and Go implementations of the collection-only variant
following the mechanism from dimensions 2, 5, and 6, threading a
collecting parameter through a series of extracted steps rather than
letting one bulky method own the accumulation.

```typescript
interface RawUserFile {
  fileName: string;
}

interface User {
  fileName: string;
  loaded: boolean;
}

function addUsersTo(userFile: RawUserFile, userList: User[]): void {
  userList.push({ fileName: userFile.fileName, loaded: true });
}

function loadAllUsers(userFiles: RawUserFile[]): User[] {
  const userList: User[] = [];
  for (const userFile of userFiles) {
    addUsersTo(userFile, userList);
  }
  return userList;
}
```

```python
from dataclasses import dataclass
from typing import List


@dataclass
class RawUserFile:
    file_name: str


@dataclass
class User:
    file_name: str
    loaded: bool


def add_users_to(user_file: RawUserFile, user_list: List[User]) -> None:
    user_list.append(User(file_name=user_file.file_name, loaded=True))


def load_all_users(user_files: List[RawUserFile]) -> List[User]:
    user_list: List[User] = []
    for user_file in user_files:
        add_users_to(user_file, user_list)
    return user_list
```

```go
package collectingparameter

type RawUserFile struct {
	FileName string
}

type User struct {
	FileName string
	Loaded   bool
}

func addUsersTo(userFile RawUserFile, userList []User) []User {
	return append(userList, User{FileName: userFile.FileName, Loaded: true})
}

func loadAllUsers(userFiles []RawUserFile) []User {
	userList := make([]User, 0, len(userFiles))
	for _, userFile := range userFiles {
		userList = addUsersTo(userFile, userList)
	}
	return userList
}
```
