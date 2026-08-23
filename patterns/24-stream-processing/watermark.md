---
name: Watermark
slug: watermark
family: 24-stream-processing
category: Stream Processing
aliases: [Low Watermark]
first_described: "Tyler Akidau, Alex Balikov, Kaya Bekiroglu, Slava Chernyak, Josh Haberman, Reuven Lax, Sam McVeety, Daniel Mills, Paul Nordstrom, Sam Whittle, MillWheel: Fault-Tolerant Stream Processing at Internet Scale, Proceedings of the VLDB Endowment, Volume 6, Number 11, pages 1033 to 1044, 2013"
maturity: established
related: [event-time-processing, windowing, exactly-once-processing]
incompatible_with: []
verified: 2026-08-23
---

## 1. Name, aliases, and lineage

The term originates in MillWheel, where it is called the low watermark and given a formal, recursive definition. MillWheel's own text, Section 4.5, quoted directly. "Given a computation, A, let the oldest work of A be a timestamp corresponding to the oldest unfinished (in-flight, stored, or pending-delivery) record in A. Given this, we define the low watermark of A to be min(oldest work of A, low watermark of C : C outputs to A)." Published by Tyler Akidau and nine co-authors, Proceedings of the VLDB Endowment, Volume 6, Number 11, pages 1033 to 1044, 2013.

The Dataflow Model paper (Akidau et al., Proceedings of the VLDB Endowment, Volume 8, Number 12, 2015, the source that formalizes event-time processing itself, see the related sibling entry) does not coin the term. It explicitly borrows it, stated in its own Section 1.3. "For our purposes, we'll consider something like MillWheel's watermark, which is a lower bound (often heuristically established) on event times that have been processed by the pipeline." The Dataflow paper generalizes the mechanism from a MillWheel-internal progress metric into a model-level primitive that a trigger can act on.

An earlier, separately-lineaged academic term exists for a related completeness signal. The Dataflow paper's own introduction cites it directly as prior art rather than as its own vocabulary, naming two publications. Tucker et al., Exploiting punctuation semantics in continuous data streams, IEEE Transactions on Knowledge and Data Engineering, 15, 2003. Srivastava and Widom, Flexible Time Management in Data Stream Systems, Proc. of the 23rd ACM SIGMOD-SIGACT-SIGART Symposium on Principles of Database Systems, pages 263 to 274, 2004. Punctuation predates MillWheel's watermark by a decade and was used in Microsoft's CEDR and Trill streaming database systems. The Dataflow paper names the cost of a punctuation-driven completeness signal directly. "the use of punctuations essentially transforms the streaming system into micro-batch, introducing additional latency."

Modern engine terminology diverges further. Apache Flink keeps watermark as its primary term, formally. "A Watermark(t) declares that event time has reached time t in that stream, meaning that there should be no more elements from the stream with a timestamp t' less than or equal to t." Apache Beam also uses watermark, current wording from the programming guide. "Watermarks are a concept in Beam that represent the point in event time that Beam has finished processing all data with event times less than or equal to the watermark. In other words, the watermark represents the notion of completeness of the data." Apache Spark Structured Streaming uses watermark as an explicit column annotation set through withWatermark.

Apache Kafka Streams does not use the word watermark anywhere in its documentation. Its nearest functional analog is stream time, a per-processor, data-driven clock, combined with a per-window grace period governing how long out-of-order records are still accepted. Kafka Streams' own core-concepts documentation defines it directly. "Kafka Streams assigns a timestamp to every data record via the TimestampExtractor interface. These per-record timestamps describe the progress of a stream with regards to time... this time will only advance when a new record arrives at the processor. We call this data-driven time the stream time of the application to differentiate with the wall-clock time." A peer-reviewed comparative analysis of the mechanism classifies this design precisely, not as an absence of the idea but as a weaker variant of it. "Kafka Streams uses a non-conformant watermark (referred to as a grace period) to provide final results. Conformant and non-conformant watermarks are sometimes referred to as perfect and heuristic watermarks, respectively." Source, Begoli, Akidau, Chernyak, Hueske, Knight, Knowles, Mills, Sotolongo, Watermarks in Stream Processing Systems, Semantics and Comparative Analysis of Apache Flink and Google Cloud Dataflow, Proceedings of the VLDB Endowment, Volume 14, Number 12, pages 3135 to 3147, 2021.

## 2. Problem and context

A stream processing system that groups records by when they actually happened, not by when the system happened to receive them, faces a specific unanswerable-looking question. Given that records can arrive arbitrarily out of order, or not at all for arbitrarily long, when is it safe to say I have seen everything that will ever belong to the interval [t1, t2)? Without an answer, no grouping over event time can ever be considered finished, because a straggler record could in principle still be en route.

The Dataflow paper states the need for a signal directly, in a sentence the related sibling entry on event-time processing also draws on, because the two problems are the same problem viewed from different sides. "Since the data are unordered with respect to event time, we require some other signal to tell us when the window is done." Watermark is that signal.

MillWheel's own paper explains why the signal cannot be computed exactly, only estimated, and frames this as a deliberate, named trade-off rather than an implementation shortcoming. Section 7.2. "we are able to optionally strip away outliers and offer heuristic low watermark values for pipelines that are more interested in speed than accuracy." The context this problem arises in is any pipeline where event time and processing time can diverge by an unbounded amount, a mobile device going offline for days being the paper's own concrete example, carried in more detail in the sibling event-time-processing entry.

Why the naive answer, wait longer, does not resolve the problem. Waiting longer narrows the error but never eliminates it, because the bound on how out of order data can arrive is itself unknown in a general distributed system. The Dataflow paper states the resulting trade-off as a footnote. "For most real-world distributed data sets, the system lacks sufficient knowledge to establish a 100 percent correct watermark... most watermarks must be heuristically defined based on limited knowledge available." A perfect watermark would require certainty that no earlier-timestamped record is still anywhere in flight, which is not achievable without either closing off the possibility of out-of-order arrival entirely, or accepting unbounded wait time. Watermark turns this unsolvable dilemma into a tunable dial, how heuristic, how conservative, rather than leaving it as a binary choice between never emitting and emitting something that might be wrong.

## 3. Forces

Aggressive advancement against conservative advancement. MillWheel's percentile watermark feature is a sourced, deliberate example of trading correctness for speed on purpose, Section 7.2. "we can compute a 99 percent low watermark that corresponds to the progress of 99 percent of the record timestamps in the system. A windowing consumer that is only interested in approximate results could then use these low watermark values to operate with lower latency, having eliminated its need to wait on stragglers." The opposite failure, one slow record holding back every downstream window, follows directly from the min-of-inputs rule covered in Dynamics below, and Flink's own documentation names the symptom concretely for an idle source. "If one of the input splits, partitions, or shards does not carry events for a while this means that the WatermarkGenerator also does not get any new information on which to base a watermark."

Heuristic watermarks against perfect watermarks, stated by the Dataflow paper as a genuine binary, not merely a spectrum. Assigning arrival time as event time at ingestion gives, in the paper's own words, "perfect (i.e. non-heuristic) watermarks, with no late data," at the direct cost of discarding the true event-time correctness the mechanism exists to protect. This is the sharpest force in the whole pattern. Watermark uncertainty can be eliminated entirely, but only by giving up the thing the watermark was built to provide.

Watermark drift across parallel sources, one source racing ahead of another. Flink's watermark alignment feature is a designed-for response to exactly this force, named directly in Flink's documentation. "you have to tell the maximal drift from the current minimal watermarks across all sources belonging to that group," so as to "enable watermark alignment, which will make sure no sources, splits, shards, or partitions increase their watermarks too far ahead of the rest." Without this control a fast source can push a pipeline's effective watermark far ahead of a genuinely slow but healthy source, producing spurious lateness for data that arrived on time relative to its own source.

State-buffering cost against the width of the correctness horizon. A more conservative watermark, or a wider allowed-lateness or grace-period setting, means holding more per-window state alive for longer, a direct and quantifiable operational cost, memory footprint and checkpoint size, traded against a lower rate of dropped late records. Spark's own documentation names the mechanical form of this trade for its multi-stream case, choosing the minimum watermark across unioned streams by default, "as a side effect, data from the slower streams will be aggressively dropped" if the maximum policy is chosen instead.

A peer-reviewed comparative study of Flink and Cloud Dataflow's watermark implementations names a further, structural force, in-band propagation against out-of-band propagation. Flink embeds the watermark directly in the data stream and never persists it centrally. Cloud Dataflow persists watermark progress to a central aggregator, which the paper states trades a "slightly higher" reporting latency, from "the extra network hop... as well as the time spent on persisting watermark progress to persistent state," for a materially faster, finer-grained fault recovery, covered further in Failure modes below.

## 4. Applicability and non-applicability

Reach for a watermark when the pipeline does event-time windowing over unbounded, out-of-order data, because per the Dataflow paper's own framing, quoted above, some other signal is required to know a window is done, and watermark is that signal. Watermark is not optional infrastructure layered on top of event-time windowing, it is the mechanism that makes such windowing computable in the first place, a relationship the sibling event-time-processing entry states directly from its own side.

Reach for a watermark when a genuinely tunable correctness-against-latency dial is wanted. MillWheel's own named use cases sit at opposite ends of that dial on purpose, an exact, heuristically tight watermark for billing, and a 99th-percentile watermark for abuse detection, trading a known, bounded error rate for materially lower latency.

Do not reach for a watermark in a processing-time-only system. If windows are defined purely by wall-clock arrival, there is nothing for a watermark to track, the question a watermark answers, has all the data up to event time T arrived, does not arise, because the window boundary was never defined in terms of event time to begin with. Flink's own documentation states processing time plainly. "refers to the system time of the machine that is executing the respective operation," needing no event-time progress signal at all.

Do not reach for a watermark over a bounded, already-complete dataset. The whole mechanism exists to answer whether everything up to T has arrived while data are still arriving. Over a closed, finite input, completeness is known trivially the moment the input is exhausted, so there is nothing left to estimate.

Do not reach for the full heuristic machinery when out-of-order arrival provably cannot occur. The Dataflow paper's own arrival-time-as-event-time pattern, already cited above, is the sourced example, assigning event time at ingestion removes the possibility of out-of-order arrival relative to that timestamp by construction, which gives a watermark that is technically still present but trivially and always correct. At that point the heuristic tuning surface, out-of-orderness bounds, allowed lateness, percentile watermarks, buys nothing.

Do not reach for watermark-gated completeness when a fast, rough, arrival-order-driven signal is what the use case actually needs. The Dataflow paper's own trend-detection pipeline deliberately used processing-time triggers instead, stating the reason directly, forcing watermark-based completeness "essentially transforms the streaming system into micro-batch, introducing additional latency," which the use case could not tolerate. Its own recommendation-system pipeline made the identical deliberate choice, preferring continuously-updated partial views over waiting for the watermark to pass a session's end.

## 5. Structure

Watermark generator, attached at or directly after a source. Flink's documentation states this placement directly. "Watermarks are generated at, or directly after, source functions. Each parallel subtask of a source function usually generates its watermarks independently." Two generation styles are named identically across engines that support the concept explicitly. A periodic generator observes every event and emits on a framework-driven tick. A punctuated generator waits for a special marker event carrying watermark information already embedded in the stream and emits immediately on seeing one.

Per-partition watermark, for a partitioned source consumed in parallel. Flink's own documentation states this as a distinct structural step, separate from the operator-level merge below, because "when consuming streams from Kafka, multiple partitions often get consumed in parallel, interleaving the events from the partitions and destroying the per-partition patterns, this is inherent in how Kafka's consumer clients work." Watermarks are generated per Kafka partition, and the per-partition watermarks are merged inside the source operator before a single watermark is ever emitted downstream, "in the same way as watermarks are merged on stream shuffles."

Per-operator watermark, defined as the minimum across every upstream input to that operator. This rule is confirmed identically in two systems built roughly a decade apart. MillWheel's own recursive definition, quoted in Name, aliases, and lineage above, and Flink's current documentation, stated independently on two separate pages. "the current watermark of the operator is defined as the minimum of both of its inputs" and, elsewhere, "such an operator's current event time is the minimum of its input streams' event times."

Global watermark authority, a MillWheel-specific structural participant with no equivalent in Flink or Beam's fully decentralized propagation. MillWheel implements a sharded central authority that tracks every worker's already-computed low watermark and journals it to persistent state, and it is this authority, not the individual workers, that computes percentile watermarks. MillWheel's own text states the authority never leads the workers it aggregates. "By having workers compute the minima of their respective inputs, the authority's low watermark never leads the workers', and this property is preserved."

Watermark alignment, a drift-bounding participant in Flink. A configured maximum drift across a named alignment group causes a fast-progressing source to be paused once it outruns the group's slowest member by more than the configured bound, resuming once the gap narrows.

Idle-source exclusion. A source or partition can declare itself idle after a configured timeout, removing it from the per-operator minimum calculation so a single silent partition does not stall every downstream watermark indefinitely. Flink exposes this directly on its WatermarkStrategy through withIdleness.

Per-key timers, firing as the watermark advances. MillWheel's own text, Section 4.6. "Timers are per-key programmatic hooks that trigger at a specific wall time or low watermark value... Once set, timers are guaranteed to fire in increasing timestamp order."

Source-side custom watermark control, a Beam-specific structural extension point with no direct equivalent surveyed in the other three systems. Beam's programming guide describes a Splittable DoFn's ability to communicate its own progress through event time. "Watermark estimation allows a Splittable DoFn to communicate to the runner how far it has progressed through its input, enabling better scheduling and late-data handling," and a DoFn implementation can "explicitly control watermark advancement through estimator callbacks."

Kafka Streams' structurally different substitute. There is no propagated watermark object anywhere in its architecture. In its place sits a per-processor stream time, a data-driven clock that "will only advance when a new record arrives at the processor," paired with a per-window grace period evaluated locally rather than as a value flowing through a topology.

## 6. ASCII structure diagram

```
  partitioned source (N partitions, e.g. a Kafka topic)
        |
        v
  per-partition watermark generator      (periodic: onEvent() + onPeriodicEmit()
        |  (one per partition,            punctuated: fires on an in-band marker event)
        |   independent of the others)
        v
  per-partition watermarks merged inside the source operator
  (same min-of-inputs rule as the operator merge below, applied one level earlier)
        |
        v
  source operator's emitted watermark  ---->  [optional: idle-source exclusion]
        |                                     [optional: watermark alignment,
        |                                      pauses a source that drifts too
        |                                      far ahead of its alignment group]
        v
  downstream operator A  <---(input 1)---  source operator's watermark
        ^
        |
  downstream operator A  <---(input 2)---  a different upstream operator's watermark
        |
        v
  operator A's watermark = min( operator A's own oldest unfinished work,
                                 watermark of every upstream input to A )
        |
        | whenever an operator's own event time advances, it emits a
        | new watermark downstream to its successor operators
        v
  ... the same merge rule repeats recursively through the DAG ...
        |
        v
  per-key timers fire, in increasing timestamp order, as the low
  watermark passes each timer's scheduled value
        |
        v
  a window's trigger fires once the watermark crosses the window's
  event-time end (the handoff into windowing and triggering, see
  the related event-time-processing entry)
        |
        v
  a late record arrives, event time earlier than the current watermark
        |
        +--- within the allowed lateness or grace period --> re-enters
        |                                                     the window, re-fires the trigger
        |
        +--- past that horizon -----------------------------> dropped, or
                                                                routed to a side output if configured

  [ separate, optional path, MillWheel-specific: a sharded, central
    watermark authority aggregates every worker's already-computed
    minimum, purely to report progress and to compute percentile
    (heuristic, approximate) watermarks. It never leads what the
    workers themselves have already computed. ]
```

The per-partition merge and the per-operator merge are the same rule applied at two structural levels, not two different mechanisms. Flink's own documentation states the per-partition case is merged "in the same way as watermarks are merged on stream shuffles," the identical min-of-inputs rule that governs every later step in the chain.

## 7. Dynamics

The core algorithm, minimum of upstream watermarks, is confirmed identically in two systems built roughly a decade apart, which is itself evidence this is close to the canonical shape of the mechanism rather than one vendor's arbitrary choice. MillWheel's 2013 recursive definition and Flink's current documentation, on two separately fetched pages, both state the identical rule, quoted in full in Structure above.

Propagation is reactive, not polled on a fixed clock. Flink states this directly. "whenever an operator advances its event time, it generates a new watermark downstream for its successor operators." An operator does not ask upstream for its current watermark, it re-evaluates its own minimum and emits a new value exactly when that minimum changes.

Advancement is not smooth or monotonic in wall-clock terms, a concrete illustration already carried in the related event-time-processing entry, drawn from the Dataflow paper's own figures.

Idle-source exclusion is a deliberate carve-out from the always-take-the-minimum rule, not a separate mechanism layered beside it. Without it, a single silent partition deadlocks every downstream watermark permanently, since the minimum of a set that includes a value which never advances can itself never advance.

Watermark alignment is a runtime-adjusted, actively enforced dynamic, not a static configuration value read once. A fast source is paused the moment it exceeds the configured drift bound relative to its alignment group, and resumed once the group's slowest member closes the gap.

The percentile watermark rollup carries a stated correctness invariant on its own dynamics, not merely an implementation detail. MillWheel's own text. "By having workers compute the minima of their respective inputs, the authority's low watermark never leads the workers', and this property is preserved." The global, approximate signal can lag the true, precise signal, but the paper states it can never outrun it.

Per-key timers fire in strict, increasing timestamp order as the watermark advances past each one's scheduled value, MillWheel's own guarantee, quoted in Structure above.

Spark Structured Streaming's dynamics diverge structurally from the DAG-propagation model shared by MillWheel, Flink, and Beam. Spark's watermark is a column-attached value recomputed once per micro-batch trigger, not a value propagated operator to operator through a topology. Spark's own documentation states the formula directly. "the watermark set as (max event time minus a late threshold) at the beginning of every trigger is the red line," and ties this to window finalization concretely, "the engine waits for the threshold for late data to be counted, then drops intermediate state of a window less than the watermark, and appends the final counts to the result table." A window's final answer is only appended to the sink once the recomputed watermark has actually passed the window's end, a decision made fresh each trigger, not carried forward as a continuously propagated stream value.

Kafka Streams' dynamics are local rather than global. Stream time, quoted in Structure above, "will only advance when a new record arrives at the processor," and there is no cross-operator value to propagate. Each window's close is governed entirely locally, by that processor's own stream time plus its own configured grace period, with no equivalent of a pipeline-wide minimum.

## 8. Implementation variants

Apache Flink combines a TimestampAssigner and a WatermarkGenerator inside one WatermarkStrategy. "The Flink API expects a WatermarkStrategy that contains both a TimestampAssigner and WatermarkGenerator." The generator exposes exactly two methods, onEvent, called for every event so the generator can examine or remember timestamps or emit immediately, and onPeriodicEmit, called on an interval controlled by the execution configuration's auto-watermark-interval setting, which may or may not emit a new watermark. Two built-in strategies are named directly, forMonotonousTimestamps, and forBoundedOutOfOrderness, which "assumes that elements arrive out of order, but only to a certain degree." Idle sources are excluded through withIdleness, and drift across sources is bounded through Flink's watermark alignment feature, which pauses a fast source once it exceeds a configured maximal drift relative to its alignment group. Late data handling is a separate, composable setting on the windowed stream, allowedLateness, defaulting to zero, meaning "elements that arrive behind the watermark will be dropped," with an optional sideOutputLateData routing dropped-but-late elements to a side output instead of discarding them, and a late-but-accepted element can "trigger another firing for the window," a documented late firing. Flink's own documentation flags a superseded API pair, AssignerWithPeriodicWatermarks and AssignerWithPunctuatedWatermarks, still present but explicitly recommended against in favour of WatermarkStrategy.

Apache Beam and Google Cloud Dataflow, the model's original implementation, track a single watermark per PCollection. "Beam tracks a watermark, which is the system's notion of when all data in a certain window can be expected to have arrived in the pipeline. Once the watermark progresses past the end of a window, any further element that arrives with a timestamp in that window is considered late data." Beam's own guide is explicit that the watermark it exposes to a user is a simplification. "For simplicity, we've assumed that we're using a very straightforward watermark that estimates the lag time. In practice, your PCollection's data source determines the watermark, and watermarks can be more precise or complex." By default no late data is allowed at all, and this is widened through withAllowedLateness on a window, a setting that propagates forward to every PCollection derived from the one it is set on. The default trigger fires exactly once the watermark passes a window's end and then discards anything later, because the default allowed lateness is zero, and an AfterWatermark trigger can be composed with withEarlyFirings and withLateFirings for speculative and corrective panes.

Kafka Streams deliberately does not implement watermarks in this sense at all, a design choice named directly by a Kafka Streams committer at Confluent, not merely an omission. "By continuous refinement, I mean that Kafka Streams emits new results whenever records are updated," and, arguing the completeness signal a watermark provides is not actually required, "Whether Streams emits every single update or groups updates is irrelevant to the semantics of a data processing application." In its place, window builders take an explicit grace period, ofSizeAndGrace, ofTimeDifferenceAndGrace, ofInactivityGapWithNoGrace, and the documentation states the grace period's effect concretely. "The specified grace period of 10 minutes... allows us to bound the lateness of events the window will accept. For example, the 09:00 to 10:00 window will accept out-of-order records until 10:10, at which point, the window is closed." Continuous refinement is Kafka Streams' default emission behaviour, every update to a window's aggregate is emitted downstream immediately, the opposite default from Flink and Beam. A single, final answer per window is opted into explicitly through suppress, "This configures the suppression operator to emit nothing for a window until it closes, and then emit the final result." A comparative peer-reviewed study classifies the grace period precisely as a non-conformant, that is heuristic rather than perfect, watermark, already quoted in Name, aliases, and lineage above.

Apache Spark Structured Streaming exposes the mechanism as a DataFrame method, withWatermark, set on the event-time column immediately before an aggregation. The threshold formula and its effect on state are stated directly, quoted in full in Dynamics above. The guarantee is documented as one-directional only. "A watermark delay of, for example, two hours guarantees that the engine will never drop any data that is less than two hours delayed. However, the guarantee is strict only in one direction. Data delayed by more than two hours is not guaranteed to be dropped, it may or may not get aggregated." withWatermark is a documented no-op on a non-streaming, batch Dataset. When several streams are combined, the default policy takes the minimum watermark across them, and an opt-in setting, multipleWatermarkPolicy set to max since Spark 2.4, lets the fastest stream drive the pipeline instead, at the stated cost that slower streams' data is aggressively dropped.

## 9. Known production uses

A peer-reviewed comparative study, authored by engineers who built two of the four systems surveyed in this entry, reports a real, reproducible benchmark of watermark latency under production-realistic conditions. Begoli, Akidau, Chernyak, Hueske, Knight, Knowles, Mills, Sotolongo, Watermarks in Stream Processing Systems, Proceedings of the VLDB Endowment, Volume 14, Number 12, 2021. "We ran our Flink experiments with Apache Flink 1.12.1 on Google Compute Engine... We ran our Cloud Dataflow experiments in early February with Apache Beam 2.27. Each user worker also ran on an n1-standard-2 node using Cloud Dataflow's Streaming Engine service." Its result, stated directly. "In the Flink pipeline, the watermark latency grows only moderately from 105 milliseconds to 140 milliseconds when increasing the throughput from 10,000 to 100,000 messages per second," with both systems yielding "respectable watermark latencies in the 100s of milliseconds range, even in the face of scaling worker counts and throughput." The paper's own artifacts are published, "The source code, data, and other artifacts have been made available at s.apache.org slash watermarks-paper-beam-pipeline."

Apache Flink's own list of production users names concrete deployments at scale that depend on its event-time and watermark model. Bouygues Telecom, "30 production applications powered by Flink," processing "10 billion raw events per day." Klaviyo, a system that "deduplicates and aggregates over a million events per second." Uber, which built AthenaX, described as "an SQL-based, open-source streaming analytics platform," on top of Flink.

Apache Beam's own case studies name further deployments at comparable scale. LinkedIn, "processes 4 trillion events daily through 3,000 plus pipelines." Palo Alto Networks, processing "hundreds of billions of security events daily," reporting a "60 percent" reduction in processing costs. Credit Karma, running "5 to 10 terabytes daily at 5,000 events per second." None of these companies' own public summaries use the word watermark explicitly, an honest gap worth stating plainly rather than smoothing over. What the combination of these named deployments and the documentation in Implementation variants above establishes is that running windowed streaming aggregation at this scale on Flink or Beam is, by construction, a production use of watermark-based completeness tracking, because the windowing model these systems expose has no other mechanism for deciding a window is done.

Kafka Streams' deliberate non-adoption of the watermark and trigger model is itself a named, sourced production design decision, not merely an absence. John Roesler, a Kafka Streams committer at Confluent, states the reasoning directly in a company engineering post, already quoted in Implementation variants above, arguing that continuous refinement makes the completeness guarantee a watermark provides unnecessary for the semantics Kafka Streams targets.

## 10. Consequences

Positive. A bounded-lateness completeness signal supports work that a purely eventually-consistent, unbounded-wait approach serves poorly. The 2021 comparative paper's own abstract names four such uses directly. "Computing a single correct answer, as in notifications... Reasoning about a lack of data, as in dip detection... Performing non-incremental processing over temporal subsets of an infinite stream... Safely and punctually garbage collecting obsolete inputs and intermediate state." A watermark also functions as a general pipeline-health signal, stated in the same paper. "a [thorough] and well-instrumented watermark system provides a reliable and general signal of overall pipeline health. Since watermarks track progress throughout a data processing pipeline, any issue that impacts the pipeline's progress will manifest as a delay in its watermarks." In MillWheel and Cloud Dataflow specifically, the watermark is also the trigger for garbage collecting exactly-once deduplication state on the receiver side of a shuffle, covered further in Related and incompatible patterns below.

Negative. Data past the watermark, allowed-lateness, or grace-period horizon is dropped by default in every one of the four systems surveyed, unless the pipeline explicitly opts into a side output or a widened lateness window. The mechanism carries real implementation and operational complexity, a criticism the 2021 paper addresses directly rather than dismissing. "Another common criticism of watermarks is their complexity, but we believe this is a false argument, as systems which opt out of tackling the challenges of completeness themselves simply push that complexity onto their users." The complexity does not vanish when a system avoids watermarks, it moves to whoever consumes the output and has to reason about completeness some other way. Watermark-driven completeness carries a genuine latency cost, stated bluntly in Akidau's companion essay to the Dataflow paper. "depending upon completeness for producing output is often not ideal from a latency perspective... You simply cannot get both low latency and correctness out of a system that relies solely on notions of completeness." Choosing an out-of-orderness bound, a grace period, or an allowed-lateness value is a per-pipeline judgement call with no universally correct default, a tuning burden that falls on whoever operates the pipeline.

## 11. Failure modes and misuse

A stalled or idle partition stalls the entire pipeline's watermark. Because the watermark at any fan-in point is the minimum across every parallel upstream watermark, one silent or idle source partition holds back every downstream window from ever closing. The 2021 comparative paper names this directly. "Idle workers require special handling in Flink. A source node without watermark progress can affect the progress of the whole program." The mitigation, withIdleness, exists precisely because this is a common enough production incident to need first-class handling rather than documentation advice alone, and a pipeline that omits it on a genuinely bursty or intermittently idle source is a live misuse pattern, not a hypothetical one.

Watermark skew across sources leads to unbounded state growth. The same paper, stated directly. "Watermark skew is another common problem. For example, two source nodes can read different partitions of the same source or from completely unrelated sources. In either case, watermark progress is limited to the source node with the lowest watermark and slowest progress. Unaligned source watermarks can lead to a significant increase in state size to buffer in-flight data." Both Flink and Cloud Dataflow ship a dedicated synchronization feature, watermark alignment in Flink's case, specifically because this failure mode recurs often enough to warrant first-class tooling rather than a documentation warning.

Naive heuristics are problematic in both directions at once, not merely imprecise in one direction. The comparative paper names the two most common heuristics directly, a fixed bounded-disorder assumption and a fixed timeout, then states plainly. "We have found both of these heuristics to be problematic in practice, as they introduce unnecessary delays when the system is running well and not enough delay when problems arise, yielding large amounts of late data." A fixed constant is simultaneously too conservative on the healthy path, adding latency for no reason, and too aggressive the moment a real upstream incident occurs, dropping real data exactly when correctness matters most.

Overly conservative watermarks are a named, recurring operational pain point, not merely a theoretical trade-off. The same paper's own summary. "Watermarks do have their shortcomings. A common pain point is watermark generation algorithms which are overly conservative, resulting in unwanted delays," with the stated remedy being either tightening the watermark implementation or deliberately relaxing the completeness constraint the watermark enforces, implying there is no default setting that is correct for every pipeline, and leaving the default unexamined is itself a form of misuse.

Silent data loss from an unexamined default, a class of misuse confirmed identically across all four systems surveyed by the related event-time-processing entry. Flink drops late elements by default once the watermark has passed a window's end. Beam's default trigger emits exactly once and discards late data because the default allowed lateness is zero. Kafka Streams drops a record carrying a negative or invalid extracted timestamp. The observable production symptom, per that entry, is "a metric or count that is silently and permanently short, discovered only when totals fail to reconcile against a source-of-truth system, often days or weeks later." Arguably the single most common real-world misuse of the whole mechanism is shipping the default, zero allowed lateness, zero grace period, configuration without ever making an explicit decision about it.

Fault-recovery asymmetry between systems is a real operational risk, not merely a tuning knob. The comparative paper's own account. "Fault recovery is slower in Flink than in Cloud Dataflow due to the finer granularity at which Cloud Dataflow's state, including watermark progress, is checkpointed. When a single Cloud Dataflow node fails, a replacement node must be brought online, after which it can read its state to initialize watermark values. In contrast, when a single Flink node fails, a replacement node must be brought online, and the entire pipeline must halt, rewind, and resume from the last completed checkpoint before the failure occurred." A team that assumes both systems recover from a single-node failure with the same latency profile will be surprised in production by how differently the two behave.

## 12. Trade-off matrix

Compared against two named alternatives that solve the same underlying problem, when is a window's answer final, differently. Kafka Streams' continuous refinement over a grace period, and pure processing-time windowing, which sidesteps the question by never asking it.

| Force | Watermark-gated windowing (Flink, Beam, Dataflow) | Continuous refinement over a grace period (Kafka Streams) | Pure processing-time windowing |
|---|---|---|---|
| Completeness signal | A conformant or heuristic bound on event time, tracked and propagated through the pipeline | No global signal, a local, per-processor grace deadline decides when a window closes | None, event time is not tracked at all |
| Default emission | One final answer per window, once the watermark passes its end | Every update emitted immediately, continuous refinement, a single final answer requires opting in through suppress | One answer per window, at wall-clock boundary, unrelated to when the data actually happened |
| Late-data handling | Bounded by allowed lateness, dropped or side-outputted past the horizon, source, Beam programming guide | Bounded by the grace period, dropped once it elapses, source, Kafka Streams DSL documentation | Not meaningful, there is no event-time axis for a record to be late against |
| Operational complexity | Real and acknowledged directly by the mechanism's own designers, source, 2021 comparative paper | Lower, no trigger or pane semantics to learn, a deliberate simplification, source, Confluent engineering blog | Lowest, but the complexity has not been eliminated, it has been pushed onto whoever needs event-time correctness downstream |
| Correctness under reordering | Correct with respect to event time, by design | Correct with respect to event time, within the grace period, weaker completeness guarantee, classified as a non-conformant watermark by the 2021 comparative paper | Not correct with respect to event time at all, by construction |
| Fault-recovery granularity | Differs by system, coarse pipeline-wide rewind in Flink against fine per-node recovery in Cloud Dataflow, source, 2021 comparative paper | Not directly comparable, no propagated watermark state to recover | Not directly comparable, no event-time state to recover |

A further axis worth naming inside the watermark-gated column itself, since Flink and Cloud Dataflow answer it differently even though both use the same underlying model. Flink propagates the watermark in-band with the data stream and never persists it centrally. Cloud Dataflow persists watermark progress to a central aggregator, a "slightly higher" per-hop latency traded for materially faster, finer-grained fault recovery, both already sourced in Forces and Failure modes above.

## 13. Related and incompatible patterns

Event-Time Processing, the related sibling entry in this same family, is the umbrella discipline watermark is one constituent mechanism of. That entry's own words on the relationship, quoted directly. "Watermarking without windowing is meaningless, there is nothing to close. Windowing without a watermark degenerates to processing-time windowing, with no signal for when a window is done, only wall-clock elapsed time. The two are mutually necessary, not merely compatible, whenever event-time correctness with bounded output latency is the goal." Watermark supplies the when, in processing time, a window's event-time contents can be considered materializable, per that entry's own dimension 13.

Windowing, queued in this repository and not yet authored. Windowing answers where in event time data is grouped, watermark answers when, in processing time, a grouping can be considered done. The two are drafted as tightly coupled but conceptually distinct dimensions, and whoever authors the Windowing entry will need to decide, without this entry pre-empting that decision, which of the two entries is the canonical home for the mechanics of trigger firing on watermark crossing and for allowed-lateness handling, since both facts have a legitimate claim from either side, and both already appear once in the related event-time-processing entry.

Exactly-Once Processing, queued. The 2021 comparative paper states a direct, compositional dependency, not merely a thematic one. "MillWheel and Cloud Dataflow utilize system-time watermarks to determine when it is safe to garbage collect exactly-once deduplication data on the receiver side of a shuffle between two physical stages in the pipeline." Exactly-once deduplication state cleanup in these two systems is gated on watermark advancement.

Stream Backpressure, queued. Flink's watermark alignment is, functionally, a targeted form of backpressure, deliberately pausing a fast-progressing source's consumption to bound in-flight state, the same lever general backpressure uses, triggered here specifically by watermark drift rather than by downstream queue depth.

Dead-Letter Topic, queued. The natural companion to the silent-drop failure mode named in Failure modes and misuse above. Rather than letting data past the watermark, allowed-lateness, or grace-period horizon vanish, a deliberately designed pipeline routes it to a side output or dead-letter sink, Flink's sideOutputLateData being the concrete, sourced example, instead of discarding it.

Punctuations, an academically earlier, related but distinct completeness mechanism, named in the Dataflow paper's own related-work section and not itself a pattern queued in this repository. The paper frames watermarks as a deliberately more tractable special case chosen over the harder-to-implement-efficiently general punctuation model, "the generality of punctuations is also their weakness... the arbitrary nature of the predicates makes efficient state management for updating and propagating the punctuations through the pipeline hard," a framing the Kafka Streams comparison above independently corroborates, since a grace period is functionally a much narrower, more tractable special case of the same idea again.

Incompatible or in direct tension. Pure processing-time-only systems, a logical incompatibility rather than a weaker alternative, stated directly by the related sibling entry. "Processing-time-only windowing is not merely a weaker alternative to event-time processing, it is logically incompatible with the correctness goal event-time processing exists to solve. Correct temporal grouping regardless of arrival order cannot be retrofitted onto a processing-time window after the fact, because the information about when things actually happened was never captured in the grouping decision." A watermark has nothing to track in such a system, there is no event-time axis for it to bound.

Kafka Streams' continuous-refinement default is in direct philosophical tension with the watermark and trigger model, not merely a different implementation of the identical idea, already quoted in Implementation variants and Known production uses above. A team porting a Flink or Beam pipeline, which relies on the watermark's one-final-answer guarantee, onto Kafka Streams without adding suppress will silently change the pipeline's output semantics from one final answer per window to many intermediate answers per window, a change downstream consumers built against the watermark model will not expect.

Systems that require a single, perfectly ordered global clock, of largely academic or legacy interest, are in tension with a heuristic watermark by construction, since a heuristic watermark explicitly trades strict ordering guarantees for a practical, bounded-latency estimate. A system demanding provably perfect ordering needs either a conformant watermark, achievable only with complete source knowledge such as a bounded replay, or a fundamentally different mechanism altogether.

## 14. Refactoring path in and out

Migrating in, within an already-adopted engine. Flink's own documentation states a real, still-live, low-risk migration path for a pipeline already using the mechanism under an older API. "Prior to introducing the current abstraction of WatermarkStrategy, TimestampAssigner, and WatermarkGenerator, Flink used AssignerWithPeriodicWatermarks and AssignerWithPunctuatedWatermarks. You will still see them in the API but it is recommended to use the new interfaces." The old interfaces remain present and functional, which is the ordinary shape of an internal API migration, move at the team's own pace, with a concrete, named replacement target.

Migrating in, from a processing-time-only system. The lowest-effort on-ramp, named directly by the Dataflow paper and already cited in Applicability and non-applicability above, is to assign arrival time as event time at ingestion, rather than attempting to recover true event time from a legacy source immediately. This gives the system, in the paper's own words, "perfect knowledge of the event times in flight," and therefore "perfect, that is non-heuristic, watermarks, with no late data," from the very first step. A team can adopt the watermark mechanism itself with zero out-of-orderness handling on day one, then progressively push true event-time extraction upstream as individual sources are able to supply it, tightening the watermark's heuristic bound incrementally rather than all at once.

The mechanical first step differs by engine, all four already sourced in Implementation variants above. In Flink, attach a WatermarkStrategy to the source through assignTimestampsAndWatermarks, and set an explicit allowedLateness on the window rather than accepting the zero default. In Beam, set the source's watermark policy, which is source-dependent, and call withAllowedLateness explicitly. In Spark, add withWatermark on the event-time column, immediately before, not after, the aggregation it feeds. In Kafka Streams, switch a window builder from a no-grace constructor, ofSizeWithNoGrace or ofInactivityGapWithNoGrace, to an explicit grace-bearing one, ofSizeAndGrace or ofTimeDifferenceAndGrace, and add suppress if a single final answer per window, rather than continuous refinement, is what the downstream consumer expects.

A real, sourced motivating case for adopting the model exists inside the Dataflow paper itself. Two internal MillWheel-based teams building processing-time-only billing and resource-utilization pipelines hit correctness problems severe enough to directly motivate parts of the eventual model, one team's own account, already carried in the related sibling entry, states plainly that the earlier system's lack of a "principled system for updates and retractions" led it to abandon the platform for a custom solution rather than continue without event-time correctness.

Migrating away. No documented case of a team deliberately removing an already-working watermark-based pipeline in favour of a different late-data strategy was found across either research pass behind this entry, and none should be invented to fill the gap. The one directly relevant, sourced data point is architectural rather than a migration narrative, Kafka Streams' own designers chose, from the project's inception, not to build a watermark-and-trigger model at all, preferring grace periods and continuous refinement instead, a documented decision to never adopt the mechanism, not a documented account of abandoning it once adopted.

## 15. Testing and verification

Watermark-driven code is hard to test with real time, because the whole point of the mechanism is to react to a progress signal that, in production, advances unpredictably relative to the wall clock. Both Beam and Flink ship a dedicated, official testing facility that lets a test control watermark advancement directly rather than waiting on real time.

Beam's TestStream is a PTransform built specifically for this. Its own description, from Beam's blog documentation on testing unbounded pipelines. "A PTransform that performs a series of events, consisting of adding additional elements to a pipeline, advancing the watermark of the TestStream, and advancing the pipeline processing time clock." TestStream lets a test inject elements at chosen event times, advance the watermark to a chosen value on command, and separately advance the simulated processing-time clock, which makes it possible to write a deterministic, non-flaky unit test that exercises early, on-time, and late firings, speculative panes, and corrective panes, all without a real clock or a real out-of-order network in the loop.

Flink ships dedicated operator test utility classes for the same purpose, named directly in its testing documentation, `OneInputStreamOperatorTestHarness`, `KeyedOneInputStreamOperatorTestHarness`, `TwoInputStreamOperatorTestHarness`, and `ProcessFunctionTestHarnesses`, among others. A test drives a watermark's advancement explicitly through one of these classes, "trigger event time timers by advancing the event time of the operator with a watermark," via a call such as `testHarness.processWatermark`. As with TestStream, this makes timer firing, window closing, and late-data handling testable deterministically, on a timeline the test itself controls, rather than on the real system clock.

What becomes easy to test because of the mechanism, exactly the on-time, early, and late firing paths a naive processing-time-only test could never exercise deterministically, since real out-of-order arrival cannot reliably be reproduced against a real clock in a unit test. What becomes harder, the interaction between watermark advancement and checkpoint or savepoint recovery, since a correct test must also assert that watermark state itself survives a simulated fault and resumes from the right point, a scenario neither TestStream nor Flink's own test utility classes are described, in the sources verified for this entry, as covering directly, and which is better exercised at an integration or end-to-end test tier rather than a unit test tier.

## 16. Observability signals

The watermark's own value and its rate of advance are the single most direct health signal a pipeline built on this mechanism can expose, a claim the 2021 comparative paper states as a general property of the mechanism, quoted in full in Consequences above, any issue that impacts a pipeline's progress manifests as a delay in its watermarks.

Flink exposes the watermark itself as a set of named, documented per-task and per-operator metrics, verified directly from its metrics documentation. currentInputWatermark, "The last watermark this operator or task has received, in milliseconds. Note, for operators or tasks with two inputs this is the minimum of the last received watermarks." currentInputNWatermark, the same value broken out per numbered input for a multi-input operator, currentInput1Watermark, currentInput2Watermark, and so on. currentOutputWatermark, "The last watermark this operator has emitted, in milliseconds." A per-split variant, watermark.currentWatermark, exists for a source split. Read together, these expose exactly the min-of-inputs propagation chain described in Structure and Dynamics above, so a stalled input on one specific numbered input, rather than the operator as a whole, is directly diagnosable from currentInputNWatermark without inferring it indirectly.

Google Cloud Dataflow documents an equivalent operational concept named data freshness rather than watermark lag, defined explicitly in terms of the same underlying signal. "Data freshness is the difference between the time when a data element is processed, processing time, and the data element's timestamp, event time." The same page ties a widening gap directly back to a stuck or slow operation. "If some input data has not yet been processed, the output watermark might be delayed, which affects data freshness," and, "A significant difference between the watermark time and the event time might indicate a slow or stuck operation." This is the direct, documented operational counterpart of the stalled-partition failure mode named in Failure modes and misuse above, a widening data-freshness gap is what that failure mode looks like on a dashboard before it is diagnosed as a specific stalled source.

A healthy instance, read against these signals, shows currentOutputWatermark advancing at a rate close to real time, tracking the input rate, with data freshness or watermark lag staying within a small, roughly constant band. A failing instance shows currentInputWatermark for one specific input frozen while its siblings continue advancing, the exact per-input diagnostic these metrics exist to surface, or a data-freshness gap that grows without bound rather than tracking real time, both of which point directly at the stalled-partition and watermark-skew failure modes named above, well before a downstream reconciliation discrepancy would otherwise surface the same problem days or weeks later.

## 17. Security and privacy implications

None of the sources behind this entry, across two independent research passes, address watermark-specific security or privacy concerns directly, and this dimension says so plainly rather than inventing a threat model no primary source supports. Watermark itself carries no payload data, it is a progress-tracking value derived from timestamps, so it does not introduce a new data-exfiltration or injection surface in the way a field carrying user content would.

Two implications follow as reasoned judgement from facts already sourced elsewhere in this entry, rather than from a source that discusses them as security concerns specifically. First, a wider allowed-lateness or grace-period window, the direct trade named in Forces and Consequences above, means holding buffered per-window state alive for longer. Any data-retention or deletion-window requirement a pipeline is subject to needs to account for this buffering horizon explicitly, since data judged eligible for deletion by wall-clock time may still be sitting in live, in-memory or checkpointed operator state if it belongs to a window whose watermark has not yet passed. Second, an event-time field that is client-supplied and not independently validated is, by construction, an input an upstream party can set to an arbitrary value. A deliberately or accidentally malformed timestamp, far in the past or far in the future, does not compromise the watermark mechanism's own correctness, since the min-of-inputs rule and idle-source exclusion already bound its effect, but it can degrade a specific pipeline's observed watermark lag or hold a window's state open longer than intended, an operational effect rather than a security breach in the conventional sense.

Billing correctness, already named as a driving use case in Applicability and non-applicability above, has an audit and compliance dimension worth stating explicitly even though no source in this entry frames it as such. A watermark tuned too aggressively for latency, rather than for the correctness a billing pipeline specifically needs, produces a systematically wrong financial answer rather than a randomly wrong one, since the same heuristic bias applies to every window. This is a data-integrity concern adjacent to, but distinct from, the security surface conventionally covered by this dimension in other entries in this repository, and it is named here for completeness rather than smoothed over.

## 18. References

Tyler Akidau, Alex Balikov, Kaya Bekiroglu, Slava Chernyak, Josh Haberman, Reuven Lax, Sam McVeety, Daniel Mills, Paul Nordstrom, Sam Whittle. "MillWheel: Fault-Tolerant Stream Processing at Internet Scale." Proceedings of the VLDB Endowment, Volume 6, Number 11, pages 1033 to 1044, 2013. https://www.vldb.org/pvldb/vol6/p1033-akidau.pdf. Verified 2026-08-23.

Tyler Akidau, Robert Bradshaw, Craig Chambers, Slava Chernyak, Rafael J. Fernandez-Moctezuma, Reuven Lax, Sam McVeety, Daniel Mills, Frances Perry, Eric Schmidt, Sam Whittle. "The Dataflow Model: A Practical Approach to Balancing Correctness, Latency, and Cost in Massive-Scale, Unbounded, Out-of-Order Data Processing." Proceedings of the VLDB Endowment, Volume 8, Number 12, pages 1792 to 1803, 2015. https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf. Verified 2026-08-23.

Edmon Begoli, Tyler Akidau, Slava Chernyak, Fabian Hueske, Sean Knight, Kenneth Knowles, Daniel Mills, Dan Sotolongo. "Watermarks in Stream Processing Systems: Semantics and Comparative Analysis of Apache Flink and Google Cloud Dataflow." Proceedings of the VLDB Endowment, Volume 14, Number 12, pages 3135 to 3147, 2021. http://www.vldb.org/pvldb/vol14/p3135-begoli.pdf. Verified 2026-08-23.

Tyler Akidau. "The world beyond batch: Streaming 101." O'Reilly Radar, 5 August 2015. https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/. Verified 2026-08-23.

Tyler Akidau. "The world beyond batch: Streaming 102." O'Reilly Radar, 20 January 2016. https://www.oreilly.com/radar/the-world-beyond-batch-streaming-102/. Verified 2026-08-23.

Peter A. Tucker, David Maier, Tim Sheard, Leonidas Fegaras. "Exploiting punctuation semantics in continuous data streams." IEEE Transactions on Knowledge and Data Engineering, Volume 15, 2003. Cited via the Dataflow Model paper's own bibliography entry [30], not independently fetched in the research behind this entry.

Utkarsh Srivastava, Jennifer Widom. "Flexible Time Management in Data Stream Systems." Proceedings of the 23rd ACM SIGMOD-SIGACT-SIGART Symposium on Principles of Database Systems, pages 263 to 274, 2004. Cited via the Dataflow Model paper's own bibliography entry [28], not independently fetched in the research behind this entry.

Apache Flink documentation. "Generating Watermarks." https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/event-time/generating_watermarks/. Verified 2026-08-23.

Apache Flink documentation. "Timely Stream Processing." https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/time/. Verified 2026-08-23.

Apache Flink documentation. "Windows." https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/operators/windows/. Verified 2026-08-23.

Apache Flink documentation. "Testing." https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/testing/. Verified 2026-08-23.

Apache Flink documentation. "Metrics." https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/metrics/. Verified 2026-08-23.

Apache Flink. "Powered By." https://flink.apache.org/what-is-flink/powered-by/. Verified 2026-08-23.

Apache Beam documentation. "Programming Guide," section 8.4, Watermarks and late data. https://beam.apache.org/documentation/programming-guide/#watermarks-and-late-data. Verified 2026-08-23.

Apache Beam. "Testing Unbounded Pipelines in Apache Beam." https://beam.apache.org/blog/test-stream/. Verified 2026-08-23.

Apache Beam. "Case Studies." https://beam.apache.org/case-studies/. Verified 2026-08-23.

Apache Kafka documentation. "Streams DSL." https://kafka.apache.org/43/streams/developer-guide/dsl-api/. Verified 2026-08-23.

Apache Kafka documentation. "Core Concepts," Streams. https://kafka.apache.org/43/streams/core-concepts/. Verified 2026-08-23.

John Roesler. "Kafka Streams' Take on Watermarks and Triggers." Confluent blog, 2019. https://www.confluent.io/blog/kafka-streams-take-on-watermarks-and-triggers/. Verified 2026-08-23.

Apache Spark documentation. "Structured Streaming Programming Guide," Handling Late Data and Watermarking. https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html. Verified 2026-08-23.

Google Cloud documentation. "Using monitoring interfaces," Dataflow. https://docs.cloud.google.com/dataflow/docs/guides/using-monitoring-intf. Verified 2026-08-23.

patterns/24-stream-processing/event-time-processing.md. The related sibling entry in this repository, cited directly for its own stated relationship between event-time processing, windowing, and watermarks, and for its own security and privacy reasoning, reused here as a cross-reference rather than restated as independent fact.

```markdown
**Evidence grade.** high

**Most solid findings.** The core min-of-upstream-watermarks algorithm is confirmed identically from two independently built systems a decade apart, MillWheel's 2013 paper and Flink's current documentation, both read directly. The four-system implementation comparison in dimension 8, Flink, Beam, Kafka Streams, Spark, draws on each project's own current, live-fetched documentation rather than a secondary aggregator, and Kafka Streams' deliberate non-adoption of the watermark model is independently corroborated by a named committer's own engineering blog post, not inferred from the absence of the word alone. The failure-mode and trade-off content in dimensions 11 and 12 rests on a single peer-reviewed comparative paper authored by engineers who built two of the four systems surveyed, giving it unusually direct, first-party grounding for a catalogue entry.

**Unverified or unclear.** No named-company production incident specifically about watermark tuning was found, despite a genuine search effort, dimension 9's production-use claims rest on real deployments at real scale rather than a watermark-specific incident narrative. The Tucker et al. 2003 and Srivastava and Widom 2004 papers are cited only via the Dataflow paper's own bibliography, not independently fetched, and should not be treated as directly verified beyond what the Dataflow paper itself states about them. Dimension 17's security and privacy content is explicitly reasoned judgement, not sourced from a primary source discussing watermark security directly, and is labelled as such in the text itself.
```

## Code

TypeScript, Python, and Go each model a minimal watermark tracker directly, the mechanism dimension 5 describes, source generation, per-source merge as a minimum, idle-source exclusion, and per-key timers firing as the watermark advances, rather than the fuller windowing and triggering engine the related event-time-processing entry's own code samples already cover. Kotlin and Swift are omitted for the same reason as the sibling entry, neither has a first-party streaming-windowing library idiomatic enough to demonstrate the mechanism without pulling in a large external dependency.

### TypeScript

```typescript
type SourceId = string;

interface PendingTimer {
  key: string;
  fireAt: number;
}

class WatermarkTracker {
  private sourceWatermarks = new Map<SourceId, number>();
  private idleSince = new Map<SourceId, number>();
  private idleTimeoutMs: number;
  private timers: PendingTimer[] = [];
  private currentWatermark = Number.NEGATIVE_INFINITY;

  constructor(idleTimeoutMs: number) {
    this.idleTimeoutMs = idleTimeoutMs;
  }

  // A source reports its own progress. This is the per-source generator step.
  onEvent(source: SourceId, eventTime: number, nowMs: number): void {
    this.sourceWatermarks.set(source, eventTime);
    this.idleSince.delete(source);
    this.recompute();
  }

  // Called periodically, models onPeriodicEmit against the wall clock.
  tick(nowMs: number): void {
    for (const [source] of this.sourceWatermarks) {
      if (!this.idleSince.has(source)) this.idleSince.set(source, nowMs);
      const idleFor = nowMs - (this.idleSince.get(source) ?? nowMs);
      if (idleFor > this.idleTimeoutMs) this.sourceWatermarks.delete(source);
    }
    this.recompute();
  }

  scheduleTimer(key: string, fireAt: number): void {
    this.timers.push({ key, fireAt });
  }

  // The min-of-inputs rule. Every active, non-idle source bounds the result.
  private recompute(): void {
    const active = [...this.sourceWatermarks.values()];
    if (active.length === 0) return;
    const next = Math.min(...active);
    if (next <= this.currentWatermark) return;
    this.currentWatermark = next;
    this.fireDueTimers();
  }

  private fireDueTimers(): void {
    this.timers.sort((a, b) => a.fireAt - b.fireAt);
    while (this.timers.length > 0 && this.timers[0].fireAt <= this.currentWatermark) {
      const timer = this.timers.shift()!;
      this.onTimerFired(timer.key, timer.fireAt);
    }
  }

  private onTimerFired(key: string, fireAt: number): void {
    console.log("timer fired key=" + key + " at=" + fireAt + " watermark=" + this.currentWatermark);
  }

  get watermark(): number {
    return this.currentWatermark;
  }
}
```

### Python

```python
import math
from dataclasses import dataclass


@dataclass
class PendingTimer:
    key: str
    fire_at: float


class WatermarkTracker:
    # Idle timeout excludes a stalled source from the min-of-inputs rule.
    def __init__(self, idle_timeout: float) -> None:
        self._source_watermarks: dict[str, float] = {}
        self._idle_since: dict[str, float] = {}
        self._idle_timeout = idle_timeout
        self._timers: list[PendingTimer] = []
        self._current_watermark = -math.inf

    def on_event(self, source: str, event_time: float, now: float) -> None:
        self._source_watermarks[source] = event_time
        self._idle_since.pop(source, None)
        self._recompute()

    def tick(self, now: float) -> None:
        for source in list(self._source_watermarks):
            since = self._idle_since.setdefault(source, now)
            if now - since > self._idle_timeout:
                del self._source_watermarks[source]
        self._recompute()

    def schedule_timer(self, key: str, fire_at: float) -> None:
        self._timers.append(PendingTimer(key, fire_at))

    def _recompute(self) -> None:
        if not self._source_watermarks:
            return
        candidate = min(self._source_watermarks.values())
        if candidate <= self._current_watermark:
            return
        self._current_watermark = candidate
        self._fire_due_timers()

    def _fire_due_timers(self) -> None:
        self._timers.sort(key=lambda t: t.fire_at)
        while self._timers and self._timers[0].fire_at <= self._current_watermark:
            timer = self._timers.pop(0)
            self._on_timer_fired(timer.key, timer.fire_at)

    def _on_timer_fired(self, key: str, fire_at: float) -> None:
        print("timer fired key=" + key + " at=" + str(fire_at) + " watermark=" + str(self._current_watermark))

    @property
    def watermark(self) -> float:
        return self._current_watermark
```

### Go

```go
package watermark

import (
	"fmt"
	"math"
	"sort"
)

type pendingTimer struct {
	key    string
	fireAt float64
}

// Tracker applies the min-of-inputs rule across active sources,
// excludes an idle source, and fires per-key timers in order.
type Tracker struct {
	sourceWatermarks map[string]float64
	idleSince        map[string]float64
	idleTimeout      float64
	timers           []pendingTimer
	current          float64
}

func NewTracker(idleTimeout float64) *Tracker {
	return &Tracker{
		sourceWatermarks: make(map[string]float64),
		idleSince:        make(map[string]float64),
		idleTimeout:      idleTimeout,
		current:          math.Inf(-1),
	}
}

func (t *Tracker) OnEvent(source string, eventTime, now float64) {
	t.sourceWatermarks[source] = eventTime
	delete(t.idleSince, source)
	t.recompute()
}

func (t *Tracker) Tick(now float64) {
	for source := range t.sourceWatermarks {
		since, ok := t.idleSince[source]
		if !ok {
			t.idleSince[source] = now
			continue
		}
		if now-since > t.idleTimeout {
			delete(t.sourceWatermarks, source)
		}
	}
	t.recompute()
}

func (t *Tracker) ScheduleTimer(key string, fireAt float64) {
	t.timers = append(t.timers, pendingTimer{key: key, fireAt: fireAt})
}

func (t *Tracker) recompute() {
	if len(t.sourceWatermarks) == 0 {
		return
	}
	candidate := math.Inf(1)
	for _, wm := range t.sourceWatermarks {
		if wm < candidate {
			candidate = wm
		}
	}
	if candidate <= t.current {
		return
	}
	t.current = candidate
	t.fireDueTimers()
}

func (t *Tracker) fireDueTimers() {
	sort.Slice(t.timers, func(i, j int) bool { return t.timers[i].fireAt < t.timers[j].fireAt })
	for len(t.timers) > 0 && t.timers[0].fireAt <= t.current {
		next := t.timers[0]
		t.timers = t.timers[1:]
		fmt.Println("timer fired key=" + next.key + " watermark=" + fmt.Sprint(t.current))
	}
}

func (t *Tracker) Watermark() float64 {
	return t.current
}
```
