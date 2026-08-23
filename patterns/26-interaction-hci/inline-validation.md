---
name: Inline Validation
slug: inline-validation
family: 26-interaction-hci
category: Interaction and HCI
aliases: [Live Validation, Real-Time Form Validation, Field-Level Validation]
first_described: "Luke Wroblewski, with Etre, A List Apart, September 1, 2009"
maturity: established
related: [wizard]
incompatible_with: []
verified: 2026-08-23
---

# Inline Validation

## 1. Name, aliases, and lineage

Inline validation checks a form field against its rule as the person fills the
form in, and shows the result next to that field, rather than waiting until
the whole form is submitted. It is also called live validation, real-time form
validation, or field-level validation.

The canonical origin is Luke Wroblewski's study, published on A List Apart
under the title "Inline Validation in Web Forms," dated September 1, 2009. The
study's methodology is stated directly in the article: "I worked with Etre, a
London-based usability firm, to test 22 average users on six variations of a
typical web registration form" (Wroblewski, Luke, "Inline Validation in Web
Forms," A List Apart, September 1, 2009,
https://alistapart.com/article/inline-validation-in-web-forms/, verified
2026-08-23). Wroblewski's own site references the same body of work as one of
several interaction patterns for reducing form errors (Wroblewski, Luke, "How
to Reduce Errors in Forms," lukew.com, May 7, 2014,
https://www.lukew.com/ff/entry.asp?1870, verified 2026-08-23), and the two
sources are treated here as describing the same original research.

## 2. Problem and context

A form that only validates on submit forces the person to fill in every field
before learning which of them were wrong, then reconcile a wall of errors
against fields that may have scrolled off screen. GOV.UK's own design system
mitigates exactly this by requiring a linked error summary at the top of the
page with keyboard focus moved to it on submit failure (GOV.UK Design System,
"Error summary,"
https://design-system.service.gov.uk/components/error-summary/, verified
2026-08-23), an accommodation that exists specifically because reconciling a
late, disconnected wall of errors is hard.

The opposite failure is validating too early, before the person has finished
typing. The Nielsen Norman Group states this plainly: "Presenting errors too
early is a hostile pattern. It's like grading a test before the student has
had a chance to answer" (Neusesser, Tim, and Sunwall, Evan, "Error-Message
Guidelines," Nielsen Norman Group, May 14, 2023,
https://www.nngroup.com/articles/error-message-guidelines/, verified
2026-08-23). Smashing Magazine names this directly as an anti-pattern:
premature validation, showing errors when users focus on empty fields before
typing anything, creates frustration and wastes user time (Friedman, Vitaly,
"Inline Validation In Web Forms: Design Guidelines," Smashing Magazine,
September 21, 2022,
https://www.smashingmagazine.com/2022/09/inline-validation-web-forms-ux/,
verified 2026-08-23).

A purely per-field model also strains against rules that span more than one
field, such as a password confirmation matching its original, or a date input
split across day, month, and year controls. GOV.UK's error summary guidance
special-cases exactly this: for multi-field questions such as date inputs, the
summary links to the first field that contains an error, rather than treating
each sub-field independently (GOV.UK Design System, "Error summary," verified
2026-08-23).

## 3. Forces

Timeliness of feedback pulls toward validating as early as possible, so a
mistake is caught while the person's attention is still on that field rather
than several fields later. Respect for an unfinished answer pulls the other
way, since validating before a field is complete punishes normal typing speed
rather than a genuine error.

Consistency across field types is a real force too. Baymard Institute's
practical guidance ties the trigger to the nature of each field: for
format-strict fields such as ZIP codes, phone numbers, and credit cards,
validate once the input reaches the correct character length rather than on
every keystroke (Baymard Institute, "Inline Form Validation: 22 UX Guidelines
for the Perfect UI," January 9, 2024,
https://baymard.com/blog/inline-form-validation, verified 2026-08-23).

Accessibility and typing speed pull toward restraint. GOV.UK's own guidance
states this as the reason it avoids validating a field before the person has
finished entering it: this sort of validation can cause problems, especially
for users who type more slowly (GOV.UK Design System, "Validation,"
https://design-system.service.gov.uk/patterns/validation/, verified
2026-08-23).

The pattern favors catching an error close to the moment it was made, and it
sacrifices some interruption risk to do so. Getting the trigger timing right,
covered in dimension 6, is what decides whether that trade pays off or turns
into the hostile pattern the Nielsen Norman Group warns against.

## 4. Applicability and non-applicability

Baymard Institute's guidance targets the pattern at format-strict,
error-prone fields, validating once the input reaches the correct character
length for ZIP codes, phone numbers, and credit card numbers (Baymard
Institute, "Inline Form Validation," verified 2026-08-23). The Nielsen Norman
Group states the same principle more generally: consider inline, real-time
errors for error-prone interactions where users are unlikely to enter the
correct information on their first try (Neusesser and Sunwall, "Error-Message
Guidelines," verified 2026-08-23).

GOV.UK's Design System takes the strongest documented position against
defaulting to inline validation found for this entry. Its guidance states
plainly: generally speaking, avoid validating the information in a field
before the user has finished entering it, and do not validate when the user
moves away from a field, wait until they try to move to the next part of the
service instead (GOV.UK Design System, "Validation," verified 2026-08-23).
Real-time validation is added on top of that default only if user research
shows it solves more problems than it creates, per the same source, on a
government service serving a very wide population including users with lower
digital literacy and users of assistive technology.

Smashing Magazine gives a concrete non-applicability case for a specific
condition: validate empty fields on submit only, since flagging a field the
person has not yet reached, or has just cleared, as an error is not a genuine
mistake worth interrupting them for (Friedman, "Inline Validation In Web
Forms," verified 2026-08-23).

## 5. Structure

Four parts recur across every source consulted. A validation rule tied to a
specific field. A trigger event that decides when the rule runs, covered in
dimension 6. A visual indicator adjacent to the field. And an accessible
association that connects the message to the field for a screen reader user.

GOV.UK specifies the visual indicator directly: put the message in red after
the question text and hint text, and use a red border to visually connect the
message and the question it belongs to (GOV.UK Design System, "Error
message," https://design-system.service.gov.uk/components/error-message/,
verified 2026-08-23). IBM's Carbon Design System documents three visual
indicators together: a red border, an error icon indicator, and an error
message (IBM, "Text input, usage," Carbon Design System,
https://carbondesignsystem.com/components/text-input/usage/, verified
2026-08-23).

The accessible association is specified precisely by the World Wide Web
Consortium. The invalid field carries aria-describedby pointing at the id of
its error text, and aria-invalid is set to true on each invalid form control
(World Wide Web Consortium, "Providing Notifications," WAI Web Accessibility
Tutorials, https://www.w3.org/WAI/tutorials/forms/notifications/, verified
2026-08-23; WebAIM, "Usable and Accessible Form Validation and Error
Recovery," https://webaim.org/techniques/formvalidation/, verified
2026-08-23). Making the message announce automatically needs role alert on the
container it appears in, but the same W3C guide's Alert pattern warns that
screen readers do not inform users of alerts that are present on the page
before page load completes, so the container must be empty at load and filled
only when the error actually fires. aria-live set to polite is the lighter
option, since it de-emphasizes the message rather than interrupting the
person's current task the way assertive does (World Wide Web Consortium,
"Providing Notifications," verified 2026-08-23).

## 6. ASCII structure diagram

```
Person types into a field
        |
        v
Debounce timer starts, resets on each keystroke
        |
        v
Typing pauses, or the field loses focus (on blur)
        |
        v
The rule for that field runs
        |
   +----+----+
   |         |
   v         v
 Pass       Fail
   |         |
   v         v
Neutral     Error message renders next to the field
state       (aria-invalid true, linked via aria-describedby)
   |         |
   +----+----+
        |
        v
Person edits the field again
        |
        v
Was the field already marked invalid?
        |
   +----+----+
   |         |
  yes        no
   |         |
   v         v
Recheck    Wait for the next blur or pause
on every   before checking again
keystroke
(clear the
error the
instant it
is fixed)
```

## 7. Dynamics

The strongest, most independently corroborated finding across every source
consulted for this entry is an asymmetric timing rule: validate late the
first time a field is checked, then validate immediately once that field has
already been flagged invalid.

Wroblewski's original study found the timing directly. Validating after the
person leaves a field, on blur, beat both validating on every keypress and
validating before the person had typed anything at all; the last of the three
was rated worst, with a participant quote capturing the experience: it is
frustrating that you do not get the chance to put anything in the field
before it is flashing red at you (Wroblewski, "Inline Validation in Web
Forms," verified 2026-08-23).

Smashing Magazine names the asymmetry explicitly: reward early, punish late.
When users edit an erroneous field, validate immediately to confirm fixes.
However, if input was already valid, wait until they leave the field before
flagging new errors (Friedman, "Inline Validation In Web Forms," verified
2026-08-23). Baymard Institute states the same mechanism operationally,
validating primarily as users leave a field on blur, then rechecking on a
keystroke level after errors occur, to clear the message the instant it is
corrected (Baymard Institute, "Inline Form Validation," verified 2026-08-23).

React Hook Form ships this exact behavior as two named configuration options,
which is strong evidence the pattern is standard practice rather than a single
study's finding. Its default mode is onSubmit, but its onTouched mode
validates on the first blur event and, after that, on every change event
after the first blur. Its separate reValidateMode option, defaulting to
onChange, governs an already-invalid field specifically, so it is rechecked
as the person types (React Hook Form, "useForm," https://react-hook-form.com/docs/useform,
verified 2026-08-23).

## 8. Implementation variants

The lightest variant is the browser's own Constraint Validation API, requiring
no library. The Mozilla Developer Network documents a ValidityState object
exposing flags such as patternMismatch, tooLong, tooShort, rangeOverflow,
rangeUnderflow, typeMismatch, and valueMissing, alongside checkValidity,
reportValidity, and setCustomValidity methods, plus the required, minlength,
maxlength, min, max, step, and pattern HTML attributes that drive it, and the
valid and invalid CSS pseudo-classes for styling (Mozilla Developer Network,
"Client-side form validation,"
https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Form_validation,
verified 2026-08-23). MDN's own recommendation is layered: begin a form using
solid HTML features, then enhance the experience with JavaScript as needed.

A library-driven variant is common in single-page applications. React Hook
Form exposes the mode and reValidateMode options from dimension 7 directly on
its useForm hook, with its onChange mode carrying an explicit performance
warning in its own documentation (React Hook Form, "useForm," verified
2026-08-23). Formik exposes the same choice as two boolean props,
validateOnChange and validateOnBlur, both true by default, and accepts either
a synchronous validate function returning an errors object or an asynchronous
one returning a promise (Formik, "API reference,"
https://formik.org/docs/api/formik, verified 2026-08-23).

An async, server-checked variant is needed whenever a rule cannot be checked
purely on the client, such as whether a username is already taken. This
variant adds two genuine complications. The first is debouncing the trigger so
a rapid typist does not fire a request per keystroke, which the use-debounce
package documents as one of its named use cases, HTTP request debouncing to
prevent excessive server calls (xnimorz, "use-debounce," GitHub,
https://raw.githubusercontent.com/xnimorz/use-debounce/master/README.md,
verified 2026-08-23). The second is the stale-response race condition: React's
own documentation states this exactly for a search-as-you-type scenario that
is structurally identical to an async availability check, and gives the fix,
an ignore flag set inside a useEffect cleanup function so a response that
arrives after a newer request has been sent is discarded rather than applied
(React, "You Might Not Need an Effect," https://react.dev/learn/you-might-not-need-an-effect,
verified 2026-08-23). The lower-level primitive for actually canceling, rather
than merely ignoring, a superseded request is the AbortController interface,
whose abort method aborts an asynchronous operation before it has completed
(Mozilla Developer Network, "AbortController,"
https://developer.mozilla.org/en-US/docs/Web/API/AbortController, verified
2026-08-23).

## 9. Known production uses

GOV.UK's Design System is the clearest documented production case, and
notably a case against defaulting to inline, real-time validation. Its
guidance states this approach has been used on a number of services over an
extended period, explicitly naming the passport renewal service, while the
team continues to seek additional research on client-side validation needs
and screen reader compatibility with non-required form fields (GOV.UK Design
System, "Validation," verified 2026-08-23). This is a large, accessibility-led
government service that deliberately chose validate-on-submit-only for the
reasons in dimension 4.

IBM's Carbon Design System documents both options for its TextInput component
and leaves the choice to the implementer: real-time validation helps
simplify the process and keep data clean, otherwise validate the text input
data when the user submits the associated form (IBM, "Text input, usage,"
verified 2026-08-23). Carbon is a widely adopted enterprise design system
underlying a large number of production business applications, so its stated
default of leaving the choice open, backed by the three-part visual indicator
from dimension 5, represents real, shipped guidance rather than a theoretical
position.

## 10. Consequences

Positive. Wroblewski's Etre study is the strongest quantified source found for
this entry. The best-performing inline-validation variant against a
no-inline-validation control produced a 22 percent increase in success rates,
a 22 percent decrease in errors made, a 31 percent increase in satisfaction
rating, a 42 percent decrease in completion times, and a 47 percent decrease
in the number of eye fixations (Wroblewski, "Inline Validation in Web Forms,"
verified 2026-08-23).

Negative. Premature validation, flagging a field before the person has
finished, is directly named as a hostile pattern by the Nielsen Norman Group
and as an explicit anti-pattern by Smashing Magazine, and Wroblewski's own
study drew a direct participant quote describing the frustration of being
flagged before finishing typing. Vague, unhelpful messages compound the
problem; the Nielsen Norman Group states that generic messages such as an
error occurred lack context, and Smashing Magazine separately names vague
error messages as a distinct failure, particularly with interdependent fields
such as date inputs. GOV.UK's stated reason for avoiding real-time validation
by default is that it can disadvantage users who type more slowly and
behaves inconsistently across browsers and assistive technology. Wroblewski's
own study also found that inline validation goes unnoticed on easy, early
fields: only 30 to 50 percent of participants saw validation messages on the
first half of a typical form, compared with 80 to 100 percent on the harder
second half, meaning the pattern's benefit concentrates almost entirely on
fields that are already error-prone.

## 11. Failure modes and misuse

Premature validation is the most consistently documented failure mode across
this entry's sources, covered in full in dimensions 2 and 10. It is worth
restating as a misuse pattern specifically: a field going red the instant a
person types a single character, before there was ever a chance to finish the
answer, is not a caught error, it is a false alarm.

Vague, unhelpful messages are the second failure mode. The Nielsen Norman
Group states directly that phrasing should never blame users or imply they
are doing something wrong, using words such as invalid, illegal, or
incorrect, with the stated reasoning that the proper usage of any system lies
with its creators and not with the system's users (Neusesser and Sunwall,
"Error-Message Guidelines," verified 2026-08-23). A message with no
correction guidance, a bare indicator with no explanation of how to fix the
problem, fails the same requirement, since both GOV.UK and the World Wide Web
Consortium's tutorial call for an indication of how to correct the mistake,
not only that one exists.

Disabling copy-paste into a field, or enforcing an overly rigid input format,
is named directly by Smashing Magazine as a misuse: this practice traps users
in frustrating loops, reducing satisfaction and increasing abandonment
(Friedman, "Inline Validation In Web Forms," verified 2026-08-23), with the
recommendation to support multiple valid input formats rather than a single
rigid pattern.

An auto-disappearing error message is a misuse the World Wide Web
Consortium's own accessibility guidance names directly: avoid designing
alerts that disappear automatically, since an alert that disappears too
quickly can lead to failure to meet WCAG 2.0 success criterion 2.2.3 (World
Wide Web Consortium, "Alert Pattern," WAI-ARIA Authoring Practices Guide,
https://www.w3.org/WAI/ARIA/apg/patterns/alert/, verified 2026-08-23).

## 12. Trade-off matrix

| Dimension | Inline, per-field, real-time | Submit-time, all at once | Hybrid, inline format checks plus submit-time cross-field checks |
|---|---|---|---|
| Perceived friction | Lowest when timed correctly, per Wroblewski's on-blur finding and Baymard's per-field-type triggers | Highest, GOV.UK accepts this deliberately to avoid punishing slower typists, at the cost of surprises only discovered at submit | Balanced, GOV.UK's own error summary paired with inline messages is effectively this shape |
| Cognitive load | Low if debounced or on-blur, high if validated on every keystroke before typing finishes, per Wroblewski's worst-rated condition | Can spike if many fields fail at once, which is why GOV.UK mandates focus-move to a linked error summary | Moderate, one summary to scan but each item is pre-linked to its field |
| Cross-field rule support | Weak by construction, a per-field model cannot natively express a rule spanning two fields without deliberate extra wiring | Natural fit, cross-field and server-side rules evaluate together at one gate | Strong, GOV.UK explicitly routes multi-field questions to the submit-time summary path rather than pure per-field inline |
| Accessibility risk | Higher without care, since frequent aria-live announcements interrupt more than they help, per the W3C's own warning against overusing alerts | Lower, a single well-defined moment to move focus and announce | Moderate, needs both a restrained live-region strategy and the alert-on-submit summary pattern |

## 13. Related and incompatible patterns

A wizard, which splits a large form across several pages, typically must
decide per step whether its next control is enabled, and the decision usually
depends on whether every field on the current step currently passes
validation. That decision is built on the same rule-plus-trigger mechanism
documented here, applied to gate a step transition instead of, or in addition
to, a final form submission. No source consulted for this entry states this
connection to a wizard directly, so it is reported here as a reasonable
structural inference rather than a sourced claim.

No source consulted relates progressive disclosure or a command palette to
inline validation, so no relationship is claimed for either here.

## 14. Refactoring path in and out

To introduce inline validation into a form that only validates on submit,
first pick the trigger per field type rather than one blanket rule.
Format-strict fields validate at their correct character length per Baymard's
guidance, and most other fields validate on blur per Wroblewski's and Smashing
Magazine's shared timing finding. Wire the accessible association from
dimension 5, aria-invalid and aria-describedby, at the same time the visual
indicator is added, never as an afterthought, since retrofitting
accessibility onto an already-shipped validation UI is far more error-prone
than building it in from the first commit. Add the reward-early, punish-late
behavior from dimension 7 last, once the basic on-blur trigger is proven
correct.

To remove inline validation from a form where it has become a source of
premature or noisy interruptions, per the failure modes in dimension 11, the
safest first step is switching the trigger from onChange or every keystroke
to onBlur or on submit only, per GOV.UK's stated default, before removing the
mechanism entirely. If user research (per GOV.UK's own bar for adding
real-time validation in the first place) does not show it solving more
problems than it creates, remove it and fall back to submit-time validation
with a linked error summary.

## 15. Testing and verification

Debounced or delayed triggers make a test suite unpredictable unless timers
are controlled explicitly. Testing Library's own guidance states this
directly: when code uses timers such as setTimeout, setInterval,
clearTimeout, and clearInterval, tests may become unpredictable, slow, and
flaky (Testing Library, "Using Fake Timers,"
https://testing-library.com/docs/using-fake-timers/, verified 2026-08-23). The
documented setup installs fake timers, and the documented cleanup runs any
pending timers before switching back to real timers, since switching to real
timers without progressing the fake ones first leaves a scheduled task
unexecuted and produces unexpected behavior. The same guide names a specific,
documented gotcha for this pattern: combining fake timers with user-event can
cause test timeouts, solved through the advanceTimers option.

Asserting the accessible association itself, that an error message is
actually wired to its field through aria-describedby and not merely placed
nearby visually, is supported directly by jest-dom's toHaveAccessibleDescription
matcher, which supports an exact string, a regular expression, or a partial
match (Testing Library, "jest-dom," https://github.com/testing-library/jest-dom,
verified 2026-08-23).

The composite assertions this supports are, first, that the correct error
message renders for a given invalid input, second, that the message clears
once the field is corrected, following the reward-early behavior from
dimension 7, and third, that the message is genuinely reachable by assistive
technology through its accessible-name or accessible-description wiring, not
only visible on screen.

## 16. Observability signals

No source consulted supplied a canonical, named production dashboard or
methodology specific to inline validation, so this dimension is built as
reasoned synthesis on top of the sourced material in earlier dimensions,
labeled as such rather than presented as established fact.

Baymard Institute's own measurement practice, that 31 percent of the
e-commerce sites it studied lacked inline validation entirely and 4 percent
implemented it incorrectly (Baymard Institute, "Inline Form Validation,"
verified 2026-08-23), implies the same kind of per-field auditing a team
could run on its own product: tracking, per field, how often a validation
rule fires, how often the resulting message is dismissed or ignored, echoing
Wroblewski's own finding that a large share of participants never even
noticed validation on easy fields, and how long it takes a person to move
from an error state to a corrected, valid one. The underlying event to log,
per dimension 15, is the same boolean invalid-to-valid transition a test
suite would assert against.

## 17. Security and privacy implications

The OWASP Input Validation Cheat Sheet states the governing principle without
qualification. Input validation must be implemented on the server side before
any data is processed by an application's functions, as any JavaScript-based
input validation performed on the client side can be circumvented by an
attacker who disables JavaScript or uses a web proxy (OWASP, "Input
Validation Cheat Sheet,"
https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html,
verified 2026-08-23). The same source recommends the dual-layer model this
pattern sits inside: client-side validation for the experience described
throughout this entry, and server-side validation for security, using
each for its own strength.

The Mozilla Developer Network states the identical conclusion independently:
client-side validation should not be considered an exhaustive security
measure, and a form's submitted data should always be validated on the server
as well as the client, because client-side validation is too easy to bypass
(Mozilla Developer Network, "Client-side form validation," verified
2026-08-23). Its own boxed warning is direct: never trust data passed to a
server from the client, since a malicious user can alter the network request
even when the client-side form is validating correctly.

Applied to this pattern specifically, an inline validation error message, an
aria-invalid flag, and a disabled submit button are all UX conveniences the
person's own browser fully controls, and none of them are a substitute for an
independent server-side check of the same rule before the data is trusted or
stored.

## 18. References

1. Wroblewski, Luke, "Inline Validation in Web Forms," A List Apart,
   September 1, 2009,
   https://alistapart.com/article/inline-validation-in-web-forms/, verified
   2026-08-23.
2. Wroblewski, Luke, "How to Reduce Errors in Forms," lukew.com, May 7, 2014,
   https://www.lukew.com/ff/entry.asp?1870, verified 2026-08-23.
3. GOV.UK Design System, "Error summary,"
   https://design-system.service.gov.uk/components/error-summary/, verified
   2026-08-23.
4. GOV.UK Design System, "Validation,"
   https://design-system.service.gov.uk/patterns/validation/, verified
   2026-08-23.
5. GOV.UK Design System, "Error message,"
   https://design-system.service.gov.uk/components/error-message/, verified
   2026-08-23.
6. Neusesser, Tim, and Sunwall, Evan, "Error-Message Guidelines," Nielsen
   Norman Group, May 14, 2023,
   https://www.nngroup.com/articles/error-message-guidelines/, verified
   2026-08-23.
7. Friedman, Vitaly, "Inline Validation In Web Forms: Design Guidelines,"
   Smashing Magazine, September 21, 2022,
   https://www.smashingmagazine.com/2022/09/inline-validation-web-forms-ux/,
   verified 2026-08-23.
8. Baymard Institute, "Inline Form Validation: 22 UX Guidelines for the
   Perfect UI," January 9, 2024, https://baymard.com/blog/inline-form-validation,
   verified 2026-08-23.
9. IBM, "Text input, usage," Carbon Design System,
   https://carbondesignsystem.com/components/text-input/usage/, verified
   2026-08-23.
10. World Wide Web Consortium, "Providing Notifications," WAI Web
    Accessibility Tutorials,
    https://www.w3.org/WAI/tutorials/forms/notifications/, verified
    2026-08-23.
11. WebAIM, "Usable and Accessible Form Validation and Error Recovery,"
    https://webaim.org/techniques/formvalidation/, verified 2026-08-23.
12. World Wide Web Consortium, "Alert Pattern," WAI-ARIA Authoring Practices
    Guide, https://www.w3.org/WAI/ARIA/apg/patterns/alert/, verified
    2026-08-23.
13. Mozilla Developer Network, "Client-side form validation,"
    https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Form_validation,
    verified 2026-08-23.
14. React Hook Form, "useForm," https://react-hook-form.com/docs/useform,
    verified 2026-08-23.
15. Formik, "API reference," https://formik.org/docs/api/formik, verified
    2026-08-23.
16. xnimorz, "use-debounce," GitHub,
    https://raw.githubusercontent.com/xnimorz/use-debounce/master/README.md,
    verified 2026-08-23.
17. React, "You Might Not Need an Effect,"
    https://react.dev/learn/you-might-not-need-an-effect, verified
    2026-08-23.
18. Mozilla Developer Network, "AbortController,"
    https://developer.mozilla.org/en-US/docs/Web/API/AbortController,
    verified 2026-08-23.
19. Testing Library, "Using Fake Timers,"
    https://testing-library.com/docs/using-fake-timers/, verified
    2026-08-23.
20. Testing Library, "jest-dom," GitHub,
    https://github.com/testing-library/jest-dom, verified 2026-08-23.
21. OWASP, "Input Validation Cheat Sheet,"
    https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html,
    verified 2026-08-23.

**Evidence grade.** high

**Most solid findings.** Wroblewski's original timing study is directly read
and its figures are internally consistent. The reward-early, punish-late
timing asymmetry is corroborated independently across three sources,
Wroblewski, Smashing Magazine, and Baymard, plus confirmed as shipped,
documented behavior in React Hook Form's own API. GOV.UK's explicit
against-the-default position is a primary source read directly.

**Unverified or unclear.** No canonical, named source was found specifically
documenting an async username-availability check as a single, complete
pattern; the building blocks, debouncing and race-condition handling, are each
independently sourced but not united in one citable reference. This entry's
wizard connection in dimension 13 is this entry's own structural inference,
not a sourced claim. Observability data specific to inline validation is
thin; dimension 16 is reasoned synthesis rather than direct citation.

## Code

TypeScript, Python, and Go implementations of a per-field validator following
the reward-early, punish-late timing from dimension 7: a field validates on
blur the first time, then revalidates on every change once it has already
been marked invalid, and exposes the accessible attributes from dimension 5.

```typescript
type Validator = (value: string) => string | null;

interface FieldState {
  value: string;
  error: string | null;
  wasBlurred: boolean;
}

class ValidatedField {
  private state: FieldState = { value: "", error: null, wasBlurred: false };
  private readonly validate: Validator;
  private readonly fieldId: string;

  constructor(fieldId: string, validate: Validator) {
    this.fieldId = fieldId;
    this.validate = validate;
  }

  onChange(value: string): FieldState {
    this.state.value = value;
    if (this.state.error !== null) {
      this.state.error = this.validate(value);
    }
    return this.state;
  }

  onBlur(): FieldState {
    this.state.wasBlurred = true;
    this.state.error = this.validate(this.state.value);
    return this.state;
  }

  ariaAttributes(): Record<string, string> {
    const attrs: Record<string, string> = {
      "aria-invalid": String(this.state.error !== null),
    };
    if (this.state.error !== null) {
      attrs["aria-describedby"] = this.fieldId + "-error";
    }
    return attrs;
  }

  currentState(): FieldState {
    return this.state;
  }
}

function requiredZip(value: string): string | null {
  if (value.length < 5) {
    return null;
  }
  return /^[0-9]{5}$/.test(value) ? null : "Enter a five digit ZIP code";
}
```

```python
from dataclasses import dataclass
from typing import Callable, Optional


Validator = Callable[[str], Optional[str]]


@dataclass
class FieldState:
    value: str = ""
    error: Optional[str] = None
    was_blurred: bool = False


class ValidatedField:
    def __init__(self, field_id: str, validate: Validator) -> None:
        self._field_id = field_id
        self._validate = validate
        self._state = FieldState()

    def on_change(self, value: str) -> FieldState:
        self._state.value = value
        if self._state.error is not None:
            self._state.error = self._validate(value)
        return self._state

    def on_blur(self) -> FieldState:
        self._state.was_blurred = True
        self._state.error = self._validate(self._state.value)
        return self._state

    def aria_attributes(self) -> dict[str, str]:
        attrs = {"aria-invalid": str(self._state.error is not None).lower()}
        if self._state.error is not None:
            attrs["aria-describedby"] = self._field_id + "-error"
        return attrs

    def current_state(self) -> FieldState:
        return self._state


def required_zip(value: str) -> Optional[str]:
    if len(value) < 5:
        return None
    return None if value.isdigit() and len(value) == 5 else "Enter a five digit ZIP code"
```

```go
package validation

import "regexp"

type Validator func(value string) *string

type FieldState struct {
	Value      string
	Error      *string
	WasBlurred bool
}

type ValidatedField struct {
	fieldID  string
	validate Validator
	state    FieldState
}

func NewValidatedField(fieldID string, validate Validator) *ValidatedField {
	return &ValidatedField{fieldID: fieldID, validate: validate}
}

func (f *ValidatedField) OnChange(value string) FieldState {
	f.state.Value = value
	if f.state.Error != nil {
		f.state.Error = f.validate(value)
	}
	return f.state
}

func (f *ValidatedField) OnBlur() FieldState {
	f.state.WasBlurred = true
	f.state.Error = f.validate(f.state.Value)
	return f.state
}

func (f *ValidatedField) AriaAttributes() map[string]string {
	invalid := "false"
	if f.state.Error != nil {
		invalid = "true"
	}
	attrs := map[string]string{"aria-invalid": invalid}
	if f.state.Error != nil {
		attrs["aria-describedby"] = f.fieldID + "-error"
	}
	return attrs
}

func (f *ValidatedField) CurrentState() FieldState {
	return f.state
}

var zipPattern = regexp.MustCompile("^[0-9]{5}$")

func RequiredZip(value string) *string {
	if len(value) < 5 {
		return nil
	}
	if zipPattern.MatchString(value) {
		return nil
	}
	msg := "Enter a five digit ZIP code"
	return &msg
}
```
