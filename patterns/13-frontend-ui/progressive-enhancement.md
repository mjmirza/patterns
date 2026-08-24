---
name: Progressive Enhancement
slug: progressive-enhancement
family: 13-frontend-ui
category: Delivery Strategy
aliases: [PE, Layered Web Design]
first_described: "Steven Champeon and Nick Finck, SXSW, 11 March 2003"
maturity: canonical
related: [islands-architecture, server-components, atomic-design]
incompatible_with: []
verified: 2026-08-21
---

# Progressive Enhancement

## 1. Name, aliases, and lineage

The canonical name is Progressive Enhancement, a design philosophy
that builds a web experience starting from a working baseline of
semantic content and functionality available to every user, then
layers presentation and behavior on top for users whose browser can
support it. The term was coined by Steve Champeon, with Nick Finck,
in a presentation titled "Inclusive Web Design For the Future" at
SXSW Interactive on 11 March 2003, and expanded in a following series
of articles. MDN's own glossary defines the resulting idea directly.
"a design philosophy that provides a baseline of essential content
and functionality to as many users as possible, while delivering the
best possible experience only to users of the most modern browsers
that can run all the required code."

The alias **PE** is the common abbreviation used throughout web
development documentation and discussion. **Layered Web Design**
names the same idea by describing its mechanism, content, then
presentation, then behavior, added in successive layers, rather than
by its outcome.

## 2. Problem and context

Before Progressive Enhancement was named, a common alternative
approach, graceful degradation, started from the richest possible
experience, built for the most capable browsers, and then attempted
to strip features back for users on older or less capable browsers,
an approach Champeon himself characterized as building from an
assumed baseline browser and treating everyone else as an
afterthought. This left users on an older browser, a slow connection,
or assistive technology with a degraded, sometimes broken experience,
since the richest version was the one actually designed and tested
first. Progressive Enhancement solves this by inverting the starting
point entirely, building a genuinely working experience from
semantic HTML content first, verified to work for every user with no
CSS and no JavaScript at all, and only then layering CSS for
presentation and JavaScript for behavior on top, so a user without
either still gets a working, if plainer, experience.

## 3. Forces

The pattern balances the following competing pressures.

- **Universal baseline access.** Favored. Because the starting point
  is semantic HTML content with no dependency on CSS or JavaScript,
  every user, regardless of browser capability, connection quality,
  or assistive technology, gets a genuinely working baseline
  experience.
- **A richer experience for capable browsers.** Favored, layered on
  top. A user with a modern, capable browser still receives the full,
  enhanced presentation and interactivity, since nothing about the
  baseline-first approach prevents adding a richer layer for users who
  can support it.
- **Development effort spent building and testing the baseline
  first.** Sacrificed in exchange for the universal-access benefit. A
  team practicing Progressive Enhancement spends real effort
  verifying the baseline genuinely works with no CSS and no
  JavaScript, effort a team building only for the richest experience
  would not spend at all.
- **Feature detection over assumption.** Favored. Rather than
  assuming a target browser's capabilities, as the graceful
  degradation approach implicitly does, Progressive Enhancement uses
  feature detection to decide whether a given enhancement can safely
  be layered on for a given user.

## 4. Applicability and non-applicability

Reach for Progressive Enhancement when the following hold.

- The application or site genuinely needs to serve a wide, uncertain
  range of browser capabilities, connection quality, or assistive
  technology, where a broken baseline for some users is a real,
  unacceptable cost.
- The team is prepared to build and verify a working, semantic HTML
  baseline first, before adding CSS presentation or JavaScript
  behavior, rather than building the richest version first and
  hoping it degrades acceptably.
- The content and core functionality can genuinely be expressed in
  plain, semantic HTML, with CSS and JavaScript adding presentation
  and behavior on top rather than being load-bearing for the content
  to exist at all.

Do NOT reach for Progressive Enhancement in these cases, and the
reason matters more than the rule.

- **The application is genuinely a rich, interactive tool that has no
  real baseline experience without JavaScript**, such as a
  design tool, a spreadsheet, or a real-time collaborative editor,
  where there is no genuinely useful degraded version to build
  toward.
- **The audience and deployment context are tightly controlled and
  known to support a specific, modern baseline**, such as an internal
  enterprise tool deployed only to a managed fleet of current
  browsers, where the universal-access benefit has little practical
  value.
- **The team is not prepared to invest the extra effort of building
  and verifying a genuinely working baseline first**, adopting the
  philosophy without the discipline to test the no-CSS,
  no-JavaScript baseline produces the name without the actual
  benefit.

## 5. Structure

Progressive Enhancement has three structural layers, applied in
order.

- **Content**, semantic HTML that expresses the page's actual
  information and functionality, working correctly with no CSS and
  no JavaScript at all.
- **Presentation**, CSS layered on top of the content, styling the
  baseline into a visually refined experience for browsers that
  support it.
- **Behavior**, JavaScript layered on top of both content and
  presentation, adding interactivity for browsers and contexts that
  support it, using feature detection to decide what to enable.

## 6. ASCII structure diagram

```
  Layer 3   +----------------------------------------------------+
  Behavior  |  JavaScript, added via feature detection            |
            |  (form validation, dynamic updates, animations)     |
            +----------------------------------------------------+
                                    ^
  Layer 2   +----------------------------------------------------+
  Presentation |  CSS, styling the semantic content                |
            +----------------------------------------------------+
                                    ^
  Layer 1   +----------------------------------------------------+
  Content   |  Semantic HTML, works with no CSS and no JavaScript |
            |  (a working form, a readable article, a link)       |
            +----------------------------------------------------+
```

## 7. Dynamics

The trace below shows a form built with Progressive Enhancement,
working at the baseline and gaining behavior for a capable browser.

```
Baseline request, no JavaScript

a user with JavaScript disabled requests the page
   |-- the semantic HTML form renders, with a real action attribute
       pointing at a server endpoint
   |-- the user fills in the form and submits it
   |-- the browser performs a full page navigation to the server
       endpoint, which processes the submission and returns a new page

Enhanced request, JavaScript available

a user with a capable, JavaScript-enabled browser requests the page
   |-- the same semantic HTML form renders first, exactly as before
   |-- JavaScript then runs feature detection, confirming the browser
       supports the APIs the enhancement needs
   |-- an event listener is attached to the form's submit event,
       intercepting the default full-page-navigation behavior
   |-- submitting the form now sends the data asynchronously and
       updates the page in place, without a full page reload

Feature detection failure

a user's browser lacks a required API the enhancement depends on
   |-- the feature-detection check fails
   |-- the enhancement is not applied
   |-- the form falls back to its baseline behavior, the full page
       navigation, which still works correctly
```

## 8. Implementation variants

**Feature detection before enhancement.** The core technique MDN
names directly, checking whether a browser supports a specific API
or capability before applying an enhancement that depends on it,
rather than assuming support based on an inferred browser identity.

**Polyfills for near-baseline support.** A JavaScript implementation
of a missing browser feature, used to bring an older or less capable
browser close enough to the baseline that a given enhancement can
still be safely applied.

**Server-rendered baseline with client-side enhancement.** A page
whose baseline content and functionality is rendered entirely on the
server, with client-side JavaScript layered on afterward purely to
enhance, rather than being required for the page's core content or
functionality to exist at all.

**Progressive Enhancement combined with graceful degradation.** MDN's
own documentation notes the two approaches, though often framed as
opposites, "are valid and can often complement one another," and a
real system can use Progressive Enhancement as its default
philosophy while still applying graceful-degradation techniques for
specific, narrower cases.

## 9. Known production uses

**MDN's own glossary, defining the core idea.** MDN's documentation
states the definition directly. "a design philosophy that provides a
baseline of essential content and functionality to as many users as
possible, while delivering the best possible experience only to
users of the most modern browsers that can run all the required
code." It explains the word progressive as describing a design that
"progresses the user experience up to a" richer, "fully featured
experience for users of newer browsers and devices with richer
capabilities." MDN Web Docs, "Progressive Enhancement,"
https://developer.mozilla.org/en-US/docs/Glossary/Progressive_Enhancement,
verified 2026-08-21.

**Steve Champeon's own account of the term's origin and philosophy.**
In an interview shortly after coining the term, Champeon describes
the technique's core idea. "The idea is to separate not only the
structure from its presentation, but also make distinctions between
what content needs to be arranged," rejecting the assumption of a
single target browser in favor of a baseline that works for everyone
by design. Steve Champeon, interviewed by Simon Willison, "Interview
with Steve Champeon,"
https://simonwillison.net/2003/Apr/4/interviewWithSteveChampeon/,
verified 2026-08-21.

## 10. Consequences

Positive.

- Every user gets a genuinely working baseline experience, regardless
  of browser capability, connection quality, or assistive technology,
  since the baseline is built and verified to work with no CSS and no
  JavaScript at all.
- A user with a modern, capable browser still receives the full,
  enhanced presentation and interactivity, since the richer layers
  are added on top of, not instead of, the working baseline.
- Feature detection, rather than an assumed target browser, decides
  what enhancement is safely applied, so the approach naturally
  holds up against new and unanticipated browsers and devices.

Negative.

- A team practicing the pattern spends real, additional effort
  building and verifying a working no-CSS, no-JavaScript baseline,
  effort a team targeting only the richest experience would not spend
  at all.
- An application that is genuinely, pervasively interactive with no
  real degraded baseline gains little from the approach, since
  there is no genuinely useful baseline experience to build toward.
- Adopting the philosophy's name and vocabulary without the
  discipline of actually testing the baseline produces the label
  without the real benefit, a gap that is easy to fall into
  unintentionally.

## 11. Failure modes and misuse

**Building the enhanced, JavaScript-dependent experience first, and
only afterward attempting to make a baseline work, calling the result
Progressive Enhancement.** Symptom. The supposed baseline is broken
or incomplete, since it was retrofitted from the richer version
rather than genuinely built and verified first, reproducing the exact
graceful-degradation shortcoming the pattern was named to avoid.
Cause. Confusing the pattern's name with its actual required
starting point and order of work. Fix. Build and verify the
semantic HTML baseline first, with no CSS and no JavaScript, before
adding any presentation or behavior layer, regardless of how the
richer experience is eventually built.

**Applying a JavaScript enhancement without checking whether the
browser actually supports the API it depends on.** Symptom. The
enhancement throws an error or silently fails in an older or less
capable browser, breaking the page rather than falling back to the
working baseline. Cause. Assuming a target browser's capabilities
rather than using feature detection to confirm support before
applying the enhancement. Fix. Check for the specific capability an
enhancement depends on before applying it, and fall back to the
baseline behavior when the check fails, rather than assuming support.

**Making core content or functionality depend on JavaScript running
successfully, defeating the baseline the pattern is meant to
guarantee.** Symptom. A user with JavaScript disabled or a
JavaScript error on the page cannot access the page's actual content
or complete its core functionality at all, since what was meant to
be an enhancement turned out to be load-bearing. Cause. Treating
JavaScript as a required layer rather than an additive one, letting
core content or functionality quietly depend on it. Fix. Verify the
page's actual content and core functionality genuinely work with
JavaScript disabled, treating any failure of that test as a defect
in the baseline, not an acceptable trade-off.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Progressive Enhancement | Graceful degradation | A JavaScript-required single-page application | Server-rendered with no baseline testing |
|---|---|---|---|---|
| Guaranteed baseline for every user | Strong, by construction | Weak, depends on how well degradation was tested | Weak, usually no baseline without JavaScript | Weak, untested baseline is unverified |
| Richer experience for capable browsers | Strong, layered on top | Strong, the starting point | Strong, the only point | Strong, if JavaScript happens to work |
| Development effort for the baseline | Real, deliberate investment | Real, but reactive rather than foundational | Minimal, no baseline is built | Minimal, no baseline is verified |
| Resilience to an unanticipated browser or device | Strong, feature detection over assumption | Weak, assumes a known target browser | Weak, assumes a capable, JavaScript-enabled client | Weak, untested against the unanticipated case |
| Fit for a genuinely, pervasively interactive tool | Weak, little baseline value | Weak, same reason | Strong | Strong, if reliability is otherwise addressed |

Reading of the table. Progressive Enhancement wins specifically when
serving a wide, uncertain range of users and devices matters, and the
team is willing to invest the deliberate effort of building and
verifying a genuine baseline first. A genuinely, pervasively
interactive tool with no real degraded experience, or a tightly
controlled, known-capable deployment context, gains comparatively
little from the pattern's core guarantee.

## 13. Related and incompatible patterns

- **Islands Architecture.** A complementary modern rendering strategy
  that can be understood as Progressive Enhancement applied at the
  component level, shipping static, working HTML by default and
  layering JavaScript interactivity onto explicitly marked islands.
- **Server Components.** A closely related modern technique, defaulting
  a component's rendering to a server-only, JavaScript-free baseline
  and layering client interactivity on top only for components
  explicitly marked to need it, echoing Progressive Enhancement's
  content-first ordering.
- **Atomic Design.** A complementary component-organization
  methodology a team practicing Progressive Enhancement can use to
  structure the presentation layer consistently, once the semantic
  content baseline is already in place.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an existing page or application whose core
content or functionality currently depends on JavaScript running
successfully.

1. Identify the page or feature's actual core content and
   functionality, distinguishing it from purely presentational or
   interactive enhancement.
2. Rebuild the core content and functionality as semantic HTML,
   verifying it genuinely works correctly with no CSS and no
   JavaScript at all.
3. Layer CSS presentation on top of the verified baseline, styling it
   into the intended visual experience.
4. Layer JavaScript behavior on top, using feature detection to
   decide what enhancement to apply for a given browser, and
   confirming the baseline still works correctly if the JavaScript
   fails or is disabled.
5. Add a test that specifically verifies the baseline with JavaScript
   disabled, treating any failure of that test as a defect.

Removing the pattern when it stops earning its place, most relevant
when the application has genuinely become a pervasively interactive
tool with no real baseline experience to preserve.

1. Confirm the application's core content and functionality
   genuinely has no real baseline worth preserving, rather than
   assuming so without review.
2. Migrate the application to a fully client-rendered or
   JavaScript-required model, preserving its actual behavior for
   users on a supported, capable browser.
3. Retire the no-JavaScript baseline test and the feature-detection
   layering discipline once the migration is complete.

## 15. Testing and verification

Easier because of the pattern.

- The baseline's correctness can be tested directly, with no CSS and
  no JavaScript engine involved at all, since it is genuinely only
  semantic HTML, making it fast and simple to verify in isolation.
- A test asserting the page works with JavaScript disabled gives an
  unambiguous, binary signal, the baseline either genuinely works or
  it does not, with no partial or ambiguous state to interpret.

Harder because of the pattern.

- Testing every layer, the baseline, the presentation, and the
  behavior, and confirming each genuinely degrades correctly to the
  layer below it, needs more test surface than testing only the
  richest, fully enhanced experience.
- Verifying feature detection correctly falls back to baseline
  behavior for a genuinely unsupported browser needs either real
  older browsers or a deliberate simulation of the missing
  capability, which is more involved than testing only against a
  modern, fully capable browser.

Techniques that apply.

- **No-JavaScript baseline tests.** Run the page or feature's test
  suite with JavaScript disabled entirely, asserting the core content
  and functionality still work correctly.
- **Feature-detection fallback tests.** Simulate a browser missing a
  specific capability an enhancement depends on, and assert the page
  falls back to its baseline behavior rather than breaking.
- **Layered visual regression tests.** Capture the page's appearance
  at each layer, content only, content plus presentation, and the
  fully enhanced experience, catching an unintended regression at any
  layer.
- **Full enhanced integration tests.** Test the fully enhanced
  experience end to end on a capable, JavaScript-enabled browser,
  confirming the richer layer works correctly once it is applied.

## 16. Observability signals

Progressive Enhancement has a genuine runtime footprint, since it
directly governs what a real user's browser actually receives and can
successfully use, so a dedicated production signal is honest here.

What to record.

- The rate at which users successfully complete a core action, such
  as submitting a form, broken down by whether their session had
  JavaScript enabled, since a real gap between the two rates
  signals the baseline is not genuinely working as intended.
- Feature-detection failure rates for a given enhancement, since a
  rising rate of browsers failing a specific capability check signals
  either a growing population of less capable users or a
  detection check that has become miscalibrated against current
  browser reality.

A healthy state. Users without JavaScript can still complete the
page's core actions at a rate close to users with JavaScript enabled,
and feature-detection failures correctly and consistently route to
working baseline behavior rather than a broken experience.

A failing state. A real gap between the completion rate of
users with and without JavaScript, pointing at a baseline that is not
genuinely working, or a feature-detection check that passes for a
browser that then fails to run the enhancement correctly, pointing at
a detection check that no longer matches real browser behavior.

## 17. Security and privacy implications

Progressive Enhancement is close to neutral for security, being a
delivery and layering strategy rather than a data-handling one, and
inventing a dedicated attack surface here would be dishonest. One
practical implication is worth naming.

**Because the baseline of Progressive Enhancement is a genuinely
working, full page submission or navigation rather than a client-side
intercepted request, the server-side endpoint that baseline depends
on must independently validate and authorize every request the same
way it would for any other request, since a client-side-only
enhancement, such as disabling a submit button after one click, is
never a substitute for genuine server-side validation.** Because a
Progressive Enhancement baseline deliberately keeps the server
endpoint as the real, working path rather than an afterthought behind
a JavaScript layer, a team should treat that endpoint's own
validation and authorization as the actual security boundary, and
never rely on a client-side enhancement to enforce a rule the server
does not also enforce.

## 18. References

1. MDN Web Docs. "Progressive Enhancement".
   https://developer.mozilla.org/en-US/docs/Glossary/Progressive_Enhancement
   Verified 2026-08-21. Source of the defining sentence and the
   graceful-degradation comparison quoted in dimensions 1, 8, and 9.
2. Simon Willison. "Interview with Steve Champeon".
   https://simonwillison.net/2003/Apr/4/interviewWithSteveChampeon/
   Verified 2026-08-21. Source of the term's origin and Champeon's own
   account of the philosophy, quoted in dimensions 1, 2, and 9.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models a form's baseline
submit handling and its progressively applied enhancement, the way a
web page structures the layered content, presentation, and behavior
approach, kept free of JSX and any specific framework's package so
the sample compiles as plain TypeScript. Python shows the same
conceptual split using a minimal, framework-agnostic server-side form
handler that processes a full-page submission directly, since Python
has no single dominant client-side Progressive Enhancement UI
framework the way TypeScript has browser APIs to model directly.
Swift shows the pattern using a minimal model where a baseline
behavior is defined first and an enhancement is conditionally applied
only once a capability check passes, closely analogous to how
capability-gated enhancement is reasoned about in a native context.
Java, Go, and Rust are omitted, since none has a dominant, idiomatic
UI-component framework this specifically frontend delivery pattern
maps to as directly as TypeScript and Swift do.

### TypeScript

```typescript
interface FormResult {
  submitted: boolean;
  usedEnhancement: boolean;
}

function baselineSubmit(formData: Record<string, string>): FormResult {
  console.log("performing a full page navigation submit with", formData);
  return { submitted: true, usedEnhancement: false };
}

function supportsEnhancedSubmit(): boolean {
  return typeof fetch === "function";
}

function enhancedSubmit(formData: Record<string, string>): FormResult {
  console.log("submitting asynchronously with fetch, no page reload", formData);
  return { submitted: true, usedEnhancement: true };
}

function submitForm(formData: Record<string, string>): FormResult {
  if (supportsEnhancedSubmit()) {
    return enhancedSubmit(formData);
  }
  return baselineSubmit(formData);
}

const result = submitForm({ email: "user@example.com" });
console.log("used enhancement: " + result.usedEnhancement);
```

### Python

```python
from dataclasses import dataclass


@dataclass
class FormResult:
    submitted: bool
    used_enhancement: bool


def baseline_submit(form_data: dict[str, str]) -> FormResult:
    print(f"performing a full page navigation submit with {form_data}")
    return FormResult(submitted=True, used_enhancement=False)


def handle_server_form_submission(form_data: dict[str, str]) -> FormResult:
    if not form_data.get("email"):
        raise ValueError("email is required, validated on the server regardless of the client")
    return baseline_submit(form_data)


if __name__ == "__main__":
    result = handle_server_form_submission({"email": "user@example.com"})
    print("used enhancement:", result.used_enhancement)
```

### Swift

```swift
struct FormResult {
    let submitted: Bool
    let usedEnhancement: Bool
}

func baselineSubmit(formData: [String: String]) -> FormResult {
    print("performing a baseline submit with " + String(describing: formData))
    return FormResult(submitted: true, usedEnhancement: false)
}

func supportsEnhancedSubmit() -> Bool {
    true
}

func enhancedSubmit(formData: [String: String]) -> FormResult {
    print("submitting with the enhanced, asynchronous path")
    return FormResult(submitted: true, usedEnhancement: true)
}

func submitForm(formData: [String: String]) -> FormResult {
    if supportsEnhancedSubmit() {
        return enhancedSubmit(formData: formData)
    }
    return baselineSubmit(formData: formData)
}

let result = submitForm(formData: ["email": "user@example.com"])
print("used enhancement: " + String(result.usedEnhancement))
```
