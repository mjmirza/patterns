---
name: Output Encoding
slug: output-encoding
family: 15-security
category: Security
aliases: [Output Escaping, Contextual Escaping, Context-Sensitive Escaping, HTML Escaping]
first_described: "OWASP Cross Site Scripting Prevention Cheat Sheet"
maturity: established
related: [input-validation, content-security-policy, complete-mediation, secure-by-default, parameterized-query]
incompatible_with: [raw-html-rendering, string-concatenated-code, interceptor-only-escaping]
verified: 2026-08-02
---

# Output Encoding

## 1. Name, aliases, and lineage

The canonical name in this entry is Output Encoding. In web security practice
the same pattern is often called output escaping, contextual escaping,
context-sensitive escaping, HTML escaping, or template autoescaping. OWASP uses
the name Output Encoding in its Cross Site Scripting Prevention Cheat Sheet and
places it inside the XSS defense guidance, with separate rules for HTML text,
HTML attributes, JavaScript, CSS, and URL contexts
([https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
verified 2026-08-02).

The lineage is older than any one library. HTML parsers, JavaScript parsers,
CSS parsers, URL parsers, XML parsers, shell parsers, and SQL parsers all assign
special meaning to selected characters. Security work turned that parsing fact
into a software pattern. Before untrusted data crosses from an internal value
domain into an output grammar, transform the data into a representation that
the next parser treats as data rather than syntax. The WHATWG HTML Standard
defines named character references and numeric character references as part of
the HTML syntax, which is the browser-side substrate behind common HTML entity
escaping
([https://html.spec.whatwg.org/multipage/named-characters.html](https://html.spec.whatwg.org/multipage/named-characters.html),
verified 2026-08-02).

The term escaping is shorter, but it hides one of the pattern's hard edges.
There is no single escape operation. The target grammar decides the operation.
OWASP states that browsers parse HTML, JavaScript, URLs, and CSS differently,
and that the wrong method can create weakness or break behavior
([https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
verified 2026-08-02). This entry uses Output Encoding for the general pattern,
and uses escaping for a concrete operation such as HTML text escaping.

Output Encoding is not input validation. Input validation decides whether a
value is allowed for a business operation. Output Encoding decides how an
allowed value must be represented for a parser. Output Encoding is not HTML
sanitization. Sanitization accepts a markup-bearing input and removes or rewrites
unsafe markup. OWASP distinguishes the two, recommending sanitization when users
need to author HTML because plain output encoding would display the markup as
text
([https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
verified 2026-08-02). Output Encoding is also not Content Security Policy. CSP
is a browser policy layer; encoding changes bytes before a parser gives them
syntax power.

Engineering judgement. Treat this pattern as a boundary pattern, not as a
string helper. Its correct name in a code review is "encode for the next
grammar." A call named `escape` with no target context in the name is usually a
weak abstraction.

## 2. Problem and context

A program has data that may contain characters with special meaning in the
output grammar. The program wants to display, serialize, log, or embed that data
without granting those characters grammar authority. The defect appears when
the program concatenates the value into the output and lets the downstream
parser decide where data ends and syntax begins.

The browser case is the best known. A product renders a profile name, comment,
search query, error message, file name, tenant name, or markdown title into an
HTML page. The value is legitimate data. It can contain angle brackets, quotes,
ampersands, slashes, parentheses, backticks, line breaks, or Unicode
punctuation. If the value is written into HTML text without HTML escaping, a
browser can interpret some bytes as tags or entity starts. If it is written into
an attribute without attribute encoding and quoting, it can change the attribute
or start another one. If it is written into inline JavaScript, CSS, or a URL
component, each target grammar has different special characters. OWASP names
these separate contexts and warns that some contexts are unsafe for dynamic
variables at all
([https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
verified 2026-08-02).

The same problem appears outside browsers. XML needs entity escaping. CSV needs
quoting rules. Logs need record-boundary handling. Shell command strings need a
different treatment again, although the better pattern there is to pass an
argument vector rather than encode a shell string. SQL is the cautionary
example. Manual escaping was historically attempted, but parameterized queries
replace it for values because the database protocol can carry data separately
from syntax. The Query Parameterization entry covers that separate pattern.

The context that makes Output Encoding the right pattern has four parts. First,
there is a known sink, such as HTML text, an HTML attribute, a JavaScript string
literal, a URL query component, a JSON response, XML text, or log text. Second,
the value is meant to remain data in that sink. Third, the program can choose an
encoder that is specific to the sink. Fourth, the encoded representation is
written at the last responsible moment, close to the output boundary, so the
code does not accidentally reuse an HTML-encoded value in a URL or a
JavaScript-encoded value in HTML.

The pattern is needed even when the data was validated on input. A valid last
name can contain an apostrophe. A valid company name can contain an ampersand. A
valid search term can contain angle brackets because a user searched for a tag.
Input validation that rejects such values to make rendering easier is a product
bug wearing a security label. Encode the value for the place where it is
rendered.

## 3. Forces

Engineering judgement. Output Encoding favours parser safety, local reasoning,
and framework defaults. It sacrifices some readability in templates, can create
bugs when applied too early, and becomes hard when one value is nested through
several grammars.

- **Latency.** Usually low cost. Encoding is linear in the number of output
  bytes. It can matter on hot template paths that render large tables, feeds, or
  logs, so measured allocations and streaming behavior still matter.
- **Coupling.** Favoured when the encoder is selected by the sink. A template
  engine can bind HTML text nodes, attribute values, and JavaScript contexts to
  different encoders. Sacrificed when business objects carry pre-encoded
  strings, because those objects become coupled to one output grammar.
- **Consistency.** Favoured by centralized template autoescaping and typed safe
  strings. Sacrificed by ad hoc calls in controllers, view models, and helper
  methods.
- **Operability.** Favoured because encoded output gives fewer exploitable
  parser transitions. Sacrificed when an incident responder cannot tell whether
  a value was encoded, double encoded, sanitized, or intentionally rendered as
  trusted markup.
- **Cost.** Low when the framework already autoescapes. Higher in legacy pages
  that mix HTML, inline scripts, inline styles, and string-built fragments.
- **Team topology.** Favoured when a platform team can provide safe template
  primitives and ban raw sinks. Sacrificed when many feature teams own different
  rendering stacks and no one owns the shared sink inventory.
- **Cognitive load.** Sacrificed. Engineers must know which grammar they are
  entering, which contexts are safe, and which framework escape hatches bypass
  the default.
- **Correctness.** Mixed. Encoding preserves data while making it safe for the
  parser. Double encoding can show users artifacts such as `&amp;lt;` instead of
  the intended text.

The hard trade is timing. Encoding too late can miss a sink. Encoding too early
can freeze a value into the wrong grammar. Good implementations make the sink
choose the encoder.

## 4. Applicability and non-applicability

Reach for Output Encoding when the following hold.

- Untrusted or mixed-trust data is inserted into HTML text, a quoted HTML
  attribute, a JavaScript quoted data value, a CSS property value, a URL query
  component, XML text, JSON embedded in HTML, CSV, logs, or another parseable
  output.
- The value should be displayed or transported as data, not interpreted as
  markup, script, style, a selector, a tag name, an attribute name, a protocol,
  a file path, or a command.
- The output sink is known at the call site or known by the template compiler.
- A framework autoescaping layer exists and its escape hatches are reviewable.
  Django documents automatic HTML escaping for variables in templates
  ([https://docs.djangoproject.com/en/5.2/ref/templates/language/#automatic-html-escaping](https://docs.djangoproject.com/en/5.2/ref/templates/language/#automatic-html-escaping),
  verified 2026-08-02). Jinja documents configurable autoescaping for HTML and
  XML templates
  ([https://jinja.palletsprojects.com/en/stable/templates/#html-escaping](https://jinja.palletsprojects.com/en/stable/templates/#html-escaping),
  verified 2026-08-02).
- A typed safe-value mechanism can mark values already proven safe for one
  specific grammar, and that marker is not a plain string alias.
- Legacy code is being migrated away from string-built markup. Output Encoding
  can be introduced at the sink while the data model remains unchanged.

Non-applicability list. Do NOT reach for Output Encoding in these cases.

- **The user is meant to author HTML.** Encoding will display tags as text and
  break the feature. Use HTML sanitization with a positive policy, then render
  the sanitized result through a trusted-markup type. OWASP describes
  sanitization as the route for user-authored HTML
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
  verified 2026-08-02).
- **The value controls a tag name, attribute name, event handler name, CSS
  selector, script block body, style block body, or URL scheme.** OWASP lists
  several dangerous contexts where variables should not be placed because
  encoding is not a complete defense
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
  verified 2026-08-02).
- **The target grammar supports data binding or parameters.** Use the parameter
  facility. SQL values belong in prepared statement parameters, not escaped SQL
  text. Shell commands should receive an argument vector instead of a
  shell-escaped string.
- **The value is already encoded for a different grammar.** HTML encoding does
  not make a value safe inside JavaScript, and URL encoding does not make the
  full `href` attribute safe after concatenation. Reuse the raw value and encode
  for the new sink.
- **The encoder would run in an HTTP interceptor after rendering.** OWASP warns
  that interceptor approaches can choose the wrong context, break rendering by
  double encoding, miss DOM-based XSS, and miss data outside the application
  response path
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
  verified 2026-08-02).
- **The output is a binary protocol with length-delimited fields.** Do not turn
  binary data into escaped text unless the protocol demands text. Preserve the
  binary protocol's data boundary.
- **The goal is authorization, secrecy, or integrity.** Encoding does not decide
  who may see data, does not encrypt it, and does not sign it.
- **The application cannot identify the sink.** A generic `safeString` helper is
  not enough. First inventory sinks, then assign encoders.

## 5. Structure

The participants are named by their security role.

- **Raw value.** The internal value before it crosses an output boundary. It may
  be user supplied, partner supplied, database stored, computed, or translated.
  It should remain unencoded inside domain code.
- **Trust decision.** The earlier validation, authorization, and sanitization
  work that decides whether the raw value may be shown at all. Output Encoding
  does not replace this participant.
- **Output context.** The exact grammar position that will receive the value.
  Examples include HTML text node, quoted HTML attribute value, URL query
  parameter, JavaScript string literal, CSS property value, XML text, JSON
  string, and log field.
- **Context encoder.** The function, template compiler, framework renderer, or
  typed sink that maps raw value characters to a representation safe for that
  output context.
- **Encoded token stream.** The resulting text that enters the downstream
  parser. It is safe only for the context that created it.
- **Parser.** The browser, JavaScript engine, CSS parser, URL parser, XML
  parser, log processor, CSV reader, or other consumer that assigns grammar
  meaning.
- **Escape hatch.** Any API that bypasses the context encoder, such as React's
  `dangerouslySetInnerHTML`, Angular's trust bypass APIs, Jinja's `safe` marker,
  or a template helper that returns trusted markup. React documents
  `dangerouslySetInnerHTML` as raw HTML insertion and warns about XSS risk for
  untrusted HTML
  ([https://react.dev/reference/react-dom/components/common#dangerously-setting-the-inner-html](https://react.dev/reference/react-dom/components/common#dangerously-setting-the-inner-html),
  verified 2026-08-02). Angular documents security contexts and explicit trust
  bypass APIs
  ([https://angular.dev/best-practices/security](https://angular.dev/best-practices/security),
  verified 2026-08-02).

Relationships. The rendering layer receives a raw value and a known output
context. The context selects the encoder. The encoded token stream is sent to
the parser. Escape hatches require a separate trust decision and audit trail.
Safe-value types should include the target context in the type name, such as
`SafeHtml`, because safety is not portable across grammars.

## 6. ASCII structure diagram

```text
  +-------------+      allowed?       +----------------+
  |  Raw value  | ------------------> | Trust decision |
  +-------------+                     +----------------+
          |                                   |
          | raw data                          | permit display
          v                                   v
  +----------------+     chooses      +------------------+
  | Output context | ---------------> | Context encoder  |
  | HTML text      |                  | htmlTextEncode   |
  | HTML attr      |                  | attrEncode       |
  | JS string      |                  | jsStringEncode   |
  | URL component  |                  | urlComponentEnc  |
  +----------------+                  +------------------+
                                               |
                                               | encoded text
                                               v
                                      +------------------+
                                      | Encoded token    |
                                      | stream           |
                                      +------------------+
                                               |
                                               | parsed by
                                               v
                                      +------------------+
                                      | Browser, XML,    |
                                      | JSON, log parser |
                                      +------------------+

  Escape hatch path:

  +-------------+      separate review       +------------------+
  | Raw markup  | -------------------------> | Sanitizer or     |
  +-------------+                            | trusted producer |
                                             +------------------+
                                                      |
                                                      v
                                             +------------------+
                                             | SafeHtml only    |
                                             +------------------+
```

## 7. Dynamics

At runtime the pattern has a short path when used well. The renderer does not
ask the caller to pre-escape. It knows the sink and applies the right encoder at
the point where bytes are emitted.

```text
Controller       Template compiler      Encoder table          Browser
    |                    |                    |                    |
    | raw view model     |                    |                    |
    |------------------->|                    |                    |
    |                    | locate sink        |                    |
    |                    | "HTML text"        |                    |
    |                    |------------------->|                    |
    |                    | html text encoder  |                    |
    |                    |<-------------------|                    |
    |                    | encode raw value   |                    |
    |                    |------------------->|                    |
    |                    | encoded token      |                    |
    |                    |<-------------------|                    |
    |                    | emit response      |                    |
    |                    |--------------------------------------->|
    |                    |                    | parse as text      |
    |                    |                    |<-------------------|

Nested URL in an HTML attribute:

Controller       URL builder            Attr encoder           Browser
    |                    |                    |                    |
    | raw query value    |                    |                    |
    |------------------->|                    |                    |
    |                    | percent-encode     |                    |
    |                    | query component    |                    |
    |                    |------------------->|                    |
    |                    | URL with query     |                    |
    |                    |<-------------------|                    |
    |                    | HTML-attribute     |                    |
    |                    | encode full URL    |                    |
    |                    |------------------->|                    |
    |                    | attr value         |                    |
    |                    |<-------------------|                    |
    |                    |                    | parse attribute    |
    |                    |                    | then parse URL     |
```

The second flow shows the source of many bugs. A URL component is encoded for
the URL grammar first. The full URL is then encoded for the HTML attribute
grammar. OWASP calls out this ordering for URLs placed in attributes
([https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
verified 2026-08-02).

Dynamics also include escape hatches. When a caller supplies trusted markup,
the renderer must require a distinct type or API. If raw strings and trusted
markup share the same path, reviewers cannot see whether a value was encoded,
sanitized, or waved through.

## 8. Implementation variants

**Template autoescaping.** The template engine selects the encoder from the
syntax tree. This is the strongest everyday variant because the sink is visible
to the compiler or renderer. Django autoescapes template variables by default
for HTML output
([https://docs.djangoproject.com/en/5.2/ref/templates/language/#automatic-html-escaping](https://docs.djangoproject.com/en/5.2/ref/templates/language/#automatic-html-escaping),
verified 2026-08-02). Go's `html/template` package states that it adds escaping
pipeline stages based on the HTML, CSS, JavaScript, and URI context
([https://pkg.go.dev/html/template](https://pkg.go.dev/html/template),
verified 2026-08-02).

**Typed safe values.** A framework may represent trusted output as a special
type. Go `html/template` exposes typed strings such as `template.HTML` and
`template.URL` for content already known to be safe for a context
([https://pkg.go.dev/html/template](https://pkg.go.dev/html/template),
verified 2026-08-02). This variant gives reviewers a visible marker. The cost
is that any conversion into the trusted type becomes security-sensitive.

**Manual sink functions.** Small libraries expose functions such as
`htmlText`, `htmlAttr`, `jsString`, and `urlComponent`. This variant fits small
programs and non-template outputs. Its weakness is that the caller must pick
the context, so code review must find every sink.

```typescript
type HtmlText = string & { readonly kind: unique symbol };
type HtmlAttr = string & { readonly kind: unique symbol };

function htmlText(value: string): HtmlText {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;") as HtmlText;
}

function htmlAttr(value: string): HtmlAttr {
  return htmlText(value)
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#x27;") as HtmlAttr;
}

function link(label: string, query: string): string {
  const href = "/search?q=" + encodeURIComponent(query);
  return `<a href="${htmlAttr(href)}">${htmlText(label)}</a>`;
}

console.log(link("Find <tags>", "a&b=c"));
```

**Safe DOM sinks.** Client code can use APIs that assign text rather than HTML.
OWASP lists `textContent`, `insertAdjacentText`, `createTextNode`, and form
field `value` as safe sinks for data display
([https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
verified 2026-08-02). This variant removes manual encoding from the caller and
lets the browser create the right text node.

```python
from html import escape
from urllib.parse import urlencode


class Html(str):
    pass


def text(value: str) -> Html:
    return Html(escape(value, quote=False))


def attr(value: str) -> Html:
    return Html(escape(value, quote=True))


def result_link(label: str, query: str) -> Html:
    url = "/search?" + urlencode({"q": query})
    return Html(f'<a href="{attr(url)}">{text(label)}</a>')


if __name__ == "__main__":
    print(result_link("Find <tags>", "a&b=c"))
```

**Contextual compilation.** A template compiler rewrites pipelines after parsing
the template, so the same expression receives a different encoder depending on
where it appears. Go `html/template` documents this contextual model
([https://pkg.go.dev/html/template](https://pkg.go.dev/html/template),
verified 2026-08-02). It works best when templates are valid and can be parsed
as a whole.

```go
package main

import (
	"html/template"
	"os"
)

type View struct {
	Label string
	Query string
}

func main() {
	t := template.Must(template.New("page").Parse(
		`<a href="/search?q={{.Query}}">{{.Label}}</a>`))
	view := View{Label: "Find <tags>", Query: "a&b=c"}
	if err := t.Execute(os.Stdout, view); err != nil {
		panic(err)
	}
}
```

**Late boundary encoding.** Services keep raw strings in storage and encode
only when writing an output. This variant avoids double encoding and keeps one
stored value usable in HTML, JSON, email, CSV, and logs. The cost is that every
output boundary needs coverage.

**Encoded-at-rest strings.** Some legacy systems store HTML-escaped text in the
database. This reduces work at render time but creates long-lived ambiguity.
The stored value is no longer raw data, search and comparison can change, and
reusing it in a non-HTML context can be wrong. Engineering judgement. Prefer
raw-at-rest plus sink encoding unless a migration cannot be funded yet.

**Sanitize then trust.** Rich text editors need sanitized markup, not escaped
markup. The sanitizer produces a trusted-markup value for one context. The
renderer still must keep that value out of JavaScript strings, URL components,
and other grammars.

## 9. Known production uses

**React DOM, JSX child text and the raw HTML escape hatch.** React documents
`children` as content inside built-in browser components and documents
`dangerouslySetInnerHTML` as assigning a raw HTML string to the DOM `innerHTML`
property, with an XSS warning for untrusted HTML
([https://react.dev/reference/react-dom/components/common#dangerously-setting-the-inner-html](https://react.dev/reference/react-dom/components/common#dangerously-setting-the-inner-html),
verified 2026-08-02). The named production use is React DOM's default rendering
model for text children, paired with a deliberately named raw HTML API.

**Django template engine.** Django documents automatic HTML escaping for
template variables and describes escaping of characters such as ampersand,
quotes, and angle brackets in variable output
([https://docs.djangoproject.com/en/5.2/ref/templates/language/#automatic-html-escaping](https://docs.djangoproject.com/en/5.2/ref/templates/language/#automatic-html-escaping),
verified 2026-08-02). The named production use is Django's template language in
server-rendered applications.

**Go standard library, `html/template`.** The Go package documentation describes
contextual escaping for HTML templates and states that it treats template
authors as trusted while treating executed data as untrusted
([https://pkg.go.dev/html/template](https://pkg.go.dev/html/template),
verified 2026-08-02). The named production use is Go's standard
`html/template` renderer.

**ASP.NET Core Razor.** Microsoft documents Razor's automatic HTML encoding of
output and warns against concatenating untrusted input into JavaScript
([https://learn.microsoft.com/en-us/aspnet/core/security/cross-site-scripting?view=aspnetcore-10.0](https://learn.microsoft.com/en-us/aspnet/core/security/cross-site-scripting?view=aspnetcore-10.0),
verified 2026-08-02). The named production use is Razor rendering in ASP.NET
Core.

**Ruby on Rails Action View.** Rails security guidance includes XSS discussion,
and the Rails API documents `ERB::Util.html_escape` and related escaping helpers
([https://edgeguides.rubyonrails.org/security.html#cross-site-scripting-xss](https://edgeguides.rubyonrails.org/security.html#cross-site-scripting-xss),
verified 2026-08-02;
[https://api.rubyonrails.org/classes/ERB/Util.html](https://api.rubyonrails.org/classes/ERB/Util.html),
verified 2026-08-02). The named production use is Action View escaping in Rails
applications.

**Angular templates.** Angular documents security contexts for HTML, style, URL,
and resource URL values, and says interpolation escapes HTML
([https://angular.dev/best-practices/security](https://angular.dev/best-practices/security),
verified 2026-08-02). The named production use is Angular's template binding
and sanitization model.

## 10. Consequences

Positive.

- Parser control characters in data lose grammar power at the output boundary.
- The same raw domain value can be rendered in several contexts, each with its
  own representation.
- Framework autoescaping makes the safe path shorter than string concatenation.
- Reviewers can focus on escape hatches and unsupported contexts instead of
  reading every normal interpolation as suspicious.
- The pattern preserves user data. It lets a product display characters such as
  apostrophes, angle brackets, and ampersands instead of rejecting them during
  validation.
- Contextual encoders create a narrow contract that can be tested with a fixed
  corpus of parser-breaking characters.
- A typed safe-value design makes trust transitions visible in code review.

Negative.

- The correct encoder is context-specific. A generic helper invites misuse.
- Double encoding produces visible artifacts and can break links, search
  results, email bodies, and exported files.
- Early encoding contaminates storage and makes later outputs guess whether a
  value is raw or already transformed.
- Some contexts should not receive dynamic data at all. Encoding can create
  false confidence when the sink is unsafe by design.
- Template escape hatches become high-value review points and can accumulate
  without ownership.
- Contextual template compilers depend on parseable templates. Broken markup or
  string-built partials can push values outside the compiler's view.
- Encoding is not authorization, validation, sanitization, transport security,
  or supply-chain control.

Engineering judgement. The biggest win is not the replacement of five special
characters. The biggest win is an architecture where raw data remains raw until
a known sink makes the context explicit.

## 11. Failure modes and misuse

Engineering judgement. These are the failure modes to look for in production
and code review.

**Wrong context encoder.** Symptom. A payload displays safely in a paragraph but
executes or breaks syntax when the same field is moved into an `href`, inline
script string, or style value. Cause. The code used an HTML text encoder for a
non-text context. Fix. Move encoding to the sink and use a context-specific
encoder or a contextual template engine.

**Double encoding.** Symptom. Users see `&amp;lt;`, `&amp;amp;`, or percent signs
that appear to multiply after each save. Cause. The application stored encoded
text or encoded an already encoded view model. Fix. Store raw data, mark trusted
typed values separately, and make encoders accept raw strings only.

**Encoding before validation.** Symptom. A business rule permits a value after
encoding but the decoded value violates the rule, or uniqueness checks disagree
with what users see. Cause. The system validated transformed output rather than
domain data. Fix. Validate raw values for business rules, then encode only at
output.

**Raw HTML escape hatch drift.** Symptom. A search for `innerHTML`,
`dangerouslySetInnerHTML`, `safe`, `bypassSecurityTrust`, or template raw output
finds dozens of call sites with no reviewer or sanitizer. Cause. The escape
hatch was cheaper than modeling rich text. Fix. Wrap the escape hatch behind a
single trusted-markup constructor fed by a sanitizer or a trusted producer.

**Interceptor-only escaping.** Symptom. Server-rendered HTML looks safe, but DOM
updates after page load still create XSS, or some routes show broken entities.
Cause. A response filter tried to rewrite final HTML without knowing each sink.
Fix. Remove the interceptor as the main control and encode inside the renderer
or DOM sink. OWASP lists interceptor problems, including wrong context, double
encoding, DOM-based XSS gaps, and data outside the application response path
([https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
verified 2026-08-02).

**Unsafe dynamic URL.** Symptom. A link appears escaped in HTML but still opens
a `javascript:` or `data:` URL when clicked. Cause. Attribute encoding protected
the HTML parser but did not validate the URL scheme. Fix. Validate allowed
schemes and hosts before URL construction, encode components with URL encoding,
then attribute-encode the final URL for HTML.

**Context split across concatenation.** Symptom. A template compiler escapes a
value correctly in one partial, but a helper that returns a string fragment
changes the parser state before the value arrives. Cause. Markup was assembled
through string concatenation, hiding the true sink from the compiler. Fix. Keep
markup in templates or typed builders that preserve parser context.

**Trusted type laundering.** Symptom. A wrapper named `SafeHtml` appears around
unreviewed strings, and XSS tests pass only when the payload lacks a bypass for
the sanitizer. Cause. The trusted type constructor is public or too easy to
call. Fix. Restrict constructors, require sanitizer policy names, and audit all
conversions into trusted output types.

**Log injection by record boundaries.** Symptom. A single user value creates
fake log lines or corrupts CSV export rows. Cause. The team treated encoding as
a browser-only concern and wrote raw control characters to a record grammar.
Fix. Use structured logging fields, JSON logs, or CSV writers that quote fields
according to the output format.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Output Encoding | Input Validation | HTML Sanitization | Content Security Policy | Trusted Types | Parameterized Query |
|---|---|---|---|---|---|---|
| Main question | How is this value represented for this parser? | Is this value allowed for this operation? | Which markup may remain? | What may this browser document execute or load? | Which DOM sinks accept only typed trusted values? | How does SQL receive data separately from syntax? |
| Coupling | Coupled to output context | Coupled to business rule | Coupled to allowed markup policy | Coupled to routes, assets, and browser support | Coupled to DOM sink policy | Coupled to database driver protocol |
| Consistency | Strong with autoescaping | Strong with shared validators | Strong with one sanitizer policy | Strong with central headers | Strong in supported browsers | Strong for SQL values |
| Latency | Linear text transform | Depends on rule | Parser and sanitizer cost | Header parse plus report traffic | Browser enforcement cost | Driver and server bind cost |
| Cognitive load | Medium. Context choice matters | Medium. Rule intent matters | High. Markup policy matters | High. Directives matter | High. Type policy matters | Low for callers after adoption |
| Best fit | Display data as data | Reject invalid domain data | Allow limited rich text | Reduce exploit impact in browser | Govern risky DOM APIs | SQL data values |
| Poor fit | Dynamic syntax positions | Parser safety by itself | Plain text display | Non-browser outputs | Server-rendered templates alone | HTML, XML, shell, or logs |
| Operability | Test corpus and sink inventory | Validation error metrics | Sanitizer rejection metrics | Violation reports | Policy violation reports | Query logs and database errors |
| Team topology | Platform owns encoders, teams own sinks | Domain teams own rules | Security owns policy | Security and platform own defaults | Frontend platform owns policy | Data platform owns query APIs |

Reading of the table. Output Encoding and Input Validation compose because they
answer different questions. HTML Sanitization replaces encoding only for the
special case where user-authored markup must remain markup. CSP and Trusted
Types are browser-side layers around script execution and risky DOM APIs.
Parameterized Query is the stronger pattern for SQL values because it avoids a
text grammar boundary for those values.

## 13. Related and incompatible patterns

- **Input Validation.** Complements it. Validation decides whether a value is
  acceptable for the operation. Encoding decides how that value is written to a
  grammar. Treating one as the other either rejects good data or leaves parser
  transitions exposed.
- **Content Security Policy.** Composes as defense in depth for browser pages.
  Encoding prevents many injected tokens from becoming syntax. CSP limits what
  the browser will execute or load if injection still occurs. OWASP warns
  against sole reliance on CSP for XSS prevention
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
  verified 2026-08-02).
- **HTML Sanitization.** Replaces plain encoding when the product requires a
  user to author limited markup. It should feed a trusted HTML type, not a raw
  string that can drift into another context.
- **Parameterized Query.** Replaces manual output encoding for SQL values. SQL
  values should move through bind parameters rather than escaped SQL text.
- **Safe Sink.** A concrete implementation of the pattern. DOM APIs such as
  `textContent` create text nodes instead of parsing HTML, which makes the sink
  itself perform the right operation for text display. OWASP lists several safe
  sinks
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
  verified 2026-08-02).
- **Template Method.** Often hosts the pattern in server frameworks. The
  framework owns render sequencing while application templates supply values.
- **Builder.** Composes when the builder preserves grammar context. A structured
  HTML builder can choose encoders per node and attribute. A string builder does
  not.
- **Decorator.** Can wrap a writer so all text nodes pass through an encoder.
  It is unsafe if the wrapper cannot distinguish text, attribute, script, style,
  and URL contexts.
- **Interceptor-only escaping.** Incompatible as the main control. It sees bytes
  after context has been lost.
- **String-concatenated code.** Actively conflicts. When code, markup, and data
  are all strings, the reviewer must infer parser state by hand.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it.

1. Inventory sinks, not inputs. Search for `innerHTML`, raw template markers,
   string-built HTML, inline script interpolation, inline style interpolation,
   CSV writers, XML writers, and log line concatenation.
2. Classify each sink by grammar and position. Use names such as HTML text,
   quoted HTML attribute, URL query component, JavaScript string literal, CSS
   property value, XML text, JSON response, CSV field, or log field.
3. Replace broad string helpers with context-named functions. A helper named
   `escape` becomes `htmlText`, `htmlAttr`, `jsString`, or `urlComponent`.
4. Move encoding toward the output boundary. If encoded data is stored in a
   database, add a raw column or migration path and decode once during migration
   only when the original raw value can be recovered.
5. Adopt framework autoescaping where available. Convert raw string templates
   to the framework's template syntax so the compiler can see context.
6. Quarantine escape hatches. Wrap raw HTML rendering, trust bypass APIs, and
   trusted type constructors in one module. Require a policy name or sanitizer
   result.
7. Add regression payloads for every context. The payload set should include
   angle brackets, ampersands, both quote characters, backticks, line breaks,
   URL delimiters, and strings that test the specific context.
8. Remove dead pre-encoding. Once sinks encode correctly, delete controller and
   model helpers that prepare HTML strings in advance.

Cross references to the refactoring family. Extract Function applies when a
repeated escape sequence becomes a named context encoder. Replace Magic Literal
with Symbolic Constant applies to context names and sanitizer policy names.
Introduce Parameter Object applies when a renderer receives value plus context,
encoding policy, and trust metadata. Replace Primitive with Object applies to
typed safe values such as `SafeHtml`.

Removing the pattern when it stops earning its place.

1. If the target grammar now has data binding, replace encoding with binding.
   SQL string escaping should leave in favor of prepared statements.
2. If the output moved from HTML to structured JSON, remove HTML encoders and
   let the JSON serializer own JSON string encoding.
3. If a value is no longer dynamic, replace the interpolation with a static
   template literal and delete the encoder call.
4. If rich text is now prohibited by product policy, remove sanitizer and
   trusted-markup paths, then render the stored plain text through normal
   encoding.
5. After removal, run the context payload tests. A deleted encoder is safe only
   when the sink has disappeared or the stronger binding pattern took over.

## 15. Testing and verification

Output Encoding is testable because each context has a small set of characters
that should lose grammar meaning. The harder part is proving every sink uses
the right encoder.

Techniques that apply.

- **Golden tests per context.** Feed the encoder a fixed corpus and assert exact
  output. Include ampersand, less-than, greater-than, quotes, apostrophe, slash
  where relevant, line terminators, percent signs, equals signs, and Unicode
  characters.
- **Parser round-trip tests.** Render a template with hostile values, parse it
  with the real parser when practical, and assert that the value is text, not an
  element, attribute, script, style, or extra record.
- **Sink inventory tests.** Static checks can fail builds when raw sinks appear
  outside the quarantine module. Examples include `innerHTML`, raw template
  filters, trust bypass functions, and string-built script tags.
- **Property tests.** For HTML text, generate strings and assert that parsing
  the rendered fragment creates one text node in the intended location.
- **Browser tests for DOM sinks.** Assign hostile values through `textContent`
  or equivalent safe sinks and assert no new element or handler appears.
- **Trusted-type conversion tests.** Any constructor that creates `SafeHtml` or
  similar should require sanitizer output or an explicit trusted producer.
- **Regression tests for nested contexts.** URL component inside HTML attribute
  should be tested as two encodings in order.

The samples below are intentionally small and runnable.

TypeScript sample command:

```text
npx tsc /tmp/output-encoding.ts --target es2020 --module commonjs --outDir /tmp
node /tmp/output-encoding.js
```

Python sample command:

```text
python3 /tmp/output_encoding.py
```

Go sample command:

```text
go run /tmp/output_encoding.go
```

What became easier. Encoder behavior can be tested without a web server, a
browser, or a database. Template rendering can be tested with a tiny view model.
Escape hatch policy can be tested with static search.

What became harder. A raw value may render differently in several contexts, so
tests must name the sink. Snapshot tests can hide double encoding if reviewers
do not inspect entity artifacts. Browser security tests can miss unsafe URL
schemes if they only check HTML parsing.

## 16. Observability signals

Engineering judgement. Encoding should be mostly invisible in healthy
production traffic. Observability should focus on escape hatches, rejected
trusted-markup conversions, and evidence that unsafe sinks are appearing.

What to record.

- Count escape hatch calls by route, component, helper, sanitizer policy, and
  caller. The count should be low and explainable.
- Count sanitizer rejections and removed elements or attributes for rich text
  paths. Spikes can indicate probing or a broken editor.
- Count encoder errors for invalid input type, unsupported context, or attempted
  conversion from already encoded data.
- Emit build metrics from static sink scans, such as number of raw sinks,
  number of waived findings, and age of each waiver.
- In browser applications, collect CSP and Trusted Types violation reports where
  those layers are deployed. Treat them as evidence of missed encoding or raw
  DOM paths, not as proof that encoding worked.
- For logs and exports, measure malformed record counts at downstream parsers.
  A spike after a release can indicate unencoded record delimiters.

A healthy dashboard. Raw sink count is zero outside quarantine. Escape hatch
calls are stable and tied to known rich-text features. Sanitizer rejection rates
are low enough to review and high enough to prove the path is exercised by
tests. No route shows a sudden rise in CSP or Trusted Types violations after a
template change.

A failing dashboard. Raw sink count grows by feature team. Escape hatch calls
appear on pages that do not render rich text. Sanitizer rejection rates spike
with payload-looking strings. A CSV or log consumer reports malformed records
after a new untrusted field was added. CSP reports point to inline script
execution on a route where templates were recently edited.

Privacy note. Do not log raw attack payloads by default. XSS probes often
contain copied cookies, URLs, email addresses, or customer text. Store samples
behind sampling, redaction, and retention limits.

## 17. Security and privacy implications

Output Encoding closes a parser-confusion path. It makes data stay data at a
specific output boundary. In browser applications that reduces XSS risk because
attacker-controlled text is less likely to become executable script, parsed
markup, style, or a navigable malicious URL. OWASP describes XSS as injection
of malicious content into web pages and places output encoding among the main
XSS prevention techniques
([https://owasp.org/www-community/attacks/xss/](https://owasp.org/www-community/attacks/xss/),
verified 2026-08-02;
[https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
verified 2026-08-02).

The attack surface it closes.

- HTML injection into text nodes and quoted attributes, when the correct encoder
  and quoting are used.
- JavaScript string literal breakout, when values are confined to quoted data
  positions and encoded for JavaScript.
- URL query and fragment delimiter confusion, when components are encoded
  before the full URL is embedded in another context.
- XML text and attribute injection, when XML encoders are used for XML output.
- Log and CSV record injection, when structured writers or format-specific
  quoting preserve record boundaries.

The attack surface it does not close.

- Unsafe dynamic syntax positions such as tag names, attribute names, event
  handler bodies, script bodies, CSS selectors, and URL schemes.
- Business authorization failures. Encoding a secret does not make it allowed
  to show.
- Rich text policy failures. Encoding is not a sanitizer.
- DOM-based XSS created after page load by assigning raw strings to HTML-parsing
  sinks.
- Supply-chain script compromise. Encoding user data does not make third-party
  script trustworthy.
- Browser policy gaps. CSP and Trusted Types may reduce impact, but they do not
  replace correct output representation.

Privacy implications. Output Encoding can preserve personal names, messages,
and search terms without forcing product teams to reject ordinary punctuation.
That is privacy-positive because it avoids unnecessary data distortion. It can
also create privacy risk when teams log raw rejected payloads or rendered
fragments while debugging. The safer practice is to log context name, route,
encoder name, and a redacted hash of the value, then store raw samples only in a
restricted security workflow.

Engineering judgement. The pattern is strongest when paired with three design
rules. Keep raw data raw inside the domain. Make output context explicit at the
sink. Treat every bypass from raw string to trusted output as a security review
event.

## 18. References

- OWASP Foundation, "Cross Site Scripting Prevention Cheat Sheet," sections
  "Output Encoding," "Output Encoding Rules Summary," "Dangerous Contexts,"
  "HTML Sanitization," "Safe Sinks," and "Common Anti-patterns: Ineffective
  Approaches to Avoid,"
  [https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
  verified 2026-08-02.
- OWASP Foundation, "Cross Site Scripting (XSS),"
  [https://owasp.org/www-community/attacks/xss/](https://owasp.org/www-community/attacks/xss/),
  verified 2026-08-02.
- WHATWG, "HTML Standard," section "Named character references,"
  [https://html.spec.whatwg.org/multipage/named-characters.html](https://html.spec.whatwg.org/multipage/named-characters.html),
  verified 2026-08-02.
- Django Software Foundation, "The Django template language," section
  "Automatic HTML escaping,"
  [https://docs.djangoproject.com/en/5.2/ref/templates/language/#automatic-html-escaping](https://docs.djangoproject.com/en/5.2/ref/templates/language/#automatic-html-escaping),
  verified 2026-08-02.
- Pallets, "Template Designer Documentation," section "HTML Escaping,"
  [https://jinja.palletsprojects.com/en/stable/templates/#html-escaping](https://jinja.palletsprojects.com/en/stable/templates/#html-escaping),
  verified 2026-08-02.
- Go Project, package documentation for `html/template`,
  [https://pkg.go.dev/html/template](https://pkg.go.dev/html/template),
  verified 2026-08-02.
- React, "Common components," section "dangerouslySetInnerHTML,"
  [https://react.dev/reference/react-dom/components/common#dangerously-setting-the-inner-html](https://react.dev/reference/react-dom/components/common#dangerously-setting-the-inner-html),
  verified 2026-08-02.
- Angular, "Security,"
  [https://angular.dev/best-practices/security](https://angular.dev/best-practices/security),
  verified 2026-08-02.
- Microsoft, "Prevent Cross-Site Scripting (XSS) in ASP.NET Core,"
  [https://learn.microsoft.com/en-us/aspnet/core/security/cross-site-scripting?view=aspnetcore-10.0](https://learn.microsoft.com/en-us/aspnet/core/security/cross-site-scripting?view=aspnetcore-10.0),
  verified 2026-08-02.
- Ruby on Rails Guides, "Securing Rails Applications," section
  "Cross-Site Scripting (XSS),"
  [https://edgeguides.rubyonrails.org/security.html#cross-site-scripting-xss](https://edgeguides.rubyonrails.org/security.html#cross-site-scripting-xss),
  verified 2026-08-02.
- Ruby on Rails API, `ERB::Util`,
  [https://api.rubyonrails.org/classes/ERB/Util.html](https://api.rubyonrails.org/classes/ERB/Util.html),
  verified 2026-08-02.
