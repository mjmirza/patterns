---
name: Postel's Law
slug: postel-law
family: 04-principles-and-laws
category: Principle
aliases: [Robustness Principle, "Be Conservative In What You Do, Be Liberal In What You Accept"]
first_described: "Jon Postel, RFC 761, January 1980"
maturity: contested
related: [adapter, protected-variations, open-closed-principle, template-method]
incompatible_with: [fail-fast]
verified: 2026-08-02
---

# Postel's Law

## 1. Name, aliases, and lineage

The common name is Postel's Law. Its formal name, and the one the Internet
Engineering Task Force itself uses in specification text, is the Robustness
Principle. Both names refer to the same sentence, stated in RFC 761,
"Transmission Control Protocol", January 1980, section 2.10. The text reads,
"TCP implementations should follow a general principle of robustness. be
conservative in what you do, be liberal in what you accept from others"
(https://datatracker.ietf.org/doc/html/rfc761, verified 2026-08-02, section
2.10). RFC 793, the September 1981 revision that superseded RFC 761 as the
standard TCP specification, restates the same sentence with one word changed,
from "should" to "will". It reads, "TCP implementations will follow a
general principle of robustness. be conservative in what you do, be liberal
in what you accept from others" (https://datatracker.ietf.org/doc/html/rfc793,
verified 2026-08-02, section 2.10). The shift from "should" to "will" is
small but not accidental. It moves the sentence from a recommendation to a
stated expectation of every conforming TCP implementation.

RFC 761 and RFC 793 both name Jon Postel of USC's Information Sciences
Institute as the document's author, which is the direct basis for calling the
sentence "Postel's Law" in later literature, though neither RFC uses that name
for itself. The RFCs simply call it "a general principle of robustness."
Some secondary sources trace an earlier appearance of the same idea to
Postel's parallel work on the Internet Protocol specification in the same
period. This entry does not assert that earlier date as fact, because it was
not independently confirmed against a primary IETF document during
verification for this entry. The earliest instance verified here is the RFC
761 text quoted above.

The principle was generalized beyond TCP nine years later by Robert Braden in
RFC 1122, "Requirements for Internet Hosts, Communication Layers", October
1989, section 1.2.2, titled "Robustness Principle." It reads, "Be liberal in
what you accept, and conservative in what you send"
(https://datatracker.ietf.org/doc/html/rfc1122, verified 2026-08-02, section
1.2.2). Note the reordering. RFC 761 and RFC 793 say "conservative in what
you do" first and "liberal in what you accept" second. RFC 1122 reverses the
two clauses and also narrows "what you do" to "what you send." Both
orderings circulate in later writing, and both are exact RFC text, not a
paraphrase drifting over time. RFC 1122 extends the principle past a
wire-format detail into a stance for reading the entire protocol suite. The
same section states that it is best to assume the network is filled with
malevolent entities that will send packets designed to have the worst
possible effect, so an implementation following this principle must
anticipate every conceivable error a hostile or merely broken peer could
produce, not only the common ones (same source, section 1.2.2).

Two further names are worth recording because they mark real disagreement
rather than mere restatement. Marshall Rose, in RFC 3117, "On the Design of
Application Protocols", November 2001, section 4.5, calls the same sentence
"Postel's robustness principle" while arguing it "often leads to deployment
problems" (https://datatracker.ietf.org/doc/html/rfc3117, verified
2026-08-02, section 4.5). Martin Thomson and David Schinazi, writing for the
IETF's Internet Architecture Board, published RFC 9413, `"Maintaining Robust Protocols"`, 2023, an Informational document that treats the principle as
something to be actively managed rather than followed by default
(https://www.rfc-editor.org/rfc/rfc9413, verified 2026-08-02). RFC 9413
evolved from an earlier Internet-Draft originally titled "The Harmful
Consequences of the Robustness Principle", authored by Martin Thomson
(https://datatracker.ietf.org/doc/draft-thomson-postel-was-wrong/, verified
2026-08-02), a title that gives away the draft's argument before the
abstract does. Both names, favorable and critical, are recorded in dimension
4 and dimension 10, because the disagreement between them is not a footnote
to this entry. It is most of the entry.

## 2. Problem and context

Two or more parties implement the same open, published specification
independently, without coordinating their release schedules, their source
code, or in most cases even knowing about each other's existence until their
software tries to talk over a wire. The specification itself is written in
natural language, and natural language is never perfectly precise. Some
detail is genuinely ambiguous, some corner case was never considered by the
authors, and some requirement will later prove to be a mistake that a future
revision of the specification has to correct.

This is the ordinary condition of an open network protocol, an email
standard, a markup language rendered by many independent browsers, or a
public HTTP API consumed by clients the API owner has never met. Nobody can
flip every implementation to a new version at the same instant. A mail
transfer agent cannot refuse to talk to the ten-year-old server still running
at some university, an HTTP client library cannot break every website that
sends a slightly non-conformant header, and a browser vendor cannot make
every website on the internet rewrite its markup before that browser ships.
The specification is shared, but conformance to it is scattered across an
unknown and unmanageable number of independent codebases evolving on their
own timelines.

Inside that context, an implementer who writes the strictest possible
receiver, one that rejects any message deviating from the letter of the
specification, will fail to interoperate with a large share of the real
population of peers, because that population contains implementations with
small bugs, implementations built against an earlier draft of the
specification, and implementations that made a defensible but different
reading of an ambiguous passage. An implementer who writes the loosest
possible sender, one that emits whatever is convenient regardless of the
specification's precise grammar, pushes the cost of that laxity onto every
receiver that must infer what was meant. Postel's Law is the advice that
resolves this asymmetrically. Hold your own output to the letter of the
specification, because you are the one party who can control it completely,
and hold your tolerance for other people's output loose, because you cannot
control them at all and rejecting them serves nobody.

The problem the principle answers, stated plainly, is this. How should one
side of an open, uncoordinated, multi-implementer protocol behave at the
boundary where its own bytes meet somebody else's, given that the
specification governing that boundary is imperfect and the population of
peers on the other side of it will never be perfectly conformant.

## 3. Forces

**Interoperability now against correctness later.** A liberal receiver talks
to more of the real population of peers today. Every peer accepted is one
fewer support ticket, one fewer broken connection, one fewer user blaming the
wrong side of the wire. That gain is immediate and visible. The cost of the
same leniency is deferred and largely invisible until the day a stricter
peer, or an attacker, exploits the very gap the leniency opened.

**Evolvability against specification precision.** A message format that
lets a receiver silently ignore fields it does not recognize can be extended
by adding new optional fields without breaking every deployed receiver at
once. This is the single strongest positive force behind the principle, and
it is the half of the idea that survives essentially unchallenged even in
the critical literature, discussed further in dimension 4 and dimension 8.
The price is that the specification's boundary between "conformant" and
"not conformant" becomes fuzzier the more receivers are told to look past
deviations.

**The flag day problem.** Marshall Rose names this directly. "Eventually,
the not-quite-correct implementations run into other implementations that
are less liberal than the initial set of implementations. The reader should
be able to figure out what happens next" (RFC 3117, section 4.5,
https://datatracker.ietf.org/doc/html/rfc3117, verified 2026-08-02). A
tolerant receiver hides a sender's bug from the sender's own author, who has
no reason to fix what appears to work. Every later implementer who tests
against that popular, buggy, widely deployed sender copies the same
tolerance to interoperate with it, and the bug becomes load-bearing across
the whole population of deployed peers. Years later, a genuinely new and
strictly conformant implementation arrives, has no reason to reproduce the
accumulated tolerances of its predecessors, and fails to talk to a large
share of a network that quietly stopped following its own written
specification long ago. Rose's insight is that this is not a rare accident.
It is close to the default outcome of applying the principle without limit.

**Security surface against tolerance.** RFC 9413 states the newer critical
argument in plain terms. Tolerating an unexpected input, in the document's
own words, "relies on an assumption that existing specifications and
implementations cannot change" (https://www.rfc-editor.org/rfc/rfc9413,
verified 2026-08-02). A grammar that accepts more strings than the strict
specification defines is, by construction, a larger attack surface than a
grammar that accepts only the strict strings, because every string the
grammar accepts is a string an adversary can also send. Every ambiguity a
liberal receiver resolves on the sender's behalf is a decision an attacker
can try to make differently from how a second receiver in the same request
path resolves it, which is the exact mechanism behind HTTP request
smuggling, worked through in dimension 11.

**Debuggability against apparent success.** This is the same force the Fail
Fast principle is built on, approached from the opposite side, and dimension
13 returns to the comparison directly. A liberal receiver that silently
repairs or ignores a malformed input reports success to its caller. The
sender that produced the malformed input never learns it made a mistake. The
defect stays latent, sometimes for years, until it surfaces somewhere
downstream with none of the original context attached.

**Coordination cost against precision.** The genuine, non-security
justification for the principle is that coordinating a synchronized upgrade
across every independent implementer of an open protocol is close to
impossible, and demanding strict conformance from day one is equivalent to
demanding that coordination happen anyway. The principle trades away
precision specifically to avoid paying that coordination cost, which is a
real and often decisive advantage in a genuinely open, federated system, and
an advantage that does not exist at all inside a single team's own service
boundary, which is exactly where dimension 4 draws the line.

## 4. Applicability and non-applicability

Reach for the robustness principle, in its bounded form described in
dimension 8, when the following hold.

- The boundary is a genuinely open, federated protocol with many
  independently released implementations you do not control and cannot
  force to upgrade on your schedule, the situation email, DNS, HTTP, and
  TCP itself were designed for.
- The message format includes, or is meant to include, fields a future
  version of the specification will add, and today's receivers should keep
  working when they encounter a message carrying a field from a version they
  have not yet been updated to understand.
- You are consuming input from a large, effectively unmanaged population of
  senders, such as arbitrary websites, arbitrary email servers, or arbitrary
  API clients you have never met, where rejecting a message on a minor,
  harmless deviation costs you real interoperability and the deviation
  carries no real risk.
- You are the author of the specification itself, or a widely used
  implementation of it, and you are deliberately building in a "must
  ignore unknown fields" extension mechanism as future-proofing, the way
  protocol buffers, TLS extensions, and HTTP header parameters all do.

Do NOT apply the robustness principle in these cases, and the reason in each
case is the more useful half of this dimension.

- **A security-relevant parsing boundary, especially one shared by more than
  one implementation in the same request path.** This is the situation RFC
  9413 and the HTTP request smuggling literature both target directly. When
  two different HTTP implementations liberally, but differently, resolve
  the same ambiguous framing header, the disagreement between their two
  interpretations is the vulnerability, not a side effect of it. Strict,
  identical rejection of the ambiguous case removes the vulnerability;
  tolerant, divergent acceptance of it creates one.
- **Fields whose meaning, not merely whose presence, is safety or money
  critical.** Being liberal about an unrecognized optional field is safe.
  Being liberal about the syntax of a required field, such as coercing a
  malformed currency amount, an ambiguous date, or a partially valid
  authorization token into "close enough", turns a parsing decision into a
  business or security decision made silently, far from any reviewer.
  Dimension 11 develops this failure mode with a concrete symptom.
- **A boundary you fully control on both sides and can deploy atomically.**
  The entire justification for the principle is the impossibility of
  coordinated deployment across independent parties. A service and its
  client owned by the same team, released from the same monorepo, deployed
  by the same pipeline, has none of that coordination cost, so trading
  correctness for tolerance buys nothing there and only imports the flag-day
  risk for free. Prefer strict validation and Fail Fast at that boundary,
  see dimension 13.
- **A protocol you intend to actively maintain and evolve, without a
  commitment to periodically retire accumulated tolerances.** RFC 9413's
  central recommendation is that active protocol maintenance, not passive
  tolerance, is what actually keeps a protocol healthy over time. Applying
  unlimited leniency without ever measuring or removing it is precisely the
  path to the flag-day failure in dimension 3.
- **Content-type or format guessing that overrides an explicit,
  authoritative declaration from the sender.** MIME sniffing, where a
  receiver decides to reinterpret content as a different type than the one
  the sender declared, is the misapplication worked through in dimension 11.
  The sender's declaration is not ambiguous data to be liberally
  interpreted. It is an explicit statement that should be honored or
  rejected, not second-guessed.
- **Canonicalization boundaries for cryptographic signatures or distributed
  consensus.** Two implementations of a consensus protocol, or two verifiers
  of the same signed message, must compute the identical canonical byte
  sequence from the identical logical message, or the whole point of the
  signature or the consensus round is defeated. A parser that liberally
  accepts several syntactic variants of the same logical value produces
  exactly the kind of parser differential that breaks this property, even
  when neither variant is individually malicious.

## 5. Structure

The robustness principle names five participants, roles rather than classes,
because it governs behavior at a network boundary rather than object
composition inside one process.

- **Sender (Producer).** The conservative half. Its obligation is to emit
  output that conforms exactly to the specification's strict grammar, in
  full, every time, regardless of which optional parts of a message happen
  to be present.
- **Receiver (Consumer).** The liberal half. Its obligation is to accept any
  input a conforming sender could produce, plus a defined, bounded set of
  deviations from strict conformance that experience or design has shown to
  be harmless.
- **Specification (Contract).** The shared but imperfect natural-language or
  formal-grammar document both parties are supposed to conform to. It is the
  reason the tension exists at all. A perfect, unambiguous, universally
  implemented specification would need no leniency on either side.
  Dimension 3's flag-day force is the mechanism by which the receiver's
  leniency quietly rewrites this document without anyone editing it.
- **Core field (Required data).** The part of a message the receiver's own
  correctness depends on. This is where leniency is dangerous, because
  coercing an ambiguous core field changes the meaning of the message rather
  than merely tolerating its shape.
- **Extension field (Unknown or optional data).** Data present in a message
  that the receiver's current implementation does not recognize, or that the
  specification explicitly marks as optional. This is where leniency is
  cheap and, per dimension 3, the single strongest positive force behind the
  principle. The well-designed version of the robustness principle applies
  leniency here and only here, which is the distinction dimension 8 develops
  as "bounded" leniency.

## 6. ASCII structure diagram

```
                       shared, imperfect Specification
                    (natural language, evolves over time)
                    /                                   \
                   /                                     \
   +-----------------------+                 +-----------------------+
   |   Sender (Producer)    |                 |  Receiver (Consumer)  |
   |------------------------|    encoded      |------------------------|
   | emits strictly         | -- message -->  | accepts strict AND    |
   | conforming output,     |    on the wire   | a bounded set of      |
   | full grammar, always   |                 | tolerated deviations   |
   +-----------------------+                 +-----------------------+
                                                        |
                                          splits the message into
                                                        |
                                     +------------------+------------------+
                                     |                                     |
                          +--------------------+              +----------------------+
                          |    Core field      |              |   Extension field     |
                          |--------------------|              |------------------------|
                          | validated strictly |              | unknown or optional,   |
                          | rejected if wrong,  |              | ignored (or preserved) |
                          | meaning must be     |              | without complaint,     |
                          | exact               |              | never rejects the      |
                          |                     |              | message                |
                          +--------------------+              +----------------------+

   Leniency belongs on the right branch only. Leniency applied to the
   left branch is the misapplication traced through dimension 11.
```

## 7. Dynamics

Two flows illustrate the principle. The intended, healthy one, and the
degraded one Rose describes in RFC 3117 and dimension 3.

The healthy flow. An ordinary message from a spec-conformant sender, plus a
message from a newer sender that adds one extension field an older receiver
does not yet understand.

```
Sender A (v1)         Wire            Receiver (any version)
    |                   |                       |
    |-- strict v1 msg ->|                       |
    |                   |-- strict v1 msg ----->|
    |                   |                       |-- validates core fields
    |                   |                       |-- no extension fields present
    |                   |                       |-- accepted, processed
    |                   |                       |

Sender B (v2, adds "traceId" extension field)     Receiver (still v1)
    |                                                    |
    |-- strict v2 msg (core fields + traceId) -------->  |
    |                                                    |-- validates core fields, OK
    |                                                    |-- "traceId" unrecognized
    |                                                    |-- extension field ignored,
    |                                                    |   not an error
    |                                                    |-- accepted, processed
```

The degraded flow. Rose's flag-day sequence, where the same tolerance that
made the healthy flow possible quietly absorbs a real defect instead of an
intentional extension.

```
Sender X (buggy)        Receiver 1 (lenient, v1)        Receiver 2 (new, strict, v2)
     |                          |                                  |
     |-- slightly malformed --> |                                  |
     |    core field            |-- tolerates the deviation,       |
     |                          |   silently repairs it,           |
     |                          |   reports success                |
     |                          |                                  |
     |   (Sender X's author never learns anything is wrong,        |
     |    because Receiver 1 never complained)                     |
     |                                                              |
     |-- same slightly malformed core field ---------------------->|
     |                                                              |-- rejects, strict
     |                                                              |   conformance
     |                                                              |
     |   (interoperability failure surfaces years after the bug     |
     |    was introduced, with no context connecting it back to    |
     |    Sender X's original mistake)
```

## 8. Implementation variants

**Unbounded classical leniency.** The receiver attempts a best-effort
interpretation of nearly any input, including malformed core fields, and
rarely rejects a message outright. Early web browsers rendering broken HTML,
and the historically permissive `sendmail` mail transfer agent, are the
usual examples cited in the secondary literature for this style. It buys the
most interoperability against the widest population of imperfect senders and
pays the largest share of the flag-day and security costs from dimensions 3
and 11, because the leniency is not confined to extension fields. It reaches
into core, meaning-bearing data.

**Bounded leniency with a must-ignore extension mechanism.** The receiver
validates core, required fields strictly and rejects a message that fails
that validation. Separately, and only for fields the specification marks as
extensible, the receiver is required to ignore anything it does not
recognize rather than rejecting the whole message. Protocol Buffers'
handling of unknown fields (dimension 9) and TLS's extension negotiation are
both this shape. This is the variant RFC 9413 treats as the acceptable,
sanctioned remainder of the principle once the unbounded form is set aside,
and it is the variant demonstrated in the Code examples section of this
entry.

**Deterministic error-recovery parsing.** Rather than leaving "be liberal"
to each implementer's individual judgment, the specification itself defines
exactly what a receiver must do with every specific class of malformed
input, so that every conforming implementation converges on the identical
behavior even when the input is wrong. The WHATWG HTML Standard's parsing
algorithm, discussed in dimension 9, is the clearest production example of
this variant. It keeps the tolerance for a sender's mistakes that the
original principle called for, while removing the ambiguity of leaving each
implementer to infer what "liberal" means in a given case, which is exactly
the ambiguity that produces divergent, security-relevant parser
differentials.

**Leniency scoped by explicit version or capability negotiation.** The
receiver is liberal only within a declared compatibility window, established
by a version field, an `Accept` header, or a similar negotiation step, rather
than applying tolerance blindly and permanently to every input regardless of
its stated version. HTTP content negotiation and versioned API media types
fit this shape. It lets an implementation retire an old tolerance
deliberately, at a version boundary, instead of never being able to remove it
without breaking an unknown population of callers.

**Leniency with telemetry and a retirement path.** The receiver accepts a
tolerated deviation exactly as in the bounded variant, but also records that
the deviation occurred, per deviation type, so the accumulated cost of the
tolerance is visible and can eventually be scheduled for removal rather than
becoming permanent by default. This is less a distinct parsing technique
than an operational discipline layered onto any of the variants above, and it
is the direct, practical answer to the RFC 3117 flag-day problem, developed
further in dimension 14 and dimension 16.

## 9. Known production uses

**The TCP/IP protocol suite itself.** The principle originates as an
operating rule for TCP in RFC 761 and RFC 793, and Robert Braden's RFC 1122
extends it into the general requirements for every Internet host's
communication layers. It remains, in its generalized form, the stated
governing philosophy for how Internet hosts are expected to handle malformed
or unexpected input across the whole TCP/IP stack, not only TCP itself
(https://datatracker.ietf.org/doc/html/rfc1122, verified 2026-08-02, section
1.2.2).

**SMTP receivers tolerating trailing whitespace.** RFC 5321, "Simple Mail
Transfer Protocol", October 2008, section 4.1.1, states plainly, "In the
interest of improved interoperability, SMTP receivers SHOULD tolerate
trailing white space before the terminating <CRLF>"
(https://datatracker.ietf.org/doc/html/rfc5321, verified 2026-08-02, section
4.1.1). This is a narrow, bounded, and precisely scoped instance of the
principle written directly into a current Internet Standard for one of the
internet's oldest and still-active protocols.

**Protocol Buffers preserving unknown fields.** The Protocol Buffers proto3
language guide states that "proto3 messages preserve unknown fields and
include them during parsing and in the serialized output, which matches
proto2 behavior" (https://protobuf.dev/programming-guides/proto3/, verified
2026-08-02, section "Unknowns"). A parser generated from an older `.proto`
schema does not fail when it receives a message serialized by a newer schema
that has added fields. It decodes the fields it recognizes and carries the
rest through untouched, which is the bounded, must-ignore variant from
dimension 8 in wide production use across every system built on Protocol
Buffers, including gRPC.

**The WHATWG HTML Standard's parsing algorithm.** The current HTML Standard
does not simply reject markup that does not conform to a formal grammar. It
defines a deterministic parsing algorithm, and section 13.2, "Parsing HTML
documents", specifies exact recovery behavior for classes of malformed input
so that certain points in the parsing algorithm are formally designated as
parse errors, each with a defined processing rule attached
(https://html.spec.whatwg.org/multipage/parsing.html, verified 2026-08-02,
section 13.2, subsection "Parse errors"). This is the deterministic
error-recovery variant from dimension 8. It descends directly from decades
of browsers being unilaterally, and inconsistently, liberal about broken
HTML, and the specification's own text records that the resulting
confusion, with validators claiming documents to have one representation
while widely deployed web browsers interoperably implemented a different
representation, is exactly the flag-day-style cost the principle can
accumulate when receivers are left to be liberal without a shared, published
definition of what "liberal" means (same source, section 13.2, introductory
text on the history of HTML parsing).

## 10. Consequences

Positive.

- Independent implementations of an open protocol can interoperate without
  a synchronized release schedule, which is the founding justification for
  the principle and remains true wherever the applicability conditions in
  dimension 4 hold.
- A message format can be extended with new optional fields without
  breaking existing receivers, giving a population of interoperating
  implementations forward and backward compatibility across versions that
  were never coordinated with each other.
- Receivers degrade gracefully at a network boundary instead of hard
  failing on a minor or cosmetic deviation, which lowers the support and
  operational burden of talking to a large, unmanaged population of peers.
- A sender's small, harmless mistake does not immediately become the
  receiving user's problem, buying implementers time to fix bugs on their
  own schedule rather than under the pressure of an outage.

Negative.

- Accumulated tolerances become load-bearing across a whole population of
  deployed peers, so removing a leniency later, even one that was only ever
  meant to be temporary, risks breaking every peer that came to depend on
  it, exactly the flag-day mechanism in dimension 3.
- A grammar broadened to accept more input than the strict specification
  defines is, by construction, a larger attack surface, and every ambiguity
  a liberal receiver resolves on the sender's behalf is a decision two
  different receivers in the same request path can resolve differently,
  which is the exact shape of the vulnerabilities in dimension 11.
- Tolerating a malformed input hides the defect from the party that could
  actually fix it, moving the cost of the bug downstream, later, and to a
  different, less informed party, the opposite of the debuggability
  dividend Fail Fast is built to protect, discussed in dimension 13.
- The written specification stops being an authoritative description of
  what implementations actually do, once enough receivers have quietly
  accreted the same tolerances around the same popular sender's bugs, and
  the real, de facto protocol drifts away from the document that is
  supposed to define it.

## 11. Failure modes and misuse

**HTTP request smuggling.** Symptom. A front-end proxy and a back-end server
disagree about where one HTTP request ends and the next one begins, and an
attacker-crafted request causes the back end to interpret part of one
request as the start of a second, smuggled request that the attacker did not
send through the normal path. Cause. Both HTTP implementations liberally
accept an ambiguous or duplicated pair of `Content-Length` and
`Transfer-Encoding` framing headers, but each resolves the ambiguity
differently, exactly the kind of parser differential dimension 3's security
force warns about. Fix. Treat request framing as a core, meaning-bearing
field, not an extension field. Reject any request carrying ambiguous or
duplicate framing headers outright rather than guessing which one governs,
so both sides of a chain agree by rejecting the same input instead of
disagreeing by each accepting it differently.

**MIME content-type sniffing.** Symptom. A resource served with an explicit
`Content-Type: text/plain` header is nonetheless rendered and executed by a
browser as HTML or JavaScript, opening a cross-site scripting path against a
site that never intended to serve executable content. Cause. The browser's
liberal, content-based guess at the "real" type overrides the sender's
explicit, authoritative declaration, which is the misapplication named in
dimension 4. A declared type is not ambiguous data to interpret generously.
It is a decision the sender already made. Fix. Honor the
`X-Content-Type-Options: nosniff` response header and stop content-based
type reinterpretation for the security-sensitive subset of content types,
treating the declared `Content-Type` as a core field rather than an
extension field.

**Silent data corruption from an over-lenient parser.** Symptom. Numbers in
a downstream report drift quietly wrong over weeks or months, with no single
error or crash pointing at the cause. Cause. An upstream producer's
serializer has a subtle bug, such as a locale-dependent decimal separator or
an off-by-one in a count, and a lenient consumer coerces the malformed value
into something plausible instead of rejecting it, so the defect is absorbed
rather than surfaced. Fix. Validate core, meaning-bearing fields strictly at
the boundary and reject a message that fails validation, reserving leniency
for genuinely unknown or optional fields only, per the bounded variant in
dimension 8.

**The flag-day failure.** Symptom. A newly written, strictly conformant
implementation of a long-lived protocol cannot interoperate with a large
share of the real, deployed population of peers, even though it correctly
follows the current written specification. Cause. Years of liberal receivers
quietly tolerating the same non-conformant sender behavior, described
directly by Marshall Rose in RFC 3117 section 4.5, until the tolerance
became load-bearing across the deployed population and the written
specification stopped describing what implementations actually do. Fix. Log
and count every accepted deviation from strict conformance by type, per
dimension 16, so drift is visible while it is still small, and periodically
retire tolerated deviations behind an explicit, coordinated version boundary
rather than letting them accumulate silently forever, per dimension 14.

**Unbounded leniency applied to core, semantic fields.** Symptom. Two
configuration files that both parse without error, and that both look
correct to a human reading them, cause different runtime behavior, because
the parser silently coerced an ambiguous value differently in each case.
The well-known YAML example is the string `no` being parsed as the boolean
`false` in some contexts and as the literal string `"no"` in others,
sometimes called the "Norway problem" in the YAML community. Cause. The
parser's leniency reaches into the meaning of a core field's type and
value, not merely into whether an unrecognized field is present. Fix.
Confine leniency strictly to the extension-field branch of the structure in
dimension 5, and require an explicit, unambiguous type for every core field,
rejecting a value the grammar cannot parse without ambiguity rather than
silently picking one interpretation.

## 12. Trade-off matrix

Compared against named alternatives at the same kind of boundary, across the
forces from dimension 3.

| Force | Postel's Law (bounded, dimension 8) | Fail Fast at the boundary | Design by Contract / strict schema validation | Deterministic error-recovery spec (HTML5-style) | Version-negotiated contract |
|---|---|---|---|---|---|
| Interoperability with uncoordinated peers | Strong. This is its founding purpose | Poor. Rejects any deviation, however harmless | Poor to medium. Depends how strict the schema is written | Strong, and consistent across implementations | Strong within a declared version window, poor outside it |
| Security / attack surface | Weakened, unless leniency is confined to extension fields | Strong. Rejects ambiguous input outright | Strong. Ambiguity is rejected by the schema | Strong. Ambiguity is removed by a shared, exact recovery rule | Strong within the negotiated version, unmanaged outside it |
| Debuggability of the producing side | Poor. Defects are hidden, not surfaced, to the sender | Strong. The sender is told immediately what is wrong | Strong. The schema names exactly which field is invalid | Medium. Errors are defined, not surfaced back to the sender | Medium. Debuggable only for callers on the current version |
| Forward compatibility (new optional fields) | Strong, when leniency is scoped to extension fields | Poor. A new field an old receiver does not expect may be rejected | Poor, unless the schema explicitly allows additional properties | Not addressed. Concerns document structure, not field extension | Strong. Version negotiation is the intended mechanism for this |
| Coordination cost across independent implementers | Low. This is the force it exists to avoid paying | High. Assumes every peer can be made to conform | Medium to high. Assumes a shared, enforced schema | High to establish, low to maintain once adopted | Medium. Requires agreeing on a negotiation mechanism, not a release date |
| Risk of accumulated technical debt (flag-day risk) | High, unless bounded and monitored per dimension 14 and 16 | Low. Nothing is silently tolerated to accumulate | Low. A schema violation is caught immediately | Low. The recovery behavior is fixed, not accreted ad hoc | Low, provided old versions are eventually retired |
| Fit for a single-team, atomically-deployable boundary | Poor. Buys nothing when coordination cost is already zero | Strong. Coordination cost genuinely is zero here | Strong. The natural default for this case | Overkill. The determinism this buys is not needed here | Overkill for the same reason |

Reading of the table. The bounded form of Postel's Law wins specifically at
the boundary the original RFCs were written for, a genuinely open protocol
with many uncoordinated implementers and a real need to extend the message
format over time. Fail Fast and Design by Contract win at any boundary a
single team fully controls. The deterministic error-recovery variant wins
where a population of implementers has already suffered the flag-day cost
of unmanaged leniency once and needs a shared, exact definition of tolerance
to avoid repeating it. Version negotiation wins wherever the protocol can
afford to name its own compatibility windows explicitly rather than
tolerating everything forever.

## 13. Related and incompatible patterns

- **Fail Fast.** Directly incompatible at the same boundary, which is why
  the Fail Fast entry itself lists the Robustness Principle in its own
  `incompatible_with` field. Fail Fast says detect an anomaly and stop
  immediately, surfacing it to the party that caused it. Postel's Law says
  absorb the anomaly and continue, sparing the caller. Both cannot govern
  one boundary at the same time, because they prescribe opposite responses
  to the identical event, an unexpected or malformed input. Dimension 4
  draws the practical line between them. Use Fail Fast at a boundary you
  fully control and can deploy atomically, and reserve the bounded form of
  Postel's Law for a boundary you genuinely do not control.
- **Adapter.** Compositional, and the most practical resolution of the
  tension with Fail Fast available in real systems. Put the liberal-accept
  logic inside a single Adapter, or anti-corruption layer, sitting exactly
  at the untrusted external boundary. The adapter translates whatever
  variety of external input it liberally accepts into the system's own
  strict internal model, and everything on the internal side of that
  adapter can then apply Fail Fast without contradiction, because by the
  time input reaches the internal model it has already been validated and
  normalized. The leniency and the strictness both exist, at different,
  clearly separated layers, rather than fighting for the same boundary.
- **Protected Variations.** Shares the same underlying goal, shielding the
  rest of a system from a source of variation, applied one layer more
  generally than Postel's Law. The "must-ignore unknown extension field"
  mechanism from dimension 8 is a specific, wire-format-level technique for
  achieving protected variations against future changes to a message
  format, in the same spirit as an interface achieving it against future
  changes to an implementation.
- **Open/Closed Principle.** The extension-field half of the structure in
  dimension 5, accepting new, unrecognized fields without editing or
  breaking every existing receiver, is the wire-protocol analogue of being
  open for extension and closed for modification. A message format that
  supports this is open to new optional fields; the receivers that already
  exist need no modification to keep working once such a field appears.
- **Template Method.** A looser relationship, but a real one for the
  deterministic error-recovery variant from dimension 8 and dimension 9.
  The WHATWG HTML parsing algorithm is, in effect, a published, versioned
  procedure every implementer must follow exactly, including its defined
  error-recovery steps, in place of leaving each implementer's own
  individual judgment to decide what "being liberal" means for a given
  piece of malformed input. The specification plays the role a Template
  Method plays inside one codebase, fixing the sequence and leaving no
  discretionary step for the implementer to vary unpredictably.

## 14. Refactoring path in and out

Introducing the bounded form of the principle at a boundary that does not
have it yet.

1. Identify the specific boundary where you exchange messages with a party
   you do not control and cannot force onto your own release schedule.
   Confirm this really is that kind of boundary, per dimension 4, rather
   than an internal call your own team could simply deploy atomically
   instead.
2. Separate every field in the message format into two explicit groups,
   core fields your own correctness depends on, and extension fields that
   are either genuinely optional today or reserved for future use. This
   mirrors the structure in dimension 5 and is the single decision that
   determines whether the result is the bounded, sanctioned variant or the
   unbounded, RFC 9413-criticized variant.
3. Wrap the boundary in an Adapter, per dimension 13, that performs all
   parsing and validation in one place rather than scattering it across
   every internal call site that happens to touch external input.
4. Inside that adapter, validate every core field strictly and reject the
   whole message on failure, exactly as Fail Fast would at an internal
   boundary.
5. Inside the same adapter, explicitly ignore, rather than reject on, any
   field not recognized as a known core or extension field, so a future
   sender's new optional field does not break today's receiver.
6. Add the deviation counter from dimension 16 for any tolerance beyond
   strict conformance that you decide to keep, so the tolerance's actual
   cost is visible from the day it is introduced, not discovered later.
7. Confirm the rest of the system, everything downstream of the adapter,
   receives only the validated, strict internal model, never the raw
   external input, keeping the internal code free to apply Fail Fast
   without contradiction.

Removing or tightening an accumulated leniency once its retirement path is
warranted, following on directly from step 6 above and from dimension 3's
flag-day argument.

1. Confirm the deviation counter for the tolerance in question has been
   running for a period long enough to represent real traffic, and read its
   actual current rate rather than assuming it is now unused.
2. If the rate is genuinely at or near zero, add an explicit rejection for
   the deviation behind a feature flag or a new protocol version, so it can
   be enabled selectively rather than for every caller at once.
3. If the rate is not near zero, do not remove the tolerance yet. Instead
   identify which specific senders still rely on it and, where feasible,
   notify them directly rather than breaking them without warning, which is
   the coordinated alternative to the uncoordinated flag day Rose describes.
4. Once the senders relying on the tolerance have migrated, or the
   deprecation window set for them has closed, flip the feature flag or
   ship the new protocol version as the default, converting the tolerated
   deviation into a rejected one.
5. Delete the now-unused tolerance branch and its deviation counter, and
   record in the specification, or the internal contract document, that the
   deviation is no longer accepted, closing the gap between the written
   contract and the implementation's real behavior that dimension 10
   identifies as the principle's most durable cost.

## 15. Testing and verification

Techniques that specifically address the risks this principle introduces.

- **Conformance and interoperability test suites.** A shared corpus of test
  vectors, run against every independent implementation of the same
  specification, is the direct countermeasure to the drift Rose describes
  in RFC 3117. The WHATWG maintains exactly this kind of shared test suite
  for HTML parsing so that independent browser engines converge on
  identical parsing behavior rather than each accreting its own separate
  set of tolerances.
- **Differential testing across implementations.** Run two or more
  independent implementations of the receiving side against the same corpus
  of malformed or ambiguous input and diff their outputs. A disagreement
  between the two is, by definition, exactly the class of parser
  differential responsible for the HTTP request smuggling failure mode in
  dimension 11, so finding the disagreement in a test environment is
  strictly better than finding it in production traffic or in an attacker's
  crafted request.
- **Fuzzing targeted at the liberal-accept branch specifically.** A
  general-purpose fuzz corpus for a parser tends to spend most of its
  mutation budget wandering through the strict, well-formed branch of the
  grammar. Bias the corpus, or write a second, separate fuzz target, toward
  inputs that are close to but not quite conformant, since that is precisely
  the surface RFC 9413 identifies as the principle's attack surface, and it
  is underrepresented by generic random mutation of already-valid inputs.
- **Golden, round-trip tests for the conservative sending half.** Serialize
  a fixed set of known messages and diff the output byte-for-byte against a
  committed canonical fixture. The sender's obligation under the principle
  is to always emit the strict, full canonical form regardless of which
  optional data happens to be set, and a golden test is the cheapest way to
  catch a regression where the sender quietly starts emitting a shortened or
  non-canonical form instead.
- **A regression corpus of previously tolerated malformed inputs.** Keep a
  living, growing test file of every input the receiver has, at some point,
  had to accept via its bounded leniency, each entry commented with why it
  exists and, where relevant, which real sender or bug motivated it. This
  corpus is what makes step 1 of the retirement path in dimension 14 safe.
  A future tightening of the receiver can be checked against the corpus to
  confirm it does not silently reintroduce an old, already-solved
  interoperability failure.

## 16. Observability signals

The point of instrumenting a lenient receiver is to make an invisible,
accumulating cost visible before it becomes the flag-day failure in
dimension 3 and dimension 11.

What to record.

- A counter of accepted deviations from strict conformance, labeled by the
  specific deviation type or rule that fired. This single signal is what
  turns dimension 14's retirement path from a guess into a measured
  decision, because it answers exactly how much traffic, from how many
  distinct sources, is actually relying on each individual piece of
  tolerated leniency.
- An alert on any deviation type that does not already match a known,
  named, deliberately tolerated case. An unrecognized deviation is either a
  brand-new peer bug that has not yet been evaluated, or an attacker
  deliberately probing the boundary for input the strict grammar was not
  supposed to accept, and both possibilities deserve a human's attention
  rather than silent, blanket tolerance.
- A rejection-rate metric for core-field validation failures, segmented by
  peer identity or client version where that is available. A rejection rate
  that rises sharply for one specific peer, correlated with a new release of
  that peer's software, points directly at a producer-side regression the
  receiver is quietly absorbing rather than surfacing, which is exactly the
  situation dimension 3's debuggability force warns against.
- A trace attribute or log tag naming which code path, strict or lenient,
  and if lenient which specific tolerated rule, handled a given message.
  When a downstream defect is eventually traced back to a message that took
  the lenient path, this attribute is what connects the eventual symptom to
  its actual, upstream cause instead of leaving the connection to guesswork.

A healthy dashboard shows the deviation counters flat and already explained
by a known, named tolerance, the unrecognized-deviation alert silent over a
long window, and the core-field rejection rate low and stable across peers
and versions. A failing instance shows a deviation counter for one specific
peer climbing steadily, or a spike in one deviation type correlated with a
new client rollout, either of which signals a producer-side regression that
the receiver's own leniency is currently hiding rather than exposing.

## 17. Security and privacy implications

This dimension is a real, active area of disagreement in the current
literature, not a settled analytical exercise, and the disagreement is
recorded here rather than smoothed over.

**Parser differentials as an attack surface, the RFC 9413 argument.** RFC
9413 states the core objection directly. Sloppy implementations and lax
interpretations of a specification can, and do, result in security problems
(https://www.rfc-editor.org/rfc/rfc9413, verified 2026-08-02). The mechanism
is concrete rather than abstract. Whenever a specification leaves room for a
receiver to be "liberal" about an ambiguous case, two different,
independently built receivers can resolve the same ambiguous input
differently, and an attacker who controls the input can exploit exactly
that difference. HTTP request smuggling, worked through in dimension 11, is
the clearest and most consequential production instance of this pattern, and
it exists specifically because two systems in the same request path each
applied their own liberal interpretation to the same ambiguous framing
headers rather than the identical strict one.

**A documented example against Tor's routing protocol.** Florentin Rochet
and Olivier Pereira's paper, "Dropping on the Edge, Flexibility and Traffic
Confirmation in Onion Routing Protocols", published in the Proceedings on
Privacy Enhancing Technologies (PoPETs) 2018, describes how tolerant,
flexible handling of malformed or unusual traffic inside Tor's onion routing
protocol can be exploited by malicious relays to convey information
covertly and to help locate the guard relay a particular onion service
uses, degrading the anonymity the protocol is meant to provide. This entry
cites the paper's title, venue, and year as verified during research for
this entry, without quoting its text directly, because the paper's PDF
could not be rendered as extractable text during verification. The claim
about its subject matter rests on a search-engine summary of the published
abstract rather than a directly confirmed quotation, and is presented here
as a documented, named example of the security force in dimension 3 rather
than a literal citation.

**The counter-argument, that the extension mechanism itself is not the
problem.** RFC 9413 and the criticism in RFC 3117 both target the unbounded
form of the principle described in dimension 8, tolerance applied to core,
meaning-bearing fields, not the bounded, must-ignore extension mechanism
that Protocol Buffers and TLS both rely on in wide production use. Confining
leniency strictly to the extension-field branch of dimension 5's structure,
and validating every core field with the same strictness Fail Fast would
demand, is the practical answer both critical documents point toward, and it
is the shape recommended throughout dimension 4, dimension 8, and the code
examples in this entry.

**A privacy implication tied to observability, not the principle itself.** A
receiver instrumented per dimension 16 to log every accepted deviation, for
the entirely legitimate purpose of measuring and eventually retiring it, is
also a receiver that may now be retaining raw, attacker-or-sender-controlled
freeform input inside a debugging or telemetry pipeline that a strict
receiver would simply have rejected before it reached any logging surface at
all. Where a tolerated deviation could plausibly carry personal or sensitive
data, that data should be handled by the same retention and access controls
as any other identifier the system stores, and the deviation log itself
reviewed for whether it needs to retain the raw payload or only the fact
that a deviation of a given type occurred.

## Code examples

Three languages, chosen because each demonstrates a different, idiomatic way
of drawing the exact line dimension 5 and dimension 8 describe. Strict
validation of core fields, and separate, explicit tolerance of unrecognized
extension fields, never the reverse. Java, Rust, and Swift are omitted
because the principle does not depend on inheritance, ownership, or any
other language-specific mechanism to demonstrate. The same structural split
would look nearly identical in any of the three, and the three shown already
cover a statically typed compiled language, a dynamically typed scripting
language, and a statically typed language with an explicit raw-field escape
hatch.

Every example below implements the same message envelope. Two strictly
required core fields, `type` and `id`, and one additional field a newer
sender might include that the current receiver does not need to recognize.
The receiver validates the core fields and ignores anything else. The sender
always emits the complete canonical shape.

### TypeScript

```typescript
interface Envelope {
  type: string;
  id: string;
  payload?: unknown;
}

// Liberal receiver: validates only the fields the contract requires.
// Anything else present in the raw input is simply never read, neither
// rejected nor merged into the result.
function parseEnvelope(raw: unknown): Envelope {
  if (typeof raw !== "object" || raw === null) {
    throw new Error("envelope must be an object");
  }
  const obj = raw as Record<string, unknown>;
  if (typeof obj.type !== "string" || obj.type.length === 0) {
    throw new Error("envelope.type must be a non-empty string");
  }
  if (typeof obj.id !== "string" || obj.id.length === 0) {
    throw new Error("envelope.id must be a non-empty string");
  }
  return { type: obj.type, id: obj.id, payload: obj.payload };
}

// Conservative sender: always emits the full canonical shape, with a
// version number, regardless of which optional fields were set.
function encodeEnvelope(env: Envelope): string {
  return JSON.stringify({
    version: 1,
    type: env.type,
    id: env.id,
    payload: env.payload ?? null,
  });
}

const fromNewerPeer = JSON.parse(
  '{"type":"order.created","id":"o-42","payload":{"sku":"A1"},"traceId":"t-9"}',
);
console.log(parseEnvelope(fromNewerPeer));
console.log(encodeEnvelope({ type: "order.created", id: "o-42" }));
```

### Python

```python
from dataclasses import dataclass
from typing import Any


@dataclass
class Envelope:
    type: str
    id: str
    payload: Any = None


def parse_envelope(raw: dict) -> Envelope:
    # Liberal: read only the two fields the contract promises, and
    # validate those two strictly. Every other key in raw, such as a
    # newer peer's "traceId", is left untouched.
    msg_type = raw.get("type")
    msg_id = raw.get("id")
    if not isinstance(msg_type, str) or not msg_type:
        raise ValueError("envelope.type must be a non-empty string")
    if not isinstance(msg_id, str) or not msg_id:
        raise ValueError("envelope.id must be a non-empty string")
    return Envelope(type=msg_type, id=msg_id, payload=raw.get("payload"))


def encode_envelope(env: Envelope) -> dict:
    # Conservative: always emit the complete canonical shape.
    return {"version": 1, "type": env.type, "id": env.id, "payload": env.payload}


if __name__ == "__main__":
    from_newer_peer = {
        "type": "order.created",
        "id": "o-42",
        "payload": {"sku": "A1"},
        "traceId": "t-9",
    }
    print(parse_envelope(from_newer_peer))
    print(encode_envelope(Envelope(type="order.created", id="o-42")))
```

### Go

```go
package main

import (
	"encoding/json"
	"errors"
	"fmt"
)

// Envelope is the strict, canonical shape this service both emits and
// relies on internally, once a message has passed the boundary.
type Envelope struct {
	Version int             `json:"version"`
	Type    string          `json:"type"`
	ID      string          `json:"id"`
	Payload json.RawMessage `json:"payload,omitempty"`
}

// ParseEnvelope is the liberal half. It decodes into a field map first,
// so a field this build does not recognize, such as a newer peer's
// extension field, is simply left unread rather than causing the whole
// decode to fail.
func ParseEnvelope(raw []byte) (Envelope, error) {
	var fields map[string]json.RawMessage
	if err := json.Unmarshal(raw, &fields); err != nil {
		return Envelope{}, err
	}
	var typ, id string
	if v, ok := fields["type"]; ok {
		_ = json.Unmarshal(v, &typ)
	}
	if v, ok := fields["id"]; ok {
		_ = json.Unmarshal(v, &id)
	}
	if typ == "" {
		return Envelope{}, errors.New("envelope.type must be a non-empty string")
	}
	if id == "" {
		return Envelope{}, errors.New("envelope.id must be a non-empty string")
	}
	return Envelope{Version: 1, Type: typ, ID: id, Payload: fields["payload"]}, nil
}

// EncodeEnvelope is the conservative half. It always writes the full
// canonical shape.
func EncodeEnvelope(e Envelope) ([]byte, error) {
	e.Version = 1
	return json.Marshal(e)
}

func main() {
	fromNewerPeer := []byte(`{"type":"order.created","id":"o-42","payload":{"sku":"A1"},"traceId":"t-9"}`)
	env, err := ParseEnvelope(fromNewerPeer)
	if err != nil {
		panic(err)
	}
	fmt.Printf("%+v\n", env)
	out, err := EncodeEnvelope(Envelope{Type: "order.created", ID: "o-42"})
	if err != nil {
		panic(err)
	}
	fmt.Println(string(out))
}
```

## 18. References

1. Jon Postel. RFC 761, "Transmission Control Protocol". Internet
   Engineering Task Force, January 1980, section 2.10.
   https://datatracker.ietf.org/doc/html/rfc761
   Verified 2026-08-02. Source of the original wording of the robustness
   principle, in dimensions 1, 2, and the Code examples header.
2. Jon Postel, ed. RFC 793, "Transmission Control Protocol". Internet
   Engineering Task Force, September 1981, section 2.10.
   https://datatracker.ietf.org/doc/html/rfc793
   Verified 2026-08-02. Source of the superseding TCP specification's
   restatement of the principle, quoted in dimension 1.
3. Robert Braden, ed. RFC 1122, "Requirements for Internet Hosts,
   Communication Layers". Internet Engineering Task Force, October 1989,
   section 1.2.2. https://datatracker.ietf.org/doc/html/rfc1122
   Verified 2026-08-02. Source of the generalized, host-wide statement of
   the principle and the "malevolent entities" language, in dimensions 1,
   3, and 9.
4. Marshall T. Rose. RFC 3117, "On the Design of Application Protocols".
   Internet Engineering Task Force, November 2001, section 4.5.
   https://datatracker.ietf.org/doc/html/rfc3117
   Verified 2026-08-02. Source of the flag-day critique quoted in
   dimensions 1, 3, and 11, and referenced in dimension 15.
5. Martin Thomson and David Schinazi. RFC 9413, `"Maintaining Robust Protocols"`. Internet Architecture Board, Internet Engineering Task
   Force, 2023. https://www.rfc-editor.org/rfc/rfc9413
   Verified 2026-08-02. Source of the active-maintenance argument against
   unbounded tolerance, quoted in dimensions 1, 3, and 17.
6. Martin Thomson. Internet-Draft, "The Harmful Consequences of the
   Robustness Principle" (draft-thomson-postel-was-wrong).
   https://datatracker.ietf.org/doc/draft-thomson-postel-was-wrong/
   Verified 2026-08-02. Predecessor draft to RFC 9413, cited in dimension 1
   for its original working title.
7. J. Klensin. RFC 5321, "Simple Mail Transfer Protocol". Internet
   Engineering Task Force, October 2008, section 4.1.1.
   https://datatracker.ietf.org/doc/html/rfc5321
   Verified 2026-08-02. Source of the SMTP trailing-whitespace tolerance
   cited as a named production use in dimension 9.
8. Google LLC. Protocol Buffers Language Guide (proto3), section
   "Unknowns". https://protobuf.dev/programming-guides/proto3/
   Verified 2026-08-02. Source of the unknown-field preservation behavior
   cited as a named production use in dimensions 8 and 9.
9. WHATWG. "HTML Standard", section 13.2, "Parsing HTML documents".
   https://html.spec.whatwg.org/multipage/parsing.html
   Verified 2026-08-02. Source of the deterministic error-recovery parsing
   variant and its historical framing, cited in dimensions 8 and 9.
10. Florentin Rochet and Olivier Pereira. "Dropping on the Edge,
    Flexibility and Traffic Confirmation in Onion Routing Protocols".
    Proceedings on Privacy Enhancing Technologies (PoPETs), 2018. Cited
    by title, venue, and year in dimension 17 as a documented security
    finding against tolerant handling of protocol traffic in Tor's onion
    routing; its full text was not independently rendered during
    verification for this entry, and the claim rests on a corroborated
    search-engine summary of the published work rather than a direct
    quotation.
11. Eric Allman. "The Robustness Principle Reconsidered". ACM Queue,
    volume 9, issue 6, 2011. Referenced by title, author, venue, and year
    for its framing of the principle needing to be applied in moderation
    once security concerns are weighed against interoperability; the
    article's full text returned an access error during verification for
    this entry and is cited here from its corroborated public summary
    rather than a direct quotation from the article body.
