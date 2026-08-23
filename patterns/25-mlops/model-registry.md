---
name: Model Registry
slug: model-registry
family: 25-mlops
category: MLOps
aliases: [ML Model Registry, Model Repository]
first_described: "Del Balso and Hermann, Meet Michelangelo, Uber Engineering, 2017"
maturity: established
related: [feature-store, training-serving-skew-guard, champion-challenger, batch-inference, online-inference]
incompatible_with: []
verified: 2026-08-23
---

# Model Registry

## 1. Name, aliases, and lineage

A model registry is a versioned, centralized store for trained machine
learning model artifacts and the metadata describing each version, so a
model can be found, compared, promoted between environments, and rolled
back, independent of the training run that produced it and the serving
system that consumes it.

Uber Michelangelo, described in Meet Michelangelo, Uber's Machine
Learning Platform, Mike Del Balso and Jeremy Hermann, Uber Engineering,
September 5, 2017, is the earliest well documented production system
covering this ground, ahead of any dedicated open source registry project.
The post describes a model repository storing a copy of the learned
parameters, feature information, training dataset information, evaluation
metrics, and arbitrary metadata, each with a unique ID that should always
be traceable back to its original training run, training data set, and full
model configuration, a striking early use of the word alias for a stable
name a specific model version can be promoted under.

MLflow, the dominant open source implementation today, added a dedicated
Model Registry component considerably later than MLflow itself. MLflow's
own release history shows Model Registry entering as a preview feature in
version 1.4.0, October 2019, and reaching general availability in
version 1.7.0, March 2020.

## 2. Problem and context

A model that exists only as a file on someone's laptop, or an artifact
saved into a training run's own log directory, has no independent identity.
Nothing distinguishes the tenth retraining of a model from the ninth except
memory, nobody can say with confidence which specific version is currently
serving traffic, and rolling back after a bad deploy means finding the right
file by hand under time pressure. A registry gives every trained version a
stable, queryable identity, separate from the ephemeral run that created it,
so promotion, rollback, and audit become deliberate operations against a
record rather than archaeology against a filesystem.

## 3. Forces

- Reproducibility pulls toward capturing everything about how a version was
  produced, the exact training data, code commit, hyperparameters, and
  environment, alongside the artifact itself, but capturing too much
  metadata for every version imposes real storage and process overhead.
- Serving systems want a small, stable set of names to depend on, such as
  the production model, while data scientists want to register many
  experimental versions freely without polluting that stable namespace.
- Governance wants every promotion gated by an approval step, while rapid
  iteration wants a version promotable the moment it beats a benchmark.
- A registry can be a thin metadata layer pointing at artifacts stored
  elsewhere, or the artifact store itself, and that choice changes both the
  registry's own availability requirements and its coupling to the object
  store or database backing it.

## 4. Applicability and non-applicability

Applies once more than one trained version of a model exists at any point in
its life, once a serving system needs to resolve the current model to a
specific artifact without a human editing a path by hand, or once an
organization needs to answer, after the fact, exactly which version served a
given prediction. Does not help, and adds pure overhead, for a single
notebook-trained model that is manually copied once and never revisited, or
for a research setting where no version is ever deployed to serve real
traffic.

## 5. Structure

Every registry, regardless of implementation, separates three concerns. A
logical model name groups every version of a conceptually single model. A
version is an immutable, numbered or hashed reference to one specific
trained artifact plus its metadata, never mutated after creation. A stage or
alias is a mutable pointer, held against exactly one version at a time
per name, that a serving system resolves at load time, so promoting a
version is repointing a name rather than moving or copying a file.

## 6. ASCII structure diagram

```
  training run
       |
       v
  +-----------+        +--------------------+
  | artifact  |------->| model registry     |
  | (weights, |        |                    |
  |  code,    |        |  name: fraud-model |
  |  params)  |        |   v1  v2  v3 (new) |
  +-----------+        |            ^       |
                        |  alias:champion----+
                        +--------------------+
                                   |
                                   v
                        serving system resolves
                        name + alias -> version
```

## 7. Dynamics

A training run completes and registers a new version under a logical model
name, recording the run's identifying metadata and a pointer to the
artifact's storage location. A human or an automated evaluation gate then
repoints an alias, such as champion, from the previously promoted version to
the new one. A serving process, at load time or on a polling interval,
resolves the name plus alias pair to a concrete version and fetches that
version's artifact. Rolling back is the identical operation run in reverse,
repointing the alias back to the prior version, with no retraining and no
artifact movement required.

## 8. Implementation variants

MLflow's current documentation has fully replaced its earlier Stage based
model, None, Staging, Production, Archived, with aliases and tags. MLflow's
docs give the direct example of setting an alias, champion, on a specific
version, and instruct serving code to load it by that alias rather than by a
stage name. MLflow's own version 2.13.0 documentation, the last version
pinned copy where Stages still appear, itself carries the deprecation
notice, confirming Stages are removed from MLflow's current, unversioned
docs entirely.

AWS SageMaker's Model Registry organizes versions inside a `Model Package
Group`, with each version, a `Model Package`, carrying an
`ApprovalStatus` enum. SageMaker's documentation describes a model package's
approval status transition as the trigger an organization can use to kick
off downstream deployment automation, tying the registry directly into a
CI or CD pipeline.

Databricks ran its own pre-Unity-Catalog registry, now explicitly labeled
Workspace Model Registry (legacy) on Databricks' current documentation,
which describes a hard cutover, new workspaces created on or after
April 2024 default to Unity Catalog for model registration, with the older
workspace-scoped registry retained only for backward compatibility on
existing workspaces.

Google renamed its Vertex AI product line to Gemini Enterprise Agent Platform in an October 2025 announcement, per Google Cloud CEO Thomas Kurian, though this session could not retrieve a stable, live-reachable citation for the specific Model Registry product page under its new name, so the rename is noted here without a citation rather than asserted against a broken link.

Weights and Biases' dedicated Model Registry documentation path now returns
a not-found response, superseded by a broader W&B Registry spanning both
models and datasets under one product. No explicit deprecation notice for
the old Model Registry naming could be found live, so this consolidation is
inferred from the redirect and the current docs' framing, not confirmed by
a direct statement, and is presented here as such.

## 9. Known production uses

Uber's Michelangelo, described directly above, is the earliest well
documented production deployment of this pattern, predating MLflow's own
Model Registry component by roughly two years. MLflow's own current
documentation lists a broad adopter set directly, naming, among others,
Databricks, Microsoft, Meta, MosaicML, Zillow, Toyota Motor Corporation,
Booking.com, Wix, Accenture, and ASML as organizations reporting production
MLflow usage.

## 10. Consequences

A registry turns which model is live into a queryable fact rather than a
matter of institutional memory, and turns rollback into a metadata update
instead of a redeploy. It adds an operational dependency, however, since
serving now depends on the registry's own availability at load time unless
the resolved artifact is cached locally, and it adds a small but real
process cost, since every version now needs an intentional registration
step rather than simply existing as a file.

## 11. Failure modes and misuse

Treating registration as optional for experimental runs erodes the
registry's value quickly, since a serving system asked to resolve an alias
that was never repointed after a bad promotion will happily keep serving a
known-bad version indefinitely. Conflating the registry with the artifact
store itself, rather than treating it as metadata pointing at artifacts held
in dedicated storage, couples the registry's own uptime and backup strategy
to every model's raw weights, often unnecessarily. Skipping the approval
gate a registry like SageMaker's ApprovalStatus is built to enforce, by
promoting versions programmatically without human or automated evaluation
review, defeats the governance the pattern exists to provide.

## 12. Trade-off matrix

| Approach | Governance | Rollback speed | Operational coupling |
|---|---|---|---|
| File on disk, manual copy | None | Slow, manual | None |
| Registry, stage-based (legacy MLflow) | Fixed lifecycle names | Fast | Low |
| Registry, alias-based (current MLflow) | Flexible, multiple named pointers | Fast | Low |
| Registry, approval-gated (SageMaker) | Enforced status transitions | Fast | Medium, tied to pipeline |

## 13. Related and incompatible patterns

Directly composes with feature-store, since a served model version and the
feature values it was trained against are two halves of the same
reproducibility problem, tracked by two adjacent but distinct stores.
Composes with champion-challenger, since MLflow's own documented alias
example uses the literal name champion, making the alias mechanism a
direct, sourced implementation vehicle for that pattern. Related to
batch-inference and online-inference, both of which resolve a model version
from the registry at the point they load a model to serve predictions. Not
incompatible with any pattern in this family, a registry is additive
infrastructure rather than a competing approach. The repository's duplicate detector also flags a naming collision against the pre-existing enterprise-architecture Registry pattern, patterns/06-enterprise-application-architecture/registry.md; that pattern is a general object lookup mechanism unrelated to ML model versioning, so no merge or rename is warranted, and this note records the check rather than resolving it silently.

## 14. Refactoring path in and out

Introducing a registry into an existing system starts by wrapping the
current manual artifact-copy step with a registration call that captures
the same artifact plus its metadata, without yet changing how serving loads
a model. Serving code is then migrated to resolve a name and alias against
the registry instead of a hardcoded file path, one serving path at a time.
Removing a registry, rare in practice, means pinning every consumer to the
last resolved concrete version paths directly, freezing the system at its
current state before decommissioning the registry.

## 15. Testing and verification

Verify that registering a new version never silently overwrites a prior
version's immutable record. Verify that repointing an alias is atomic from
a resolving consumer's perspective, no window where the alias resolves to
neither the old nor the new version. Verify that rollback, repointing the
alias back to the previous version, is exercised in a drill rather than
assumed to work the first time it is needed for real.

## 16. Observability signals

Track which concrete version each alias currently resolves to, and alert on
an unexpected change. Track the age of the version currently serving under
each alias, since a version that has not been challenged in a long time is
a governance signal worth surfacing on its own. Track registration events
themselves, since a training pipeline that silently stops registering new
versions is a common, quiet failure mode.

## 17. Security and privacy implications

A model registry is a natural place for role-based access control, since
the ability to repoint a production alias is effectively the ability to
change what a live system serves. Model artifacts can themselves memorize
and leak training data under certain attacks, so registry access controls
should be treated with a similar seriousness to the training data access
controls that produced the artifact, not as a lesser concern.

## 18. References

- Mike Del Balso and Jeremy Hermann, Meet Michelangelo, Uber's Machine Learning Platform, Uber Engineering, September 5, 2017. https://www.uber.com/blog/michelangelo-machine-learning-platform/
- MLflow documentation, Model Registry, current. https://mlflow.org/docs/latest/ml/model-registry/
- MLflow documentation, version 2.13.0, Model Registry (Stages, deprecated). https://mlflow.org/docs/2.13.0/model-registry.html
- AWS SageMaker documentation, Model Registry. https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html
- Databricks documentation, Workspace Model Registry (legacy). https://docs.databricks.com/aws/en/mlflow/model-registry

## Code

```typescript
type Alias = "champion" | "challenger";

interface ModelVersion {
  name: string;
  version: number;
  artifactUri: string;
  createdAt: string;
}

class ModelRegistry {
  private versions: Map<string, ModelVersion[]> = new Map();
  private aliases: Map<string, Map<Alias, number>> = new Map();

  registerVersion(name: string, artifactUri: string): ModelVersion {
    const existing = this.versions.get(name) ?? [];
    const nextVersion = existing.length + 1;
    const mv: ModelVersion = {
      name,
      version: nextVersion,
      artifactUri,
      createdAt: new Date().toISOString(),
    };
    existing.push(mv);
    this.versions.set(name, existing);
    return mv;
  }

  setAlias(name: string, alias: Alias, version: number): void {
    const all = this.versions.get(name) ?? [];
    const found = all.find((v) => v.version === version);
    if (!found) {
      throw new Error("version not found for name " + name);
    }
    const nameAliases = this.aliases.get(name) ?? new Map<Alias, number>();
    nameAliases.set(alias, version);
    this.aliases.set(name, nameAliases);
  }

  resolve(name: string, alias: Alias): ModelVersion {
    const nameAliases = this.aliases.get(name);
    const version = nameAliases?.get(alias);
    if (version === undefined) {
      throw new Error("alias not set for name " + name);
    }
    const all = this.versions.get(name) ?? [];
    const found = all.find((v) => v.version === version);
    if (!found) {
      throw new Error("resolved version missing artifact record");
    }
    return found;
  }
}
```

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ModelVersion:
    name: str
    version: int
    artifact_uri: str
    created_at: str


class ModelRegistry:
    def __init__(self) -> None:
        self._versions: dict[str, list[ModelVersion]] = {}
        self._aliases: dict[str, dict[str, int]] = {}

    def register_version(self, name: str, artifact_uri: str) -> ModelVersion:
        existing = self._versions.setdefault(name, [])
        next_version = len(existing) + 1
        mv = ModelVersion(
            name=name,
            version=next_version,
            artifact_uri=artifact_uri,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        existing.append(mv)
        return mv

    def set_alias(self, name: str, alias: str, version: int) -> None:
        candidates = self._versions.get(name, [])
        if not any(v.version == version for v in candidates):
            raise ValueError(f"version not found for name {name}")
        self._aliases.setdefault(name, {})[alias] = version

    def resolve(self, name: str, alias: str) -> ModelVersion:
        version = self._aliases.get(name, {}).get(alias)
        if version is None:
            raise ValueError(f"alias not set for name {name}")
        for mv in self._versions.get(name, []):
            if mv.version == version:
                return mv
        raise ValueError("resolved version missing artifact record")
```

```go
package registry

import (
	"errors"
	"fmt"
	"time"
)

type ModelVersion struct {
	Name        string
	Version     int
	ArtifactURI string
	CreatedAt   time.Time
}

type ModelRegistry struct {
	versions map[string][]ModelVersion
	aliases  map[string]map[string]int
}

func NewModelRegistry() *ModelRegistry {
	return &ModelRegistry{
		versions: make(map[string][]ModelVersion),
		aliases:  make(map[string]map[string]int),
	}
}

func (r *ModelRegistry) RegisterVersion(name, artifactURI string) ModelVersion {
	existing := r.versions[name]
	next := len(existing) + 1
	mv := ModelVersion{
		Name:        name,
		Version:     next,
		ArtifactURI: artifactURI,
		CreatedAt:   time.Now().UTC(),
	}
	r.versions[name] = append(existing, mv)
	return mv
}

func (r *ModelRegistry) SetAlias(name, alias string, version int) error {
	found := false
	for _, mv := range r.versions[name] {
		if mv.Version == version {
			found = true
			break
		}
	}
	if !found {
		return fmt.Errorf("version not found for name %s", name)
	}
	if r.aliases[name] == nil {
		r.aliases[name] = make(map[string]int)
	}
	r.aliases[name][alias] = version
	return nil
}

func (r *ModelRegistry) Resolve(name, alias string) (ModelVersion, error) {
	version, ok := r.aliases[name][alias]
	if !ok {
		return ModelVersion{}, errors.New("alias not set for name " + name)
	}
	for _, mv := range r.versions[name] {
		if mv.Version == version {
			return mv, nil
		}
	}
	return ModelVersion{}, errors.New("resolved version missing artifact record")
}
```
