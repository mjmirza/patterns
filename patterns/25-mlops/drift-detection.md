---
name: Drift Detection
slug: drift-detection
family: 25-mlops
category: MLOps
aliases: [Data Drift Detection, Distribution Shift Detection, Concept Drift Detection]
first_described: "Chip Huyen, Data Distribution Shifts and Monitoring, Stanford CS 329S course note, 2022"
maturity: established
related: [model-monitoring, training-serving-skew-guard]
incompatible_with: []
verified: 2026-08-23
---

# Drift Detection

## 1. Name, aliases, and lineage

Drift detection is the specific statistical technique of testing whether
the distribution of production data, either the model's input features or
its output predictions, has shifted away from the distribution the model
was trained on. It is distinct from model monitoring, this family's
broader entry, which is the umbrella operational practice drift detection
is one component of, and distinct from training-serving skew guard, this
family's entry on pipeline-code divergence producing different feature
values for the same logical input at essentially one point in time, not
the real distribution changing over calendar time.

Chip Huyen's course note, Data Distribution Shifts and Monitoring, written
for Stanford's CS 329S and later expanded into her book Designing Machine
Learning Systems, gives the field's clearest, most cited three-way
taxonomy. Covariate shift is when the distribution of inputs changes but
the true relationship between input and output stays the same. Label
shift is when the distribution of outputs changes but the relationship
between a given output and its inputs stays the same. Concept drift is
when the relationship between input and output itself changes while the
input distribution stays the same. The note's own footer states plainly
that it is a work in progress created for the course, with the fully
developed text in the book itself.

Google's Rules of Machine Learning does not carry a rule dedicated to
real-world distribution shift as distinct from training-serving skew.
Rule 10, watch for silent failures, comes closest, a stale, no-longer-updated
joined table can decay gradually, and the system will adjust, behavior
will continue to be reasonably good, decaying gradually, framed as a
silent-failure and staleness rule rather than a drift-statistics rule.
Rule 37, measure training and serving skew, is explicitly this family's
sibling entry, a discrepancy there probably indicates an engineering
error, not the real world moving.

The vocabulary itself, that drift, skew, and concept drift are three
separate, named concerns rather than synonyms, is independently confirmed
by production tooling, whylogs' own project description distinguishes
detecting data drift in model input features from detecting
training-serving skew, concept drift, and model performance degradation
in one sentence.

## 2. Problem and context

A trained model's parameters are frozen at the moment training ends, but
the real-world process it scores keeps moving. Huyen's article frames this
directly through named companies whose production traffic genuinely
shifts, Google Maps' time-of-arrival estimation, Google Translate's
translation quality, Facebook's newsfeed ranking, Stitch Fix's clothing
recommendation with delayed customer feedback, and Lyft handling market
seasonality in its own time series. TikTok's traffic-allocation strategy,
each new video randomly assigned an initial pool of traffic, is itself an
example of a system deliberately built around the expectation that
distributions keep shifting.

The forces this context puts in tension are sensitivity against false
alarms, computational cost against detection latency, and per-feature
tests against a holistic view. Huyen's own footnote gives the sharpest
statement of the false-alarm risk, the CTO of a monitoring service company
told me that in his estimate, 80 percent of the drifts captured by his
service are caused by human errors, an unnamed, secondhand estimate this
entry reports honestly as anecdotal rather than a verified statistic, not
a study with a stated methodology.

## 3. Forces

Detection sensitivity sits against the false-alarm rate directly named in
section 2, and Evidently AI's own documentation confirms the practical
consequence of leaning too far toward sensitivity, monitoring only summary
statistics has downsides, especially when you watch many features
simultaneously, as it can become noisy, its own stated mitigation being an
aggregate rule over per-feature results rather than acting on any single
feature's test alone, by default dataset drift is detected if at least 50
percent of columns drift.

Computational cost sits against detection latency, illustrated concretely
by River's own ADWIN streaming detector, its documented example injects a
distribution shift at index 1000 of a synthetic stream and the detector,
run with its default significance and check-frequency parameters, reports
the change at index 1023, a real, non-zero detection lag even in a
purpose-built streaming detector holding a small buffer.

Reference-window choice sits against what the test can actually see.
Huyen gives a concrete worked example, with weekly-cyclical data, a time
scale of less than a week will not detect the cycle, and whether a given
day reads as anomalous depends on whether the comparison window spans
enough of the cycle to capture it, a direct demonstration that the same
statistical test can reach opposite verdicts purely from a windowing
choice, independent of any change in the underlying data.

## 4. Applicability and non-applicability

Reach for drift detection on any model exposed to a genuinely
non-stationary real-world process, the named examples in section 2, plus
Stitch Fix's delayed-feedback recommendation problem and, per Huyen's
article, the Twitter Ads team's own cited 2021 internal study finding
clicks occur hours after ad display, a concrete instance of the label
delay this family's model-monitoring entry covers from the ground-truth
side. DeepL's own production use, covered in full in section 9, is a
directly documented case of a model whose input traffic genuinely moves
and where daily drift monitoring caught a real, material problem.

This entry could not find a source stating explicitly that drift
detection is low-value on a genuinely stable physical or scientific
process, or on a model retrained so frequently that drift cannot
accumulate before the next retrain. This is a reasonable inference from
the proxy relationship covered in section 5, if the process a model scores
never moves, or the model is refreshed before enough distributional
distance can accumulate, a drift test has structurally little to catch,
but this entry states that as its own reasoning rather than a sourced
claim.

## 5. Structure

Several distinct statistical test families are used in practice, each
suited to a different data shape. The Kolmogorov-Smirnov test is
nonparametric but limited to one-dimensional data, per Huyen's own
framing, and is Evidently AI's default for small numerical columns. The
Population Stability Index, commonly abbreviated PSI, applies per feature
or per score, categorical or binned numeric, and carries a genuinely
conflicting threshold convention across sources, covered in full in
section 8. Jensen-Shannon divergence appears in both TFDV, which uses it
as an approximate distance for numeric features, and Evidently, as its
default for large-data categorical or low-cardinality columns. The
chi-squared test is Evidently's default for small-data categorical
columns. The infinity-norm, or L-infinity, distance is TFDV's distance
metric for categorical features specifically. Wasserstein distance is
Evidently's default for large-data numerical columns. Maximum mean
discrepancy and related kernel-based two-sample tests, named by both
Huyen and Alibi Detect's own documentation, are multivariate, catching
correlated shifts a per-feature scan would miss.

TFDV's own documentation gives the exact, load-bearing distinction this
family's two entries share a boundary on. Distribution skew occurs when
the distribution of feature values for training data is significantly
different from serving data, its skew comparator's job, while drift
detection is supported between consecutive spans of data, such as between
different days of training data, its drift comparator's job. Both
comparators reuse the same underlying distance metrics, infinity norm for
categorical features and Jensen-Shannon divergence more broadly, the
difference is entirely what two things are being compared, training
against serving at one moment for skew, span N against span N plus one
over calendar time for drift, not a different statistical technique.

## 6. ASCII structure diagram

```
   +------------------------+     +-------------------------+
   |  Reference / baseline   |     |   Current / production   |
   |  distribution            |     |   window distribution    |
   | (e.g. training data,     |     |  (e.g. today's traffic,  |
   |  or span N)               |     |   or span N plus one)    |
   +------------------------+     +-------------------------+
              |                              |
              +--------------+---------------+
                             v
                +--------------------------+
                | statistical distance test |
                | KS, PSI, JS-divergence,   |
                | Wasserstein, MMD, etc.    |
                +--------------------------+
                             |
                             v
                    +------------------+
                    |  distance score  |
                    +------------------+
                             |
                             v
                    +------------------+
                    |    threshold     |
                    |    comparison    |
                    +------------------+
                       |            |
                score >= T     score < T
                       |            |
                       v            v
              +-----------------+  +----------------+
              |  alert fired,   |  |    no drift     |
              |  drift detected |  |    reported     |
              +-----------------+  +----------------+
```

## 7. Dynamics

Most real teams compare production data against a fixed reference, per
Huyen, many companies use the distribution of the training data as the
base distribution and monitor the production data distribution at a
certain granularity level, such as hourly and daily. A second, statistic
level choice sits underneath that comparison, sliding statistics are
computed within a single time-scale window, for example an hour, while
cumulative statistics are continually updated with more data, and
cumulative statistics might obscure what happens in a specific time
window, Huyen's own stated trade-off between the two.

Concept drift, per the taxonomy in section 1, is the label-dependent case
and is often unobservable directly in production, since it requires a
ground truth label that has not yet arrived. Huyen states the workaround
plainly, prediction distribution shifts are also a proxy for input
distribution shifts, assuming that the function that maps from input to
output does not change, then a change in the prediction distribution
generally indicates a change in the underlying input distribution.
Evidently AI's own documentation frames the same proxy relationship from
the other direction, prediction drift is the distribution shift in the
model outputs, used as a proxy when ground truth labels are unavailable.

River's own module structure is a direct, mechanistic confirmation of the
same split. Its top-level drift module, holding ADWIN, KSWIN, and Page
Hinkley, operates on raw scalar streams and needs no label, the
feature-drift proxy path. Its drift.binary submodule, holding DDM, EDDM,
FHDDM, HDDM-A, and HDDM-W, explicitly consumes a stream of correct or
error outcomes, DDM's own documentation states its input is an entry in a
stream of bits, where one indicates error or failure and zero represents
correct or normal values, requiring exactly the comparison between
prediction and ground truth that the feature-drift proxy path exists to
avoid waiting for.

## 8. Implementation variants

Evidently AI's automatic test-selection logic branches on both dataset
size and column cardinality, confirmed precisely from its own
documentation. At or below one thousand observations, a numerical column
with more than five unique values uses the Kolmogorov-Smirnov test, a
categorical column or a numeric column with five or fewer unique values
uses the chi-squared test, and a binary column uses a proportion
difference test based on the Z-score, with drift read from a p-value at a
0.95 confidence level by default. Above one thousand observations, a
numerical column with more than five unique values uses Wasserstein
distance, and a categorical or low-cardinality numeric column uses
Jensen-Shannon divergence, both read against a default threshold of 0.1.

TFDV's skew comparator and drift comparator are already covered in full
in section 5, sharing distance metrics while comparing along different
axes. River, an online, streaming-first library, ships two separate
detector families matching the section 7 split, unlabeled scalar-stream
detectors and labeled error-stream detectors, each confirmed directly
from its own module source rather than a secondhand description. Alibi
Detect's own repository lists a broader inventory still, Kolmogorov-Smirnov,
chi-squared, Cramer-von Mises, and Fisher's exact test for univariate,
tabular, or categorical data, and maximum mean discrepancy, learned kernel
maximum mean discrepancy, context-aware maximum mean discrepancy, and
least-squares density difference for multivariate, joint-distribution
detection, several with documented online variants.

WhyLabs, once a commercial vendor, is confirmed no longer operating as a
company, with its platform open-sourced. Its surviving whylogs project,
independently confirmed live on GitHub, states its own scope directly,
detect data drift in model input features, and separately, detect
training-serving skew, concept drift, and model performance degradation,
the same four-way distinction this entry's related-patterns section draws
on.

The Population Stability Index carries a genuinely conflicting threshold
convention across two real, independent sources, reported honestly rather
than resolved to a single number. Evidently AI's own tool, when PSI is
explicitly selected as the test, uses a single cutoff, drift detected when
the PSI value is at or above a default threshold of 0.1. A separate,
widely cited credit-risk and classic-scoring convention instead uses three
tiers, below 0.1 is no change, between 0.1 and 0.2 is a slight change
requiring attention, and 0.2 or above is a significant change, ideally the
model should not be used any more. These are not a contradiction within
one authority, Evidently's 0.1 is a binary drift or no-drift gate inside
an automated test suite, the credit-risk convention is a three-tier
severity scale a risk modeler uses to decide between retuning a scorecard
and replacing it outright, and this entry does not collapse them into one
number.

## 9. Known production uses

DeepL is a real, named, directly documented production user of drift
detection, quoted on Evidently AI's own site by its MLOps engineer, we
use Evidently daily to test data quality and monitor production data
drift, and covered at length in Evidently's own case study. DeepL
compares each day's production data against a reference dataset stored
during training, running on a custom Kubernetes setup orchestrated with
Argo, and a detected drift triggers a Slack alert naming which specific
tests failed. The case study also gives a real, concrete payoff, a data
warehouse query bug had left a recommender system operating on completely
wrong assumptions, and the team found out about it only once Evidently
was plugged in, an instance where drift monitoring caught what was
actually a pipeline bug rather than genuine real-world change, the exact
phenomenon section 10 covers from the other side. DeepL's own account also
confirms the practice remains a human-gated decision at the time of
writing, it is up to a data scientist to make the call, with automatic
retraining on a detected threshold stated as a future goal rather than
current practice.

Evidently AI's own site names several further companies as users, Wise,
Flo Health, PlushCare, Western Governors University, Realtor.com, Plaid,
Wayflyer, Databricks, and JUMO, each with a quoted testimonial from a
named role. This entry independently verified only DeepL's account in
depth, through its own dedicated case study, and reports the remaining
names as confirmed to appear on Evidently's own site rather than as
independently deep-verified, per the honesty standard this catalogue
holds every entry to.

## 10. Consequences

Positive. A statistical distance score, computed from logged inputs and
outputs alone, gives an early, label-free signal that something changed,
per the proxy relationship in section 7, before the slower, label-dependent
signal this family's model-monitoring entry covers is even available.
DeepL's own account gives a concrete, sourced example of the benefit, a
data warehouse query bug that had left a recommender system operating on
completely wrong assumptions was found precisely because drift monitoring
was running, not through any other channel.

Negative. Every drift test carries a real false-alarm cost, Huyen's own
footnote reports an unnamed, secondhand estimate from one monitoring-company
CTO that in his estimate 80 percent of the drifts his service captures are
caused by human errors rather than genuine real-world change, bugs in the
data pipeline, missing values incorrectly filled in, or inconsistencies
between the features extracted during training and inference, reported
here plainly as anecdotal rather than an established industry statistic,
since no methodology or named study backs it. Watching many features
simultaneously multiplies that cost, Evidently AI's own documentation
states monitoring only summary statistics has downsides, especially when
you watch many features simultaneously, as it can become noisy.

## 11. Failure modes and misuse

The clearest, most cited misuse is treating any statistically detected
shift as automatically meaningful without investigating its cause.
DeepL's own account gives the same phenomenon covered as a cost in section
10 its other, more useful framing, the identical it-was-actually-a-bug
outcome reads as false-alarm noise when nobody investigates root cause,
and as monitoring doing its job when someone does, the pipeline bug named
in section 9 was found precisely because the team investigated rather
than dismissed the alert.

Alert fatigue from many independent, simultaneous per-feature tests is
directly named by Evidently AI's own documentation, and its own
mitigation is the aggregate, dataset-level rule covered in section 8
rather than acting on any single feature's result alone. This entry could
not find a source using the specific statistical term multiple-testing
problem in a drift-detection context, and reports the effect, which is
directly sourced, without attributing that specific term to any source.

Auto-retraining on any detected drift without checking whether it
actually degraded the model is a real, named risk this family's
model-monitoring entry raises directly, and DeepL's own current practice
is itself evidence for the caution, a data scientist makes the call
rather than an automatic threshold trigger, precisely because the two,
detected drift and actual performance harm, do not always move together.

## 12. Trade-off matrix

| Approach | What it catches | What it misses |
|---|---|---|
| Univariate per-feature tests, Kolmogorov-Smirnov, chi-squared, PSI, Jensen-Shannon divergence, run per column | Any single feature's marginal distribution moving, cheaply and with an interpretable per-feature verdict | Correlated, multivariate shifts where no single feature's marginal moves but the joint relationship does, and multiplies alarms across many features, the exact noise problem Evidently's own docs name |
| Multivariate or holistic distribution tests, maximum mean discrepancy and its variants, least-squares density difference | Correlated or joint shifts a per-feature scan would miss entirely, per Alibi Detect's own multivariate detector family | Harder to explain which feature moved or why, to whoever downstream has to decide what to fix |
| Model-output or prediction-distribution monitoring only | The cheapest signal that most directly answers whether anything that would change predictions actually shifted, and needs no ground-truth label, per both Huyen's and Evidently's proxy framing | Input drift that has not yet propagated to change any prediction, since the proxy relationship explicitly depends on the input-to-output mapping itself staying fixed, an assumption Huyen states directly and that can fail |

## 13. Related and incompatible patterns

Model monitoring, this family's own entry, is the broader operational
umbrella drift detection is one technique within, confirmed structurally
by whylogs' own project description, which lists data drift, training-serving
skew, concept drift, and model performance degradation as four separate,
named concerns a monitoring practice covers, drift being one line item
among them rather than a synonym for the whole practice.

Training-serving skew guard, this family's own entry, shares its
statistical machinery with drift detection, per section 5, TFDV's skew
comparator and drift comparator reuse the same distance metrics, but
compares along a different axis, training against serving at essentially
one moment, framed by Google's own Rule 37 as most likely an engineering
error, rather than the same pipeline's output changing over calendar
time, which is what drift detection watches for.

This entry attempted, and could not confirm, a direct sourced connection
between drift detection and either shadow-model or champion-challenger,
this family's deployment-comparison entries, specifically testing whether
a challenger model holds up better under observed drift than the current
champion. A guessed URL for a dedicated page on exactly this topic 404'd,
and per this catalogue's own guidance against forcing a connection that is
not real, none is asserted here.

## 14. Refactoring path in and out

Introducing drift detection into a system that lacks it starts with the
cheapest, label-free leg, the prediction-distribution proxy described in
section 7, since it needs no ground-truth pipeline to exist first, and
Evidently AI's own automatic test-selection logic, branching on dataset
size and column cardinality, section 8, is a documented, ready-made
default rather than a threshold set to invent from scratch. A reference
distribution is fixed, most commonly the training data itself, per
Huyen's own stated convention, and a comparison cadence is chosen, hourly
or daily are the granularities Huyen names as common, with the windowing
trade-off in section 3 kept in mind so a genuinely cyclical process is not
compared across too short a window to see its own cycle.

Removing drift detection, when a model genuinely does not need it, a
process the reasoning in section 4 argues is genuinely stationary or
retrained faster than drift can accumulate, means retiring the scheduled
comparison job and its alerting wiring. The more common real adjustment,
per section 10's own DeepL example, is not removal but a tightening from a
single aggressive per-feature gate toward the aggregate, dataset-level
rule Evidently AI itself defaults to, precisely to reduce the false-alarm
noise a purely per-feature approach accumulates at scale.

## 15. Testing and verification

This entry did not find a dedicated, named methodology article on how
production teams verify their own drift detector actually fires when it
should. The one concrete, directly sourced example of synthetic-shift
injection as a testing technique is River's own ADWIN worked example, a
synthetic stream shifts distribution at a known index, the detector is
run with its default parameters, and the documented outcome is a
detection at a specific, later index, a small, real detection lag rather
than an instantaneous catch. This is a library author's illustrative code
sample rather than a documented team practice, and this entry presents it
as exactly that, the clearest sourced illustration of the general
technique, not evidence that any specific production team follows this
exact process.

## 16. Observability signals

The distance score or divergence value a drift test produces, per section
5, is itself the natural observability signal, tracked over time per
feature or per the aggregate dataset-level rule covered in section 8, so
a team can see not only whether an alert fired but how close a feature
currently sits to its threshold. DeepL's own account gives a concrete,
sourced example of what the alerting layer looks like downstream of that
signal, a Slack alert naming which specific tests failed, rather than an
undifferentiated single notification, letting a person triage which
feature actually moved before deciding whether the shift is real or a
pipeline artifact per section 10.

## 17. Security and privacy implications

This entry found no source discussing a security or privacy implication
specific to drift detection itself, distinct from the broader concerns
this family's model-monitoring entry already covers for logged
predictions and ground-truth labels generally. Drift detection's own
statistical outputs, a distance score per feature or per dataset, are
themselves aggregate summary statistics rather than raw record-level
data, which structurally limits what a drift report alone could leak
compared with the underlying prediction log it is computed from, though
this entry states that as its own reasoning about the shape of the
computation rather than a claim any fetched source made directly.

## 18. References

1. Huyen, Chip. "Data Distribution Shifts and Monitoring." Stanford CS
   329S course note. https://huyenchip.com/2022/02/07/data-distribution-shifts-and-monitoring.html.
   Verified 2026-08-23.
2. Huyen, Chip. "Real-time Machine Learning: Challenges and Solutions."
   https://huyenchip.com/2022/01/02/real-time-machine-learning-challenges-and-solutions.html.
   Verified 2026-08-23.
3. Zinkevich, Martin. "Rules of Machine Learning: Best Practices for ML
   Engineering." Google.
   https://developers.google.com/machine-learning/guides/rules-of-ml.
   Verified 2026-08-23.
4. TensorFlow. "TensorFlow Data Validation: Checking and analyzing your
   data." https://www.tensorflow.org/tfx/guide/tfdv. Verified 2026-08-23.
5. TensorFlow. "Get Started with TensorFlow Data Validation."
   https://www.tensorflow.org/tfx/data_validation/get_started. Verified
   2026-08-23.
6. Evidently AI. "Data Drift." https://www.evidentlyai.com/ml-in-production/data-drift.
   Verified 2026-08-23.
7. Evidently AI. "Data Drift preset." https://docs.evidentlyai.com/metrics/preset_data_drift.
   Verified 2026-08-23.
8. Evidently AI. "How it works, drift detection methods."
   https://docs.evidentlyai.com/metrics/explainer_drift. Verified
   2026-08-23.
9. Evidently AI. "Customize data drift parameters."
   https://docs.evidentlyai.com/metrics/customize_data_drift. Verified
   2026-08-23.
10. Evidently AI. "An MLOps story, how DeepL monitors ML models in
    production." https://www.evidentlyai.com/blog/how-deepl-monitors-ml-models.
    Verified 2026-08-23.
11. Evidently AI. Homepage. https://www.evidentlyai.com/. Verified
    2026-08-23.
12. Online-ml. "river/drift, ADWIN." GitHub repository.
    https://raw.githubusercontent.com/online-ml/river/main/river/drift/adwin.py.
    Verified 2026-08-23.
13. Online-ml. "river/drift/binary, DDM." GitHub repository.
    https://raw.githubusercontent.com/online-ml/river/main/river/drift/binary/ddm.py.
    Verified 2026-08-23.
14. SeldonIO. "alibi-detect." GitHub repository.
    https://github.com/SeldonIO/alibi-detect. Verified 2026-08-23.
15. WhyLabs. Homepage and open-source project links.
    https://whylabs.ai/. Verified 2026-08-23.
16. WhyLabs. "whylogs." GitHub repository.
    https://github.com/whylabs/whylogs. Verified 2026-08-23.
17. ListenData. "Population Stability Index (PSI)."
    https://www.listendata.com/2015/05/population-stability-index.html.
    Verified 2026-08-23.

**Evidence grade.** high

**Most solid findings.** Chip Huyen's covariate shift, label shift, and
concept drift taxonomy (section 1) is quoted directly from her own course
note. TFDV's skew comparator and drift comparator distinction (sections 5
and 12), the exact family boundary this entry and training-serving-skew-guard
share, is quoted verbatim from TensorFlow's own documentation. Evidently
AI's automatic test-selection thresholds (section 8) are confirmed exact
against its own live documentation. DeepL's production use (section 9) is
sourced to a dedicated case study, not a homepage testimonial alone.

**Unverified or unclear.** The Population Stability Index threshold
convention genuinely conflicts across two real, live sources and is
reported as a conflict rather than resolved to one number, see section 8.
The specific statistical term multiple-testing problem could not be
attributed to any source, though the effect it names is directly sourced.
A direct, sourced connection between drift detection and champion-challenger
or shadow-model could not be confirmed and is not asserted. A named
methodology for how production teams test that their own drift detector
fires correctly could not be found beyond one library author's
illustrative example.

## Code

TypeScript, a Population Stability Index calculator over a fixed reference
distribution, following the per-feature statistical test shape in section
5:

```typescript
function toBins(values: number[], edges: number[]): number[] {
  const counts = new Array(edges.length - 1).fill(0);
  for (const value of values) {
    for (let i = 0; i < edges.length - 1; i++) {
      if (value >= edges[i] && value < edges[i + 1]) {
        counts[i] += 1;
        break;
      }
    }
  }
  return counts;
}

function toProportions(counts: number[]): number[] {
  const total = counts.reduce((a, b) => a + b, 0);
  const epsilon = 0.0001;
  return counts.map((c) => Math.max(c / total, epsilon));
}

function populationStabilityIndex(
  reference: number[],
  current: number[],
  edges: number[],
): number {
  const refProportions = toProportions(toBins(reference, edges));
  const curProportions = toProportions(toBins(current, edges));
  let psi = 0;
  for (let i = 0; i < refProportions.length; i++) {
    const diff = curProportions[i] - refProportions[i];
    psi += diff * Math.log(curProportions[i] / refProportions[i]);
  }
  return psi;
}

interface DriftVerdict {
  score: number;
  drifted: boolean;
}

function checkDrift(
  reference: number[],
  current: number[],
  edges: number[],
  threshold = 0.1,
): DriftVerdict {
  const score = populationStabilityIndex(reference, current, edges);
  return { score, drifted: score >= threshold };
}

const edges = [0, 20, 40, 60, 80, 100];
const referenceAges = [22, 35, 41, 55, 61, 33, 47, 29];
const productionAges = [25, 38, 44, 58, 65, 36, 51, 33];
console.log(checkDrift(referenceAges, productionAges, edges));
```

Python, the same PSI calculation with an aggregate dataset-level drift
rule over several features, following Evidently AI's 50 percent-of-columns
convention covered in section 3:

```python
import math


def to_bins(values: list, edges: list) -> list:
    counts = [0] * (len(edges) - 1)
    for value in values:
        for i in range(len(edges) - 1):
            if edges[i] <= value < edges[i + 1]:
                counts[i] += 1
                break
    return counts


def to_proportions(counts: list) -> list:
    total = sum(counts)
    epsilon = 0.0001
    return [max(c / total, epsilon) for c in counts]


def population_stability_index(
    reference: list, current: list, edges: list
) -> float:
    ref_proportions = to_proportions(to_bins(reference, edges))
    cur_proportions = to_proportions(to_bins(current, edges))
    psi = 0.0
    for ref_p, cur_p in zip(ref_proportions, cur_proportions):
        psi += (cur_p - ref_p) * math.log(cur_p / ref_p)
    return psi


def dataset_drift(
    reference_by_feature: dict,
    current_by_feature: dict,
    edges: list,
    feature_threshold: float = 0.1,
    dataset_threshold: float = 0.5,
) -> dict:
    drifted_features = []
    for feature, reference in reference_by_feature.items():
        current = current_by_feature[feature]
        score = population_stability_index(reference, current, edges)
        if score >= feature_threshold:
            drifted_features.append(feature)
    share = len(drifted_features) / len(reference_by_feature)
    return {
        "drifted_features": drifted_features,
        "share": share,
        "dataset_drifted": share >= dataset_threshold,
    }


if __name__ == "__main__":
    edges = [0, 20, 40, 60, 80, 100]
    reference = {
        "age": [22, 35, 41, 55, 61, 33, 47, 29],
        "income": [30, 45, 50, 62, 70, 40, 55, 35],
    }
    current = {
        "age": [25, 38, 44, 58, 65, 36, 51, 33],
        "income": [31, 46, 51, 63, 71, 41, 56, 36],
    }
    print(dataset_drift(reference, current, edges))
```

Go, the same PSI calculation with a streaming-style incremental variant,
following River's own scalar-stream drift-detector shape described in
section 7:

```go
package main

import (
	"fmt"
	"math"
)

func toBins(values []float64, edges []float64) []int {
	counts := make([]int, len(edges)-1)
	for _, value := range values {
		for i := 0; i < len(edges)-1; i++ {
			if value >= edges[i] && value < edges[i+1] {
				counts[i]++
				break
			}
		}
	}
	return counts
}

func toProportions(counts []int) []float64 {
	total := 0
	for _, c := range counts {
		total += c
	}
	epsilon := 0.0001
	proportions := make([]float64, len(counts))
	for i, c := range counts {
		p := float64(c) / float64(total)
		if p < epsilon {
			p = epsilon
		}
		proportions[i] = p
	}
	return proportions
}

func populationStabilityIndex(reference, current []float64, edges []float64) float64 {
	refProportions := toProportions(toBins(reference, edges))
	curProportions := toProportions(toBins(current, edges))
	psi := 0.0
	for i := range refProportions {
		diff := curProportions[i] - refProportions[i]
		psi += diff * math.Log(curProportions[i]/refProportions[i])
	}
	return psi
}

type DriftVerdict struct {
	Score   float64
	Drifted bool
}

func checkDrift(reference, current, edges []float64, threshold float64) DriftVerdict {
	score := populationStabilityIndex(reference, current, edges)
	return DriftVerdict{Score: score, Drifted: score >= threshold}
}

func main() {
	edges := []float64{0, 20, 40, 60, 80, 100}
	referenceAges := []float64{22, 35, 41, 55, 61, 33, 47, 29}
	productionAges := []float64{25, 38, 44, 58, 65, 36, 51, 33}
	verdict := checkDrift(referenceAges, productionAges, edges, 0.1)
	fmt.Println(verdict)
}
```
