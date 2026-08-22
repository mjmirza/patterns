---
name: USE Method
slug: use-method
family: 22-observability
category: Structural
aliases: [Utilization Saturation Errors]
first_described: 'Brendan Gregg, brendangregg.com/usemethod.html, exact first publication year not independently verified this session'
maturity: canonical
related: [red-method, structured-logging, correlation-id]
incompatible_with: []
verified: 2026-08-22
---

# USE Method

## 1. Name, aliases, and lineage

USE Method. The name is an acronym for its three checks, Utilization, Saturation, Errors, and it is sometimes written out as Utilization Saturation Errors in full.

Brendan Gregg is its author, and his own site states the method in the fewest possible words, for every resource, check utilization, saturation, and errors (https://www.brendangregg.com/usemethod.html). He defines each term precisely rather than loosely. Utilization is the average time that the resource was busy servicing work. Saturation is the degree to which the resource has extra work which it cannot service, often queued. Errors is the count of error events. He states its purpose directly too, it is intended to be used early in a performance investigation, to identify systemic bottlenecks, and he makes a specific, quantified claim about its value, it solves about 80 percent of server issues with 5 percent of the effort.

## 2. Problem and context

When a system is running slowly, the obvious first instinct is to start with application level profiling, reading through code paths, adding instrumentation, and guessing at what might be slow. That instinct often skips past the simpler, faster question of whether the underlying hardware itself, the CPU, the memory, a disk, or the network, is the actual bottleneck, and it is easy to miss an obviously overloaded resource entirely if there is no systematic way of checking every one of them.

The USE Method solves this by giving a fixed, repeatable checklist. for every resource in the system, check three things in the same order, every time. Utilization, how busy is it. Saturation, does it have more work queued than it can service. Errors, is it failing outright. Because the checklist is the same for every resource and every system, it turns an open ended investigation into a fast, mechanical sweep that either finds the bottleneck directly or rules out the hardware layer entirely before moving on to application level analysis.

## 3. Forces

- A fast, systematic sweep across every resource finds an obvious hardware bottleneck quickly, but Gregg's own framing is honest about its limit, it solves about 80 percent of server issues with 5 percent of the effort, meaning a real fraction of problems still need slower, deeper methods.
- Utilization measured as an average over a long window can look calm even while the resource was fully busy for short bursts within that window, and Gregg's own worked example shows exactly this, an 80 percent average utilization figure that hid a period where the resource actually hit 100 percent for seconds at a time, causing real performance issues that the average alone would never reveal.
- Saturation is conceptually simple but was historically hard to measure directly on some platforms, which is part of why modern operating systems have added dedicated tooling for it, Linux's pressure stall information reports the share of time in which at least some, or all, tasks are stalled waiting on a given resource (https://docs.kernel.org/accounting/psi.html), giving a direct answer where earlier tooling only offered an indirect proxy.
- The method is explicitly scoped to resources, not services, and Grafana's own account of the RED Method's origin quotes this distinction directly from the RED Method's own creator, the USE Method does not really apply to services, it applies to hardware, network disks, things like this (https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/), so a request driven service needs a different pattern entirely.
- Checking every resource and every metric combination on a system takes real time, and Gregg's own page names this cost plainly, reading metrics for every combination can be very time consuming, so in practice an investigator may only have time to check a subset.

## 4. Applicability and non-applicability

### When it applies

Use the USE Method early in any performance investigation involving hardware or infrastructure resources, CPU, memory, storage I/O, and network, whether the goal is to rule the hardware layer in or out before moving to application level analysis, or to build a standing dashboard that watches these resources on an ongoing basis.

### When it does not apply (non-applicability)

Skip it, or reach for the RED Method instead, for a request driven service, where the natural unit of analysis is a request rather than a resource, and where Rate, Errors, and Duration answer the actual question users care about. The RED Method's own creator states this boundary directly, the USE Method does not really apply to services, it applies to hardware, not to the request driven services RED was created for (https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/), and ClickHouse's own comparison of the two methods states it from the resource side too, USE covers the resources those services run on, RED covers the services users talk to (https://clickhouse.com/resources/engineering/red-use-methods).

## 5. Structure

- Resource. anything with a finite capacity a system depends on, CPU, memory, a storage device, a network interface, and the like, each considered in turn.
- Utilization metric. the average time the resource was busy servicing work, expressed as a percentage.
- Saturation metric. the degree to which the resource has extra work queued that it cannot currently service, on Linux increasingly measured directly through pressure stall information rather than inferred indirectly.
- Errors metric. the count of error events reported by or about the resource.
- The checklist. the fixed, repeatable sequence, for every resource, check Utilization, then Saturation, then Errors, applied uniformly rather than improvised per investigation.

## 6. ASCII structure diagram

```
  List every resource
  (CPU, memory, disk, network, ...)
        |
        v
  For each resource:
        |
        +----> check Utilization  (percent busy)
        |
        +----> check Saturation   (queued work it cannot service)
        |
        +----> check Errors       (error event count)
        |
        v
  High Utilization + rising Saturation
  = candidate bottleneck
        |
        v
  Move to the next resource, repeat
```

## 7. Dynamics

1. The investigator, or an automated dashboard, enumerates every resource on the system worth checking, CPU, memory, each storage device, each network interface.
2. For the first resource, Utilization is checked, the average time it was busy servicing work over the measurement window.
3. Saturation is checked next, whether the resource has more work queued than it can currently service, on modern Linux systems read directly from pressure stall information rather than approximated (https://docs.kernel.org/accounting/psi.html).
4. Errors are checked last for that resource, any reported error events.
5. The same three checks repeat for every remaining resource, in the same order, so the sweep produces a directly comparable picture across the whole system rather than a deeper look at only the resource that seemed obviously suspicious at the start.
6. A resource showing high Utilization together with rising Saturation is the strongest candidate for the actual bottleneck, and Gregg's own guidance is to look at errors and saturation first, since both are easy to interpret, and only then move to utilization, as Netflix's own performance engineering team describes applying the method in practice (https://netflixtechblog.com/linux-performance-analysis-in-60-000-milliseconds-accc10403c55).

## 8. Implementation variants

- Gregg's own Linux checklist. concrete, named commands per resource, CPU utilization and saturation from vmstat, checking the user plus system time and the run queue length against the CPU count, storage I/O saturation from iostat looking at queue size and wait time, and network errors from the interface error and drop counters (https://www.brendangregg.com/USEmethod/use-linux.html).
- A standing Prometheus and Grafana dashboard. Grafana Labs ships an official community dashboard titled USE Method, Node, built directly on Gregg's own Linux checklist and node_exporter metrics, turning the manual sweep into an always on view rather than a one off investigation (https://grafana.com/grafana/dashboards/12136-use-method-node/).
- Pressure stall information based saturation. Linux kernels with PSI support expose per resource stall statistics directly, and Prometheus's own node_exporter ships a pressure collector that exposes these figures for CPU, memory, and I/O directly from proc, giving Saturation a first class, directly measured metric rather than an inferred one (https://github.com/prometheus/node_exporter).
- A fast, manual sweep during an active incident. the shape Gregg designed it for in the first place, a short, memorized checklist an engineer runs by hand in the first minutes of an investigation, before reaching for any dashboard at all.

## 9. Known production uses

- Netflix's own Performance Engineering team documents applying the USE Method directly in production incident response, describing checking utilization, saturation, and error metrics for all resources as part of a fast, standard first pass (https://netflixtechblog.com/linux-performance-analysis-in-60-000-milliseconds-accc10403c55).
- Grafana Labs ships and maintains an official community dashboard built specifically around the USE Method for Linux nodes, a direct, named vendor implementation of the pattern (https://grafana.com/grafana/dashboards/12136-use-method-node/).
- Prometheus's own node_exporter project ships a dedicated collector for Linux pressure stall information, the modern, direct way of measuring the Saturation signal the method calls for (https://github.com/prometheus/node_exporter).

## 10. Consequences

### Benefits

- A fast, repeatable checklist finds an obvious hardware bottleneck quickly, with Gregg's own stated result, about 80 percent of server issues resolved with 5 percent of the effort a deeper investigation would otherwise take.
- The same three checks, in the same order, apply to any resource on any system, so an engineer who has run it once already knows how to run it on an unfamiliar system.
- Modern tooling, particularly Linux pressure stall information, has turned Saturation from an indirectly inferred signal into a directly measured one, closing a gap that existed when the method was first described.

### Costs

- The method explicitly does not solve every problem type, and reading every resource and metric combination for a large system takes real time, time an investigator may not have during an active incident.
- Utilization measured as an average over too coarse a window can hide a real, short lived saturation event entirely, so the measurement resolution has to be chosen carefully or the check gives a false sense of health.
- It does not apply to request driven services at all, so a team has to pair it with the RED Method or an equivalent to get a full picture across both the resource layer and the service layer.

## 11. Failure modes and misuse

- Utilization and Saturation are conflated as if they were the same measurement, when Gregg's own example shows they can diverge sharply. a resource can show a low average utilization figure over a long window while still saturating in short bursts within that same window, and only Saturation, not Utilization, reveals the real problem (https://www.brendangregg.com/usemethod.html).
- The USE Method is applied to a request driven service instead of a hardware resource, producing checks that do not map to anything the service's users actually experience, exactly the boundary the method's own creator and RED's creator both state directly (https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/).
- Saturation is skipped entirely because it seems hard to measure, when a direct measurement is often already available on the platform, Linux pressure stall information reports the share of time in which some, or all, tasks are stalled on a given resource (https://docs.kernel.org/accounting/psi.html), and skipping it in favor of Utilization alone reintroduces the exact blind spot the method exists to close.
- Time pressure during an incident leads an investigator to check only the resource that already looks suspicious and skip the rest of the sweep, which can miss the actual bottleneck sitting on a resource nobody thought to look at, the failure mode Gregg's own caveat about limited time implicitly warns against.
- Errors are checked only for the resource believed to be the problem, rather than for every resource in the sweep, so a genuine error condition on an unrelated resource goes unnoticed.

## 12. Trade-off matrix

| Dimension | USE Method | RED Method | Four golden signals |
|---|---|---|---|
| Signal count | 3, Utilization, Saturation, Errors | 3, Rate, Errors, Duration | 4, Latency, Traffic, Errors, Saturation |
| Primary scope | Hardware and infrastructure resources | Request driven services | User facing systems generally |
| Covers request rate and latency | No | Yes, its central signals | Yes |
| Best fit for CPU, disk, memory, network | Very good | Poor, does not apply to resources in this sense | Partial, via Saturation only |
| Best fit for a fleet of microservices | Poor, does not apply to services | Very good | Good, but heavier to instrument fully |

## 13. Related and incompatible patterns

Related to the RED Method, its direct counterpart, the two are usually run together rather than as alternatives, USE for the resources a service runs on and RED for the service itself, the exact split both methods' own creators describe.

Related to Structured Logging, since a standing USE dashboard depends on the same consistent field naming discipline to stay comparable across many hosts and resources over time.

Related to Correlation ID, more loosely, since correlating a resource level saturation event back to the specific requests it affected depends on the same request scoped identifier that pattern defines.

Not incompatible with anything in this catalog. it is one leg of a fuller observability setup, most useful alongside the RED Method rather than instead of it.

## 14. Refactoring path in and out

To introduce it into a team's practice, start with the manual checklist itself, the fast, memorized sweep an engineer can run by hand within the first minutes of any performance investigation, before reaching for a dashboard. Once the checklist has proven useful a few times, formalize the same checks into a standing dashboard, adopting an existing implementation such as Grafana's own USE Method node dashboard rather than building one from scratch, and wire Saturation to a direct measurement such as Linux pressure stall information where the platform supports it rather than an indirect proxy.

Removing it is rare, since it costs almost nothing once it exists as a standing dashboard, but a team migrating fully off the underlying platform it targets, for example moving entirely to a managed serverless platform with no visible host level resources to check, would retire the resource level checklist and rely on whatever the platform itself exposes instead.

## 15. Testing and verification

Verify a dashboard or checklist implementation actually covers every resource type present on the target platform, CPU, memory, every storage device, every network interface, rather than a partial list that quietly omits one, since a missed resource is a blind spot the method is specifically meant to close. Verify Saturation is collected through a real, direct mechanism, pressure stall information on a Linux platform that supports it, rather than approximated from Utilization alone, which the method's own worked example shows can hide a real problem. Verify Utilization is sampled at a fine enough time resolution to catch a short lived burst, not only a long window average, directly testing against the exact failure mode Gregg's own page names.

## 16. Observability signals

Watch Utilization trending toward its ceiling on any resource, since a resource sitting consistently near full utilization is close to becoming a bottleneck even before Saturation appears. Watch Saturation directly wherever a direct measurement exists, Linux pressure stall information's own share-of-time figures for CPU, memory, and I/O, since a rising Saturation figure is a stronger and earlier signal of a real problem than Utilization alone. Watch Errors on every resource, not only the one currently under suspicion. The strongest compound signal the method produces is high Utilization together with rising Saturation on the same resource at the same time, which is the clearest sign that resource is the actual bottleneck rather than a coincidence of measurement timing.

## 17. Security and privacy implications

Utilization, Saturation, and Errors are aggregate, resource level figures, and they carry low direct privacy risk since they describe hardware behavior rather than the content of any request or any person's data. The risk that does exist is around exposure rather than content. a detailed, publicly reachable USE style dashboard reveals a system's real capacity and current headroom, information that is genuinely useful to someone planning to exhaust a resource deliberately, so these dashboards are ordinarily kept internal, behind the same access controls as any other operational tooling, rather than published where an outside party could watch them.

## 18. References

1. Brendan Gregg's own site, the USE Method. Defines Utilization, Saturation, and Errors precisely, states the method's purpose and its stated 80 percent, 5 percent value claim, and gives the worked example distinguishing average utilization from a real saturation burst. https://www.brendangregg.com/usemethod.html, verified 2026-08-22.
2. Brendan Gregg's own site, the USE Method for Linux. A concrete, per resource checklist naming the exact commands and fields to check for CPU, memory, storage, and network. https://www.brendangregg.com/USEmethod/use-linux.html, verified 2026-08-22.
3. Netflix Technology Blog, Linux performance analysis in 60,000 milliseconds. Documents Netflix's own production application of the USE Method as a fast first pass during an investigation. https://netflixtechblog.com/linux-performance-analysis-in-60-000-milliseconds-accc10403c55, verified 2026-08-22.
4. Grafana Labs, USE Method Node dashboard. An official, named vendor dashboard implementing the method directly for Linux hosts. https://grafana.com/grafana/dashboards/12136-use-method-node/, verified 2026-08-22.
5. Grafana Labs engineering blog, the RED Method. Quotes the RED Method's own creator on why the USE Method does not apply to request driven services. https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/, verified 2026-08-22.
6. ClickHouse engineering resource hub. Explicit comparison stating USE covers the resources a service runs on while RED covers the service itself. https://clickhouse.com/resources/engineering/red-use-methods, verified 2026-08-22.
7. Google SRE book, monitoring distributed systems. Defines the four golden signals, including Saturation and Errors, the two terms the USE Method shares with that broader framework. https://sre.google/sre-book/monitoring-distributed-systems/, verified 2026-08-22.
8. Linux kernel documentation, pressure stall information. Defines PSI's some and full metrics, the modern, direct way of measuring Saturation on Linux. https://docs.kernel.org/accounting/psi.html, verified 2026-08-22.
9. Prometheus node_exporter, GitHub repository. Documents the pressure collector exposing Linux PSI based saturation statistics as Prometheus metrics. https://github.com/prometheus/node_exporter, verified 2026-08-22.

**Evidence grade.** high

**Most solid findings.** The core definitions of Utilization, Saturation, and Errors, the stated purpose, the 80 percent, 5 percent value claim, and the burst example distinguishing utilization from saturation (source 1) are quoted directly from Brendan Gregg's own site. The USE-versus-RED boundary (source 5, 6) is quoted directly from both methods' own surrounding accounts, not inferred. The modern PSI based Saturation measurement (source 8, 9) is quoted directly from the Linux kernel's own documentation and Prometheus's own node_exporter project.

**Unverified or unclear.** The exact year Brendan Gregg first published the USE Method was not independently confirmed with a live, dated source in this research pass, so the frontmatter states honestly that the first publication year is not verified rather than asserting a specific year from memory.

## Code examples

### Go, a USE Method resource checklist runner

```go
package main

import "fmt"

type resourceCheck struct {
	name              string
	utilizationPct    float64
	saturationQueue   int
	errorCount        int
}

func evaluateUSE(checks []resourceCheck) []string {
	var bottlenecks []string
	for _, c := range checks {
		if c.utilizationPct >= 90 && c.saturationQueue > 0 {
			bottlenecks = append(bottlenecks, c.name)
		}
		if c.errorCount > 0 {
			bottlenecks = append(bottlenecks, c.name+" (errors)")
		}
	}
	return bottlenecks
}

func main() {
	checks := []resourceCheck{
		{name: "cpu", utilizationPct: 95, saturationQueue: 3, errorCount: 0},
		{name: "disk0", utilizationPct: 40, saturationQueue: 0, errorCount: 0},
		{name: "eth0", utilizationPct: 10, saturationQueue: 0, errorCount: 2},
	}
	for _, b := range evaluateUSE(checks) {
		fmt.Println("bottleneck candidate:", b)
	}
}
```

### Python, a USE Method resource checklist runner

```python
from dataclasses import dataclass


@dataclass
class ResourceCheck:
    name: str
    utilization_pct: float
    saturation_queue: int
    error_count: int


def evaluate_use(checks):
    bottlenecks = []
    for c in checks:
        if c.utilization_pct >= 90 and c.saturation_queue > 0:
            bottlenecks.append(c.name)
        if c.error_count > 0:
            bottlenecks.append(f"{c.name} (errors)")
    return bottlenecks


checks = [
    ResourceCheck("cpu", 95.0, 3, 0),
    ResourceCheck("disk0", 40.0, 0, 0),
    ResourceCheck("eth0", 10.0, 0, 2),
]
for name in evaluate_use(checks):
    print("bottleneck candidate:", name)
```

### TypeScript, a USE Method resource checklist runner

```typescript
interface ResourceCheck {
  name: string;
  utilizationPct: number;
  saturationQueue: number;
  errorCount: number;
}

function evaluateUSE(checks: ResourceCheck[]): string[] {
  const bottlenecks: string[] = [];
  for (const c of checks) {
    if (c.utilizationPct >= 90 && c.saturationQueue > 0) {
      bottlenecks.push(c.name);
    }
    if (c.errorCount > 0) {
      bottlenecks.push(`${c.name} (errors)`);
    }
  }
  return bottlenecks;
}

const checks: ResourceCheck[] = [
  {name: "cpu", utilizationPct: 95, saturationQueue: 3, errorCount: 0},
  {name: "disk0", utilizationPct: 40, saturationQueue: 0, errorCount: 0},
  {name: "eth0", utilizationPct: 10, saturationQueue: 0, errorCount: 2},
];
for (const name of evaluateUSE(checks)) {
  console.log("bottleneck candidate:", name);
}
```
