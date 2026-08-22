---
name: Autoscaling
slug: autoscaling
family: 08-cloud-distributed
category: Capacity Management
aliases: [Auto Scaling, Elastic Scaling, Dynamic Scaling]
first_described: "AWS Auto Scaling for Amazon EC2, announced May 2009 per the Amazon Web Services Blog, cited via Wikipedia; NIST later named rapid elasticity a defining characteristic of cloud computing in Special Publication 800-145, September 2011"
maturity: canonical
related: [load-balancing, health-endpoint-monitoring, queue-based-load-leveling, deployment-stamps, throttling, cell-based-architecture, competing-consumers]
incompatible_with: []
verified: 2026-08-22
---

# Autoscaling

## 1. Name, aliases, and lineage

The canonical name is Autoscaling, also written Auto Scaling. Vendor products use
Elastic Scaling and Dynamic Scaling as near-synonyms for the same idea.

Amazon Elastic Compute Cloud went into full production on October 23, 2008,
with AWS stating plans at the time for load balancing, autoscaling, and cloud
monitoring services still to come. Those three services, Elastic Load
Balancing, Auto Scaling, and CloudWatch, shipped together on May 18, 2009
([Wikipedia, Amazon Elastic Compute
Cloud](https://en.wikipedia.org/wiki/Amazon_Elastic_Compute_Cloud), verified
2026-08-22, citing the Amazon Web Services Blog post announcing the features).
This date rests on a secondary source, since the original AWS announcement
itself could not be fetched directly in this research pass, and is noted here
at moderate confidence rather than as a settled primary-source fact. AWS's own
current documentation confirms the same product lineage under the name Amazon
EC2 Auto Scaling, organizing instances into Auto Scaling groups
([AWS, What is Amazon EC2 Auto
Scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/what-is-amazon-ec2-auto-scaling.html),
verified 2026-08-22).

A broader industry precedent predates AWS's shipped feature by roughly eight
years. IBM initiated the autonomic computing effort in 2001, describing
self-optimization as automatic monitoring and control of resources to keep a
system running at its defined requirements ([Wikipedia, Autonomic
computing](https://en.wikipedia.org/wiki/Autonomic_computing), verified
2026-08-22). The connection between that broader research program and the
specific, named pattern of adding and removing compute instances against a
metric is indirect rather than a stated lineage, so it is presented here as a
plausible conceptual forerunner in the wider discourse about self-managing
systems, not as the origin of what AWS, Google Cloud, Azure, and Kubernetes
later built.

The National Institute of Standards and Technology later canonized the
underlying capability as one of five essential characteristics of cloud
computing itself. Special Publication 800-145 names rapid elasticity, defined
as capabilities that can be rapidly and elastically provisioned, in some
cases automatically, to scale out and scale in ([NIST Special Publication
800-145, Mell and Grance, September
2011](https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-145.pdf),
verified 2026-08-22). Since NIST's publication postdates AWS's 2009 shipped
feature by two years, the accurate framing is that NIST later named, as a
defining property of cloud computing generally, a capability AWS had already
shipped as a specific product.

## 2. Problem and context

A fixed-size pool of servers forces a choice between two costly extremes. AWS's
own guidance frames this directly with a worked example of an application that
sees midweek demand spikes. Provision for peak demand and idle capacity sits
unused on every quiet day, raising the cost of running the application.
Provision for average demand instead and the application degrades whenever
real demand exceeds it, producing a poor experience for the people using it
([AWS, Benefits of Amazon EC2 Auto
Scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/auto-scaling-benefits.md),
verified 2026-08-22). Autoscaling is the third option AWS names. add capacity
only when it is needed, and remove it again once it is not, so the running
cost tracks real demand rather than either extreme.

Google Cloud frames the same problem in terms of a resource pool's size rather
than its traffic distribution. an autoscaler adds virtual machines to a
managed instance group when load rises and deletes them when the need for
capacity falls, changing the pool's size directly rather than routing traffic
within a pool of fixed size ([Google Cloud, Autoscaling groups of
instances](https://docs.cloud.google.com/compute/docs/autoscaler), verified
2026-08-22). This is the structural distinction from Load Balancing that
matters for this family. a load balancer distributes work across whatever
pool currently exists. autoscaling decides how large that pool should be.
Neither pattern is useful without the other. a bigger pool with no traffic
distribution across it accomplishes nothing, and a load balancer with a fixed
pool cannot absorb demand beyond that pool's ceiling.

Azure's own architecture guidance states the problem in general terms.
capabilities must expand to satisfy service objectives as demand grows, then
release again as demand slackens, so cost tracks only what is actually needed
at any moment ([Microsoft Learn, Autoscaling guidance for cloud
applications](https://learn.microsoft.com/en-us/azure/architecture/best-practices/auto-scaling),
verified 2026-08-22, page dated 2022-10-11 and last updated 2026-06-04). The
same page draws a design boundary worth stating plainly. autoscaling mostly
applies to compute resources, and while a database or a message queue can in
principle be scaled horizontally too, that process usually involves
partitioning data, which is generally a manual or semi-manual undertaking
rather than something an autoscaler drives on its own.

## 3. Forces

**Cost of over-provisioning versus risk of under-provisioning.** Restated as a
force rather than the problem itself, the entire mechanism exists to keep a
pool close to right-sized on both axes at once, and every remaining force in
this section is a consequence of trying to hold that balance under real,
noisy, time-delayed conditions.

**Reaction speed versus premature judgment on a still-booting instance.** A
newly launched instance cannot serve real traffic the moment it exists. AWS's
target tracking documentation names this directly with an instance warmup
period. an instance is excluded from the group's aggregated metrics until its
warmup period expires, and while a scale-out is in progress every scale-in
action is blocked until the new instances finish warming up
([AWS, Target tracking scaling
policies](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-scaling-target-tracking.html),
verified 2026-08-22). Google Cloud documents the same idea under a different
name, the initialization period, defaulting to 60 seconds, during which a new
instance is excluded from scale-out decisions but is still counted toward
scale-in decisions, an asymmetry in the opposite direction from AWS's warmup,
which blocks scale-in entirely rather than counting the new instance toward
it ([Google Cloud, Autoscaling groups of
instances](https://docs.cloud.google.com/compute/docs/autoscaler), verified
2026-08-22). Kubernetes documents a comparable exclusion for its own metric
aggregation. a pod still initializing, or whose most recent metric point
predates it becoming ready, is set aside from the aggregate the autoscaler
reads, with a default readiness delay of 30 seconds and a default CPU
initialization period of 5 minutes ([Kubernetes, Horizontal Pod
Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/),
verified 2026-08-22).

**Thrashing, and cooldowns as the shared fix.** Three vendors independently
converge on a wait-before-undoing mechanism, at different default magnitudes.
AWS's default cooldown for simple scaling policies is 300 seconds, and it
states plainly that the intent is to let the group settle before another
scaling activity is allowed to start, though target tracking and step scaling
policies bypass this cooldown mechanism in favor of the warmup period above
([AWS, Scaling cooldowns for Amazon EC2 Auto
Scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-scaling-cooldowns.html),
verified 2026-08-22). Google Cloud's stabilization period, the mirror concept
for scale-in, defaults to 10 minutes, configurable from 0 to 3600 seconds
([Google Cloud, Autoscaling groups of
instances](https://docs.cloud.google.com/compute/docs/autoscaler), verified
2026-08-22). Kubernetes applies no stabilization window to scale-up by default
and a 5 minute window to scale-down, and additionally skips any scaling
action at all when the ratio between the current and target metric sits
within a tolerance of 0.1 around 1.0, a dead band that prevents action on
noise near the target ([Kubernetes, Horizontal Pod
Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/),
verified 2026-08-22).

**Flapping as the sharper failure this force guards against.** Azure's own
worked example is the clearest primary-source description found. with a
scale-out threshold of 50 percent CPU and a scale-in threshold of 30 percent,
two instances at 56 percent CPU scale out to three, whose average then falls
to 28 percent, which would trigger scale-in back to two, which would
immediately push the average back over the original 56 percent threshold and
trigger scale-out again, an unbroken loop. Azure documents that its own
engine detects this exact shape and defers the scale-in step rather than
executing it, checking for this condition only on the scale-in side, since
the vendor states its priority is always to favor availability over strict
cost minimization ([Microsoft Learn, Understand autoscale settings, and
Overview of autoscale flapping in Azure
Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/autoscale/autoscale-flapping),
verified 2026-08-22, page last updated 2026-08-21). Azure names small or
absent margins between thresholds, scaling by more than one instance at a
time, and using different metrics for scale-out versus scale-in as the three
concrete root causes of flapping in its own systems.

**Scale-out versus scale-up as two distinct dimensions.** Azure's guidance
states the reason vertical scaling is rarely automated. changing an
instance's own size typically requires making it briefly unavailable while it
is redeployed, whereas horizontal scaling adds or removes whole instances
while the application keeps running without interruption
([Microsoft Learn, Autoscaling guidance for cloud
applications](https://learn.microsoft.com/en-us/azure/architecture/best-practices/auto-scaling),
verified 2026-08-22). This is why every implementation surveyed in this entry
scales horizontally by default and treats vertical resizing as a separate,
narrower mechanism, covered in dimension 8.

## 4. Applicability and non-applicability

**Reach for autoscaling when.**

- Demand is cyclical, recurring, or otherwise variable in a way a fixed pool
  cannot serve cheaply at both its peak and its trough. AWS names cyclical
  business-hours traffic and recurring batch or testing workloads as the
  cases its own predictive scaling feature targets directly
  ([AWS, Predictive
  scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-predictive-scaling.html),
  verified 2026-08-22).
- The workload is stateless, or its state has already been externalized to a
  shared store, so any given instance is interchangeable and safe to add or
  remove without a data-migration step.
- Cost sensitivity to idle capacity is real, and the operational cost of
  configuring and tuning an autoscaler is worth paying against that saving.

**Do not reach for autoscaling when.**

- The workload has a hard service objective that cannot tolerate the reaction
  lag between a metric crossing its threshold and new capacity actually
  becoming healthy. Azure's own guidance names this directly, stating that
  autoscaling might not be the right mechanism for a sudden burst, since it
  takes time to bring new capacity online and peak demand can pass before
  that capacity is ready, and names Throttling as the better fit for that
  specific case ([Microsoft Learn, Autoscaling guidance for cloud
  applications](https://learn.microsoft.com/en-us/azure/architecture/best-practices/auto-scaling),
  verified 2026-08-22).
- The workload is stateful or runs long tasks that cannot be interrupted
  cleanly. Azure's same page warns that without deliberate design, a
  long-running task can prevent an instance from shutting down cleanly during
  scale-in, or can lose data if the process is terminated forcibly, and
  points to checkpointing to durable storage as the mitigation such a
  workload needs before it is a fit for autoscaling at all.
- The load is genuinely constant and predictable. no vendor source states
  this negative case directly, and it is reasoned here from the definitions
  above rather than cited. if none of the stated benefits, cost savings on
  idle capacity or absorbing variable demand, apply to a workload, a
  correctly sized fixed pool is equally cost-effective with none of the
  configuration and operational overhead, and this point should be read as
  engineering judgement, not a sourced claim.

## 5. Structure

The exact terminology differs enough across vendors to be worth naming
precisely rather than flattening into one vocabulary.

- **Metric source.** AWS reads a CloudWatch metric, predefined
  (`ASGAverageCPUUtilization`, `ALBRequestCountPerTarget`, and similar) or
  custom. Google Cloud reads CPU utilization, load balancing serving
  capacity, or a Cloud Monitoring custom metric. Kubernetes reads resource
  metrics such as CPU or memory, or a custom or external metric. Azure reads
  host metrics from the scale set itself, or metrics pushed from a storage
  account, a Service Bus queue, or Application Insights.
- **The autoscaler or controller.** AWS's Auto Scaling service acts on an
  Auto Scaling group. Kubernetes runs the Horizontal Pod Autoscaler
  controller inside the control plane, evaluating on a fixed interval.
  Google Cloud runs an autoscaler attached to a managed instance group.
  Azure evaluates autoscale settings against a Virtual Machine Scale Set or
  another supported compute resource.
- **The scaling policy.** AWS names four policy types, target tracking, step
  scaling, scheduled scaling, and predictive scaling, plus an older simple
  scaling type it now advises against in favor of target tracking. The
  `HorizontalPodAutoscaler` API resource is Kubernetes' own policy object.
  Azure organizes rules into profiles, each holding one or more threshold
  rules with its own comparison operator and cooldown.
- **The resource pool being scaled.** AWS's Auto Scaling group, a
  Kubernetes Deployment or StatefulSet's replica count, a Google Cloud
  managed instance group, or an Azure Virtual Machine Scale Set.
- **The provisioning mechanism.** In every vendor surveyed, the actual launch
  and termination of capacity is performed by the vendor's own service or
  controller directly, honoring configured minimum, maximum, and desired
  bounds. AWS's own definition states this precisely. a group never falls
  below its configured minimum, never exceeds its configured maximum, and is
  kept at its desired capacity in between ([AWS, What is Amazon EC2 Auto
  Scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/what-is-amazon-ec2-auto-scaling.html),
  verified 2026-08-22).

Azure's own architecture guidance names a structural principle worth stating
on its own, since it applies across every vendor's actual implementation even
though Azure alone states it explicitly. the components that make the scaling
decision and carry it out should be decoupled from the workload's own code,
managed as an external process, because code that is idle or already
overwhelmed is a poor place to also make its own scaling decisions
([Microsoft Learn, Autoscaling guidance for cloud
applications](https://learn.microsoft.com/en-us/azure/architecture/best-practices/auto-scaling),
verified 2026-08-22).

## 6. ASCII structure diagram

```
                       +-------------------+
                       |   Metric source    |
                       | (CPU, requests,    |
                       |  queue depth, ...) |
                       +----------+---------+
                                  |
                                  v
                       +-------------------+
                       |  Autoscaler /      |
                       |  controller        |
                       | (reads policy,     |
                       |  computes target)  |
                       +----------+---------+
                                  |
                       provisions or removes
                                  |
                                  v
          +-----------+     +-----------+      +-----------+
          | Instance A |     | Instance B |      | Instance C |
          +-----------+     +-----------+      +-----------+
                ^                 ^                  ^
                |                 |                  |
                +-----------------+------------------+
                                  |
                       +-------------------+
                       | Load balancer,     |
                       | distributes across |
                       | current pool size  |
                       +-------------------+
```

## 7. Dynamics

```
1. The metric source reports a rising value, for example CPU utilization
   climbing past a target tracking threshold.
2. The autoscaler evaluates its policy against the current pool size and
   computes a new desired capacity above the current count.
3. The autoscaler requests new capacity from the provisioning layer, which
   launches new instances or pods.
4. Each new instance is excluded from the aggregated metric, and from
   scale-in eligibility, until its warmup or readiness period passes.
5. The load balancer or scheduler begins routing traffic or work to a new
   instance only once it passes its own health check.
6. Once the metric returns below the scale-in threshold and any cooldown or
   stabilization window has elapsed, the autoscaler computes a lower desired
   capacity and begins removing instances.
7. A terminating instance is drained, given time for in-flight work to
   complete, before it is actually destroyed.
```

## 8. Implementation variants

**AWS EC2 Auto Scaling, the four policy types.** Target tracking maintains a
metric near a chosen value, the vendor's own comparison being a thermostat
holding a target temperature. Step scaling applies a set of adjustments sized
to how far a CloudWatch alarm has been breached. Scheduled scaling changes
capacity at a known time. Predictive scaling forecasts daily or weekly
traffic patterns from history and provisions capacity ahead of the forecast
rather than reacting to it after the fact, which AWS states helps compensate
for the reactive nature of ordinary dynamic scaling
([AWS, Scaling based on
demand](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-scale-based-on-demand.html)
and [AWS, Predictive
scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-predictive-scaling.html),
verified 2026-08-22). AWS's own guidance favors target tracking over the
older simple scaling type, which it advises against together with the
cooldown mechanism that type relies on.

**AWS Application Auto Scaling.** A separate, cross-service abstraction
covering resources beyond EC2 instances, sharing the same four policy types.
AWS's own list includes DynamoDB tables, ECS services, Aurora replicas,
Lambda provisioned concurrency, and SageMaker endpoints, among others
([AWS, What is Application Auto
Scaling](https://docs.aws.amazon.com/autoscaling/application/userguide/what-is-application-auto-scaling.html),
verified 2026-08-22).

**Google Cloud managed instance group autoscaler.** Reads CPU utilization,
load balancing serving capacity, a Cloud Monitoring custom metric, or a
schedule, and computes a recommended size per signal, then sets the group's
size to the largest of those recommendations, an or-toward-scale-out rule
that mirrors AWS's own multi-policy priority behavior of always favoring
availability ([Google Cloud, Scaling based on CPU utilization and load
balancing
capacity](https://docs.cloud.google.com/compute/docs/autoscaler/scaling-cpu-load-balancing),
verified 2026-08-22). A group autoscaling on CPU or load balancing capacity
cannot scale to zero instances, a documented limit that matters for a
workload that is genuinely idle much of the time. Google Cloud allows up to
128 scaling schedules per instance group, which combine with rather than
override any active metric-based signal ([Google Cloud, Scaling based on a
schedule](https://docs.cloud.google.com/compute/docs/autoscaler/scaling-schedules),
verified 2026-08-22).

**Azure Virtual Machine Scale Sets autoscale.** Reads host metrics or metrics
pushed from a storage account, a Service Bus queue, or Application Insights,
and applies scale actions as either a fixed count or a percentage change, the
vendor recommending fixed counts for smaller scale sets and percentage
changes for larger ones where a small fixed increase changes the pool size
by very little
([Microsoft Learn, Overview of autoscale with Azure Virtual Machine Scale
Sets](https://learn.microsoft.com/en-us/azure/virtual-machine-scale-sets/virtual-machine-scale-sets-autoscale-overview),
verified 2026-08-22, page dated 2026-05-19). A scale set supports up to 20
autoscale rules, and automatic instance repair caps a scale set at 1000
instances.

**Kubernetes Horizontal Pod Autoscaler.** Computes a desired replica count as
the current replica count multiplied by the ratio of the current metric
value to the desired metric value, rounded up, evaluated on a control loop
that runs by default every 15 seconds. Kubernetes' own worked example shows
a current value of 200 milli-units against a desired value of 100
milli-units doubling the replica count, and the reverse halving it
([Kubernetes, Horizontal Pod
Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/),
verified 2026-08-22).

**Kubernetes Vertical Pod Autoscaler.** Changes a pod's resource requests and
limits rather than its replica count, through a Recommender that computes
suggested values from historical usage, an Updater that applies them to
already-running pods, and an Admission Controller that injects them into a
pod at creation time ([Kubernetes SIG Autoscaling, Vertical Pod Autoscaler
readme](https://github.com/kubernetes/autoscaler/blob/master/vertical-pod-autoscaler/README.md),
verified 2026-08-22). It is documented as incompatible with a workload that
defines pod-level resource limits rather than container-level ones, since the
admission controller can then reject a pod whose container totals exceed the
pod-level limit.

**Kubernetes Cluster Autoscaler.** Operates one level below the Horizontal
Pod Autoscaler, adding or removing nodes rather than pods. Its scale-out
trigger is a pod that failed to schedule due to insufficient node resources,
and its scale-in candidate is a node that has stayed underutilized for an
extended period with a documented default of 10 minutes, below a documented
default utilization threshold of 0.5, itself gated by a further 10 minute
cooldown after any scale-up before scale-down is reconsidered
([Kubernetes SIG Autoscaling, Cluster Autoscaler readme and
FAQ](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md),
verified 2026-08-22). A pod can opt out of eviction entirely with the
annotation `cluster-autoscaler.kubernetes.io/safe-to-evict` set to false, and
several classes of pod are protected by default, including those backed by a
restrictive disruption budget or those using local storage.

**KEDA, event-driven autoscaling.** A layer that watches an external event
source, a message queue depth or similar, and generates and manages a
Kubernetes `HorizontalPodAutoscaler` object from that data, with the native
HPA controller then making and executing the actual scaling decision
([KEDA, Scaling deployments](https://keda.sh/docs/2.18/concepts/scaling-deployments/),
verified 2026-08-22). Its `ScaledObject` resource targets an existing
Deployment or StatefulSet through more than a hundred documented connectors
to external systems. Its `ScaledJob` resource works differently, scheduling
one discrete Kubernetes Job per detected event rather than adding replicas
to a long-running workload, which pulls a single event, processes it to
completion, and terminates ([KEDA, Scaling
jobs](https://keda.sh/docs/2.18/concepts/scaling-jobs/), verified
2026-08-22). KEDA can scale a deployment to zero when idle and reactivate it
the moment an event arrives, a capability none of the cloud vendors' own
metric-based virtual machine autoscalers offer by default.

## 9. Known production uses

1. **Netflix Scryer.** Built specifically because reactive scaling alone left
   a real gap. Netflix states instance startup at its own operating scale
   ranged from 10 to 45 minutes, a window during which existing servers
   remained exposed if load kept rising, and adds a predictive layer built
   on its own well-understood weekly traffic curves rather than relying
   purely on a reactive threshold ([Netflix Technology Blog, Scryer,
   Netflix's Predictive Auto Scaling
   Engine](https://netflixtechblog.com/scryer-netflixs-predictive-auto-scaling-engine-a3f8fc922270),
   verified 2026-08-22).
2. **Spotify's event delivery consumers.** Autoscales hundreds of separately
   tuned Google Cloud managed instance groups, one per event type, absorbing
   traffic ranging from under one event per hour on some streams to more
   than 300000 events per second on others, using CPU-based target
   autoscaling specifically because the consumer is stateless and its CPU
   correlates well with its real load ([Spotify Engineering, Autoscaling
   Pub or Sub
   consumers](https://engineering.atspotify.com/2017/11/autoscaling-pub-sub-consumers),
   verified 2026-08-22).
3. **Slack's AWS Auto Scaling fleet.** During a real incident, Slack's
   automated system attempted to add 1200 servers to its web tier within a
   fourteen minute window, a concrete demonstration of the scale at which a
   named production system runs Auto Scaling groups as core infrastructure,
   detailed fully as a failure mode in dimension 11 below ([Slack
   Engineering, Slack's Outage on January 4th,
   2021](https://slack.engineering/slacks-outage-on-january-4th-2021/),
   verified 2026-08-22).

## 10. Consequences

**Positive.**

- Capacity tracks real demand rather than either provisioning extreme,
  lowering the cost of idle capacity while still absorbing genuine spikes.
- A workload survives an individual instance failure the same way a load
  balanced pool does, since a lost instance is simply replaced.
- The decision and the mechanism are decoupled from application code, per
  Azure's own stated principle in dimension 5, so the workload itself never
  has to reason about its own scaling.
- KEDA and similar event-driven autoscalers let a genuinely idle workload
  cost nothing at rest, scaling to zero rather than holding a warm minimum.

**Negative.**

- Every scale-out carries the reaction lag named in dimension 3. new
  capacity is not instantly useful, and a spike that resolves faster than
  that lag cannot be absorbed by autoscaling alone.
- Misconfigured thresholds can thrash, adding and removing capacity
  repeatedly, a documented failure mode covered fully in dimension 11.
- A scaling decision is only as good as the metric behind it. a metric that
  does not track true load, covered in dimension 11, makes autoscaling add
  capacity that does not relieve the real bottleneck.
- The pool size is bounded not only by the autoscaler's own configuration
  but by unrelated account-level or infrastructure-level limits, which can
  be hit silently during exactly the moment extra capacity is most needed.

## 11. Failure modes and misuse

**Scaling lag outpacing a real spike.** Netflix's own account, cited fully
in dimension 9, names a real service-degradation window that exists even
when reactive autoscaling behaves exactly as designed, because the
metric-driven trigger only fires after load has already risen, and instance
readiness at Netflix's own scale lagged that trigger by 10 to 45 minutes.
Netflix also documents a second, related shape. after an outage resolves, a
retry storm hits the recovering service, but a purely reactive system can
mistakenly scale down during the outage itself, since in-flight requests and
CPU momentarily dip, leaving the fleet under-provisioned exactly when the
retry storm arrives.

**Flapping.** Covered as a force in dimension 3, with Azure's own worked
example and its documented, name-specific detection event,
`Microsoft.Insights/AutoscaleSettings/Flapping/Action`, exposed to operators
in the activity log ([Microsoft Learn, Overview of autoscale
flapping](https://learn.microsoft.com/en-us/azure/azure-monitor/autoscale/autoscale-flapping),
verified 2026-08-22).

**A metric that does not track true load.** Spotify's own post names two
concrete cases from its production system. an average CPU metric across a
fleet can mask a genuinely overloaded machine sitting beside a hung, near-
idle one, since the fleet average of a zero-percent zombie and a
hundred-percent-loaded machine reads as fifty percent, hiding the real
problem entirely. Separately, when a downstream export dependency failed,
the consumer kept retrying against it, keeping CPU busy even though the
real constraint was the dead dependency, not compute capacity, so the
autoscaler kept adding machines that never relieved the bottleneck. Spotify
states that exponential backoff on the retry path is what stopped this loop
([Spotify Engineering, Autoscaling Pub or Sub
consumers](https://engineering.atspotify.com/2017/11/autoscaling-pub-sub-consumers),
verified 2026-08-22).

**A capacity ceiling hit silently.** Slack's own postmortem of its January
4, 2021 outage documents this compounding with a metric-direction failure in
the same incident. a network degradation raised true load but, because more
threads were blocked waiting rather than computing, measured CPU utilization
initially dropped, triggering an automated scale-down at the worst possible
moment. As true load became visible, Slack's system then attempted to add
1200 servers within a fourteen minute window, and this burst failed at the
provisioning layer rather than the policy layer. an internal provisioning
service hit a Linux open-files limit and an AWS account-level quota at the
same time. The resulting pile of broken, non-functional instances then hit
the Auto Scaling group's own configured maximum size, leaving no headroom to
launch healthy replacements even though the instances counted against that
maximum were doing nothing useful. Slack's own responders had to disable
scale-down manually to stop the automated system from making the incident
worse, and recovery resumed only once the underlying provisioning bottleneck
was fixed directly ([Slack Engineering, Slack's Outage on January 4th,
2021](https://slack.engineering/slacks-outage-on-january-4th-2021/),
verified 2026-08-22). AWS's own quota documentation corroborates the general
shape of this failure, stating plainly that quotas for other services such
as EC2 and VPC can affect an Auto Scaling group's own effective ceiling,
outside the group's own configured limits ([AWS, Quotas for Amazon EC2 Auto
Scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-quotas.html),
verified 2026-08-22).

## 12. Trade-off matrix

| Approach | Reaction speed | Handles unpredictable spikes | Idle cost | Operational complexity |
|---|---|---|---|---|
| Fixed pool sized for peak | Instant, no reaction needed | Yes, by construction | High, capacity sits unused most of the time | Low, nothing to configure |
| Fixed pool sized for average | Instant | No, degrades past average demand | Low | Low |
| Reactive autoscaling (target tracking, step scaling) | Bounded by instance warmup and cooldown, minutes | Partially, limited by the reaction lag | Low, tracks real demand | Medium, threshold and cooldown tuning |
| Predictive or scheduled autoscaling | Ahead of forecasted or scheduled demand | Yes for known patterns, no for genuine surprises | Low | High, needs historical data or an accurate schedule |
| Event-driven autoscaling (KEDA-style, scale to zero) | Bounded by cold-start time from zero | Yes for event-driven load specifically | Lowest, zero at rest | Medium to high, depends on the event source |

## 13. Related and incompatible patterns

**Load Balancing.** The two patterns are complementary, not overlapping.
Load Balancing distributes traffic across whatever pool currently exists.
Autoscaling decides how large that pool should be. Neither is useful without
the other, and every implementation surveyed in this entry assumes a load
balancer or equivalent traffic-distribution layer sits underneath the
autoscaled pool.

**Health Endpoint Monitoring.** Every implementation surveyed excludes a
newly launched or still-draining instance from receiving real traffic until
it passes a health check, the same dependency Load Balancing has on this
pattern. Autoscaling adds a second use for the same mechanism, since a
health check failure during the warmup window is what an autoscaler
distinguishes from a genuine capacity shortfall.

**Queue-Based Load Leveling.** A queue absorbs a burst that arrives faster
than new capacity can be provisioned, buying the time autoscaling's reaction
lag would otherwise cost as dropped or degraded requests. The two patterns
compose directly. autoscale the consumers reading from the queue, using
queue depth itself as the scaling metric, which several of KEDA's own
connectors implement directly.

**Throttling.** Named explicitly by Azure as the better fit for a sudden
burst that autoscaling's reaction lag cannot absorb in time, covered in
dimension 4. the two are alternative responses to the same class of problem,
chosen based on whether the workload can tolerate a delayed capacity
response or needs an immediate, if degraded, one instead.

**Deployment Stamps and Cell-Based Architecture.** Both partition a system
into isolated units at a coarser granularity than an individual instance.
Autoscaling typically operates within one stamp or cell, sizing that unit's
own pool, while the stamp or cell boundary itself is a separate, usually
manual or semi-automated decision about capacity allocation across tenants
or regions.

**Competing Consumers.** The pattern that gives multiple worker instances a
shared unit of work to pull from, most commonly a queue. Autoscaling changes
how many competing consumers exist at a given moment. the two patterns are
frequently deployed together, with autoscaling reading the same queue depth
that Competing Consumers already uses for work distribution.

## 14. Refactoring path in and out

**Introducing it.** Start from a correctly sized fixed pool with health
checking already in place, since every autoscaler surveyed depends on that
health signal to know when a new instance is genuinely ready. Add a single,
simple metric-based policy first, target tracking on a metric that
correlates well with real load, per Spotify's own stated reasoning for
choosing CPU specifically because the workload was stateless. Verify the
warmup or readiness period and the cooldown or stabilization window are
configured deliberately rather than left at a default that was never
checked against the workload's own boot time. Only add scheduled or
predictive scaling once enough historical traffic data exists to make a
forecast reliable, per Netflix's own stated approach.

**Removing it.** Two honest reasons exist. Demand has become genuinely
constant and predictable, so the operational cost of tuning thresholds no
longer buys anything a correctly sized fixed pool would not already give,
or the workload has moved to an architecture, an event-driven serverless
platform for example, where the provisioning platform itself absorbs the
scaling decision entirely and there is no group or scale set left to
configure directly.

## 15. Testing and verification

- **Unit test the scaling decision in isolation.** Feed the policy's decision
  function a fixed metric value and a fixed current capacity, and assert the
  computed desired capacity matches the documented formula, without a real
  cloud API call anywhere in the test.
- **Test the warmup and cooldown exclusion windows directly.** Simulate a
  newly launched instance reporting a metric before its warmup period has
  elapsed, and assert it is excluded from the aggregate the policy reads,
  matching the behavior documented in dimension 3.
- **Load test the reaction lag itself.** Drive a synthetic spike against a
  test environment and measure the real wall-clock time between the metric
  crossing its threshold and new capacity actually passing its health
  check, comparing that measured lag against the SLA the workload needs to
  meet, rather than assuming the vendor's documented defaults are close
  enough for this specific workload's own boot time.
- **Test the flapping and quota-exhaustion cases on purpose.** Configure
  thresholds deliberately close together in a test environment and confirm
  the system either avoids oscillation or exposes it through the
  observability signals in dimension 16, and separately, confirm the
  behavior when a configured maximum size is reached, so what dimension 11
  describes as a silent ceiling is discovered in a test rather than in a
  real incident.

## 16. Observability signals

- **Group or pool size, at every stage of its lifecycle.** AWS's own
  CloudWatch metrics separate this cleanly. `GroupDesiredCapacity`,
  `GroupInServiceInstances`, `GroupPendingInstances`, and
  `GroupTerminatingInstances`, plus `GroupMinSize` and `GroupMaxSize` for the
  configured bounds themselves ([AWS, Amazon EC2 Auto Scaling group
  metrics](https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-metrics.html),
  verified 2026-08-22). A healthy group shows desired and in-service
  capacity converging smoothly, with pending and terminating counts
  returning to zero between events. A struggling group shows a persistently
  non-zero pending or terminating count that never fully drains before the
  next change, or an in-service count that plateaus below desired capacity
  while pending stays high, the specific signature of instances failing
  to become healthy rather than a policy problem.
- **Kubernetes HPA status.** The `HorizontalPodAutoscalerStatus` object
  exposes `currentReplicas`, `desiredReplicas`, `currentMetrics`, and a set
  of conditions describing whether the autoscaler is currently able to
  scale, actively scaling, or limited in what it can do
  ([Kubernetes, HorizontalPodAutoscaler
  v2](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/horizontal-pod-autoscaler-v2/),
  verified 2026-08-22, the precise wording of each condition was not fully
  retrievable in this research pass and is not restated here as an exact
  quote).
- **Azure's named flapping event.** The `Microsoft.Insights/AutoscaleSettings/Flapping/Action`
  activity log event fires with the intended and actual instance counts
  Azure applied to avoid the loop, giving an operator a direct, queryable
  signal rather than having to infer thrashing from raw instance-count
  history alone.
- **A capacity ceiling being hit.** Watch the configured maximum against the
  current desired or in-service count directly, since none of the vendors
  surveyed raise a loud, dedicated alert the moment a group is capped, per
  the Slack incident in dimension 11. the ceiling is visible only to an
  operator already watching for it.

## 17. Security and privacy implications

**A misconfiguration scales out with the workload.** Every instance an
autoscaled group creates shares one launch configuration at a time, an AMI,
a security group set, and an IAM role in AWS's own model
([AWS, Create a launch template for an Auto Scaling
group](https://docs.aws.amazon.com/autoscaling/ec2/userguide/create-launch-template.html),
verified 2026-08-22). This means a single overly broad IAM role or an open
security group baked into that shared template is reproduced identically
across every instance a scale-out event creates, so a mistake that would
affect one machine in a manually managed fleet is multiplied across however
many new instances autoscaling launches. This inference is stated here as
the entry's own analysis of the documented mechanism, since AWS's own
documentation does not frame launch templates as a security-propagation risk
in these terms itself. AWS's documented default is fail-safe rather than
fail-open. a launch template with no security group specified falls back to
the VPC's default group, which does not allow inbound traffic from external
networks by default.

**Graceful termination and in-flight requests.** AWS's lifecycle hooks let a
scale-in event pause an instance before it is actually terminated, notify an
external system through EventBridge, and run custom cleanup logic, such as
extracting logs or session data, before signaling that termination may
proceed, with a default one hour heartbeat timeout and a hard cap at 48
hours or 100 times that timeout ([AWS, Amazon EC2 Auto Scaling lifecycle
hooks](https://docs.aws.amazon.com/autoscaling/ec2/userguide/lifecycle-hooks.html),
verified 2026-08-22). If a termination hook times out or is abandoned, AWS
proceeds with termination anyway rather than blocking indefinitely, a
deliberate trade between guaranteeing graceful shutdown and keeping the
termination path itself from becoming stuck. Separately, at the load
balancer, a deregistering target's connections are drained for up to 300
seconds by default before deregistration completes, though a target with no
in-flight requests deregisters immediately without waiting out that window
([AWS, Target group attributes for Elastic Load
Balancing](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html),
verified 2026-08-22). AWS states plainly what happens if the underlying
instance is terminated before that drain window finishes. a client whose
connection is cut mid-request receives a 500-level error, a directly
documented answer to whether in-flight requests survive a scale-in event.

## 18. References

1. Wikipedia. *Amazon Elastic Compute Cloud*.
   https://en.wikipedia.org/wiki/Amazon_Elastic_Compute_Cloud
   Verified 2026-08-22. Source of the May 2009 date for Auto Scaling,
   Elastic Load Balancing, and CloudWatch shipping together, noted at
   moderate confidence, secondary source, citing the original Amazon Web
   Services Blog announcement.
2. AWS. *What is Amazon EC2 Auto Scaling*.
   https://docs.aws.amazon.com/autoscaling/ec2/userguide/what-is-amazon-ec2-auto-scaling.html
   Verified 2026-08-22. Source of the current product naming and the
   minimum, maximum, desired capacity model.
3. Wikipedia. *Autonomic computing*.
   https://en.wikipedia.org/wiki/Autonomic_computing
   Verified 2026-08-22. Source of IBM's 2001 self-optimization framing,
   presented as an indirect conceptual forerunner, not a direct lineage.
4. NIST. Mell, P. and Grance, T. *Special Publication 800-145, The NIST
   Definition of Cloud Computing*, September 2011.
   https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-145.pdf
   Verified 2026-08-22. Source of rapid elasticity as one of five essential
   characteristics of cloud computing.
5. AWS. *Benefits of Amazon EC2 Auto Scaling*.
   https://docs.aws.amazon.com/autoscaling/ec2/userguide/auto-scaling-benefits.md
   Verified 2026-08-22. Source of the over-provisioning versus
   under-provisioning worked example.
6. Google Cloud. *Autoscaling groups of instances*.
   https://docs.cloud.google.com/compute/docs/autoscaler
   Verified 2026-08-22. Source of the pool-size framing, the initialization
   period default, and the stabilization period default.
7. Microsoft Learn. *Autoscaling guidance for cloud applications*
   (Azure architecture center best-practice reference).
   https://learn.microsoft.com/en-us/azure/architecture/best-practices/auto-scaling
   Verified 2026-08-22, page dated 2022-10-11, updated 2026-06-04. Source of
   the vertical versus horizontal distinction, the sudden-burst
   non-applicability case, the stateful-workload caveat, and the
   decoupled-decision-maker structural principle.
8. AWS. *Target tracking scaling policies for Amazon EC2 Auto Scaling*.
   https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-scaling-target-tracking.html
   Verified 2026-08-22. Source of the instance warmup mechanism, the
   thermostat comparison, and the conservative rounding behavior.
9. Kubernetes. *Horizontal Pod Autoscaling*.
   https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
   Verified 2026-08-22. Source of the desired-replicas formula, the worked
   doubling and halving example, the 15 second evaluation interval, the 0.1
   tolerance, the default stabilization windows, and the readiness delay and
   CPU initialization period defaults.
10. AWS. *Scaling cooldowns for Amazon EC2 Auto Scaling*.
    https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-scaling-cooldowns.html
    Verified 2026-08-22. Source of the 300 second default cooldown for
    simple scaling policies.
11. Microsoft Learn. *Understand autoscale settings, and overview of
    autoscale flapping in Azure Monitor*.
    https://learn.microsoft.com/en-us/azure/azure-monitor/autoscale/autoscale-flapping
    Verified 2026-08-22, page last updated 2026-08-21. Source of the worked
    flapping example, the three named root causes, and the named
    activity-log flapping event.
12. AWS. *Predictive scaling for Amazon EC2 Auto Scaling*.
    https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-predictive-scaling.html
    Verified 2026-08-22. Source of the cyclical and recurring workload
    applicability cases and the reactive-versus-predictive framing.
13. AWS. *Scaling based on demand for Amazon EC2 Auto Scaling*.
    https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-scale-based-on-demand.html
    Verified 2026-08-22. Source of the target tracking, step scaling, and
    simple scaling definitions and AWS's recommendation to favor target
    tracking.
14. AWS. *What is Application Auto Scaling*.
    https://docs.aws.amazon.com/autoscaling/application/userguide/what-is-application-auto-scaling.html
    Verified 2026-08-22. Source of the list of non-EC2 resources Application
    Auto Scaling covers.
15. Google Cloud. *Scaling based on CPU utilization and load balancing
    capacity*.
    https://docs.cloud.google.com/compute/docs/autoscaler/scaling-cpu-load-balancing
    Verified 2026-08-22. Source of the largest-of-signals combination rule
    and the cannot-scale-to-zero limitation.
16. Google Cloud. *Scaling based on a schedule*.
    https://docs.cloud.google.com/compute/docs/autoscaler/scaling-schedules
    Verified 2026-08-22. Source of the 128 schedules per group limit and the
    combines-rather-than-overrides behavior.
17. Microsoft Learn. *Overview of autoscale with Azure Virtual Machine Scale
    Sets*.
    https://learn.microsoft.com/en-us/azure/virtual-machine-scale-sets/virtual-machine-scale-sets-autoscale-overview
    Verified 2026-08-22, page dated 2026-05-19. Source of the fixed versus
    percentage scale action guidance and the 20 rule and 1000 instance
    limits.
18. GitHub, Kubernetes SIG Autoscaling. *Vertical Pod Autoscaler readme*.
    https://github.com/kubernetes/autoscaler/blob/master/vertical-pod-autoscaler/README.md
    Verified 2026-08-22. Source of the Recommender, Updater, Admission
    Controller structure and the pod-level resource limit incompatibility.
19. GitHub, Kubernetes SIG Autoscaling. *Cluster Autoscaler readme and FAQ*.
    https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md
    Verified 2026-08-22. Source of the scale-up-on-unschedulable-pod
    trigger, the 10 minute defaults, the 0.5 utilization threshold, and the
    safe-to-evict annotation.
20. KEDA. *Scaling deployments*.
    https://keda.sh/docs/2.18/concepts/scaling-deployments/
    Verified 2026-08-22. Source of the KEDA-generates-an-HPA relationship
    and the ScaledObject description.
21. KEDA. *Scaling jobs*.
    https://keda.sh/docs/2.18/concepts/scaling-jobs/
    Verified 2026-08-22. Source of the ScaledJob one-job-per-event model.
22. Netflix Technology Blog. *Scryer, Netflix's Predictive Auto Scaling
    Engine*.
    https://netflixtechblog.com/scryer-netflixs-predictive-auto-scaling-engine-a3f8fc922270
    Verified 2026-08-22. Source of the 10 to 45 minute instance startup
    figure and the outage-recovery retry-storm failure shape.
23. Spotify Engineering. *Autoscaling Pub or Sub consumers*.
    https://engineering.atspotify.com/2017/11/autoscaling-pub-sub-consumers
    Verified 2026-08-22. Source of the zombie-machine averaging problem, the
    downstream-dependency bottleneck incident, and the production traffic
    range figures.
24. Slack Engineering. *Slack's Outage on January 4th, 2021*.
    https://slack.engineering/slacks-outage-on-january-4th-2021/
    Verified 2026-08-22. Source of the metric-inversion scale-down, the 1200
    server scale-out attempt, and the compounding quota and group-maximum
    failure.
25. AWS. *Quotas for Amazon EC2 Auto Scaling*.
    https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-quotas.html
    Verified 2026-08-22. Source of the cross-service quota caveat
    corroborating the Slack incident.
26. AWS. *Health check grace period for Amazon EC2 Auto Scaling instances*.
    https://docs.aws.amazon.com/autoscaling/ec2/userguide/health-check-grace-period.html
    Verified 2026-08-22. Source of the 300 second default grace period and
    the EC2-state exception carve-out.
27. AWS. *Amazon EC2 Auto Scaling group metrics for CloudWatch*.
    https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-metrics.html
    Verified 2026-08-22. Source of the observability metric list.
28. Kubernetes. *HorizontalPodAutoscaler v2*.
    https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/horizontal-pod-autoscaler-v2/
    Verified 2026-08-22. Source of the status object field list, with the
    exact per-condition wording flagged as not fully retrievable.
29. AWS. *Create a launch template for an Auto Scaling group*.
    https://docs.aws.amazon.com/autoscaling/ec2/userguide/create-launch-template.html
    Verified 2026-08-22. Source of the shared launch template mechanics and
    the fail-safe default security group behavior.
30. AWS. *Amazon EC2 Auto Scaling lifecycle hooks*.
    https://docs.aws.amazon.com/autoscaling/ec2/userguide/lifecycle-hooks.html
    Verified 2026-08-22. Source of the pause-notify-cleanup termination
    mechanism and its timeout defaults.
31. AWS. *Target group attributes for Elastic Load Balancing*.
    https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html
    Verified 2026-08-22. Source of the deregistration delay default and the
    documented client-facing error on a premature termination.

**Evidence grade.** high

**Most solid findings.** AWS's, Google Cloud's, Azure's, and Kubernetes' own
documentation gave concrete, numeric, directly quotable defaults for warmup,
cooldown, and stabilization mechanisms across every vendor surveyed. The
Netflix, Spotify, and Slack sources are each a named company's own
engineering account, giving this entry real, sourced production evidence
rather than invented figures, and the Slack incident in particular is an
unusually strong single source, since it documents several distinct failure
modes compounding in one real, public postmortem.

**Unverified or unclear.** The May 2009 shipping date for AWS's Auto Scaling
feature rests on a secondary Wikipedia citation rather than a directly
fetched primary announcement. The exact per-condition wording of
Kubernetes' `AbleToScale`, `ScalingActive`, and `ScalingLimited` status
conditions could not be retrieved in its exact wording and is named but not
quoted here. No vendor or engineering source gave a concrete, sourced
cost-savings figure comparing autoscaling against a fixed pool, so the
trade-off matrix in dimension 12 states this qualitatively rather than with
an invented number.

## Code

### TypeScript, a target tracking style controller with warmup exclusion

```typescript
type Instance = {
  id: string;
  launchedAt: number;
  warmupSeconds: number;
};

class TargetTrackingAutoscaler {
  private instances: Instance[] = [];
  private minSize: number;
  private maxSize: number;
  private targetMetric: number;

  constructor(minSize: number, maxSize: number, targetMetric: number) {
    this.minSize = minSize;
    this.maxSize = maxSize;
    this.targetMetric = targetMetric;
  }

  private warmInstances(now: number): Instance[] {
    return this.instances.filter(
      (i) => now - i.launchedAt >= i.warmupSeconds * 1000
    );
  }

  evaluate(currentMetric: number, now: number): number {
    const warm = this.warmInstances(now);
    const warmCount = Math.max(warm.length, 1);
    const ratio = currentMetric / this.targetMetric;
    const rawDesired = Math.ceil(warmCount * ratio);
    const bounded = Math.min(this.maxSize, Math.max(this.minSize, rawDesired));

    while (this.instances.length < bounded) {
      this.instances.push({
        id: "i-" + this.instances.length,
        launchedAt: now,
        warmupSeconds: 60,
      });
    }
    if (bounded < this.instances.length && warm.length >= bounded) {
      this.instances = this.instances.slice(0, bounded);
    }
    return this.instances.length;
  }
}

const scaler = new TargetTrackingAutoscaler(1, 10, 50);
console.log(scaler.evaluate(200, 0));
console.log(scaler.evaluate(200, 30000));
```

### Python, a Kubernetes HPA style desired-replica calculation with a tolerance band

```python
import math
from dataclasses import dataclass


@dataclass
class HpaState:
    current_replicas: int
    min_replicas: int
    max_replicas: int
    tolerance: float = 0.1


def desired_replicas(state: HpaState, current_metric: float, target_metric: float) -> int:
    ratio = current_metric / target_metric
    if abs(ratio - 1.0) <= state.tolerance:
        return state.current_replicas
    raw = math.ceil(state.current_replicas * ratio)
    return max(state.min_replicas, min(state.max_replicas, raw))


def simulate() -> None:
    state = HpaState(current_replicas=2, min_replicas=1, max_replicas=20)
    print(desired_replicas(state, 200.0, 100.0))
    print(desired_replicas(state, 105.0, 100.0))
    print(desired_replicas(state, 50.0, 100.0))


simulate()
```

### Go, a flapping guard that defers a scale-in when it would immediately reverse

```go
package main

import "fmt"

type PoolState struct {
	Instances       int
	ScaleOutPercent float64
	ScaleInPercent  float64
}

func projectedUtilization(currentUtil float64, currentInstances, newInstances int) float64 {
	totalLoad := currentUtil * float64(currentInstances)
	return totalLoad / float64(newInstances)
}

func evaluateScaleIn(state PoolState, currentUtil float64) (int, bool) {
	candidate := state.Instances - 1
	if candidate < 1 {
		return state.Instances, false
	}
	afterRemoval := projectedUtilization(currentUtil, state.Instances, candidate)
	wouldReverse := afterRemoval >= state.ScaleOutPercent
	if wouldReverse {
		return state.Instances, false
	}
	return candidate, true
}

func main() {
	state := PoolState{Instances: 3, ScaleOutPercent: 50.0, ScaleInPercent: 30.0}
	next, scaledIn := evaluateScaleIn(state, 28.0)
	fmt.Println("next instance count:", next, "scaled in:", scaledIn)
}
```
