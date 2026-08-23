---
name: Batch Inference
slug: batch-inference
family: 25-mlops
category: MLOps
aliases: [Batch Prediction, Offline Inference, Batch Scoring]
first_described: "Common industry practice, formalized in AWS SageMaker Batch Transform, 2018"
maturity: established
related: [model-registry, feature-store, online-inference, shadow-model]
incompatible_with: []
verified: 2026-08-23
---

# Batch Inference

## 1. Name, aliases, and lineage

Batch inference runs a trained model against a large, bounded set of inputs
collected ahead of time, producing predictions written to storage for later
use, rather than responding to individual requests as they arrive.

The pattern predates any single named product, since running a trained
model over a Spark or Hadoop dataset offline was already common industry
practice before any vendor formalized it as a managed service. AWS
SageMaker's Batch Transform, generally available since 2018, is a well
documented, still-current formalization of the pattern as a managed job
type, distinct from SageMaker's separately named real-time and asynchronous
inference options.

## 2. Problem and context

Many prediction workloads have no human waiting on a response, a nightly
churn score for every customer, a fraud risk score recomputed after a data
refresh, a batch of images to caption ahead of a content release. Serving
these through a low-latency, always-on endpoint forces a system to pay for
constant availability it never needs and to build request-shaped plumbing
around what is fundamentally a bulk data transformation.

## 3. Forces

- Throughput per dollar favors large, parallel batch jobs over many small,
  serially-billed requests, but batch jobs trade away the ability to react
  to any single input the moment it becomes available.
- A held-open, always-on endpoint gives the lowest possible latency for a
  request that does arrive, at the cost of paying for idle capacity between
  requests.
- Reprocessing a mistake is cheap in batch, rerun the job against the same
  input set, but expensive in a real-time system already serving live
  predictions to users.
- Model loading cost, reading weights from storage into memory, is paid
  once per worker for an entire batch, rather than once per individual
  prediction, which changes which model sizes are practical for which mode.

## 4. Applicability and non-applicability

Applies whenever predictions are needed for a known, boundable set of
inputs on a schedule or trigger, and no individual prediction needs to
reflect data newer than the batch's own input snapshot. Does not apply when
a prediction must reflect an event that happened moments ago, a live
recommendation reacting to a click just made, or when the full input set is
not knowable in advance, an open stream of arbitrary user requests.

## 5. Structure

A batch inference job reads a defined input dataset, typically partitioned
across storage, such as S3 keys or a data warehouse table, loads a single
model version once per worker, applies it across the partition assigned to
that worker, and writes predictions to an output location keyed so each
input's prediction can be looked up afterward. A job status record tracks
the whole run's lifecycle independent of any single partition's progress.

## 6. ASCII structure diagram

```
  input dataset (S3 / warehouse)
       |
       v
  +--------------------+
  | batch inference job|
  |                    |
  |  worker 1 --model--+--> partition 1 predictions
  |  worker 2 --model--+--> partition 2 predictions
  |  worker N --model--+--> partition N predictions
  +--------------------+
       |
       v
  output store (predictions keyed by input id)
```

## 7. Dynamics

The job scheduler splits the input dataset into partitions, sized so each
worker's slice fits available memory alongside the loaded model. Each
worker loads the model once, then iterates its assigned partition, applying
the model to each input and writing a prediction record keyed to the
original input's identifier. The job's overall status transitions only once
every partition has completed or a defined failure threshold has been
exceeded, and a downstream consumer reads the completed output location
only after that terminal status is observed.

## 8. Implementation variants

AWS SageMaker's Batch Transform, `TransformJob`, splits the input by S3 key
and additionally supports `SplitType=Line` for mini-batching within a
single large file, provisions ephemeral compute that materializes the model
from storage, up to 30GB of attached storage per instance in
SageMaker's own documented limits, and exposes a `TransformJobStatus`
enum a caller polls or subscribes to. Billing is scoped to the job's actual
runtime window rather than to any idle time before or after it.

AWS documents four distinct deployment shapes side by side, real-time,
Asynchronous Inference, Serverless Inference, and Batch Transform,
positioning Asynchronous Inference explicitly as a queued, near-real-time
hybrid for large payloads that still need an eventual per-request response,
a useful, sourced middle point between this pattern and always-on serving.

Google's batch prediction product now surfaces under the same Gemini
Enterprise Agent Platform rename already noted for the Model Registry
product line, per Google's own October 2025 announcement naming Thomas
Kurian; this session confirmed the renamed page's title live but could not
retrieve its full current body prose, since the page renders client side,
so the exact current field schema of a batch prediction job is not asserted
here as verified.

Databricks documents two distinct paths under the same general banner. AI
Functions, `ai_query`, is Databricks' current, LLM-focused marketing
narrative for batch-style scoring inside SQL and Spark pipelines, while the
older, general-purpose mechanism for classical models is
`mlflow.pyfunc.spark_udf`, which wraps a registered MLflow model as a Spark
user-defined function so it can be applied across a DataFrame using
ordinary Spark parallelism. Spark's own worker semantics mean a model
wrapped this way is loaded once per worker process and reused across the
rows that worker handles, standard Spark UDF behavior rather than a
documented claim specific to MLflow.

## 9. Known production uses

Uber's Michelangelo platform, already cited for its feature store and
model registry components, documents its own offline scoring path running
trained models against data materialized in Spark and Hive, predating any
dedicated managed batch-inference product. Shopify's Merlin machine
learning platform has publicly described a batch-first approach to serving
predictions, deferring real-time serving to a later stage of a workload's
maturity rather than defaulting to it. A third, independently documented
production case beyond these two could not be found live this session and
is not asserted.

## 10. Consequences

Batch inference amortizes model-loading cost across an entire partition
instead of every single request, and lets compute scale to exactly the size
of the job rather than to a provisioned, always-on baseline. It introduces
latency between when an input becomes available and when its prediction is
usable, bounded by the job's own schedule or trigger interval, and it makes
a prediction's freshness a property of the whole batch run rather than of
any individual input.

## 11. Failure modes and misuse

Running batch inference on a schedule tight enough that consecutive jobs
overlap, without a lock or a check for the prior run's completion, can
double-process input or corrupt a shared output location mid-write.
Treating a batch job's average latency as representative of any single
input's latency misleads downstream consumers who actually need a bound on
the worst case, the tail of a batch job, not its mean. Loading the model
fresh per input row instead of once per worker, an easy mistake inside a
naive UDF, silently turns a batch job's dominant cost into repeated model
loads rather than the inference work itself.

## 12. Trade-off matrix

| Approach | Latency to a single input | Cost model | Reprocessing cost |
|---|---|---|---|
| Real-time endpoint | Milliseconds | Pays for idle capacity | Expensive, live traffic |
| Asynchronous Inference | Seconds to minutes | Pays per invocation plus queue | Moderate |
| Batch Transform / batch job | Minutes to hours, bound by schedule | Pays only for job runtime | Cheap, rerun the job |
| Serverless Inference | Milliseconds after cold start | Pays per invocation | Moderate |

## 13. Related and incompatible patterns

Composes directly with model-registry, since a batch job resolves the
specific model version it should load from the registry rather than a
hardcoded path, and with feature-store, since the offline store described
under that pattern is frequently the exact input dataset a batch inference
job reads from. Related to online-inference and shadow-model, since a new
model version is often first run in batch against historical data to
validate its predictions before being promoted to serve live traffic. Not
incompatible with real-time serving, the two commonly coexist for the same
model, batch for bulk scoring and real-time for individual requests that
need a fresh answer.

## 14. Refactoring path in and out

Introducing batch inference into a system currently computing predictions
ad hoc starts by defining the bounded input dataset and the output schema
explicitly, then wrapping the existing scoring logic in a job that reads
that input and writes that output on a schedule, without yet touching
whatever consumes the predictions. Migrating from batch to real-time
serving means keeping the batch job as a fallback path while a new
low-latency endpoint is introduced, then cutting consumers over once the
endpoint's correctness has been validated against the batch job's own
output. Removing batch inference entirely means confirming every consumer
has migrated to a real-time or asynchronous path before decommissioning the
scheduled job.

## 15. Testing and verification

Verify a batch job's output against a known input set with precomputed
expected predictions, so a change to the scoring logic or the loaded model
version is caught before it reaches the full production input set. Verify
that a job which fails partway through leaves the output location in a
state a downstream consumer can detect as incomplete, rather than a
partially-written result indistinguishable from a successful run. Verify
that overlapping runs of the same job are prevented or safely serialized.

## 16. Observability signals

Track job duration and the fraction of a partition's inputs successfully
scored versus failed, since a rising per-input failure rate inside an
otherwise successful job is easy to miss if only the job's overall
completion status is watched. Track the age of the most recent completed
batch, since a consumer silently reading a stale output from a job that
stopped running weeks ago is a common, quiet failure. Track model-load time
separately from per-input scoring time, since the two have very different
scaling behavior as batch size grows.

## 17. Security and privacy implications

A batch job's input dataset commonly aggregates records across many
individuals into a single readable file or table, which concentrates
exposure if that intermediate location is not access-controlled as
carefully as the original source data. Output predictions can themselves
be sensitive, a computed risk or health score is derived personal data even
when the original input fields were not directly identifying, and should be
governed accordingly rather than treated as a lesser artifact than the
input.

## 18. References

- AWS SageMaker documentation, Batch Transform. https://docs.aws.amazon.com/sagemaker/latest/dg/batch-transform.html
- AWS SageMaker documentation, Deploy models for inference (real-time, serverless, asynchronous, batch). https://docs.aws.amazon.com/sagemaker/latest/dg/deploy-model.html
- AWS SageMaker documentation, Asynchronous Inference. https://docs.aws.amazon.com/sagemaker/latest/dg/async-inference.html
- Databricks documentation, mlflow.pyfunc.spark_udf. https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html
- Mike Del Balso and Jeremy Hermann, Meet Michelangelo, Uber's Machine Learning Platform, Uber Engineering, September 5, 2017. https://www.uber.com/blog/michelangelo-machine-learning-platform/
- Shopify Engineering, Merlin, Shopify's Machine Learning Platform. https://shopify.engineering/merlin-shopify-machine-learning-platform

## Code

```typescript
interface BatchInput {
  id: string;
  payload: unknown;
}

interface BatchPrediction {
  inputId: string;
  score: number;
}

type PredictFn = (payload: unknown) => number;

class BatchInferenceJob {
  private status: "pending" | "running" | "succeeded" | "failed" = "pending";

  constructor(private readonly modelVersion: string, private readonly predict: PredictFn) {}

  run(inputs: BatchInput[]): BatchPrediction[] {
    this.status = "running";
    const results: BatchPrediction[] = [];
    try {
      for (const input of inputs) {
        const score = this.predict(input.payload);
        results.push({ inputId: input.id, score });
      }
      this.status = "succeeded";
      return results;
    } catch (err) {
      this.status = "failed";
      throw err;
    }
  }

  getStatus(): string {
    return this.status;
  }
}
```

```python
from dataclasses import dataclass
from typing import Callable, Literal


@dataclass
class BatchInput:
    id: str
    payload: object


@dataclass
class BatchPrediction:
    input_id: str
    score: float


class BatchInferenceJob:
    def __init__(self, model_version: str, predict: Callable[[object], float]) -> None:
        self.model_version = model_version
        self._predict = predict
        self.status: Literal["pending", "running", "succeeded", "failed"] = "pending"

    def run(self, inputs: list[BatchInput]) -> list[BatchPrediction]:
        self.status = "running"
        results: list[BatchPrediction] = []
        try:
            for item in inputs:
                score = self._predict(item.payload)
                results.append(BatchPrediction(input_id=item.id, score=score))
            self.status = "succeeded"
            return results
        except Exception:
            self.status = "failed"
            raise
```

```go
package batch

type Input struct {
	ID      string
	Payload interface{}
}

type Prediction struct {
	InputID string
	Score   float64
}

type PredictFunc func(payload interface{}) float64

type Status string

const (
	StatusPending   Status = "pending"
	StatusRunning   Status = "running"
	StatusSucceeded Status = "succeeded"
	StatusFailed    Status = "failed"
)

type Job struct {
	ModelVersion string
	predict      PredictFunc
	status       Status
}

func NewJob(modelVersion string, predict PredictFunc) *Job {
	return &Job{ModelVersion: modelVersion, predict: predict, status: StatusPending}
}

func (j *Job) Run(inputs []Input) ([]Prediction, error) {
	j.status = StatusRunning
	results := make([]Prediction, 0, len(inputs))
	for _, in := range inputs {
		score := j.predict(in.Payload)
		results = append(results, Prediction{InputID: in.ID, Score: score})
	}
	j.status = StatusSucceeded
	return results, nil
}

func (j *Job) Status() Status {
	return j.status
}
```
