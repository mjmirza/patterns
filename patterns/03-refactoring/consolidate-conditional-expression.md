---
name: Consolidate Conditional Expression
slug: consolidate-conditional-expression
family: 03-refactoring
category: Refactoring
aliases: [Merge Conditional, Combine Conditions, Consolidate Conditionals]
first_described: "Fowler 1999"
maturity: canonical
related: [decompose-conditional, replace-nested-conditional-with-guard-clauses, consolidate-conditional-expression, extract-function, replace-conditional-with-polymorphism]
incompatible_with: []
verified: 2026-08-13
---

# Consolidate Conditional Expression

## 1. Name, aliases, and lineage

The canonical name is **Consolidate Conditional Expression**, introduced by
Martin Fowler in *Refactoring. Improving the Design of Existing Code*, 1st
edition, Addison-Wesley, 1999, chapter 9, "Simplifying Conditional
Expressions." The refactoring survived into the second edition, Martin
Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
edition, Addison-Wesley, 2018, chapter 10, "Simplifying Conditionals,"
under the same name and with the same mechanics. Fowler groups it with
Decompose Conditional and Replace Nested Conditional with Guard Clauses
in both editions, because the three refactorings form a family: you
split a conditional, you merge conditionals, and you flatten nested ones.

The alias **Merge Conditional** appears in the IntelliJ IDEA refactoring
menu, where the operation is offered as an inspection that detects a
series of conditionals with the same body and suggests merging them. The
alias **Combine Conditions** is used in the JavaScript community, where
short circuit evaluation is the mechanism and the merge is expressed
through the `||` and `&&` operators.

## 2. Problem and context

You have a series of conditional checks, each of which leads to the same
result or the same action. The checks are written as separate `if`
statements, each with its own body, but the bodies are identical. The
reader must scan each conditional to verify that the body is the same,
and a change to the body must be made in every copy, which is a
maintenance burden and a source of bugs when one copy is missed.

The situation reads like this. A function that calculates a disability
benefit has three separate checks that each return zero: if the person is
under 18, return zero. If the person has no contributions, return zero.
If the person is already retired, return zero. Each check is a separate
`if` statement with the same `return 0` body. A change to the zero
benefit amount, for example to return a nominal minimum instead of zero,
must be made in three places. A reader must verify all three to
understand when the benefit is zero, and there is no single expression
that communicates "the benefit is zero when any of these conditions hold."

The fix is to consolidate the conditions into a single conditional, using
the OR operator to combine the checks into one expression. The body
appears once, the conditions are visible in one place, and a change to
the body is made in one place.

## 3. Forces

**Readability versus detail.** A series of separate `if` statements makes
each condition individually visible, with its own body and its own
context. A consolidated conditional makes the combined condition visible
as a single expression, but the individual conditions are compressed into
one line. The force favours consolidation when the conditions are simple
and the combined expression is readable, and favours separation when the
conditions are complex enough that combining them produces an
unreadable expression.

**Maintenance versus performance.** A consolidated conditional has one
body, so a change to the body is made once. Separate conditionals have
multiple copies of the body, so a change must be made in every copy. The
force favours consolidation for maintainability, and is neutral on
performance, because short circuit evaluation in modern languages means
the consolidated form evaluates the same checks in the same order and
with the same cost.

**Short circuit semantics versus explicitness.** A consolidated
conditional using OR relies on short circuit evaluation: if the first
condition is true, the remaining conditions are not evaluated. This is
the same behaviour as separate `if` statements that each return, but it
is less explicit about the control flow. The force favours consolidation
when the short circuit behaviour is the desired behaviour, and favours
separation when the evaluation order has side effects that must be made
visible.

**Extractability versus inlinability.** A consolidated conditional is a
single expression, which can be extracted into a named function or a
boolean variable. Separate conditionals are statements, which cannot be
extracted as a single expression without first consolidating them. The
force favours consolidation when the combined condition would benefit
from a name, because the consolidation is the mechanical step that
enables the extraction.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- Two or more conditional checks lead to the same body, and the checks
  are related, not coincidental. The conditions represent different cases
  of the same decision, and combining them communicates that relationship.
- The checks are simple enough that the combined expression is readable.
  A combined expression with three short conditions joined by OR is
  readable. A combined expression with three complex subexpressions is
  not, and the refactoring would make the code harder to read.
- The body is duplicated across the checks, and the duplication is a
  maintenance burden. A change to the body must be made in every copy,
  and missing a copy is a bug.
- The combined condition would benefit from a name. After consolidating,
the expression can be extracted into a named function or a boolean
variable, which communicates the intent.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The checks are unrelated, even though they have the same body. The
  conditions represent different decisions that happen to have the same
  result, and combining them would communicate a relationship that does
  not exist.
- The combined expression is unreadable. Three conditions joined by OR
  with nested parentheses is harder to read than three separate `if`
  statements, and the refactoring would reduce clarity rather than
  increase it.
- The checks have different bodies that happen to be similar. The
  refactoring requires the bodies to be identical, not similar. If the
  bodies differ in any detail, consolidating the conditions would lose
  the difference, which is a bug.
- The evaluation order has side effects that must be visible. If a
  condition calls a function with a side effect, and the side effect
  must occur in a specific order, consolidating into a single expression
  hides the order behind short circuit evaluation.

## 5. Structure

The refactoring has one participant.

- **The conditionals.** A series of `if` statements, each with the same
  body. After the refactoring, they are combined into a single `if`
  statement whose condition is the OR of the original checks.

The invariant is that the consolidated conditional produces the same
result as the series of separate conditionals for every input. The
short circuit evaluation order of the OR operator must match the order
of the original checks.

## 6. ASCII structure diagram

```
  BEFORE                                  AFTER
  ------                                  -----

  if cond1:                               if cond1 or cond2 or cond3:
      return 0                                return 0
  if cond2:
      return 0
  if cond3:
      return 0

  (3 copies of "return 0")               (1 copy of "return 0")
```

## 7. Dynamics

```
  t0  identify series of conditionals with same body
       |
       v
  t1  verify the bodies are truly identical
       (not just similar, not just "return 0" when one
        returns 0 and another returns 0.0)
       |
       v
  t2  combine the conditions with OR
       -- in languages with short circuit OR:  cond1 || cond2 || cond3
       -- in languages without: check the language's evaluation rules
       |
       v
  t3  remove the duplicated bodies, keeping one
       |
       v
  t4  run test suite
       -- every input that triggered any of the original
          checks should now trigger the consolidated check
       |
       v
  t5  consider extracting the combined condition
       into a named function or boolean variable
       (this is the next refactoring, Extract Function)
       |
       v
  t6  commit. the conditionals are consolidated.
```

## 8. Implementation variants

**OR consolidation.** The canonical variant. The conditions are joined by
the OR operator, and the body appears once. This is the variant Fowler
describes in both editions, and it works when the original checks each
return the same value and the short circuit evaluation matches the
original order.

**AND consolidation for guard clauses.** When the original checks are
guard clauses that each prevent an error, and the body is a cleanup or
a no op, the conditions can be joined by AND to express that all guards
must pass. This is a less common variant, used when the checks are
inverted guards rather than positive conditions.

**Extract to named boolean.** After consolidating the conditions into a
single expression, the expression can be assigned to a named boolean
variable or extracted into a named function. This is the Extract Function
or Introduce Explaining Variable variant, and it is the natural next
step when the combined expression is long enough to warrant a name.

```python
# Python: before (separate checks, same body)

def disability_amount(person):
    if person.age < 18:
        return 0
    if person.contributions == 0:
        return 0
    if person.is_retired:
        return 0
    # ... calculate amount
    return amount

# Python: after (consolidated with OR)

def disability_amount(person):
    if person.age < 18 or person.contributions == 0 or person.is_retired:
        return 0
    # ... calculate amount
    return amount

# Python: further (extract to named boolean)

def is_not_eligible(person):
    return person.age < 18 or person.contributions == 0 or person.is_retired

def disability_amount(person):
    if is_not_eligible(person):
        return 0
    # ... calculate amount
    return amount
```

```typescript
// TypeScript: before (separate checks)

function disabilityAmount(person: Person): number {
    if (person.age < 18) return 0;
    if (person.contributions === 0) return 0;
    if (person.isRetired) return 0;
    return calculateAmount(person);
}

// TypeScript: after (consolidated)

function disabilityAmount(person: Person): number {
    if (person.age < 18 || person.contributions === 0 || person.isRetired) {
        return 0;
    }
    return calculateAmount(person);
}
```

```java
// Java: before (separate checks with AND for guards)

public double disabilityAmount(Person person) {
    if (person.getAge() >= 18
            && person.getContributions() > 0
            && !person.isRetired()) {
        return calculateAmount(person);
    }
    return 0;
}

// Java: after (extracted named method)

private boolean isEligible(Person person) {
    return person.getAge() >= 18
            && person.getContributions() > 0
            && !person.isRetired();
}

public double disabilityAmount(Person person) {
    if (isEligible(person)) {
        return calculateAmount(person);
    }
    return 0;
}
```

## 9. Known production uses

**IntelliJ IDEA's inspection "Conditional with identical branches"**
detects the pattern this refactoring targets and offers to consolidate
the conditions automatically. JetBrains documents that the inspection
identifies a series of `if` statements with the same body and suggests
merging them into a single conditional
([JetBrains Inspections](https://www.jetbrains.com/help/idea/code-inspection.html),
verified 2026-08-13). This is the production realisation of the
refactoring at the IDE level, and it is the tool most Java developers
use to apply it.

**SonarQube rule S1066, "Collapsible if statements"** detects a related
pattern where two nested `if` statements can be collapsed into one, and
it is the inspection that catches the case where the conditions are
nested rather than sequential
([SonarSource rule S1066](https://rules.sonarsource.com/java/rspec-S1066/),
verified 2026-08-13). The rule is the complementary inspection to the
OR consolidation variant, because it handles the AND case where two
nested conditions are combined.

## 10. Consequences

Positive.

- The duplicated body appears once, which eliminates the maintenance
  burden of keeping copies in sync.
- The combined condition communicates that the checks are related cases
  of the same decision, which is information the separate conditionals
  do not communicate.
- The combined condition can be extracted into a named function, which
  gives the decision a name in the code.
- The short circuit evaluation of the OR operator produces the same
  behaviour as the separate conditionals with the same evaluation order.

Negative.

- The individual conditions are compressed into one expression, which is
  less readable when the conditions are complex.
- The short circuit evaluation order is implicit in the OR operator,
  which is less explicit than separate `if` statements for a reader who
  needs to understand which conditions are evaluated.
- The combined expression may be long, which pushes the line past a
  readable width and requires formatting choices that may obscure the
  structure.

## 11. Failure modes and misuse

**Consolidating conditions with different bodies.** The bodies appear
identical but are subtly different, for example one returns `0` and
another returns `0.0`, which are equal in most languages but not in all
type systems. The consolidation loses the difference, which is a bug
that is invisible in the diff because the bodies looked the same.

**Consolidating unrelated conditions.** The conditions have the same
body by coincidence, not by relationship. Combining them into a single
conditional communicates that the conditions are cases of the same
decision, which is false. A future reader who sees the combined
conditional will assume a relationship and may reason incorrectly about
the code.

**Consolidating conditions with side effects.** A condition calls a
function with a side effect, and the short circuit evaluation of the OR
operator means the function is not called when an earlier condition is
true. The original separate `if` statements always evaluated every
condition, so the side effect always occurred. The consolidation
silently removes the side effect for some inputs, which is a behaviour
change.

**Over-consolidation.** The combined expression is long and unreadable,
and the refactoring has reduced clarity rather than increased it. The
symptom is a single line with five conditions joined by OR, which no
reader can parse at a glance, and which should have been left as
separate checks or extracted into a named function before combining.

## 12. Trade-off matrix

| Alternative | Duplication | Readability | Extractability | When to prefer |
|---|---|---|---|---|
| Consolidate Conditional Expression | Eliminated | Higher for simple conditions | Enables extraction | Same body, related conditions, readable combined |
| Decompose Conditional | None | Higher for complex conditionals | N/A | A single complex conditional needs splitting |
| Extract Function on conditions | None | Highest, condition has a name | The extraction itself | The combined condition is long enough to warrant a name |
| Replace Conditional with Polymorphism | Eliminated | Highest, removes conditional entirely | N/A | The conditional dispatches on type, and polymorphism is better |

## 13. Related and incompatible patterns

**Decompose Conditional** (same catalog) is the inverse. It splits a
complex conditional into separate named functions for the condition, the
then branch, and the else branch. The two refactorings are applied in
opposite directions: Consolidate merges, Decompose splits. The choice
depends on whether the condition is too simple (merge) or too complex
(split).

**Replace Nested Conditional with Guard Clauses** (same catalog) is the
alternative when the conditionals are nested rather than sequential.
Guard clauses flatten the nesting by returning early, which is a
different restructuring from consolidating the conditions into one
expression.

**Extract Function** (same catalog) is the natural next step after
consolidation. The combined condition can be extracted into a named
function, which gives the decision a name and removes the expression
from the caller's body. The two refactorings are frequently applied
together: consolidate, then extract.

**Replace Conditional with Polymorphism** (same catalog) is the
alternative when the conditional dispatches on type. If the conditions
check `type == X`, `type == Y`, and `type == Z`, polymorphism is a
better structure than consolidating the conditions, because the
polymorphic dispatch removes the conditional entirely.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by combining the conditions
into a single conditional. The steps are:

1. Identify the series of `if` statements with the same body.
2. Verify the bodies are identical, not just similar. Check return
   types, return values, and any code after the return.
3. Combine the conditions with the OR operator, preserving the original
   order.
4. Remove the duplicated bodies, keeping one.
5. Run the test suite. Any failure means either the bodies were not
   identical or the short circuit evaluation order differs from the
   original.
6. Consider extracting the combined condition into a named function or
   a boolean variable if the expression is long.

**Path out.** The refactoring is reversed by Decompose Conditional or by
splitting the combined expression back into separate `if` statements. The
reverse is applied when the combined expression is unreadable or when the
conditions turn out to be unrelated and the consolidation communicated a
false relationship.

## 15. Testing and verification

The test suite is the primary verification. After the consolidation,
every test that triggered any of the original checks should now trigger
the consolidated check and should produce the same result. A test
failure means either the bodies were not identical or the short circuit
evaluation order differs from the original.

A new test should verify the short circuit evaluation order. If the
conditions call functions with side effects, a test should verify that
the side effects occur in the expected order and that the short circuit
does not skip a side effect that the original separate checks always
produced.

A test that checks the boundary between conditions should verify that
an input that satisfies exactly one condition triggers the body, and
an input that satisfies multiple conditions triggers the body exactly
once (which is guaranteed by the single conditional).

## 16. Observability signals

The consolidation does not change behaviour, so the observable signal in
production is nothing. The same inputs produce the same outputs. If
production observability changes, the consolidation introduced a
behaviour change, and the difference is the signal that the bodies were
not identical or that the short circuit evaluation removed a side
effect.

The one observable difference is in code coverage. The consolidated
conditional has one branch where the original had multiple branches, and
a coverage tool that reported each `if` statement separately now reports
one conditional. The coverage percentage may change because the
consolidated conditional has two paths (the condition is true or false)
where the original series had multiple paths. This is a reporting
difference, not a behaviour difference.

## 17. Security and privacy implications

The consolidation does not change what data is checked or what action is
taken, so it does not change the security surface. The security relevant
case is when the conditions are security checks, for example checking
whether a user is authorised, and the consolidation makes the checks
visible as a single expression. A caller that sees `if isNotAuthorised`
can understand the security boundary, where separate `if` statements
might obscure that the checks are related security conditions.

The privacy relevant case is when the conditions check data handling
preferences, for example whether a user has opted out of tracking. The
consolidation makes the opt out checks visible as a group, which is a
positive privacy signal because it makes the privacy boundary visible
in the code.

Where the refactoring is silent is in the conditions themselves: the
checks are the same checks in a different structure. The data that is
checked, the action that is taken, and the consequences for the user are
unchanged.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 10, "Consolidate Conditional
  Expression."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 9, "Consolidate Conditional
  Expression."
- JetBrains, "Code Inspection,"
  [https://www.jetbrains.com/help/idea/code-inspection.html](https://www.jetbrains.com/help/idea/code-inspection.html),
  verified 2026-08-13.
- SonarSource, "Collapsible if statements," rule S1066,
  [https://rules.sonarsource.com/java/rspec-S1066/](https://rules.sonarsource.com/java/rspec-S1066/),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
