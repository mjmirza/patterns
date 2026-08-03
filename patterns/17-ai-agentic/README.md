# Family 17. AI and Agentic

Origin. Papers and vendor engineering, 2023 to 2026

21 entries, 177,062 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## AI Agentic

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Advanced RAG](advanced-rag.md) | established | 9,369 | Naive RAG treats "find the k nearest vectors to this query's embedding" as if it were the same question as "find the passages that actually let the model answer this question ... |
| [Agentic RAG](agentic-rag.md) | emerging | 10,218 | Naive RAG performs exactly one retrieval and exactly one generation per user turn, embed the query, fetch the top-k nearest chunks from a single index, paste them into the prompt ... |
| [Chunking Strategies](chunking-strategies.md) | established | 7,093 | A large language model has a finite context limit, and even models with very large limits charge per token and lose retrieval accuracy on needles buried deep in a long context, a ... |
| [Corrective RAG](corrective-rag.md) | emerging | 8,133 | A support bot answers questions by retrieving from a company's help center index and handing the top few documents to a generator. |
| [GraphRAG](graphrag.md) | emerging | 7,850 | A team has a large private corpus, contracts, incident postmortems, research notes, support transcripts, and wants an LLM to answer questions grounded in that corpus. |
| [Parallelization](parallelization.md) | established | 9,204 | An agentic pipeline built as a single sequential chain of LLM calls has one throughput limit, the wall-clock latency of the slowest single call multiplied by the number of calls ... |
| [Reranking](reranking.md) | canonical | 7,225 | A reader who has never heard the word reranking has still hit the problem it solves. |
| [Retrieval Augmented Generation](retrieval-augmented-generation.md) | canonical | 8,731 | A large language model's knowledge is frozen at the moment its training data was collected, and its parameters have a fixed, finite capacity that cannot hold every fact a user ... |
| [Self-Consistency](self-consistency.md) | established | 6,441 | A large language model generating a chain-of-thought answer with standard greedy decoding commits to one path through the reasoning space, token by token, and never reconsiders. |

## AI and Agentic

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Tree of Thoughts](tree-of-thoughts.md) | established | 9,275 | A language model produces its answer as a single left-to-right token stream. |

## Agentic

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Plan and Execute](plan-execute.md) | canonical | 7,815 | A language model asked to solve a task that takes many steps, and that must call external tools along the way, faces a tension between two failure modes. |
| [ReAct](react.md) | canonical | 7,775 | A language model asked to answer a multi-hop factual question, or to complete a task that spans several tool calls, has two failure modes when it is prompted with only one of the ... |
| [Reflexion](reflexion.md) | emerging | 8,450 | An LLM agent that tries a task once and stops inherits every mistake in that one attempt permanently. |
| [Self-RAG](self-rag.md) | established | 10,532 | A retrieval-augmented language model that always retrieves, for every query, pays the same fixed cost whether the query needs an external source or not. |

## Agentic Workflow

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Prompt Chaining](prompt-chaining.md) | established | 7,673 | A task is handed to a single LLM call, and the call is asked to do everything at once, understand a long or ambiguous instruction, apply several unrelated rules, transform the ... |

## Multi-Agent Coordination

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Orchestrator-Worker](orchestrator-worker.md) | established | 10,095 | A task arrives whose internal shape cannot be known until the model has already looked at it. |

## Reasoning

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Chain of Thought](chain-of-thought.md) | canonical | 8,805 | A large language model predicts its next token from everything that came before it in the same context. |

## Retrieval

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [HyDE (Hypothetical Document Embeddings)](hyde.md) | established | 7,932 | Dense retrieval works by embedding a query into the same vector space as a corpus of documents and finding the nearest neighbors by cosine similarity or inner product. |
| [Hybrid Search](hybrid-search.md) | established | 7,225 | A retrieval-augmented generation system, an internal document search box, or an agent's memory lookup all face the same underlying failure. |

## Workflow

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Evaluator-Optimizer](evaluator-optimizer.md) | established | 9,063 | A single LLM call is a single roll of the dice against a task that has more than one way to go wrong. |
| [Routing](routing.md) | canonical | 8,158 | A single LLM call, driven by one prompt, is asked to handle every shape of input a system receives. |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
