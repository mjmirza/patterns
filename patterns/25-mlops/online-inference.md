---
name: Online Inference
slug: online-inference
family: 25-mlops
category: MLOps
aliases: [Real-Time Inference, Real-Time Serving, Real-Time Model Serving]
first_described: "Common industry practice, formalized in AWS SageMaker real-time endpoints, 2018"
maturity: established
related: [model-registry, feature-store, batch-inference, shadow-model]
incompatible_with: []
verified: 2026-08-23
---

# Online Inference

## 1. Name, aliases, and lineage

Online inference, also called real-time inference or real-time serving,
runs a trained model as a persistent, request-answering process that
returns a prediction to a caller waiting synchronously on the response,
the direct counterpart to batch-inference in this same family.

The pattern is convergent industry practice with no single canonical
academic origin. AWS's SageMaker real-time inference endpoint
documentation is a well-documented, current, managed formalization,
stating plainly, real-time inference is ideal for inference workloads where
you have real-time, interactive, low latency requirements. You can deploy
your model to SageMaker AI hosting services and get an endpoint that can be
used for inference. These endpoints are fully managed and support
autoscaling.

Uber's Michelangelo, already cited in this family for its feature store and
model registry components, gives one of the plainest descriptions of the
structural pattern found in this research, the model is deployed to an
online prediction service cluster, generally containing hundreds of
machines behind a load balancer.

## 2. Problem and context

A user or a system is synchronously blocked waiting on a prediction, a
fraud check on a payment, a ranking call in a search or feed, a
recommendation on a product page, a chatbot turn, and needs an answer
inside a tight latency budget, milliseconds to low seconds, before it can
proceed. This is the direct structural opposite of a nightly job scoring
millions of rows with no one waiting, the caller is present, in the loop,
and a late answer risks timeout or abandonment.

## 3. Forces

- Latency versus cost. A real-time endpoint is provisioned and typically
  always-on so it can answer in milliseconds, but that capacity is paid for
  whether or not requests are currently arriving.
- Model size versus response time. A heavier model directly threatens a
  latency service level agreement, and serverless variants document this
  tension directly, memory tiers are chosen according to model size and
  benchmarked against a latency target.
- Horizontal scaling versus cold start. Auto scaling reacts to changing
  load, but reaction time is not instant, so a sudden traffic spike can
  degrade latency before new capacity comes online, and a variant that
  scales down to zero when idle documents a real cold-start cost as the
  price of that savings.

## 4. Applicability and non-applicability

Applies when a caller is synchronously waiting on a result and traffic is
frequent or steady enough that continuous provisioned capacity, or an
acceptable cold start, is tolerable, and payloads are small enough for a
synchronous request and response cycle. Does not apply when there is no
synchronous caller, a nightly scoring run over a whole customer table is
batch-inference, or when a request needs more time or data than a
synchronous cycle affords, where an asynchronous, queue-based option is the
documented middle ground instead.

## 5. Structure

A persistent or auto-scaled serving process holds a loaded model in
memory, fronted by a request and response API, typically HTTP or gRPC,
load balanced across multiple instances. TensorFlow Serving formalizes
this into named components, servables are the underlying objects clients
use to perform computation, loaders manage a servable's lifecycle and
standardize loading and unloading it, sources are plugin modules that find
and provide servables from arbitrary storage systems, and managers handle
the full lifecycle of servables and give clients a simple interface to
access a loaded one.

## 6. ASCII structure diagram

```
  request
     |
     v
  +----------------+
  | load balancer  |
  +----------------+
     |        |        |
     v        v        v
  worker 1  worker 2  worker N
  (model    (model    (model
   loaded)   loaded)   loaded)
     |        |        |
     +---> response returned
```

## 7. Dynamics

A request arrives and is routed by a load balancer to a warm worker
holding the loaded model. The model executes its forward pass in process
and a response is returned, typically within a tight service level
agreement. TensorFlow Serving's dynamics are versioned rather than
single-shot, a source creates a loader for a specific version, the source
notifies a manager of the aspired version, the manager applies a configured
version policy, and if safe gives the loader resources to load the new
version, so a running online-inference service can hot-swap model versions
without downtime. Uber's Michelangelo traces this concretely, raw features
arrive from the client service, pass through compiled expressions for
transformation, additional features are fetched from the feature store if
needed, the final feature vector is scored by the model, and predictions
are returned over the network.

## 8. Implementation variants

AWS SageMaker real-time endpoints are fully managed with autoscaling and
per-instance, per-container, and per-GPU CloudWatch metrics, and multiple
model variants can share one endpoint, including a shadow variant whose
responses are logged for comparison and never returned to the caller, a
documented way to validate a new model's performance without exposing
callers to it. SageMaker Serverless Inference trades latency for cost,
scaling an endpoint to zero when idle, with memory tiers from 1024 to 6144
megabytes and a documented cold-start behavior mitigated by provisioned
concurrency, which keeps an endpoint warm and ready to respond in
milliseconds for a chosen concurrency count. AWS names four deployment
shapes side by side, real-time, serverless, asynchronous, and batch
transform, positioning asynchronous inference explicitly as a queued,
near-real-time hybrid for large payloads, up to one gigabyte, and long
processing times, up to one hour, that still needs an eventual per-request
response.

Google's real-time prediction product now surfaces under the same Gemini
Enterprise Agent Platform rename already confirmed for its Model Registry
and Feature Store products. This session confirmed the rename live on the
current page's own title and, unlike the prior two products, the body
prose itself loaded successfully rather than being client rendered,
describing deployment to endpoints via a public endpoint, a dedicated
public endpoint, or a private endpoint through Private Service Connect,
which Google's documentation recommends. No latency figures were present
on that specific page.

TensorFlow Serving provides out-of-the-box integration with TensorFlow
models and can be extended to serve other model types, with a gRPC C plus
plus server API and a REST client API. NVIDIA Triton Inference Server
supports multiple frameworks, TensorRT, PyTorch, ONNX, and more, and
implements dynamic batching, sequence batching, and concurrent model
execution to raise throughput while still serving low-latency requests,
exposed over HTTP, gRPC, and embeddable C and Java APIs. KServe formalizes
serving on Kubernetes into a control plane managing model lifecycle,
revision tracking, canary rollouts, and A or B testing, and a data plane
providing a standardized inference protocol, with the InferenceService
resource giving automatic scaling, networking, and health checks.
Databricks Model Serving deploys a model as a REST API on serverless
compute that automatically scales to meet demand, distinct from the batch
path, AI Functions and its ai_query and mlflow.pyfunc.spark_udf mechanisms,
already documented in the sibling batch-inference entry.

## 9. Known production uses

Uber's Michelangelo is the strongest documented named production
deployment of this pattern found in this research, with concrete,
sourced numbers, a P95 latency under 5 milliseconds without a feature
store lookup, rising to under 10 milliseconds when a Cassandra-backed
feature store lookup is required, and a highest-traffic model serving more
than 250,000 predictions per second, achieved simply by adding more hosts
to the prediction service cluster behind the load balancer. Multiple model
versions run in the same serving container simultaneously in that system,
referenced by identifier or tag, enabling safe transitions and A or B
testing. No other named production deployment beyond the vendor platforms
themselves was independently confirmed in this session.

## 10. Consequences

Online inference gives low, predictable per-request latency, evidenced
concretely by Michelangelo's sub-10 millisecond P95 figure, at the cost of
continuous infrastructure spend even when idle, the direct inverse of
batch inference's ephemeral job cost model. Both alternative deployment
shapes, serverless and asynchronous, market scaling to zero as their
headline cost benefit, which only makes sense as a differentiator if the
always-on real-time baseline does not itself scale to zero, a reasoned
inference from that contrast rather than a single sentence stating it
directly.

## 11. Failure modes and misuse

Cold starts are a documented, real failure mode for any variant that
scales down when idle, it can take time to spin up compute resources when
requests suddenly resume, and this worsens further if concurrent requests
exceed current usage. Insufficient auto-scaling headroom under a load spike
is a real, acknowledged risk, which is exactly why load testing an auto
scaling configuration is a documented required practice rather than an
afterthought. Serving a stale model version silently is the specific risk
the versioning machinery in TensorFlow Serving and the shadow-variant
mechanism in SageMaker both exist to prevent, promoting an unvalidated
model straight into production traffic is the failure both are built
against.

## 12. Trade-off matrix

| Deployment mode | Latency | Cost model | Cold start |
|---|---|---|---|
| Online inference, real-time endpoint | Milliseconds, interactive | Continuous provisioned capacity | Minimal in steady state, auto-scaling lag under a spike |
| Serverless inference | Millisecond scale once warm, degraded during a cold start | Pay per use, scales to zero | Explicit, documented, mitigated by provisioned concurrency |
| Asynchronous inference | Near real time, queued rather than blocking | Scales to zero when idle | Not blocking in the same sense, queue based |
| Batch inference (sibling pattern) | Not latency bound, an offline job | Ephemeral compute for the job's duration | Not applicable |

## 13. Related and incompatible patterns

Composes directly with model-registry, since a real-time server resolves
which model version to load from the registry at startup or on a hot swap,
and TensorFlow Serving's source and loader mechanism is exactly this
consumer relationship in miniature. Composes with feature-store,
specifically its online store half, since online-inference is the direct
consumer of that store, and Michelangelo's own latency figures separate
cleanly along this exact seam, under 5 milliseconds without a feature
store lookup and under 10 milliseconds with one. Directly paired with
batch-inference as the sibling deployment mode, both captured side by side
in AWS's own four-way deployment taxonomy, and Databricks explicitly frames
its batch and real-time paths as tightly integrated but distinct. Related
to shadow-model, since a new model version commonly runs in shadow behind
a live real-time endpoint before full promotion, a real, current,
vendor-supported feature in SageMaker rather than a hypothetical technique.

## 14. Refactoring path in and out

Introducing online inference where predictions were previously computed by
batch means standing up a low-latency endpoint that loads the same model
artifact, keeping the batch job running in parallel as a fallback path
while the endpoint's correctness is validated, ideally by comparing its
output against the batch job's own known results. Migrating between
serving frameworks, for example from a hand-rolled server to TensorFlow
Serving or Triton, is safest done behind the same load balancer, cutting
traffic over incrementally rather than all at once. Removing an online
endpoint entirely means confirming every synchronous caller has migrated
to an accepted alternative, batch, asynchronous, or a different service,
before decommissioning it.

## 15. Testing and verification

Verify a candidate model version against real traffic before promoting it,
using a shadow variant whose responses are logged for comparison and never
returned to the caller, the strongest available pre-promotion check since
it uses genuine live traffic rather than a static validation set. Verify
auto-scaling configuration under actual load testing, since a documented
best practice names this directly as the way to catch an under-provisioned
scaling policy before it causes a real latency incident. Verify that a
version hot-swap leaves no window where a request could resolve to neither
the old nor the new version.

## 16. Observability signals

Track per-instance, per-container, and where applicable per-accelerator
utilization and latency metrics, the enhanced metrics dimensions SageMaker
documents for exactly this purpose. Track request latency at meaningful
percentiles, not only the average, since Michelangelo's own reported
figures are given as P95, not a mean, reflecting that the tail is what
actually threatens a service level agreement. Track which model version is
currently serving on each worker, so a stale-version incident can be
diagnosed immediately rather than discovered from a downstream symptom.

## 17. Security and privacy implications

An always-on real-time endpoint is a persistent, continuously reachable
network surface, in contrast to an ephemeral batch job that exists only
for the duration of its run, a reasoned architectural inference from the
always-provisioned versus scales-to-zero framing throughout this pattern's
sourcing rather than a sentence any fetched source states in exactly those
security terms. A serving endpoint that returns a prediction derived from
personal data is itself handling sensitive output, a computed risk or
recommendation score, and should be governed with the same care as the
input data it was derived from.

## 18. References

- AWS SageMaker documentation, Real-time inference. https://docs.aws.amazon.com/sagemaker/latest/dg/realtime-endpoints.html
- AWS SageMaker documentation, Deploy models for inference. https://docs.aws.amazon.com/sagemaker/latest/dg/deploy-model.html
- AWS SageMaker documentation, Serverless Inference. https://docs.aws.amazon.com/sagemaker/latest/dg/serverless-endpoints.html
- AWS SageMaker documentation, Endpoint auto scaling. https://docs.aws.amazon.com/sagemaker/latest/dg/endpoint-auto-scaling.html
- AWS SageMaker documentation, Model validation and shadow variants. https://docs.aws.amazon.com/sagemaker/latest/dg/model-validation.html
- Mike Del Balso and Jeremy Hermann, Meet Michelangelo, Uber's Machine Learning Platform, Uber Engineering. https://www.uber.com/en-DE/blog/michelangelo-machine-learning-platform/
- TensorFlow Serving architecture overview. https://www.tensorflow.org/tfx/serving/architecture
- NVIDIA Triton Inference Server documentation. https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/index.html
- KServe documentation. https://kserve.github.io/website/
- Databricks documentation, Model Serving. https://docs.databricks.com/en/machine-learning/model-serving/index.html

## Code

```typescript
interface LoadedModel {
  version: number;
  predict(payload: unknown): number;
}

class OnlineInferenceServer {
  private current: LoadedModel | null = null;
  private shadow: LoadedModel | null = null;
  private shadowLog: Array<{ inputHash: string; shadowScore: number }> = [];

  loadModel(model: LoadedModel): void {
    this.current = model;
  }

  setShadow(model: LoadedModel | null): void {
    this.shadow = model;
  }

  handleRequest(payload: unknown, inputHash: string): number {
    if (!this.current) {
      throw new Error("no model loaded");
    }
    const score = this.current.predict(payload);
    if (this.shadow) {
      const shadowScore = this.shadow.predict(payload);
      this.shadowLog.push({ inputHash, shadowScore });
    }
    return score;
  }

  getShadowLog(): ReadonlyArray<{ inputHash: string; shadowScore: number }> {
    return this.shadowLog;
  }
}
```

```python
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class LoadedModel:
    version: int
    predict: Callable[[object], float]


@dataclass
class ShadowLogEntry:
    input_hash: str
    shadow_score: float


class OnlineInferenceServer:
    def __init__(self) -> None:
        self._current: Optional[LoadedModel] = None
        self._shadow: Optional[LoadedModel] = None
        self._shadow_log: list[ShadowLogEntry] = []

    def load_model(self, model: LoadedModel) -> None:
        self._current = model

    def set_shadow(self, model: Optional[LoadedModel]) -> None:
        self._shadow = model

    def handle_request(self, payload: object, input_hash: str) -> float:
        if self._current is None:
            raise RuntimeError("no model loaded")
        score = self._current.predict(payload)
        if self._shadow is not None:
            shadow_score = self._shadow.predict(payload)
            self._shadow_log.append(ShadowLogEntry(input_hash, shadow_score))
        return score

    def shadow_log(self) -> list[ShadowLogEntry]:
        return self._shadow_log
```

```go
package online

import "errors"

type PredictFunc func(payload interface{}) float64

type LoadedModel struct {
	Version int
	Predict PredictFunc
}

type ShadowLogEntry struct {
	InputHash   string
	ShadowScore float64
}

type OnlineInferenceServer struct {
	current   *LoadedModel
	shadow    *LoadedModel
	shadowLog []ShadowLogEntry
}

func (s *OnlineInferenceServer) LoadModel(model *LoadedModel) {
	s.current = model
}

func (s *OnlineInferenceServer) SetShadow(model *LoadedModel) {
	s.shadow = model
}

func (s *OnlineInferenceServer) HandleRequest(payload interface{}, inputHash string) (float64, error) {
	if s.current == nil {
		return 0, errors.New("no model loaded")
	}
	score := s.current.Predict(payload)
	if s.shadow != nil {
		shadowScore := s.shadow.Predict(payload)
		s.shadowLog = append(s.shadowLog, ShadowLogEntry{InputHash: inputHash, ShadowScore: shadowScore})
	}
	return score, nil
}

func (s *OnlineInferenceServer) ShadowLog() []ShadowLogEntry {
	return s.shadowLog
}
```
