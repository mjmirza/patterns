---
name: Code Mode
slug: code-mode
family: 17-ai-agentic
category: AI Agentic
aliases: [Tools-as-Code, Code Execution Tool Calling]
first_described: "Cloudflare's own engineering blog post introducing the technique"
maturity: emerging
related: []
incompatible_with: []
verified: 2026-08-23
---

# Code Mode

## 1. Name, aliases, and lineage

Code Mode has an agent write and execute code that calls tools as regular
function calls in a sandboxed runtime, rather than having the model emit a
tool-call request for every individual step of a multi-step task.

This entry sources it directly from Cloudflare's own engineering blog,
fetched live. "instead of using tool calls directly, code mode instructs
the model to write code that calls the tools instead... LLMs are much
better at writing code to call APIs than at direct tool calling, probably
because of the vast amount of code available on the internet to train on"
(Kenton Varda and Sunil Pai, "Code Mode. the better way to use MCP,"
Cloudflare blog, 2025-09-26,
https://blog.cloudflare.com/code-mode/, verified
2026-08-23).

This entry explicitly checked the fetched source for a stated applicability
boundary, a named failure mode, a testing or observability recommendation,
and a Command pattern cross-reference, and confirmed the post states none
of them. this entry reports each of those four gaps honestly under its own
dimension below, rather than inventing content the source does not supply.

## 2. Problem and context

Cloudflare's own text states the problem directly, contrasting it with
standard tool calling. "each individual tool call requires a full round
trip. the model generates a tool call, the client executes it, the result
goes back into the context, and the model decides what to do next... for a
task requiring many tool calls in sequence, this is slow and burns a lot of
tokens" (Varda and Pai, "Code Mode," verified 2026-08-23). the standard
round trip this contrasts against is defined precisely by the Model
Context Protocol's own specification. "to invoke a tool, clients send a
`tools/call` request," and the protocol's own message-flow diagram shows
that path completing before the model resumes. "Client, tools/call. Server,
Tool result. Client, Process result" (Model Context Protocol, "Tools,"
https://modelcontextprotocol.io/docs/concepts/tools, verified 2026-08-23),
one such round trip per tool invocation, which the round-trip cost
compounds specifically because intermediate results, per dimension 3, must
pass back through the model's own context to be acted on.

## 3. Forces

Cloudflare's own text names the direct trade the technique resolves.
"when a model needs to process the result of one tool call before calling
the next, and that processing is something code is good at, filtering,
transforming, looping, code mode skips shuttling the intermediate data
through the model's context entirely" (Varda and Pai, "Code Mode,"
verified 2026-08-23). the tension is between the model's own strength,
generating code from a vast training corpus of real API usage, and its own
weakness, direct structured tool-call syntax, which the post states models
handle less reliably.

## 4. Applicability and non-applicability

This entry explicitly checked the fetched source for a stated
applicability or non-applicability boundary and did not find one. the post
frames the technique as broadly beneficial for MCP tool usage without
naming a task shape it is unsuited to, and this entry reports that absence
directly rather than inferring a boundary the source does not state.

## 5. Structure

Cloudflare's own text describes the generated artifact directly. "the
model writes a TypeScript program. tools appear as ordinary async
functions it can call, and it can use normal language constructs, loops,
conditionals, variables, to orchestrate them" (Varda and Pai, "Code Mode,"
verified 2026-08-23), executed inside "a V8 isolate running inside a
Cloudflare Worker... with no access to the network or filesystem except
through the specific tool bindings it's given" (same source). Cloudflare's
own current platform documentation for the underlying primitive states the
same sandboxing guarantee independently. "spin up Workers at runtime to
execute code on-demand in a secure, sandboxed environment... a lightweight
alternative to containers for securely sandboxing code you don't trust"
(Cloudflare, "Dynamic Workers Overview,"
https://developers.cloudflare.com/workers/runtime-apis/bindings/worker-loader/,
verified 2026-08-23).

## 6. ASCII structure diagram

```
  standard tool calling, one round trip per step:

  model -> tool call 1 -> client -> result 1 -> model (in context)
  model -> tool call 2 -> client -> result 2 -> model (in context)
  model -> tool call 3 -> client -> result 3 -> model (in context)

  code mode, one round trip for the whole sequence:

  model -> generated code, calling tool 1, tool 2, tool 3 in sequence
              |
              v
  +------------------------------+
  | sandboxed runtime (V8 isolate)|
  |  tool 1()  tool 2()  tool 3()|
  |  intermediate data stays here |
  +------------------------------+
              |
              v
  final result only -> model (in context)
```

## 7. Dynamics

Cloudflare's own text describes the runtime path directly. "the code runs
inside a Worker, calling into the actual MCP tools through bindings, and
only the final result comes back to the model" (Varda and Pai, "Code
Mode," verified 2026-08-23). the underlying mechanism enabling this on
Cloudflare's own platform is a distinct, named primitive, called Worker
Loaders in the original post and Dynamic Workers in the platform's own
current documentation. "this is possible because of Worker Loaders, which
let a Worker dynamically create and run another Worker containing
arbitrary, untrusted code, in a fully isolated sandbox" (Varda and Pai,
"Code Mode," verified 2026-08-23).

## 8. Implementation variants

This entry explicitly checked the fetched source for a second, independent
implementation of the same technique and did not find one described in
Cloudflare's own post beyond its own MCP-to-TypeScript-tool-binding
approach. this entry reports that as a single confirmed implementation
rather than asserting a second vendor's variant the source does not
describe.

## 9. Known production uses

Cloudflare's own blog names its own platform capability, Worker Loaders,
as the mechanism this technique runs on, per dimension 7, and Cloudflare's
own current documentation for the same primitive, now named Dynamic
Workers, confirms it is a real, documented platform feature rather than an
experimental one-off, per dimension 5. this entry did not find a specific,
named third-party production consumer of Code Mode itself in the fetched
sources, and reports that gap directly. the original post also states the
underlying primitive "is currently in closed beta" (Varda and Pai, "Code
Mode," verified 2026-08-23) at the time it was written, which this entry
reports as a direct constraint on how widely deployable the technique was
when first described.

## 10. Consequences

Cloudflare's own text states the benefit directly, already quoted in
dimension 2, fewer round trips and less context spent shuttling
intermediate results. a real, named cost is stated for a specific case.
"if a tool call returns a huge amount of data that the model actually
needs to see and reason about, code mode does not save you anything, you
still have to get that data into the model's context somehow" (Varda and
Pai, "Code Mode," verified 2026-08-23), a direct, sourced limit on the
technique's own benefit.

## 11. Failure modes and misuse

This entry explicitly checked the fetched source for a named failure mode
or misuse case and did not find one. Cloudflare's own post describes the
sandbox's isolation guarantee, per dimension 5, as the reason arbitrary
generated code can run safely, but does not name a case where that
isolation is insufficient or where the technique itself misleads a model
into a wrong result. this entry reports that absence directly rather than
inventing a plausible-sounding failure mode the source does not state.

## 12. Trade-off matrix

| Dimension | Code Mode | Standard tool calling |
|---|---|---|
| Round trips for a multi-step task | One, for the whole generated program, dimension 7 | One per individual tool call, dimension 2 |
| Intermediate data location | Stays inside the sandbox, dimension 7 | Passes through the model's own context, dimension 2 |
| Reliability of the call syntax itself | Ordinary code the model has seen a vast corpus of, dimension 3 | Structured tool-call syntax, stated as less reliable, dimension 3 |
| Large result the model must reason about | No benefit, still enters context, dimension 10 | Same, enters context either way |
| Underlying platform maturity | Closed beta at time of writing, now a documented platform primitive, dimension 9 | Broadly available today |

## 13. Related and incompatible patterns

This entry explicitly checked whether Cloudflare's own post compares Code
Mode to the classic Command pattern, which also turns an operation into a
callable, executable unit, and confirmed the post does not draw that
comparison anywhere in the fetched text. this entry reports that absence
directly rather than asserting a bridge the source itself never states.

## 14. Refactoring path in and out

This entry explicitly checked the fetched source for a documented
migration path from standard tool calling to Code Mode, or an explicit
off switch, and did not find either described. the post frames the two as
alternative usage modes for the same underlying MCP tool set rather than a
staged migration with its own named steps, and this entry reports that
directly.

## 15. Testing and verification

This entry explicitly checked the fetched source for a testing or
verification recommendation specific to this technique and did not find
one. the sandbox's own isolation guarantee, per dimension 5, is the
closest safety-relevant claim in the post, but it is a runtime isolation
property, not a test methodology, and this entry reports that distinction
directly rather than overstating the match.

## 16. Observability signals

This entry explicitly checked the fetched source for a named metric,
log field, or dashboard specific to this technique and did not find one.
this entry reports that absence directly rather than inventing an
observability surface the source does not describe.

## 17. Security and privacy implications

Cloudflare's own text states the sandbox's isolation guarantee directly,
already quoted in dimension 5, no network or filesystem access except
through the specific tool bindings granted. Cloudflare's own current
documentation for the underlying primitive independently confirms a
network-level control on top of that isolation. "network access. intercept
or block Internet access for outbound requests" (Cloudflare, "Dynamic
Workers Overview," verified 2026-08-23). together these are the strongest,
directly sourced security claims in the fetched material, and this entry
reports them as the isolation boundary the technique relies on for running
model-generated, untrusted code safely.

## 18. References

1. Kenton Varda and Sunil Pai, "Code Mode. the better way to use MCP,"
   Cloudflare blog, 2025-09-26,
   https://blog.cloudflare.com/code-mode/,
   verified 2026-08-23.
2. Model Context Protocol, "Tools,"
   https://modelcontextprotocol.io/docs/concepts/tools, verified
   2026-08-23.
3. Cloudflare, "Dynamic Workers Overview,"
   https://developers.cloudflare.com/workers/runtime-apis/bindings/worker-loader/,
   verified 2026-08-23.

## Code

TypeScript, Python, and Go implementations of a minimal sandboxed runner
following the mechanism from dimensions 5 through 7, exposing a fixed set
of tool functions to a generated program and returning only the final
result, never the intermediate calls, to the caller.

```typescript
type ToolFn = (input: string) => string;

class SandboxRunner {
  private tools = new Map<string, ToolFn>();

  registerTool(name: string, fn: ToolFn): void {
    this.tools.set(name, fn);
  }

  runProgram(steps: Array<{ tool: string; input: string }>): string {
    let lastResult = "";
    for (const step of steps) {
      const fn = this.tools.get(step.tool);
      if (!fn) {
        throw new Error("unknown tool: " + step.tool);
      }
      lastResult = fn(step.input);
    }
    return lastResult;
  }
}
```

```python
from typing import Callable, Dict, List, TypedDict


class Step(TypedDict):
    tool: str
    input: str


class SandboxRunner:
    def __init__(self) -> None:
        self._tools: Dict[str, Callable[[str], str]] = {}

    def register_tool(self, name: str, fn: Callable[[str], str]) -> None:
        self._tools[name] = fn

    def run_program(self, steps: List[Step]) -> str:
        last_result = ""
        for step in steps:
            fn = self._tools.get(step["tool"])
            if fn is None:
                raise ValueError("unknown tool: " + step["tool"])
            last_result = fn(step["input"])
        return last_result
```

```go
package sandboxrunner

import "fmt"

type ToolFn func(input string) string

type Step struct {
	Tool  string
	Input string
}

type SandboxRunner struct {
	tools map[string]ToolFn
}

func NewSandboxRunner() *SandboxRunner {
	return &SandboxRunner{tools: make(map[string]ToolFn)}
}

func (r *SandboxRunner) RegisterTool(name string, fn ToolFn) {
	r.tools[name] = fn
}

func (r *SandboxRunner) RunProgram(steps []Step) (string, error) {
	lastResult := ""
	for _, step := range steps {
		fn, ok := r.tools[step.Tool]
		if !ok {
			return "", fmt.Errorf("unknown tool: %s", step.Tool)
		}
		lastResult = fn(step.Input)
	}
	return lastResult, nil
}
```
