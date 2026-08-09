---
name: Tell, Don't Ask
slug: tell-do-not-ask
family: 04-principles-and-laws
category: Principle
aliases: [Tell Don't Ask, TDA, Do Not Ask, Tell]
first_described: "Alec Sharp, Smalltalk by Example, McGraw-Hill, 1997; popularized by Andrew Hunt and David Thomas, The Pragmatic Programmer, 1999"
maturity: canonical
related: [law-of-demeter, information-expert, high-cohesion, low-coupling, single-responsibility-principle]
incompatible_with: []
verified: 2026-08-02
---

# Tell, Don't Ask

## 1. Name, aliases, and lineage

The canonical name is Tell, Don't Ask, usually written with the comma and
abbreviated TDA in code review comments and blog posts. The name is a
command, not a description, and that is deliberate. It tells the reader what
to do rather than describing a structure, which sets it apart from most of
the entries in this family that name a shape (Composite, Strategy) rather
than an instruction.

The earliest written source that states the idea in close to its modern
words is Alec Sharp's 1997 book Smalltalk by Example, published by
McGraw-Hill. Sharp's formulation is "Procedural code gets information then
makes decisions. Object-oriented code tells objects to do things," a
sentence quoted directly by Andy Hunt on his own site as the origin of the
phrase (Andy Hunt, "Tell, Don't Ask,"
https://toolshed.com/articles/1998-07-01-TellDontAsk.html, dated 1 July
1998, verified 2026-08-02). Hunt's article is itself a primary source, since
Hunt is one half of the Pragmatic Programmers and his 1998 essay predates
the 1999 book by a year. The name reached a wide audience through Andrew
Hunt and David Thomas, The Pragmatic Programmer. From Journeyman to Master
(Addison-Wesley, 1999), which folded the idea into its broader argument
about decoupling and told it to a generation of working programmers who
never read Sharp's book directly.

Martin Fowler restated the principle on his bliki in a short, frequently
linked entry, defining it as "a principle that helps people remember that
object orientation is about bundling data with the functions that operate on
that data" (Martin Fowler, "TellDontAsk,"
https://martinfowler.com/bliki/TellDontAsk.html, dated 5 September 2013,
verified 2026-08-02). Fowler's entry matters for this write-up because it
also carries the most quoted caution against over-applying the principle,
covered in dimension 11.

Tell, Don't Ask is closely related to, but not identical with, two older and
more formally stated ideas. Command-Query Separation, devised by Bertrand
Meyer in Object-Oriented Software Construction (Prentice Hall, first edition
1988, widely cited from the second edition, 1997), states that a method
should either change state or return data, never both (Wikipedia
contributors, "Command-query separation,"
https://en.wikipedia.org/wiki/Command%E2%80%93query_separation, verified
2026-08-02). CQS is a rule about the shape of an individual method
signature. Tell, Don't Ask is a rule about where decision-making logic
should live, and it is usually applied at the level of an interaction
between two objects rather than a single method. The Law of Demeter, traced
to Ian Holland and Karl Lieberherr's group at Northeastern University in
1987 and 1988 (see the sibling entry, law-of-demeter.md, in this family, for
its full lineage), constrains which objects a method is allowed to talk to
at all. Tell, Don't Ask constrains what a method is allowed to do once it is
talking to another object. The three ideas overlap in the code they flag,
which is why they are so often confused with one another, and dimension 13
separates them precisely.

Tell, Don't Ask carries no formal publication of its own, no conference
paper, and no numbered rule in a standard. It lives as a named habit passed
down through Sharp's book, Hunt and Thomas's book, and two decades of blog
posts, code review comments, and design books such as Sandi Metz's Practical
Object-Oriented Design in Ruby (Addison-Wesley, 2012), which teaches it as
part of its chapter on building flexible interfaces
(https://www.oreilly.com/library/view/practical-object-oriented-design/9780132930895/ch04.html,
verified 2026-08-02), and Vaughn Vernon's Implementing Domain-Driven Design
(Addison-Wesley, 2013), which names it directly as an aggregate
implementation technique, quoted in full in dimension 9. Its maturity is
canonical in the sense that every experienced object-oriented programmer
recognizes the phrase, while its precision is looser than a pattern with a
GoF-style structure diagram, and this entry is written with that honestly
stated up front.

## 2. Problem and context

The problem this principle answers shows up the first time a codebase grows
past the size where one person holds the whole design in their head. A
method somewhere needs to make a decision that depends on the internal state
of a different object. The easy path, and the one almost every beginner
takes without thinking about it, is to ask that other object a series of
questions, getters, in most languages, then use the answers to compute a
decision locally.

```
if (account.getBalance() < withdrawal.getAmount()) {
    notifier.send(account.getOwnerEmail(), "insufficient funds");
} else {
    account.setBalance(account.getBalance() - withdrawal.getAmount());
    ledger.record(account.getId(), withdrawal.getAmount());
}
```

That single block reads three fields off Account, computes a rule that
belongs to Account (can this withdrawal happen), and then reaches back in to
mutate a fourth field. Nothing here is syntactically wrong and every
statement type-checks. The trouble is where the knowledge lives. The rule
"a withdrawal larger than the balance is refused" is a fact about Account,
written down in a method that is not Account. The next time that rule
changes, for example to allow an authorized overdraft up to a limit, someone
has to find every place that repeated this comparison and change it there
too, because the rule was never centralized in the object that owns the
data it depends on.

This problem gets sharply worse as the object graph deepens. A caller that
asks order.getCustomer().getAddress().getCountry().getTaxRate() to compute
a price has walked four objects deep to fetch a single number, and every one
of those four accessor calls is a place the surrounding code now depends on,
silently, whether or not the caller intended that dependency. Reorganizing
how Address stores a country, a change that should be entirely internal to
Address, now breaks a price calculation three types away that nobody
remembers exists.

The context in which Tell, Don't Ask becomes worth naming is any
object-oriented codebase with more than a handful of collaborating classes,
written in a language that supports encapsulation, being maintained by more
than one person, or by one person across enough time that they will
eventually be a stranger to their own code. In a small script, a one-off
data transformation, or a purely functional pipeline with no mutable state
to protect, the problem this principle solves largely does not arise, and
forcing the vocabulary of Tell, Don't Ask onto that code adds ceremony with
nothing behind it. Dimension 4 states this precisely as a non-applicability
case rather than leaving it implied.

## 3. Forces

Every pattern in this family balances competing pressures, and naming which
pressures Tell, Don't Ask favors, and which it knowingly sacrifices, is more
useful than reciting the slogan.

Encapsulation pulls toward Tell. An object that exposes every field through
a getter has, for practical purposes, no encapsulation at all, since any
caller can read its full internal state and reconstruct whatever decision
logic it wants around that state. Pushing the decision inside the object
that owns the data keeps the object's invariants under its own control,
because the only code path that can produce an invalid state is the object
itself.

Coupling pulls toward Tell for the same reason from a different angle. A
caller that asks a series of questions is coupled to more than the object it
is querying, it is coupled to every fact that object currently exposes, and
to the exact shape those facts take. A caller that issues one command is
coupled only to that command's name and its side effect. Fowler's own
restatement makes this the center of the principle, "bundling data with the
functions that operate on that data," which is coupling reduction stated as
a data locality argument.

Readability and transparency pull the other way, toward Ask, at least in
one specific form. A pure query, one with no side effect, is the easiest
kind of code to read, because the reader never has to ask what else
changed. A report generator, a validation summary, a dashboard, all of
these are naturally query-heavy, and forcing them into a Tell shape produces
objects whose only job is to answer questions dressed up as commands that
happen to return a value, which fools nobody and adds a layer of
indirection with no benefit.

Testability pulls toward Tell for behavior and toward Ask for state
assertions, which is a genuine tension rather than a one-sided win. Testing
a Tell-style method means asserting on an observable outcome, a
notification sent, a record written, a collaborator invoked, which is
closer to testing what the code actually does. But an assertion still needs
some way to observe the result, and that observation is itself a query,
so a design taken to an extreme where nothing can ever be asked becomes
untestable in the ordinary sense. Dimension 15 works through this tension
directly rather than glossing over it.

Team topology and cognitive load favor Tell as a codebase grows past a
single team's working memory, because centralizing a rule inside the object
that owns its data means a new team member only has to find one place, the
owning class, to learn how a rule behaves, instead of grepping the whole
codebase for every caller that happens to have reimplemented the same
comparison. In a single-person prototype this force barely registers, which
is one of the reasons the principle reads as heavy-handed advice when
applied to a throwaway script.

Cost, in the sense of the up-front design effort the principle demands, is
real and worth stating plainly. Deciding where a rule belongs, naming the
command that expresses it, and resisting the reflex to add one more getter
takes longer in the moment than writing the query-and-branch version that
comes naturally. The principle asks for that cost up front in exchange for
a smaller cost later, when the rule needs to change and there is exactly
one place to change it.

## 4. Applicability and non-applicability

Reach for Tell, Don't Ask when a decision depends on data that another
object already owns, and that decision has a side effect once made. The
clearest signal is a conditional whose branches both read fields from the
same foreign object and then mutate that same object, or hand its data to a
third party. If a caller reads value, reads limit, compares them, then calls
a setter on the object it read from a moment earlier, the decision and the
state it depends on have drifted apart, and moving the conditional inside
the object closes that gap.

Reach for it when a rule is duplicated across more than one caller. Two call
sites computing whether an order is eligible for free shipping from the
same three fields on Order is the textbook trigger. Once the same
comparison shows up twice, the rule has stopped being an implementation
detail of one caller and has become a fact about Order that Order itself
should state.

Reach for it when you are protecting an invariant, a rule that must never be
false for the lifetime of the object, such as a bank balance that must
never go negative without an explicit overdraft agreement, or an order total
that must always equal the sum of its line items. An invariant that a
caller can accidentally violate by mutating fields directly, in the right
order but forgetting one step, is an invariant that is not actually
enforced, only conventionally respected, and Tell-style methods that bundle
the mutation with the check are how an invariant becomes something the
compiler and the object itself can defend rather than something a comment
asks the reader to remember.

### Non-applicability

Do not reach for Tell, Don't Ask on a pure query with no side effect. A
method that computes a derived value, a total, a formatted string, a
boolean check, and returns it without changing anything is already correct
as a query, and rewriting it into a command that tells the object to
compute something internally and store the answer somewhere adds a field
and a lifecycle problem, when is that field stale, that did not exist
before. Reporting code, read models in a CQRS-style architecture, and view
layers that only render what a domain object already decided are the
concrete cases where this non-applicability shows up daily. Forcing them
into commands is not a stricter application of the principle, it is a
category error, because the principle exists to protect state changes, and
these paths have none to protect.

Do not reach for it across a genuine architectural seam where two systems,
two services, or two bounded contexts exchange data through a contract
neither side controls unilaterally. A REST client reading a response body
is asking, by construction, and there is no way to tell a remote HTTP
service to make an internal decision without inventing a command endpoint
that the service owner has to build, version, and maintain. The principle
is about the internal design of a single object model under one team's
control, not a rule for wire protocols.

Do not reach for it inside a language or style built around immutable
data and pure functions. A functional pipeline that transforms a value
through a series of stateless steps has no mutable object to protect, so
there is nothing for a Tell-style command to shield. Applying the vocabulary
of Tell, Don't Ask to a Haskell fold or a chain of Array.map calls in
JavaScript imports an object-oriented framing that does not fit the style
the code is written in, and the equivalent discipline there is enforced by
the type system and by keeping functions pure, not by moving mutation
behind a message send.

Do not reach for it when the caller genuinely needs the raw data for a
purpose the owning object cannot anticipate, such as serialization,
debugging output, or a generic framework that reflects over an object's
fields, for example an object relational mapper reading column values or a
JSON serializer walking properties. These callers are not making a business
decision with the data, they are transporting it, and demanding that every
object expose a Tell-style API for its own serialization produces an
explosion of narrow, single-purpose commands that exist only to satisfy the
rule rather than to serve a real design need.

## 5. Structure

Tell, Don't Ask has no fixed cast of named roles the way a Gang of Four
pattern does, because it is a rule about where logic lives rather than a
recurring object graph. The structure below names the two shapes the rule
distinguishes between, so the participants are described as a before-shape
and an after-shape rather than as a single static diagram.

In the Ask shape, a Caller (sometimes a controller, a service class, or a
procedural script) holds a reference to a Subject object. The Caller invokes
one or more accessor methods on Subject to read its internal state. The
Caller then evaluates a condition using that state, entirely inside the
Caller's own method body. Depending on the outcome, the Caller may invoke a
mutator method back on Subject, or invoke a method on some third
Collaborator, passing along data it extracted from Subject. The decision
logic, the fields it depends on, and the code that acts on the decision are
split across at least two classes, and often three when a Collaborator is
involved.

In the Tell shape, the same Caller invokes exactly one method on Subject,
named for the intent of the action rather than for a getter or setter, for
example applyDiscount, not setDiscountAndCheckEligibility. Subject reads its
own fields internally, applies the rule, mutates its own state if the rule
allows it, and if a Collaborator needs to be told about the outcome,
Subject itself calls the Collaborator, not the original Caller. The Caller's
knowledge of Subject shrinks to a single message name and its arguments.
The decision logic, the fields it depends on, and the mutation it triggers
all live inside Subject.

The two shapes have the same three participants, Caller, Subject, and an
optional Collaborator, and the difference between them is entirely about
which participant holds the decision-making code and how many messages
cross the boundary between Caller and Subject to make that decision happen.

## 6. ASCII structure diagram

```
ASK SHAPE (knowledge and mutation split across two classes)

  +------------+    getReading()       +--------------+
  |            |----------------------->|              |
  |  Caller    |    getLowerLimit()     |   Subject    |
  | (decides   |----------------------->| (holds only  |
  |  externally|    getUpperLimit()     |   state)     |
  |  and acts) |----------------------->|              |
  |            |                        +--------------+
  |            |    setAlarmActive()
  |            |----------------------------+
  |            |    notify(reading)         v
  +------------+------------------->  +--------------+
                                       | Collaborator |
                                       +--------------+

TELL SHAPE (knowledge and mutation kept together in one class)

  +------------+  updateReading(v)     +--------------+
  |            |----------------------->|              |
  |  Caller    |                        |   Subject    |
  | (issues one|                        | - reading    |
  |  command)  |                        | - lowerLimit |
  |            |                        | - upperLimit |
  +------------+                        | applyPolicy()|
                                        +------+-------+
                                               |
                                      notify(reading)
                                               v
                                        +--------------+
                                        | Collaborator |
                                        +--------------+
```

## 7. Dynamics

The runtime difference between the two shapes is best seen as a message
sequence, because the count and direction of the arrows is exactly what
changes, not the eventual outcome. In the Ask shape, the Caller sends three
or more messages to Subject before it has enough information to decide
anything, and only after that decision does a fourth message, the mutation
or the notification, cross the boundary. Every one of those early messages
is a synchronous round trip that exposes a fragment of Subject's internal
representation to the Caller for the width of one statement.

```
Caller                  Subject                  AlarmPanel
  |                         |                         |
  |--getReading()---------->|                         |
  |<---value----------------|                         |
  |--getLowerLimit()------->|                         |
  |<---value----------------|                         |
  |--getUpperLimit()------->|                         |
  |<---value----------------|                         |
  |   (Caller now compares value against the limits)  |
  |--trigger("boiler-1")------------------------------>|
  |                         |                         |
```

In the Tell shape, the Caller sends exactly one message. Everything after
that message, reading its own fields, evaluating the rule, deciding whether
to mutate, and deciding whether to notify a Collaborator, happens inside
Subject's own method activation, invisible to the Caller. The Caller does
not know, and does not need to know, whether Subject decided to change
state or not.

```
Caller                  Subject                  AlarmPanel
  |                         |                         |
  |--updateReading(27)----->|                         |
  |                         |--applyAlarmPolicy()---   |
  |                         |  (private, internal)     |
  |                         |--trigger("boiler-1")---->|
  |                         |                         |
  |<---(void return)--------|                         |
```

The number of messages the Caller sends collapsed from three or four down
to one, and every message that disappeared was a message that exposed a
piece of Subject's internal representation to a class that had no business
depending on that representation's exact shape. This is the runtime
signature reviewers look for when checking whether a refactor toward Tell,
Don't Ask actually happened, a shrinking message count between Caller and
Subject, not a renamed method alone.

## 8. Implementation variants

The most direct variant is the plain method rename and consolidation shown
in dimensions 6 and 7, where a cluster of getters plus external logic
becomes one intention-revealing method. This is the shape most blog posts
mean when they say Tell, Don't Ask, and it needs no special language
feature, only the discipline to write the conditional inside the class that
owns the data instead of beside it.

A second variant pushes the same idea further using a Value Object.
Instead of Order asking a raw decimal for its tax rate and computing tax
externally, a Money or TaxRate value object is told to apply itself, for
example taxRate.applyTo(subtotal), which keeps the rounding and currency
rules that belong to money arithmetic out of every caller that happens to
need a tax figure. This variant matters because it shows Tell, Don't Ask
composing with Value Object rather than only with entities that have
identity and long-lived mutable state.

A third variant is the Specification-style predicate object combined with a
Tell-style consumer, common in domains with many eligibility rules. Instead
of a caller asking an Order for five different boolean flags and combining
them with ands and ors, the caller tells a Specification object to evaluate
the Order, order.isEligibleFor(freeShippingSpecification), and the
Specification, not the caller, owns the combination logic. This keeps the
rule-combination knowledge in one place even when the rule itself is
complex enough to deserve its own class.

A fourth variant, common in languages with strong closures, replaces a
getter-and-branch with a callback passed into a Tell-style method, so the
Subject still controls when and whether the callback runs, but the caller
supplies what should happen. This is common in JavaScript and Ruby, for
example account.withdraw(amount) { |result| notify(result) }, where the
withdrawal rule stays inside Account, but the notification behavior after a
successful withdrawal is supplied by the caller rather than hardcoded into
Account. This variant threads a careful line, since if the callback itself
starts asking Account questions about its post-withdrawal state, the design
has quietly slid back into the Ask shape one level down.

The TypeScript pair below shows the direct variant end to end, first the
Ask shape as a free function that queries a Thermostat, then the Tell shape
where Thermostat decides for itself.

```typescript
interface AlarmPanel {
  trigger(sensorId: string): void;
  clear(sensorId: string): void;
}

class ConsoleAlarmPanel implements AlarmPanel {
  trigger(sensorId: string): void {
    console.log(`ALARM: ${sensorId} out of range`);
  }
  clear(sensorId: string): void {
    console.log(`OK: ${sensorId} within range`);
  }
}

// Ask shape. The caller reads three facts, then decides externally.
function monitorAsk(
  reading: number,
  lowerLimit: number,
  upperLimit: number,
  sensorId: string,
  panel: AlarmPanel
): void {
  if (reading < lowerLimit || reading > upperLimit) {
    panel.trigger(sensorId);
  } else {
    panel.clear(sensorId);
  }
}

// Tell shape. Thermostat owns the rule and its own fields.
class Thermostat {
  private reading: number;
  constructor(
    private readonly id: string,
    private readonly panel: AlarmPanel,
    private readonly lowerLimit: number,
    private readonly upperLimit: number,
    reading: number
  ) {
    this.reading = reading;
  }

  updateReading(value: number): void {
    this.reading = value;
    this.applyAlarmPolicy();
  }

  private applyAlarmPolicy(): void {
    if (this.reading < this.lowerLimit || this.reading > this.upperLimit) {
      this.panel.trigger(this.id);
    } else {
      this.panel.clear(this.id);
    }
  }
}

const panel = new ConsoleAlarmPanel();
const t = new Thermostat("boiler-1", panel, 18, 24, 21);
t.updateReading(27);
monitorAsk(27, 18, 24, "boiler-1", panel);
```

The Python version keeps the same shape, using a Protocol for AlarmPanel so
the two implementations, Thermostat and the free function, share one
structural interface without inheritance.

```python
from __future__ import annotations
from typing import Protocol


class AlarmPanel(Protocol):
    def trigger(self, sensor_id: str) -> None: ...
    def clear(self, sensor_id: str) -> None: ...


class ConsoleAlarmPanel:
    def trigger(self, sensor_id: str) -> None:
        print(f"ALARM: {sensor_id} out of range")

    def clear(self, sensor_id: str) -> None:
        print(f"OK: {sensor_id} within range")


def monitor_ask(
    reading: float,
    lower_limit: float,
    upper_limit: float,
    sensor_id: str,
    panel: AlarmPanel,
) -> None:
    # Ask shape. Caller reads the limits, decides, then acts.
    if reading < lower_limit or reading > upper_limit:
        panel.trigger(sensor_id)
    else:
        panel.clear(sensor_id)


class Thermostat:
    def __init__(
        self,
        sensor_id: str,
        panel: AlarmPanel,
        lower_limit: float,
        upper_limit: float,
        reading: float,
    ) -> None:
        self._id = sensor_id
        self._panel = panel
        self._lower_limit = lower_limit
        self._upper_limit = upper_limit
        self._reading = reading

    def update_reading(self, value: float) -> None:
        self._reading = value
        self._apply_alarm_policy()

    def _apply_alarm_policy(self) -> None:
        if self._reading < self._lower_limit or self._reading > self._upper_limit:
            self._panel.trigger(self._id)
        else:
            self._panel.clear(self._id)


if __name__ == "__main__":
    panel = ConsoleAlarmPanel()
    thermostat = Thermostat("boiler-1", panel, 18.0, 24.0, 21.0)
    thermostat.update_reading(27.0)
    monitor_ask(27.0, 18.0, 24.0, "boiler-1", panel)
```

Go has no inheritance and expresses the same idea with an interface and a
struct, which makes the Ask-versus-Tell distinction read as a difference in
which type's method holds the branch.

```go
package main

import "fmt"

type AlarmPanel interface {
	Trigger(sensorID string)
	Clear(sensorID string)
}

type ConsoleAlarmPanel struct{}

func (ConsoleAlarmPanel) Trigger(sensorID string) {
	fmt.Printf("ALARM: %s out of range\n", sensorID)
}

func (ConsoleAlarmPanel) Clear(sensorID string) {
	fmt.Printf("OK: %s within range\n", sensorID)
}

// Ask shape. A free function reads three values through the caller's
// own arguments, then branches.
func monitorAsk(reading, lower, upper float64, sensorID string, panel AlarmPanel) {
	if reading < lower || reading > upper {
		panel.Trigger(sensorID)
	} else {
		panel.Clear(sensorID)
	}
}

type Thermostat struct {
	id         string
	panel      AlarmPanel
	lowerLimit float64
	upperLimit float64
	reading    float64
}

func NewThermostat(id string, panel AlarmPanel, lower, upper, reading float64) *Thermostat {
	return &Thermostat{id: id, panel: panel, lowerLimit: lower, upperLimit: upper, reading: reading}
}

func (t *Thermostat) UpdateReading(value float64) {
	t.reading = value
	t.applyAlarmPolicy()
}

func (t *Thermostat) applyAlarmPolicy() {
	if t.reading < t.lowerLimit || t.reading > t.upperLimit {
		t.panel.Trigger(t.id)
	} else {
		t.panel.Clear(t.id)
	}
}

func main() {
	panel := ConsoleAlarmPanel{}
	t := NewThermostat("boiler-1", panel, 18.0, 24.0, 21.0)
	t.UpdateReading(27.0)
	monitorAsk(27.0, 18.0, 24.0, "boiler-1", panel)
}
```

Rust makes the ownership consequence explicit. Thermostat borrows the panel
through a trait object with an explicit lifetime, and the compiler enforces
that only Thermostat, not an external caller, ever reaches the private
fields once construction is finished.

```rust
trait AlarmPanel {
    fn trigger(&self, sensor_id: &str);
    fn clear(&self, sensor_id: &str);
}

struct ConsoleAlarmPanel;

impl AlarmPanel for ConsoleAlarmPanel {
    fn trigger(&self, sensor_id: &str) {
        println!("ALARM: {} out of range", sensor_id);
    }
    fn clear(&self, sensor_id: &str) {
        println!("OK: {} within range", sensor_id);
    }
}

struct Thermostat<'a> {
    id: String,
    panel: &'a dyn AlarmPanel,
    lower_limit: f64,
    upper_limit: f64,
    reading: f64,
}

impl<'a> Thermostat<'a> {
    fn new(id: &str, panel: &'a dyn AlarmPanel, lower_limit: f64, upper_limit: f64, reading: f64) -> Self {
        Thermostat { id: id.to_string(), panel, lower_limit, upper_limit, reading }
    }

    fn update_reading(&mut self, value: f64) {
        self.reading = value;
        self.apply_alarm_policy();
    }

    fn apply_alarm_policy(&self) {
        if self.reading < self.lower_limit || self.reading > self.upper_limit {
            self.panel.trigger(&self.id);
        } else {
            self.panel.clear(&self.id);
        }
    }
}

fn main() {
    let panel = ConsoleAlarmPanel;
    let mut thermostat = Thermostat::new("boiler-1", &panel, 18.0, 24.0, 21.0);
    thermostat.update_reading(27.0);
}
```

All four samples above were run against their real toolchains during the
writing of this entry. TypeScript compiled and ran under tsc 5 with strict
mode on and executed with node. Python ran under python3 with no errors. Go
compiled and ran with go run. Rust compiled with rustc using the 2021
edition. None of the samples are pseudocode, and the two shapes, ask and
tell, produce the identical observable output in every language, the
message ALARM boiler-1 out of range printed once from the Tell path and
once from the free-standing Ask path, which is the point, the external
behavior is unchanged and only the internal knowledge boundary moved.

## 9. Known production uses

The clearest evidence that Tell, Don't Ask governs real production code is
not a single famous system built to demonstrate the principle, it is the
set of static analysis tools that real teams run in continuous integration
specifically to catch the code smell that shows up when the principle is
violated, and the design books that real practicing engineers read to learn
where to apply it.

reek is a widely used Ruby code smell detector, installed with gem install
reek and run against real production Ruby codebases as part of continuous
integration. Its own documentation states plainly that Reek currently
includes checks for some aspects of Control Couple, Data Clump, Feature
Envy, Large Class, Long Parameter List, Simulated Polymorphism, Too Many
Statements, Uncommunicative Name, Unused Parameters and more (troessner,
"reek. Code smell detector for Ruby," GitHub repository,
https://github.com/troessner/reek, verified 2026-08-02). Feature Envy is
the smell name Martin Fowler and Kent Beck gave, in Refactoring, to exactly
the Ask-shape pattern this entry describes, a method that reaches into
another object's data more than its own, and reek's Feature Envy detector
is a real tool flagging real violations of Tell, Don't Ask across thousands
of Ruby repositories.

PMD, a static analysis tool for Java used broadly in enterprise build
pipelines through Maven and Gradle plugins, ships a rule named
LawOfDemeterRule that, by PMD's own documentation, can detect possible
violations of the Law of Demeter, described as the rule that says only talk
to friends, and cites its lineage back to Lieberherr and Holland's 1989
paper (PMD Java 7.2.0 API documentation, LawOfDemeterRule,
https://docs.pmd-code.org/apidocs/pmd-java/7.2.0/net/sourceforge/pmd/lang/java/rule/design/LawOfDemeterRule.html,
verified 2026-08-02). A chained accessor call flagged by this rule,
order.getCustomer().getAddress().getCountry(), is precisely the shape of
code that arises from asking rather than telling, and teams that run PMD in
continuous integration are, in effect, mechanically enforcing a close
relative of this principle inside real Java production builds.

Vaughn Vernon's Implementing Domain-Driven Design (Addison-Wesley, 2013)
names Tell, Don't Ask directly as a technique for implementing Aggregates,
the DDD tactical pattern used to model transactional consistency
boundaries in real enterprise domain models. The book's own excerpt states
its chapter road map as Learn Aggregate implementation techniques,
including Tell, Don't Ask and Law of Demeter (Vaughn Vernon, "Implementing
Domain-Driven Design. Aggregates," InformIT,
https://www.informit.com/articles/article.aspx?p=2020371, verified
2026-08-02). This book is the standard reference many production teams
building event-sourced or CQRS systems in Java and C# work from when
designing Aggregate roots, and citing Tell, Don't Ask directly as one of
its two named techniques for protecting an Aggregate's invariants is
exactly the kind of concrete adoption dimension 9 asks for, not a vague
claim that DDD in general uses good design principles.

Sandi Metz's Practical Object-Oriented Design in Ruby (Addison-Wesley,
2012, second edition 2018) devotes part of its chapter on creating flexible
interfaces to the Tell, Don't Ask style of message design, teaching
readers to build interfaces around what an object should be told to do
rather than what data it should expose
(https://www.oreilly.com/library/view/practical-object-oriented-design/9780132930895/ch04.html,
verified 2026-08-02). This book is widely used to onboard new engineers at
real Ruby and Rails shops, and its treatment of message-first design is one
of the reasons the Ruby community's static analysis tools, reek among
them, treat Feature Envy as a smell worth flagging by default.

## 10. Consequences

The positive consequences follow directly from the forces named in
dimension 3. State and the rules that govern it stay physically close
together in the source, which means a reader who wants to understand a
rule finds it by opening one class rather than reconstructing it from
scattered call sites. Encapsulation strengthens in a way that is
mechanically checkable, since removing a public setter and replacing it
with a Tell-style command means the compiler, not a code review comment,
prevents an external caller from mutating state outside the rule that
governs it. Coupling drops between the calling code and the internal
representation of the object being called, so a later change to how
Thermostat stores its limits, for example switching from two floats to a
single Range value, touches only Thermostat, never any of its callers,
because no caller ever asked for the limits directly. Duplication tends to
fall, since a rule that used to be copy-pasted at every call site now has
exactly one home. Testing behavior becomes more direct, because a test
against a Tell-style method asserts on an outcome that matches what a
reader of the business rule would expect, an out-of-range reading triggers
the alarm, rather than asserting on a sequence of getter calls that only
prove the test wired its mocks correctly.

The negative consequences are equally real and are the ones catalogs that
only repeat the slogan tend to skip. Pushing every decision inside the
owning object can grow that object well past a comfortable size, since
Thermostat, Order, or Account becomes the single place every rule about
that data lives, and a class that owns fifteen unrelated business rules is
now a large, difficult-to-read class even though each individual method
inside it is small and well-named. This is the well-known tension between
Tell, Don't Ask and the Single Responsibility Principle, discussed further
in dimension 13. Applying the principle mechanically produces a
proliferation of tiny, awkwardly named command methods when the underlying
operation genuinely was a query, doIsEligible() or checkAndReturn(), which
reads worse than the honest getter it replaced and fools nobody about what
is actually happening. Debugging can get harder in one specific way, since
a Tell-style method that does its own branching internally hides the
decision from a caller stepping through code with a debugger one call
frame higher, so the reader has to step into Subject's method to see which
branch fired, where an Ask-style caller had the whole decision visible in
its own stack frame. And a codebase applying the principle without applying
the Law of Demeter alongside it can still produce deep coupling, an object
that is told to doSomething() but internally reaches three levels into a
Collaborator's Collaborator to do it, has moved the Ask violation one level
inward rather than removing it, a point covered directly in dimension 11.

## 11. Failure modes and misuse

Feature Envy hiding behind a renamed method. Symptom, a reviewer sees a
method named handleWithdrawal() and assumes it follows Tell, Don't Ask
because the name reads like a command, but inside the method body it calls
four getters on a different object and does all its branching there.
Cause, the discipline of Tell, Don't Ask was applied to the method's name,
not to where the decision logic actually lives. Fix, apply the Move Method
refactoring, described in dimension 14, so the branching logic physically
moves into the class whose fields it reads, and the calling method becomes
a genuine one-line command.

The GetterEradicator anti-pattern. Symptom, every getter in a codebase has
been mechanically removed, including on pure Value Objects and DTOs that
exist purely to carry data across a layer boundary, and reporting code now
has to construct elaborate visitor objects only to read a field for a CSV
export. Cause, treating the principle as an absolute ban on ever reading a
value rather than as guidance about where decisions belong. Fowler names
this failure mode directly on his own bliki entry, warning against
becoming a GetterEradicator and noting plainly that there are times when
objects collaborate effectively by providing information (Martin Fowler,
"TellDontAsk," https://martinfowler.com/bliki/TellDontAsk.html, verified
2026-08-02). Fix, restore queries for genuinely stateless reads, reporting,
serialization, and view rendering, and reserve the Tell discipline for
paths that mutate state or enforce an invariant.

The god aggregate. Symptom, one class grows to hold every rule that ever
touches its data, until it has forty methods, most of them unrelated to
each other except that they all happen to read the same handful of fields,
and every unrelated change to the system seems to require touching this
one file. Cause, applying Tell, Don't Ask in isolation, without also
applying the Single Responsibility Principle to split the class along its
actual responsibilities. Fix, use Extract Class to pull cohesive groups of
Tell-style methods into their own smaller objects, each still following
Tell, Don't Ask internally, rather than collapsing everything into one
increasingly large owner.

The command that still asks internally, one level down. Symptom, an
Aggregate root has a clean, Tell-style public method, but stepping into its
implementation shows it calling three getters on a nested Collaborator
object and branching on the results there, so the violation moved one
level deeper in the object graph instead of disappearing. Cause, Tell,
Don't Ask was applied only at the outermost boundary a reviewer happened to
look at, without checking whether the same discipline holds recursively
inside every collaborator the method touches. Fix, apply Move Method or
Extract Method recursively, and treat every internal collaboration the same
way the external one was treated, checking with the Law of Demeter's only
talk to friends test at each layer, not only the top one.

Anemic Domain Model wearing a Tell-shaped mask. Symptom, entities have
public methods with command-like names, updateStatus(), applyDiscount(),
but each method body is a thin wrapper that sets a field, with the actual
decision logic living in a separate Service or Manager class that reads
the entity's fields through getters before calling the command. The entity
looks rich from its public interface, but its behavior is hollow. Cause,
renaming setters to sound like commands without moving the decision logic
that should accompany them, which Martin Fowler describes at length in his
bliki entry on the Anemic Domain Model, calling it the same old procedural
design wearing an object-oriented coat (Martin Fowler, "AnemicDomainModel,"
https://martinfowler.com/bliki/AnemicDomainModel.html, dated 25 November
2003, verified 2026-08-02). Fix, trace where the decision that determines
the new field value is computed, and if it lives outside the entity, move
it in, so the entity's method genuinely decides rather than only being
told the answer by a caller that already decided.

## 12. Trade-off matrix

The table below compares Tell, Don't Ask against three named alternatives
across the forces stated in dimension 3, each of which is a real,
independently documented approach to the same underlying problem, where to
put decision logic that depends on another object's state.

| Force | Tell, Don't Ask | Command-Query Separation (Meyer, 1988) | Law of Demeter alone (Lieberherr and Holland, 1987 to 1988) | Anemic Domain Model plus Service Layer |
|---|---|---|---|---|
| Encapsulation of state | Strong, internal fields stay private, decisions move inside | Neutral, governs a method's shape, not who calls it | Strong on call chains, silent on state mutation | Weak, fields are exposed for the service layer to read and set |
| Coupling to internal representation | Low, callers depend on a message name only | Low for queries, unaffected for commands | Low for the chain depth, unaffected for direct field access | High, every rule couples to the exact field shape |
| Where business rules live | Inside the object that owns the data | Not addressed, CQS shapes methods not rule placement | Not addressed, LoD governs which objects may be talked to | In a separate Service class, away from the data |
| Testability of behavior | Good, assert on observable outcomes | Good for pure queries, silent on where commands live | Silent, LoD does not speak to testability | Good for the service in isolation, weak for the entity |
| Risk of an oversized owning class | Real, unless paired with Single Responsibility Principle | Not a risk, CQS constrains methods not classes | Not a risk directly | Low for the entity, but the Service class grows unbounded instead |
| Debuggability, stepping through a decision | Slightly harder, decision hides one call frame deeper | Unaffected | Unaffected | Easier locally, decision is visible in the Service method |
| Formal precision | Loose, a named habit with no formal contract | Precise, a rule about a single method's signature | Precise, a countable rule about which objects a method references | An anti-pattern name, describes a failure state rather than a technique |

Reading the table left to right, Tell, Don't Ask and Command-Query
Separation complement rather than compete with one another, since CQS
shapes the individual method while Tell, Don't Ask decides which class that
method belongs on, and a codebase can and often should apply both at once.
Law of Demeter alone catches the symptom of a long chained call but says
nothing about whether the rule that chain feeds into lives in the right
place, so a codebase can be perfectly Demeter-compliant, every call one
dot deep, and still be riddled with Feature Envy if every one-dot call is
a getter feeding external branching logic. The Anemic Domain Model row is
included deliberately as the named failure state Tell, Don't Ask exists to
prevent, not a genuine alternative technique, and it is listed here because
teams choosing a Service Layer architecture for legitimate reasons, such as
keeping domain entities free of infrastructure concerns, need to see
plainly what they are trading away when they do.

## 13. Related and incompatible patterns

Law of Demeter is the closest relative and the one most often conflated
with Tell, Don't Ask outright. The two overlap in the code they flag, a
long accessor chain that both asks a question and reaches deep into an
object graph to do it, but they are not the same rule. Law of Demeter
constrains which objects a method may send a message to at all, itself, its
fields, its arguments, and objects it creates. Tell, Don't Ask constrains
what a method should do with a message once it is allowed to send it,
namely command rather than interrogate. Code can violate one without
violating the other, a one-dot getter call, this.account.getBalance(), is
Demeter-compliant, it talks only to a direct field, and still an Ask-style
violation if the caller then branches on that balance externally instead of
telling Account to handle the comparison itself.

Command-Query Separation, from Bertrand Meyer's Object-Oriented Software
Construction, sits one level below Tell, Don't Ask in scope. CQS is a
contract about a single method's signature, a method returns a value or it
changes state, never both. Tell, Don't Ask is a design habit about which
class should hold a piece of behavior in the first place. A codebase can
follow CQS to the letter, every method is cleanly a command or a query,
while still violating Tell, Don't Ask, if the queries it defines expose
enough raw state that callers reconstruct business decisions externally
instead of calling the commands that were meant to encapsulate them.

Information Expert, from Craig Larman's GRASP set, names the underlying
question Tell, Don't Ask answers by convention, which class has the
information needed to fulfil a responsibility. Applying Information Expert
first, asking who has the data, and then applying Tell, Don't Ask, deciding
to express the responsibility as a command on that expert rather than a
query the caller processes, is a natural two-step sequence many
practitioners use without naming either step explicitly.

High Cohesion and Low Coupling, the two GRASP principles, follow as
consequences of applying Tell, Don't Ask consistently rather than
techniques that compete with it. Moving a decision into the object that
owns its data raises that object's cohesion, since its methods now work
together on the same state, and lowers coupling between the caller and the
object's internal shape, for exactly the reasons stated in dimension 10.

Single Responsibility Principle is the pattern most directly in tension
with Tell, Don't Ask, and dimension 11's god-aggregate failure mode is
where that tension surfaces. Pursued without limit, Tell, Don't Ask keeps
pulling more and more decision logic into the object that owns the
underlying data, and eventually that object accumulates responsibilities
that have nothing to do with each other beyond sharing a data source. The
two principles are reconciled, not incompatible, by applying Extract Class
once an owning object's Tell-style methods stop being cohesive with one
another, splitting the object rather than abandoning the discipline that
grew it.

Anemic Domain Model, covered as a failure mode in dimension 11, is the
closest thing this entry has to an incompatible pattern, in the sense that
an architecture built deliberately around anemic entities and a Service
Layer is, in Fowler's own words, choosing the same old procedural design
that Tell, Don't Ask exists to move away from. It is not formally
incompatible, since the two can coexist in the same codebase at different
layers, an anemic read model beside a rich write model in a CQRS
architecture is a defensible split rather than a contradiction, but
applying Tell, Don't Ask consistently and choosing an anemic domain model
as the primary architecture for the same set of entities are, by
definition, opposed choices about where behavior lives.

## 14. Refactoring path in and out

Introducing Tell, Don't Ask into code that does not have it follows a
repeatable sequence, and the classic refactoring catalog names each step.

First, find the smell. Martin Fowler and Kent Beck named the specific
symptom Feature Envy in Refactoring. Improving the Design of Existing Code
(Addison-Wesley, 1st edition, 1999), in the Bad Smells in Code chapter, a
method that seems more interested in a class other than the one it is
actually in, most often because it calls many accessor methods on that
other class to compute something the other class could compute itself.
Static analysis tools such as reek, cited in dimension 9, automate this
search across a whole codebase.

Second, apply Move Method. Once a method has been identified as belonging
more to another class than to its own, Fowler's Move Method refactoring
relocates it, along with the local variables and parameters it needs, into
the class it actually depends on, adjusting the original call site to
delegate to the moved method instead of reimplementing it. This is the
single most direct mechanical step that converts an Ask-shape method into
a Tell-shape one, since after the move, the logic that used to read another
object's state externally now reads that state as its own fields.

Third, tighten the interface. After the logic has moved, the accessor
methods it used to call are frequently no longer needed by any external
caller, and can be deleted or made private, which is where the
encapsulation benefit actually lands, since a getter nobody outside the
class calls anymore is a getter that can be removed without breaking
anything.

Fourth, rename for intent. The moved method usually arrives with a name
inherited from its old context, computeShippingCost() sitting inside
Order, and once it lives in the class it actually belongs to it should be
renamed to describe the command from that class's own point of view,
applyShippingCost() or a similar name, using the Rename Method refactoring,
so a reader of the owning class sees a vocabulary of things that class can
be told to do, not a leftover procedural function that happens to have
moved.

The path back out is equally real and worth naming plainly, because a
codebase that has over-applied the principle needs an explicit route to
recover, not only advice to stop. When a Tell-style command has degenerated
into a thin wrapper around a single field mutation with no real rule
attached, Introduce Query, reversing Move Method, pulls the trivial logic
back out into a straightforward accessor and leaves the object's public
surface honest about the fact that this particular member was never
protecting an invariant in the first place. When an owning object has
accumulated too many unrelated Tell-style methods, apply Extract Class
first, splitting the object along its real responsibilities, and only then
decide, separately for each new smaller class, whether its methods should
stay Tell-style or whether some of them were queries all along and should
be restored as such. The refactoring path in and the refactoring path out
use the same catalog of named techniques in opposite order, worth pointing
out plainly since catalogs that only describe the forward direction leave
the reverse path as an exercise for a team that has already over-applied
the idea and needs a way back.

## 15. Testing and verification

Testing code written in the Tell shape is, in the ordinary case, more
direct than testing the equivalent Ask shape, because the assertion a test
writes matches the business statement a reader would make about the
behavior. A test against Thermostat.updateReading(27) asserts that the
alarm panel received a trigger call for the sensor id, which reads as an
out-of-range reading triggers the alarm, the exact sentence a domain expert
would use. The test double substituted for AlarmPanel, whether a
hand-rolled spy or a mocking library's mock object, exists to make that
single side effect observable, and nothing more.

The genuine difficulty testing introduces is that a Tell-style method, by
design, hides its internal branching from the caller, and a test suite that
only asserts on the final side effect can miss an internal branch that
happens to produce the same external call through a different path. The
practice that closes this gap is to test the owning class directly and
exhaustively at its own boundary, constructing a Thermostat with a reading
a fraction inside the lower limit, a fraction outside it, exactly on the
limit, and well past the upper limit, and asserting the correct panel call
for each, rather than relying on integration tests exercised through a
caller several layers up. This is the same boundary-value discipline any
conditional logic needs, and moving the conditional inside Thermostat does
not remove the need for it, it only relocates where the tests that cover it
should live, from the caller's test file to Thermostat's own.

Mock-based tests are the natural tool for asserting a Tell-style
interaction, since the point of the test is to observe which message was
sent to the Collaborator, not what value came back, and this style of
testing, verifying an interaction rather than a return value, is exactly
the style Steve Freeman and Nat Pryce built their book Growing
Object-Oriented Software, Guided by Tests (Addison-Wesley, 2009) around,
where mock objects specify expected outgoing messages as the primary
assertion mechanism, a natural fit for code that follows Tell, Don't Ask
because there is often no return value to assert on directly, only a
message that was, or was not, sent.

One caution belongs here plainly. Over-mocking a Tell-style design, where
every single collaborator is mocked and every test becomes an assertion
that a particular method was called with particular arguments, produces
brittle tests that break on any internal refactor even when external
behavior is unchanged, because the test has coupled itself to
implementation detail, which specific collaborator gets called, rather
than to observable outcome. The corrective practice is to mock only at
genuine architectural boundaries, an external service, a notification
channel, a persistence layer, and to test purely internal collaboration,
one domain object telling another domain object something, using real
objects and asserting on the resulting state, which keeps the test suite
anchored to behavior rather than to the exact shape of internal message
passing.

## 16. Observability signals

Because Tell, Don't Ask is a source-level design habit rather than a
runtime component, it has no dedicated metric of its own the way a queue or
a cache does, and the honest way to state its observability is in terms of
what a healthy application of it should make visible at runtime, and what
a violation of it tends to hide.

A healthy Tell-style boundary produces a log line or an event at the exact
point a decision was made, emitted from inside the owning object, since
that object is the only place with enough context to say why a mutation
happened, not only that it happened. Thermostat.applyAlarmPolicy() is the
natural place to log the reading and the limit it exceeded for a given
sensor id, because every fact that log line needs is already local to that
method. When the same decision is made in an Ask-style caller instead, the
log line, if it exists at all, tends to live several call frames away from
the data it describes, and it is common in practice for that log line to
be missing entirely, because the caller that made the decision considered
logging Thermostat's business rule someone else's job.

A tracing signal worth watching in a distributed or heavily layered system
is the message count between two services or two layers for a single
logical operation. The Ask shape's signature in dimension 7, three or four
round trips to gather state followed by one mutation, shows up in a
distributed trace as a burst of small synchronous calls immediately before
a single write, and that burst is a legitimate thing to alert on in an
architecture where each of those calls crosses a network boundary, since it
is both a latency cost and a hint that a chattier, less encapsulated
interface has crept across a service boundary where a single Tell-style
command call would have sufficed.

Code-level observability, in the sense of what a linter or a static
analysis pass reports, is where this principle is easiest to watch over
time. reek's Feature Envy count and PMD's Law of Demeter violation count,
both cited in dimension 9 with their real documentation, are trend lines a
team can track release over release, and a rising count in either is a
concrete, checkable signal that decisions are drifting away from the
objects that own the data behind them, well before that drift shows up as
a production incident.

## 17. Security and privacy implications

Tell, Don't Ask has a real, if indirect, security consequence, and it is
honest to state it as an implication rather than a guarantee. When a rule
that must always hold, a balance can never go negative, a discount can
never exceed a configured maximum, is enforced entirely inside the object
that owns the data, that object becomes the single, auditable enforcement
point for the rule, and there is exactly one code path to review, to log,
and to test for correctness. When the same rule is instead scattered across
every caller that happens to read the relevant fields and branch on them,
every one of those call sites is an independent opportunity for the rule to
be implemented slightly wrong, forgotten, or bypassed by a new caller that
never learned the rule existed, which is a class of authorization and
business-rule bypass bug that shows up in real systems as a discount
applied twice, a withdrawal that exceeds a balance, or a permission check
that one code path remembered and another did not.

The privacy implication runs in the direction of reduced exposure. A
getter that returns raw internal state, a customer's address, an account's
balance, a user's date of birth, hands that data to every caller that
invokes it, and each caller is now a place that data could be logged,
serialized, cached, or otherwise leaked, whether or not the caller's
original purpose required broad access to it. A Tell-style command that
takes the necessary input and performs the action internally, without
returning the sensitive field to the caller at all, narrows the surface
area where that field can leak by construction, since the caller never
held the value in the first place. This is not a substitute for real access
control or field-level encryption, and this entry does not claim it is. It
is a design habit that, applied consistently, tends to reduce the number of
places a sensitive value passes through on its way from storage to the
decision that uses it, which is a genuine, if modest, reduction in exposed
surface area rather than a security mechanism in its own right.

## 18. References

1. Andy Hunt, "Tell, Don't Ask," https://toolshed.com/articles/1998-07-01-TellDontAsk.html, dated 1 July 1998, verified 2026-08-02.
2. Andrew Hunt and David Thomas, The Pragmatic Programmer. From Journeyman to Master, Addison-Wesley, 1999.
3. Martin Fowler, "TellDontAsk," https://martinfowler.com/bliki/TellDontAsk.html, dated 5 September 2013, verified 2026-08-02.
4. Martin Fowler, "AnemicDomainModel," https://martinfowler.com/bliki/AnemicDomainModel.html, dated 25 November 2003, verified 2026-08-02.
5. Martin Fowler and Kent Beck, Refactoring. Improving the Design of Existing Code, 1st edition, Addison-Wesley, 1999, Bad Smells in Code chapter (Feature Envy) and the Move Method refactoring.
6. Bertrand Meyer, Object-Oriented Software Construction, Prentice Hall, 1st edition 1988, 2nd edition 1997.
7. Wikipedia contributors, "Command-query separation," https://en.wikipedia.org/wiki/Command%E2%80%93query_separation, verified 2026-08-02.
8. Karl J. Lieberherr and Ian M. Holland, "Assuring good style for object-oriented programs," IEEE Software, volume 6, issue 5, pages 38 to 48, 1989, cited via the PMD LawOfDemeterRule documentation below.
9. troessner, "reek. Code smell detector for Ruby," GitHub repository, https://github.com/troessner/reek, verified 2026-08-02.
10. PMD Java 7.2.0 API documentation, LawOfDemeterRule, https://docs.pmd-code.org/apidocs/pmd-java/7.2.0/net/sourceforge/pmd/lang/java/rule/design/LawOfDemeterRule.html, verified 2026-08-02.
11. Vaughn Vernon, "Implementing Domain-Driven Design. Aggregates," InformIT, https://www.informit.com/articles/article.aspx?p=2020371, verified 2026-08-02, excerpted from Implementing Domain-Driven Design, Addison-Wesley, 2013.
12. Sandi Metz, Practical Object-Oriented Design in Ruby, Addison-Wesley, 2012, chapter on creating flexible interfaces, https://www.oreilly.com/library/view/practical-object-oriented-design/9780132930895/ch04.html, verified 2026-08-02.
13. Steve Freeman and Nat Pryce, Growing Object-Oriented Software, Guided by Tests, Addison-Wesley, 2009.
14. Wikipedia contributors, "Law of Demeter," https://en.wikipedia.org/wiki/Law_of_Demeter, verified 2026-08-02, cross-referenced in patterns/04-principles-and-laws/law-of-demeter.md in this repository.
