---
name: Synthetic Monitoring
slug: synthetic-monitoring
family: 22-observability
category: Structural
aliases: [Synthetic Testing, Proactive Monitoring, Black-Box Monitoring, Scripted Transaction Monitoring]
first_described: 'Google names it black-box monitoring in the Site Reliability Engineering book, 2016; the term synthetic monitoring is standard vendor and industry usage by the mid 2010s'
maturity: canonical
related: [correlation-id, structured-logging, red-method, use-method, span-and-trace-context-propagation]
incompatible_with: []
verified: 2026-08-22
---

# Synthetic Monitoring

## 1. Name, aliases, and lineage

Synthetic Monitoring. Also called Synthetic Testing, Proactive Monitoring, and Scripted Transaction Monitoring. Google's own Site Reliability Engineering book calls the underlying idea Black-Box Monitoring, defined as testing externally visible behavior the way a user would see it (https://sre.google/sre-book/monitoring-distributed-systems/).

No single inventor is credited. Vendor docs across the industry converge on the same shape. Datadog describes it as observing how systems and applications are performing using simulated requests and actions from around the globe (https://docs.datadoghq.com/synthetics/), and Grafana Cloud describes its own version as a black box monitoring solution that assesses availability, performance, and correctness by emulating user behavior from global probe locations (https://grafana.com/docs/grafana-cloud/testing/synthetic-monitoring/).

## 2. Problem and context

A team wants to know when a system is broken before a person using it finds out first, and it wants that signal even during a quiet period when little or no real traffic is flowing through the exact path that broke. Waiting for a real user to hit a broken checkout flow, or a broken password reset, or a broken third party payment integration, means the team learns about the outage from a complaint rather than from its own tooling.

Synthetic Monitoring solves this by running a scripted, scheduled simulation of a real user action against the live system, on a fixed cadence, regardless of whether any real person is doing that exact thing right now. AWS's own CloudWatch Synthetics docs put it plainly, canaries follow the same routes and perform the same actions as a customer, which makes it possible to continually verify the customer experience even when there is no customer traffic on the application, and by using canaries a team learns of an issue before its customers do (https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries.html).

## 3. Forces

- A scripted check runs on a fixed schedule independent of real traffic, so it catches an outage on a rarely used but critical path, a password reset, an old account tier, a third party integration, that real user monitoring might not touch for a while, the same point AWS's own canary docs make directly (https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries.html), continually verifying the customer experience even when there is no customer traffic on the application.
- The check runs from a location the team controls rather than wherever a real user happens to be, which is a strength for repeatable measurement and a weakness for representativeness. Dynatrace names the weakness directly, because synthetic monitoring does not track real users, a team faces challenges gauging what an end user might experience for any variable it did not anticipate (https://www.dynatrace.com/news/blog/real-user-monitoring-vs-synthetic-monitoring/).
- Checking from more places and more often catches more regional and intermittent problems, but costs scale with both dimensions. AWS states this plainly for its own multi-location canaries, cost scales linearly with the number of replicas, and each replica incurs the same cost as a standalone canary (https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries_MultiLocation.html).
- A script that simulates a full login or checkout needs a real, working credential to authenticate with, which turns the check itself into a security surface that has to be scoped and protected rather than left as an afterthought.
- Google's SRE book frames the deeper tension. black-box, externally visible checks are the right tool for symptom based paging discipline, only nagging a person when a problem is both already happening and producing a real, user visible effect, but they are largely useless for catching a problem that has not yet surfaced externally, which is what internal, white-box metrics exist for instead (https://sre.google/sre-book/monitoring-distributed-systems/).

## 4. Applicability and non-applicability

### When it applies

Use Synthetic Monitoring for any user facing critical path, login, signup, checkout, a payment integration, a public API endpoint, where the cost of an undetected outage is high and where waiting for a real user complaint is not acceptable. It is the right tool for verifying a contractual uptime SLA independent of a vendor's own status page, since a team running its own scheduled checks against a dependency's endpoint gets independent, self controlled, time stamped evidence of that dependency's actual delivery, a use the Postman engineering blog describes directly for holding a vendor accountable to its own service level terms (https://blog.postman.com/sla-monitoring/).

### When it does not apply (non-applicability)

Skip it, or lean on Real User Monitoring instead, when the goal is understanding the real distribution of experience across real devices, browsers, networks, and geographies, since a scripted check only ever exercises the specific paths an engineer thought to script, from the specific location the check runs from. MDN's own contrast page names this limit directly, synthetic monitoring does not reflect what real users are experiencing and provides only a narrow view of performance (https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Rum-vs-Synthetic). It also does not apply where the check would need broad, unscoped production credentials with no dedicated test account available, since that turns a monitoring tool into a standing credential risk.

## 5. Structure

- Script. the recorded or coded sequence of actions the check performs, an API call, a chain of API calls, or a full browser flow driven by a headless browser tool such as Playwright, Puppeteer, or Selenium WebDriver (https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries.html).
- Check location. the geographic vantage point, or set of vantage points, the script runs from, chosen so a regional outage is caught rather than masked by an unaffected location.
- Schedule. the interval the check runs on, as often as once a minute for the highest priority paths (https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries.html).
- Assertion. the pass or fail condition the check evaluates, an HTTP status match, a response time budget, or the presence of expected content on a rendered page.
- Test credential. a dedicated, scoped account used only by the check, never a real customer's own credentials, held in a secrets store rather than embedded in the script itself.
- Alerting policy. the rule that turns a check failure into a page or a notification, often requiring failure from more than one location before it fires, to avoid paging on a single location's transient network issue.

## 6. ASCII structure diagram

```
   Schedule (e.g. every 1 minute)
        |
        v
   +----------------------+
   |  Synthetic check      |----uses---->  Test credential
   |  (script + assertion) |              (scoped, secrets store)
   +----------------------+
        |
        v  runs from N locations
   +--------+   +--------+   +--------+
   | Loc A  |   | Loc B  |   | Loc C  |
   +--------+   +--------+   +--------+
        |            |            |
        v            v            v
   +------------------------------------+
   |  Live production endpoint / flow    |
   +------------------------------------+
        |
        v
   pass / fail per location, per run
        |
        v
   Alerting policy (e.g. 2+ locations must fail)
        |
        v
   Page / notification, before a real user reports it
```

## 7. Dynamics

1. A team scripts the sequence of actions that matter, a single API call, a chain of calls, or a full browser run through a checkout or a login flow, and defines the pass or fail assertion for it.
2. The check is scheduled to run at a fixed interval, and configured to run from one or more geographic locations, so a region specific problem is not masked by a single unaffected vantage point. AWS's multi-location docs name the exact class of problem this catches, performance and availability can vary across locations because of network latency, ISP throttling, or a regional outage, and testing from diverse locations helps pinpoint a region specific bottleneck that a single location would not surface (https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries_MultiLocation.html).
3. On each scheduled run, the script executes against the live system using its dedicated test credential, and the result, pass or fail, along with timing data, is recorded.
4. When a check fails, the alerting policy decides whether to page. Google Cloud's Uptime Checks default to requiring at least two locations to report a failure for at least a minute before a notification fires (https://docs.cloud.google.com/monitoring/uptime-checks), a threshold chosen so one location's own network flakiness does not page a person for nothing.
5. Because the check ran without waiting for real traffic, a failure can surface before any real user hits the broken path, giving the team a window to respond ahead of a customer report. AWS's own engineering blog frames this directly, using canary alarm data a team can determine whether a change is acceptable before it affects an end user (https://aws.amazon.com/blogs/mt/visual-monitoring-of-applications-with-amazon-cloudwatch-synthetics/).
6. Timing data collected during a browser based check, page load timing, resource timing, is commonly captured through browser performance APIs such as the W3C Navigation Timing interface, still an active editor's draft rather than a finalized recommendation as of this writing (https://w3c.github.io/navigation-timing/).

## 8. Implementation variants

- API and uptime checks. a single request or a chain of requests against an endpoint, asserting on status code, response body, and latency. Datadog's own docs describe chaining requests to verify a key system across network levels (https://docs.datadoghq.com/synthetics/).
- Full browser transaction checks. a headless browser drives a real multi-step user flow, login, add to cart, checkout, capturing screenshots and load time data along the way (https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries.html).
- Script driven load style smoke checks. a lightweight scripting tool, such as Grafana's k6, scheduled to run a smoke test on an interval for continuous production verification rather than a one off load test (https://grafana.com/docs/k6/latest/testing-guides/synthetic-monitoring/).
- Black box uptime probing. the simplest variant, issuing a request from multiple global locations to a public URL and checking only whether it responds as expected, without a multi-step script (https://docs.cloud.google.com/monitoring/uptime-checks).

## 9. Known production uses

- Amazon CloudWatch Synthetics. AWS's own product for scripted canaries, supporting Node.js and Python runtimes with programmatic headless browser access through Playwright, Puppeteer, or Selenium WebDriver, checking availability, latency, and page content, and storing screenshots for visual review (https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries.html).
- Google Cloud Monitoring Uptime Checks. Google's own product issuing requests from multiple global locations to publicly available URLs or Google Cloud resources, asserting on HTTP status and response content (https://docs.cloud.google.com/monitoring/uptime-checks).
- Datadog itself migrated its own internal acceptance test corpus, previously a manually maintained Puppeteer setup consuming 6 CI or CD jobs and around 35 minutes of machine time per commit across roughly 100,000 lines of test code, onto its own Synthetic Monitoring product, integrated into CI or CD through its own datadog-ci tool. Datadog's engineering blog is explicit that this migration targeted internal acceptance testing rather than customer facing outage detection directly (https://www.datadoghq.com/blog/engineering/migrating-acceptance-tests-to-synthetic-monitoring/).

## 10. Consequences

### Benefits

- A failure can be caught before a real user hits it, turning an outage into a page for an engineer instead of a complaint from a customer.
- Coverage of a path does not depend on real traffic reaching it, so a rarely used but critical flow stays checked on a fixed schedule regardless of how quiet it currently is.
- Running from many locations catches a regional problem, a CDN edge issue, a DNS propagation problem, a single ISP's routing issue, that a small or unevenly distributed real user sample might take a while to surface on its own.
- The same scheduled, independent measurement gives a team its own evidence of a dependency's SLA delivery, rather than trusting a vendor's self reported status page.

### Costs

- Coverage is only as good as the paths a person thought to script, and Speedscale's engineering commentary names the sharpest version of this limit, a single customer action can trigger dozens of calls across services, databases, and third party dependencies, and customers take paths an engineer never anticipated (https://speedscale.com/blog/synthetic-monitoring-is-broken-production-traffic-can-fix-it/).
- Checking more often and from more locations costs proportionally more, a check running every minute instead of every five minutes multiplies cost roughly five times over (https://www.getmonetizely.com/articles/is-your-synthetic-monitoring-tool-priced-by-check-frequency-understanding-the-true-cost), and adding locations scales linearly on top of that (https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries_MultiLocation.html).
- A script that authenticates needs a real credential stored somewhere, adding a security surface that has to be scoped and secured deliberately rather than left as an afterthought.
- Because it does not track real users, it cannot answer what an actual person on an actual device, network, and browser is experiencing, only what the script itself experienced from where it ran.

## 11. Failure modes and misuse

- Treating a passing synthetic check as proof the whole system works, when the script only ever exercises the specific narrow path it was written for, and a real customer routinely takes a path the script never covers (https://speedscale.com/blog/synthetic-monitoring-is-broken-production-traffic-can-fix-it/).
- Embedding a real production credential directly in a script instead of a dedicated, scoped test account, so a leaked script leaks a real account. Datadog's own security docs recommend a dedicated account for testing specifically to avoid this (https://docs.datadoghq.com/data_security/synthetics/).
- Storing a secret used by the script in plain configuration instead of a secrets mechanism with access control, when the correct pattern, per the same Datadog docs, is an obfuscated variable store with role based permissions restricting who can read it (https://docs.datadoghq.com/data_security/synthetics/).
- Paging on a single location's failure without confirming a second location also fails, which turns one location's own network flakiness into a false alarm, exactly the failure mode Google Cloud's default multi-location confirmation threshold exists to avoid (https://docs.cloud.google.com/monitoring/uptime-checks).
- Running checks so often and from so many locations that cost grows unchecked, when the two named cost drivers, frequency and location count, both scale the bill in ways that should be sized to the path's actual importance rather than left at a default.

## 12. Trade-off matrix

| Dimension | Synthetic Monitoring | Real User Monitoring | Span and Trace Context Propagation |
|---|---|---|---|
| Coverage without real traffic | Yes | No, requires real users | No, requires real requests |
| Reflects actual user device, network, browser | No | Yes | Partially, per real request |
| Detects issue before a customer does | Yes, if the path is scripted | No, learns from the customer's own request | No, explains a request already in progress |
| Cost driver | Check frequency and location count | Real traffic volume | Span volume and export cost |
| Regional and DNS/CDN issue detection | Strong, deliberately multi-location | Depends on real traffic distribution | Not its purpose |

## 13. Related and incompatible patterns

Related to Structured Logging and Span and Trace Context Propagation, since a failing synthetic check is investigated the same way a real failing request is, by pulling the structured logs and the trace for that specific run.

Related to the RED Method and the USE Method, since a synthetic check's own latency and error rate are exactly the Rate, Errors, and Duration signals the RED Method already tracks, applied to a scripted request instead of only real ones.

Complementary to Real User Monitoring rather than a substitute for it. MDN's own framing captures the split cleanly, synthetic is well suited for catching a regression during development and for spot checking, while RUM captures what real users on real devices actually experience (https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Rum-vs-Synthetic).

Not incompatible with anything in this catalog. it is the black box half of an observability strategy that white box, internal metrics complete, per the Google SRE book's own framing of the split.

## 14. Refactoring path in and out

To introduce it, start with a small number of API level uptime checks on the most critical public endpoints, from at least two geographic locations, with an alerting policy that requires more than one location to agree before paging. Add a dedicated test account and store its credential in a secrets mechanism with restricted access before writing the first script that authenticates. Once uptime checks are stable, extend to full browser transaction checks for the highest value user flows, login, checkout, signup, and wire the check's own failure metric into the existing alerting pipeline alongside real request based alerts, rather than as a separate, disconnected notification channel.

Removing it is reasonable only when a path has genuinely stopped being critical, since the debugging value scales with exactly the paths that would hurt the most to leave without a check. A team scaling back cost pressure should first reduce check frequency or location count on lower priority paths before removing coverage on a path a customer would actually notice breaking.

## 15. Testing and verification

Assert that a known good path passes the check and a known bad path, an intentionally broken staging endpoint, fails it, so the check itself is proven to distinguish success from failure before it is trusted in production. Assert that the check's credential is genuinely a dedicated test account and not a real customer's own login, by confirming it authenticates against a test or sandboxed environment where that separation matters. Test the alerting policy directly, forcing a single location failure and confirming no page fires, then forcing two locations to fail and confirming one does, to prove the confirmation threshold behaves as configured rather than assumed.

## 16. Observability signals

Watch the pass and fail rate per check, per location, over time, since a check that fails only from one location points at a regional problem while a check failing everywhere points at the system itself. Watch the check's own latency trend, since a slow but passing check is an early warning of a coming failure rather than a confirmed one. Watch how often the alerting policy actually pages against how often a single location alone fails, since a policy that pages far more often than it should for real, confirmed outages is a sign the confirmation threshold or the check's own stability needs attention.

## 17. Security and privacy implications

The test credential a script authenticates with is a real security surface. Datadog's own guidance is direct, use a dedicated account for testing rather than a real user's credentials, and store any secret value in an obfuscated variable with access restricted by role based permissions rather than embedded directly in the script (https://docs.datadoghq.com/data_security/synthetics/). A screenshot or a recorded response body captured by a browser based check can also contain personal data if the check happens to render it, so a check's captured artifacts deserve the same handling discipline as any other system that stores a snapshot of production content.

## 18. References

1. Google Site Reliability Engineering book, Monitoring Distributed Systems chapter. Defines black-box monitoring, testing externally visible behavior as a user would see it, and frames its role alongside white-box monitoring. https://sre.google/sre-book/monitoring-distributed-systems/, verified 2026-08-22.
2. Datadog documentation, Synthetic Monitoring overview. Defines the practice and its API and browser test variants. https://docs.datadoghq.com/synthetics/, verified 2026-08-22.
3. MDN Web Docs, RUM versus Synthetic monitoring. The direct head to head contrast between the two techniques. https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Rum-vs-Synthetic, verified 2026-08-22.
4. AWS documentation, CloudWatch Synthetics Canaries. Defines canaries, their headless browser tooling, and the learn-of-an-issue-before-customers-do benefit. https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries.html, verified 2026-08-22.
5. AWS documentation, CloudWatch Synthetics Multilocation Canaries. Defines multi-region checking, the regional-bottleneck rationale, and the linear cost-per-replica model. https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries_MultiLocation.html, verified 2026-08-22.
6. Google Cloud documentation, Monitoring Uptime Checks. Defines the product and its default multi-location alerting confirmation threshold. https://docs.cloud.google.com/monitoring/uptime-checks, verified 2026-08-22.
7. Datadog documentation, Data Security for Synthetics. Recommends dedicated test accounts and describes the obfuscated, role restricted secrets mechanism. https://docs.datadoghq.com/data_security/synthetics/, verified 2026-08-22.
8. Speedscale engineering blog, on the limits of scripted synthetic coverage against real, unanticipated user paths. Cited as industry commentary from a vendor with a competing product, not neutral fact. https://speedscale.com/blog/synthetic-monitoring-is-broken-production-traffic-can-fix-it/, verified 2026-08-22.
9. Datadog engineering blog, migrating an internal acceptance test corpus to Synthetic Monitoring. A real, first party account of production use, though it describes Datadog dogfooding its own product for internal testing rather than an independent company's customer facing outage detection. https://www.datadoghq.com/blog/engineering/migrating-acceptance-tests-to-synthetic-monitoring/, verified 2026-08-22.

**Evidence grade.** high

**Most solid findings.** The black-box monitoring definition and its relationship to white-box monitoring (source 1) come directly from Google's own SRE book, fetched live from sre.google. The AWS canary docs (source 4, 5) are first party, current vendor documentation naming a real, specific product with concrete capability numbers, including the up-to-50-replica-location figure and the linear cost model. The Datadog security guidance (source 7) is a first party security document, not a marketing page, giving a specific, checkable recommendation.

**Unverified or unclear.** No first party engineering account from an independent company outside the observability vendor space, Uber, Netflix, Shopify, Stripe, GitHub, or Slack were checked, could be found describing classic scripted synthetic monitoring specifically, as opposed to canary deployment or traffic shadowing, which is a related but different technique. Source 9 is therefore a vendor's account of using its own product internally rather than an independent customer's account, and is labeled honestly as such rather than presented as broader independent validation. A concrete location count for Datadog's own probe network was found only through a third party blog citing Datadog, not through Datadog's own docs directly, so that specific number was left out of the entry rather than cited on secondary sourcing alone.

## Code examples

### Go, a minimal scheduled uptime check with multi-location confirmation

```go
package main

import (
	"fmt"
	"net/http"
	"time"
)

type checkResult struct {
	location string
	ok       bool
}

func runCheck(location, url string, client *http.Client) checkResult {
	resp, err := client.Get(url)
	if err != nil {
		return checkResult{location: location, ok: false}
	}
	defer resp.Body.Close()
	return checkResult{location: location, ok: resp.StatusCode == http.StatusOK}
}

func shouldPage(results []checkResult, minFailures int) bool {
	failed := 0
	for _, r := range results {
		if !r.ok {
			failed++
		}
	}
	return failed >= minFailures
}

func main() {
	client := &http.Client{Timeout: 5 * time.Second}
	locations := []string{"us-east", "eu-west"}
	url := "https://example.com/health"

	results := make([]checkResult, 0, len(locations))
	for _, loc := range locations {
		results = append(results, runCheck(loc, url, client))
	}

	if shouldPage(results, 2) {
		fmt.Println("PAGE: confirmed from 2+ locations")
	} else {
		fmt.Println("ok, or single-location noise")
	}
}
```

### Python, a scripted browser style transaction check assertion

```python
from dataclasses import dataclass


@dataclass
class StepResult:
    name: str
    passed: bool
    duration_ms: float


def assert_transaction(steps: list[StepResult], budget_ms: float) -> bool:
    if any(not s.passed for s in steps):
        return False
    total = sum(s.duration_ms for s in steps)
    return total <= budget_ms


steps = [
    StepResult("login", True, 320.0),
    StepResult("add_to_cart", True, 210.0),
    StepResult("checkout", True, 480.0),
]
print(assert_transaction(steps, budget_ms=1500.0))
```

### TypeScript, an alerting-policy confirmation threshold

```typescript
interface LocationCheck {
  location: string;
  ok: boolean;
}

function confirmedFailure(checks: LocationCheck[], threshold: number): boolean {
  const failed = checks.filter((c) => !c.ok).length;
  return failed >= threshold;
}

const checks: LocationCheck[] = [
  { location: "us-east", ok: false },
  { location: "eu-west", ok: false },
  { location: "ap-south", ok: true },
];

console.log(confirmedFailure(checks, 2));
```
