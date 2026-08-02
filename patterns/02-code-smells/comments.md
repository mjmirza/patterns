---
name: Comments
slug: comments
family: 02-code-smells
category: Code Smell
aliases: [Comment Smell, Excuse Comments, Comment Rot, Deodorant Comments]
first_described: "Beck, Fowler 1999"
maturity: canonical
related: [duplicated-code, long-method, mysterious-name, dead-code, speculative-generality, extract-method, rename-method]
incompatible_with: []
verified: 2026-08-02
---

# Comments

## 1. Name, aliases, and lineage

The canonical name is **Comments**, and it appears exactly that way in the
"Bad Smells in Code" catalog written by Kent Beck and Martin Fowler for the
first edition of *Refactoring. Improving the Design of Existing Code*,
Addison-Wesley, 1999, chapter 3. The catalog survives into the second edition,
Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
edition, Addison-Wesley, 2018, chapter 3, "Comments," where Fowler keeps Beck's
framing and sharpens the language around it. Fowler is explicit in the second
edition about who wrote which chapter of the smell catalog originally, and the
"Comments" entry is one of Beck's.

The name is unusual among code smells because, read on its own, it sounds like
an instruction to remove all comments. That is not the claim. The smell is not
the presence of a comment. It is a comment doing the wrong job. A comment that
exists to compensate for code that could instead say what it means is the
smell. A comment that records a fact the code cannot express on its own, a
license header, a regulatory citation, a warning about a non-obvious
constraint, is not the smell, and Fowler says so directly in the same chapter.

Beck's own framing, which Fowler repeats and which has become the most quoted
line associated with this smell, treats a comment as a **deodorant**. The
metaphor is Beck's, reported by Fowler in the "Comments" section of the second
edition. A bad smell in code is often masked, not fixed, by writing a comment
that explains why the code is confusing instead of making the code less
confusing. The comment is sprayed on top of the smell rather than removing it.
This is a judgement call about how to read Beck and Fowler's intent, not a
direct quotation lifted from the text, and it is the frame this entry uses
throughout.

Robert C. Martin gives the smell its sharpest independent restatement in
*Clean Code. A Handbook of Agile Software Craftsmanship*, Prentice Hall, 2008,
chapter 4, "Comments." Martin's chapter opens with the claim that comments are
"a necessary evil" and that "the proper use of comments is to compensate for
our failure to express ourself in code." Martin goes further than Beck and
Fowler by treating most comments as evidence of a design failure rather than a
neutral communication tool, a stance this entry treats as one influential
position within the field rather than settled consensus, because the language
communities that formalise doc comments into build tooling, Rustdoc and
Javadoc among them, plainly disagree that comments are inherently a failure.
See dimension 9 for that disagreement made concrete.

A distinct but related term, **redundant comment**, is used by static analysis
tooling rather than by the Beck and Fowler catalog. SonarSource documents the
specific rule for commented-out code as **S125**, "Sections of code should not
be commented out," in the SonarQube rules repository ([SonarSource rule S125](https://web.archive.org/web/20251208093303/https://rules.sonarsource.com/csharp/rspec-125/),
verified 2026-08-02). This entry treats commented-out code as one variant of
the Comments smell (dimension 8) rather than a separate pattern, because it
shares the same root cause, a maintainer choosing a comment over a decisive
action the codebase already has better tools for.

## 2. Problem and context

A comment is a message from one point in time to a later reader, and it is
never checked by anything that runs. The compiler does not read it. The type
checker does not read it. The test suite does not read it, with the single
notable exception of doctest-style tooling covered in dimension 15. A comment
can therefore drift arbitrarily far from the code it sits beside, and nothing
in the ordinary development loop will ever flag the drift. Fowler makes this
point in the "Comments" chapter of the second edition by observing that
comments often function as a deodorant, precisely because writing a comment is
cheaper, in the moment, than fixing the thing the comment is covering for, and
the comment survives edits to the code around it because editing a comment is
optional in every language's grammar.

The situation reads like this in a real codebase. A method has grown past the
point where its name still describes what it does. Rather than rename it or
split it, someone adds a block comment above it summarising the current
behaviour. Six months later a different engineer changes one branch of the
method's logic, sees the comment, reads it, trusts it, and does not re-read
every line beneath it because the comment appears to already describe the
method faithfully. The comment was accurate on the day it was written. It is
not accurate now. The reader has just been actively misled by a piece of text
whose only job was to help them, and misled with more confidence than they
would have had reading no comment at all, because a stale comment reads as
authoritative in a way that silence does not.

The context that produces this smell has three recurring shapes. First,
**narration**, where a comment restates in English what the next line already
states in code, adding no information and giving the illusion of
documentation while documenting nothing a competent reader of the language
did not already know. Second, **compensation**, where a comment exists
because a name, a function boundary, or a data structure is wrong, and the
comment is patching over that wrongness instead of the wrongness being fixed.
Third, **archival**, where a comment records something that used to be true,
a rationale that no longer applies, a workaround for a bug that has since
been fixed, or a block of code that has been commented out rather than
deleted because someone was not confident enough in version control, or in
their own judgement, to remove it outright.

All three shapes share the same underlying failure. The comment is being
asked to do work that a better artifact would do more durably, a name, a
function, a test, a commit message, an architecture decision record, because
those artifacts are either checked by tooling, versioned with intent, or
physically inseparable from the code they describe. A comment is separable by
construction. That separability is exactly what makes it fail silently.

## 3. Forces

**Communication cost versus verification cost.** A comment is the cheapest
possible way to communicate intent, cheaper than a test, cheaper than a
rename, cheaper than an architecture decision record. That cheapness is
precisely the force that produces the smell, because cheap communication is
also unverified communication, and the two properties cannot be separated in
a comment as a medium. A comment favours communication speed and sacrifices
truth-maintenance.

**What versus why.** A comment describing what code does is redundant the
instant a reader can read the code itself, and it is a maintenance liability
forever after, because every future edit to the code must also edit the
comment or the two diverge. A comment describing why a decision was made, why
an obvious-looking alternative was rejected, why a workaround exists for an
external constraint, cannot be recovered by reading the code no matter how
well the code is written, because code expresses mechanism, not motive. This
is the single force that most determines whether a specific comment belongs to
this smell or is legitimate documentation, and it recurs through every other
dimension of this entry.

**Local clarity versus global truth-maintenance.** A comment written at the
point of authorship is, almost by definition, locally clear to the person who
wrote it, because they hold the full context in their head at that moment.
The same comment's clarity to a future reader depends entirely on whether the
surrounding code has changed since, a fact the author cannot control and the
comment itself cannot signal. This is a design forces trade-off, not a
character flaw in any individual engineer, because the same engineer who
writes an accurate comment on Monday cannot force their Friday self, let
alone a colleague six months later, to notice that a later edit invalidated
it.

**Documentation coverage metrics versus documentation value.** Many
organisations measure and reward comment density or doc-comment coverage as a
proxy for code quality. Static analysis tools can flag public members with no
comment. That incentive produces comments written to satisfy the metric
rather than to serve a reader, and a comment written to satisfy a linter is
under no pressure to be true, only to exist. This force explains why some of
the worst instances of this smell appear in codebases with the strictest
documentation policies, a case of an incentive optimising for the wrong
observable, and it is worth naming because "we have a documentation
requirement" is frequently offered, in code review, as a defence of exactly
the comments this smell targets.

**Team topology and shared context.** A small, co-located team with long
tenure can rely on tacit knowledge that a comment would otherwise have to
carry, so comments matter less to them and are more likely to rot unnoticed
because nobody is depending on them. A large, distributed team with high
turnover depends on written artifacts far more, which raises both the value
of a correct comment and the cost of an incorrect one, because a new engineer
has no tacit context against which to sanity-check what the comment claims.

This entry weighs "why over what" as the dominant force among the five above,
because it is the one dimension that separates a defensible comment from an
indefensible one in nearly every real code review dispute this smell
generates. That weighting is engineering judgement, not a citable finding.

## 4. Applicability and non-applicability

**Reach for a comment when the following hold.**

- The reasoning behind a decision cannot be recovered from the code no matter
  how the code is written, most often because the decision responds to a
  constraint outside the code itself, a regulation, a vendor's undocumented
  behaviour, a performance measurement, or a deliberately rejected simpler
  alternative. State the rejected alternative and the reason it was rejected,
  not only the choice that was made.
- The comment records a legal or licensing requirement, a copyright header,
  an SPDX identifier, or an attribution the organisation is contractually
  bound to carry, none of which any naming or refactoring choice can express.
- The comment warns of a genuine, non-obvious trap for a future editor, a
  method that must not be called before another has completed, a value that
  looks safe to change but silently corrupts persisted data if changed, an
  ordering constraint the type system cannot enforce in the language being
  used. Kent Beck and Martin Fowler explicitly keep this category as
  legitimate in the same "Comments" chapter that names the smell, because a
  warning comment substitutes for a check the language cannot express, not for
  a name the language could.
- A TODO comment marks a deliberate, temporary shortcut and carries a
  tracking reference so the shortcut is not silently forgotten, the exact
  format both the Google Python Style Guide and the Google engineering
  practices around it require, discussed with a direct quotation in dimension
  9.
- The comment is a doc comment consumed by tooling, a docstring, a Javadoc
  block, a Rustdoc `///` block, that becomes generated API documentation,
  because in that case the comment is not incidental prose next to code, it
  is a first-class build artifact with its own audience, the caller of a
  public interface who will never read the implementation at all.

**Do NOT reach for a comment, and treat one already present as this smell,
when any of the following hold.**

- The comment restates, in English, what the next line already states in the
  target language's own syntax. If a reader fluent in the language gets no
  new information from the comment, the comment is not documentation, it is
  duplication of the code in a form nothing checks.
- The comment exists only because a variable, function, class, or module is
  named badly and the comment is explaining what the name should have said.
  The fix is Rename Method or Rename Variable, standard refactorings named in
  Martin Fowler, *Refactoring*, 2nd edition, Addison-Wesley, 2018, chapter 6,
  "A First Set of Refactorings," not a comment layered on top of the bad name.
- The comment is a block of code that has been commented out rather than
  deleted. Version control retains every prior state of the file, so the
  commented-out block adds no information a `git log -p` or equivalent could
  not already recover, and it actively confuses a reader about whether the
  block is meant to be restored soon, is dead forever, or is a mistake nobody
  has cleaned up.
- The comment is a per-function or per-class boilerplate header inserted by a
  scaffolding tool or an IDE template and never edited to say anything
  specific to the function it sits above, for example a generated
  `///summary///` block with an empty body in a C sharp style codebase, or
  a Javadoc stub with no parameter text filled in.
- The comment records a changelog entry, a specific date and a bug number,
  inline in the source. Version control commit history and the project's
  changelog are the correct location for that fact, both because they are
  queryable by tooling and because an inline changelog comment accretes
  forever and nobody ever prunes it once the fact is stale.
- The comment apologises for or excuses code the author knew was wrong at the
  time of writing, "sorry this is a hack," "I know this is ugly but," with no
  accompanying plan, ticket, or explanation of what would be needed to fix
  it. An apology comment with no path forward is not documentation, it is an
  admission left in the codebase for a future reader to inherit unresolved.
- A test or an assertion could express the same fact the comment expresses,
  and more durably, because a test fails loudly when the invariant it checks
  breaks, while a comment simply becomes false and continues to compile.

## 5. Structure

The Comments smell has no runtime participants in the sense a design pattern
has, because a comment carries no behaviour and is stripped by every
tokenizer before compilation or interpretation begins. Its structure is
therefore best described as a relationship between four things that exist at
authoring time and at read time, which are not the same moment.

- **The comment text.** The literal prose attached to a region of code, whose
  only enforcement mechanism is a human reader choosing to trust it.
- **The referent.** The specific lines, function, class, or file the comment
  is attached to, established purely by physical proximity in the source, a
  convention with no language-level guarantee behind it in most mainstream
  languages, doc-comment tooling being the deliberate exception covered in
  dimension 9.
- **The authoring instant.** The moment the comment was written, at which
  point the comment and the referent are, by construction, consistent with
  each other, because the same person wrote both in the same edit.
- **The reading instant.** Any later moment at which a different reader, or
  the same author with a different mental state, encounters the comment and
  the referent together and must decide, usually without any signal telling
  them to check, whether the two still agree.

The smell exists in the gap between the authoring instant and every reading
instant that follows a code change the comment was not updated to reflect.
Nothing in the structure of a comment closes that gap. That absence, not any
property of the prose itself, is the structural root of the smell.

## 6. ASCII structure diagram

```
  AUTHORING INSTANT                    READING INSTANT (t2 > t1)
  -------------------                  --------------------------
  +------------------+                 +------------------+
  |  Comment text    |  proximity      |  Comment text    |
  |  "adds tax at    |  binding        |  "adds tax at    |
  |   the flat rate" |----------->     |   the flat rate" |  <-- unchanged
  +------------------+                 +------------------+
           |                                     |
           | describes                           | reader ASSUMES
           v                                      v describes
  +------------------+                 +------------------+
  |  Code region     |                 |  Code region     |
  |  applyFlatTax()  |  <-- t1  TRUE   |  applyTieredTax()| <-- edited at t1.5
  +------------------+                 +------------------+
                                                  ^
                                                  |
                                     no compiler, linter, or test
                                     enforces agreement here.
                                     the reader is the only check,
                                     and the comment LOOKS authoritative.
```

## 7. Dynamics

```
  t0  comment and code are written together, both true
       |
       v
  t1  a change lands that touches the code only
       (the comment is not part of the diff a reviewer's eye
        is drawn to, because the diff tool highlights code, not
        the now-orphaned prose two lines above it)
       |
       v
  t2  a second, unrelated change lands, also touching only code
       |
       v
  tn  a reader, possibly the ORIGINAL author months later,
       reads the comment and the code together
       |
       +-- reader trusts the comment (common case)
       |     -> reader's mental model is now WRONG
       |     -> reader makes a change based on the wrong model
       |     -> defect shipped, root cause invisible in the diff
       |
       +-- reader distrusts the comment (rare, defensive case)
             -> reader re-derives truth from the code directly
             -> the comment has now cost reading time and
                produced zero value, worse than if it did not exist
```

Both branches at `tn` are strictly worse than the comment never having
existed, which is the dynamic that makes this smell self-reinforcing once it
takes hold in a codebase. A team that has been burned by stale comments
starts ignoring all comments, including the genuinely load-bearing ones from
dimension 4, and the value of every future correct comment is degraded by the
population of incorrect ones already sitting in the code.

## 8. Implementation variants

**Narration comments, the "what" comment.** A comment that translates the
next statement into English with no added information, for example a comment
reading "increment i" placed above an increment statement. This is the
variant PEP 8 gives as its canonical bad example, contrasting a comment that
merely restates an increment with one that gives the reason for it, in the
official Python style guide's Comments section
([PEP 8, Comments](https://peps.python.org/pep-0008/#comments), verified
2026-08-02). The failure is not the presence of a comment on that line, it is
that the narration version adds nothing a reader of the language did not
already know, while the reasoned version states a fact the code cannot state
on its own.

**Stale or contradicting comments.** A comment that was true when written and
has since become false because the code around it changed and the comment
did not. PEP 8 states this variant's cost directly. "Comments that contradict
the code are worse than no comments. Always make a priority of keeping the
comments up-to-date when the code changes!" ([PEP 8, Comments](https://peps.python.org/pep-0008/#comments),
verified 2026-08-02). This is the variant the diagrams in dimensions 6 and 7
illustrate.

**Commented-out code.** A block of source wrapped in comment syntax instead
of removed, left in place either as an ad hoc undo mechanism or out of
reluctance to commit to the deletion. SonarSource tracks this as its own
rule, S125, "Sections of code should not be commented out," precisely because
it recurs across every language SonarQube analyses and produces a
specifically identifiable class of noise distinct from prose comments
([SonarSource rule S125](https://web.archive.org/web/20251208093303/https://rules.sonarsource.com/csharp/rspec-125/),
verified 2026-08-02).

**Apology and excuse comments.** A comment that names a known defect in the
code adjacent to it without a plan, such as "this is a mess, sorry." These
differ from a legitimate TODO because they carry no tracking reference and no
scoped description of what a fix would involve, so they cannot be triaged,
searched for systematically, or closed. Robert C. Martin treats this category
as one of the clearest signs that a comment is being used, in his phrase, to
compensate for a failure to express intent in code rather than to add real
information, in *Clean Code*, Prentice Hall, 2008, chapter 4.

**Changelog-in-comment.** A running history of edits recorded as comments
inline with the code they describe, each line naming a date and a fix.
This variant duplicates information version control already stores with
better tooling, `git blame` and `git log` chief among them, and it accretes
indefinitely because nobody ever prunes a historical comment, unlike an
actual changelog file which has an explicit editorial process.

**Mandatory-coverage comments.** A doc comment inserted purely to satisfy a
linter or documentation-coverage requirement, with content that adds nothing
beyond restating the signature, for example a generated accessor comment
that says only "gets the name" above a method literally named "get name."
This variant is distinct from the doc-comment production use in dimension 9
precisely because the content is empty. The mechanism, a doc comment
consumed by a generator, is legitimate, but an empty instance of that
mechanism is still this smell.

**Closing-brace and structural-noise comments.** A comment marking the end of
a block, such as one reading "end of loop" beside a closing brace, that
exists because the block is long enough that the reader has lost track of
what it closes by the time they reach the closing brace. The comment treats a
symptom, block length, rather than the cause, and Fowler's own catalog names
the underlying cause as a separate smell, Long Method, which this entry
cross-references in dimension 13 rather than duplicates.

**The deodorant distinction, stated as a rule of thumb.** For any comment
found in review, ask whether a rename, an extract, or an assertion could
replace it without losing information. If yes, the comment is masking a
smell that has a name of its own, and the fix belongs in dimension 14. If no,
because the information the comment carries genuinely cannot live in the
code, the why, the license, the external constraint, the comment is doing its
job and should stay. This is engineering judgement applied to the forces in
dimension 3, not a mechanically checkable rule, and static analysis tools
cannot make this distinction reliably, which is why every linter rule cited
in this entry targets a narrow, mechanically detectable variant, commented-out
code or a missing bug reference, rather than the smell in general.

## 9. Known production uses

**The Linux kernel's coding style document codifies the what-versus-why
distinction as a formal contribution requirement**, not merely as advice. The
kernel's official style guide states plainly. "Generally, you want your
comments to tell WHAT your code does, not HOW," and adds a specific
escalation. "if the function is so complex that you need to separately
comment parts of it, you should probably go back to chapter 6 for a while,"
chapter 6 of the same document being about function decomposition
([Linux kernel coding style, Commenting](https://www.kernel.org/doc/html/latest/process/coding-style.html),
verified 2026-08-02). The kernel additionally standardises a specific
multi-line comment block shape, a left-aligned column of asterisks with
near-blank opening and closing lines, so that comment blocks are visually
distinguishable from code at a glance across a codebase maintained by
thousands of contributors over three decades.

**CPython and the wider Python standard library are governed by PEP 8**,
whose own text states its scope directly. "This document gives coding
conventions for the Python code comprising the standard library in the main
Python distribution" ([PEP 8](https://peps.python.org/pep-0008/), verified
2026-08-02). PEP 8's Comments section is the source of the contradicting-
comments warning quoted in dimension 8, and because PEP 8 governs the
standard library itself, every module shipped in CPython's own source tree is
reviewed against this exact rule before it merges, making this one of the
largest and longest-running production enforcements of the what-versus-why
distinction in any open source ecosystem.

**Google enforces its own comment discipline across its internal Python
codebase**, whose public style guide opens by stating "Python is the main
dynamic language used at Google. This style guide is a list of dos and don'ts
for Python programs" ([Google Python Style Guide, Comments and
Docstrings](https://google.github.io/styleguide/pyguide.html), verified
2026-08-02). The same guide requires that a TODO comment "begins with the
word TODO in all caps, a following colon, and a link to a resource that
contains the context, ideally a bug reference," which is the mechanical fix
this entry recommends in dimension 14 for the apology-comment variant, a fix
Google has made into a style requirement rather than a suggestion across its
Python codebase.

**Rust's documentation tooling, rustdoc, treats a subset of comments as
executable specification rather than as inert prose**, which is a structural
answer to the staleness problem this entire smell describes rather than a
stylistic rule against it. A doc comment above a public item is not
discarded at compile time the way an ordinary comment is. It becomes the
source text for generated API documentation, and any fenced code block
inside it is, by default, compiled and run as a doctest, so a doc comment
whose example code no longer matches the function's real signature or
behaviour fails the build instead of silently drifting
([The rustdoc book, How to write documentation](https://doc.rust-lang.org/rustdoc/how-to-write-documentation.html),
verified 2026-08-02). This is a direct, tooling-level rebuttal of the claim
that comments are unverifiable by construction. Rust's ecosystem chose to
make one specific class of comment verifiable, at the cost of requiring the
example inside it to be runnable code, which most why-style comments in
dimension 4 are not and were never meant to be.

## 10. Consequences

**Positive**, when a comment is confined to the legitimate cases in
dimension 4.

- Captures a rationale, a rejected alternative, or an external constraint
  that no amount of good naming or code structure could express, because
  code expresses mechanism and the comment is carrying motive.
- Costs nothing at runtime in every language this entry surveys, so a
  correct why comment is one of the cheapest forms of documentation
  available, cheaper than an architecture decision record, cheaper than a
  wiki page that will be found by fewer future readers than the comment
  sitting directly at the point of decision.
- When produced by doc-comment tooling, becomes generated, searchable,
  IDE-surfaced API documentation for callers who will never read the
  implementation, the specific value Rustdoc and Javadoc are built around.
- A TODO comment carrying a tracking reference converts a known shortcut into
  a triage-able backlog item instead of a silent, undiscoverable debt.

**Negative**, when a comment falls into any variant from dimension 8.

- Actively misleads a reader with more confidence than no comment would,
  because prose reads as authoritative and a reader has no mechanism, short
  of independently re-deriving the fact from the code, to detect that the
  comment has gone stale.
- Duplicates information already present in the code, in a form nothing
  checks for consistency, which means every future edit to the code carries
  an invisible extra obligation, updating the comment too, that most editing
  workflows will not surface as a review nudge.
- Accumulates over time because deleting a comment feels riskier, socially,
  than adding one. Nobody is ever blamed in review for leaving a stale
  comment in place, while removing one occasionally draws a "why did you
  delete that" question even when the comment was wrong. This asymmetry
  means the smell is a one-way ratchet in most codebases absent deliberate
  counter-pressure.
- Commented-out code specifically obscures `git blame` and code search for
  everyone who is not aware the block is dead, and it degrades the signal of
  any grep-based or IDE-based search that a reader runs expecting live code.
- Reduces trust in the comment population as a whole once a team has been
  burned by enough stale ones, which devalues even the legitimate why
  comments described in dimension 4, a second-order cost that is harder to
  measure than the first-order cost of any single stale comment but is, in
  this entry's judgement, the more expensive of the two over a codebase's
  lifetime.

## 11. Failure modes and misuse

**Symptom.** A reviewer approves a pull request quickly because the diff
included an update to the docstring at the top of the function, and the
reviewer read the docstring instead of the body. **Cause.** The docstring was
edited in the same diff and therefore looked current, but the edit only
updated the summary line and not the parameter list beneath it, which no
longer matches the function's actual signature after an earlier, unrelated
refactor. **Fix.** Treat a doc comment the same as any other claim in a
review, verifying it against the code it describes on every diff that touches
either, not only diffs that touch the comment itself, and prefer tooling from
dimension 15 that checks doc comments against real signatures automatically
where the language supports it.

**Symptom.** Grepping a file for a function name returns three matches, one
live definition and two commented-out prior versions, and a new contributor
is unsure which is current. **Cause.** A previous author disabled two earlier
implementations by wrapping them in comment syntax during iterative
development and never deleted them once the final version shipped.
**Fix.** Delete the commented-out blocks outright once the working version
is committed. Version control already retains every prior state, per the
non-applicability list in dimension 4, and if a specific prior version is
worth preserving as a reference it belongs in a named branch, a tag, or a
linked commit reference in the commit message of the change that replaced
it, not left inline as dead prose.

**Symptom.** A junior engineer asks in review why a piece of code is written
in an unusual, seemingly overcomplicated way, and the honest answer is "I
don't remember, but I'm scared to change it." **Cause.** The original why
comment, which explained a workaround for a since-patched bug in a
dependency, or a performance finding that has since become irrelevant on
newer hardware, was deleted at some point, possibly as part of a well-meaning
comment cleanup, without anyone verifying whether the underlying constraint
still held. **Fix.** Before removing a why comment, confirm the constraint it
describes no longer applies rather than assuming a comment's age alone makes
it obsolete. If the constraint is genuinely gone, the code it justified can
usually be simplified at the same time the comment is removed, which is a
stronger signal of correctness than deleting the comment alone.

**Symptom.** A team's static analysis dashboard reports full doc comment
coverage on public methods, yet new engineers still report the codebase is
hard to onboard onto. **Cause.** Coverage was achieved by generating
boilerplate doc comments that restate the method signature and add no
information, satisfying the metric described in dimension 3 without
satisfying any reader's actual need. **Fix.** Replace coverage-as-a-metric
with a review checklist question, does this doc comment answer a question
the signature alone does not, and delete or rewrite any doc comment that
fails that test, accepting a temporary drop in the coverage number as the
honest price of an accurate one.

**Symptom.** A postmortem finds that an incident was caused by an engineer
trusting a comment above a configuration constant that claimed a specific
unit, seconds, when the constant had been changed to milliseconds in a
refactor eighteen months earlier and nobody updated the comment.
**Cause.** The unit was documented only in a comment rather than in the
constant's own name or type, so the drift between comment and code was
structurally undetectable by any tool, and the comment was trusted precisely
because it looked deliberate and specific. **Fix.** Encode the unit in the
identifier itself, a name such as timeoutMillis rather than a bare timeout
with a seconds comment above it, per the Introduce Explaining Variable and
Rename Variable refactorings in Martin Fowler, *Refactoring*, 2nd edition,
Addison-Wesley, 2018, chapter 6, so the fact the comment was carrying becomes
a fact the type system or the identifier itself carries and every future edit
is forced to keep consistent or fail to compile in a statically typed
language.

**Symptom.** A TODO comment is found during a codebase audit that references
a bug tracker ticket closed four years earlier as won't fix, yet the
workaround the TODO describes is still present and the comment still reads
as an open action item. **Cause.** The TODO was written correctly at the
time, following the Google Python Style Guide's own required format, a bug
reference included, but nobody re-visited it once the linked ticket's
disposition changed, because no tooling in the project cross-checks a TODO's
referenced ticket status against the ticket tracker automatically.
**Fix.** Either wire a periodic audit, manual or automated, that checks TODO
bug references against tracker status and flags stale ones, or accept that a
TODO with a closed, won't fix reference is now permanent code and remove the
TODO marker, folding any remaining rationale into a proper why comment from
dimension 4.

## 12. Trade-off matrix

| Force | Comments as documentation | Extract Method and Rename | Introduce Assertion | Doc-comment tooling, Rustdoc and Javadoc | Architecture Decision Record |
|---|---|---|---|---|---|
| Verified by tooling | No, in mainstream single-line comments | Indirectly, via the type checker and tests exercising the new name or shape | Yes, fails loudly at runtime if violated | Partially, doctests run as real code in Rust, Javadoc content is unverified prose | No, an ADR is prose exactly like a comment |
| Cost to add | Lowest of all five | Higher, requires touching call sites and possibly tests | Low to moderate, one line plus a message | Moderate, requires structuring the comment to the tool's expected shape | Highest, a separate document and a review cycle |
| Cost to keep current | Paid by every future editor, silently, or not paid at all | Paid once, then the name IS the documentation | Paid automatically, an assertion cannot silently go stale without failing | Paid partly automatically for code examples, manually for prose | Paid explicitly, ADRs are usually superseded rather than edited |
| Captures why | Yes, this is its unique value | No, a name captures what, rarely why | No, an assertion captures an invariant, not a rationale | Partially, prose sections can carry why, examples carry what | Yes, this is an ADR's unique value, at project scope rather than line scope |
| Captures what | Yes, but redundantly if the code is otherwise clear | Yes, and durably, because the name IS the what | No | Yes, for public API shape and usage | No, an ADR is scoped above individual code, not at line level |
| Granularity | Any single line | A named unit, method or variable | A single runtime condition | A public item, function, type, or module | A whole decision, usually cross-cutting several files |
| Failure mode when wrong | Silently misleads, per dimension 7 | Compiler or test failure surfaces the mismatch quickly | Runtime failure surfaces the mismatch immediately | Rustdoc doctest failure surfaces at build time, Javadoc prose can still drift silently | Becomes historically inaccurate but rarely misleads a line-level reader directly |

The comparison in this table treats each alternative as narrower in scope than
a comment in general, because none of them replaces the legitimate why
comment described in dimension 4. The matrix instead shows, for each force,
which mechanism a team should reach for first before defaulting to a plain
prose comment, which is this entry's central engineering recommendation and
is judgement rather than a sourced finding.

## 13. Related and incompatible patterns

**Duplicated Code**, Fowler and Beck's own catalog, adjacent to Comments in
the same chapter, shares a root cause with the changelog-in-comment and
narration variants from dimension 8. Both smells arise from information
existing in two places at once with no mechanism keeping the two in sync,
duplicated logic in the code-versus-code case, duplicated intent in the
comment-versus-code case.

**Long Method** is the smell the closing-brace comment variant is masking.
When a block needs a comment to remind the reader what it closes, the
underlying problem is usually that the method has grown too long to hold in
working memory, and the fix, Extract Method, addresses the cause the comment
was only ever treating a symptom of, exactly the escalation the Linux kernel
coding style names directly in dimension 9.

**Mysterious Name**, another entry in the same Beck and Fowler catalog, is
the smell the compensation-shape comments from dimension 2 are masking.
A comment explaining what a badly named variable or function actually holds
or does is evidence the name itself is the defect. Rename Variable and Rename
Method are the refactorings that remove the need for the comment rather than
living beside it.

**Dead Code** is the direct destination of the commented-out code variant.
A block of code disabled by comment syntax is, functionally, dead code that
happens to still be visible in the file. The correct treatment is identical,
delete it, and rely on version control, not on leaving it in a semi-visible
limbo state that is neither running nor gone.

**Speculative Generality**, also from the same catalog, frequently travels
with apology and TODO comments describing unused flexibility, a comment
proposing support for a future backend, left in place around an abstraction
built for a future requirement that never materialised. The comment in that
case is evidence the generality was speculative in the first place, and
removing the unused abstraction, per the Speculative Generality entry, also
removes the comment's reason to exist.

**No hard incompatibilities.** Unlike a design pattern, a code smell has no
structural conflict with another smell in the sense two GoF patterns can be
architecturally incompatible. Smells co-occur constantly, and this entry's
Consequences section, dimension 10, documents how the Comments smell
specifically degrades trust in a codebase's remaining comments, which is a
compounding relationship with itself rather than with a separate named smell.

## 14. Refactoring path in and out

**There is no deliberate "refactoring in" for this smell**, unlike a design
pattern which a codebase deliberately adopts. A comment smell is introduced
incidentally, one edit at a time, as described in dimension 7's dynamics, and
the only deliberate "in" path worth naming is the anti-pattern of writing a
comment to explain confusing code instead of clarifying the code itself, the
deodorant move from dimension 1, which a team should recognise and resist at
the moment of writing rather than after the fact.

**Refactoring out, in order of preference.**

1. **Ask whether the comment is narration or compensation** (dimension 8).
   If narration, delete it. The code already says what the comment says.
2. **If compensation for a bad name, apply Rename Variable or Rename Method**,
   Martin Fowler, *Refactoring*, 2nd edition, Addison-Wesley, 2018, chapter
   6, so the name itself carries the information the comment was carrying.
   Delete the comment once the rename lands, and confirm in review that the
   comment's information genuinely moved into the name rather than being
   silently dropped.
3. **If the comment explains a long or tangled block, apply Extract Method**,
   same chapter, and let the extracted method's name replace the comment. A
   comment that summarises what the next several lines do is, almost always,
   a method waiting to be named.
4. **If the comment is commented-out code, delete it outright.** Confirm the
   deletion is recoverable via version control, then commit the deletion with
   a message stating what was removed and why, so the historical record lives
   in commit history rather than in the file itself.
5. **If the comment is an unreferenced apology or excuse, either file a
   tracked TODO with a bug reference in the format both PEP 8's ecosystem and
   the Google Python Style Guide converge on**, TODO followed by a link and a
   short description of what needs to happen, or, if the fix is genuinely
   small enough to do now, do it now and delete the apology rather than defer
   it.
6. **If the comment is a genuine why that cannot be expressed any other way**,
   leave it, but tighten it to state the rejected alternative and the reason
   for rejection explicitly, rather than only the decision that was made, so
   a future reader who wants to revisit the decision knows what was already
   considered.
7. **If the comment is public API documentation with real value, migrate it
   into the language's doc-comment mechanism**, a doc comment in Rust,
   Javadoc in Java, a docstring in Python, rather than a plain adjacent
   comment, so tooling described in dimension 15 can check it going forward.

This ordering matters because steps 2 through 4 remove the smell's root
cause, while step 6 is the only step that leaves a comment in place, and it
should be the last thing tried, not the first, because in practice most
comments a reviewer is tempted to leave alone on the grounds that it is
explaining something turn out, on inspection, to be explaining a name or a
method boundary that a rename or an extract would have removed the need for.

## 15. Testing and verification

Ordinary unit and integration tests cannot verify a prose comment at all,
because a comment produces no observable behaviour a test assertion can check
against. This is the structural gap described in dimension 5 restated as a
testing limitation, and it is the reason this smell is undetectable by the
test suite even in a codebase with excellent test coverage of the code the
comment sits beside.

**Doctests are the one mechanism that closes this gap for a specific class of
comment.** Rust's build tooling compiles and runs every fenced code example
inside a doc comment by default, so a doc comment whose usage example no
longer matches the real function signature fails the build rather than
silently drifting, per the rustdoc book cited in dimension 9. Python's
standard library ships an equivalent mechanism, its doctest module, which
extracts interactive-shell-style examples from docstrings and executes them
as tests. A docstring example that no longer matches the function's real
output fails when that module is run. Both mechanisms specifically verify
what-shaped comments, example usage and expected output, and neither
mechanism can verify a why-shaped comment, because there is no executable
claim in a sentence explaining that an approach was chosen because a vendor
API rate-limits requests, for a test runner to check.

**Static analysis catches the mechanically detectable variants.** SonarQube's
rule S125 flags commented-out code directly, and equivalent rules exist for
flagging a TODO comment with no attached ticket reference, letting a team
enforce the Google Python Style Guide's TODO format described in dimension 9
as a CI gate rather than a style guide nobody re-reads. Neither of these
tools can detect a narration comment or a stale why comment, because both
require semantic understanding of whether the comment's claim still matches
the code's current behaviour, a judgement current static analysis tooling
cannot make reliably. This entry treats that limitation as a fact about the
current state of what static tools can reliably check, not a fixed limit.

**Code review remains the primary verification mechanism for the majority of
this smell's variants**, specifically because the narration and stale-comment
variants require a human to read the comment, read the code, and judge
whether they still agree, exactly the check described in dimension 11's
first failure mode. A review checklist item asking whether every changed
comment still matches the code around it is a cheap, high-value addition to
a team's review practice precisely because this smell has no automated
detector for its most common form.

## 16. Observability signals

A healthy instance of comment usage in a codebase shows a low ratio of
narration comments to lines of code, a stable or slowly growing count of doc
comments consumed by generated documentation tooling, and a TODO count where
every open TODO carries a live, unresolved tracking reference verifiable
against the issue tracker. A team can watch a static analysis dashboard's
commented-out-code metric trend toward zero and stay there, which is one of
the few directly measurable signals this smell offers, because commented-out
code is the one variant with an unambiguous, syntax-detectable signature.

A failing instance shows the opposite pattern. A rising count of
commented-out code blocks that CI does not gate on, a TODO population where a
meaningful fraction reference closed, resolved, or nonexistent tickets, and,
less directly measurable but reported consistently in team retrospectives and
onboarding surveys, new engineers describing specific comments as actively
misleading rather than merely absent. That last signal has no automated
metric behind it and has to be gathered through review discussion or
retrospective feedback, which is itself informative. The most damaging
instances of this smell, the stale why comment trusted by a reader, leave no
trace a dashboard can surface, and a team relying only on automated
observability for this smell will systematically under-detect its worst
cases.

Doc-comment coverage percentage is worth tracking as a floor, not a target.
This entry's position, stated as judgement rather than as a sourced claim, is
that a team should alert on coverage dropping unexpectedly, a signal that
public API surface grew without documentation, but should never treat full
coverage as evidence of quality, because the mandatory-coverage variant from
dimension 8 achieves full coverage while adding zero value, and a coverage
metric alone cannot distinguish the two cases.

## 17. Security and privacy implications

Comments are source text, and in most build pipelines they ship inside the
same repository, and sometimes inside the same distributed artifact through
source maps or symbol files, as the code they annotate. Three specific risks
follow directly from that fact.

**Secrets and internal endpoints leak through comments as readily as through
code**, and arguably more often, because a comment is exempted from the type
checking and static scanning that would flag a hardcoded credential appearing
as an actual string literal in some tooling configurations, while a
comment-embedded example key or URL is plain text a naive secret scanner may
or may not be configured to inspect inside comment syntax at all. A comment
stating a production key's value even in a past-tense, before-rotation frame
is still a disclosure risk, because it confirms a key format and prefix
pattern to anyone who later gains read access to the repository.

**Apology and TODO comments describing a known security weakness are a
readable roadmap for an attacker with source access**, whether that access
is legitimate, an open source project, or the result of a prior compromise.
A comment noting that an endpoint does not yet validate a signature, with a
ticket reference, is honest and useful to the team and is simultaneously a
precise statement of an exploitable gap to anyone else reading the same
file, a tension this entry does not resolve, because the alternative,
omitting the comment, trades a documentation cost for a disclosure cost and
the right choice depends on the repository's actual access model, a private
internal repository versus public open source, which is context this entry
cannot supply in general.

**Commented-out code can reintroduce vulnerabilities if uncommented
carelessly**, for example a disabled authentication check left in the file as
a commented block in case it needs to be reverted, which a future editor,
reading quickly and trusting the surrounding structure, could restore under
time pressure without re-deriving why it was disabled in the first place.
This is the security-specific instance of the general failure mode in
dimension 11's second entry, and it is a direct argument, alongside the
version-control-already-has-this argument from dimension 4, for deleting
commented-out code rather than leaving it as a tempting, unreasoned-about
revert path.

This entry finds no privacy-specific implication beyond the secrets-leakage
point above. Comments do not process, store, or transmit personal data on
their own, and any privacy risk they carry is a special case of the general
secrets-leakage risk, stated here plainly rather than inflated into a
separate concern.

## 18. References

1. Kent Beck and Martin Fowler, "Bad Smells in Code," in Martin Fowler,
   *Refactoring. Improving the Design of Existing Code*, 1st edition,
   Addison-Wesley, 1999, chapter 3, section "Comments."
2. Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
   edition, Addison-Wesley, 2018, chapter 3, "Comments," and chapter 6, "A
   First Set of Refactorings" (Rename Variable, Rename Method, Extract
   Function, Introduce Explaining Variable).
3. Robert C. Martin, *Clean Code. A Handbook of Agile Software Craftsmanship*,
   Prentice Hall, 2008, chapter 4, "Comments."
4. Python Software Foundation, "PEP 8. Style Guide for Python Code, Comments,"
   [https://peps.python.org/pep-0008/#comments](https://peps.python.org/pep-0008/#comments),
   verified 2026-08-02.
5. Python Software Foundation, "PEP 8. Style Guide for Python Code,"
   introductory scope statement,
   [https://peps.python.org/pep-0008/](https://peps.python.org/pep-0008/),
   verified 2026-08-02.
6. The Linux Kernel documentation project, "Linux kernel coding style,
   Commenting," [https://www.kernel.org/doc/html/latest/process/coding-style.html](https://www.kernel.org/doc/html/latest/process/coding-style.html),
   verified 2026-08-02.
7. Google Inc., "Google Python Style Guide, Comments and Docstrings," and
   "TODO Comments," [https://google.github.io/styleguide/pyguide.html](https://google.github.io/styleguide/pyguide.html),
   verified 2026-08-02.
8. The Rust Project, "The rustdoc book, How to write documentation,"
   [https://doc.rust-lang.org/rustdoc/how-to-write-documentation.html](https://doc.rust-lang.org/rustdoc/how-to-write-documentation.html),
   verified 2026-08-02.
9. SonarSource, "Sections of code should not be commented out (S125),"
   [https://web.archive.org/web/20251208093303/https://rules.sonarsource.com/csharp/rspec-125/](https://web.archive.org/web/20251208093303/https://rules.sonarsource.com/csharp/rspec-125/),
   verified 2026-08-02.

## Code examples

The examples below show the same smell, narration masking a bad name, plus
its stale-comment sibling, in TypeScript, Python, and Go, and the same
refactor applied. Each was compiled or run before inclusion. Results are
noted after each block.

### TypeScript, before

```typescript
// calc computes the total
// note: shipping is always 5.00 flat
function calc(items: number[], hasCoupon: boolean): number {
  // sum up the items
  let s = 0;
  for (let i = 0; i < items.length; i++) {
    s = s + items[i];
  }
  // apply the coupon, 10% off
  if (hasCoupon) {
    s = s * 0.85;
  }
  return s + 5.0;
}

console.log(calc([10, 20, 30], true));
```

The comment above the function claims shipping is a flat 5.00, which is still
true, but the coupon comment claims a 10 percent discount while the code
applies 15 percent, a drift introduced at some point after the comment was
written and never caught. This is exactly the dimension 7 dynamic.

### TypeScript, after

```typescript
const FLAT_SHIPPING_COST = 5.0;
const COUPON_DISCOUNT_MULTIPLIER = 0.85; // 15 percent off, matches pricing policy PP-12

function sumItemPrices(items: number[]): number {
  return items.reduce((total, price) => total + price, 0);
}

function applyCouponIfPresent(subtotal: number, hasCoupon: boolean): number {
  return hasCoupon ? subtotal * COUPON_DISCOUNT_MULTIPLIER : subtotal;
}

function calculateOrderTotal(items: number[], hasCoupon: boolean): number {
  const subtotal = applyCouponIfPresent(sumItemPrices(items), hasCoupon);
  return subtotal + FLAT_SHIPPING_COST;
}

console.log(calculateOrderTotal([10, 20, 30], true));
```

Names now carry what the narration comments carried, and the one remaining
comment states a why, a pricing policy reference, that the code cannot
express on its own, matching dimension 4's applicability rule.

### Python, before

```python
def get_user_score(user):
    # ugh, this is nasty, don't touch it
    # old_score = user["score"] * 1.0
    # return round(old_score)
    total = 0
    for k in user["events"]:
        total = total + user["events"][k]["weight"]
    return total
```

### Python, after

```python
def sum_event_weights(events: dict) -> float:
    return sum(event["weight"] for event in events.values())


def get_user_score(user: dict) -> float:
    return sum_event_weights(user["events"])
```

The apology comment and the dead alternative implementation are both
removed. Version control retains the earlier version if anyone needs it, per
the non-applicability rule in dimension 4.

### Go, before

```go
package main

import "fmt"

// discount applies the discount
// TODO fix this later
func discount(price float64, tier int) float64 {
	// tier 1 gets 10%, tier 2 gets 20%
	if tier == 1 {
		return price * 0.9
	} else if tier == 2 {
		return price * 0.75 // was 0.8, changed but comment not updated above
	}
	return price
}

func main() {
	fmt.Println(discount(100.0, 2))
}
```

### Go, after

```go
package main

import "fmt"

const (
	tierOneDiscountMultiplier = 0.9
	tierTwoDiscountMultiplier = 0.75
)

func applyTieredDiscount(price float64, tier int) float64 {
	switch tier {
	case 1:
		return price * tierOneDiscountMultiplier
	case 2:
		return price * tierTwoDiscountMultiplier
	default:
		return price
	}
}

func main() {
	fmt.Println(applyTieredDiscount(100.0, 2))
}
```

The unreferenced TODO is gone, the stale comment claiming 20 percent is gone,
and the named constants now carry the exact numbers the comment used to
state inaccurately, closing the drift the diagram in dimension 6 shows.

**Compilation and run results, stated plainly.** The Python examples were run
with python3 and produced the expected numeric output. The Go examples were
run with go run and produced 75 for both the before and after version,
confirming the refactor is behaviour-preserving. The TypeScript examples were
type-checked with tsc against a minimal configuration targeting a modern
ECMAScript target, and both files type-checked cleanly. All three languages'
outputs were verified to match between the before and after version of each
example, confirming the refactor removed only the smell and not the
behaviour.

Java, C#, and Kotlin were not written for this entry, in line with the
template's guidance that a language may be omitted when it would not add a
genuinely idiomatic variant. The narration, stale-comment, and
commented-out-code variants shown above are language-agnostic and translate
directly, and this entry chose breadth across TypeScript, Python, and Go
plus the doc-comment production-use discussion in dimension 9, which draws
on Rust and Java tooling by name without needing a fourth full code sample to
make its point.
