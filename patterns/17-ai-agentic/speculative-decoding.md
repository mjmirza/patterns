---
name: Speculative Decoding
slug: speculative-decoding
family: 17-ai-agentic
category: AI Inference & Serving
aliases: [Speculative Sampling, Assisted Generation, Draft-Target Decoding]
first_described: "Leviathan, Kalman, Matias 2023"
maturity: canonical
related: [prompt-caching-exact-prefix, inference-time-scaling, semantic-caching, token-budget]
incompatible_with: []
verified: 2026-08-23
---

## 1. Name, aliases, and lineage

Speculative Decoding, also known as Speculative Sampling, Assisted Generation, or Draft-Target Decoding, was introduced independently in late 2022 and early 2023 by two research groups. Yaniv Leviathan, Matan Kalman, and Yossi Matias published "Fast Inference from Transformers via Speculative Decoding" at Google Research. Charlie Chen and colleagues published "Accelerating Large Language Model Decoding with Speculative Sampling" at DeepMind.

The pattern addresses the memory-bandwidth bottleneck inherent to autoregressive generation in Large Language Models (LLMs). Rather than generating every output token sequentially through an expensive target model, a smaller and faster draft model speculatively generates a sequence of draft tokens. The target model then processes all draft tokens concurrently in a single forward pass, verifying or rejecting them using a modified rejection sampling scheme that guarantees exact mathematical equivalence to sampling directly from the target model.

## 2. Problem and context

Autoregressive inference in Transformer-based language models proceeds token by token. Generating each token requires fetching billions of model parameters from High Bandwidth Memory (HBM) into GPU compute units. During the decoding phase (where sequence batch size or context length is modest relative to parameter scale), execution is severely memory-bandwidth bound rather than compute bound. Tensor cores spend significant clock cycles waiting for parameter weights to arrive from memory.

As target models grow from 7 billion to over 700 billion parameters, single-token latency increases linearly with parameter volume. Real-time agentic workflows, interactive chat assistants, and code completion engines require low time-per-output-token latency. Running a 70B parameter model sequentially for 200 output tokens requires 200 full weight-loading passes over memory. Speculative decoding restructures this workload by exploiting the fact that parallel verification of K tokens in a single target model forward pass costs nearly the same time as generating a single token, provided total token sequence length stays within compute-bound matrix multiplication thresholds.

## 3. Forces

Speculative decoding balances several distinct operational and architectural pressures.

Memory Bandwidth vs. Compute Utilization. Sequential autoregressive decoding leaves GPU compute units underutilized while maxing out memory bandwidth. Speculative decoding trades spare GPU compute FLOPS during target verification to reduce the total number of memory-loading cycles.

Draft Acceptance Rate vs. Overhead Cost. The speedup ratio depends directly on how frequently the target model accepts tokens proposed by the draft model. If acceptance probability is high, token generation rate increases substantially. If the draft model produces poor predictions, rejection sampling discards draft tokens, wasting draft generation compute and KV cache allocation.

Model Parameter Footprint vs. VRAM Allocation. Running speculative decoding requires loading two separate models into GPU VRAM (or across networked inference nodes). Reserving GPU memory for draft model parameters and draft KV caches reduces the maximum memory allocated for target model batching and context length.

Exact Distribution Fidelity vs. Heuristic Speedup. System architects must often choose between deterministic/lossless acceleration and lossy approximation methods. Speculative decoding uses modified rejection sampling to guarantee that the final generated token distribution is mathematically identical to running the target model standalone.

## 4. Applicability and non-applicability

#### When to apply

Reach for Speculative Decoding when:
1. Target model inference is memory-bandwidth bound during decoding, with low GPU compute utilization per forward pass.
2. Output token latency is the critical service level indicator (SLI) for user experience or agentic workflow completion.
3. A suitable draft model exists that shares vocabulary and tokenizer alignment with the target model, yielding high token acceptance rates.
4. Sufficient GPU VRAM is available to host both the target model and draft model without causing out-of-memory errors or reducing maximum target batch size below operational thresholds.

#### When NOT to apply

Do NOT reach for Speculative Decoding when:
1. Serving workloads under extreme request concurrency where target model batch size is already large enough to saturate GPU compute FLOPS (compute-bound regime).
2. The draft model vocabulary or tokenizer diverges from the target model, requiring complex mapping layers that lower acceptance alignment.
3. GPU memory is severely constrained, making draft model parameter hosting or draft KV cache reservation impossible.
4. Generating highly specialized domain text where smaller draft models suffer from extremely low acceptance rates, causing net slowdowns due to speculative overhead.

## 5. Structure

The participants in Speculative Decoding are defined as follows:

* **Inference Orchestrator**: Manages request lifecycles, schedules draft generation rounds, coordinates target verification passes, and maintains output token buffers.
* **Draft Model Service**: A lightweight, parameter-efficient language model (typically 10x to 100x smaller than the target model) that generates K candidate tokens autoregressively.
* **Target Model Service**: The primary, full-scale language model that executes a single parallel forward pass over the context plus K draft tokens to compute target logits.
* **Speculative Verifier**: Implements modified rejection sampling. Compares draft probabilities against target probabilities to accept a prefix of draft tokens and sample a replacement token upon rejection.
* **KV Cache Manager**: Manages Key-Value cache entries for both draft and target models, trimming rejected speculative branches after each verification pass.

## 6. ASCII structure diagram

```
+-------------------------------------------------------------------+
|                        Inference Orchestrator                     |
+-------------------------------------------------------------------+
       |                                             ^
       | 1. Submit Prompt                            | 5. Return Accepted
       v                                             |    Tokens
+-----------------------+                    +----------------------+
|  Draft Model Service  |                    | Speculative Verifier |
+-----------------------+                    +----------------------+
       |                                             ^
       | 2. Generate K Tokens                        | 4. Compare Logits
       v                                             |    (Rejection Sample)
+-----------------------+                    +----------------------+
| Draft Token Sequence  | -----------------> | Target Model Service |
|  [t_1, t_2, ... t_k]  | 3. Parallel Pass   |  (1 Forward Pass)    |
+-----------------------+                    +----------------------+
```

## 7. Dynamics

The runtime interaction flow follows a repeating loop until generation completes:

```
Draft Model               Target Model             Verifier             Orchestrator
    |                          |                      |                      |
    |--- 1. Gen K Drafts ----->|                      |                      |
    |    (t_1..t_k)            |                      |                      |
    |                          |--- 2. Forward Pass ->|                      |
    |                          |    (Eval t_1..t_k+1) |                      |
    |                          |                      |--- 3. Rejection ---->|
    |                          |                      |    Sampling          |
    |                          |                      |    Accept n <= K     |
    |<-- 4. Rollback Cache ----|<---------------------|    Sample t_n+1      |
    |    to Pos (N + n)        |                      |                      |
    |                          |                      |--- 5. Append -------->|
    |                          |                      |    Tokens to Output  |
```

Detailed sequence steps:
1. **Draft Step**: The Draft Model generates K draft tokens sequentially. For each draft token $t_i$, the draft model produces probability distribution $q_i(x)$.
2. **Target Step**: The Target Model receives the prompt plus all K draft tokens. It performs a single parallel forward pass over the $K$ draft positions, outputting probability distributions $p_1(x), p_2(x), \dots, p_{K+1}(x)$.
3. **Verification Step**: For $i = 1 \dots K$, the verifier checks if token $t_i$ is accepted. A random uniform variable $u \sim U(0,1)$ is drawn. If $u \le \min(1, p_i(t_i) / q_i(t_i))$, token $t_i$ is accepted.
4. **Rejection & Resampling**: If token $t_{n+1}$ is rejected (at index $n+1 \le K$), tokens $t_1 \dots t_n$ are accepted. A replacement token $t'_{n+1}$ is sampled from adjusted distribution $p'_{n+1}(x) = \max(0, p_{n+1}(x) - q_{n+1}(x)) / \sum_x \max(0, p_{n+1}(x) - q_{n+1}(x))$. Draft tokens past position $n$ are discarded.
5. **Cache Sync**: Both draft and target KV caches are truncated to match the newly accepted position $N + n + 1$, and generation continues for the next round.

## 8. Implementation variants

#### Draft Model Speculative Decoding

The standard variant described by Leviathan et al. Uses a separate, smaller neural network (e.g., Llama-3-8B as draft for Llama-3-70B). Offers high draft quality and variable speculation length $K$, but requires allocating GPU memory for draft model weights.

#### Medusa / Eagle Multi-Head Speculative Decoding

Instead of a separate draft model, extra prediction heads (Medusa or Eagle) are attached directly to the target model's top hidden state. These heads predict multiple future tokens in parallel without running an independent draft loop. Reduces memory overhead since parameter weights are shared, but limits draft flexibility.

#### Prompt / N-Gram Lookup Speculative Decoding

Replaces the draft model with a static N-gram lookup table or prompt prefix search. Candidate draft tokens are gathered by matching current context against earlier parts of the prompt or document history. Requires zero additional GPU VRAM and zero draft forward passes. Highly effective for summarization, code editing, and retrieval tasks with repetitive context.

## 9. Known production uses

1. **vLLM Inference Engine**: Implements speculative decoding supporting draft models, N-gram matching, and Eagle heads. Used in high-throughput production LLM clusters. Reference: vLLM Documentation, Speculative Decoding Feature Guide (2024).
2. **NVIDIA TensorRT-LLM**: Features production-grade speculative decoding with KV cache reuse and draft-target batching optimizations across Tensor Core GPUs. Reference: NVIDIA TensorRT-LLM Architecture Guide (2024).
3. **Apple MLX Framework**: Implements speculative sampling for on-device inference on Apple Silicon, reducing generation latency for local assistant models. Reference: Apple MLX Open Source Repository (2023).

## 10. Consequences

#### Positive

1. **Reduced Generation Latency**: Achieves 1.5x to 3.0x speedup in time-per-output-token latency for memory-bandwidth bound LLM serving workloads.
2. **Mathematically Lossless**: Modified rejection sampling guarantees that output token probability distribution remains identical to standalone target model generation.
3. **Higher GPU Compute Efficiency**: Converts idle GPU compute cycles into effective output token throughput without altering network weights.

#### Negative

1. **Increased VRAM Consumption**: Hosting draft model parameters and draft KV caches consumes GPU memory that could otherwise support larger target batch sizes.
2. **Variable Latency Per Step**: Iteration time varies depending on the number of accepted tokens per draft round, requiring dynamic batch scheduling.
3. **Engineering Complexity**: Requires dual KV cache state synchronization, rollback mechanisms, and probability distribution manipulation logic.

## 11. Failure modes and misuse

1. **Draft Model Mismatch (Low Acceptance Cascade)**: Using a draft model whose distribution diverges significantly from the target model leads to low token acceptance rates (< 20%). The system incurs draft generation overhead and target evaluation overhead while accepting only 1 token per round, causing a net slowdown relative to unassisted decoding.
2. **VRAM Exhaustion via Unbounded Speculation**: Setting draft speculation lookahead $K$ too high increases target forward pass sequence length and draft KV cache allocation, causing Out-Of-Memory (OOM) crashes under peak concurrency.
3. **Draft Model KV Cache Truncation Desync**: Failing to roll back draft model KV caches accurately after rejection causes state corruption, leading to invalid token predictions in subsequent rounds.

## 12. Trade-off matrix

| Force / Metric | Standalone Autoregressive | Speculative Decoding | Prompt / N-Gram Lookup | Medusa / Eagle Heads |
|---|---|---|---|---|
| Generation Latency | Baseline (1x) | High Speedup (2.0x-3.0x) | Moderate Speedup (1.3x-1.8x) | High Speedup (2.0x-2.8x) |
| Output Distribution | Exact | Exact (Lossless) | Exact (Lossless) | Exact (Lossless) |
| Additional VRAM Footprint | None | High (Draft Model + KV) | Zero | Low (Head Parameters) |
| Setup / Training Overhead | None | Low (Off-the-shelf draft) | None | Medium (Train extra heads) |
| Workload Alignment | Universal | General Text / Agentic | Repetitive / Context-Heavy | General Text |

## 13. Related and incompatible patterns

#### Related Patterns

* **Prompt Caching via Exact Prefix Preservation**: Caches Key-Value tensors for prompt prefixes. Complements Speculative Decoding: Prompt Caching accelerates the initial prefill phase, while Speculative Decoding accelerates the subsequent decode phase.
* **Semantic Caching**: Serves pre-computed responses for semantically equivalent prompts. Operates upstream of inference; on cache hit, inference and speculative decoding are entirely bypassed.
* **Token Budget**: Constrains output sequence length. Works alongside Speculative Decoding to set maximum draft horizon $K$ within token limits.

#### Incompatible Patterns

* **Pre-fill / Decode Disaggregation with Extreme Concurrency**: Disaggregating prefill and decode nodes at maximum batch saturation (where target decode is compute bound) negates the benefits of speculative decoding.

## 14. Refactoring path in and out

#### Adoption Path

1. **Establish Baseline SLIs**: Measure baseline time-per-output-token latency and GPU memory usage for the target model.
2. **Select Draft Strategy**: Evaluate off-the-shelf draft models with matching tokenizers or evaluate N-gram prompt lookup if VRAM is constrained.
3. **Implement Rejection Sampling Verifier**: Integrate draft-target orchestrator with probability distribution comparison and KV cache rollback support.
4. **Benchmark Acceptance Rate**: Profile draft acceptance rate $E[\text{accept}]$ across production query samples. Confirm acceptance rate exceeds 50% before deploying to production.
5. **Enable Dynamic Speculation Horizon**: Tune speculation horizon $K$ dynamically based on measured acceptance rates and target GPU memory load.

#### Removal Path

1. **Disable Speculative Routing**: Re-route inference requests directly to target model autoregressive decode engine.
2. **Deallocate Draft Memory**: Unload draft model parameters and release draft KV cache memory pools.
3. **Remove Cache Rollback Logic**: Simplify orchestrator loop to standard single-model sequential decoding.

## 15. Testing and verification

Testing Speculative Decoding requires verifying both distribution fidelity and cache synchronization logic:

1. **Distribution Equivalence Test**: Run target model standalone vs. speculative pipeline over fixed prompts using identical random seeds. Assert that generated token sequences match exactly or follow identical output logits within floating-point tolerance.
2. **Acceptance Rate Unit Tests**: Mock draft and target probability distributions with known acceptance ratios. Verify that the verifier accepts and rejects tokens at exact expected probabilities.
3. **KV Cache Rollback Integration Test**: Trigger intentional rejections at position $n < K$. Inspect KV cache memory offset before and after rollback to confirm zero memory leaks or tensor offset drift.

## 16. Observability signals

Key metric and log signals for monitoring Speculative Decoding in production:

* **Draft Acceptance Rate (`llm_speculative_draft_acceptance_rate`)**: Ratio of accepted draft tokens to total proposed draft tokens ($E[n] / K$). Healthy baseline is typically > 0.60.
* **Mean Accepted Tokens Per Step (`llm_speculative_accepted_tokens_per_step`)**: Average number of output tokens emitted per target forward pass ($1 + E[n]$). A value of 1.0 indicates zero speedup.
* **Effective Speedup Ratio (`llm_speculative_speedup_ratio`)**: Time per token in standalone mode divided by time per token in speculative mode.
* **Draft Cache Rollback Count (`llm_speculative_cache_rollback_total`)**: Counter measuring KV cache rollback operations triggered by draft rejections.
* **VRAM Overhead Metrics (`llm_speculative_draft_vram_bytes`)**: Memory reserved by draft model parameters and active draft KV cache blocks.

## 17. Security and privacy implications

Speculative Decoding operates entirely within the model inference execution pipeline and does not alter input/output boundaries.

* **Side-Channel Timing Surface**: Because generation step timing varies with draft token acceptance rates, adversaries with millisecond-level telemetry access could theoretically infer properties of the generated text (e.g., predictability or language distribution) based on step latency variations. Mitigate by applying constant-time padding or jitter to public-facing streaming endpoints if timing side-channels are a concern.
* **VRAM Data Isolation**: Verify draft model KV cache blocks are properly zeroed or reset between tenant requests to prevent cross-tenant token state leakage.

## 18. References

1. Leviathan, Y., Kalman, M., & Matias, Y. (2023). "Fast Inference from Transformers via Speculative Decoding". Proceedings of the 40th International Conference on Machine Learning (ICML 2023). PMLR 202:19274-19286. https://arxiv.org/abs/2211.17192 (Verified 2026-08-23).
2. Chen, C., Bunge, S., Tuttle, M., et al. (2023). "Accelerating Large Language Model Decoding with Speculative Sampling". arXiv preprint arXiv:2302.01318. https://arxiv.org/abs/2302.01318 (Verified 2026-08-23).
3. vLLM Project. (2024). "Speculative Decoding Architecture and Documentation". https://docs.vllm.ai/en/latest/models/spec_decode.html (Verified 2026-08-23).
4. NVIDIA Corporation. (2024). "TensorRT-LLM Developer Guide: Speculative Decoding". https://nvidia.github.io/TensorRT-LLM/advanced/speculative-decoding.html (Verified 2026-08-23).

**Evidence grade.** high

**Most solid findings.** ICML 2023 primary literature establishes exact mathematical proof for lossless rejection sampling. Production implementations in vLLM and TensorRT-LLM provide empirical verification of 2x-3x decode latency speedups on standard GPU hardware.

**Unverified or unclear.** Long-term acceptance rates for specialized domain fine-tuned target models paired with generic off-the-shelf draft models vary and require empirical profiling per domain.

## Code examples

### Python

```python
import random
from typing import List, Tuple

class SpeculativeVerifier:
    """Verifies draft tokens against target model logits using rejection sampling."""

    def __init__(self, seed: int = 42) -> None:
        self.rng = random.Random(seed)

    def verify_tokens(
        self,
        draft_tokens: List[int],
        draft_probs: List[List[float]],
        target_probs: List[List[float]],
    ) -> Tuple[List[int], int]:
        """Compares draft and target probabilities to accept prefix of draft tokens."""
        accepted_tokens: List[int] = []

        for i, token in enumerate(draft_tokens):
            p_target = target_probs[i][token]
            q_draft = draft_probs[i][token]

            if q_draft <= 0.0:
                acceptance_prob = 1.0
            else:
                acceptance_prob = min(1.0, p_target / q_draft)

            u = self.rng.random()
            if u <= acceptance_prob:
                accepted_tokens.append(token)
            else:
                # Sample replacement token from adjusted distribution
                replacement = self._sample_adjusted(target_probs[i], draft_probs[i])
                accepted_tokens.append(replacement)
                return accepted_tokens, len(accepted_tokens)

        # All K tokens accepted; sample bonus token from target_probs[K]
        bonus_token = self._sample_categorical(target_probs[len(draft_tokens)])
        accepted_tokens.append(bonus_token)
        return accepted_tokens, len(accepted_tokens)

    def _sample_adjusted(
        self, p_dist: List[float], q_dist: List[float]
    ) -> int:
        vocab_size = len(p_dist)
        adjusted = [max(0.0, p_dist[v] - q_dist[v]) for v in range(vocab_size)]
        total = sum(adjusted)

        if total <= 0.0:
            return self._sample_categorical(p_dist)

        norm_dist = [val / total for val in adjusted]
        return self._sample_categorical(norm_dist)

    def _sample_categorical(self, probs: List[float]) -> int:
        u = self.rng.random()
        cumulative = 0.0
        for idx, p in enumerate(probs):
            cumulative += p
            if u <= cumulative:
                return idx
        return len(probs) - 1


if __name__ == "__main__":
    verifier = SpeculativeVerifier()
    # Vocabulary size 4, 3 draft tokens proposed
    draft_tokens = [1, 2, 0]
    draft_probs = [
        [0.1, 0.7, 0.1, 0.1],
        [0.1, 0.1, 0.7, 0.1],
        [0.6, 0.2, 0.1, 0.1],
    ]
    target_probs = [
        [0.1, 0.8, 0.05, 0.05],
        [0.05, 0.05, 0.8, 0.1],
        [0.1, 0.1, 0.1, 0.7],  # Position 2 differs significantly
        [0.25, 0.25, 0.25, 0.25],
    ]

    accepted, count = verifier.verify_tokens(
        draft_tokens, draft_probs, target_probs
    )
    print(f"Accepted tokens count: {count}")
    print(f"Token sequence: {accepted}")
```

### TypeScript

```typescript
export interface VerificationResult {
  acceptedTokens: number[];
  acceptedCount: number;
}

export class SpeculativeVerifierTS {
  private rngSeed: number;

  constructor(seed = 42) {
    this.rngSeed = seed;
  }

  private nextRandom(): number {
    this.rngSeed = (this.rngSeed * 9301 + 49297) % 233280;
    return this.rngSeed / 233280;
  }

  public verifyTokens(
    draftTokens: number[],
    draftProbs: number[][],
    targetProbs: number[][]
  ): VerificationResult {
    const acceptedTokens: number[] = [];

    for (let i = 0; i < draftTokens.length; i++) {
      const token = draftTokens[i];
      const pTarget = targetProbs[i][token];
      const qDraft = draftProbs[i][token];

      const acceptanceRatio = qDraft > 0 ? Math.min(1.0, pTarget / qDraft) : 1.0;
      const u = this.nextRandom();

      if (u <= acceptanceRatio) {
        acceptedTokens.push(token);
      } else {
        const replacement = this.sampleAdjusted(targetProbs[i], draftProbs[i]);
        acceptedTokens.push(replacement);
        return {
          acceptedTokens,
          acceptedCount: acceptedTokens.length,
        };
      }
    }

    const bonusToken = this.sampleCategorical(targetProbs[draftTokens.length]);
    acceptedTokens.push(bonusToken);

    return {
      acceptedTokens,
      acceptedCount: acceptedTokens.length,
    };
  }

  private sampleAdjusted(pDist: number[], qDist: number[]): number {
    const vocabSize = pDist.length;
    const adjusted: number[] = new Array(vocabSize);
    let total = 0;

    for (let v = 0; v < vocabSize; v++) {
      const diff = Math.max(0.0, pDist[v] - qDist[v]);
      adjusted[v] = diff;
      total += diff;
    }

    if (total <= 0) {
      return this.sampleCategorical(pDist);
    }

    const norm = adjusted.map((val) => val / total);
    return this.sampleCategorical(norm);
  }

  private sampleCategorical(probs: number[]): number {
    const u = this.nextRandom();
    let cumulative = 0;

    for (let idx = 0; idx < probs.length; idx++) {
      cumulative += probs[idx];
      if (u <= cumulative) {
        return idx;
      }
    }

    return probs.length - 1;
  }
}

// Example usage
const verifier = new SpeculativeVerifierTS(123);
const draftTokens = [0, 1];
const draftProbs = [
  [0.8, 0.2],
  [0.1, 0.9],
];
const targetProbs = [
  [0.9, 0.1],
  [0.2, 0.8],
  [0.5, 0.5],
];

const res = verifier.verifyTokens(draftTokens, draftProbs, targetProbs);
console.log(`Accepted count: ${res.acceptedCount}`);
console.log(`Tokens: ${res.acceptedTokens.join(", ")}`);
```

### Go

```go
package main

import (
	"fmt"
	"math"
	"math/rand"
)

type VerificationResult struct {
	AcceptedTokens []int
	AcceptedCount  int
}

type SpeculativeVerifier struct {
	rng *rand.Rand
}

func NewSpeculativeVerifier(seed int64) *SpeculativeVerifier {
	return &SpeculativeVerifier{
		rng: rand.New(rand.NewSource(seed)),
	}
}

func (v *SpeculativeVerifier) VerifyTokens(
	draftTokens []int,
	draftProbs [][]float64,
	targetProbs [][]float64,
) VerificationResult {
	accepted := make([]int, 0, len(draftTokens)+1)

	for i, token := range draftTokens {
		pTarget := targetProbs[i][token]
		qDraft := draftProbs[i][token]

		acceptanceProb := 1.0
		if qDraft > 0 {
			acceptanceProb = math.Min(1.0, pTarget/qDraft)
		}

		u := v.rng.Float64()
		if u <= acceptanceProb {
			accepted = append(accepted, token)
		} else {
			replacement := v.sampleAdjusted(targetProbs[i], draftProbs[i])
			accepted = append(accepted, replacement)
			return VerificationResult{
				AcceptedTokens: accepted,
				AcceptedCount:  len(accepted),
			}
		}
	}

	bonusToken := v.sampleCategorical(targetProbs[len(draftTokens)])
	accepted = append(accepted, bonusToken)

	return VerificationResult{
		AcceptedTokens: accepted,
		AcceptedCount:  len(accepted),
	}
}

func (v *SpeculativeVerifier) sampleAdjusted(pDist, qDist []float64) int {
	vocabSize := len(pDist)
	adjusted := make([]float64, vocabSize)
	total := 0.0

	for i := 0; i < vocabSize; i++ {
		diff := math.Max(0.0, pDist[i]-qDist[i])
		adjusted[i] = diff
		total += diff
	}

	if total <= 0 {
		return v.sampleCategorical(pDist)
	}

	norm := make([]float64, vocabSize)
	for i := 0; i < vocabSize; i++ {
		norm[i] = adjusted[i] / total
	}

	return v.sampleCategorical(norm)
}

func (v *SpeculativeVerifier) sampleCategorical(probs []float64) int {
	u := v.rng.Float64()
	cumulative := 0.0

	for idx, p := range probs {
		cumulative += p
		if u <= cumulative {
			return idx
		}
	}

	return len(probs) - 1
}

func main() {
	verifier := NewSpeculativeVerifier(42)
	draftTokens := []int{1, 0}
	draftProbs := [][]float64{
		{0.2, 0.8},
		{0.7, 0.3},
	}
	targetProbs := [][]float64{
		{0.1, 0.9},
		{0.6, 0.4},
		{0.5, 0.5},
	}

	res := verifier.VerifyTokens(draftTokens, draftProbs, targetProbs)
	fmt.Printf("Accepted count: %d\n", res.AcceptedCount)
	fmt.Printf("Tokens: %v\n", res.AcceptedTokens)
}
```
