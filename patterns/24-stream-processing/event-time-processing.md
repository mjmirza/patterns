---
name: Event-Time Processing
slug: event-time-processing
family: 24-stream-processing
category: Stream Processing
aliases: []
first_described: "Tyler Akidau, Robert Bradshaw, Craig Chambers, Slava Chernyak, Rafael J. Fernandez-Moctezuma, Reuven Lax, Sam McVeety, Daniel Mills, Frances Perry, Eric Schmidt, Sam Whittle, The Dataflow Model, Proceedings of the VLDB Endowment, Volume 8, Number 12, pages 1792 to 1803, 2015"
maturity: established
related: [watermark, windowing, lambda-architecture]
incompatible_with: []
verified: 2026-08-23
---

## 1. Name, aliases, and lineage

Event-Time Processing is the discipline of grouping and computing over streaming records according to the timestamp when they occurred in the real world, the event time, rather than the timestamp when the processing system happened to observe them, the processing time. The companion, contrasting term used across every source is processing-time processing, or simply processing time.

The formal treatment of this distinction, together with watermarks as a heuristic completeness estimator and a four-question decomposition (what, where, when, how), was introduced as the Dataflow Model by Tyler Akidau and ten co-authors, published in the Proceedings of the VLDB Endowment, Volume 8, Number 12, pages 1792 to 1803, presented at the 41st International Conference on Very Large Data Bases, Kohala Coast, Hawaii, 31 August to 4 September 2015. The paper's own footnote states its scope directly. "We use the term Dataflow Model to describe the processing model of Google Cloud Dataflow, which is based upon technology from FlumeJava and MillWheel."

The watermark mechanism that event-time processing depends on to know when a window is done enough to emit was formally defined two years earlier, in the MillWheel paper (Akidau et al., Proceedings of the VLDB Endowment, Volume 6, Number 11, pages 1033 to 1044, 2013), not the Dataflow paper. MillWheel's own definition, quoted directly. "The low watermark for a computation provides a bound on the timestamps of future records arriving at that computation." Given a computation A, the low watermark is defined recursively as "min(oldest work of A, low watermark of C : C outputs to A)." The Dataflow paper credits this lineage in its own footnote, describing "something like MillWheel's watermark, which is a lower bound (often heuristically established) on event times that have been processed."

So the lineage runs, MillWheel (2013) introduces the low watermark as a per-computation progress metric inside a specific streaming execution engine at Google. The Dataflow Model (2015) generalizes this into a full model, formally separating event time and processing time as two orthogonal domains, reusing the watermark for event-time completeness, and adding windowing plus a triggering model that decouples what is computed from when results are emitted. This model was operationalized as Google Cloud Dataflow and, per the paper's own statement, externalized as a runtime-agnostic SDK, the lineage that became Apache Beam. Independently, Apache Flink converged on the identical event-time and processing-time vocabulary with its own watermark mechanism, and the Dataflow paper's own related-work section names Flink's predecessor by name, noting that "Stratosphere/Flink" already had "limited window triggering semantics in event-time mode" before the Dataflow paper's own proposal.

Event-Time Processing is the umbrella discipline that two other, separately catalogued patterns serve as mechanisms. Watermark is the progress-tracking mechanism that estimates event-time completeness. Windowing is the grouping mechanism that slices the event-time axis into finite buckets. The Dataflow paper states this relationship in one sentence. "Windowing determines where in event time data are grouped together for processing" while "Triggering determines when in processing time the results of groupings are emitted as panes." This entry treats Event-Time Processing as the discipline; Watermark and Windowing are not re-explained here beyond what is needed to place this pattern among them.

No standalone Wikipedia article exists under the exact name "Event-Time Processing." Wikipedia's own article on Apache Beam states the lineage independently. "Apache Beam is one implementation of the Dataflow model paper," based on "previous work on distributed processing abstractions at Google, in particular on FlumeJava and Millwheel," released "as an open SDK implementation of the Dataflow model in 2014" before becoming an Apache Software Foundation project with its first release on 15 June 2016.

## 2. Problem and context

The Dataflow paper states the root cause directly. "Event time for a given event essentially never changes, but processing time changes constantly for each event as it flows through the pipeline and time marches ever forward." The paper names the mechanism behind the mismatch. "During processing, the realities of the systems in use (communication delays, scheduling algorithms, time spent processing, pipeline serialization, etc.) result in an inherent and dynamically changing amount of skew between the two domains."

The paper's own running example, carried through the entire remainder of the paper, is a streaming video platform that wants to bill advertisers for video views, needing "the time and length of each video viewing, who viewed it, and with which ad or content it was paired." If the platform grouped billing events by when the billing system received the record rather than when the person actually watched the video, an advertiser could be billed for the wrong day, or a viewing session could split across the wrong hourly bucket purely from pipeline latency, not from anything about the person's actual behaviour.

A concrete, named failure mode appears independently in two of the paper's own related publications, in near-identical phrasing. The Dataflow paper's own footnote on why watermarks can only ever be heuristic. "If someone takes their mobile device into the wilderness, the system has no practical way of knowing when they might come back to civilization, regain connection, and begin uploading data about video views during that time." Akidau's companion essay, Streaming 101, generalizes the same scenario. "In cases where a given mobile device goes offline for any amount of time (brief loss of connectivity, airplane mode while flying across the country, etc.), the data recorded during that period won't be uploaded until the device comes online again," producing "event time skew of minutes, hours, days, weeks, or more."

The paper's own Figure 12 walks through a concrete, granular case of the same problem inside a single running pipeline, not just a device going offline. A datum with value 9 arrives late relative to the watermark, because an earlier datum with value 5 arrived first and the system had no way to know the 9 was still outstanding. "Hence, once the 9 finally arrives, it causes the first window (for event time range [12:00, 12:02)) to retrigger with an updated sum." This is the paper's own illustration of what late data concretely looks like, and what a correctly designed system must do about it, rather than silently produce a wrong final answer.

The practical payoff of solving this, stated in Apache Flink's own documentation. "Event time operations will behave as expected, and produce correct and consistent results even when working with out-of-order or late events, or when reprocessing historic data." The implicit failure this solves, stated directly for the processing-time alternative. "It provides the best performance and the lowest latency. However, in distributed and asynchronous environments processing time does not provide determinism." A processing-time-based system, run twice over the same input, once live and once as a replay for backfill or debugging, produces different answers each time, because processing time is a property of when the machine happened to see the data, which is non-deterministic across runs, machines, and network conditions.

## 3. Forces

Several of the trade-offs below are directly and explicitly named by the sources as deliberate choices, which makes them sourced claims rather than pure engineering judgement; each is marked as such.

Latency versus correctness and completeness, the paper's own headline framing. The paper's own title states this as the central tension. "A Practical Approach to Balancing Correctness, Latency, and Cost." The paper is explicit that these forces cannot all be maximized at once, and that the model exists to make the trade-off tunable rather than fixed. "practicality dictates that one can never fully optimize along all dimensions of correctness, latency, and cost for these types of input."

The watermark-as-sole-completeness-signal trap, named explicitly as too fast versus too slow. The paper states plainly that relying on watermarks alone is insufficient, naming "two major shortcomings with respect to correctness." Watermarks are "sometimes too fast, meaning there may be late data that arrives behind the watermark," because "it is intractable to derive a completely perfect event time watermark." They are also "sometimes too slow... the watermark can be held back for the entire pipeline by a single slow datum," even for otherwise healthy pipelines where "the baseline level of skew may still be multiple minutes or more." Akidau's companion essay, Streaming 102, sharpens this with a concrete figure, describing a case where waiting for a watermark to correctly account for known slow data can mean waiting "nearly seven minutes from the time the first value in the window occurs until we see any results," concluding. "You simply cannot get both low latency and correctness out of a system that relies solely on notions of completeness."

Buffering-state cost against correctness and refinement. Supporting retractions and accumulating window semantics, needed to correctly refine an answer as late data arrives, has an explicit resource cost. Akidau's essay names the mitigation directly, "placing a bound on how late any given record may be (relative to the watermark) for the system to bother processing it; any data that arrive after this horizon are simply dropped." This is the direct trade, a longer allowed-lateness window buys more correctness at the cost of holding more state alive for longer per window.

Determinism and reproducibility versus raw throughput or lowest possible latency. Flink's own docs state the processing-time side of the trade directly. Processing time "provides the best performance and the lowest latency," at the direct cost that "in distributed and asynchronous environments processing time does not provide determinism." Event time buys reproducible, replay-consistent answers at the cost of having to wait for, or heuristically estimate, completeness before a window can be considered done.

Which forces the pattern favours, and which it deliberately sacrifices, stated as judgement. Event-time processing structurally favours correctness and reproducibility of the answer relative to what actually happened, at the direct and unavoidable cost of latency and of implementation and operational complexity. It sacrifices the guarantee that the first answer produced is the final answer. The Dataflow paper's own account of two internal MillWheel-based billing pipelines shows exactly this cost when the model did not yet exist. "Another billing team had significant issues with watermark lags caused by stragglers in their input."

## 4. Applicability and non-applicability

When event-time processing matters, drawn from the paper's own stated design goals and its Motivating Experiences section.

Billing and monetization pipelines where the amount charged must correspond to what actually happened, not to when the system noticed it. This is the paper's own running example, and its section on billing states the real cost of getting it wrong directly. "Two teams with billing pipelines built on MillWheel experienced issues that motivated parts of the model... Lacking a principled system for updates and retractions, a team that processed resource utilization statistics ended up leaving our platform to build a custom solution."

Analytics requiring correctness and reproducibility across re-runs, including backfills and offline reprocessing of historical data. The paper's own section on large-scale backfills states the motivating need. "A number of teams run log joining pipelines on MillWheel... A much nicer setup would be to have a single implementation written in a unified model that could run in both streaming and batch mode without modification." Flink's docs give the same justification generally. "Event time operations... produce correct and consistent results even when... reprocessing historic data."

Session-based analysis of user behaviour, correlating bursts of otherwise disjoint activity over a period of time. The paper states this was a first-class motivating requirement. "Sessions are an extremely important use case within Google (and were in fact one of the reasons MillWheel was created), and are used across a number of product areas, including search, ads, analytics, social, and YouTube."

When event-time processing is not necessary, or is the wrong tool, with reasons drawn from the paper's own internal counter-examples.

Monitoring or anomaly-detection systems where a fast, rough signal matters more than complete correctness against event time. The paper's own abuse-detection pipeline is stated directly. "Abuse detection is another example of a use case where processing a majority of data quickly is much more useful than processing 100% of the data more slowly... they are heavy users of MillWheel's percentile watermarks."

Spike or trend detection over live query streams, where a processing-time-based, arrival-order signal is sufficient because the thing being measured is recent arrival behaviour itself. The paper's own web-search trend-detection pipeline deliberately avoided watermark-based triggers, because forcing that completeness "essentially transforms the streaming system into micro-batch, introducing additional latency," which the use case could not tolerate.

Recommendation systems built from continuously-updated live views, where waiting for event-time completeness actively degrades the product. The paper states this as a deliberate, named production choice. "having regularly updated, partial views on the data was much more valuable than waiting until mostly complete views were ready once the watermark passed the end of the session. It also meant that lags in watermark progress due to a small amount of slow data would not affect timeliness of output for the rest of the data."

A named middle ground worth carrying forward. The paper states that arrival time can be assigned as event time at ingestion, then windowed normally, and calls this "an effective and cost-efficient way of processing unbounded data for use cases where true event times are not necessary or available," because the system then has "perfect knowledge of the event times in flight," giving "perfect (i.e. non-heuristic) watermarks, with no late data."

## 5. Structure

Each participant below is drawn from and cited to a specific source; the arrangement into a structure list is this entry's own organization.

Timestamp assignment, the mechanism by which every element entering the system is stamped with the event time it occurred at, rather than relying on wall-clock arrival time. The paper states this as a core primitive. "to support event-time windowing natively, instead of passing (key, value) pairs through the system, we now pass (key, value, event_time, window) 4-tuples. Elements are provided to the system with event-time timestamps (which may also be modified at any point in the pipeline)."

The stream of unbounded, unordered records, the raw input. "Unbounded, unordered, global-scale datasets are increasingly common in day-to-day business (e.g. Web logs, mobile usage statistics, and sensor networks)."

Watermark generator, the component responsible for producing the low watermark, the bound below which no more event times are expected. Formally defined recursively in the MillWheel paper, and reused unmodified as "something like MillWheel's watermark, which is a lower bound (often heuristically established) on event times that have been processed by the pipeline." Flink formalizes the same guarantee. "A Watermark(t) declares that event time has reached time t in that stream, meaning that there should be no more elements from the stream with a timestamp t prime less than or equal to t."

Window assignment, assigning each timestamped element to zero or more logical windows measured in event time. The paper's own formal definition. "Set&lt;Window&gt; AssignWindows(T datum), which assigns the element to zero or more windows." Fixed, sliding, and session, unaligned, windows are all supported strategies.

Window merging, for unaligned strategies such as sessions, an operation that merges overlapping per-key windows as new data arrive. "Set&lt;Window&gt; MergeWindows(Set&lt;Window&gt; windows)," so that "window-driven windows can be constructed over time as data arrive and are grouped together."

Triggering mechanism, determining when, in processing time, the possibly partial results of a window are emitted as a pane. "triggers are a mechanism for stimulating the production of GroupByKeyAndWindow results in response to internal or external signals... triggering determines when in processing time the results of groupings are emitted as panes."

Refinement or accumulation mode, controlling how successive trigger firings for the same window relate to each other. The paper names three modes explicitly, discarding, accumulating, and accumulating with retraction, each with a stated responsibility, quoted in full under dimension 7.

Late-data handler, the participant deciding what happens to a record whose event time falls behind the current watermark by more than a configured tolerance. Akidau's essay names the mechanism. "placing a bound on how late any given record may be (relative to the watermark) for the system to bother processing it; any data that arrive after this horizon are simply dropped." Once that horizon passes, buffered state for the window is garbage collected.

Downstream consumer, the recipient of the panes emitted by the pipeline. The paper is explicit that this participant's own semantics constrain which refinement mode fits. "Accumulating... is useful when the downstream consumer expects to overwrite old values with new ones" versus "Discarding... useful in cases where the downstream consumer of the data... expects the values from various trigger fires to be independent."

## 6. ASCII structure diagram

The technical shape below is sourced from the structural participants above and from the layout of the Dataflow paper's own Figures 5, 6, and 12, which plot event time on one axis and processing time on the other, with a watermark line moving irregularly across the plot.

```
  unbounded event stream
          |
          v
  event-time timestamp assignment
          |
          v
  window assignment (event-time based)         watermark tracking
          |                                      (running in parallel,
          v                                       observing the same stream)
  [window merging, for session/unaligned]              |
          |                                             |
          v                                             v
  per-key, per-window buffered state  <----- feeds threshold into ----->  trigger evaluation
          |                                                                     |
          |                                                                     v
          |                                        fires when watermark crosses window end,
          |                                        OR on a processing-time period,
          |                                        OR on a data-driven condition
          |                                                                     |
          v                                                                     v
  late-data handler                                                    pane emission
  (record's event time behind                                    (discarding / accumulating /
   the current watermark)                                      accumulating-and-retracting)
          |                                                                     |
          +----- within allowed lateness: re-enters window,                    |
          |      causes a repeat trigger fire (refinement)                     |
          |                                                                    v
          +----- past allowed lateness: dropped                        downstream sink
```

The watermark is drawn as a moving boundary line across the event-time axis, separate from the linear, monotonic processing-time axis along which the system actually observes and reacts to data. This two-axis relationship, event time on one dimension, the system's own view of that event time advancing non-monotonically relative to real time due to skew, is the single most important visual idea across the paper's own figures.

## 7. Dynamics

Events arrive out of order relative to event time, the baseline assumption of the whole model. "Since the data are unordered with respect to event time, we require some other signal to tell us when the window is done."

Each incoming record is timestamped with its event time and assigned to one or more windows by the windowing strategy, independent of when it physically arrived.

The watermark advances monotonically as a heuristic estimate that no more data before event time T is coming, but its real-world behaviour is not a clean straight line. The paper states this directly. "In an ideal world, time domain skew would always be zero... Reality is not so favorable, however... Starting around 12:00, the watermark starts to skew more away from real time as the pipeline lags, diving back close to real time around 12:02, then lagging behind again noticeably by the time 12:03 rolls around." This dynamic, irregular skew is expected behaviour, not an edge case.

Windows fire, trigger, when the watermark crosses the window's end boundary, the default behaviour. "The watermark trigger fires when the watermark passes the end of the window in question... Should any data arrive after the watermark, they will instantiate the repeated watermark trigger, which will fire immediately since the watermark has already passed." Non-default triggers can also fire on a fixed processing-time period for lower-latency partial results, or on a data-driven condition such as after every N elements arrive.

Late data arriving after the watermark has already passed a window's boundary is handled per the allowed-lateness policy. If within the horizon, the late record causes the window's trigger to fire again, a refinement of the original result. The paper's own illustration, the late-arriving value 9, "causes the first window (for event time range [12:00, 12:02)) to retrigger with an updated sum." If the record arrives after the allowed-lateness horizon, it is dropped, "any data that arrive after this horizon are simply dropped."

What retriggering with an updated sum looks like on the wire is governed by the refinement mode chosen up front. Discarding, "upon triggering, window contents are discarded, and later results bear no relation to previous results." Accumulating, "upon triggering, window contents are left intact in persistent state, and later results become a refinement of previous results. This is useful when the downstream consumer expects to overwrite old values with new ones." Accumulating and retracting, "in addition to the Accumulating semantics, a copy of the emitted value is also stored in persistent state. When the window triggers again in the future, a retraction of the previous value will be emitted first, followed by the new value as a normal datum." The paper's own Figure 14 walks through a full worked example, an initial singleton session emitted for one value, later joined into a combined session as the watermark advances, with the system emitting an explicit retraction of the earlier standalone result before emitting the new combined one, demonstrating that this mode's runtime dynamics genuinely include emitting an undo signal, not merely a new number.

The watermark's own dual failure modes shape observed runtime behaviour. A watermark that races ahead of true completeness, too fast, produces late data handled per the paragraph above. A watermark that correctly but slowly lags behind, too slow, produces visibly delayed output, which is why systems layer processing-time-based or data-driven triggers alongside the watermark trigger rather than relying on it alone.

## 8. Implementation variants

Every mainstream engine surveyed separates the same two concerns the Dataflow paper separates, assigning a per-record event timestamp, and generating a progress signal from those timestamps, but packages the separation differently. The organization below is this entry's own synthesis; each individual claim is cited to its own source.

Apache Flink uses a WatermarkStrategy, containing both a TimestampAssigner and a WatermarkGenerator. Two generation styles exist. Periodic generators observe every event and emit a watermark on a fixed interval. Punctuated generators "wait for special marker events or punctuations that carry watermark information in the stream. When it sees one of these events it emits a watermark immediately." Built-in strategies include forBoundedOutOfOrderness, which emits a watermark at the current maximum timestamp minus the configured out-of-orderness, and forMonotonousTimestamps, which assumes timestamps are non-decreasing per source task. Flink handles a Kafka-specific complication directly, noting that consuming multiple partitions in parallel "interleaving the events from the partitions" destroys any per-partition ordering pattern, so "watermarks are generated inside the Kafka consumer, per Kafka partition, and the per-partition watermarks are merged in the same way as watermarks are merged on stream shuffles."

Apache Beam, which directly implements the Dataflow model, defines its own watermark this way. "Beam tracks a watermark, which is the system's notion of when all data in a certain window can be expected to have arrived in the pipeline. Once the watermark progresses past the end of a window, any further element that arrives with a timestamp in that window is considered late data." Beam states plainly that the watermark is source-dependent, not one universal formula. "your PCollection's data source determines the watermark, and watermarks can be more precise or complex." Beam's own default trigger. "emits the results of the window when the Beam's watermark passes the end of the window, and then fires each time late data arrives. However, if you are using both the default windowing configuration and the default trigger, the default trigger emits exactly once, and late data is discarded." Beam frames its trigger choice directly in the paper's own vocabulary. "These capabilities allow you to control the flow of your data and balance between different factors depending on your use case. Completeness... Latency... Cost."

Kafka Streams is the only one of the four systems that documents a third, first-class time notion. Event time, "The point in time when an event or data record occurred, i.e. was originally created at the source." Processing time, "The point in time when the event or data record happens to be processed by the stream processing application." Ingestion time, "The point in time when an event or data record is stored in a topic partition by a Kafka broker... this ingestion timestamp is generated when the record is appended to the target topic by the Kafka broker, not when the record is created at the source." The choice between event time and ingestion time is set at the broker or topic level, not in application code. "Depending on Kafka's configuration these timestamps represent event-time or ingestion-time. The respective Kafka configuration setting can be specified on the broker level or per topic." Timestamp extraction is via a stateless TimestampExtractor interface; a negative return value causes the record to be "silently skipped." Kafka Streams calls its own event-time clock "stream time... this time will only advance when a new record arrives at the processor." Windows are configured with an explicit grace period rather than Flink's allowed-lateness naming, for example ofSizeAndGrace(Duration.ofHours(1), Duration.ofMinutes(10)), which "allows us to bound the lateness of events the window will accept... at which point, the window is closed."

Spark Structured Streaming attaches a watermark to a DataFrame column rather than to the source connector. "For a specific window ending at time T, the engine will maintain state and allow late data to update the state until (max event time seen by the engine minus late threshold greater than T). In other words, late data within the threshold will be aggregated, but data later than the threshold will start getting dropped." Spark's own guarantee is stated with unusual precision. A watermark delay "guarantees that the engine will never drop any data that is less than 2 hours delayed... However, the guarantee is strict only in one direction. Data delayed by more than 2 hours is not guaranteed to be dropped; it may or may not get aggregated." Watermarking only actually cleans state in Append or Update output mode, and Spark names a specific, quotable class of user error. withWatermark must be called on the same event-time column used in the aggregation, and must be called before the aggregation, or watermarking silently fails to apply.

## 9. Known production uses

Google Cloud Dataflow, the external production system the model itself describes, built on Google's internal MillWheel and FlumeJava. Source, the Dataflow Model paper. A naming caveat worth stating plainly, since the entry template demands honesty over a smooth story. one of the paper's eleven listed authors is named Eric Schmidt; this is a different, less prominent Google engineer, not the well-known former Google chief executive of the same name, based on the paper's own author affiliations, though this entry could not independently cross-check the byline against a bibliographic index such as DBLP within its research budget.

Apache Beam pipelines run on Apache Flink, Apache Spark, and Google Cloud Dataflow as pluggable runners, per Beam's own project overview documentation.

Alibaba runs a fork of Flink, called Blink, "to optimize search rankings in real time," per Apache Flink's own Powered By page. Uber built AthenaX, its "internal SQL-based, open-source streaming analytics platform," on Apache Flink, per the same source.

Netflix's Keystone real-time stream processing platform "processes trillions of events" daily and is "currently focusing on [using] Apache Flink," per Netflix's own engineering blog. That source names window sizes ranging from a few seconds to hours-long custom session windows, but does not itself discuss event time, watermarks, or out-of-order handling in the material available, so this entry treats it as evidence of Flink at scale rather than as a sourced claim that Netflix specifically depends on event-time correctness.

Kafka Streams' own list of named production users includes The New York Times, described as using "Apache Kafka and the Kafka Streams API to store and distribute, in real-time," Pinterest, using the same "at large scale to power" real-time systems, LINE, which "[uses] Kafka Streams to reliably transform and filter topics," and Rabobank, which built a real-time customer fraud and financial-event alerting service "using Kafka Streams." Source, Kafka's own Powered By page.

## 10. Consequences

Positive. Correctness independent of arrival order and pipeline delay. "if you care about correctness... you cannot define those temporal boundaries using processing time," because "the skew between event time and processing time is not only non-zero, but often a highly variable function." Reproducibility on reprocessing. The Dataflow paper's stated goal is that batch, micro-batch, and streaming engines can provide equal levels of correctness, turning engine choice into an operational latency and cost decision rather than a correctness one; this is the same idea the Kappa Architecture depends on, replaying a retained log through a corrected job to get a comparable answer. A tunable trade-off, not a fixed cost. Beam's own docs frame trigger choice as a direct, user-facing lever trading "Completeness... Latency... Cost" against each other per pipeline.

Negative. Requires buffering state. Every implementation surveyed holds partial aggregation state until the watermark, plus any grace or lateness period, passes, a real operational cost in state and checkpoint size a pure processing-time system does not pay. Watermark heuristics can simply be wrong. The Dataflow paper names this directly, watermarks are "often heuristically established," with the paper naming both failure directions, too fast producing late data, too slow stalling global progress. Increased latency for correctness. Spark's own docs state this plainly, output "is delayed the late threshold specified in withWatermark()," meaning a ten-minute watermark adds ten minutes of output latency in the default case. More complex to reason about than processing time, engineering judgement, well supported by the shape of the APIs themselves. correct event-time processing across every system surveyed requires reasoning about four separate, composable concerns, what is computed, where in event time it is grouped, when in processing time it is emitted, and how successive emissions relate, versus one concern for simple processing-time aggregation.

## 11. Failure modes and misuse

Watermark stalls from an idle partition or source, the straggler problem, documented directly by Flink. "If one of the input splits/partitions/shards does not carry events for a while this means that the WatermarkGenerator also does not get any new information on which to base a watermark." Because the overall watermark is the minimum across all parallel sources, one silent partition holds back every downstream window from ever firing, even though the rest of the pipeline is healthy. The observable symptom is a job that appears to hang, no windows ever close, while most of the pipeline is otherwise producing data normally. Flink's fix is withIdleness, which excludes a source from the minimum calculation after a timeout.

Late data silently dropped by default, in three of the four systems surveyed. Flink, "By default... late elements are dropped when the watermark is past the end of the window... elements that arrive behind the watermark will be dropped," with allowedLateness and sideOutputLateData as the opt-in escape hatch. Beam, "if you are using both the default windowing configuration and the default trigger, the default trigger emits exactly once, and late data is discarded," with withAllowedLateness as the opt-in. Kafka Streams, a negative or invalid extracted timestamp causes the record to be quietly dropped, "Returning a negative timestamp will cause the record not to be processed but rather silently skipped," and out-of-window records past the grace period are simply excluded. The observable production symptom is a metric or count that is silently and permanently short, discovered only when totals fail to reconcile against a source-of-truth system, often days or weeks later.

Watermark advancing too fast causing spurious late-data cascades, and too slow holding back global progress on healthy data, both explicitly named as watermark shortcomings. A too-fast watermark is a misuse or misconfiguration failure mode distinct from the idle-source case above. setting a bounded-out-of-orderness threshold, or a Spark watermark delay, too tight for the real-world lateness distribution of the actual data causes the system to systematically treat legitimate, only-slightly-late data as late, producing continuous drops rather than an occasional edge case.

A precisely documented, Spark-specific misuse. withWatermark must be called on the same event-time column used in the aggregation, and must be called before the aggregation, or watermarking silently fails to apply. Spark's own docs name the exact invalid shape. calling withWatermark on one column then grouping by a different one, or calling withWatermark after the aggregation rather than before it.

Clock skew across event producers producing bad timestamps is a plausible, related failure mode, but this entry could not locate a primary source discussing producer-side clock synchronization directly within its research budget, as distinct from the well-sourced pipeline and network skew covered above. This is stated here as an honest gap rather than an invented citation, per the entry template's judgement-versus-sourced-claim rule.

## 12. Trade-off matrix

Comparing event-time processing against its two named alternatives, processing-time processing and ingestion-time processing, the third option Kafka Streams documents as a first-class notion, across correctness, latency, complexity, and reproducibility.

| Force | Event time | Processing time | Ingestion time |
|---|---|---|---|
| Correctness of temporal grouping | High, deterministic regardless of when or how fast the pipeline runs. "if you care about correctness... you cannot define those temporal boundaries using processing time." | Low for the actual business event, by construction, since grouping tracks when the pipeline happened to observe a record, not when it occurred. | Medium, correct with respect to when the system saw the record, deterministic per broker but still divorced from when the event occurred at the source. |
| Latency to a final, unrevised result | Higher, must wait for the watermark, plus any grace or lateness period, before a final result in append-style semantics. Spark, output "is delayed the late threshold specified in withWatermark()." | Lowest, a processing-time window closes purely on elapsed wall-clock time, with no dependency on data completeness. | Lower than event time, comparable to processing time, since ingestion time is assigned once at broker append with no further heuristic waiting. |
| Implementation complexity | Highest, requires per-record timestamp extraction, an explicit watermark or lateness policy, and an explicit late-data handling choice in every system surveyed. | Lowest, no timestamp extraction or watermark configuration required. | Low, in Kafka Streams the choice is a single broker or topic configuration flag, not application code. |
| Reproducibility on reprocessing | High, replaying the same event-time-stamped data through a corrected job yields the same grouping, the mechanism the Kappa Architecture depends on. | Low, replaying old data through processing-time windows groups it by when the replay happened, not when it originally occurred, so a backfill produces different window contents than the original live run. | Medium, ingestion time is fixed at original broker append and does not change on replay, but is not correct with respect to the actual business event if the source clock and the broker append time diverge. |

This table is this entry's own synthesis across the four systems' documented behaviour, following the same posture as the sibling entries in this family and catalogue, never a single quoted source.

## 13. Related and incompatible patterns

Watermark and Windowing are the two mechanisms this pattern composes from, and the primary sources are explicit about keeping them orthogonal. Akidau's companion essay, Streaming 102, gives the clearest sourced framing, a four-question structure. "What results are calculated? This question is answered by the types of transformations within the pipeline." "Where in event time are results calculated? This question is answered by the use of event-time windowing within the pipeline." "When in processing time are results materialized? This question is answered by the use of watermarks and triggers." "How do refinements of results relate? This question is answered by the type of accumulation used."

This is the primary-source basis for the relationship among the three concepts. Event-Time Processing is the umbrella discipline, the decision to define correctness against event time at all. Windowing answers the where, the grouping mechanism slicing the unbounded event-time axis into finite buckets, fixed, sliding, and session windows documented near-identically across every implementation surveyed. Watermarks, composed with triggers, answer the when, the progress-tracking mechanism deciding, in processing time, when a window's event-time contents can be considered materializable. Watermarking without windowing is meaningless, there is nothing to close. Windowing without a watermark degenerates to processing-time windowing, with no signal for when a window is done, only wall-clock elapsed time. The two are mutually necessary, not merely compatible, whenever event-time correctness with bounded output latency is the goal.

Triggers sit on top of watermarks as a third composable piece. a watermark passing a window's end is only the default trigger condition, and every system surveyed allows firing early on a processing-time or count-based trigger, or firing again on late arrivals, independently of the watermark's own advancement.

Lambda and Kappa Architecture, a directly documented relationship. The Dataflow paper itself states that its trigger-based progressive refinement gives "low-latency results" that are later refined, "mirroring Lambda Architecture benefits within a unified system." Lambda Architecture runs two separate codebases, a batch layer for correctness and a speed layer for low latency, merging their outputs at query time. The Dataflow authors' own claim is that event-time processing with watermarks, triggers, and accumulation modes lets one system produce both the fast, provisional early result and the eventual, correct, watermark-triggered final result, without maintaining two codebases. Kappa Architecture drops the batch layer entirely, relying on a durable, replayable log plus reprocessing a corrected streaming job from the start of the log, which only produces a consistent replayed result if the job groups by event time rather than processing time, making event-time correctness a structural prerequisite for the Kappa pattern to work.

Incompatibility. Processing-time-only windowing is not merely a weaker alternative to event-time processing, it is logically incompatible with the correctness goal event-time processing exists to solve. Correct temporal grouping regardless of arrival order cannot be retrofitted onto a processing-time window after the fact, because the information about when things actually happened was never captured in the grouping decision.

## 14. Refactoring path in and out

Refactoring in, from a processing-time pipeline to an event-time pipeline, reconstructed from the documented APIs above rather than copied from a single migration guide.

1. Identify or add a per-record event timestamp field in the payload itself, if one does not already exist, a source-side change outside any framework.
2. Attach a timestamp extractor or assigner. Flink's withTimestampAssigner, or accepting one from the source connector directly. Beam's ParDo calling outputWithTimestamp instead of output. Kafka Streams' custom TimestampExtractor supplied via Consumed.with. Spark's implicit use of whatever column is named in withWatermark.
3. Choose and attach a watermark or lateness policy sized to the real-world lateness distribution of the actual data, never a guess. Flink's forBoundedOutOfOrderness. Beam's runner-provided watermark plus withAllowedLateness. Kafka Streams' ofSizeAndGrace. Spark's withWatermark threshold.
4. Switch the grouping operator from a processing-time-driven trigger to an event-time-keyed window, moving away from a wall-clock timestamp extractor or a legacy processing-time characteristic.
5. Decide, and make explicit, the late-data policy. drop silently, the default in every system surveyed, acceptable only if the business tolerates it; capture to a side output for separate handling; or extend the allowed-lateness or grace window at the cost of more buffered state and later final output.
6. Verify determinism under replay. run the same historical data twice through the new event-time pipeline and confirm identical window contents, the concrete, checkable proof that the migration achieved the reproducibility benefit, mirroring the Kappa Architecture's own replay pattern.

Refactoring out, when correctness genuinely does not matter, is engineering judgement rather than a sourced playbook. When the aggregation is an operational metric about the pipeline or system itself, such as requests handled in the last five minutes of wall-clock time, a liveness or load indicator, rather than a business-record aggregation about real-world events where the hour must mean the hour the sale actually happened, the value event-time correctness buys is not being spent, while its full cost, state buffering, added output latency, and API complexity, is still being paid. Removing it means dropping the timestamp extractor and watermark strategy, switching the window assigner back to a processing-time or count-based trigger, and no longer promising downstream consumers that results are stable or replayable.

## 15. Testing and verification

None of the sources fetched for this entry addressed testing strategy for event-time processing directly; this entire dimension is engineering reasoning drawn from the structure the sources above describe, stated as judgement rather than dressed as fact, following the same posture as the sibling entries in this catalogue.

Deterministic replay is the natural correctness test for this pattern, and it is directly implied by the reproducibility claim in dimension 10. feeding the identical, fixed set of timestamped records through the pipeline twice, in two different arrival orders, and asserting the two runs produce byte-identical window contents, is the most direct way to prove a pipeline is genuinely keyed on event time rather than accidentally leaking processing-time behaviour.

Watermark generation and window-firing logic are natural seams for unit testing in isolation. Flink, Beam, and Spark all expose a way to advance a synthetic watermark or clock under test without running a live source, letting a test assert that a window fires at the exact moment the watermark crosses its boundary, neither earlier nor later.

The late-data path deserves its own explicit test, separate from the happy path. a record whose event time falls just inside the allowed-lateness horizon should cause the affected window to refire with the correct refinement semantics, discarding, accumulating, or accumulating with retraction, and a record just past the horizon should be either dropped or routed to a side output, exactly per whichever policy the implementation under test declares, since the primary sources are explicit that the miss-handling contract is implementation-defined.

The idle-source failure mode named in dimension 11 is directly testable. a test that starves one simulated partition of data while feeding the others should assert that the pipeline's overall watermark either correctly stalls, if idleness handling is not configured, or correctly advances past the idle source, if it is, rather than silently passing either way.

## 16. Observability signals

None of the sources fetched addressed observability directly; this dimension is engineering judgement.

The single most pattern-specific signal is watermark lag, the gap between real wall-clock time and the current watermark's position on the event-time axis, tracked over time. A healthy pipeline shows this lag stable within an expected bound; a lag that grows without recovering is the direct, measurable symptom of the too-slow watermark failure mode named in dimension 11, and per-source watermark lag broken out individually is what actually surfaces a single idle or straggling partition rather than only the pipeline-wide minimum.

A second signal is the rate of late, dropped records against total records processed, broken out per window or per source. Because every system surveyed drops late data silently by default, this counter is the only way to notice the silent-loss failure mode named in dimension 11 before totals fail to reconcile against a source of truth days or weeks later.

A third signal, specific to the accumulating-and-retracting refinement mode, is the rate of retraction events emitted relative to normal pane emissions. A system whose retraction rate is unexpectedly high is a proxy for how often the watermark is racing ahead of the true data, prompting a review of whether the configured out-of-orderness or lateness bound still matches the real-world skew of the data.

## 17. Security and privacy implications

None of the sources fetched addressed security or privacy for event-time processing directly, and the reasoning here is analytical rather than sourced.

The most concrete implication follows from the pattern's own reliance on caller-supplied timestamps. because event time is extracted from the data itself rather than assigned independently by the receiving system, a producer that can influence its own event-time field can also influence which window its records land in, and, in an accumulating-and-retracting pipeline, can trigger repeated retraction and refinement cycles on a window purely by supplying records with deliberately skewed timestamps. A system whose downstream consumers treat window boundaries as a trust boundary, for example a billing pipeline, per the paper's own running example, should validate or bound the plausible range of an untrusted producer's event-time field rather than accepting it unchecked, though none of the sources fetched name this concern explicitly.

Event-Time Processing carries no data-handling implications of its own beyond whatever the underlying event payloads already carry; it introduces no new storage, network surface, or serialization boundary on its own. Where the pattern's own sources are silent on a security concern, that silence is recorded here rather than an invented one supplied in its place.

## 18. References

Tyler Akidau, Robert Bradshaw, Craig Chambers, Slava Chernyak, Rafael J. Fernandez-Moctezuma, Reuven Lax, Sam McVeety, Daniel Mills, Frances Perry, Eric Schmidt, Sam Whittle. "The Dataflow Model: A Practical Approach to Balancing Correctness, Latency, and Cost in Massive-Scale, Unbounded, Out-of-Order Data Processing." Proceedings of the VLDB Endowment, Volume 8, Number 12, pages 1792 to 1803, 2015. https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf. Verified 2026-08-23.

Tyler Akidau, Alex Balikov, Kaya Bekiroglu, Slava Chernyak, Josh Haberman, Reuven Lax, Sam McVeety, Daniel Mills, Paul Nordstrom, Sam Whittle. "MillWheel: Fault-Tolerant Stream Processing at Internet Scale." Proceedings of the VLDB Endowment, Volume 6, Number 11, pages 1033 to 1044, 2013. https://www.vldb.org/pvldb/vol6/p1033-akidau.pdf. Verified 2026-08-23.

Tyler Akidau. "The world beyond batch: Streaming 101." O'Reilly Radar, 5 August 2015. https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/. Verified 2026-08-23.

Tyler Akidau. "The world beyond batch: Streaming 102." O'Reilly Radar, 20 January 2016. https://www.oreilly.com/radar/the-world-beyond-batch-streaming-102/. Verified 2026-08-23.

Apache Flink documentation. "Timely Stream Processing." https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/time/. Verified 2026-08-23.

Apache Flink documentation. "Generating Watermarks." https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/event-time/generating_watermarks/. Verified 2026-08-23.

Apache Flink documentation. "Windows." https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/operators/windows/. Verified 2026-08-23.

Apache Flink. "Powered By." https://flink.apache.org/what-is-flink/powered-by/. Verified 2026-08-23.

Apache Beam. "Programming Guide" (source markdown). https://raw.githubusercontent.com/apache/beam/master/website/www/site/content/en/documentation/programming-guide.md. Verified 2026-08-23.

Apache Beam. "Beam Overview." https://raw.githubusercontent.com/apache/beam/master/website/www/site/content/en/get-started/beam-overview.md. Verified 2026-08-23.

Wikipedia. "Apache Beam." https://en.wikipedia.org/wiki/Apache_Beam. Verified 2026-08-23.

Apache Kafka documentation. "Streams Concepts" (source markdown). https://raw.githubusercontent.com/apache/kafka/trunk/docs/streams/core-concepts.md. Verified 2026-08-23.

Apache Kafka documentation. "Streams DSL" (source markdown). https://raw.githubusercontent.com/apache/kafka/trunk/docs/streams/developer-guide/dsl-api.md. Verified 2026-08-23.

Apache Kafka. "TimestampExtractor" Javadoc. https://kafka.apache.org/40/javadoc/org/apache/kafka/streams/processor/TimestampExtractor.html. Verified 2026-08-23.

Apache Kafka. "Powered By." https://kafka.apache.org/powered-by. Verified 2026-08-23.

Apache Spark documentation. "Structured Streaming Programming Guide, event time and window operations." https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html. Verified 2026-08-23.

Zhenzhong Xu. "Keystone Real-time Stream Processing Platform." Netflix Technology Blog, 10 September 2018. https://netflixtechblog.com/keystone-real-time-stream-processing-platform-a3ee651812a. Verified 2026-08-23.

Jay Kreps. "Questioning the Lambda Architecture." O'Reilly Radar, 2 July 2014. https://www.oreilly.com/radar/questioning-the-lambda-architecture/. Verified 2026-08-23.

**Evidence grade.** high

**Most solid findings.** The Dataflow Model and MillWheel papers were read directly from their own PDF text, giving primary-source grounding for the event-time versus processing-time definitions, the watermark's own recursive formalism, and the too-fast versus too-slow watermark trade-off in dimension 3. The four-implementation comparison in dimension 8 draws on each project's own current documentation or source repository rather than a secondary aggregator, and Kafka Streams' three-way time-domain distinction (event, processing, ingestion) is independently corroborated as a genuinely distinctive implementation variant not present in Flink or Beam's own documented models.

**Unverified or unclear.** One of the Dataflow paper's eleven listed authors shares a name with a well-known former Google chief executive; this entry treats it as a different, unrelated person based on the paper's own author affiliations, but could not independently cross-check the byline against a bibliographic index such as DBLP within its research budget. The Netflix Keystone source documents Flink usage at scale but does not itself discuss event-time correctness, so the claim there is scoped narrowly to production Flink usage, not to event-time-specific practice. The claim that Apache Beam is the open-sourced Dataflow Model draws on Wikipedia's own article rather than a primary Apache Beam project source. No primary source was found discussing distributed clock skew across event producers as a distinct failure mode from pipeline or network delay, and dimension 11 states this gap plainly rather than filling it with an invented citation.

## Code

TypeScript, Python, and Go each model a minimal event-time windowing engine directly, following the Dataflow model's own vocabulary (event time, watermark, allowed lateness, refinement) rather than any single framework's API surface. Kotlin and Swift are omitted, since neither has a first-party streaming-windowing library idiomatic enough to demonstrate the pattern without pulling in a large external dependency.

### TypeScript

```typescript
interface Event {
  key: string;
  eventTime: number;
  value: number;
}

interface WindowResult {
  windowStart: number;
  windowEnd: number;
  sum: number;
  isRetraction: boolean;
}

class EventTimeWindowEngine {
  private windowSizeMs: number;
  private allowedLatenessMs: number;
  private windowSums = new Map<number, number>();
  private firedWindows = new Set<number>();
  private watermark = -Infinity;

  constructor(windowSizeMs: number, allowedLatenessMs: number) {
    this.windowSizeMs = windowSizeMs;
    this.allowedLatenessMs = allowedLatenessMs;
  }

  private windowStartFor(eventTime: number): number {
    return Math.floor(eventTime / this.windowSizeMs) * this.windowSizeMs;
  }

  advanceWatermark(newWatermark: number): WindowResult[] {
    this.watermark = Math.max(this.watermark, newWatermark);
    const results: WindowResult[] = [];
    for (const [start, sum] of this.windowSums) {
      const end = start + this.windowSizeMs;
      if (this.watermark >= end && !this.firedWindows.has(start)) {
        results.push({ windowStart: start, windowEnd: end, sum, isRetraction: false });
        this.firedWindows.add(start);
      }
    }
    return results;
  }

  ingest(event: Event): WindowResult | null {
    const start = this.windowStartFor(event.eventTime);
    const end = start + this.windowSizeMs;

    if (this.watermark >= end + this.allowedLatenessMs) {
      return null;
    }

    const previousSum = this.windowSums.get(start) ?? 0;
    this.windowSums.set(start, previousSum + event.value);

    if (this.firedWindows.has(start)) {
      return { windowStart: start, windowEnd: end, sum: this.windowSums.get(start)!, isRetraction: true };
    }
    return null;
  }
}
```

### Python

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Event:
    key: str
    event_time: int
    value: int


@dataclass
class WindowResult:
    window_start: int
    window_end: int
    total: int
    is_retraction: bool


class EventTimeWindowEngine:
    def __init__(self, window_size_ms: int, allowed_lateness_ms: int) -> None:
        self.window_size_ms = window_size_ms
        self.allowed_lateness_ms = allowed_lateness_ms
        self.window_sums: dict[int, int] = {}
        self.fired_windows: set[int] = set()
        self.watermark = float("-inf")

    def _window_start(self, event_time: int) -> int:
        return (event_time // self.window_size_ms) * self.window_size_ms

    def advance_watermark(self, new_watermark: int) -> list[WindowResult]:
        self.watermark = max(self.watermark, new_watermark)
        results: list[WindowResult] = []
        for start, total in self.window_sums.items():
            end = start + self.window_size_ms
            if self.watermark >= end and start not in self.fired_windows:
                results.append(WindowResult(start, end, total, False))
                self.fired_windows.add(start)
        return results

    def ingest(self, event: Event) -> Optional[WindowResult]:
        start = self._window_start(event.event_time)
        end = start + self.window_size_ms

        if self.watermark >= end + self.allowed_lateness_ms:
            return None

        self.window_sums[start] = self.window_sums.get(start, 0) + event.value

        if start in self.fired_windows:
            return WindowResult(start, end, self.window_sums[start], True)
        return None
```

### Go

```go
package eventtime

type Event struct {
	Key       string
	EventTime int64
	Value     int64
}

type WindowResult struct {
	WindowStart  int64
	WindowEnd    int64
	Total        int64
	IsRetraction bool
}

type WindowEngine struct {
	windowSizeMs      int64
	allowedLatenessMs int64
	windowSums        map[int64]int64
	firedWindows      map[int64]bool
	watermark         int64
}

func NewWindowEngine(windowSizeMs, allowedLatenessMs int64) *WindowEngine {
	return &WindowEngine{
		windowSizeMs:      windowSizeMs,
		allowedLatenessMs: allowedLatenessMs,
		windowSums:        make(map[int64]int64),
		firedWindows:      make(map[int64]bool),
		watermark:         -1 << 62,
	}
}

func (e *WindowEngine) windowStart(eventTime int64) int64 {
	return (eventTime / e.windowSizeMs) * e.windowSizeMs
}

func (e *WindowEngine) AdvanceWatermark(newWatermark int64) []WindowResult {
	if newWatermark > e.watermark {
		e.watermark = newWatermark
	}
	var results []WindowResult
	for start, total := range e.windowSums {
		end := start + e.windowSizeMs
		if e.watermark >= end && !e.firedWindows[start] {
			results = append(results, WindowResult{start, end, total, false})
			e.firedWindows[start] = true
		}
	}
	return results
}

func (e *WindowEngine) Ingest(ev Event) *WindowResult {
	start := e.windowStart(ev.EventTime)
	end := start + e.windowSizeMs

	if e.watermark >= end+e.allowedLatenessMs {
		return nil
	}

	e.windowSums[start] += ev.Value

	if e.firedWindows[start] {
		return &WindowResult{start, end, e.windowSums[start], true}
	}
	return nil
}
```
