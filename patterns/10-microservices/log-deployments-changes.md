---
name: Log Deployments and Changes
slug: log-deployments-changes
family: 10-microservices
category: Observability
aliases: [Deployment Markers, Deploy Events, Change Annotations, Change Correlation Logging]
first_described: "Chris Richardson, microservices.io, 2026"
maturity: established
related: [log-aggregation, application-metrics, distributed-tracing, audit-logging, health-check-api]
incompatible_with: []
verified: 2026-08-04
---

# Log Deployments and Changes

## 1. Name, aliases, and lineage

The canonical name for this pattern is Log Deployments and Changes. It is documented by Chris Richardson on microservices.io, in the Observability section of the pattern catalog that accompanies his book *Microservices Patterns* (Manning, 2019). The page states the solution plainly as "Log every deployment and every change to the (production) environment," and lists the benefit as enabling "deployments and changes to be easily correlated with issues leading to faster resolution" ([microservices.io, Log deployments and changes](https://microservices.io/patterns/observability/log-deployments-and-changes.html), verified 2026-08-04). The catalog credits AWS CloudTrail as a worked example of the idea, an audit log of every API call against an AWS account, used the same way an application team would use a deploy event stream.

The pattern does not appear as a numbered, page-cited pattern inside the printed edition of *Microservices Patterns*. A search of the book's table of contents for chapter 11, which covers building services fit to run in production, turns up Health Check API, Log Aggregation, Distributed Tracing, Application Metrics, Exception Tracking, and Audit Logging as the named observability patterns in the book itself ([Manning livebook, Chapter 11](https://livebook.manning.com/book/microservices-patterns/chapter-11), verified 2026-08-04). Log Deployments and Changes lives on the companion site as a standalone catalog entry. This entry treats it as an established, widely practiced pattern rather than a canonical, book-page-cited one, and every claim about its shape below is checked against a named tool that actually implements it, not against the catalog description alone.

Several names describe the same idea across different vendor toolchains, and a reader moving between vendors benefits from knowing they are synonyms.

- **Deployment marker** or **deploy marker.** The term used by dashboarding and APM tools (Datadog, Grafana, New Relic) for a vertical line drawn on a time series graph at the moment a deploy happened.
- **Deploy event.** The term used by pipeline and messaging systems for the discrete record emitted when a rollout starts or finishes.
- **Change annotation.** The term used when the scope is widened past code deploys to configuration changes, feature flag flips, and schema migrations, all of which are changes to a live system even though none of them ships a new binary.
- **Release.** Sentry's term for the entity that ties a specific build to the environments it has been deployed into, and the anchor for its error and regression correlation ([Sentry, Releases](https://docs.sentry.io/product/releases/), verified 2026-08-04).

A useful distinction separates this pattern from two neighbors it is frequently confused with. Audit Logging records who did what to which resource for compliance and forensics, and its audience is typically a security or compliance reviewer working after the fact. Log Deployments and Changes records the narrower fact that the running system itself changed, and its primary audience is an on-call engineer working during an active incident, at the moment they are asking the single most common incident question, what changed recently. The two patterns often share infrastructure, an audit log can double as a change log if it captures deploy and config events, but they are read by different people under different time pressure, and conflating them is a common design mistake covered under dimension 11.

## 2. Problem and context

An engineer is paged. A service that was healthy an hour ago now returns higher error rates, or its latency has doubled, or a queue is backing up. The single most productive question available to that engineer, before reading a single stack trace, is whether anything changed in the system recently, because in aggregate most production incidents trace back to a change rather than to a pre-existing, dormant bug being triggered by traffic alone.

This is not intuition. Google's site reliability engineering practice states the finding directly. "SRE has found that roughly 70% of outages are due to changes in a live system," according to the Google SRE Book ([Introduction](https://sre.google/sre-book/introduction/), verified 2026-08-04). The same finding motivates Google's error budget policy, which treats the rate of change as the primary dial an organization can turn to trade feature velocity against reliability. A number that high means that for the majority of incidents, the fastest path to mitigation is not root-causing the failure mode from first principles, it is finding the most recent change to the affected service or its dependencies and asking whether reverting it removes the symptom.

The trouble is that in a microservice system this question is hard to answer quickly by any method other than deliberate instrumentation. A single logical release might touch a dozen independently deployable services, each on its own pipeline, each with its own deploy cadence, some deploying multiple times a day. The person paged for the incident is rarely the person who ran any specific deploy, and is often on a different team than the services upstream or downstream of the one alerting. Slack scrollback, a CI dashboard that only shows the last few runs per repository, and a shared spreadsheet of planned releases are the tools teams reach for by default, and all three degrade badly under time pressure, at 3 AM, and across organizational boundaries.

The context that makes this pattern necessary has three parts that mirror the shape of the problem.

- Changes to a live system, not bugs discovered at write time, are the dominant proximate cause of user-visible incidents, per the finding above.
- A microservice architecture multiplies the number of independently deployable units, and therefore multiplies the number of places a change can originate from, well past what a single person can hold in their head.
- The person diagnosing an incident is frequently not the person who made the most recent change, and does not have privileged access to that person's local knowledge of what shipped.

Outside that context, in a monolith deployed by one team on one cadence, the same information exists but the cost of finding it is much lower, the deploy log of one pipeline is the whole picture, and a lighter-weight version of this pattern, or none at all, is often sufficient. See dimension 4 for where the pattern earns its keep and where it does not.

## 3. Forces

The pattern balances several pressures that pull against each other, and naming which side each one favors is more useful than a list that pretends the pattern is free.

- **Time to diagnosis.** Strongly favored. This is the entire reason the pattern exists. A responder who can answer "what changed" in seconds rather than minutes closes incidents faster, and every minute of mean time to recovery has a real cost in a paged organization.
- **Instrumentation coupling.** Sacrificed to a degree. Every deploy pipeline, GitOps controller, and manual `kubectl apply` now carries a responsibility beyond its primary job, emitting an event about itself. A pipeline step that silently fails to emit degrades the pattern without failing the deploy, which is a subtle new failure mode layered onto an existing system.
- **Signal to noise ratio.** Sacrificed if applied carelessly, favored if applied at the right granularity. A dashboard with one marker per logical rollout is a signal. The same dashboard with one marker per pod restart across a hundred replicas during a rolling update is noise that trains engineers to stop looking at the markers, which defeats the pattern entirely. See dimension 11.
- **Event volume and storage cost.** Mildly sacrificed. Every event carries at minimum a service name, a version, an environment, and a timestamp, and at scale, on a system deploying hundreds of times a day across hundreds of services, that is a real and growing time series or log volume that a retention policy has to account for.
- **Blast radius awareness.** Favored. Because the event is tied to a specific service and environment, the pattern narrows the search space for an incident to the services that actually changed, rather than every service that could theoretically be involved, which is a direct reduction in cognitive load during an incident.
- **Accountability and trust.** Favored for legitimate use, a real tension for security. Recording who deployed what is valuable for accountability and post-incident review, and the same data is sensitive personal information and, if writable by an untrusted actor, a vector for hiding a real change inside a flood of fake ones. See dimension 17.
- **Coverage completeness.** Sacrificed by default, and this is the pattern's most common practical failure. "Deployments" is the easy 80%, an artifact push through a known pipeline. "Changes" is the harder 20%, a feature flag flip, a database migration, a manual configuration edit, an infrastructure change, and each of those needs its own emission point, which is easy to skip when the pattern is scoped narrowly at adoption time.

No pattern that traded away nothing would be worth naming. Here the price is paid in pipeline coupling, storage volume, and the discipline required to keep the definition of "change" wide enough to be useful.

## 4. Applicability and non-applicability

Reach for Log Deployments and Changes when the following hold.

- More than one team or more than one independently deployable service exists, so a single person's memory of recent changes is not sufficient to answer "what changed" during an incident.
- Deploys and configuration changes happen frequently enough, more than roughly weekly per service, that a manual release calendar or changelog becomes stale faster than anyone maintains it.
- The organization already has, or is willing to build, a time series dashboard or log aggregation system that can display the deploy events next to the metrics they might have affected. The pattern's value is almost entirely in that correlation view, an event log nobody looks at during an incident earns nothing.
- Post-incident reviews repeatedly conclude "we should have known this deployed before we paged," which is the direct symptom this pattern is built to remove.
- The system is subject to change failure rate and mean time to recovery targets, the stability half of the four DORA metrics identified by Nicole Forsgren, Jez Humble, and Gene Kim, *Accelerate, The Science of Lean Software and DevOps* (IT Revolution Press, 2018), because a reliable change log is a prerequisite for computing failed deployment recovery time honestly rather than by guesswork.

Do NOT reach for this pattern, or reach for a lighter version of it, in the following cases, and the reason matters more than the rule.

- **A single team owns a single deployable unit and reads its own deploy log as a matter of habit.** The pipeline's own history page already answers "what changed" for that one unit, and wiring a separate event stream duplicates information that already exists in an accessible place. Add the pattern when a second team, or a second deployable unit whose changes affect the first, enters the picture.
- **The system changes so rarely, quarterly or less, that a manually maintained changelog entry per release is not a maintenance burden.** Automated event emission is solving a scaling problem that does not yet exist, and the pipeline plumbing costs more than the manual alternative it replaces.
- **The goal is compliance evidence for auditors, not incident diagnosis speed.** That is Audit Logging's job, and it has stricter requirements around immutability, retention period, and access control than a deploy marker on a dashboard typically carries. Building one system to serve both goals, without deliberately meeting the stricter of the two requirement sets, under-serves the compliance use case. See dimension 17.
- **The team cannot yet reliably compute or trust deployment timestamps because the pipeline itself is flaky, retries silently, or reports success before work actually lands.** Wiring an event emitter on top of an unreliable pipeline produces a change log that lies, and a change log a responder learns to distrust is worse than no change log, because it still costs attention to check and dismiss.
- **The change is entirely internal to a build tool with no runtime effect, a linter version bump, a CI cache key change, a README edit.** Logging every commit as a change event, rather than every change to the running production environment, produces the noise failure described under dimension 3 and buries the events that matter.
- **A GitOps controller already reconciles from a Git history that is itself a complete, timestamped, attributable record of every change**, and the team's actual practice is to read that Git log during incidents rather than a dashboard. In that case the pattern already exists in a different shape, see the GitOps variant under dimension 8, and building a parallel event stream is redundant unless the correlation view against metrics is specifically missing.
- **The event pipeline itself would become a single point of failure that can block or slow the deploy it is describing.** If emitting the change event is a synchronous, blocking call inside the critical path of the deploy, an outage in the logging backend now causes deploy failures for a system trying to become more reliable, which is precisely backwards. See the fire-and-forget guidance in dimension 8 and the test in dimension 15.

## 5. Structure

Five participants, named by the role each plays rather than by a specific vendor's product name.

- **Change Origin.** Whatever actually performs the change to the running system. In practice this is a CI/CD pipeline stage, a GitOps reconciler such as Argo CD or Flux applying a new commit, a human running `kubectl set image` or `terraform apply`, or a feature flag service flipping a flag. The Change Origin is the only participant that has first-hand, authoritative knowledge of exactly what changed and when.
- **Change Event.** The structured record the Change Origin produces, or that is derived from it. At minimum it carries a subject, the service or resource that changed, a version or change identifier, an environment, a timestamp, and an actor. It is the payload every other participant consumes.
- **Event Sink.** Where the Change Event is sent. This might be a metrics backend that accepts annotations (Datadog, Grafana, New Relic), a dedicated release entity in an error tracker (Sentry), a log aggregator that indexes the event alongside application logs, or a resource attribute attached to every subsequent telemetry emission from the changed service (OpenTelemetry's `deployment.environment.name`, see dimension 9). A mature deployment often writes to more than one sink for the same event, because different responders look in different places.
- **Change Ledger.** The durable, queryable store the Event Sink persists into, and the thing a responder actually queries during an incident. This is a time series database's annotation table, a log index, or a dedicated deployments API resource such as GitHub's Deployment and Deployment Status objects. The Change Ledger is what survives after the Change Origin process has exited.
- **Correlator.** The tool or the human process that overlays Change Ledger entries against the metrics, logs, or traces from around the same time window, and surfaces the overlap. This might be a dashboard that literally draws a vertical line on a graph, an alerting rule that annotates a page with "last deploy 4 minutes ago," or an incident commander's habit of pulling up the deploy log as the first step of triage. The Correlator is where the pattern pays off, everything upstream of it exists only to feed this step.

The relationship worth naming explicitly is that the Change Origin depends on the Event Sink's API, not the other way around, and that dependency must be one-directional and non-blocking, see dimension 8. The Correlator depends on the Change Ledger's schema being consistent across every Change Origin that writes to it, which is the coordination cost the pattern imposes across teams, every emitter has to agree on what fields a Change Event carries.

## 6. ASCII structure diagram

```
+---------------------+
| Change Origin       |
| CI/CD pipeline      |
| GitOps reconciler   |
| kubectl / terraform |
| feature flag flip   |
+---------------------+
     | emits
     v
+-----------------------------------+
| Change Event                      |
| subject, version/sha, environment |
| actor, timestamp                  |
+-----------------------------------+
     | writes
     v
+-------------------+
| Event Sink        |
| metrics annotator |
| log aggregator    |
| release tracker   |
| audit log         |
+-------------------+
     | persists
     v
+------------------------------------------------+
| Change Ledger                                  |
| queryable history of every change, per service |
| and environment                                |
+------------------------------------------------+
     | queried by
     v
+----------------------------------------+
| Correlator                             |
| overlays events on metrics/logs/traces |
| surfaces what changed recently         |
+----------------------------------------+
     ^
     |
+------------------------------+
| Responder (on-call engineer) |
+------------------------------+
```

## 7. Dynamics

The common path, described as a sequence, starts well before an incident and pays off during one.

```
Pipeline    Change Origin    Event Sink    Change Ledger    Correlator    Responder
   |              |               |              |               |            |
   | build        |               |              |               |            |
   |------------->|               |              |               |            |
   |              | deploy vN     |               |               |            |
   |              | to prod-east  |               |               |            |
   |              |               |              |               |            |
   |              | emit event    |               |               |            |
   |              |-------------->|              |               |            |
   |              |   (fire and forget, does not block deploy)   |            |
   |              |               | store event   |               |            |
   |              |               |-------------->|               |            |
   |              |               |               |               |            |
   |              |               |               |   ...time passes...       |
   |              |               |               |               |            |
   |              |               |               |               |  alert fires
   |              |               |               |               |<-----------|
   |              |               |               |               |            |
   |              |               |               |  query window |            |
   |              |               |               |<--------------|            |
   |              |               |               |  vN deployed  |            |
   |              |               |               |  4 min ago    |            |
   |              |               |               |-------------->|            |
   |              |               |               |               | show marker|
   |              |               |               |               |----------->|
   |              |               |               |               |            |
   |              |               |               |               |  responder confirms
   |              |               |               |               |  correlation, decides
   |              |               |               |               |  rollback or continue
```

Two properties of this flow are load-bearing and worth stating outside the diagram. The event emission from the Change Origin to the Event Sink happens off the critical deploy path, so a slow or unavailable sink degrades the pattern's usefulness for that one deploy but never delays or fails the deploy itself, see dimension 8 for the fire-and-forget implementation and dimension 15 for the failure injection test that proves it. The query from Correlator to Change Ledger happens on demand, driven by the responder, rather than as a standing push notification for every change, because pushing every change to every responder for every service defeats the pattern the same way an over-granular event does under dimension 3, the responder needs to pull the specific window around their specific incident, not receive a firehose.

A second, less common but equally important dynamic is the rollback path, where the Correlator's answer changes the outcome. If the responder confirms the timing correlation and the symptom disappears after reverting to the previous version, the same event stream typically records the rollback itself as a new Change Event, closing the loop and leaving an accurate record for the postmortem, rather than leaving the ledger showing only the change that caused the incident and silently omitting the fix.

## 8. Implementation variants

The pattern takes several concrete shapes in practice, and the right one for a given team depends heavily on what observability stack already exists.

- **Pseudo-metric increment.** The earliest documented form, from Etsy's engineering culture around StatsD and Graphite in 2011, treats a deploy as one more counter, incremented at deploy time and displayed as a line on the same graph as request rate or error rate, so a change in the graph's shape lines up visually with the counter's spike ([Etsy, Code as Craft, Measure Anything, Measure Everything](https://www.etsy.com/codeascraft/measure-anything-measure-everything/), verified 2026-08-04). This is the cheapest variant to build, it needs no new API, only an existing metrics pipeline, and it is the ancestor of every first-class deployment marker feature that followed.
- **First-class annotation API.** Modern APM and dashboarding tools expose a dedicated endpoint or UI concept for this exact use case rather than overloading the metrics pipeline. Datadog's Deployment Tracking correlates a `version` tag against infrastructure metrics, traces, profiles, and logs, and offers automatic faulty deployment detection that flags a rollout whose error rate diverges from its predecessor's ([Datadog, Deployment Tracking](https://docs.datadoghq.com/tracing/services/deployment_tracking/), verified 2026-08-04). This variant costs more to integrate, it usually needs the deploy tool to call a specific API with specific tags, but it produces a purpose-built correlation view rather than a graph the team has to interpret by eye.
- **Release entity in an error tracker.** Sentry's Releases tie a version identifier to the environments it has shipped to, and once an event stream is tagged with that release, Sentry can identify new issues and regressions, determine whether an issue is resolved by a later release, and predict which commit and which author is likely responsible for a given error ([Sentry, Releases](https://docs.sentry.io/product/releases/), verified 2026-08-04). This variant is specific to error and exception correlation rather than general metrics correlation, and pairs naturally with the Exception Tracking pattern.
- **Platform-native rollout history.** Kubernetes Deployments keep a revision history, queryable with `kubectl rollout history`, and a `kubernetes.io/change-cause` annotation can record why a given revision was created, which shows up against each entry in that history ([Kubernetes, Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/), verified 2026-08-04). The `--record` flag that once auto-populated this annotation from the triggering command is deprecated, so a current pipeline must set the annotation explicitly, either with `kubectl annotate deployments.apps <name> kubernetes.io/change-cause="<reason>"` or by templating it directly into the manifest, and a team that still relies on `--record` in a script inherited from an older Kubernetes version will find the annotation quietly stops populating ([kubernetes/kubernetes issue #40422, deprecate and remove --record](https://github.com/kubernetes/kubernetes/issues/40422), verified 2026-08-04). This variant is free, it needs no external service, but it only covers Kubernetes-managed resources and only surfaces inside `kubectl`, not on a dashboard, unless something else scrapes it out.
- **Deployment platform API as the ledger.** GitHub's Deployments API models a deployment as a request to deploy a specific ref, with a sequence of statuses, pending, in progress, success, failure, each of which can carry a description and a log URL, and creating a new active deployment automatically marks prior deployments to the same environment inactive, which gives a de facto timeline per environment for free ([GitHub, Deployments API](https://docs.github.com/en/rest/deployments/deployments), verified 2026-08-04). This variant is attractive when the deploy pipeline already runs as a GitHub Action, because the ledger is a byproduct of the deploy mechanism rather than a separate system to stand up.
- **Resource attribute on every subsequent signal, rather than a discrete event.** OpenTelemetry's semantic conventions define `deployment.environment.name` as a resource attribute, attached once at process startup and then carried on every metric, log, and trace that process emits for its lifetime, with the explicit note that this attribute does not itself identify the deployment as a unique entity, it distinguishes environments such as staging and production so telemetry from the same logical service is not conflated across them ([OpenTelemetry, Deployment resource semantic conventions](https://opentelemetry.io/docs/specs/semconv/resource/deployment-environment/), verified 2026-08-04). Paired with a `service.version` resource attribute set to the build's git sha, this variant turns every existing signal into an implicit change record without a separate emission step, at the cost of needing a query engine that can diff "which version was tagged on the signals in this time window" rather than reading a purpose-built timeline.
- **Audit trail as the change log.** AWS CloudTrail logs every API call made against an account, and a team that treats infrastructure changes, not only application deploys, as the changes worth correlating can query CloudTrail for the window around an incident to see whether a security group, an IAM policy, or a load balancer configuration changed, independent of whether the application code changed at all ([microservices.io, Log deployments and changes](https://microservices.io/patterns/observability/log-deployments-and-changes.html), verified 2026-08-04). This variant is the widest in scope and the least application-aware, it will not tell a responder which service version shipped, only that something in the account's control plane moved.
- **GitOps commit history as the implicit ledger.** When a reconciler such as Argo CD or Flux applies the desired state described in a Git repository, the repository's own commit history, author, timestamp, and message, is already a change log, and the reconciler's own sync history adds the "when did this actually land in the cluster" half that Git alone cannot answer, since a commit's timestamp is not the same as its rollout timestamp. This variant needs no new event schema, it needs the team to actually look at two existing systems together during an incident, which is a habit to build rather than a system to build.

## 9. Known production uses

- **GitHub Deployments API.** Models deployments as first-class resources with status transitions and per-environment history, used as the deployment ledger by any pipeline running through GitHub Actions or a third-party deployment tool that integrates with it ([docs.github.com/en/rest/deployments/deployments](https://docs.github.com/en/rest/deployments/deployments), verified 2026-08-04).
- **Kubernetes Deployment rollout history.** Every Deployment object retains revision history and an optional `change-cause` annotation, queryable with `kubectl rollout history`, used across essentially every organization running application workloads on Kubernetes ([kubernetes.io/docs/concepts/workloads/controllers/deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/), verified 2026-08-04).
- **Sentry Releases.** Ties error and performance data to the specific build that produced them, used by teams instrumenting JavaScript, Python, mobile, and backend applications with Sentry across thousands of organizations, to identify which release introduced a regression and predict the responsible commit ([docs.sentry.io/product/releases](https://docs.sentry.io/product/releases/), verified 2026-08-04).
- **Datadog Deployment Tracking.** Correlates a service's `version` tag against its own request volume, error rate, latency, and profiling data, and includes an automatic faulty deployment detector, used by Datadog's application performance monitoring customers to spot regressions introduced by a specific rollout without a manual dashboard comparison ([docs.datadoghq.com/tracing/services/deployment_tracking](https://docs.datadoghq.com/tracing/services/deployment_tracking/), verified 2026-08-04).
- **Etsy's StatsD-based deploy markers.** The 2011 Code as Craft post describing Etsy's culture of instrumenting everything, including deploys, over Graphite is widely credited as the origin of the lightweight "deploy as a metric" variant that every later first-class annotation feature builds on ([etsy.com/codeascraft/measure-anything-measure-everything](https://www.etsy.com/codeascraft/measure-anything-measure-everything/), verified 2026-08-04).
- **OpenTelemetry semantic conventions.** Standardizes `deployment.environment.name` as a resource attribute so that any OpenTelemetry-instrumented service, regardless of vendor backend, carries its deployment environment on every metric, log, and trace, adopted across dozens of OpenTelemetry language SDKs and backend integrations ([opentelemetry.io/docs/specs/semconv/resource/deployment-environment](https://opentelemetry.io/docs/specs/semconv/resource/deployment-environment/), verified 2026-08-04).
- **AWS CloudTrail.** Logs every control-plane API call against an AWS account, used by the microservices.io catalog itself as the reference example for logging changes at the infrastructure layer rather than only the application deploy layer ([microservices.io/patterns/observability/log-deployments-and-changes](https://microservices.io/patterns/observability/log-deployments-and-changes.html), verified 2026-08-04).

## 10. Consequences

**Positive.**

- Cuts the time to the first useful hypothesis during an incident, because "what changed" is answered by a query rather than by tribal knowledge or a search through chat history.
- Shifts a team's diagnostic default from "read the stack trace first" to "check for a recent change first," which matches the empirical shape of where most incidents actually originate.
- Produces a durable record that a post-incident review can cite precisely, turning "we think a deploy caused this" into "deploy of version X to prod-east at 14:02 UTC preceded the alert by four minutes," which makes the resulting action item, and the resulting change to the pipeline or review process, specific rather than vague.
- Composes naturally with the four DORA metrics, deployment frequency and lead time for changes are trivially derivable from the Change Ledger once it exists, and change failure rate becomes computable rather than estimated once every deploy and every incident are both recorded events that can be joined on time.
- Gives new team members, and engineers supporting a service they do not own, a way to answer "what changed" without needing the specific tribal knowledge of who owns which pipeline.

**Negative.**

- Adds a new coupling point, every deploy mechanism, human or automated, now has a second responsibility, emitting an accurate event, and a mechanism that forgets to do so degrades silently rather than failing loudly, see dimension 11.
- Costs storage and query capacity proportional to deploy frequency, which at high deploy cadence across many services is a real and growing line item, not a one-time setup cost.
- Requires cross-team schema agreement, every Change Origin has to emit fields the Correlator can rely on consistently, which is a coordination cost that grows with the number of independently deployed services and pipelines.
- If scoped only to application deploys, misses the "changes" half of the pattern's own name, configuration edits, feature flag flips, and infrastructure changes, leaving a gap that surfaces exactly during the incidents where those other kinds of change are the actual cause.
- Introduces a new sensitive data surface, the actor field records who deployed what, which is useful for accountability and dangerous if exposed too broadly or writable by an untrusted party, see dimension 17.

## 11. Failure modes and misuse

Each entry names the symptom a responder would actually observe, the underlying cause, and the fix, because the abstract mistake alone rarely helps someone debugging their own instance of it.

- **Symptom.** An incident timeline shows no deploy marker even though the on-call engineer knows a deploy happened around that time. **Cause.** The event emission step lives inside the deploy script itself, after the artifact is already live, and a crash, timeout, or network blip between the artifact landing and the emission call running means the deploy succeeded but the event never fired, and nothing noticed the mismatch. **Fix.** Emit the event from the orchestrator's own definition of deploy completion, a webhook the CI/CD platform fires on pipeline success rather than a step inside the pipeline that can be skipped by an early exit, and alert on a mismatch between the count of successful pipeline runs and the count of Change Events received for the same window.

- **Symptom.** Two services show a deploy marker at the same minute, but a responder cannot tell from the ledger which git commit or build each one actually shipped. **Cause.** The event schema records a boolean "deployed" fact per service without an immutable version identifier attached, often because the field was added as an afterthought to an existing generic metrics pipeline. **Fix.** Require every Change Event to carry a version field that is either a git sha or an equivalent immutable build identifier, never a mutable label like "latest" or a semver tag that could be reused, and reject events at the sink that omit it.

- **Symptom.** Engineers stop looking at the deploy markers on the dashboard within a few weeks of the feature launching. **Cause.** The events are emitted per replica or per canary step during a rolling update rather than once per logical rollout, so a single deploy produces dozens of markers, which trains the team to tune the signal out. **Fix.** Coalesce events at the orchestrator level, one event per rollout that reaches its target state, not one per underlying pod or task restart, and treat the raw per-replica events, if the platform emits them, as internal detail the sink aggregates rather than as the thing the responder queries.

- **Symptom.** A correlation query says no deploy happened in the ten minutes before an incident, but a later manual check finds one did, off by roughly a minute or two. **Cause.** The Change Event's timestamp was set client-side, on the machine or container running the deploy step, whose clock has drifted from the metrics backend's clock, and the drift is small enough to hide most of the time but large enough to occasionally push an event slightly outside the query window a responder checks. **Fix.** Timestamp the event server-side, at the moment the Event Sink receives it, not client-side at the moment the Change Origin sends it, and monitor clock skew across the fleet as its own signal if client-side timestamps must be trusted for any reason.

- **Symptom.** A change-correlated incident review keeps concluding "nothing deployed, so it must not have been a change," even though the postmortem later finds that a feature flag was flipped or a config value was edited manually right before the incident. **Cause.** The pattern was implemented narrowly as "log deployments" rather than "log deployments and changes," so the emission points only cover the CI/CD pipeline and never touch the feature flag service, the config management tool, or manual infrastructure edits, leaving exactly the kind of change that has no artifact and no pipeline run outside the ledger's visibility. **Fix.** Treat every system capable of altering production behavior, flags, config stores, schema migrations, manual `kubectl` or `terraform` runs, as a Change Origin in its own right, with its own emission point into the same Change Ledger, and audit periodically for a new change surface that was added to the system but never wired in.

- **Symptom.** The Change Ledger shows a deploy of version X, but the version that was actually running in production at the time of the incident, confirmed after the fact from a container image digest, was version Y. **Cause.** The event was emitted at the moment the deploy pipeline started or at the moment it was scheduled, rather than at the moment the new version actually became the one receiving traffic, which under a rolling or canary deployment strategy can be minutes or, if a rollout stalls, much longer after the event fired. **Fix.** Emit the Change Event when the orchestrator confirms the rollout has reached its target ready state and is receiving traffic, using the platform's own readiness signal, a Kubernetes rollout status check or an equivalent, rather than at pipeline start, and treat a rollout that never confirms completion as its own alertable condition.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3, on a scale of favors, neutral, or sacrifices.

| Force | Log Deployments and Changes | Distributed Tracing alone | Log Aggregation, ad hoc search | Audit Logging, general purpose | GitOps commit history only | Tribal knowledge, no tooling |
|---|---|---|---|---|---|---|
| Time to diagnosis | Favors, purpose-built for this exact question | Neutral, shows request flow, not which version handled it | Sacrifices, requires knowing what to search for | Neutral, wide scope makes deploys hard to isolate from other events | Sacrifices, needs a person to correlate a commit timestamp with a rollout timestamp by hand | Sacrifices heavily, depends entirely on who is paged |
| Instrumentation coupling | Sacrifices moderately, every Change Origin gains a responsibility | Sacrifices heavily, needs tracing context propagated through every hop | Neutral, logs already exist for other reasons | Sacrifices, needs compliance-grade emission from every writable resource | Favors, the record is a byproduct of the deploy mechanism itself | Favors, nothing to build |
| Signal to noise | Favors when scoped at rollout granularity, sacrifices if not | Sacrifices, trace volume at scale is enormous and needs sampling | Sacrifices, deploy lines are buried in general application noise | Sacrifices, audit events cover far more than production changes | Favors, commit history is naturally coarse | Sacrifices, no signal at all, only memory |
| Coverage of non-deploy changes | Favors only if scoped to include flags, config, and infra per dimension 11 | Sacrifices, traces only see requests, not the changes behind them | Neutral, whatever gets logged gets logged | Favors, general purpose audit covers most writable actions | Sacrifices, only covers what is committed to the Git repo the reconciler watches | Sacrifices, entirely dependent on whether anyone remembers |
| Cost at scale | Sacrifices moderately, grows with deploy frequency | Sacrifices heavily, grows with request volume | Favors, reuses existing log pipeline | Sacrifices, compliance-grade retention is expensive | Favors, Git storage is cheap and already paid for | Favors, no infrastructure cost, high human cost instead |
| Accountability, who changed what | Favors, actor field is part of the schema | Sacrifices, traces do not carry deploy actor information | Neutral, depends on whether the log line includes an actor | Favors strongly, this is audit logging's primary purpose | Favors, Git commit author is built in | Sacrifices, no record exists to check |

Distributed Tracing and Log Aggregation are listed because they are the two patterns most often mistaken for a substitute for this one, a team with good tracing sometimes assumes it does not need deployment markers, but a trace shows what a request did, never what version of the code did it or when that version arrived, which is the gap this pattern closes.

## 13. Related and incompatible patterns

- **Log Aggregation.** The two compose directly, the Change Ledger is frequently the same log aggregation backend the application's own logs already flow into, with deploy events indexed alongside them and distinguishable by a log type or source field. A team that has already adopted Log Aggregation has the cheapest possible path to adding this pattern, one new event type into an existing pipeline.
- **Application Metrics.** The pseudo-metric variant, dimension 8, is a direct instance of Application Metrics applied to the deploy event itself, and even in the first-class annotation variant, the value of a Change Event is realized almost entirely when it is displayed alongside a metric's time series, so the two patterns are usually adopted together in practice even when they are built by different subsystems.
- **Distributed Tracing.** Complementary rather than overlapping. Once a Change Event establishes that a particular version was live during an incident window, distributed tracing can then explain the specific request path that failed within that version, answering "what changed" and "what broke" as two separate, sequential questions rather than one.
- **Audit Logging.** A near neighbor with a different audience and different guarantees, covered in detail under dimension 1 and dimension 17. The two can share underlying storage but should not share the exact same schema or access policy without deliberately meeting the stricter of the two requirement sets.
- **Health Check API.** A Change Event answers "what changed," a health check answers "is it healthy right now," and a Correlator often uses both together, confirming that a service's health check started failing shortly after a Change Event for that same service, which is a stronger signal than either alone.
- **Circuit Breaker and canary release strategies.** Not listed as formally related because they operate on the runtime request path rather than the observability layer, but they are frequently the mechanism a team reaches for once change correlation data shows that a specific class of deploy repeatedly precedes incidents, a Change Ledger populated over months is often the evidence that justifies investing in automated canary analysis.

No pattern in this catalog is incompatible with Log Deployments and Changes. It has no structural conflict with any other observability, resilience, or deployment pattern, which is part of why it is inexpensive to retrofit onto an existing system that already has some of its neighbors in place.

## 14. Refactoring path in and out

**Introducing the pattern into a system that does not have it.**

1. Pick the single highest-incident-volume service and its existing deploy pipeline first, not the whole organization at once. Add one emission call at the end of that pipeline's success path, writing to whatever the team's existing metrics or log backend already is, using the pseudo-metric variant from dimension 8 if no purpose-built annotation API exists yet. This step alone, for one service, is usually a change measured in tens of lines.
2. Confirm the emission is genuinely non-blocking, per dimension 8's fire-and-forget requirement, and confirm the timestamp is set server-side at the sink, not client-side at the pipeline runner, per the clock-skew failure mode in dimension 11.
3. Wire the event into the one dashboard the team already opens first during an incident for that service, so the very next real incident is the first opportunity to see the pattern pay off, rather than shipping it into a dashboard nobody looks at.
4. Once the first service proves the pattern's value, standardize the event schema, subject, version, environment, actor, timestamp, as a shared contract, and template the emission step into whatever the organization's pipeline template or shared CI library already is, so every new service inherits it rather than needing a bespoke integration.
5. Extend the definition of Change Origin past the deploy pipeline, per the failure mode in dimension 11, adding emission points to the feature flag service, the configuration store, and any manual infrastructure change process, closing the "changes" gap the name of the pattern explicitly calls out.
6. Add the coverage check from dimension 15, alerting when the count of successful deploys from the pipeline's own system of record diverges from the count of Change Events received for the same window, so silent emission failures surface on their own rather than being discovered the next time they matter.

**Removing or consolidating the pattern.**

The pattern is rarely removed outright, a working change log almost never becomes actively harmful the way an over-engineered abstraction can, but it is commonly consolidated. A team that starts with several independent, ad hoc emitters, one script per pipeline, each hand-rolled, typically refactors toward a single shared library or a single platform team-owned service that every pipeline calls, once the number of independent emitters passes roughly a handful and schema drift between them starts producing Correlator queries that silently miss events from the emitters that used a slightly different field name. This consolidation looks like the Extract Class or Extract Service refactorings applied to the emission logic itself, moving duplicated code out of N pipeline scripts into one owned interface, and is a sign of the pattern maturing rather than a sign it should be abandoned. A team migrating fully onto a GitOps reconciler may also retire a bespoke pseudo-metric emitter in favor of reading the reconciler's own sync history plus the Git commit log, per the GitOps variant in dimension 8, when that history already covers the same ground with less code to maintain.

## 15. Testing and verification

Testing this pattern means testing three separate properties, that the event fires when it should, that it does not interfere with the deploy it describes, and that it carries the fields the Correlator actually needs.

- **Schema contract test.** A unit test against the event-building function, in whichever language the emitter is written in, asserting that every required field, subject, version, environment, actor, timestamp, is present and non-empty before the event is serialized, run in CI on every change to the emitter code itself, not only on every deploy that happens to trigger it.
- **Pipeline integration test.** A required, non-optional stage in the deploy pipeline template that fails the whole pipeline if the emission call returns a client error, a 4xx indicating the event was malformed, while a server error or timeout from the sink, a 5xx or a network failure, is caught and logged but explicitly does not fail the deploy, which is the fire-and-forget property from dimension 8 made testable rather than assumed. This distinction is the one most teams get wrong on the first attempt, treating every emission failure identically either blocks deploys on an observability outage or silently swallows a genuine schema bug.
- **Failure injection test on the sink.** A deliberate test, run periodically rather than only once at build time, that makes the Event Sink unavailable, a firewall rule, a killed process, a forced timeout, and confirms two things independently, that the deploy pipeline still completes successfully within its normal time budget, and that the emitter either retries the event later from a local fallback queue or logs the failure loudly enough that the coverage check in the next bullet catches the gap. This is the practical test of the non-blocking claim in dimension 3 and dimension 8, an emitter that only looks non-blocking in the happy path has not actually been tested for the property that matters.
- **Coverage reconciliation, run continuously in production.** A recurring job, not a one-time test, that compares the count of successful deploys reported by the pipeline's own system of record, GitHub Actions runs, Argo CD sync history, whatever it is, against the count of Change Events received by the Change Ledger for the same service and window, and alerts when the two diverge past a small tolerance. This is the single highest-value test in the whole set, because it is the only one that catches the specific, silent failure mode described first under dimension 11, an emitter that appears to work in every synthetic test but quietly stops firing in production for a reason no test anticipated.
- **Game day exercise.** A scheduled, simulated incident where a responder who did not perform the triggering change is asked to answer "what changed" using only the Correlator, timed from the start of the exercise to the moment they name the correct change. This tests the pattern from the end user's side rather than the emitter's side, and regularly surfaces usability problems, a dashboard nobody remembers exists, a query that needs an internal tool nobody outside the platform team has access to, that a purely mechanical test of the emission pipeline would never find.

## 16. Observability signals

A healthy instance of this pattern looks, on inspection, close to boring. The count of Change Events received for a service over a week tracks the count of successful pipeline runs for that same service closely, typically within a few percent, and any persistent gap larger than that is itself the signal described in dimension 15's coverage reconciliation. Each event, when inspected, carries a version field that resolves to a real, findable commit or build artifact, never a placeholder, a stale value, or an empty string. The latency between a rollout reaching its ready state and the corresponding event becoming queryable in the Change Ledger is measured in seconds, not minutes, because an event that surfaces slowly is an event a responder has often already given up waiting for and moved past. On a dashboard, deploy markers for a given service appear as a small, countable number of vertical lines per day, one per logical rollout, not a dense forest of lines that a human stops parsing, per the coalescing guidance in dimension 8 and the noise failure mode in dimension 11.

An unhealthy instance shows the inverse of each of those. A widening gap between pipeline success count and event count, which means the emission mechanism is failing silently somewhere and nobody has noticed yet. Events whose version field is present but wrong, most often because it was captured at build time from a branch name rather than at deploy time from the actual artifact that shipped, which produces confident-looking but misleading correlation results, arguably worse than a missing event because a responder trusts it. A growing minutes-long delay between rollout completion and event visibility, often the first symptom of an Event Sink that is itself under load or degraded, which is worth its own alert since a slow Change Ledger during an incident is a Change Ledger a responder will not wait for. And a dashboard so dense with markers that the team has stopped looking at it, which shows up not as an error in any system but as an answer of "we don't really use that anymore" the next time someone asks about it in a retrospective, the softest and most easily missed unhealthy signal of the set.

## 17. Security and privacy implications

The pattern's own strongest feature, recording exactly who changed what and when, is also its clearest privacy and security exposure, and the two cannot be fully separated.

The actor field is personal data. It identifies an individual employee as having performed a specific production action at a specific time, which is exactly the kind of record data protection regimes such as GDPR treat as personal data requiring a lawful basis, a retention limit, and access controls, not an indefinitely retained, broadly readable log entry. A Change Ledger that grows without a retention policy, on the theory that more history is always better for incident correlation, accumulates a long-lived record of individual employee activity that a security or privacy review will eventually have to account for, and the honest answer for most organizations is that the actor field is genuinely useful for the days or weeks after a deploy, and much less useful, while carrying the same privacy cost, a year later.

The change-cause or commit message text, when surfaced word for word into a dashboard visible to a wider audience than the original repository's access list, can leak information the original author did not intend to expose that broadly, an internal project codename, a reference to an unannounced feature, or in a worse case a credential or an internal hostname pasted into a commit message during debugging and never scrubbed. A Change Ledger that mirrors free-text fields from source control onto a dashboard with looser access controls than the source control system itself widens that exposure without anyone deciding to do so on purpose.

The event emission endpoint is itself a write path into a system responders trust during an incident, and that trust is exactly what makes it worth attacking. An unauthenticated or weakly authenticated emission API lets any party on the network write a fake Change Event, and the two attacks that follow from that are different but both real. A flood of fake, low-signal events reproduces the noise failure mode from dimension 11 deliberately, training responders to ignore the ledger during the exact window an attacker wants them distracted or slowed down. A single, carefully timed fake event, "deploy of version X at time T," planted around the time of a real, unauthorized change, gives a responder investigating an incident a plausible but false explanation to accept and stop looking further, which is a variant of the same log-injection technique used against traditional audit logs, applied here against a log responders are specifically trained to trust first. The mitigation is the same one that applies to any write path a security-sensitive process depends on, authenticate every Change Origin, prefer a short-lived token scoped to the specific pipeline or service rather than a long-lived shared secret, and treat the Change Ledger itself as an append-only, tamper-evident store, the same posture AWS CloudTrail takes for its own API call log, rather than a freely editable table.

Finally, when this pattern's Change Ledger is repurposed to also serve Audit Logging's compliance function, per the near-neighbor relationship in dimension 1, it inherits Audit Logging's stricter obligations, immutability, a defined retention period tied to a specific regulatory requirement rather than "as long as is convenient," and access controls that restrict who can read the actor field, not only who can write new events. Building one system to serve both an incident responder's need for a fast, wide-open, easy-to-query dashboard and a compliance reviewer's need for an immutable, access-controlled, retained-on-schedule record, without deciding explicitly which of those two requirement sets governs the shared store, is the single most common way this pattern's security posture ends up weaker than either use case alone would have required.

## 18. References

- Chris Richardson, "Pattern, Log deployments and changes," microservices.io, [https://microservices.io/patterns/observability/log-deployments-and-changes.html](https://microservices.io/patterns/observability/log-deployments-and-changes.html), verified 2026-08-04.
- Chris Richardson, *Microservices Patterns*, Manning, 2019, Chapter 11, on building services fit to run in production, table of contents confirmed at [https://livebook.manning.com/book/microservices-patterns/chapter-11](https://livebook.manning.com/book/microservices-patterns/chapter-11), verified 2026-08-04.
- Google, "Introduction," *Site Reliability Engineering*, [https://sre.google/sre-book/introduction/](https://sre.google/sre-book/introduction/), verified 2026-08-04, quoting "SRE has found that roughly 70% of outages are due to changes in a live system."
- GitHub, "Deployments," REST API documentation, [https://docs.github.com/en/rest/deployments/deployments](https://docs.github.com/en/rest/deployments/deployments), verified 2026-08-04.
- Kubernetes, "Deployments," [https://kubernetes.io/docs/concepts/workloads/controllers/deployment/](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/), verified 2026-08-04.
- Kubernetes project, "Deprecate and remove --record flag from kubectl," issue #40422, [https://github.com/kubernetes/kubernetes/issues/40422](https://github.com/kubernetes/kubernetes/issues/40422), verified 2026-08-04.
- Sentry, "Releases," [https://docs.sentry.io/product/releases/](https://docs.sentry.io/product/releases/), verified 2026-08-04.
- Datadog, "Deployment Tracking," [https://docs.datadoghq.com/tracing/services/deployment_tracking/](https://docs.datadoghq.com/tracing/services/deployment_tracking/), verified 2026-08-04.
- Ian Malpass, "Measure Anything, Measure Everything," Etsy Code as Craft, 2011, [https://www.etsy.com/codeascraft/measure-anything-measure-everything/](https://www.etsy.com/codeascraft/measure-anything-measure-everything/), verified 2026-08-04.
- OpenTelemetry, "Deployment," resource semantic conventions, [https://opentelemetry.io/docs/specs/semconv/resource/deployment-environment/](https://opentelemetry.io/docs/specs/semconv/resource/deployment-environment/), verified 2026-08-04.
- Nicole Forsgren, Jez Humble, and Gene Kim, *Accelerate, The Science of Lean Software and DevOps*, IT Revolution Press, 2018, on the four key metrics, deployment frequency, lead time for changes, change failure rate, and time to restore service, engineering judgement applied here to connect the metrics to the pattern's Change Ledger rather than a page-specific claim from the book.

## Code

### TypeScript

```typescript
interface ChangeEvent {
  subject: string;
  version: string;
  environment: string;
  actor: string;
  changeType: "deploy" | "config" | "flag" | "infra";
  timestamp: string;
}

interface EventSink {
  send(event: ChangeEvent): Promise<void>;
}

class FallbackQueueSink implements EventSink {
  private readonly primary: EventSink;
  private readonly queue: ChangeEvent[] = [];

  constructor(primary: EventSink) {
    this.primary = primary;
  }

  async send(event: ChangeEvent): Promise<void> {
    try {
      await this.primary.send(event);
    } catch {
      // Non-blocking. The deploy already succeeded, only the record is at risk.
      this.queue.push(event);
    }
  }

  pending(): readonly ChangeEvent[] {
    return this.queue;
  }
}

function buildDeployEvent(
  service: string,
  gitSha: string,
  environment: string,
  actor: string
): ChangeEvent {
  if (!service || !gitSha || !environment || !actor) {
    throw new Error("change event missing a required field");
  }
  return {
    subject: service,
    version: gitSha,
    environment,
    actor,
    changeType: "deploy",
    timestamp: new Date().toISOString(),
  };
}

// Fire and forget. A pipeline calls this after confirming rollout readiness,
// never before, and never awaits it on the deploy's success path.
function emitDeployEvent(sink: EventSink, event: ChangeEvent): void {
  void sink.send(event).catch(() => {
    // Swallowed here on purpose. The FallbackQueueSink already retried once.
  });
}

class LoggingSink implements EventSink {
  async send(event: ChangeEvent): Promise<void> {
    console.log(JSON.stringify(event));
  }
}

const sink = new FallbackQueueSink(new LoggingSink());
const event = buildDeployEvent("checkout-service", "a1b2c3d", "prod-east", "ci-bot");
emitDeployEvent(sink, event);
```

### Go

```go
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"os"
	"sync"
	"time"
)

type ChangeEvent struct {
	Subject     string    `json:"subject"`
	Version     string    `json:"version"`
	Environment string    `json:"environment"`
	Actor       string    `json:"actor"`
	ChangeType  string    `json:"change_type"`
	Timestamp   time.Time `json:"timestamp"`
}

func (e ChangeEvent) Validate() error {
	if e.Subject == "" || e.Version == "" || e.Environment == "" || e.Actor == "" {
		return errors.New("change event missing a required field")
	}
	return nil
}

type EventSink interface {
	Send(e ChangeEvent) error
}

// FallbackQueueSink retries once through the primary sink and, on failure,
// keeps the event for later inspection rather than losing it.
type FallbackQueueSink struct {
	primary EventSink
	mu      sync.Mutex
	pending []ChangeEvent
}

func (s *FallbackQueueSink) Send(e ChangeEvent) error {
	if err := s.primary.Send(e); err != nil {
		s.mu.Lock()
		s.pending = append(s.pending, e)
		s.mu.Unlock()
		return err
	}
	return nil
}

func (s *FallbackQueueSink) Pending() []ChangeEvent {
	s.mu.Lock()
	defer s.mu.Unlock()
	out := make([]ChangeEvent, len(s.pending))
	copy(out, s.pending)
	return out
}

type LoggingSink struct {
	logger *slog.Logger
}

func (s LoggingSink) Send(e ChangeEvent) error {
	body, err := json.Marshal(e)
	if err != nil {
		return err
	}
	s.logger.Info("change event", "payload", string(body))
	return nil
}

func BuildDeployEvent(service, gitSHA, environment, actor string) (ChangeEvent, error) {
	e := ChangeEvent{
		Subject:     service,
		Version:     gitSHA,
		Environment: environment,
		Actor:       actor,
		ChangeType:  "deploy",
		Timestamp:   time.Now().UTC(),
	}
	return e, e.Validate()
}

// EmitDeployEvent runs after the orchestrator confirms rollout readiness,
// and never on the goroutine that reports deploy success back to the caller.
func EmitDeployEvent(sink EventSink, e ChangeEvent) {
	go func() {
		_ = sink.Send(e)
	}()
}

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	sink := &FallbackQueueSink{primary: LoggingSink{logger: logger}}

	event, err := BuildDeployEvent("checkout-service", "a1b2c3d", "prod-east", "ci-bot")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	EmitDeployEvent(sink, event)
}
```

### Python

```python
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True)
class ChangeEvent:
    subject: str
    version: str
    environment: str
    actor: str
    change_type: str = "deploy"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        if not (self.subject and self.version and self.environment and self.actor):
            raise ValueError("change event missing a required field")


class EventSink(Protocol):
    def send(self, event: ChangeEvent) -> None: ...


class LoggingSink:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def send(self, event: ChangeEvent) -> None:
        self._logger.info(json.dumps(asdict(event)))


class FallbackQueueSink:
    # Wraps a primary sink and keeps a change on failure rather than
    # letting the record disappear when the sink is unavailable.
    def __init__(self, primary: EventSink) -> None:
        self._primary = primary
        self._pending: list[ChangeEvent] = []

    def send(self, event: ChangeEvent) -> None:
        try:
            self._primary.send(event)
        except Exception:
            self._pending.append(event)

    def pending(self) -> list[ChangeEvent]:
        return list(self._pending)


def build_deploy_event(
    service: str, git_sha: str, environment: str, actor: str
) -> ChangeEvent:
    return ChangeEvent(
        subject=service,
        version=git_sha,
        environment=environment,
        actor=actor,
        change_type="deploy",
    )


def emit_deploy_event(sink: EventSink, event: ChangeEvent) -> None:
    # Called after the orchestrator confirms the rollout is serving traffic,
    # never inside the block that reports deploy success to the caller.
    sink.send(event)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sink = FallbackQueueSink(LoggingSink(logging.getLogger("changes")))
    event = build_deploy_event("checkout-service", "a1b2c3d", "prod-east", "ci-bot")
    emit_deploy_event(sink, event)
```
