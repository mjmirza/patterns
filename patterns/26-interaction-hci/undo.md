---
name: Undo
slug: undo
family: 26-interaction-hci
category: Interaction and HCI
aliases: [Undo/Redo, Command History, Reversible Action]
first_described: "Warren Teitelman, undo built into BBN-LISP, 1971 (per Wikipedia's Undo article, citing the original Interlisp lineage)"
maturity: established
related: []
incompatible_with: []
verified: 2026-08-23
---

# Undo

## 1. Name, aliases, and lineage

Undo is the interaction technique that lets a person reverse the last
change they made to a document or system state, returning it to an
earlier version. Wikipedia's dedicated Undo article gives the direct
functional definition, undo erases the last change done to the document,
reverting it to an older state, and names its practical purpose, users can
explore and work without fear of making mistakes, because they can easily
be undone.

The feature's history predates the personal computer. Wikipedia's Undo
article credits the first documented undo feature to the File Retrieval
and Editing System at Brown University in 1968, records that Warren
Teitelman built undo into BBN-LISP in 1971, and notes Xerox PARC's Bravo
text editor had undo by 1974. The article also credits Xerox PARC
programmers with assigning the Ctrl-Z shortcut, which became the de facto
industry standard. It further states multi-level undo, letting a person
step back through a series of changes rather than only the single most
recent one, was introduced in the 1980s.

This entry could not verify Jenifer Tidwell's specific treatment of Undo
in Designing Interfaces, the book most catalogues of interaction patterns
point to for this pattern's naming. Every URL attempted for the book or
its companion site returned an unreachable result. Everything below
attributed to a named source was independently verified live and does not
rest on that unavailable source. See the honesty note at the end of this
entry.

The software-engineering implementation mechanism most closely associated
with undo is the Gang of Four Command pattern. Wikipedia's Command pattern
article confirms the link directly, if all user actions in a program are
implemented as command objects, the program can keep a stack of the most
recently executed commands, and when the user wants to undo a command, the
program simply pops the most recent command object and executes its
undo method. The same article confirms provenance, the command design
pattern is one of the twenty-three well-known Gang of Four design
patterns.

## 2. Problem and context

Any interface that lets a person change state, a text edit, a shape moved,
a value typed, a file deleted, creates a moment where the person can make
a mistake, and a mistake with no way back either forces extreme caution
before every action or punishes a slip with lost work. Wikipedia's Undo
article names the resulting freedom directly, undo lets users explore and
work without fear of making mistakes, because they can easily be undone.

The context this pattern arises in is any stateful, interactive system
where actions have a before and after that the system can represent, a
text document, a drawing canvas, a spreadsheet, a code editor, a
collaborative document. It does not arise, or arises only in a weakened
form, once an action's effect leaves the system's own state and becomes a
fact in the outside world, a message actually delivered to another
person, a payment actually charged. Section 4 below covers that boundary
directly, grounded in a real, documented example rather than an invented
generalization.

## 3. Forces

The dominant force is memory versus completeness. Wikipedia's Undo article
names the two competing history models directly, a linear model, where
only the last executed command can be undone, using a stack structure,
against a non-linear model, where a person can undo executed commands in
an arbitrary order. A linear stack is cheap to hold and simple to reason
about, a non-linear or branching history preserves more of what the person
actually did but costs more memory and more implementation complexity to
navigate correctly.

A second force is where the undoable state lives. The Gang of Four Command
pattern and the Memento pattern represent two different answers to the
same question, refactoring.guru's Memento pattern page states the
distinction plainly, you can use Command and Memento together when
implementing undo, in this case commands are responsible for performing
various operations over a target object, while mementos save the state of
that object just before a command gets executed. Command stores the
action taken, Memento stores the state before the action, and a real
system chooses, per action type, which is cheaper to reconstruct from.

A third force appears the moment more than one person can change the same
document at once. Figma's own engineering blog states the correctness
property a collaborative undo has to hold, if you undo a lot, copy
something, and redo back to the present, a common operation, the document
should not change, and names the mechanism it built to guarantee that, an
undo operation modifies redo history at the time of the undo, and likewise
a redo operation modifies undo history at the time of the redo. Without
that discipline, one person's undo can silently overwrite a collaborator's
concurrent edit, a failure mode that has no single-user analogue.

A fourth, narrower force is granularity, scoping undo to a single document
versus a whole workspace of open, related documents. The VS Code source
for its own undo and redo service distinguishes single-resource elements
from multi-resource elements directly, an optional method on the
multi-resource element is present to decompose into per-resource elements,
because a workspace-wide undo that touches several files at once needs
explicit synchronization a single-file undo does not.

## 4. Applicability and non-applicability

Reach for undo whenever a person can make a change to represented state
that the system can itself hold a prior version of, text, shape geometry,
a cell value, a file's position in a tree, a setting. Wikipedia's Undo
article frames exactly this scope, an interaction technique which is
implemented in many computer programs, and the freedom it buys, working
without fear of making mistakes, is the justification for building it even
when the underlying implementation work is nontrivial.

Do not reach for a literal reversal of an action once its effect has
already left the system as a real-world, externally-visible fact. Google's
own support documentation for Gmail's Undo Send confirms, mechanically,
that even a well-known undo feature avoids this boundary rather than
crossing it, the feature lets a person select a send cancellation period
of 5, 10, 20, or 30 seconds, a maximum thirty-second window. Because the
message's actual delivery is deliberately held back for that window rather
than reversed after departure, the feature works by preventing the send
from ever completing during the delay, not by retrieving a message that
already left the server. Once that window passes, no undo exists, because
none can, the message has become a fact in someone else's inbox. Any
action with the same shape, a payment already charged, a deletion already
propagated to a system outside your own, sits outside true undo's reach
for the identical structural reason, though this entry found no third
party source generalizing the principle explicitly beyond Gmail's own
documented mechanism, and states that as its own inference rather than a
sourced claim.

## 5. Structure

The Command pattern's undo shape, per refactoring.guru's Command pattern
page, turns a request into a stand-alone object that contains all
information about the request, and states the direct consequence, this
transformation lets you pass requests as method arguments, delay or queue
a request's execution, and support undoable operations. Its own worked
example shows the undo method restoring a previously saved backup, method
undo is editor.text = backup, and the application holding the global
command history as just a stack, pushing an executed command and popping
the most recent one on undo.

The same source draws an important refinement, not every command belongs
in that history. Its worked example distinguishes a copy command, isn't
saved to the history since it doesn't change the editor's state, from a
cut command, does change the editor's state, therefore it must be saved to
the history, with the application logic deciding per command whether to
push it.

The Memento pattern gives an alternative participant structure for the
same problem, per Wikipedia's Memento pattern article, an originator holds
the real state and produces a memento, a restricted, immutable snapshot of
that state, a caretaker holds a collection of mementos without seeing
their internals, and to roll back to the state before the operations, the
caretaker returns the memento object to the originator. The article's
worked Java example has a caretaker maintain a list of the originator's
mementos, so a person can request multiple mementos, and choose which one
to roll back to, itself a concrete example of selective, non-linear undo
built on top of Memento rather than a strict single-step stack.

## 6. ASCII structure diagram

The Command-pattern shape:

```
  user action
       |
       v
  +-----------+        +------------------+
  |  Command  | -----> | History (stack)  |
  | execute() |        | push on execute  |
  | undo()    |        | pop on undo      |
  +-----------+        +------------------+
       |                       |
       v                       v
  editor / document  <---  undo() called on
      state changes         popped command
```

The Command-plus-Memento shape, where the command performs the action and
a memento carries the state needed to reverse it:

```
  +-----------+   creates   +-------------------+
  |  Command  | ----------> | Memento (snapshot) |
  +-----------+             | held by Caretaker  |
       |                    +-------------------+
       | on undo                    |
       v                            v
  Originator  <----------------  restore state
  (the real object)              from memento
```

## 7. Dynamics

In the linear Command-stack model, per Wikipedia's Command pattern
article, each executed action pushes its command object onto a history
stack, an undo pops the most recent command and calls its undo method, and
a subsequent redo, in the common implementation, re-executes the popped
command from a parallel redo stack. Wikipedia's general Undo article
confirms the two-model split at runtime, a linear model where only the
last executed command can be undone, against a non-linear model where a
person can undo executed commands in an arbitrary order.

Collaborative, multi-user undo has a materially different runtime shape,
because a stack alone cannot say whose edit is being undone. Figma's
engineering blog states the mechanism its multiplayer system depends on
directly, figma's multiplayer servers keep track of the latest value that
any client has sent for a given property on a given object, and that an
undo operation modifies redo history at the time of the undo, and likewise
a redo operation modifies undo history at the time of the redo, so that
cycling through undo and redo back to the present state never silently
discards a collaborator's concurrent change.

VS Code's own undo and redo service source shows a third runtime shape,
workspace-scoped, multi-file undo. Its multi-resource element type carries
an optional prepareUndoRedo method described in the source as being for
synchronization preparation, and an UndoRedoGroup and UndoRedoSource pair
of classes are described as managing operation sequencing with
incrementing order values, enabling logical bundling of related edits
across the undo stack, machinery a single-document, single-user editor has
no need for.

## 8. Implementation variants

The plain Command-stack variant, one history stack per document, is the
default shape most single-user editors implement, per the structure and
dynamics already covered in sections 5 and 7, sourced to refactoring.guru
and Wikipedia's Command pattern articles.

The Memento-backed variant stores full or partial state snapshots rather
than reversible deltas. Wikipedia's Memento pattern article notes it is
explicitly immutable, the memento object itself is immutable, and lists
its own real uses beyond undo, uses of this design pattern include undo,
version control, and serialization, all three sharing the same
save-a-snapshot, restore-a-snapshot shape.

The collaborative, conflict-aware variant is the one Figma documents in
production. Its engineering blog states the system was built inspired by
CRDTs, rather than using Operational Transforms, and gives the specific
reason the team rejected Operational Transformation, unnecessarily
complex, preferring a simpler system that was easier to reason about.
Wikipedia's Operational Transformation article corroborates why undo
specifically is the hard part of that space, the essential difference
between convergence and intention preservation is that the former can
always be achieved by a serialization protocol, but the latter may not be
achieved by any serialization protocol if operations were always executed
in their original forms, and separately notes achieving the nonserialisable
intention preservation property has been a major technical challenge, and
that different Operational Transformation systems support different levels
of undo capability, some only chronological undo, others any operation,
some none at all.

The workspace-scoped variant, VS Code's IUndoRedoService, generalizes a
single-document Command stack to many files at once, per section 7, with a
readonly-resource list, an optional split method to decompose a
multi-resource element back into per-resource elements, and the
synchronization step already described.

The last-writer-wins delta variant, GitHub's Scientist library, applies
the same before-and-after comparison idea to a different problem, safely
refactoring critical paths, rather than to undo directly, refactoring.guru
and Wikipedia's descriptions of Command and Memento do not cover Scientist,
but Stripe's own use of Scientist for a real database migration is a
documented, named production use of the comparison technique this entry's
Section 9 covers directly.

## 9. Known production uses

VS Code's own source repository documents its undo and redo architecture
directly, not a blog post describing it secondhand, the primary service
decorator that manages undo and redo operations across the editor, built
from IResourceUndoRedoElement for a single file and IWorkspaceUndoRedoElement
for changes spanning several files at once, with UndoRedoGroup and
UndoRedoSource classes managing operation sequencing with incrementing
order values.

Figma's engineering blog documents a real, production, multi-user
collaborative undo system, built from a custom multiplayer system inspired
by CRDTs, rather than using Operational Transforms, with the explicit
undo-redo-history-rewriting guarantee already quoted in sections 3, 7, and
8, so that cycling undo and redo back to the present never silently
changes the document.

Google's Gmail Undo Send is a real, named, currently documented production
feature, covered directly in section 4, that intentionally implements a
delayed-commit trick rather than a true reversal, a maximum thirty-second
send cancellation period, precisely because the action it appears to undo
is not reversible once it has actually happened.

## 10. Consequences

Positive. A person can explore and correct mistakes without the cognitive
overhead of caution before every action, the exact benefit Wikipedia's
Undo article names directly. A well-built undo stack also gives a natural,
free audit trail of what changed and in what order, since Command-pattern
implementations already hold that sequence to support undo itself.

Negative. Every command or memento held in a history costs memory, and
this entry could not find a source discussing unbounded undo-stack growth
as a named, documented failure mode, so this specific cost is stated here
as a plausible engineering consequence of the mechanism already sourced in
section 5, not as an independently sourced claim. Collaborative undo adds
real implementation cost beyond a single-user stack, Figma's own
engineering blog frames the correctness property it had to specifically
design for, not something a naive port of a single-user undo stack
provides for free. Workspace-scoped undo carries a similar cost, VS Code's
multi-resource element needing an explicit synchronization step before a
multi-file undo can safely proceed.

## 11. Failure modes and misuse

The most visible single-user failure mode is a stack that grows without
bound, holding every command or full-state memento for the life of a long
editing session, a cost this entry can name as a plausible consequence of
the sourced mechanism in section 5 but could not find independently
documented, and flags as inference rather than sourced fact.

The collaborative failure mode is more concretely sourced. Figma's own
engineering blog states the exact bug shape its undo design exists to
prevent, if you undo a lot, copy something, and redo back to the present,
the document should not change, naming, by implication, what happens
without the fix, an undo or redo silently overwriting or discarding a
collaborator's concurrent edit, corrupting the shared document in a way a
single-user editor's history model would never surface.

A workspace-scoped failure mode follows from the same root cause at a
different scope. VS Code's own source models a multi-file undo as needing
an explicit prepareUndoRedo synchronization step precisely because a naive
undo across several files at once, applied without that coordination, can
leave the files in a mutually inconsistent state, one file rolled back,
a related file left as it was.

A misuse pattern that recurs across every variant is treating undo as a
substitute for a genuine confirmation step on an action that is not truly
reversible. Section 4's Gmail example shows the correct response to that
temptation, a bounded delayed-commit window rather than a false promise of
undo, and a system that instead lets a person believe an irreversible
action can be undone, when in fact it cannot once its effect has left the
system, misleads the person at the exact moment they most need an accurate
answer.

## 12. Trade-off matrix

| Approach | Memory cost | Implementation complexity | Multi-user support |
|---|---|---|---|
| Command stack (delta-based) | Low, stores only what is needed to reverse an action, per refactoring.guru's editor.text = backup example | Moderate, every action type must correctly implement both execute and undo | Not designed for it, VS Code's own model needs an added synchronization step to extend a single-user command stack to multi-file workspaces |
| Memento (snapshot-based) | Higher, full or partial object-state snapshots per memento, per Wikipedia's Memento article's list of held snapshots | Lower per-action complexity, no per-action reversal logic needed, but higher aggregate state size, explicitly composable with Command per refactoring.guru | Same limitation as Command alone, no inherent multi-user awareness |
| CRDT-based collaborative undo (Figma's model) | Not quantified in the sources available to this entry | Figma's own stated reason for choosing this over Operational Transformation was that OT was unnecessarily complex, yet still required deliberate undo and redo history rewriting logic to reach correctness | Purpose-built for it, this is the entire reason Figma built the system, per its own engineering blog |

## 13. Related and incompatible patterns

Undo's primary implementation relationship is with the Gang of Four
Command pattern, covered throughout sections 1, 5, 7, and 8, where each
user action becomes a command object carrying enough information to both
perform and reverse itself, and with the Gang of Four Memento pattern,
which refactoring.guru documents as explicitly composable with Command
rather than a competing alternative, mementos save the state of that
object just before a command gets executed. This catalogue's own family
01 design-patterns entries for command and memento, where present, are the
direct cross-references for the implementation mechanism this entry
describes at the interaction-pattern level.

This entry found no sourced connection between Undo and any other entry
currently in family 26-interaction-hci, since Undo is the first entry
authored in that family, and per this repository's own duplicate-detection
guidance, no forced relationship is asserted here in its absence.

## 14. Refactoring path in and out

Introducing undo into a system that lacks it starts by identifying which
user-triggered mutations are worth reversing at all, refactoring.guru's
own worked example draws this line directly, distinguishing a copy action,
which changes nothing and does not belong in the history, from a cut
action, which changes state and must be recorded. Each mutating action is
then wrapped as a command object exposing an execute method and an undo
method, or paired with a memento captured just before the action runs, per
the Command-and-Memento composition already covered in sections 5 and 8,
and a history stack is introduced to hold the resulting sequence.

Removing undo, when a feature genuinely does not need it, means deleting
the history stack and the per-action reversal logic, returning each action
to a plain, direct state mutation with no wrapping object. The entries
where this trade genuinely reverses, a feature moving from single-user to
collaborative, are the ones where the withdrawal path instead goes the
other direction, from a Command stack toward a system with the explicit
conflict-aware guarantees Figma's engineering blog describes, since a
naive Command stack ported as-is into a multi-user context reproduces the
exact corruption failure mode named in section 11.

## 15. Testing and verification

This entry could not find a source directly discussing test methodology
for undo correctness, such as verifying exact-state restoration after a
long sequence of actions, or the specific edge cases at the boundaries of
a history, undoing at an empty history, redoing at the most recent state.
This is stated here plainly as a gap rather than filled with an invented
testing recipe. What this entry can state with a source is the correctness
property a test suite for a collaborative undo implementation would need
to assert, Figma's own engineering blog names the exact invariant, if you
undo a lot, copy something, and redo back to the present, a common
operation, the document should not change, which is itself a directly
testable property, a round trip of undo and redo operations back to the
starting point must leave the document byte-for-byte identical to before
the round trip began.

## 16. Observability signals

This entry found no source discussing undo or redo invocation frequency as
a product or user-experience health signal, the idea that a spike in undo
usage on a specific action might indicate that action's own interface is
confusing or error-prone. This is a plausible and reasonable engineering
inference, but this entry has no citation for it and states that
explicitly rather than presenting it as a sourced fact. What is directly
observable from the sourced mechanisms above is history depth, how many
commands or mementos a given session's stack is currently holding, since
an unusually deep stack for the type of document being edited is a direct,
inspectable signal of the memory-cost consequence named in section 10.

## 17. Security and privacy implications

This entry made a real, direct attempt to source a security or privacy
implication specific to undo history retention, whether a person's belief
that a deletion or edit is gone can be undermined by an undo history that
still holds the earlier state. CWE-212, Improper Removal of Sensitive
Information, was checked directly for this, and covers document metadata,
EXIF data, network headers, and email addresses left in exported files,
but does not address undo history, clipboard history, or edit history
retention at all, an explicit, verified absence of coverage rather than an
unfetched source. Wikipedia's general Undo article was also checked and
makes no mention of privacy or security implications of undo history
retention. This entry reports that absence honestly, as a gap in what
could be verified, rather than inventing a concern neither source
supports.

## 18. References

1. Wikipedia contributors. "Undo." Wikipedia, The Free Encyclopedia.
   https://en.wikipedia.org/wiki/Undo. Verified 2026-08-23.
2. Wikipedia contributors. "Command pattern." Wikipedia, The Free
   Encyclopedia. https://en.wikipedia.org/wiki/Command_pattern. Verified
   2026-08-23.
3. Wikipedia contributors. "Memento pattern." Wikipedia, The Free
   Encyclopedia. https://en.wikipedia.org/wiki/Memento_pattern. Verified
   2026-08-23.
4. Wikipedia contributors. "Operational transformation." Wikipedia, The
   Free Encyclopedia. https://en.wikipedia.org/wiki/Operational_transformation.
   Verified 2026-08-23.
5. refactoring.guru. "Command." https://refactoring.guru/design-patterns/command.
   Verified 2026-08-23.
6. refactoring.guru. "Memento." https://refactoring.guru/design-patterns/memento.
   Verified 2026-08-23.
7. Google. "Undo an email in Gmail." Gmail Help.
   https://support.google.com/mail/answer/2819488. Verified 2026-08-23.
8. Figma. "How Figma's multiplayer technology works." Figma Blog.
   https://www.figma.com/blog/how-figmas-multiplayer-technology-works/.
   Verified 2026-08-23.
9. Microsoft. "undoRedo.ts, vs/platform/undoRedo/common." microsoft/vscode,
   GitHub. https://github.com/microsoft/vscode/blob/main/src/vs/platform/undoRedo/common/undoRedo.ts.
   Verified 2026-08-23.

**Evidence grade.** mixed

**Most solid findings.** The Command and Memento pattern mechanics
(sections 5, 7, 8, 13, 14) are independently corroborated across two
sources each. The Gmail Undo Send delayed-commit mechanism (section 4) is
sourced directly to Google's own current support documentation. Figma's
collaborative undo correctness guarantee (sections 3, 7, 8, 10, 11, 15) is
sourced directly to Figma's own engineering blog and stated with a direct
quote.

**Unverified or unclear.** Jenifer Tidwell's specific treatment of Undo in
Designing Interfaces could not be reached from any of six attempted URLs
and is not relied on anywhere in this entry. Apple's Human Interface
Guidelines pages for undo and redo returned only page titles with no
retrievable body content and are likewise not relied on. A concrete,
named example of tree or graph-shaped, as opposed to linear, undo history
(such as Vim's undo branches or Emacs' undo-tree) could not be reached
live and is represented only by Wikipedia's general taxonomy naming the
non-linear model as a category. The pre-ML lineage claim in dimension 1
attributed to Wikipedia's own sourcing is reported at the depth Wikipedia
itself documents it, this entry did not independently verify the Brown
University 1968 or Teitelman 1971 claims against a primary source beyond
Wikipedia's own citation trail.

## Code

TypeScript, a Command-stack undo/redo manager operating on a simple text
buffer, following the structure in section 5:

```typescript
interface Command {
  execute(): void;
  undo(): void;
}

class ReplaceTextCommand implements Command {
  private before = "";

  constructor(
    private buffer: { text: string },
    private newText: string,
  ) {}

  execute(): void {
    this.before = this.buffer.text;
    this.buffer.text = this.newText;
  }

  undo(): void {
    this.buffer.text = this.before;
  }
}

class UndoManager {
  private undoStack: Command[] = [];
  private redoStack: Command[] = [];

  run(command: Command): void {
    command.execute();
    this.undoStack.push(command);
    this.redoStack = [];
  }

  undo(): boolean {
    const command = this.undoStack.pop();
    if (!command) return false;
    command.undo();
    this.redoStack.push(command);
    return true;
  }

  redo(): boolean {
    const command = this.redoStack.pop();
    if (!command) return false;
    command.execute();
    this.undoStack.push(command);
    return true;
  }

  historyDepth(): number {
    return this.undoStack.length;
  }
}

const buffer = { text: "" };
const manager = new UndoManager();
manager.run(new ReplaceTextCommand(buffer, "hello"));
manager.run(new ReplaceTextCommand(buffer, "hello world"));
manager.undo();
console.log(buffer.text);
```

Python, the same Command-stack shape using a dataclass-backed Memento for
the reversible state, following the composition described in sections 5
and 8:

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TextMemento:
    text: str


class TextDocument:
    def __init__(self) -> None:
        self.text = ""

    def snapshot(self) -> TextMemento:
        return TextMemento(text=self.text)

    def restore(self, memento: TextMemento) -> None:
        self.text = memento.text


class ReplaceTextCommand:
    def __init__(self, document: TextDocument, new_text: str) -> None:
        self.document = document
        self.new_text = new_text
        self.before: Optional[TextMemento] = None

    def execute(self) -> None:
        self.before = self.document.snapshot()
        self.document.text = self.new_text

    def undo(self) -> None:
        if self.before is not None:
            self.document.restore(self.before)


@dataclass
class UndoManager:
    undo_stack: list = field(default_factory=list)
    redo_stack: list = field(default_factory=list)

    def run(self, command: ReplaceTextCommand) -> None:
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            return False
        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)
        return True


if __name__ == "__main__":
    doc = TextDocument()
    manager = UndoManager()
    manager.run(ReplaceTextCommand(doc, "hello"))
    manager.run(ReplaceTextCommand(doc, "hello world"))
    manager.undo()
    print(doc.text)
```

Go, a Command-stack manager with an explicit history-depth accessor,
useful for the observability signal named in section 16:

```go
package main

import "fmt"

type Command interface {
	Execute()
	Undo()
}

type ReplaceTextCommand struct {
	buffer  *string
	newText string
	before  string
}

func (c *ReplaceTextCommand) Execute() {
	c.before = *c.buffer
	*c.buffer = c.newText
}

func (c *ReplaceTextCommand) Undo() {
	*c.buffer = c.before
}

type UndoManager struct {
	undoStack []Command
	redoStack []Command
}

func (m *UndoManager) Run(cmd Command) {
	cmd.Execute()
	m.undoStack = append(m.undoStack, cmd)
	m.redoStack = nil
}

func (m *UndoManager) Undo() bool {
	n := len(m.undoStack)
	if n == 0 {
		return false
	}
	cmd := m.undoStack[n-1]
	m.undoStack = m.undoStack[:n-1]
	cmd.Undo()
	m.redoStack = append(m.redoStack, cmd)
	return true
}

func (m *UndoManager) Redo() bool {
	n := len(m.redoStack)
	if n == 0 {
		return false
	}
	cmd := m.redoStack[n-1]
	m.redoStack = m.redoStack[:n-1]
	cmd.Execute()
	m.undoStack = append(m.undoStack, cmd)
	return true
}

func (m *UndoManager) HistoryDepth() int {
	return len(m.undoStack)
}

func main() {
	buffer := ""
	manager := &UndoManager{}
	manager.Run(&ReplaceTextCommand{buffer: &buffer, newText: "hello"})
	manager.Run(&ReplaceTextCommand{buffer: &buffer, newText: "hello world"})
	manager.Undo()
	fmt.Println(buffer)
}
```
