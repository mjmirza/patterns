---
name: Champion-Challenger
slug: champion-challenger
family: 25-mlops
category: MLOps
aliases: [Champion Challenger, Challenger Model]
first_described: "MLflow Model Registry alias documentation, current"
maturity: emerging
related: [model-registry, shadow-model, online-inference, model-monitoring]
incompatible_with: []
verified: 2026-08-23
---

# Champion-Challenger

## 1. Name, aliases, and lineage

Champion-challenger names a governance process, one currently-serving
champion model is held up against one or more candidate challenger
versions using real production evidence, with a defined, repeatable
mechanism for reassigning the champion designation when a challenger
proves superior.

The term is widely reputed to originate outside machine learning
entirely, in credit-risk scoring and direct-marketing model management at
banks and insurers, well before MLOps vendors adopted it. That pre-ML,
credit-scoring lineage could not be confirmed live in this research,
repeated attempts to fetch a SAS, FICO, or IBM source discussing it
returned not-found or forbidden responses, and no working alternative
source was located. It is reported here as reputed rather than sourced,
an honest gap rather than an invented citation.

What is directly, currently confirmed is MLflow's own Model Registry
documentation, which gives champion as its literal, first-class alias
example, you can create an alias named champion that points to version 1
of a model named MyModel, and you can then refer to version 1 of MyModel
by using the URI models colon slash slash MyModel at champion. MLflow's
docs use champion as the example name but do not themselves document a
paired challenger alias, nor any promotion criteria, that governance
layer is what this pattern names.

## 2. Problem and context

A single promotion decision, is this new model good enough to replace the
old one, is a one-time event. The problem champion-challenger addresses is
different, is the model currently deployed still the best one available,
asked repeatedly, over time, as new candidates keep arriving. AWS
SageMaker's own worked example for its A or B mechanism makes the
repeatable nature explicit, after one variant wins and the loser is
deleted, you can continue testing new models in production by adding new
variants to your endpoint and following the same steps again, the same
cycle re-run indefinitely rather than a single event.

## 3. Forces

- A durable, named role, the champion, versus a transient comparison
  round. MLflow's alias is a persistent pointer that outlives any single
  promotion decision, while AWS's documented A or B mechanism is narrated
  as a bounded round, ramp traffic, decide, delete the loser, repeat.
- Multiple simultaneous challengers versus the statistical cost of
  comparing several candidates against one baseline at once, a real,
  well-known multiple-comparisons risk that no fetched MLOps-specific
  source addresses directly, noted here as reasoning rather than citation.
- Formal, auditable governance versus the real compute cost of running
  several concurrent model deployments, each an independently instanced,
  independently billed deployment in AWS's documented shape.
- A defensible promotion record versus the absence, in every source
  checked, of any documented automatic, statistically-triggered promotion
  mechanism, every promotion decision found in this research was narrated
  as a human reading dashboards and deciding.

## 4. Applicability and non-applicability

Worth the standing governance overhead where a model's decisions must
remain defensible and auditable over time, and where more than one
candidate may reasonably compete for the champion role at once. Less
justified for a team validating a single, one-off replacement, where a
shadow test or a single bounded A or B round, per AWS's own documented
worked example, is a lighter-weight fit for a single promotion event
rather than a standing process.

## 5. Structure

One model version holds the champion designation at any time, resolved
through a stable, named pointer rather than a hardcoded reference,
MLflow's alias mechanism is the clearest documented example, `models colon
slash slash MyModel at champion` always resolves to whichever version
currently holds that alias. One or more challenger versions exist
alongside it, each gathering evidence through whichever underlying
technique is chosen, a shadow test with zero exposure, or a weighted
production-variant split with partial live exposure, AWS SageMaker
documents both as genuinely distinct mechanisms under the same
model-validation umbrella. A promotion step, reassigning the alias or
shifting traffic weight, executes the decision once evidence is judged
sufficient.

## 6. ASCII structure diagram

```
  MyModel@champion  ---> points to ---> version N (currently serving)

  challenger 1  ---> gathering evidence (shadow test or partial traffic)
  challenger 2  ---> gathering evidence (shadow test or partial traffic)

  promotion event:
  MyModel@champion  ---> repointed ---> version N+1 (the winning challenger)
```

## 7. Dynamics

MLflow's documented mechanism for changing the champion is a direct
metadata operation, reassigning the champion alias to a different model
version, which repoints any serving code that resolves the alias, with no
retraining and no artifact movement. MLflow's own docs give no criteria
for when to make that reassignment, no threshold, no automation, the
decision itself is left entirely to the operator. AWS SageMaker's
production-variant mechanism narrates the same kind of decision
concretely, a human reads per-variant CloudWatch metrics, decides a
challenger is performing better, and then executes the swap gradually
through a documented API call, shifting weight from fifty-fifty to
seventy-five twenty-five to one hundred zero, before deleting the losing
variant. Both documented mechanisms are human-gated. Neither fetched
source describes an automated, statistically-triggered promotion.

## 8. Implementation variants

MLflow implements the durable-pointer half of this pattern, a registry
metadata alias, champion, that serving code resolves by URI, with no
built-in traffic-splitting capability of its own, that part is left to
whatever infrastructure actually serves the model.

AWS SageMaker implements the traffic-splitting half as documented
infrastructure, multiple production variants behind one endpoint, each
independently instanced, with a per-variant weight adjustable through a
live API call, and CloudWatch emitting per-variant latency and invocation
metrics an operator reads to judge a challenger's performance.

The two mechanisms are not equivalent and are not interchangeable, one is
a naming and indirection layer, the other is a live traffic-routing and
compute layer, and a real champion-challenger process, as reconstructed
here from the sourced mechanics of each, most plausibly combines a durable
pointer like MLflow's with a routing or shadow mechanism like SageMaker's
underneath it, though no single fetched source documents that combination
explicitly as one named product feature.

## 9. Known production uses

No source fetched for this research names a specific company or platform
running a formally-labeled champion-challenger process. Uber's
Michelangelo post, checked directly, documents A or B testing of
competing models and held-back predictions compared against later
outcomes, a related but distinct technique, and does not describe an
ongoing, multi-model, continuously-running comparison process under that
name. The credit-scoring and banking industry association named in
popular MLOps writing could not be traced to a working, fetchable primary
source in this session, and is reported here as reputed rather than
confirmed.

## 10. Consequences

The benefit, where it applies, is a defensible, auditable trail, AWS's
CloudWatch metrics per named variant and MLflow's single, inspectable
alias record both give a clear answer to which model is authoritative and
why. The cost is compute that multiplies with every additional challenger
kept running concurrently, evident directly from AWS's own configuration
shape, where each variant is independently instanced and independently
billed. A cost no fetched source addresses is the process overhead of
agreeing a promotion threshold in advance, every worked promotion decision
found in this research was an informal human judgment call made in the
moment, not a pre-agreed formal criterion.

## 11. Failure modes and misuse

Never retiring a losing challenger is a directly costed failure mode,
since AWS's own worked example treats deleting the loser as an explicit,
necessary cleanup step, skip it and the losing variant keeps consuming
billed compute indefinitely. Comparing several simultaneous challengers
against one champion without correcting for the multiple-comparisons
problem, the well-known statistical risk that running many tests on the
same data raises the overall chance of a false positive, is a real
statistical trap, though no champion-challenger-specific source addresses
it, this connection is this entry's own reasoning bridging a general
statistical fact to the pattern's structure, not a direct citation.
Promoting a challenger on a metric that does not correlate with real
business outcome is especially dangerous in a continuous process, because
it can happen repeatedly and silently ratchet quality in the wrong
direction over many rounds.

## 12. Trade-off matrix

| Strategy | Exposure | Duration | Governance |
|---|---|---|---|
| Shadow testing | None | One candidate at a time, oriented toward a single promotion | A pre-promotion technique, not a standing process |
| A or B testing | Partial, by design | Typically bounded, ramped to completion in AWS's own worked example | Repeatable, but each round is narrated as a discrete event |
| Champion-challenger | Determined by whichever underlying technique is used | Standing, MLflow's alias persists independent of any single round | A durable, named role with a persistent promotion record |

## 13. Related and incompatible patterns

Directly implemented on top of model-registry, MLflow's champion alias is
the literal, sourced promotion mechanism, not an analogy, reassigning
which version the alias resolves to is precisely how the docs describe
updating production traffic. Related to shadow-model as a technique
rather than a synonym, a shadow test is one concrete, zero-exposure way a
challenger gathers the evidence a champion-challenger process later acts
on, the governance question of when and whether to promote sits above the
technique, not inside it. Related to online-inference, since AWS's
production-variant weighting mechanism, the traffic-splitting half of a
real implementation, attaches directly to a live serving endpoint exactly
as documented there. Related to model-monitoring, since a champion
model's degrading performance, observed through ongoing monitoring, is
plausibly what prompts a team to start evaluating a challenger in the
first place, a connective relationship inferred from the shape of the
family rather than sourced from a fetched page.

## 14. Refactoring path in and out

Introducing a formal champion-challenger process starts by giving the
currently-serving model a durable, named pointer, an alias in a registry,
rather than a hardcoded version reference, so a future promotion is a
metadata change rather than a redeploy. A traffic-splitting or shadow
mechanism is then layered underneath to let a challenger gather live
evidence without full exposure. Removing the process, reverting to a
single hardcoded model reference, is straightforward once no challenger is
active, delete the alias indirection and point serving code directly at
the current version.

## 15. Testing and verification

Verify that reassigning the champion alias is atomic from a resolving
consumer's perspective, no window where the pointer resolves to neither
the old nor the new version. Verify that a deleted, losing challenger
genuinely stops consuming compute, rather than lingering as a forgotten,
still-billed deployment. Verify the promotion criterion was actually
agreed and documented before a challenger began gathering evidence, not
decided after the fact once results are already known, which is the
surest way to avoid the false-confidence trap this entry's failure modes
describe.

## 16. Observability signals

Track each active challenger's performance delta against the champion
over time, using whichever metrics the underlying technique already
surfaces, AWS's CloudWatch emits per-variant latency and invocation counts
directly. Track the traffic-split percentage or sampling rate each
challenger currently receives, an explicit, readable configuration value
in every documented mechanism checked. Track how long each challenger has
been running without a promotion decision, since a challenger accumulating
indefinitely with no resolution is itself the failure mode this pattern's
governance exists to prevent.

## 17. Security and privacy implications

Every active challenger processes the same real production data the
champion does, per the same replication or splitting mechanism documented
for shadow-model and online-inference, and therefore carries the same
data-governance obligations as the champion, even though no
champion-challenger-specific source addresses this directly. This follows
structurally from the fact that AWS's own documented configuration creates
each challenger model with the same training-data source and execution
role as the production model, not from a stated security requirement.

## 18. References

- MLflow documentation, Model Registry. https://mlflow.org/docs/latest/ml/model-registry/
- AWS SageMaker documentation, Validate models in production. https://docs.aws.amazon.com/sagemaker/latest/dg/model-validation.html
- AWS SageMaker documentation, A or B testing for production variants. https://docs.aws.amazon.com/sagemaker/latest/dg/model-ab-testing.html
- Mike Del Balso and Jeremy Hermann, Meet Michelangelo, Uber's Machine Learning Platform, Uber Engineering. https://www.uber.com/blog/michelangelo-machine-learning-platform/
- Wikipedia, Multiple comparisons problem. https://en.wikipedia.org/wiki/Multiple_comparisons_problem

## Code

```typescript
interface ChallengerMetrics {
  slug: string;
  invocations: number;
  averageScore: number;
}

class ChampionChallengerRegistry {
  private championAlias: string;
  private challengers: Map<string, ChallengerMetrics> = new Map();

  constructor(initialChampion: string) {
    this.championAlias = initialChampion;
  }

  addChallenger(slug: string): void {
    if (slug === this.championAlias) {
      throw new Error("challenger cannot equal the current champion");
    }
    this.challengers.set(slug, { slug, invocations: 0, averageScore: 0 });
  }

  recordInvocation(slug: string, score: number): void {
    const m = this.challengers.get(slug);
    if (!m) return;
    const total = m.averageScore * m.invocations + score;
    m.invocations += 1;
    m.averageScore = total / m.invocations;
  }

  promote(slug: string): void {
    if (!this.challengers.has(slug)) {
      throw new Error("cannot promote an untracked challenger");
    }
    this.challengers.delete(slug);
    this.championAlias = slug;
  }

  getChampion(): string {
    return this.championAlias;
  }
}
```

```python
from dataclasses import dataclass


@dataclass
class ChallengerMetrics:
    slug: str
    invocations: int = 0
    average_score: float = 0.0


class ChampionChallengerRegistry:
    def __init__(self, initial_champion: str) -> None:
        self._champion_alias = initial_champion
        self._challengers: dict[str, ChallengerMetrics] = {}

    def add_challenger(self, slug: str) -> None:
        if slug == self._champion_alias:
            raise ValueError("challenger cannot equal the current champion")
        self._challengers[slug] = ChallengerMetrics(slug=slug)

    def record_invocation(self, slug: str, score: float) -> None:
        m = self._challengers.get(slug)
        if m is None:
            return
        total = m.average_score * m.invocations + score
        m.invocations += 1
        m.average_score = total / m.invocations

    def promote(self, slug: str) -> None:
        if slug not in self._challengers:
            raise ValueError("cannot promote an untracked challenger")
        del self._challengers[slug]
        self._champion_alias = slug

    def champion(self) -> str:
        return self._champion_alias
```

```go
package championchallenger

import "errors"

type ChallengerMetrics struct {
	Slug         string
	Invocations  int
	AverageScore float64
}

type Registry struct {
	championAlias string
	challengers   map[string]*ChallengerMetrics
}

func NewRegistry(initialChampion string) *Registry {
	return &Registry{
		championAlias: initialChampion,
		challengers:   make(map[string]*ChallengerMetrics),
	}
}

func (r *Registry) AddChallenger(slug string) error {
	if slug == r.championAlias {
		return errors.New("challenger cannot equal the current champion")
	}
	r.challengers[slug] = &ChallengerMetrics{Slug: slug}
	return nil
}

func (r *Registry) RecordInvocation(slug string, score float64) {
	m, ok := r.challengers[slug]
	if !ok {
		return
	}
	total := m.AverageScore*float64(m.Invocations) + score
	m.Invocations++
	m.AverageScore = total / float64(m.Invocations)
}

func (r *Registry) Promote(slug string) error {
	if _, ok := r.challengers[slug]; !ok {
		return errors.New("cannot promote an untracked challenger")
	}
	delete(r.challengers, slug)
	r.championAlias = slug
	return nil
}

func (r *Registry) Champion() string {
	return r.championAlias
}
```
