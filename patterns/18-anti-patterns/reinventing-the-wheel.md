---
name: Reinventing the Wheel
slug: reinventing-the-wheel
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Reinvent the Wheel, Reinvent the Square Wheel, Design in a Vacuum, Greenfield System, Roll Your Own]
first_described: "Brown, Malveau, McCormick, Mowbray 1998"
maturity: canonical
related: [not-invented-here, golden-hammer, cargo-cult-programming, premature-optimization, vendor-lock-in, inner-platform-effect, copy-paste-programming]
incompatible_with: [common-reuse-principle, dependency-inversion-principle]
verified: 2026-08-02
---

# Reinventing the Wheel

## 1. Name, aliases, and lineage

The canonical name is Reinventing the Wheel. In ordinary English the idiom means
doing again, from the beginning, work that already has an adequate answer. The
Dictionary.com entry traces the idiom to the second half of the twentieth
century and defines it as needless or inefficient repetition of an existing
effort ([Dictionary.com, "reinvent the wheel"](https://www.dictionary.com/browse/reinvent-the-wheel),
verified 2026-08-02).

The name entered software anti-pattern catalogs through William J. Brown,
Raphael C. Malveau, Hays W. "Skip" McCormick III, and Thomas J. Mowbray,
*AntiPatterns. Refactoring Software, Architectures, and Projects in Crisis*,
first edition, John Wiley & Sons, 1998, chapter 6, "Reinvent The Wheel." Wiley
confirms the book title, authors, first edition date, publisher, ISBN, and page
count ([Wiley product page](https://www.wiley-vch.de/en/areas-interest/computing-computer-sciences/computer-science-17cs/object-technologies-17cs6/antipatterns-978-0-471-19713-3),
verified 2026-08-02). A live copy of the chapter text identifies the
anti-pattern name, its aliases "Design in a Vacuum" and "Greenfield System,"
its scale as system level, its root causes as pride and ignorance, and its
refactored solution as Architecture Mining ([Studylib copy of *AntiPatterns*](https://studylib.net/doc/27213058/antipatterns-refactoring-architectures),
verified 2026-08-02).

The harsher alias **Reinventing the Square Wheel** is used when the replacement
is not only duplicative but worse than the existing answer, engineering an
artifact that already exists as a standard solution and ending up with a
weaker result because the team was unaware of, or did not sufficiently
understand, that standard solution
([Wikipedia, "Reinventing the Wheel"](https://en.wikipedia.org/wiki/Reinventing_the_square_wheel),
verified 2026-08-20).

Reinventing the Wheel is related to Not Invented Here, but the two names do not
mean the same thing. Not Invented Here names a bias against external work.
Reinventing the Wheel names the act of rebuilding an existing answer. A team
can reinvent a wheel because it did not know the existing wheel existed, because
it rejected the existing wheel for weak reasons, because it thought learning by
building was worth the cost, or because a real requirement made the external
answer unusable. The anti-pattern begins when the rebuild cost exceeds the value
of the difference.

## 2. Problem and context

A team needs a capability that is already present in a language, standard
library, mature package, platform service, protocol, database, operating system,
or well-understood architecture. Instead of adopting, wrapping, extending, or
contributing to that existing answer, the team writes its own replacement. The
new version often starts small. It may be a date parser, retry loop, file
locking protocol, connection pool, command runner, cache, serializer, rules
engine, scheduler, identity layer, transport protocol, cryptographic envelope,
or object mapper. The first use case passes. The team ships. Months later the
homegrown part has grown a private vocabulary, private bugs, private upgrade
rules, private operational alarms, and private failure modes.

The problem is not that the team built code. Software teams are paid to build
code. The problem is that the team rebuilt a non-core capability while
underestimating the years of edge cases hidden inside the existing answer.
Mature wheels carry strange facts. Time zones have political history. Unicode
case conversion differs by locale. HTTP retries can multiply an outage. Database
connection pools can starve a server if timeout, queueing, and cancellation are
wrong. Cryptographic modes can be correct at the primitive level and broken at
the protocol level. A short local implementation tends to cover the demo path
and miss the unglamorous cases that gave the existing library its size.

The context that makes this an anti-pattern has four traits.

First, an adequate wheel exists. Adequate does not mean perfect. It means the
existing answer satisfies the written requirement at lower lifetime cost than a
replacement.

Second, the capability is not the product's source of advantage. A calendar
company may need deep calendar code. A payroll company may need deep tax rules.
A small internal dashboard usually does not need its own spreadsheet engine,
template language, authentication protocol, or JSON parser.

Third, the team has no written build-versus-adopt comparison. When asked why it
rebuilt the capability, the answer is vague. The library felt heavy. The service
felt risky. The API looked ugly. The team wanted control. Each objection may be
valid in a concrete case, but in the anti-pattern the claim is not checked
against named candidates, measured constraints, and lifetime ownership.

Fourth, the replacement becomes production infrastructure. A learning exercise
in a scratch directory is not the anti-pattern. A short-lived spike may be an
excellent way to understand a library. The failure begins when the experiment is
promoted into the path users depend on without being held to the same bar as
the mature answer it displaced.

## 3. Forces

Judgement. This dimension weighs engineering pressures. The cited sources
establish named cases and domain constraints, but the balancing below is
engineering judgement.

- **Latency.** A local wheel can reduce latency when a generic library pays for
  features the product does not need. It can also add latency by redoing work a
  mature library already tuned. The difference must be measured on the real
  workload, not guessed from code size.
- **Coupling.** Reuse couples the system to an external API, release policy, and
  dependency graph. Rebuilding removes that dependency and creates a private API
  that every local caller now learns. The coupling moves from outside the
  organization to inside it.
- **Consistency.** Existing standards create common behavior across teams and
  tools. A private wheel creates local consistency only after the team has
  documented and enforced its own semantics.
- **Operability.** Platform services and common libraries usually come with
  metrics, known failure modes, runbooks, and search results. A private wheel
  begins with none of those unless the team budgets for them.
- **Cost.** The initial build often looks cheap because the first version solves
  one case. The lifetime cost includes maintenance, security patches,
  compatibility, documentation, onboarding, incident response, and migration out.
- **Team topology.** Rebuilding can make sense when one platform team owns the
  wheel for many product teams. It harms flow when every product team rebuilds
  its own small version.
- **Cognitive load.** A standard library call may be boring, but it is easy to
  recognize. A private helper demands local knowledge. The reader must learn
  what it omits, what it guarantees, and which bugs are accepted behavior.
- **Control.** Control is the force that seduces teams. Owning every line feels
  like less risk. It is less risk only when the team has the time, skill, and
  mandate to operate the wheel for its full life.

The central trade is control against accumulated knowledge. Reinventing earns
control. It loses the review, usage, documentation, tooling, and battle history
stored in the existing answer.

## 4. Applicability and non-applicability

Reach for an internal build when these conditions hold.

- **The capability is core product value.** The work is part of what customers
  buy, not plumbing under the product. Meta's HHVM is a useful boundary case.
  Facebook built a PHP runtime because PHP execution performance and developer
  workflow affected a massive production codebase; Meta reported HHVM was used
  in sandboxes in 2011 and planned for Facebook production traffic after meeting
  its performance target ([Meta Engineering, "Speeding up PHP-based development
  with HipHop VM"](https://engineering.fb.com/2012/11/29/open-source/speeding-up-php-based-development-with-hiphop-vm/),
  verified 2026-08-02).
- **The existing options fail a written hard requirement.** A license, latency
  target, data residency rule, availability model, hardware constraint, or
  security rule rules them out. The failure must name the candidate and the
  unmet requirement.
- **The team can afford ownership after launch.** Ownership includes threat
  modeling, release notes, migration plans, compatibility tests, alerts,
  support, and deprecation.
- **The wheel is small enough to finish.** A few lines around a stable platform
  primitive may be cheaper than a large dependency. The judgement changes when
  the wheel expands into a protocol, scheduler, parser, crypto layer, or
  database.
- **The purpose is learning, and the result will not be production code.** A
  short reimplementation can teach the team how an algorithm works. The
  exercise should be thrown away or marked as reference material.
- **The new wheel will become a shared product inside the organization.** A
  platform team can build one internal library to prevent ten weaker copies.
  That team must publish an API, service-level goals, and an exit path.

Explicit non-applicability list. Do not use Reinventing the Wheel as your
chosen path in these cases.

- **Do not rebuild cryptographic algorithms, modes, random number generators, or
  authentication token formats.** OWASP warns that custom or non-tested
  cryptographic algorithms create high risk to protected data
  ([OWASP, "Using a broken or risky cryptographic algorithm"](https://owasp.org/www-community/vulnerabilities/Using_a_broken_or_risky_cryptographic_algorithm),
  verified 2026-08-02). Use reviewed libraries and standard protocols.
- **Do not rebuild date, time, locale, Unicode, currency, or email address
  parsing because the first examples look simple.** Those domains are large
  because the world is large, not because library authors enjoy size.
- **Do not rebuild an internal version of a vendor service to avoid reading that
  vendor's documentation.** Lack of familiarity is a training cost, not a
  product requirement.
- **Do not rebuild a framework feature because its API is aesthetically
  annoying.** A wrapper or adapter is cheaper than a parallel framework.
- **Do not rebuild a database, queue, cache, scheduler, or consensus component
  inside an application team unless the team is prepared to become the platform
  owner for that component.**
- **Do not rebuild when the team cannot name the migration-out plan.** If the
  wheel fails, the organization must know how callers return to the standard
  answer.
- **Do not rebuild while the same team is missing product commitments.** A wheel
  can be technically interesting and still be the wrong use of capacity.
- **Do not rebuild only to avoid a small dependency count increase.** Dependency
  count is a proxy, not a goal. Risk comes from the dependency's quality,
  maintainership, license, and blast radius.

## 5. Structure

Reinventing the Wheel is a decision and ownership anti-pattern, so its
participants are not only classes. They are roles in the path from requirement
to production code.

- **Capability need.** The real behavior the product needs. A healthy decision
  states it without naming a solution.
- **Existing wheel.** A standard library feature, mature package, hosted
  service, protocol, framework feature, or proven architecture that can satisfy
  the need.
- **Selection pressure.** The reason the team dislikes the existing wheel. This
  may be a valid requirement, a vague discomfort, a control preference, a
  misunderstanding, or a desire to learn.
- **Homegrown wheel.** The local replacement. It often starts as a thin helper
  and grows into a private subsystem.
- **Production callers.** The code paths that depend on the homegrown API. Once
  these callers exist, they raise migration cost.
- **Ownership ledger.** The missing or explicit record of who maintains the
  wheel, how it is tested, which semantics are promised, and when it should be
  retired.
- **External reality.** Security advisories, protocol updates, platform changes,
  new language releases, and user edge cases. These keep arriving after the
  first version ships.

The anti-pattern forms when the homegrown wheel reaches production before the
ownership ledger is real. The team gets code it can edit, but not the
institutional machinery that makes infrastructure dependable.

## 6. ASCII structure diagram

```text
             capability need
                    |
                    v
       +---------------------------+
       | build or adopt decision   |
       | requirement, cost, owner  |
       +-------------+-------------+
                     |
          weak or missing comparison
                     |
      +--------------+--------------+
      |                             |
      v                             v
+-------------+              +----------------+
| existing    |              | homegrown      |
| wheel       |              | wheel          |
| standard or |              | local API      |
| mature tool |              | local semantics|
+------+------+              +-------+--------+
       |                             |
       | not adopted                 | adopted by callers
       |                             v
       |                     +----------------+
       |                     | production     |
       |                     | callers        |
       |                     +-------+--------+
       |                             |
       |                             v
       |                     +----------------+
       |                     | ownership debt |
       |                     | tests, docs,   |
       |                     | alerts, fixes  |
       |                     +----------------+
       |
       v
 external knowledge remains outside the system
```

## 7. Dynamics

At runtime the anti-pattern appears as an ordinary dependency. The damaging
motion happens over time. The local wheel starts below the visibility threshold,
then becomes shared infrastructure before the team realizes it owns a platform.

```text
time ->

developer       team              homegrown wheel       production callers
    |            |                         |                      |
    | needs X    |                         |                      |
    +----------->|                         |                      |
    |            | finds existing X        |                      |
    |            | rejects it loosely      |                      |
    |            +------------------------>|                      |
    |            | writes local X v1       |                      |
    |            |                         |                      |
    |            | ships one feature       |<---------------------+
    |            |                         |     new callers copy API
    |            |                         |                      |
    |            | edge case appears       |                      |
    |            +------------------------>| patch adds branch    |
    |            |                         |                      |
    |            | security or platform    |                      |
    |            | change arrives          |                      |
    |            +------------------------>| owner unclear        |
    |            |                         |                      |
    | migration  |                         | many call sites now  |
    | proposed   |                         | depend on local quirks
    +----------->|                         |<---------------------+
```

The loop is self-reinforcing. Each patch makes the local API more special. Each
special behavior gives callers a reason not to move back to the standard answer.
The longer the wheel runs, the more its oddities become compatibility promises.

## 8. Implementation variants

**Ignorant reimplementation.** The team does not know the wheel exists. This is
common with standard library features, framework helpers, platform service
defaults, and database functions. It is easiest to fix. A code review comment,
internal cookbook, or lint rule can redirect future work.

**Aesthetic reimplementation.** The team knows the wheel exists but dislikes its
shape. The package name is ugly. The API is verbose. The framework asks for
configuration the team finds annoying. Judgement. This variant is risky because
it feels like taste while creating real maintenance.

**Control reimplementation.** The team wants every line under local control. The
argument may be sound for core systems. It becomes the anti-pattern when control
is valued without pricing the labor needed to keep that control useful.

**Learning reimplementation.** A developer rewrites a parser, allocator,
scheduler, runtime, or cryptographic primitive to understand it. This is valid
when scoped as an exercise. It becomes dangerous when merged into production
because it passed toy tests.

**Performance reimplementation.** A team believes the existing wheel is too slow
and writes a narrower version. This can be sound. The bar is measurement on
production-like traffic, correctness parity tests, and a rollback path. Meta's
HHVM work is a cited case where a runtime rebuild was tied to production
performance and workflow goals rather than vague preference
([Meta Engineering, "The HipHop Virtual Machine"](https://engineering.fb.com/2011/12/09/open-source/the-hiphop-virtual-machine/),
verified 2026-08-02).

**Protocol reimplementation.** A team creates a private wire format, key
exchange, consensus flow, or messaging protocol. This has high blast radius
because every other system must either learn the private protocol or pass
through an adapter.

**Wrapper that becomes a wheel.** A small adapter around a library accumulates
features until callers depend on the adapter rather than the library. This is
not always bad. It is bad when the adapter stops tracking the underlying
library, hides errors, or blocks upgrades.

**Fork by neglect.** The team copies external code into the repository and then
modifies it. Over time the copy stops receiving upstream fixes. This variant is
especially common in vendored snippets, generated clients, and sample code.

**AI-generated reimplementation.** A coding assistant writes a helper that the
language already provides. The code looks plausible, but nobody checked the
standard library first. This variant needs review rules that ask, "What existing
wheel did we evaluate?"

## 9. Known production uses

This dimension names real production cases. The sources do not all call their
case an anti-pattern. Where this entry classifies a case, that classification is
judgement.

**Netscape 6 browser rewrite.** Joel Spolsky's 2000 essay describes Netscape's
decision to rewrite its browser code from scratch after Netscape 4, with no
Netscape 5 release and a long wait before the Netscape 6 beta. He calls the
rewrite a severe strategic error and contrasts it with continuing to improve the
old codebase ([Joel Spolsky, "Things You Should Never Do, Part I"](https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/),
verified 2026-08-02). Mozilla's own community archive states that Netscape 6 was
released on November 14, 2000 and was the first Netscape product based on open
source code ([Mozilla community archive](https://blog.mozilla.org/community/2013/05/06/milestone-netscape-6-released-based-on-open-source-code/),
verified 2026-08-02). Judgement. This is the cleanest famous production example
of wheel rebuilding as rewrite risk, because the team traded accumulated product
behavior for a new codebase while competitors kept shipping.

**Zoom meeting encryption before its 2020 E2EE work.** Citizen Lab reported in
April 2020 that Zoom had "rolled their own" meeting encryption scheme and found
that Zoom meetings used a single AES-128 key in ECB mode for meeting audio and
video ([Citizen Lab, "Move Fast and Roll Your Own Crypto"](https://citizenlab.ca/research/move-fast-roll-your-own-crypto-a-quick-look-at-the-confidentiality-of-zoom-meetings/),
verified 2026-08-02). Zoom later documented an end-to-end encryption option
where participant machines generate keys and Zoom servers do not have access to
the decryption keys ([Zoom Support, "Using end-to-end encryption in Zoom
meetings"](https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0065408),
verified 2026-08-02). Judgement. This is a production security example of
private protocol design where the existing wheel was not a single library but a
set of established cryptographic constructions and review practices.

**Telegram MTProto.** Jakob Jakobsen and Claudio Orlandi analyzed Telegram's
MTProto after auditing Telegram's Android source code. Their paper reports that
the symmetric encryption scheme was not IND-CCA secure and says well-studied
authenticated-encryption schemes should be preferred to home-brewed encryption
schemes ([Aarhus University publication page, "On the CCA (in)security of
MTProto"](https://pure.au.dk/portal/en/publications/on-the-cca-insecurity-of-mtproto/),
verified 2026-08-02). Judgement. This is a production messaging example where a
private protocol carried more review burden than a product team should assume
lightly.

**Facebook HHVM.** Meta reported that Facebook deployed HipHop for PHP in 2010,
used HHVM in development sandboxes in 2011, and worked toward using HHVM for all
PHP execution ([Meta Engineering, "The HipHop Virtual Machine"](https://engineering.fb.com/2011/12/09/open-source/the-hiphop-virtual-machine/),
verified 2026-08-02). The later HHVM article states that the project sought a
production-ready virtual machine and a unified production and development
environment ([Meta Engineering, "Speeding up PHP-based development with HipHop
VM"](https://engineering.fb.com/2012/11/29/open-source/speeding-up-php-based-development-with-hiphop-vm/),
verified 2026-08-02). Judgement. This is a counterexample that keeps the entry
honest. It is wheel rebuilding, but the business case was tied to a core
Facebook workload, measured performance, and a team that could own the runtime.

**Amazon Dynamo.** Amazon's Dynamo paper presents a highly available key-value
storage system used by core Amazon services to support an always-on experience
([Amazon Science, "Dynamo: Amazon's highly available key-value store"](https://www.amazon.science/publications/dynamo-amazons-highly-available-key-value-store),
verified 2026-08-02). Judgement. Dynamo shows when rebuilding storage can be
valid. At Amazon's scale, the wheel was part of the operating model and the
paper records explicit trade-offs.

**Google Chubby.** The Google SRE book describes Chubby as a lock service with a
filesystem-like API, backed by Paxos, used for master election and consistent
data in Google's production environment ([Google SRE Book, "Production
Environment"](https://sre.google/sre-book/production-environment/), verified
2026-08-02). Judgement. Like Dynamo, Chubby is a valid internal wheel because it
became a platform primitive with a clear operational role.

## 10. Consequences

Judgement. Consequences vary by domain, but the categories below recur in
software systems.

Positive consequences when the rebuild is warranted.

- The team can tune behavior to a narrow workload that general tools do not
  serve well.
- The organization controls release timing, compatibility policy, and failure
  response.
- Domain knowledge deepens when the capability is core to the product.
- A shared internal wheel can reduce duplication if it replaces many weaker
  local copies.
- The team may remove external license, data residency, pricing, or supply-chain
  risks that mattered in the real decision.
- The organization can publish the wheel as open source or a platform product
  when it proves useful beyond the original team.

Negative consequences when the rebuild is the anti-pattern.

- The first version hides lifetime cost. Maintenance work arrives after the
  staffing plan has moved on.
- Edge cases become user-facing bugs. The mature wheel already learned cases the
  local team has not yet met.
- Private semantics raise onboarding cost. New engineers cannot bring knowledge
  from prior jobs or public documentation.
- Security review burden moves inside the team. This is especially expensive
  for authentication, authorization, parsing, serialization, and cryptography.
- Operability starts late. Logs, metrics, dashboards, and runbooks appear after
  the first incident instead of before launch.
- Compatibility pressure freezes poor decisions. Once callers depend on a bug,
  the bug becomes a contract.
- The local API can block upgrades to the underlying platform because it
  preserves old assumptions.
- Product delivery slows because engineers maintain plumbing rather than product
  behavior.

## 11. Failure modes and misuse

Judgement. The following triples are phrased as observable symptoms so reviewers
and operators can recognize the anti-pattern in a live codebase.

**Symptom.** A small helper grows branches for case conversion, escaping,
normalization, and locale rules.
**Cause.** The team rebuilt a standard parser or formatter after testing only
examples from one market.
**Fix.** Replace call sites with the language or platform library behind an
adapter, add golden tests for the observed edge cases, then delete local logic.

**Symptom.** A retry helper causes a traffic spike during an upstream outage.
**Cause.** The local retry loop lacks jitter, budget limits, cancellation, and
idempotency checks.
**Fix.** Move to a tested resilience library or central client policy. Add
metrics for attempts per request and retry-exhausted outcomes.

**Symptom.** A security review blocks release because a custom token format or
encryption wrapper lacks threat modeling.
**Cause.** The team treated encoding as security design.
**Fix.** Use a standard protocol and reviewed library. Record why each primitive
is present and which party owns keys.

**Symptom.** Engineers keep asking whether the local cache is safe across
threads, processes, and deploys.
**Cause.** The homegrown cache has no documented consistency model.
**Fix.** State the model in tests and docs. If the model matches an existing
cache, migrate. If it does not, make the owner explicit.

**Symptom.** A wrapper around a vendor SDK is harder to upgrade than the SDK.
**Cause.** The wrapper copied most of the vendor surface and added local quirks.
**Fix.** Collapse the wrapper to the small policy layer the product needs.
Expose the vendor types where hiding them adds no value.

**Symptom.** A production incident cannot be searched on the web because every
error name is internal.
**Cause.** The team replaced a common component with private vocabulary.
**Fix.** Map local error codes to standard terms in logs and docs, then retire
the private component where possible.

**Symptom.** A migration estimate keeps increasing because tests assert exact
local behavior that nobody intended as an API.
**Cause.** The wheel shipped without an ownership ledger, so accidental behavior
became compatibility.
**Fix.** Classify behaviors as contract or accident, add deprecation warnings
for accident cases, and migrate call sites in slices.

**Symptom.** The team argues that no library fits, but no one can name which
libraries were evaluated.
**Cause.** The decision process is post-hoc rationalization.
**Fix.** Pause the build. Write the requirement, candidates, rejected reasons,
and ownership cost. Resume only if the written comparison supports it.

**Symptom.** The local implementation handles the success path but not malformed
input, timeouts, cancellation, or partial failure.
**Cause.** The team tested the problem as a feature, while the existing wheel
had been tested as infrastructure.
**Fix.** Add adversarial and property tests before adding features. Prefer a
well-used library if the gap is not core.

**Symptom.** Engineers describe the component as "temporary" years after many
services depend on it.
**Cause.** A learning or spike implementation escaped into production.
**Fix.** Treat it as production until removed. Add an owner, version it, publish
the migration plan, and measure caller count weekly.

## 12. Trade-off matrix

Judgement. The alternatives are named patterns or strategies, not strawmen.

| Force | Reinventing the Wheel | Adopt Mature Library | Adapter or Facade | Contribute Upstream | Buy Managed Service | Architecture Mining |
|---|---|---|---|---|---|---|
| Latency | Can win on narrow workloads, can lose through immature code | Often tuned broadly | Adds small call overhead | Same as library after release | Network cost may dominate | Depends on mined asset |
| Coupling | Couples callers to private API | Couples to external API | Couples callers to local boundary | Couples to project process | Couples to vendor contract | Couples to internal standard |
| Consistency | Local semantics drift | Shared semantics with community | Shared local policy | Shared semantics plus fixes | Shared vendor behavior | Shared organizational baseline |
| Operability | Must be built from zero | Known failures and docs | Local logs can wrap common errors | Same as library | Vendor runbooks and status | Internal runbooks required |
| Cost | Low first build, high lifetime risk | Low build, upgrade cost later | Moderate wrapper cost | Review and coordination cost | Subscription and exit cost | Discovery and governance cost |
| Team topology | Works only with a true owner | Works for product teams | Works for platform boundary | Needs open source skill | Works when ops can be outsourced | Works when reuse spans teams |
| Cognitive load | High local learning | Lower for common tools | Medium | Medium | Medium, plus vendor model | Medium to high during rollout |
| Control | Maximum local control | Limited control | Control over policy boundary | Influence, not command | Contractual control | Shared internal control |
| Security | Local review burden | Community and maintainer review | Boundary can centralize policy | Fixes can return to ecosystem | Vendor risk review needed | Internal review still needed |
| Exit path | Hard after call sites grow | Usually replaceable | Easier if boundary is small | Same as library | Must plan data and API exit | Depends on chosen standard |

Use this table before writing code. If the only winning cell for rebuilding is
"control," the decision is probably weak. If several cells name measured,
product-specific gains and an owner exists, rebuilding may be the right call.

## 13. Related and incompatible patterns

**Not Invented Here** is the closest relative. NIH is a motive or bias.
Reinventing the Wheel is the resulting action. A team can have one without the
other, but they often arrive together.

**Golden Hammer** points in the opposite direction. Golden Hammer overuses one
familiar tool. Reinventing the Wheel refuses the available tool and writes a
new one. Both avoid fresh evaluation.

**Cargo Cult Programming** copies surface form without understanding. A team can
cargo-cult an existing wheel by copying its API without the hidden invariants
that make it work.

**Inner Platform Effect** is what Reinventing the Wheel becomes after it grows.
The local helpers turn into a private platform that mimics the host language,
database, queue, deployment system, or cloud provider.

**Vendor Lock-In** can be a real reason to avoid a service. It becomes a cover
story when the team invokes lock-in against every external option without
pricing the lock-in created by local code.

**Common Reuse Principle** conflicts with scattered wheel rebuilding because
reuse should group things that change together. A private copy in every feature
module creates unrelated release reasons.

**Dependency Inversion Principle** can contain the damage. Put a narrow
interface around an external wheel when the product needs insulation. Do not use
the principle as an excuse to build a parallel implementation behind the
interface before one is needed.

**Adapter** and **Facade** are often better alternatives. They let the team hide
awkward external details while keeping the mature implementation.

**Strangler Application** is a path out. A local wheel can be wrapped, drained,
and replaced with an external wheel one caller group at a time.

## 14. Refactoring path in and out

To introduce an internal wheel safely, make the decision hard to fake.

1. State the capability in solution-neutral language.
2. List the existing wheels evaluated, with version, license, maturity, and the
   exact requirement each one failed.
3. Write the ownership ledger. Name the owner, compatibility rule, security
   review path, release process, observability signals, and exit plan.
4. Build the smallest vertical slice that proves the differentiating
   requirement, not the easiest success path.
5. Create parity tests against the existing wheel for behavior that should match
   it.
6. Add failure tests for malformed input, cancellation, timeout, concurrency,
   resource exhaustion, and upgrade.
7. Publish the API and version policy before the second caller adopts it.
8. Review the decision after production data arrives. If the measured gain is
   absent, migrate out before callers multiply.

To remove an existing homegrown wheel, reduce blast radius before deleting code.

1. Inventory callers with static search and runtime metrics.
2. Classify behavior into intended contract, accidental quirk, and unknown.
3. Choose the target. It may be a library, platform service, hosted product, or
   smaller adapter over the current wheel.
4. Add an anti-corruption adapter so callers can migrate without seeing the
   target's whole API.
5. Move low-risk callers first and compare outputs in shadow mode where safe.
6. Add deprecation warnings on the old API and publish a deadline.
7. Remove dead branches after each caller slice moves.
8. Keep a rollback path until the new wheel has passed real traffic.
9. Delete the old implementation, docs, alerts, and support runbooks in the same
   change set so no stale references remain.

Named refactorings that often apply are Replace Function with Command when a
loose helper needs an explicit object boundary, Extract Function and Extract
Class when the local wheel is tangled into product code, Move Function when the
behavior belongs in a shared module, and Substitute Algorithm when a homegrown
algorithm can be replaced behind the same tests. These refactoring names come
from Martin Fowler, *Refactoring. Improving the Design of Existing Code*, second
edition, Addison-Wesley, 2018, catalog chapters.

## 15. Testing and verification

Judgement. Testing a homegrown wheel is harder than testing code that calls a
mature wheel, because the team now owns both product behavior and infrastructure
behavior.

For code that avoids the anti-pattern, test the boundary. If a product service
uses a standard JSON parser, password hashing library, HTTP client, or scheduler,
do not retest the library's whole contract. Test the product's policy around it:
which options are set, which errors are mapped, which timeouts apply, and which
inputs are accepted.

For a homegrown wheel that must exist, use a higher bar.

- **Parity tests.** Run the same inputs through the existing wheel and the local
  wheel where behavior should match. Differences must be accepted explicitly.
- **Golden corpus.** Keep real examples that caused bugs. Add the input,
  expected output, and incident or ticket link.
- **Property tests.** Use generated inputs for parsers, serializers, encoders,
  escaping, normalization, and retry math.
- **Fuzz tests.** Apply fuzzing to anything that accepts untrusted bytes.
- **Concurrency tests.** Run under race detection where the language offers it.
- **Fault injection.** Simulate timeouts, partial reads, cancellation, clock
  jumps, dependency errors, corrupt files, and process restarts.
- **Compatibility tests.** Run old and new versions against the same stored
  data or wire messages before changing formats.
- **Performance tests.** Measure p50, p95, p99, memory, allocations, and tail
  behavior under load. The claim "our version is faster" is not meaningful
  without this.
- **Security tests.** Threat model inputs, trust boundaries, key handling, and
  error messages before production use.

Test doubles need care. A fake of the homegrown wheel can hide bugs in the
wheel. Prefer contract tests that every real implementation and every fake must
pass. For adapters around external wheels, a fake is fine when it models product
policy rather than reimplementing the dependency.

## 16. Observability signals

Judgement. A homegrown wheel should be visible as infrastructure, not hidden as
ordinary helper code.

Log the wheel name, version, decision branch, caller, and error class at the
boundary. Do not log secrets, tokens, raw credentials, or private user content.
For retry, queue, cache, scheduler, parser, and protocol wheels, record both
accepted and rejected work. A parser with zero parse errors may be unused, not
healthy. A retry loop with no retry-exhausted events may be fine, or it may have
no timeout path.

Metrics should include:

- request or operation count by caller
- success, soft failure, hard failure, and fallback count
- p50, p95, and p99 latency
- queue depth, wait time, and drop count for async wheels
- retry attempts per original request
- cache hit rate, miss rate, eviction count, and stale-read count
- parse rejection count by reason
- version adoption by caller
- deprecation warning count
- divergence count when shadowing an existing wheel
- security-sensitive rejects, such as invalid signatures or malformed tokens

A healthy dashboard shows stable caller count, known versions, bounded latency,
low error rate, and no surprise growth in fallback paths. A failing dashboard
shows one of three shapes. The first is growth without ownership, where caller
count climbs but no team is assigned. The second is silent divergence, where the
local wheel and existing wheel return different results in shadow mode. The
third is retry or fallback amplification, where the wheel hides upstream failure
until it multiplies load.

Trace attributes should name the wheel and the chosen branch. For example,
`wheel.name=local_retry`, `wheel.version=3`, `retry.attempt=2`, and
`fallback.used=true`. These attributes let incident responders see when a
private wheel is on the hot path.

## 17. Security and privacy implications

Judgement. Reinventing the Wheel is silent on security unless the wheel touches
a trust boundary, untrusted input, identity, authorization, secrets, encryption,
storage, or network protocols. When it does touch those areas, risk rises
quickly.

The primary security risk is false confidence. A homegrown component can look
small because it delegates to strong primitives while composing them wrongly.
Citizen Lab's Zoom report is an example at protocol level, where the named
primitive was AES but the meeting encryption design had weaknesses
([Citizen Lab](https://citizenlab.ca/research/move-fast-roll-your-own-crypto-a-quick-look-at-the-confidentiality-of-zoom-meetings/),
verified 2026-08-02). The MTProto analysis makes the same larger point about
preferring well-studied authenticated-encryption schemes over home-brewed
schemes ([Aarhus University](https://pure.au.dk/portal/en/publications/on-the-cca-insecurity-of-mtproto/),
verified 2026-08-02).

Privacy risk appears when a local wheel handles data classification, masking,
export, deletion, retention, audit trails, or consent. Mature platform services
often have controls for these duties. A private wheel must either implement
equivalent controls or stay away from regulated data.

Supply-chain risk cuts both ways. Adopting a dependency can import malicious or
abandoned code. Rebuilding avoids that external dependency but creates an
internal supply chain with fewer reviewers. The right response is not automatic
adoption or automatic rebuilding. The right response is risk analysis by
dependency class, maintainer record, license, update path, and blast radius.

Security review checklist:

- Does a reviewed standard or library already cover this function?
- Which trust boundary does the wheel cross?
- What input is attacker controlled?
- What secrets can pass through it?
- What happens on malformed input, timeout, replay, duplicate message, and
  downgrade?
- Are errors safe to expose?
- Can algorithms, keys, formats, and protocol versions rotate?
- Does the wheel support audit logging without leaking private data?
- Who tracks advisories and upstream protocol changes?
- What is the deprecation path if the design is found weak?

## 18. References

- Brown, William J., Raphael C. Malveau, Hays W. "Skip" McCormick III, and
  Thomas J. Mowbray. *AntiPatterns. Refactoring Software, Architectures, and
  Projects in Crisis*. First edition. John Wiley & Sons, 1998. Chapter 6,
  "Reinvent The Wheel." Bibliographic details verified through Wiley product
  page, https://www.wiley-vch.de/en/areas-interest/computing-computer-sciences/computer-science-17cs/object-technologies-17cs6/antipatterns-978-0-471-19713-3,
  verified 2026-08-02. Chapter metadata checked against
  https://studylib.net/doc/27213058/antipatterns-refactoring-architectures,
  verified 2026-08-02.
- Dictionary.com. "reinvent the wheel." https://www.dictionary.com/browse/reinvent-the-wheel,
  verified 2026-08-02.
- Wikipedia. "Reinventing the Wheel." https://en.wikipedia.org/wiki/Reinventing_the_square_wheel,
  verified 2026-08-20.
- Selikoff, Scott. "The 'Reinventing the Wheel' Anti-Pattern." Down Home
  Country Coding, December 10, 2009. https://www.selikoff.net/2009/12/10/why-reinvent-the-wheel/,
  verified 2026-08-02.
- Spolsky, Joel. "Things You Should Never Do, Part I." Joel on Software, April
  6, 2000. https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/,
  verified 2026-08-02.
- Mozilla Community Archive. "Milestone: Netscape 6 released based on open
  source code." May 6, 2013. https://blog.mozilla.org/community/2013/05/06/milestone-netscape-6-released-based-on-open-source-code/,
  verified 2026-08-02.
- Marczak, Bill, and John Scott-Railton. "Move Fast and Roll Your Own Crypto. A
  Quick Look at the Confidentiality of Zoom Meetings." Citizen Lab Research
  Report No. 126, University of Toronto, April 2020.
  https://citizenlab.ca/research/move-fast-roll-your-own-crypto-a-quick-look-at-the-confidentiality-of-zoom-meetings/,
  verified 2026-08-02.
- Zoom Support. "Using end-to-end encryption in Zoom meetings."
  https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0065408,
  verified 2026-08-02.
- Jakobsen, Jakob, and Claudio Orlandi. "On the CCA (in)security of MTProto."
  ACM Workshop on Privacy in the Electronic Society, 2016. Publication page:
  https://pure.au.dk/portal/en/publications/on-the-cca-insecurity-of-mtproto/,
  verified 2026-08-02.
- OWASP Foundation. "Using a broken or risky cryptographic algorithm."
  https://owasp.org/www-community/vulnerabilities/Using_a_broken_or_risky_cryptographic_algorithm,
  verified 2026-08-02.
- Meta Engineering. "The HipHop Virtual Machine." December 9, 2011.
  https://engineering.fb.com/2011/12/09/open-source/the-hiphop-virtual-machine/,
  verified 2026-08-02.
- Meta Engineering. "Speeding up PHP-based development with HipHop VM."
  November 29, 2012. https://engineering.fb.com/2012/11/29/open-source/speeding-up-php-based-development-with-hiphop-vm/,
  verified 2026-08-02.
- Amazon Science. "Dynamo: Amazon's highly available key-value store."
  https://www.amazon.science/publications/dynamo-amazons-highly-available-key-value-store,
  verified 2026-08-02.
- Google SRE Book. "Production Environment." https://sre.google/sre-book/production-environment/,
  verified 2026-08-02.
- Fowler, Martin. *Refactoring. Improving the Design of Existing Code*. Second
  edition. Addison-Wesley, 2018. Catalog chapters.

## Code examples

The samples below use the same rule in three languages. They implement a small
policy wrapper around a standard URL parser rather than parsing URLs by hand.
The point is not URL parsing itself. The point is to keep product policy local
and leave syntax to a mature library.

### TypeScript

```typescript
type AllowedUrl = {
  host: string;
  path: string;
};

export function parseAllowedUrl(raw: string): AllowedUrl {
  const url = new URL(raw);
  if (url.protocol !== "https:") {
    throw new Error("only https URLs are accepted");
  }
  if (!url.hostname.endsWith(".example.com")) {
    throw new Error("host is outside the allowed zone");
  }
  return { host: url.hostname, path: url.pathname };
}

const parsed = parseAllowedUrl("https://api.example.com/v1/items?q=1");
console.log(`${parsed.host}${parsed.path}`);
```

Run with:

```text
npx tsc --strict --lib es2020,dom reinventing-wheel.ts
node reinventing-wheel.js
```

### Python

```python
from urllib.parse import urlparse


def parse_allowed_url(raw: str) -> tuple[str, str]:
    url = urlparse(raw)
    if url.scheme != "https":
        raise ValueError("only https URLs are accepted")
    if not url.hostname or not url.hostname.endswith(".example.com"):
        raise ValueError("host is outside the allowed zone")
    return url.hostname, url.path


if __name__ == "__main__":
    host, path = parse_allowed_url("https://api.example.com/v1/items?q=1")
    print(f"{host}{path}")
```

Run with:

```text
python3 reinventing_wheel.py
```

### Go

```go
package main

import (
	"errors"
	"fmt"
	"net/url"
	"strings"
)

type AllowedURL struct {
	Host string
	Path string
}

func ParseAllowedURL(raw string) (AllowedURL, error) {
	parsed, err := url.Parse(raw)
	if err != nil {
		return AllowedURL{}, err
	}
	if parsed.Scheme != "https" {
		return AllowedURL{}, errors.New("only https URLs are accepted")
	}
	if !strings.HasSuffix(parsed.Hostname(), ".example.com") {
		return AllowedURL{}, errors.New("host is outside the allowed zone")
	}
	return AllowedURL{Host: parsed.Hostname(), Path: parsed.Path}, nil
}

func main() {
	parsed, err := ParseAllowedURL("https://api.example.com/v1/items?q=1")
	if err != nil {
		panic(err)
	}
	fmt.Printf("%s%s\n", parsed.Host, parsed.Path)
}
```

Run with:

```text
go run reinventing_wheel.go
```
