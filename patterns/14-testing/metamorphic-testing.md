---
name: Metamorphic Testing
slug: metamorphic-testing
family: 14-testing
category: Testing
aliases: [Metamorphic Relation Testing, MR-based Testing]
first_described: "Chen, Cheung, Yiu 1998"
maturity: established
related: [property-based-test, mutation-test, golden-master, characterization-test, contract-test]
incompatible_with: []
verified: 2026-08-02
---

# Metamorphic Testing

## 1. Name, aliases, and lineage

The canonical name is metamorphic testing. It was introduced by T. Y. Chen,
S. C. Cheung and S. M. Yiu in the technical report "Metamorphic Testing.
A New Approach for Generating Next Test Cases", Technical Report
HKUST-CS98-01, Department of Computer Science, The Hong Kong University of
Science and Technology, 1998
(https://en.wikipedia.org/wiki/Metamorphic_testing, verified 2026-08-02).
The report's own framing is that a test suite should not stop at one input
and one expected output. it should also generate a follow-up input from the
first one and check a relation between the two outputs, hence
"metamorphic". a test case morphs into a next one under a known rule.

In the literature the technique is sometimes written as MR-based testing,
short for metamorphic-relation-based testing, and the core object it checks
is called a metamorphic relation, abbreviated MR throughout this entry. A
widely cited secondary source that codified the vocabulary used across the
field, including the MR terminology and the taxonomy of relation types cited
in dimension 8, is Sergio Segura, Gordon Fraser, Ana B. Sanchez and Antonio
Ruiz-Cortés, "A Survey on Metamorphic Testing", IEEE Transactions on
Software Engineering, vol. 42, no. 9, 2016. The name is not contested. every
paper in the area uses metamorphic testing and metamorphic relation as the
settled terms.

## 2. Problem and context

Some programs have no practical way to check whether a single output is
correct. A search engine ranking function, a machine translation system, a
compiler's optimizer, an image classifier, a numerical solver for a
differential equation, a route planner over real road data. for every one of
these, writing down the exact expected output for an arbitrary input is
either mathematically undecidable, prohibitively expensive to compute by an
independent method, or dependent on a judgment call nobody can encode as a
single correct string.

This is the oracle problem, named and analysed by Elaine J. Weyuker in "On
Testing Non-Testable Programs", The Computer Journal, vol. 25, no. 4, 1982,
pages 465 to 470. Weyuker's point is that a program can be perfectly
testable in the sense that it runs and produces output, while still being
untestable in the sense that no independent computation exists to say
whether that output is right. A payroll system is testable. you can compute
the expected paycheck by hand. A square root routine used inside a physics
simulation is testable. you can square the result and compare. A neural
network that classifies road signs from a camera frame is not. there is no
independent formula for the correct classification of an arbitrary photo.

Metamorphic testing answers the oracle problem without inventing an oracle.
Instead of asking whether a single output is correct, it asks whether an
output relates to another output the way the specification says it must. If
a translation service translates "the cat sat on the mat" to some German
sentence, nobody can cheaply verify that sentence is the one true correct
translation. But if the same service is asked to translate "the cat and the
dog sat on the mat", the specification of what translation even means
implies the second output should still contain a rendering of "sat on the
mat" and should not contradict the first translation's choice of vocabulary
for "cat". That relation between two related inputs and their two outputs is
checkable even when neither individual output is.

The context in which metamorphic testing earns its place has three
features together. the system under test has no cheap independent oracle,
the system's own specification or informal understanding of its purpose
implies a relation between related inputs, and that relation is precise
enough to be coded as a boolean check.

## 3. Forces

Judgment. the weighting below reflects how the technique trades off in
practice, not a formula from the original papers.

- **Oracle cost versus coverage.** Favoured heavily. Metamorphic testing
  trades a hard problem, computing the correct answer, for an easier one,
  computing whether two answers are consistent. It buys real coverage of an
  otherwise untestable system at the cost of specifying relations instead of
  exact values.
- **Precision of the check.** Sacrificed relative to an exact oracle. A
  metamorphic relation is typically a necessary property of correctness, not
  a sufficient one. A system can satisfy every known relation and still be
  wrong in a way no relation captures, per dimension 10 and dimension 11.
- **Domain expertise required.** Sacrificed. Writing a useful relation
  demands understanding what the specification actually implies about
  related inputs, which is harder than writing an example-based assertion
  and is the main place teams underinvest.
- **Test input growth.** Neutral to favoured. Once a relation exists, it can
  be checked against arbitrarily many seed inputs with almost no additional
  authoring cost, because the follow-up input and the relation are generated
  mechanically from the seed.
- **Bug class coverage.** Sacrificed on one axis, favoured on another. A
  relation only catches violations of that specific relation, so a suite
  needs several independent relations to approach the coverage a full oracle
  would give in one shot, per the search example worked through in dimension
  6 and dimension 11. In exchange it catches bugs that involve interactions
  across inputs, order sensitivity, scaling behaviour, which single-example
  tests structurally cannot see because they check one input at a time.
- **Ease of automation.** Favoured. Because the relation is a program, not
  a data table, it composes naturally with property-based test generators,
  per dimension 13, and with fuzzers, which can supply the seed corpus a
  relation needs.

## 4. Applicability and non-applicability

When to reach for it.

- The system under test has no independent, cheap way to compute the
  correct output for an arbitrary input, and building one would be as hard
  as the system itself. machine learning inference, compiler optimization,
  search and ranking, simulation, numerical solvers.
- The specification, even an informal one, implies an invariant relation
  between the outputs of related inputs. permutation invariance, scaling,
  monotonic narrowing, idempotence, symmetry.
- The system is a black box, third party, or otherwise not open to internal
  instrumentation, so techniques that need visibility into intermediate
  state are unavailable.
- A regression suite already exists for the easy cases and the team wants to
  catch bugs in the parts of the input space example tests structurally
  cannot enumerate.

When not to reach for it, with the reason.

- The system has a genuine, cheap independent oracle. a parser for a
  well-defined grammar, a calculator, a sorting routine with a known correct
  comparator. Writing exact expected-output tests is cheaper to write, read,
  and diagnose than deriving and coding a relation, and gives a sufficient
  rather than merely necessary check. Use ordinary example-based testing.
- The domain has no discoverable relation. some systems genuinely have no
  invariant a domain expert can state with confidence, and forcing one
  invented for the sake of the technique produces a relation nobody trusts
  and that catches nothing real.
- The team cannot afford the domain-analysis cost. a weak or wrong relation
  that is trusted as if it were strong is worse than no metamorphic test at
  all, because it creates false confidence, a real observed failure mode,
  see dimension 11.
- A failure needs to be pinpointed to an exact expected value for a
  regulatory or contractual reason, for example a tax calculation that must
  match a published table exactly. A relation tells you two outputs are
  inconsistent. it does not tell you which one, or either, is correct. Pair
  it with golden-master or characterization-test for that need, per
  dimension 13, or use those instead if that is the whole problem.
- The relation, once found, degenerates to checking that the output does not
  change at all for a trivial variation. that is not a metamorphic relation,
  it is an equality check in disguise and should be written as one.

## 5. Structure

Participants, named by the role each plays in a metamorphic test, not by a
generic class name.

- **System under test (SUT).** The program, function, or service being
  tested. It is treated as a black box. only its inputs and outputs are
  observed.
- **Source test case.** An input to the SUT for which an output will be
  observed, chosen the same way a normal test input is chosen, arbitrarily,
  from a corpus, or generated. It carries no requirement of a known correct
  output.
- **Metamorphic relation (MR).** A property that must hold between a source
  input and output and one or more follow-up inputs and outputs. It is
  expressed as a function of the source input, the follow-up input, the
  source output, and the follow-up output, returning true when the relation
  holds.
- **Follow-up input generator.** The transformation that derives a follow-up
  input from a source input according to the shape the MR needs, for
  example reversing term order, scaling a numeric input, adding a
  constraining term, adding noise below a threshold.
- **Relation checker.** The code that runs the SUT on both the source and
  the follow-up input, then evaluates the MR against the pair of
  input-output pairs and reports pass or fail. It is the assertion, and it
  never inspects a single output on its own.
- **MR set.** The full collection of independent relations a team maintains
  for one SUT. A single relation is rarely enough, per dimension 10 and
  dimension 11.

## 6. ASCII structure diagram

```
+--------------------+
|   Source input x    |
+---------+----------+
          |
          v
   +-------------+          derive per MR shape
   |     SUT      |<----+  +-----------------------------+
   +------+-------+      \ | Follow-up input generator     |
          |                | f(x) -> x'                    |
          v                +---------------+---------------+
  +---------------+                        |
  |  Output y = SUT(x) |                    v
  +--------+-------+          +-------------+-------------+
           |                  |            SUT              |
           |                  +-------------+-------------+
           |                                |
           |                                v
           |                  +-------------------------+
           |                  | Output y' = SUT(x')       |
           |                  +-------------+-------------+
           |                                |
           v                                v
   +----------------------------------------------------+
   |   Relation checker.  MR(x, x', y, y') true?          |
   +----------------------------------------------------+
                    |                     |
                 relation              relation
                  holds                violated
                    |                     |
                    v                     v
             test passes           bug found, no oracle
                                    needed to know it
```

## 7. Dynamics

The runtime flow for a single MR against a single seed.

```
driver             SUT                relation checker
  |                 |                        |
  | pick source x   |                        |
  |---------------->|                        |
  | y = SUT(x)      |                        |
  |<----------------|                        |
  |                 |                        |
  | x' = f(x)  (follow-up input generator)   |
  |                 |                        |
  | y' = SUT(x')    |                        |
  |---------------->|                        |
  |<----------------|                        |
  |                 |                        |
  | evaluate MR(x, x', y, y') ---------------->
  |                                            |
  |            <----------------- pass or fail |
  v
report
```

A full metamorphic test run repeats this for every seed in a corpus, for
every relation in the MR set. because relations are independent, a
violation in one relation does not stop the others from running against the
same seed, and a suite typically reports which relations failed for which
seeds, not a single pass or fail bit. Property-based test generators, per
dimension 13, replace the fixed seed corpus with generated seeds and repeat
the same source, follow-up, check cycle for each one, shrinking a failing
seed to a minimal reproducer when a relation fails.

## 8. Implementation variants

- **Manual relation with a hand-picked seed corpus.** The relation and the
  follow-up transformation are ordinary functions, and seeds come from a
  fixed list of examples the team curates. Cheapest to start, weakest
  coverage, common in early adoption inside an existing example-based suite.
- **Metamorphic testing on generated seeds.** The seed corpus comes from a
  property-based test generator or a fuzzer instead of a fixed list, so the
  same relation is checked against a much larger and less predictable input
  space. This is the composition with property-based-test described in
  dimension 13, and is the shape used in the DeepTest tool described in
  dimension 9.
- **Composite or chained relations.** Segura et al.'s survey, cited in
  dimension 1, catalogs recurring relation shapes that appear across many
  domains rather than being domain specific. Equivalence, when a
  transformation should leave the output unchanged, for example permuting
  the terms of a commutative query. Additive, when a transformation should
  change the output by a predictable, computable amount, for example
  scaling a numeric input by a known factor. Multiplicative, the same idea
  for a proportional relation. Inclusive, when a transformation should
  produce a result set that contains the original, for example widening a
  search filter. Exclusive, the mirror case, narrowing must shrink or hold
  the result set, never grow it. Permutative, when reordering an unordered
  collection of inputs must not change the output. A single system usually
  needs several of these together, because each shape exposes a different
  class of bug, per the two-relation example worked through in dimension 6
  and dimension 11.
- **Metamorphic testing as differential oracle replacement.** Instead of
  relating two outputs of the same system, the relation compares the SUT's
  output against a second, independently built implementation on the same
  transformed input. this shades into differential testing and is sometimes
  described in the literature as a metamorphic relation across two systems
  rather than across two inputs to one system, in particular in EMI,
  equivalence modulo inputs, compiler testing, Le, Afshari and Su, "Compiler
  Validation via Equivalence Modulo Inputs", ACM SIGPLAN Conference on
  Programming Language Design and Implementation, 2014.
- **Metamorphic mutation, MT plus mutation testing.** A relation's own
  strength can be measured the same way a test suite's strength is measured,
  by seeding a known bug, a mutant, into the SUT and checking whether at
  least one relation in the MR set detects it. This closes the loop between
  metamorphic-test and mutation-test, per dimension 13.

## 9. Known production uses

- **Google's GraphicsFuzz for Android graphics drivers.** In August 2018
  Google acquired GraphicsFuzz, a spinout from Imperial College London, to
  apply metamorphic testing to graphics device drivers on Android
  smartphones. the underlying idea is that a driver-generated image from a
  shader program must be equivalent, under floating point tolerance, to the
  image produced by a semantically equivalent transformed version of the
  same shader, and a mismatch reveals a driver bug with no need for a ground
  truth renderer (https://en.wikipedia.org/wiki/Metamorphic_testing,
  verified 2026-08-02).
- **DeepTest for autonomous-driving neural networks.** Yuchi Tian, Kexin
  Pei, Suman Jana and Baishakhi Ray, "DeepTest. Automated Testing of
  Deep-Neural-Network-driven Autonomous Cars", arXiv 1708.08559, first
  submitted August 2017, revised March 2018
  (https://arxiv.org/abs/1708.08559, verified 2026-08-02). DeepTest applies
  realistic image transformations, rain, fog, blur, changed lighting, to
  camera frames fed into self-driving perception models and checks that the
  model's steering decision is consistent with the untransformed frame's
  decision within a tolerance, rather than relying on a hand-labeled correct
  steering angle for every transformed frame. The paper reports thousands of
  erroneous behaviours found this way across tested models.
- **TransRepair testing production machine translation systems.** Zeyu Sun,
  Jie M. Zhang, Mark Harman, Mike Papadakis and Lu Zhang, "Automatic Testing
  and Improvement of Machine Translation", arXiv 1910.02688, first submitted
  October 2019, revised December 2019 (https://arxiv.org/abs/1910.02688,
  verified 2026-08-02). TransRepair generates paraphrased or near-synonym
  variants of a source sentence and checks that the corresponding parts of
  the translation remain consistent, rather than comparing against one
  fixed reference translation. Evaluated directly against Google Translate
  and against a Transformer-based translator, it found inconsistency rates
  of roughly 36 percent and 40 percent respectively.

## 10. Consequences

Positive.

- Makes previously untestable systems testable. it converts the oracle
  problem from unsolvable to a domain-analysis problem, which is strictly
  easier.
- Scales cheaply once written. one relation is checked against an unbounded
  number of generated or existing seeds with no extra authoring cost per
  seed.
- Finds real bugs that single-example tests cannot express, because the
  relation spans two or more related executions and can encode properties
  like order independence, monotonicity, and scaling that no single
  expected-output assertion can state.
- Composes naturally with property-based test generation and with fuzzing,
  per dimension 13, adding coverage further with little extra work.
- Documents an implicit specification. writing a relation forces the team to
  state, in code, a property of the system's contract that was previously
  only understood informally, which has value independent of the testing
  itself.

Negative, judgment. the sizing below reflects observed practice, not a
formula.

- Only checks a necessary property, not a sufficient one. a system can pass
  every relation in the MR set and still be wrong on every single output in
  a way no relation captures, so a green metamorphic suite is weaker
  evidence of correctness than a green suite of exact-value tests would be
  if one were possible.
- A failing relation localizes the bug to a pair of executions, not to a
  line of code or to which of the two outputs is wrong. diagnosis after a
  failure is genuinely harder than after an example-based test failure.
- Finding a useful, non-trivial relation is a domain-expertise task and is
  the actual bottleneck in adopting the technique. a weak team-written
  relation that degenerates to a near-tautology gives false confidence.
- Coverage is bounded by the union of what the chosen relations can express.
  adding relations has diminishing but nonzero returns, and there is no
  general way to know how many relations are enough for a given SUT.

## 11. Failure modes and misuse

- **Symptom.** The metamorphic suite is green, but a known bug still reaches
  production undetected. **Cause.** The MR set only encodes relations that
  happen not to be sensitive to that bug's shape, exactly as the search
  example in dimension 6 shows a subset relation staying green on a
  permutation bug. **Fix.** Deliberately seed a known or historical bug into
  the SUT, a mutant, and confirm at least one relation in the set catches
  it, per the metamorphic mutation variant in dimension 8, before trusting
  the set's coverage claims.
- **Symptom.** A relation fails intermittently and the team starts ignoring
  or retrying it. **Cause.** The relation was written against a system with
  genuine nondeterminism, floating point rounding across platforms, a
  randomized algorithm, a model with sampling temperature above zero, and
  the relation's equality check is exact rather than tolerance based.
  **Fix.** Encode an explicit, justified tolerance in the relation itself,
  for example a distance metric under a threshold instead of strict
  equality, and treat any failure past that as a real signal, never as
  something to retry away.
- **Symptom.** A relation always passes, no matter what is broken in the
  SUT, and nobody notices for a long time. **Cause.** The relation degenerated
  toward a tautology during a well-meaning simplification, for example a
  subset check written against a follow-up input that the SUT happens to
  treat identically to the source for unrelated reasons, so the relation
  never has a chance to be exercised differently. **Fix.** Periodically
  audit relations the same way test coverage is audited, by mutation, per
  the first item above, not by eyeballing the relation's code.
- **Symptom.** Diagnosing a failed relation takes far longer than diagnosing
  a failed example-based test. **Cause.** The failure report shows only that
  MR(x, x', y, y') is false, with no indication of which of y or y' is
  wrong, or whether both are. **Fix.** Log both full input-output pairs on
  failure, not only the boolean result, and where practical pair the
  relation with a smaller, hand-picked example test on the same domain so a
  developer has at least one exact-value anchor to reason from.
- **Symptom.** The team treats a passing metamorphic suite as equivalent
  proof of correctness to a passing exact-oracle suite, and stops writing
  the exact-value tests they could have written for the easy inputs.
  **Cause.** The necessary-but-not-sufficient nature of a relation, per
  dimension 10, is forgotten under deadline pressure. **Fix.** Keep
  exact-value tests wherever an oracle is genuinely cheap, and use
  metamorphic tests to extend coverage into the space where no oracle
  exists, never as a wholesale replacement for one that already exists.

## 12. Trade-off matrix

Compared against named alternatives that also address the oracle problem or
overlap in what they cover.

| Force | Metamorphic testing | property-based-test with a model oracle | golden-master | fault-injection |
|---|---|---|---|---|
| Needs an independent oracle | No, checks a relation instead | Yes, needs a reference model | Yes, a recorded prior output stands in for one | No, checks resilience not correctness of output |
| Catches order and scaling bugs | Strong, this is the technique's whole point | Only if the model captures the same property | Weak, only catches drift from the recorded baseline | Not its purpose |
| Localizes the failing line | Weak, points at a pair of executions | Strong, compares against a computed expectation | Moderate, diffs against a known-good snapshot | Strong for the injected fault path |
| Setup cost | Domain analysis to find a valid relation | Building and trusting a reference model | Recording a trusted baseline once | Building fault injection points |
| Detects regression from a prior known-good state | Not directly, unless the relation is against a prior version | Not directly | Directly, this is its whole purpose | Not directly |
| Works with no ground truth at all | Yes, its defining use case | No, needs some notion of correct to model | No, needs a prior output believed correct | Yes, but answers a different question, resilience not output correctness |

golden-master and metamorphic testing are frequently used together rather
than as competitors, per dimension 13. property-based-test with a model
oracle is the closest technical relative and the two combine directly, per
dimension 13, with metamorphic relations used as the oracle a property test
checks against instead of an exact expected value.

## 13. Related and incompatible patterns

- **property-based-test.** The strongest composition. a property-based
  framework supplies the random seed generation and the shrinking to a
  minimal failing case, and a metamorphic relation supplies the oracle the
  property checks, which is exactly the gap property-based testing leaves
  open when no exact model of correctness exists. See the generated-seed
  variant in dimension 8.
- **mutation-test.** Used to validate an MR set's own strength, per
  dimension 11's first failure mode. seed a mutant into the SUT and confirm
  at least one relation detects it, the same way mutation testing validates
  an ordinary assertion suite.
- **golden-master and characterization-test.** These solve an adjacent but
  distinct problem, pinning down current behaviour so a refactor does not
  silently change it, using a recorded baseline as a stand-in oracle. They
  compose with metamorphic testing rather than replace it. a golden master
  can serve as one of the source inputs a metamorphic relation is checked
  against, catching regressions the recorded snapshot alone would miss
  because the snapshot only covers the exact recorded input.
- **contract-test.** A contract test checks a service's output shape and
  invariants against a schema or a promise made to a consumer, largely
  independent of the value-relation focus of metamorphic testing. They
  overlap only where the contract itself states an invariant relation, for
  example a paginated API's promise that narrowing a filter never returns
  more results, which is itself a metamorphic relation expressed as a
  contract.
- **Incompatible with.** Nothing in this catalog is structurally
  incompatible with metamorphic testing. it is additive to an existing
  suite. The closest thing to friction is a team culture that treats a green
  suite as proof of correctness rather than as evidence bounded by what the
  relations actually check, which undermines the discipline the technique
  requires rather than conflicting with any other named pattern.

## 14. Refactoring path in and out

Introducing metamorphic testing into a codebase that has none.

1. Identify one SUT for which writing an exact-value test for an arbitrary
   input is genuinely hard or impossible, not merely tedious. If an exact
   oracle is cheap, this is the wrong candidate, per dimension 4.
2. State, in plain language, one property the specification or the domain
   implies about related inputs. reversing the order of independent terms
   should not change a conjunctive result. doubling every input to a linear
   function should double the output. widening a filter should never shrink
   the result set.
3. Write the follow-up input generator, the small function that derives x'
   from x according to that property, and keep it deterministic so failures
   reproduce.
4. Write the relation checker as a boolean function of x, x', y, y', and run
   it against a handful of hand-picked seeds first, before wiring it into a
   generator, so the relation itself is debugged on cases a human can trace
   by hand.
5. Wire the relation into the existing test runner alongside the example
   based tests already in the suite, treating a relation violation exactly
   like any other test failure.
6. Only after step 5 is stable, connect the seed corpus to a property-based
   generator or an existing fuzz corpus, per dimension 8, to extend coverage
   beyond the hand-picked seeds.
7. Repeat from step 2 for a second, independent relation, because a single
   relation structurally cannot catch every bug class, per the two-relation
   example in dimension 6 and the first failure mode in dimension 11.

Removing metamorphic testing when it stops earning its place.

1. If the SUT gained a genuine, cheap independent oracle, for example a
   reference implementation became available or the domain simplified, add
   exact-value tests against that oracle and let them subsume the weaker
   necessary-only relation checks over time, keeping the relation only where
   it still catches something the oracle-based test does not.
2. If a relation was found by mutation testing, per dimension 11, to never
   detect anything across a long history, retire it rather than let it
   accumulate as inert code, and record why in the commit message so a
   future maintainer does not reintroduce the same weak relation.
3. Never remove a relation simply because it is failing. a failing relation
   in a long-stable suite is far more likely to be a real regression than a
   flaw in the relation, unless the specific tolerance or nondeterminism
   cause from dimension 11 has been ruled out first.

## 15. Testing and verification

Judgment, this dimension describes practice rather than a documented
standard.

Testing the relations themselves, not only using them to test something
else, is the discipline most teams skip and the one that matters most. Two
techniques do this directly. First, mutation testing the SUT and confirming
each relation in the set detects at least one class of injected fault,
described in dimension 11 and dimension 13, which turns "we believe this
relation is meaningful" into a measured claim. Second, deliberately checking
that each relation is satisfiable and violable on constructed examples
before trusting it against generated seeds, meaning write one input pair by
hand where the relation should hold and one where it should not, and confirm
the checker agrees with both, catching the tautology failure mode from
dimension 11 before it reaches a generator.

What becomes easier because of this pattern. testing systems that were
previously accepted as untestable, and testing across an effectively
unbounded input space once the relation and generator exist, at close to
zero marginal cost per additional seed.

What becomes harder. localizing a failure to a specific defect, since a
relation violation names a pair of executions rather than a line of code,
and building trust in the relation set itself, since an unmeasured relation
gives a false sense of coverage exactly as easily as no test at all,
possibly more easily because a green metamorphic suite reads as strong
evidence to someone unfamiliar with the necessary-not-sufficient property
from dimension 10.

## 16. Observability signals

Judgment, based on how metamorphic suites are typically instrumented in
practice rather than a documented standard.

What to log on every relation check, pass or fail. the source input, the
derived follow-up input, both raw outputs, and the specific relation that
was evaluated, because a bare pass or fail bit throws away exactly the
information needed to diagnose a failure, per dimension 15.

What to trace at the suite level. per-relation pass rate over time, and per
seed corpus, source, hand-picked, property-generated, fuzz-derived, so a
sudden drop in one relation's pass rate against one corpus source is
visible rather than averaged away into an overall suite health number.

A healthy instance on a dashboard looks like a stable, near-100 percent pass
rate per relation across a growing seed corpus, with any transient dip
immediately traceable to a specific input pair via the logging above, and a
periodic mutation-testing score, per dimension 11, confirming the relation
set still detects injected faults rather than having quietly degenerated
into tautologies over time. A failing instance looks like a relation whose
pass rate never quite reaches 100 percent and is treated as expected noise,
or a mutation score for the relation set that has been declining and nobody
has looked at why.

## 17. Security and privacy implications

Judgment. metamorphic testing's implications here are analytical rather than
documented in a standard.

The technique itself introduces no new attack surface, because it only
observes and compares outputs of the existing SUT rather than adding a new
interface. Two implications are worth naming. First, when the SUT under
test handles sensitive data, the follow-up input generator and the logging
described in dimension 16 must be reviewed the same way any other test
fixture handling that data is reviewed, because a metamorphic test corpus
derived from real production inputs carries the same privacy obligations as
the source data it was derived from. Second, in a security-relevant domain,
for example an access-control decision function, a metamorphic relation can
directly encode a security invariant, for example widening a caller's
declared scope should never narrow the set of denied actions, turning a
security property that would otherwise be checked only by example into
something checked across a whole generated input space, which is a real
strength of the technique in that domain rather than a risk.

## 18. References

1. T. Y. Chen, S. C. Cheung, S. M. Yiu, "Metamorphic Testing. A New Approach
   for Generating Next Test Cases", Technical Report HKUST-CS98-01,
   Department of Computer Science, The Hong Kong University of Science and
   Technology, 1998, as cited via
   https://en.wikipedia.org/wiki/Metamorphic_testing, verified 2026-08-02.
2. Sergio Segura, Gordon Fraser, Ana B. Sanchez, Antonio Ruiz-Cortés, "A
   Survey on Metamorphic Testing", IEEE Transactions on Software
   Engineering, vol. 42, no. 9, 2016.
3. Elaine J. Weyuker, "On Testing Non-Testable Programs", The Computer
   Journal, vol. 25, no. 4, 1982, pages 465 to 470, as cited via
   https://en.wikipedia.org/wiki/Test_oracle, verified 2026-08-02.
4. "Metamorphic testing", Wikipedia, https://en.wikipedia.org/wiki/Metamorphic_testing,
   verified 2026-08-02. Source for the GraphicsFuzz acquisition referenced
   in dimension 9.
5. "Test oracle", Wikipedia, https://en.wikipedia.org/wiki/Test_oracle,
   verified 2026-08-02. Source for the Weyuker citation and the framing of
   metamorphic relations as partial oracles.
6. Yuchi Tian, Kexin Pei, Suman Jana, Baishakhi Ray, "DeepTest. Automated
   Testing of Deep-Neural-Network-driven Autonomous Cars", arXiv 1708.08559,
   https://arxiv.org/abs/1708.08559, first submitted August 2017, revised
   March 2018, verified 2026-08-02.
7. Zeyu Sun, Jie M. Zhang, Mark Harman, Mike Papadakis, Lu Zhang, "Automatic
   Testing and Improvement of Machine Translation", arXiv 1910.02688,
   https://arxiv.org/abs/1910.02688, first submitted October 2019, revised
   December 2019, verified 2026-08-02.
8. Vu Le, Mehrdad Afshari, Zhendong Su, "Compiler Validation via Equivalence
   Modulo Inputs", ACM SIGPLAN Conference on Programming Language Design
   and Implementation (PLDI), 2014. Cited in dimension 8 for the EMI
   compiler-testing variant related to metamorphic testing across two
   implementations.

## Code examples

The examples below implement the same small search index in three
languages, deliberately with a bug, and check it with two metamorphic
relations. permuting the order of independent query terms must not change
the result set, and adding a constraining term must never grow the result
set. The bug makes the index treat a two-term query as an ordered phrase
instead of an unordered set of required terms. The permutation relation
catches it. the subset relation does not, which is the point made in
dimension 11, one relation is rarely enough.

Java and C# and Kotlin are omitted. the runtime available for this entry had
no working Java installation to compile and run against, and the pattern
does not gain a materially different shape in C# or Kotlin over the
languages already covered by Python, Go, and Rust here, so they were left
out rather than shipped unverified.

### Python

```python
class SearchIndex:
    """Naive full-text index. Bug. treats a multi-word AND query as an
    ordered phrase, so it is sensitive to term order."""

    def __init__(self, docs):
        self.docs = {doc_id: text.lower() for doc_id, text in docs.items()}

    def search(self, query):
        q = query.lower()
        return {d for d, text in self.docs.items() if q in text}


class FixedSearchIndex:
    """Corrected version. Each term is checked independently, so the
    result set does not depend on term order."""

    def __init__(self, docs):
        self.docs = {doc_id: text.lower() for doc_id, text in docs.items()}

    def search(self, query):
        terms = query.lower().split()
        return {
            d for d, text in self.docs.items()
            if all(t in text for t in terms)
        }


def permutation_relation_holds(index_cls, docs, query):
    idx = index_cls(docs)
    terms = query.split()
    if len(terms) < 2:
        return True
    base = idx.search(" ".join(terms))
    reordered = idx.search(" ".join(reversed(terms)))
    return base == reordered


def subset_relation_holds(index_cls, docs, query, extra_term):
    idx = index_cls(docs)
    narrow = idx.search(f"{query} {extra_term}")
    wide = idx.search(query)
    return narrow.issubset(wide)


if __name__ == "__main__":
    docs = {
        "d1": "the red bicycle is fast",
        "d2": "a bicycle painted bright red",
        "d3": "a blue car with red trim",
    }
    query = "red bicycle"

    buggy_perm = permutation_relation_holds(SearchIndex, docs, query)
    fixed_perm = permutation_relation_holds(FixedSearchIndex, docs, query)
    buggy_sub = subset_relation_holds(SearchIndex, docs, "red", "bicycle")
    fixed_sub = subset_relation_holds(FixedSearchIndex, docs, "red", "bicycle")

    assert buggy_perm is False, "expected the buggy index to fail the MR"
    assert fixed_perm is True, "fixed index must satisfy the MR"
    assert buggy_sub is True, "subset MR does not expose this bug"
    assert fixed_sub is True
    print("permutation MR. buggy =", buggy_perm, "fixed =", fixed_perm)
    print("subset MR. buggy =", buggy_sub, "fixed =", fixed_sub)
```

Run with `python3 search.py`. Output confirms the permutation relation is
false for the buggy index and true for the fixed one, while the subset
relation stays true for both, showing which relation actually catches the
bug. Verified against Python 3.14 for this entry.

### Go

```go
package main

import (
	"fmt"
	"strings"
)

type searchFn func(query string) map[string]bool

func buggyIndex(docs map[string]string) searchFn {
	lower := map[string]string{}
	for id, t := range docs {
		lower[id] = strings.ToLower(t)
	}
	return func(query string) map[string]bool {
		q := strings.ToLower(query)
		out := map[string]bool{}
		for id, t := range lower {
			if strings.Contains(t, q) {
				out[id] = true
			}
		}
		return out
	}
}

func fixedIndex(docs map[string]string) searchFn {
	lower := map[string]string{}
	for id, t := range docs {
		lower[id] = strings.ToLower(t)
	}
	return func(query string) map[string]bool {
		terms := strings.Fields(strings.ToLower(query))
		out := map[string]bool{}
		for id, t := range lower {
			all := true
			for _, term := range terms {
				if !strings.Contains(t, term) {
					all = false
					break
				}
			}
			if all {
				out[id] = true
			}
		}
		return out
	}
}

func permutationHolds(f searchFn, query string) bool {
	terms := strings.Fields(query)
	if len(terms) < 2 {
		return true
	}
	base := f(strings.Join(terms, " "))
	reversed := make([]string, len(terms))
	for i, t := range terms {
		reversed[len(terms)-1-i] = t
	}
	swapped := f(strings.Join(reversed, " "))
	return setsEqual(base, swapped)
}

func setsEqual(a, b map[string]bool) bool {
	if len(a) != len(b) {
		return false
	}
	for k := range a {
		if !b[k] {
			return false
		}
	}
	return true
}

func main() {
	docs := map[string]string{
		"d1": "the red bicycle is fast",
		"d2": "a bicycle painted bright red",
		"d3": "a blue car with red trim",
	}
	buggyPerm := permutationHolds(buggyIndex(docs), "red bicycle")
	fixedPerm := permutationHolds(fixedIndex(docs), "red bicycle")

	if buggyPerm != false {
		panic("expected buggy index to violate the MR")
	}
	if fixedPerm != true {
		panic("expected fixed index to satisfy the MR")
	}
	fmt.Println("permutation MR. buggy =", buggyPerm, "fixed =", fixedPerm)
}
```

Run with `go run search.go`. Compiled and executed against go1.26 for this
entry, no external dependencies.

### Rust

```rust
use std::collections::{HashMap, HashSet};

fn buggy_search(docs: &HashMap<&str, &str>, query: &str) -> HashSet<String> {
    let q = query.to_lowercase();
    docs.iter()
        .filter(|(_, text)| text.to_lowercase().contains(&q))
        .map(|(id, _)| id.to_string())
        .collect()
}

fn fixed_search(docs: &HashMap<&str, &str>, query: &str) -> HashSet<String> {
    let terms: Vec<String> = query.to_lowercase().split_whitespace().map(String::from).collect();
    docs.iter()
        .filter(|(_, text)| {
            let lower = text.to_lowercase();
            terms.iter().all(|t| lower.contains(t.as_str()))
        })
        .map(|(id, _)| id.to_string())
        .collect()
}

fn permutation_holds<F: Fn(&HashMap<&str, &str>, &str) -> HashSet<String>>(
    search: F,
    docs: &HashMap<&str, &str>,
    query: &str,
) -> bool {
    let terms: Vec<&str> = query.split_whitespace().collect();
    if terms.len() < 2 {
        return true;
    }
    let base = search(docs, &terms.join(" "));
    let reversed: Vec<&str> = terms.iter().rev().copied().collect();
    let swapped = search(docs, &reversed.join(" "));
    base == swapped
}

fn sample_docs() -> HashMap<&'static str, &'static str> {
    let mut docs = HashMap::new();
    docs.insert("d1", "the red bicycle is fast");
    docs.insert("d2", "a bicycle painted bright red");
    docs.insert("d3", "a blue car with red trim");
    docs
}

#[test]
fn buggy_index_violates_permutation_relation() {
    let docs = sample_docs();
    assert!(!permutation_holds(buggy_search, &docs, "red bicycle"));
}

#[test]
fn fixed_index_satisfies_permutation_relation() {
    let docs = sample_docs();
    assert!(permutation_holds(fixed_search, &docs, "red bicycle"));
}

fn main() {
    let docs = sample_docs();
    let buggy = permutation_holds(buggy_search, &docs, "red bicycle");
    let fixed = permutation_holds(fixed_search, &docs, "red bicycle");
    assert!(!buggy, "expected the buggy index to violate the MR");
    assert!(fixed, "expected the fixed index to satisfy the MR");
    println!("permutation MR. buggy = {}, fixed = {}", buggy, fixed);
}
```

Run with `rustc --edition 2021 --test search.rs -o search_test` then
`./search_test` for the unit tests, or `rustc --edition 2021 search.rs -o
search` then `./search` for the standalone assertion run. Both compiled and
passed for this entry against rustc 1.97.
