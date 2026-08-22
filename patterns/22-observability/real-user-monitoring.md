---
name: Real User Monitoring
slug: real-user-monitoring
family: 22-observability
category: Structural
aliases: [RUM, Field Monitoring, Web Performance Monitoring]
first_described: 'no single named originator; the term Real User Monitoring is standard vendor and web performance industry usage by the early 2010s, formalized alongside the Core Web Vitals initiative Google introduced in 2020'
maturity: canonical
related: [correlation-id, structured-logging, red-method, use-method, span-and-trace-context-propagation, synthetic-monitoring]
incompatible_with: []
verified: 2026-08-22
---

# Real User Monitoring

## 1. Name, aliases, and lineage

Real User Monitoring, commonly shortened to RUM. Also called Field Monitoring or Web Performance Monitoring. MDN's own definition captures the core idea, RUM measures the performance of a page from real users' machines, and this technique monitors an application's actual user interactions (https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Rum-vs-Synthetic).

No single inventor is credited. Major vendors independently converge on the same shape. Datadog frames its own product as giving complete visibility into the real time activity and experience of individual users (https://docs.datadoghq.com/real_user_monitoring/), and New Relic frames its browser product the same way, measuring speed and performance as end users move through a site across different browsers, devices, operating systems, and networks (https://docs.newrelic.com/docs/browser/browser-monitoring/getting-started/introduction-browser-monitoring/).

## 2. Problem and context

A team wants to know what a real person on a real device, a real network, in a real place, actually experiences when using an application, rather than only what a controlled test run measures from one fixed location. A team can script and test every path it thinks to test, but it cannot script every real device, browser version, network condition, and geography its actual audience uses.

Real User Monitoring solves this by capturing performance data directly from real sessions as they happen. A small script embedded in the page, or an equivalent instrumentation layer in a native app, reports back what that specific person's device actually measured, aggregated across every real visit rather than a handful of controlled runs. Google's own web.dev states the business case for the metrics RUM is built to collect plainly, a study across 37 sites and over 30 million real sessions found a 0.1 second speed improvement raised retail conversion rates by 8.4 percent and travel conversion rates by 10.1 percent (https://web.dev/case-studies/milliseconds-make-millions).

## 3. Forces

- RUM captures the full range of real conditions, every device, browser, network, and location an actual audience uses, which a scripted check run from a fixed location can never fully represent. MDN names this directly, RUM captures the performance of actual users regardless of device, browser, network or geographic location, and monitors actual use cases rather than the synthetic, assumed ones a person predefined (https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Rum-vs-Synthetic).
- An average hides the tail of bad experiences, so RUM data is reported by percentile rather than mean. web.dev's own field measurement guidance states this directly, percentiles across a distribution better describe the full range of user experiences, since an average does not represent any single person's session, and recommends the 75th percentile as the primary figure with the 90th or 95th used to understand the experience of a person on a slower device or connection (https://web.dev/articles/vitals-field-measurement-best-practices).
- Collecting a signal from every real visit at a busy site produces a large volume of events, which most implementations manage through sampling. Datadog's own docs give a worked example, a session sample rate defaults to collecting every session, and a team can configure a lower rate so only a chosen percentage of sessions is tracked (https://docs.datadoghq.com/real_user_monitoring/guide/sampling-browser-plans/).
- Collection depends on a script actually running in the real person's browser, so a person running an ad blocker or a privacy focused extension can be silently absent from the data. Datadog's own troubleshooting docs confirm this directly, ad blockers prevent the RUM browser SDK from being downloaded or from sending data at all (https://docs.datadoghq.com/real_user_monitoring/browser/troubleshooting/).
- Because RUM only measures a real visit, it has no signal at all until a real person actually triggers the path being watched, unlike a scripted check that can run on its own schedule regardless of traffic.

## 4. Applicability and non-applicability

### When it applies

Use Real User Monitoring wherever the actual, felt experience of a real audience matters, and where the range of real devices, networks, and locations is wide enough that a handful of scripted checks cannot stand in for it. It is the tool for a metric that genuinely cannot be measured any other way. web.dev states this plainly for Interaction to Next Paint, one of the three Core Web Vitals, INP cannot be measured in a lab environment because there is no actual user input in a simulated run, so it can only be measured in the field, from real people (https://web.dev/articles/vitals). It is also the right tool for correlating a real, live incident with a specific release, since a team can compare error rate and load time by version and roll back a release the moment real user data shows it is causing harm (https://docs.datadoghq.com/real_user_monitoring/guide/setup-rum-deployment-tracking/).

### When it does not apply (non-applicability)

Skip it, or lean on Synthetic Monitoring instead, for a path that needs a signal even when no real person is currently using it, since RUM by definition needs real traffic before it produces anything. Dynatrace states this limitation directly, RUM requires traffic to be useful, and if a team tries to use it in a pre-production environment with no real visitors, it is challenging to get useful information (https://www.dynatrace.com/news/blog/real-user-monitoring-vs-synthetic-monitoring/). It also does not apply where a stable, controlled, repeatable measurement matters more than real world coverage, since RUM data is naturally noisy and shaped by whatever real conditions happened to occur.

## 5. Structure

- Client instrumentation. a small script embedded in a web page, or an equivalent native library on mobile, that reads browser or platform performance APIs during a real session.
- Metric collector. the in browser or in app component that gathers the raw measurements, commonly built on the Performance API and a PerformanceObserver, exactly the mechanism Google's own web-vitals library uses to measure every Core Web Vitals metric on real users (https://github.com/GoogleChrome/web-vitals).
- Delivery mechanism. the way the collected data ships back to a server without blocking the page, most reliably through the browser's background data transmission API, `navigator.sendBeacon` (reference 4), whose main use case MDN names directly as sending analytics such as client side events or session data to a server, guaranteed to be sent even as the page is closing.
- Sample rate. the configured percentage of real sessions actually collected and shipped, trading data volume and cost against representativeness.
- Segment dimensions. the facets a session can be sliced by after collection, device, browser, network condition, geography, and page, so a problem concentrated in one segment is not hidden inside a blended average.
- Field dataset. the aggregated store of real session data, queried by percentile and by segment, and in Google's case also published as the Chrome User Experience Report, described in Google's own words as similar to RUM but collected automatically by the Chrome browser itself rather than through code embedded on a site (https://web.dev/articles/crux-and-rum-differences).

## 6. ASCII structure diagram

```
   Real person's browser or app
        |
        v
   +------------------------+
   | Client instrumentation  |  reads Performance API,
   | (script or native lib)  |  PerformanceObserver
   +------------------------+
        |
        v  sample-rate filter applied
   +------------------------+
   |  Delivery (sendBeacon / |----ships data---->  Field dataset
   |  fetch keepalive)       |                     (percentile + segment)
   +------------------------+
        |
        v
   Real business signal: p75 LCP, p75 INP, CLS,
   error rate by version, conversion correlation
        |
        v
   Segment slice (device / browser / network / geo)
   to find which real audience is affected
```

## 7. Dynamics

1. A person loads a page or opens an app, and the embedded client instrumentation begins observing the real session as it happens, through the browser's own Performance API or a native equivalent.
2. A sample rate decision is applied, so only a configured percentage of real sessions is actually collected rather than every one, controlling both data volume and cost (https://docs.datadoghq.com/real_user_monitoring/guide/sampling-browser-plans/).
3. As the session runs, the instrumentation records the metrics that matter, page load timing, Largest Contentful Paint, Interaction to Next Paint, Cumulative Layout Shift, or a native equivalent such as application launch time or a hang.
4. Before the page is closed or the session ends, the collected data is shipped to a collection endpoint using a background data transmission mechanism (`navigator.sendBeacon`) built to survive the page unloading, rather than a normal request that could be cancelled mid flight (https://developer.mozilla.org/en-US/docs/Web/API/Beacon_API).
5. The field dataset accumulates real sessions over time, and a team queries it by percentile, the 75th for the primary Core Web Vitals figure, higher percentiles for the tail of a slower device or connection (https://web.dev/articles/vitals-field-measurement-best-practices), and by segment, isolating whether a problem is spread evenly or concentrated in one device type, network condition, or region.
6. When a new release goes out, the same field data is compared by version, so a rise in real error rate or load time right after a deployment is caught from real user evidence and can drive a rollback decision (https://docs.datadoghq.com/real_user_monitoring/guide/setup-rum-deployment-tracking/).

## 8. Implementation variants

- Web RUM via a JavaScript library. the most common shape, a script such as Google's web-vitals library or a vendor SDK using PerformanceObserver and a background transmission call to collect Core Web Vitals from real page loads (https://github.com/GoogleChrome/web-vitals).
- Browser native field data across the whole web. the Chrome User Experience Report, Google's own automatically collected dataset covering popular destinations, described by Google as functioning like RUM but collected by the browser itself rather than through embedded code, and used directly as a Search page experience ranking input (https://developer.chrome.com/docs/crux).
- Mobile app RUM. an equivalent practice for native apps, capturing real device metrics such as launch time and hangs through Apple's MetricKit, or crash and Application Not Responding rates through Android's own Vitals program, which defines a user perceived ANR rate as the percentage of real daily active people who experienced at least one (https://developer.android.com/topic/performance/vitals/anr).
- Deployment correlated RUM. field metrics bucketed and compared by release version specifically, so a team can see error rate and load time change immediately after a specific deployment rather than only as an undated aggregate (https://docs.datadoghq.com/real_user_monitoring/guide/setup-rum-deployment-tracking/).

## 9. Known production uses

- Google's web-vitals JavaScript library. an open source, roughly three kilobyte library that measures every Core Web Vitals metric on real users and reports the result over a reliable background channel, the reference implementation most vendor RUM products build the same idea on top of (https://github.com/GoogleChrome/web-vitals).
- The Chrome User Experience Report. Google's own global field dataset, collected automatically from real Chrome users, publicly queryable, and used by Google Search to inform the page experience ranking signal (https://developer.chrome.com/docs/crux).
- Datadog Real User Monitoring, a named commercial product providing session level real user visibility, sampling controls, deployment version tracking, and configurable PII handling for compliance with regulatory frameworks including GDPR (https://docs.datadoghq.com/data_security/real_user_monitoring/).

## 10. Consequences

### Benefits

- The full range of real devices, browsers, networks, and locations is represented, rather than only the paths and conditions an engineer thought to script.
- A metric that cannot be measured in a lab at all, such as Interaction to Next Paint, is only available through this pattern, since it needs a real person's real input to exist (https://web.dev/articles/vitals).
- A real, live incident can be correlated with a specific release the moment it happens, so a rollback decision is based on real evidence rather than a synthetic proxy.
- Slicing by device, browser, network, or region finds the specific real audience segment having a bad experience, which a single blended average would hide (https://www.motadata.com/features/rum-segmentation).

### Costs

- It has no signal at all until a real person actually triggers the path, so a rarely used but critical path can stay unmonitored for a long stretch of quiet real traffic, the opposite failure mode from Synthetic Monitoring.
- A person running an ad blocker or a privacy extension can be silently excluded from the dataset, since collection depends entirely on the client script running (https://docs.datadoghq.com/real_user_monitoring/browser/troubleshooting/).
- Data volume and its cost scale with real traffic and event count. AWS's own CloudWatch RUM pricing page gives a worked example of 500,000 monthly visits at 20 events each producing 10 million billed events at roughly 100 US dollars a month (https://aws.amazon.com/cloudwatch/pricing/).
- Real session data is tied by nature to a real person's device, network, and often their location, which raises privacy questions a purely synthetic check never has to answer.

## 11. Failure modes and misuse

- Reporting the mean instead of a percentile, which hides exactly the tail of slow, real experiences that matter most, the failure web.dev's own field guidance names directly when it states an average does not represent any single person's session (https://web.dev/articles/vitals-field-measurement-best-practices).
- Assuming ad blocker driven data loss is random noise rather than a systematic gap, when the sources of that gap are well documented, Datadog's own troubleshooting docs confirm ad blockers prevent the SDK from loading or sending data at all for the people running them (https://docs.datadoghq.com/real_user_monitoring/browser/troubleshooting/).
- Expecting RUM to catch a broken but rarely used path quickly, when by definition it only produces a signal once a real person happens to hit that exact path, unlike a scheduled synthetic check.
- Collecting raw IP address, precise location, or another identifying field with no anonymization or opt out path, when a compliant configuration is available and documented, for example Datadog's own default of tying each session only to an anonymized session identifier with no user identity tracked (https://docs.datadoghq.com/data_security/real_user_monitoring/).
- Treating a business correlation study like the Google commissioned Milliseconds Make Millions research as proof any specific site's own conversion will move by the same percentage, when the real, cited figures are aggregate findings across 37 sites and are not a guarantee for any one property (https://web.dev/case-studies/milliseconds-make-millions).

## 12. Trade-off matrix

| Dimension | Real User Monitoring | Synthetic Monitoring | Span and Trace Context Propagation |
|---|---|---|---|
| Needs real traffic to produce a signal | Yes | No | Yes, real requests only |
| Represents the actual real world device and network mix | Yes | No, only the scripted vantage point | Partially, per real request |
| Can measure a metric needing real input (e.g. INP) | Yes | No | Not its purpose |
| Detects an issue before a real person hits it | No | Yes, if the path is scripted | No, explains a request already happening |
| Cost driver | Real traffic volume and sample rate | Check frequency and location count | Span volume and export cost |

## 13. Related and incompatible patterns

Complementary to Synthetic Monitoring rather than a substitute for it, the two forming the field and lab halves of a full performance picture. MDN's own framing draws the line cleanly, synthetic is well suited for catching a regression during development and for spot checking performance, while RUM captures what real users on real devices actually experience (https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Rum-vs-Synthetic).

Related to Structured Logging and Span and Trace Context Propagation, since a real user session flagged as slow or erroring by RUM is investigated the same way any other real request is, by pulling the structured logs and the trace for that specific session.

Related to the RED Method and the USE Method, since RUM's own error rate and load time figures, sliced by real segment, are the Rate, Errors, and Duration signals applied specifically to real user traffic rather than the service's aggregate view.

Not incompatible with anything in this catalog. it is the real world, field half of an observability strategy that a scripted, lab based check completes.

## 14. Refactoring path in and out

To introduce it, start by embedding a small, well scoped instrumentation library, such as Google's web-vitals library or a vendor SDK, on the highest traffic pages first, collecting the three Core Web Vitals at a conservative sample rate. Wire the collected data into percentile based dashboards, the 75th percentile as the primary figure, before drawing any conclusion from an average. Add segmentation by device, browser, and region once the base signal is trustworthy, so a problem affecting only a real minority of the audience becomes visible rather than blended away. Only after the web side is stable should a team extend the same idea to native mobile apps through MetricKit or Android Vitals, since the collection mechanism and the metrics differ meaningfully between platforms.

Removing it is reasonable only when an application's real audience has genuinely narrowed to a small, controlled, known set of devices and networks, since that is the one condition under which a scripted synthetic check can approximate the real experience well enough on its own. For any application with a broad, uncontrolled real audience, removing RUM trades away the only source of truth for what that audience is actually feeling.

## 15. Testing and verification

Assert that the client instrumentation actually ships data on a real page load in a staging environment before trusting it in production, since a misconfigured collector can silently produce zero events while looking correctly wired. Assert that the configured sample rate produces the expected proportion of collected sessions over a known volume of real traffic, so a team can trust the percentage it believes it is collecting. Test the ad blocker failure mode directly, loading the page with a common blocker active and confirming the application still functions correctly even though its RUM data for that session is lost. Assert that a documented compliant configuration, such as IP or location field removal, is genuinely in effect by inspecting a real collected event rather than only the configuration screen.

## 16. Observability signals

Watch the 75th percentile of each Core Web Vitals metric over time as the primary health signal, with the 90th or 95th watched separately for the tail of a slower device or connection (https://web.dev/articles/vitals-field-measurement-best-practices). Watch error rate and load time bucketed by release version, since a rise immediately after a deployment is the clearest real world signal that a specific release caused harm (https://docs.datadoghq.com/real_user_monitoring/guide/setup-rum-deployment-tracking/). Watch the collected session volume against the expected sample rate and real traffic volume, since a silent drop in collected sessions, distinct from a real traffic drop, points at a broken or blocked instrumentation rather than a quieter audience.

## 17. Security and privacy implications

Real session data is tied to a real person's device, network, and often an approximate location derived from their IP address, which makes privacy handling a first class concern rather than an afterthought. Datadog's own compliance docs are direct about the available controls, IP address and geolocation data can be removed, RUM can be configured for compliance with regulatory frameworks including GDPR, and by default no user identity is tracked, each session tied only to an anonymized session identifier (https://docs.datadoghq.com/data_security/real_user_monitoring/). A team collecting RUM data should decide explicitly which identifying fields are needed at all, remove or anonymize the rest, and document that configuration the same way any other system handling real personal data would.

## 18. References

1. MDN Web Docs, RUM versus Synthetic monitoring. The core definition and the direct head to head contrast between the two techniques. https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Rum-vs-Synthetic, verified 2026-08-22.
2. web.dev, Web Vitals. Defines LCP, INP, and CLS, their thresholds, and states directly that INP can only be measured in the field since it needs real user input. https://web.dev/articles/vitals, verified 2026-08-22.
3. GitHub, GoogleChrome/web-vitals. The reference JavaScript library, its PerformanceObserver based mechanism, and its own description as measuring metrics on real users. https://github.com/GoogleChrome/web-vitals, verified 2026-08-22.
4. MDN Web Docs, the browser's background data transmission API. Defines the reliable, non blocking mechanism (`navigator.sendBeacon`) RUM data is commonly shipped back to a server through. https://developer.mozilla.org/en-US/docs/Web/API/Beacon_API, verified 2026-08-22.
5. web.dev, field measurement guidance for Web Vitals. Explains why percentiles, not averages, are used to report RUM data. https://web.dev/articles/vitals-field-measurement-best-practices, verified 2026-08-22.
6. web.dev, why CrUX data differs from RUM data. Google's own framing of the Chrome User Experience Report as functioning like RUM but collected by the browser itself. https://web.dev/articles/crux-and-rum-differences, verified 2026-08-22.
7. Chrome for Developers, Chrome User Experience Report. Confirms CrUX is used by Google Search to inform the page experience ranking signal. https://developer.chrome.com/docs/crux, verified 2026-08-22.
8. Datadog documentation, RUM sampling and compatible plans. A worked configuration example of the session sample rate mechanism. https://docs.datadoghq.com/real_user_monitoring/guide/sampling-browser-plans/, verified 2026-08-22.
9. Datadog documentation, Data Security for Real User Monitoring. Direct compliance guidance on PII, IP address handling, and GDPR configuration. https://docs.datadoghq.com/data_security/real_user_monitoring/, verified 2026-08-22.
10. Datadog documentation, RUM Deployment Tracking. Confirms the real time error rate and load time by version workflow that drives a rollback decision. https://docs.datadoghq.com/real_user_monitoring/guide/setup-rum-deployment-tracking/, verified 2026-08-22.
11. Datadog documentation, RUM browser troubleshooting. Confirms ad blockers prevent the RUM SDK from loading or sending data. https://docs.datadoghq.com/real_user_monitoring/browser/troubleshooting/, verified 2026-08-22.
12. web.dev, Milliseconds Make Millions case study. A Google commissioned study across 37 sites and over 30 million real sessions correlating page speed with conversion rate. https://web.dev/case-studies/milliseconds-make-millions, verified 2026-08-22.
13. Dynatrace blog, synthetic versus real user monitoring. States the limitation that RUM requires real traffic to be useful. https://www.dynatrace.com/news/blog/real-user-monitoring-vs-synthetic-monitoring/, verified 2026-08-22.
14. Android Developers, Application Not Responding (ANR). The mobile RUM equivalent, defining a real, field measured ANR rate across actual daily active people. https://developer.android.com/topic/performance/vitals/anr, verified 2026-08-22.

**Evidence grade.** high

**Most solid findings.** The Core Web Vitals definitions and the field-only nature of INP (source 2) come directly from web.dev's own current page. The percentile-over-average guidance (source 5) and the CrUX-as-RUM framing (source 6, 7) are Google's own stated positions, not inferred. The ad blocker data loss mechanism (source 11) and the compliance controls (source 9) are first party vendor admissions and documentation rather than third party speculation.

**Unverified or unclear.** The Milliseconds Make Millions study (source 12) demonstrates that speed correlates with conversion broadly, but its own methodology was not confirmed to be RUM specifically in the fetched content, so it is cited here as the business case for the metrics RUM measures rather than as a RUM measured result itself. The claim that ad-blocker driven data loss skews toward a specific demographic of more privacy conscious users was not found stated directly in an authoritative source and is not asserted in this entry. A concrete Datadog or Dynatrace RUM price per session figure was found only through secondary sourcing and was left out in favor of the fully verified AWS CloudWatch RUM pricing example.

## Code examples

### Go, a percentile-first RUM aggregator

```go
package main

import (
	"fmt"
	"sort"
)

func percentile(samples []float64, p float64) float64 {
	if len(samples) == 0 {
		return 0
	}
	sorted := append([]float64(nil), samples...)
	sort.Float64s(sorted)
	idx := int(p / 100 * float64(len(sorted)-1))
	return sorted[idx]
}

func mean(samples []float64) float64 {
	total := 0.0
	for _, s := range samples {
		total += s
	}
	return total / float64(len(samples))
}

func main() {
	lcp := []float64{1200, 1400, 1350, 5200, 1500, 1600, 1450, 8100, 1300, 1550}
	fmt.Println("p75 LCP:", percentile(lcp, 75))
	fmt.Println("p95 LCP:", percentile(lcp, 95))
	fmt.Println("mean would hide the tail:", mean(lcp))
}
```

### Python, RUM segmentation by device type

```python
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class RumEvent:
    device: str
    lcp_ms: float


def segment_p75(events: list[RumEvent]) -> dict[str, float]:
    by_device: dict[str, list[float]] = defaultdict(list)
    for e in events:
        by_device[e.device].append(e.lcp_ms)

    result = {}
    for device, values in by_device.items():
        values.sort()
        idx = int(0.75 * (len(values) - 1))
        result[device] = values[idx]
    return result


events = [
    RumEvent("mobile", 3200),
    RumEvent("mobile", 4100),
    RumEvent("desktop", 900),
    RumEvent("desktop", 1100),
    RumEvent("mobile", 2800),
]
print(segment_p75(events))
```

### TypeScript, a sample-rate gated send

```typescript
interface VitalMetric {
  name: string;
  value: number;
}

type BeaconCapableNavigator = Navigator & {
  sendBeacon?: (url: string, data?: string) => boolean;
};

function shouldSample(sampleRatePercent: number): boolean {
  return Math.random() * 100 < sampleRatePercent;
}

function reportMetric(metric: VitalMetric, sampleRatePercent: number): void {
  if (!shouldSample(sampleRatePercent)) return;
  const body = JSON.stringify(metric);
  const nav = navigator as BeaconCapableNavigator;
  if (nav.sendBeacon) {
    nav.sendBeacon("/rum-collect", body);
  }
}

reportMetric({ name: "LCP", value: 1420 }, 20);
```
