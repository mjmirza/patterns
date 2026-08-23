---
name: Shadow Model
slug: shadow-model
family: 25-mlops
category: MLOps
aliases: [Shadow Deployment, Shadow Testing, Shadow Variant]
first_described: "Martin Fowler, Dark Launching, martinfowler.com bliki, undated"
maturity: established
related: [online-inference, model-registry, champion-challenger, training-serving-skew-guard]
incompatible_with: []
verified: 2026-08-23
---

# Shadow Model

## 1. Name, aliases, and lineage

A shadow model, also called a shadow deployment or shadow variant, is a
candidate model version that runs against real production traffic in
parallel with the currently-serving model, computing predictions from the
same live input, without ever returning those predictions to the caller.
Its sole purpose is observation, gathering evidence on how the candidate
would have performed before anyone decides to promote it.

The general software-engineering shape of this idea predates machine
learning specifically. Martin Fowler's bliki entry on Dark Launching
defines it directly, dark launching a feature means taking a new or
changed back-end behavior and calling it from existing users without the
users being able to tell it is being called, illustrated with a retail
cross-sell recommendation engine running live in production while its
results stay hidden from users, purely to assess load and performance
before public rollout. Istio's own documentation for traffic mirroring
uses the word shadowing as a direct synonym, mirroring sends a copy of
live traffic to a mirrored service, out of band of the critical request
path, and these requests are mirrored as fire and forget, meaning the
responses are discarded, the infrastructure-layer version of the same
non-exposure guarantee.

The ML-specific framing is given by Danilo Sato's Continuous Delivery for
Machine Learning article on martinfowler.com, this pattern is useful when
considering the replacement of a model in production. You can deploy the
new model side by side with the current one, as a shadow model, and send
the same production traffic to gather data on how the shadow model
performs before promoting it, explicitly distinguished in the same article
from a slightly more complex, exposed alternative, competing models, like
an A/B test.

## 2. Problem and context

A/B testing a new model candidate necessarily risks real users receiving a
worse prediction, because the candidate's output is served to some
fraction of live requests. Shadow testing eliminates that specific risk by
construction, the candidate's output is architecturally incapable of
reaching the user, since AWS SageMaker's own documentation states the
shadow variant's responses are logged for comparison and not returned to
the caller. The trade a team makes for that safety is real, shadow mode
can only compare logged predictions against production predictions on the
same input, it cannot measure genuine user behavioral response, click,
conversion, engagement, to the candidate's actual output, since that
output never reaches anyone.

## 3. Forces

- Zero exposure risk versus zero behavioral signal. Shadow mode
  eliminates the possibility of a bad candidate harming a real user, but
  by the same construction it cannot observe how a real user would have
  responded to the candidate's actual prediction.
- Running two models per request versus one. Every shadowed request pays
  for a second forward pass, doubling compute for whatever fraction of
  traffic is sampled.
- A long-running validation window versus a quick smoke test. AWS's own
  documentation frames shadow variants as long running, oriented toward
  sustained observation rather than a brief check.
- Fire-and-forget simplicity versus a documented comparison mechanism. No
  fetched source, AWS, the CD4ML article, or Istio's docs, describes a
  concrete built-in method for comparing shadow output to production
  output afterward, leaving that work to the operator.

## 4. Applicability and non-applicability

Worth the doubled compute cost when the goal is confidence that a
candidate is correct and stable before any real user is exposed to it,
which is exactly how AWS frames its own feature, to validate any new
candidate component of your model serving stack before promoting it to
production. Not the right tool when the goal is measuring real user
response, click-through, conversion, or another downstream business
metric, since shadow mode structurally cannot observe that, the CD4ML
article's own adjacent pattern, competing models, an A/B test, is the one
sources point to for that case.

## 5. Structure

A shadow variant receives a replicated copy of a defined percentage of the
requests going to the production variant, executes independently, and its
response is logged rather than returned. AWS SageMaker's documented API
shape sets this precisely, a `ShadowModeConfig` names one production,
source variant and exactly one shadow variant per source, per the API
reference's stated array constraint, and a per-shadow `SamplingPercentage`,
an integer with a documented maximum of 100 and no stated minimum or
default, controls what share of requests get replicated.

## 6. ASCII structure diagram

```
  request
     |
     +----------------------+
     |                       |
     v                       v
  production variant     shadow variant
  (serves response)      (computes, but
     |                    response is
     v                    logged, not
  response to caller      returned)
                              |
                              v
                        comparison log
```

## 7. Dynamics

A portion of inference requests going to the production variant is
replicated to the shadow variant, per AWS's own wording, and the shadow
variant's response is logged for comparison rather than returned to the
caller. What happens to that logged data afterward is left undocumented in
every source checked for this entry, no fetched page describes a batch
comparison job, a real-time diffing engine, or a named comparison metric,
which is a genuine gap in the public documentation of this pattern rather
than an assumption made here. Istio's mirroring mechanism, the
infrastructure-layer analog, states its replicated requests happen out of
band of the critical request path, which implies but does not explicitly
guarantee that shadow scoring does not add latency to the production
response the caller actually receives.

## 8. Implementation variants

AWS SageMaker's `ShadowProductionVariants` is the clearest, currently
documented, API-level implementation of this pattern found in this
research, distinct from its production-variant weighted A or B mechanism.
The dedicated shadow-deployment page states its purpose directly, use
SageMaker Model Shadow Deployments to create long running shadow variants
to validate any new candidate component of your model serving stack before
promoting it to production, and the configuration sets a production model,
a shadow model, and a sampling percentage per shadow.

Istio's traffic mirroring is the general, non-ML infrastructure
implementation this pattern can be built on top of at the service-mesh
layer, mirroring sends a copy of live traffic to a mirrored service, fire
and forget, with the responses discarded.

GitHub's Scientist library is the code-level, non-ML analog, wrapping an
original code path and a candidate path around the same input, always
returning the original result to the caller while comparing the two
behind the scenes. Stripe's engineering blog documents a real production
use of this exact library for a database migration, running experiments
that read from both tables and comparing the results, raising an alert on
any mismatch, a shadow-read pattern rather than a shadow-write.

Among the other major MLOps platforms checked directly for this entry,
Google Cloud's MLOps architecture guide names only canary deployment and A
or B testing for online model validation, and Databricks' current model
serving documentation contains no mention of a shadow mode on the pages
checked. Neither result should be read as proof the feature does not exist
anywhere in either vendor's documentation, only that it was not found on
the specific pages fetched for this research.

## 9. Known production uses

AWS SageMaker's `ShadowProductionVariants` feature is itself a real,
documented production capability rather than merely a pattern description,
the clearest confirmed production implementation in this research. Stripe
documents a real production use of the code-level shadow-comparison
technique, via GitHub's Scientist library, for validating a database
migration rather than a model, a genuine production use of the same
underlying idea in an adjacent domain. Uber's Michelangelo post was
checked directly for a shadow-testing mention and does not contain one,
what it documents instead is A or B testing via multiple deployed models
and held-back predictions compared against later outcomes, a related but
distinct technique, reported honestly here rather than stretched to fit.

## 10. Consequences

The benefit is structural and unambiguous, a bad candidate cannot degrade
a real user's experience, because its output never reaches them, this is
the stated purpose in every fetched source. The cost is compute doubling
for whatever fraction of traffic is sampled, evident directly from AWS's
own configuration shape, where the shadow variant is a fully separate
model deployment with its own instance type and instance count. The
sharpest limitation is informational, not operational, shadow mode can
never observe real user behavioral response to a prediction it never
shows anyone.

## 11. Failure modes and misuse

Running shadow scoring synchronously in the same request path risks
adding latency to the production response the caller actually receives,
a risk implied by Istio's own framing of mirroring as happening out of
band of the critical request path, though no fetched source states this
failure mode by name. A shadow model's output being accidentally returned
to a caller instead of only logged is a plausible, real bug class given
how the two response paths share code in most implementations, though no
fetched source documents a specific real-world incident of this kind, and
it is named here as a structural risk rather than a cited fact. Treating
agreement between a shadow model and the production model as sufficient
evidence to promote is a form of false confidence, since agreement on
logged predictions says nothing about how real users would have responded
to the candidate's actual output, the same structural gap the pattern
exists inside.

## 12. Trade-off matrix

| Strategy | Real-user exposure | What it measures |
|---|---|---|
| Shadow deployment | None, responses are logged, never returned to the caller | Model agreement or divergence on real input, no user-response signal |
| A or B testing, competing models | Partial, the routed variant's response reaches the caller | Real user behavioral response, at controlled risk to a fraction of users |
| Canary release | Partial, gradually increasing | Real production stability at controlled, escalating scale |

## 13. Related and incompatible patterns

Composes with model-registry, since a shadow deployment's candidate is a
versioned artifact that must be resolved from the registry before it can
be deployed as a shadow variant. Composes directly with online-inference,
since a shadow variant attaches to a live serving endpoint exactly as
already documented there, AWS's own model-validation page is the shared
source for both entries. Related to champion-challenger as a technique
rather than a synonym, a shadow test is commonly the specific,
zero-exposure evidence-gathering step a candidate goes through before a
formal promotion decision, while champion-challenger is the surrounding
governance process that decides when and whether to act on that evidence.
Related to training-serving-skew-guard, since comparing a shadow model's
output against the production model's output on identical real traffic is
one concrete, empirical way to surface a training-serving mismatch that a
static offline test set might miss.

## 14. Refactoring path in and out

Introducing a shadow deployment starts by replicating a small, defined
percentage of production traffic to the candidate model and logging its
output without changing anything the caller experiences. The sampling
percentage can be increased incrementally as confidence grows that the
shadow path adds no meaningful overhead to the production response.
Removing a shadow deployment, once a promotion decision is made, is safe
and simple, delete the shadow variant, since it never held any part of the
production response path to begin with.

## 15. Testing and verification

Verify that a shadow variant's output genuinely never reaches the caller,
under normal operation and under a failure of the shadow path itself, a
shadow model erroring should never surface an error to the real caller.
Verify that shadow scoring does not measurably add latency to the
production response, especially if the implementation runs the shadow
call synchronously rather than fully decoupled from the request path.
Verify the comparison data collected is actually being reviewed, since a
shadow deployment that logs data nobody reads provides no real evidence
toward a promotion decision.

## 16. Observability signals

Track the agreement or divergence rate between the shadow model's logged
predictions and the production model's actual predictions on identical
input, the core signal the pattern exists to produce. Track latency and
resource overhead added by running the shadow variant, since AWS's own
per-variant instance configuration makes this a directly measurable,
directly billed cost. Track the shadow variant's own error rate on its
replicated share of traffic, since a shadow model that is failing quietly
provides no useful comparison data at all.

## 17. Security and privacy implications

A shadow variant processes the actual replicated request payload, not a
synthetic or anonymized copy, per AWS's own wording, a portion of the
inference requests is replicated to the shadow variant. It therefore
carries the same data governance obligations as the production model it
shadows, any personal data present in a live request reaches the shadow
model exactly as it reaches production, even though the shadow model's
output is never shown to anyone. No fetched source addresses this point
explicitly, it follows structurally from the replication mechanism itself
rather than from a stated security requirement.

## 18. References

- Martin Fowler, Dark Launching, martinfowler.com bliki. https://martinfowler.com/bliki/DarkLaunching.html
- Danilo Sato, Continuous Delivery for Machine Learning, martinfowler.com. https://martinfowler.com/articles/cd4ml.html
- AWS SageMaker documentation, Validate models in production. https://docs.aws.amazon.com/sagemaker/latest/dg/model-validation.html
- AWS SageMaker documentation, Model Shadow Deployments. https://docs.aws.amazon.com/sagemaker/latest/dg/model-shadow-deployment.html
- AWS SageMaker API reference, ShadowModeConfig. https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ShadowModeConfig.html
- Istio documentation, Traffic Mirroring. https://istio.io/latest/docs/tasks/traffic-management/mirroring/
- GitHub, Scientist. https://github.com/github/scientist
- Stripe Engineering, Online migrations at scale. https://stripe.com/blog/online-migrations

## Code

```typescript
interface Prediction {
  score: number;
}

type PredictFn = (payload: unknown) => Prediction;

interface ComparisonLogEntry {
  requestId: string;
  productionScore: number;
  shadowScore: number;
}

class ShadowRouter {
  private log: ComparisonLogEntry[] = [];

  constructor(
    private readonly production: PredictFn,
    private readonly shadow: PredictFn,
    private readonly samplingPercentage: number
  ) {}

  private shouldSample(): boolean {
    return Math.random() * 100 < this.samplingPercentage;
  }

  handleRequest(payload: unknown, requestId: string): Prediction {
    const result = this.production(payload);
    if (this.shouldSample()) {
      try {
        const shadowResult = this.shadow(payload);
        this.log.push({
          requestId,
          productionScore: result.score,
          shadowScore: shadowResult.score,
        });
      } catch {
        // A shadow failure never affects the caller's response.
      }
    }
    return result;
  }

  getComparisonLog(): ReadonlyArray<ComparisonLogEntry> {
    return this.log;
  }
}
```

```python
import random
from dataclasses import dataclass
from typing import Callable


@dataclass
class Prediction:
    score: float


PredictFn = Callable[[object], Prediction]


@dataclass
class ComparisonLogEntry:
    request_id: str
    production_score: float
    shadow_score: float


class ShadowRouter:
    def __init__(
        self,
        production: PredictFn,
        shadow: PredictFn,
        sampling_percentage: float,
    ) -> None:
        self._production = production
        self._shadow = shadow
        self._sampling_percentage = sampling_percentage
        self._log: list[ComparisonLogEntry] = []

    def _should_sample(self) -> bool:
        return random.uniform(0, 100) < self._sampling_percentage

    def handle_request(self, payload: object, request_id: str) -> Prediction:
        result = self._production(payload)
        if self._should_sample():
            try:
                shadow_result = self._shadow(payload)
                self._log.append(
                    ComparisonLogEntry(request_id, result.score, shadow_result.score)
                )
            except Exception:
                pass  # A shadow failure never affects the caller's response.
        return result

    def comparison_log(self) -> list[ComparisonLogEntry]:
        return self._log
```

```go
package shadow

import "math/rand"

type Prediction struct {
	Score float64
}

type PredictFunc func(payload interface{}) Prediction

type ComparisonLogEntry struct {
	RequestID       string
	ProductionScore float64
	ShadowScore     float64
}

type ShadowRouter struct {
	production         PredictFunc
	shadow             PredictFunc
	samplingPercentage float64
	log                []ComparisonLogEntry
}

func NewShadowRouter(production, shadow PredictFunc, samplingPercentage float64) *ShadowRouter {
	return &ShadowRouter{
		production:         production,
		shadow:             shadow,
		samplingPercentage: samplingPercentage,
	}
}

func (r *ShadowRouter) shouldSample() bool {
	return rand.Float64()*100 < r.samplingPercentage
}

func (r *ShadowRouter) HandleRequest(payload interface{}, requestID string) Prediction {
	result := r.production(payload)
	if r.shouldSample() {
		shadowResult := r.shadow(payload)
		r.log = append(r.log, ComparisonLogEntry{
			RequestID:       requestID,
			ProductionScore: result.Score,
			ShadowScore:     shadowResult.Score,
		})
	}
	return result
}

func (r *ShadowRouter) ComparisonLog() []ComparisonLogEntry {
	return r.log
}
```
