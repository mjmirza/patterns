---
name: Feature Store
slug: feature-store
family: 25-mlops
category: MLOps
aliases: [ML Feature Store, Feature Platform]
first_described: "Del Balso and Hermann, Meet Michelangelo, Uber Engineering, 2017"
maturity: established
related: [model-registry, training-serving-skew-guard, batch-inference, online-inference]
incompatible_with: []
verified: 2026-08-23
---

# Feature Store

## 1. Name, aliases, and lineage

A feature store is a centralized system for storing, computing, and serving
the input variables, features, that a machine learning model consumes, split
across two access paths, a low-latency online store for real-time inference
and a high-throughput offline store for generating training data, kept
consistent with each other.

The term is most credibly traced to Uber's Michelangelo platform. Uber's own
engineering blog, "Meet Michelangelo. Uber's Machine Learning Platform,"
Mike Del Balso and Jeremy Hermann, September 5, 2017, states the motivation
for building one directly, "We found that many modeling problems at Uber use
identical or similar features, and there is substantial value in enabling
teams to share features between their own projects," and, "It allows users
to easily add features they have built into a shared feature store,
requiring only a small amount of extra metadata." By the time of that post,
Uber reports, "we have approximately 10,000 features in Feature Store."

Feast, the leading open source implementation, originated separately as a
Gojek and Google collaboration. The Linux Foundation AI and Data project
page states, "Feast is an open source feature store for machine learning. It
was developed as a collaboration between Gojek and Google in 2018," and
currently lists Feast at the Incubation maturity stage. Feast's own current
homepage has broadened its framing beyond classic tabular model serving, now
describing itself as delivering "structured data to AI and LLM applications
at high scale during training and inference," a real, current shift in the
term's scope worth noting rather than smoothing over.

## 2. Problem and context

Feature computation logic written for offline, batch training, commonly
Python or Spark against a data warehouse, is easy to accidentally diverge
from the low-latency online serving path that computes the same feature at
prediction time, often in a different language or runtime entirely. Any
difference between the two, a different null-handling rule, a different
aggregation window, a bug present in one path and not the other, causes the
model to see systematically different feature values in production than it
saw during training, silently degrading accuracy with no exception thrown
anywhere. Google's own "Rules of Machine Learning" names this problem
directly, in a rule aimed exactly at avoiding it, "The best way to make sure
that you train like you serve is to save the set of features used at
serving time, and then pipe those features to a log to use them at training
time," and, separately, "Re-use code between your training pipeline and your
serving pipeline whenever possible." AWS's own SageMaker Feature Store
documentation names the failure mode by its common industry term directly,
"This reduces training-serving skew, a common issue in ML where the
difference between performance during training and serving can impact the
accuracy of your ML model."

## 3. Forces

**Freshness against cost and complexity.** AWS documents the two stores'
different purposes plainly, the online store is "primarily designed for
supporting real-time predictions that need low millisecond latency reads and
high throughput writes," while the offline store "keeps all records for your
features as a historical database... primarily intended for data
exploration, model training, and batch predictions." Running two
synchronized storage systems plus a materialization job that keeps them
consistent is a real, ongoing operational cost paid to get that freshness.

**Freshness against correctness.** A point-in-time-correct join, retrieving
a feature's value exactly as it stood at a historical training example's
timestamp, is what prevents label leakage, but it is easy to get wrong.
Feast's own documentation states the specific failure this guards against,
"a value that was backfilled or corrected after an entity dataframe
timestamp can still be returned for it" unless an additional, explicit
condition is enabled to filter it out.

**Precompute against request-time compute.** Not every feature can be
materialized ahead of time. Databricks' documentation on on-demand features
gives a concrete example, a live caller location used to compute a
real-time distance feature, stating this variant is needed "when feature
values are not known ahead of time and depend on request-time inputs." This
trades the correctness of a shared, versioned computation for the ability to
use an input that genuinely does not exist until the request arrives.

## 4. Applicability and non-applicability

Reach for a feature store when a system needs real-time inference at low
millisecond latency, when more than one model or team shares the same
underlying features and would otherwise duplicate the computation, and when
training-serving skew is a real, costly risk for the workload. AWS's own
design intent, low-latency reads paired with a discoverable, reusable
feature registry, is aimed precisely at this combination.

Do not reach for it for a single model, scored purely in batch, with no
other consumer of its inputs and no low-latency serving requirement. Google's
own Rule 32, "Re-use code between your training pipeline and your serving
pipeline whenever possible," is satisfied just as well in that case by a
shared, versioned feature-computation library imported by both the training
job and the batch scoring job, at a fraction of the operational cost of
standing up separate online and offline stores plus a materialization
pipeline.

## 5. Structure

A **registry** is the central catalog of feature definitions and their
metadata, Feast describes its default implementation as storing "the
protobuf representation of the registry as a serialized file in the local
file system," and states its purpose plainly, letting data scientists
"search, discover, and collaborate on new features." An **offline store**
holds historical, time-series feature values used for training-set
generation and as the source for materialization, Feast's supported
implementations include BigQuery, Snowflake, and Redshift among its core
set. An **online store** holds only the current value per entity key, "for
each entity key, only the latest feature values are stored. No historical
values are stored," with implementations including Redis, DynamoDB, and
SQLite. A **feature view** is the logical grouping of a set of features from
one data source, read differently depending on the access path, "a stateful
collection of features that are read when the get_online_features method is
called" versus "a stateless collection of features that are created when
the get_historical_features method is called." A **materialization job**
moves data one direction, offline to online, Databricks names three
cadences for the equivalent job, TRIGGERED, CONTINUOUS, and SNAPSHOT.

## 6. ASCII structure diagram

```
Raw data sources (databases, event streams, warehouse tables)
                    |
                    v
       Feature transformation and computation
                    |
      +-------------+-------------+
      |                           |
      v                           v
 Offline store               Online store
 (historical, time-series)   (latest value per key only)
      |                           ^
      |     materialization job   |
      +-------------------------->+
      |                           |
      v                           v
 Model training job          Model serving / inference
 (point-in-time-correct      (low-latency lookup by
  join against label          entity key, e.g. user_id)
  timestamps)

              Registry
     (feature definitions and metadata,
      read by both stores and both consumers)
```

## 7. Dynamics

At training time, a point-in-time-correct join scans backward from each
training example's own timestamp to find the feature value that was
genuinely available at that historical moment, never a value computed or
corrected afterward. Feast's own docs describe the scan bound directly,
"Feast will scan backward in time from the entity dataframe timestamp up to
a maximum of the TTL time specified," and note the TTL "is not relative to
the current point in time," it is relative to each row's own timestamp. An
optional stricter mode adds a condition comparing the feature's own
creation timestamp against the entity timestamp, closing the exact leakage
gap described in dimension 3.

Materialization runs on a schedule or continuously, pushing only the latest
value per entity key into the online store and discarding history there.
Databricks' three named modes, TRIGGERED, CONTINUOUS, and SNAPSHOT, are a
concrete illustration of how wide the range of update cadence actually is
in practice, from a one-time full copy to a continuously streaming sync.

At inference time, a low-latency lookup by entity key retrieves the current
feature vector from the online store. AWS documents this as sub-millisecond
territory, "features are read with low latency (milliseconds) reads and
used for high throughput predictions," and notes the online store can also
be enriched in real time from a streaming source at request time, a third,
hybrid path alongside the fully precomputed and fully on-demand extremes.

## 8. Implementation variants

**Feast.** Open source, Apache-2.0, hosted at Linux Foundation AI and Data
Incubation stage. Pluggable offline stores, core set includes BigQuery,
Snowflake, Redshift, and Dask, community-contributed adds Postgres, Spark,
Trino, and Ray. Pluggable online stores, core set includes SQLite, Redis,
DynamoDB, and Datastore, community adds Postgres, HBase, Cassandra, and
ScyllaDB. Its current homepage frames itself around serving "AI and LLM
applications," a broadened scope beyond its original tabular-ML framing.

**AWS SageMaker Feature Store.** A fully managed, purpose-built repository,
distinct product identity retained inside the broader SageMaker AI
ecosystem, no rename observed. States its training-serving-skew reduction
purpose directly in its own documentation, quoted in dimension 2.

**Databricks Feature Store.** Now built on Unity Catalog, with the
pre-Unity-Catalog version explicitly labeled "Workspace Feature Store
(deprecated)" on Databricks' own current documentation page, a genuine,
sourced deprecation rather than an assumption. Its newer online serving
layer is branded "Online Feature Store, powered by Databricks Lakebase," a
Postgres-based backend, supporting the TRIGGERED, CONTINUOUS, and SNAPSHOT
materialization cadences named in dimension 7.

**Google's feature store product.** A significant rename applies here.
Google announced Gemini Enterprise on October 10, 2025, and Vertex AI's
feature store now lives under the current documentation title "Feature
Store on Gemini Enterprise Agent Platform." Google's own announcement quotes
CEO Thomas Kurian directly, "Vertex AI has evolved. We've launched Gemini
Enterprise Agent Platform, the new home for building, scaling, governing,
and optimizing your agentic workforce." An entry naming this product as
plain Vertex AI Feature Store, without noting the rename, would already be
stale.

**Airbnb's Chronon.** Deliberately avoids the term feature store in its own
framing, instead describing itself as guaranteeing "online/offline
consistency," "the data that you use to train your model (offline) matches
the data that the model sees for production inference (online)." Listed
adopters on its own GitHub README include Airbnb, Stripe, OpenAI, Roku,
Netflix, Uber, Intuit, Airwallex, Sardine AI, and Monzo Bank.

**LinkedIn's Feathr.** Open sourced in 2022 after being, per its own README,
"battle tested in production for more than 6 years" at LinkedIn beforehand.
States its own point-in-time correctness guarantee explicitly, "point-in-time
correct semantics to avoid data leakage."

## 9. Known production uses

Uber Michelangelo is the namesake case, states plainly, "we have
approximately 10,000 features in Feature Store," at the time of its 2017
post, and remains referenced across the wider industry as the origin
implementation of the pattern.

Chronon's own GitHub README names ten real adopters directly, Airbnb,
Stripe, OpenAI, Roku, Netflix, Uber, Intuit, Airwallex, Sardine AI, and Monzo
Bank, a notable case of Uber itself appearing as an adopter of a second,
independent system alongside having built its own original in-house
platform, evidence of real consolidation activity in this space rather than
every large company maintaining a bespoke system forever.

LinkedIn's Feathr ran in production for more than six years internally
before its 2022 open-sourcing. Feast's own current homepage names Robinhood,
NVIDIA, Discord, Cloudflare, Walmart, Shopify, and Salesforce among its
listed adopters, though only as a named-adopter logo list rather than an
attributed case-study quote.

## 10. Consequences

Positive. Directly addresses training-serving skew through shared
computation and point-in-time-correct retrieval, the exact problem Google's
own Rules of Machine Learning names. Enables feature discovery and reuse
across teams and models rather than every model reinventing the same
computation, the original stated motivation behind Michelangelo's Feature
Store.

Negative. Real, ongoing infrastructure cost from running two synchronized
storage systems plus a materialization pipeline, three separate systems to
operate, monitor, and pay for rather than one. On-demand and request-time
features that bind serving-time computation to a specific platform API, such
as Databricks' model-logging convention for on-demand features, introduce a
genuine platform coupling cost alongside the correctness they buy.
Correctness itself is not automatic, it depends on disciplined,
consistently-applied point-in-time join usage, which dimension 11 shows is a
real, recurring, and well-documented failure mode rather than a solved
problem.

## 11. Failure modes and misuse

**Point-in-time join done incorrectly, causing label leakage.** This is the
single most cited feature-store correctness bug, and unusually, the
mechanism and the fix are both documented directly by a feature store
project against itself. Feast's own docs state, "a value that was backfilled
or corrected after an entity dataframe timestamp can still be returned for
it" unless the stricter, explicit created-timestamp condition described in
dimension 6 is enabled. A team that assumes the default join is
leakage-proof is wrong, and the wrongness produces no error, only a model
that looks better in offline evaluation than it performs in production.

**Online and offline drift when materialization lags or fails.** The online
store only ever holds the latest value per key, with no historical fallback,
so an interruption in the materialization job leaves the online store
silently stale relative to the offline store, with no built-in default
alerting on that staleness in the systems reviewed for this entry.

**Treating a feature store as a general-purpose warehouse substitute.**
Every store's own stated purpose, AWS's offline store framed narrowly around
"training, and batch predictions," is not a general warehouse, and treating
it as one accumulates scope and cost the system was never designed to carry.

## 12. Trade-off matrix

| Force | Feature store | Ad hoc per-model pipelines | Shared warehouse table |
|---|---|---|---|
| Freshness | Millisecond-latency online serving, near-real-time with a streaming materialization path | Whatever each pipeline implements independently, typically batch only | Batch-bound by definition, no low-latency serving path |
| Correctness against skew | Addressed directly by shared computation and point-in-time joins, still requires disciplined use | Each pipeline can silently diverge from every other | No skew risk from a serving path that does not exist, but no serving path at all |
| Reusability | Registry-based discovery across teams and models | None by default, every model reimplements | Reusable for offline consumers only |
| Operational cost | Highest, two synchronized stores plus a materialization pipeline | Lowest, no shared infrastructure to maintain | Low, a single existing system |

## 13. Related and incompatible patterns

**Model-registry** is the trained-artifact half of the same pipeline, a
feature store is the input side, a model registry the output side, and the
two compose directly, a served model reads from the online feature store
and is itself pulled from a model registry.

**Training-serving-skew-guard** is a real, close, and likely near-duplicate
risk against this entry. A feature store is architecturally designed to
prevent training-serving skew by construction, while a skew guard, by its
name, sounds like it detects skew after the fact through monitoring. These
are different pattern shapes aimed at the same underlying problem,
prevention-by-architecture against detection-by-monitoring, and this
overlap should be checked against the repository's duplicate detector rather
than resolved here.

**Batch-inference and online-inference** are the two consumer-side patterns
that read from a feature store's offline and online stores respectively, a
feature store is upstream infrastructure both depend on.

**Change data capture** is a common upstream producer feeding a feature
store's materialization pipeline, turning a database's own write history
into the raw material a feature transformation step consumes.

## 14. Refactoring path in and out

**In.** The consistent pattern across every vendor reviewed here starts from
feature-computation logic duplicated between a training notebook or pipeline
and a serving codepath, exactly the problem Google's Rules of Machine
Learning names, then extracts the shared feature definitions into a
registry, backs it with an offline store for training-time point-in-time
joins, and an online store fed by a materialization job for serving. Every
vendor's documented architecture, Feast, AWS, Databricks, and Google's
current platform, converges on this same shape independently.

**Out.** No vendor documents how to downgrade away from its own product, so
this direction is a defensible engineering judgment rather than a sourced
claim. A small team with one or two models can reasonably skip the separate
online and offline infrastructure entirely and instead standardize on a
shared feature-computation library, a versioned Python or Spark package
imported by both the training pipeline and the serving code, achieving the
same training-serving consistency goal Google's Rule 32 recommends, without
paying for a second storage system or a materialization job.

## 15. Testing and verification

Test the point-in-time join directly rather than trusting it by
construction. Seed the offline store with a feature value, a later
correction to that same value, and a training label timestamped between the
two, then assert the join returns the original value, never the correction,
proving no leakage occurred. Separately assert that enabling the stricter
created-timestamp filter changes the result exactly where a naive join would
have leaked. Test the materialization path by writing a known value
offline, running materialization, and asserting the online store returns
that exact value by entity key with no staleness. Test a deliberately
interrupted materialization run and assert the online store's staleness is
detectable, either through an explicit freshness signal or a test that
fails loudly rather than silently serving stale data.

## 16. Observability signals

Track materialization job lag, the time since the online store last
received a successful update per feature view, since dimension 11's drift
failure mode is silent by default and this is the signal that surfaces it.
Track online store read latency at the percentile level, since the entire
justification for the online store's existence is a millisecond-scale
latency bound, and a regression there undermines the pattern's whole reason
for being. Track the point-in-time join's row count and null rate during
training-set generation, an unexpected spike in null feature values often
indicates a registry or entity-key mismatch between the offline and online
paths. A healthy instance shows materialization lag flat and within its
target window, online read latency stable at its committed bound, and
training-set generation producing a consistent, expected null rate run over
run.

## 17. Security and privacy implications

A feature store frequently holds personal or behavioral data, purchase
history, location, demographic attributes, aggregated across every model
and team that consumes it, which concentrates privacy exposure in one
system rather than spreading it across many independent pipelines. Access
control on the registry and on both stores should reflect this
concentration, a feature accessible to one model's serving path is
effectively accessible to every team with access to the registry, not only
the team that originally computed it. A deletion request under a privacy
regulation must reach both the offline store, where historical values
persist for training-set generation, and the online store, where the
current value is served live, and a feature store with no coordinated
delete path across both leaves a real compliance gap open by construction.

## 18. References

Uber Engineering. "Meet Michelangelo. Uber's Machine Learning Platform."
Mike Del Balso, Jeremy Hermann. September 5, 2017. Verified 2026-08-23.
https://www.uber.com/blog/michelangelo-machine-learning-platform/.

Linux Foundation AI and Data. "Feast" project page. Verified 2026-08-23.
https://lfaidata.foundation/projects/feast/.

Feast. Documentation, registry, offline store, online store, and
point-in-time join concepts. Verified 2026-08-23.
https://docs.feast.dev/getting-started/concepts/point-in-time-joins.

Feast. Homepage. Verified 2026-08-23.
https://feast.dev/.

Google. "Rules of Machine Learning." Verified 2026-08-23.
https://developers.google.com/machine-learning/guides/rules-of-ml.

Amazon Web Services. "Amazon SageMaker Feature Store" documentation.
Verified 2026-08-23.
https://docs.aws.amazon.com/sagemaker/latest/dg/feature-store.html.

Databricks. "Databricks Feature Store" and "Online Feature Store"
documentation. Verified 2026-08-23.
https://docs.databricks.com/aws/en/machine-learning/feature-store/.

Google Cloud. "Introducing Gemini Enterprise." October 10, 2025. Verified
2026-08-23.
https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise.

Airbnb. "Chronon" repository README. Verified 2026-08-23.
https://github.com/airbnb/chronon.

LinkedIn. "Feathr" repository README. Verified 2026-08-23.
https://github.com/linkedin/feathr.

**Evidence grade.** medium

**Most solid findings.** The core architecture, registry, offline store,
online store, feature view, materialization, is independently and
consistently confirmed across four unrelated vendors, Feast, AWS,
Databricks, and Google, each describing essentially the same shape. The
point-in-time join leakage mechanism is confirmed directly from a feature
store project's own documentation of the exact bug and its own fix. The
Google Vertex AI to Gemini Enterprise rename is confirmed at the level of a
live current page title and a direct executive quote.

**Unverified or unclear.** Whether Databricks formally acquired Tecton, and
when, could not be confirmed by a citable press release during this entry's
research, only that tecton.ai now redirects wholesale to databricks.com,
so no acquisition claim is made in the entry body. Tecton's own founding
story is not cited here for the same reason. A dedicated Feast case study
with an attributed customer quote could not be located, so Feast's adopters
are named only as a logo-list claim, not as a sourced testimonial.

## Code examples

A minimal feature store simulation across three languages. Each implements
a registry mapping feature names to entity keyed values, a materialization
step copying the latest offline value into an online store, and a
point-in-time correct lookup that never returns a value newer than the
requested timestamp.

### TypeScript

```typescript
interface FeatureRecord {
  entityId: string;
  value: number;
  eventTimestamp: number;
}

class OfflineStore {
  private records: FeatureRecord[] = [];

  write(record: FeatureRecord): void {
    this.records.push(record);
  }

  pointInTimeLookup(entityId: string, asOf: number): FeatureRecord | null {
    const candidates = this.records.filter(
      (r) => r.entityId === entityId && r.eventTimestamp <= asOf
    );
    if (candidates.length === 0) {
      return null;
    }
    return candidates.reduce((latest, r) =>
      r.eventTimestamp > latest.eventTimestamp ? r : latest
    );
  }
}

class OnlineStore {
  private latest = new Map<string, FeatureRecord>();

  materialize(record: FeatureRecord): void {
    const current = this.latest.get(record.entityId);
    if (!current || record.eventTimestamp > current.eventTimestamp) {
      this.latest.set(record.entityId, record);
    }
  }

  get(entityId: string): FeatureRecord | undefined {
    return this.latest.get(entityId);
  }
}
```

### Python

```python
from dataclasses import dataclass


@dataclass
class FeatureRecord:
    entity_id: str
    value: float
    event_timestamp: int


class OfflineStore:
    def __init__(self):
        self._records: list[FeatureRecord] = []

    def write(self, record: FeatureRecord) -> None:
        self._records.append(record)

    def point_in_time_lookup(self, entity_id: str, as_of: int) -> FeatureRecord | None:
        candidates = [
            r for r in self._records
            if r.entity_id == entity_id and r.event_timestamp <= as_of
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda r: r.event_timestamp)


class OnlineStore:
    def __init__(self):
        self._latest: dict[str, FeatureRecord] = {}

    def materialize(self, record: FeatureRecord) -> None:
        current = self._latest.get(record.entity_id)
        if current is None or record.event_timestamp > current.event_timestamp:
            self._latest[record.entity_id] = record

    def get(self, entity_id: str) -> FeatureRecord | None:
        return self._latest.get(entity_id)
```

### Go

```go
package featurestore

type FeatureRecord struct {
	EntityID       string
	Value          float64
	EventTimestamp int64
}

type OfflineStore struct {
	records []FeatureRecord
}

func (s *OfflineStore) Write(record FeatureRecord) {
	s.records = append(s.records, record)
}

func (s *OfflineStore) PointInTimeLookup(entityID string, asOf int64) (FeatureRecord, bool) {
	var latest FeatureRecord
	found := false
	for _, r := range s.records {
		if r.EntityID == entityID && r.EventTimestamp <= asOf {
			if !found || r.EventTimestamp > latest.EventTimestamp {
				latest = r
				found = true
			}
		}
	}
	return latest, found
}

type OnlineStore struct {
	latest map[string]FeatureRecord
}

func NewOnlineStore() *OnlineStore {
	return &OnlineStore{latest: make(map[string]FeatureRecord)}
}

func (s *OnlineStore) Materialize(record FeatureRecord) {
	current, exists := s.latest[record.EntityID]
	if !exists || record.EventTimestamp > current.EventTimestamp {
		s.latest[record.EntityID] = record
	}
}

func (s *OnlineStore) Get(entityID string) (FeatureRecord, bool) {
	r, ok := s.latest[entityID]
	return r, ok
}
```
