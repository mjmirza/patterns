---
name: Hook-Based Safety Guard Rails
slug: hook-based-safety-guard-rails
family: 17-ai-agentic
category: AI Agentic
aliases: [PreToolUse Hooks, Deterministic Agent Guardrails]
first_described: "Anthropic's own Claude Code hooks reference documentation"
maturity: established
related: [filesystem-based-agent-state]
incompatible_with: []
verified: 2026-08-23
---

# Hook-Based Safety Guard Rails

## 1. Name, aliases, and lineage

A hook-based safety guard rail is a deterministic shell command an agent
runtime runs at a fixed lifecycle point, before or after a tool call, that
can inspect the pending action and allow, deny, or escalate it, so a rule
is enforced by code rather than by hoping the model chooses to follow it.

This entry sources it directly from Anthropic's own Claude Code
documentation, fetched live. "hooks are user-defined shell commands. Claude
Code runs them at specific points in its lifecycle, which gives you
deterministic control. certain actions always happen rather than relying
on the LLM to choose to run them. Use hooks to enforce project rules,
automate repetitive tasks, and integrate Claude Code with your existing
tools" (Anthropic, "Automate actions with hooks," Claude Code
documentation, https://code.claude.com/docs/en/hooks-guide, verified
2026-08-23).

## 2. Problem and context

The chapter's own text states the underlying problem directly, already
quoted in dimension 1. an instruction given only to the model, in a system
prompt or a rule file, is a request the model can forget, misjudge, or be
argued out of. a hook removes that dependency for the specific rules it
encodes, because the shell command runs every time the matching event
fires, regardless of what the model currently believes about the task.

## 3. Forces

Anthropic's own text draws the exact line between what a hook should
encode and what should stay with the model. "for decisions that require
judgment rather than deterministic rules, you can also use prompt-based
hooks or agent-based hooks that use a Claude model to evaluate conditions"
(Anthropic, "Automate actions with hooks," verified 2026-08-23). the
tension is between certainty and flexibility, a plain shell-command hook
is fast and always fires the same way on the same input, but only for a
rule that can be expressed as code, while a judgment call still needs a
model in the loop.

## 4. Applicability and non-applicability

Anthropic's own text names an explicit default that bounds how much
protection a hook actually provides, and this is the single most important
applicability caveat in the fetched material. "a timed-out command, http,
or mcp_tool hook doesn't block the tool call. the call continues through
the normal permission flow, so don't count on a stalled hook to act as a
gate" (Anthropic, "Hooks reference," Claude Code documentation,
https://code.claude.com/docs/en/hooks, verified 2026-08-23), stated
directly as a design boundary, not a bug, a hook that hangs is not a
substitute for a hard gate.

## 5. Structure

Anthropic's own text names the return-value contract directly. "with a
parsed object that fails schema validation... it's the same non-blocking
error as on exit 0. the action proceeds" and "for most hook events, exit
code 2 is the only exit code that blocks through the code alone. without
valid JSON on stdout, Claude Code treats exit code 1 as a non-blocking
error and proceeds with the action, even though 1 is the conventional Unix
failure code" (Anthropic, "Hooks reference," verified 2026-08-23). the
structured permission-decision shape is a fixed JSON object. "hookSpecificOutput,
hookEventName, permissionDecision, permissionDecisionReason," where
`permissionDecision` "accepts allow, deny, or ask" (same source).

## 6. ASCII structure diagram

```
  a PreToolUse-gated tool call:

  agent proposes a tool call
              |
              v
  +--------------------------+
  | matching hook command     |
  | runs, inspects the call    |
  +--------------------------+
              |
   -----------+-----------------------------
   |          |                            |
   v          v                            v
  exit 0    exit 2                exit 1 or timeout or
  or a      BLOCKS               malformed JSON
  JSON      unconditionally,       (a stalled or
  "allow"   even over a JSON        crashed hook)
              "allow"                     |
   |                                       v
   v                            action PROCEEDS anyway,
  action proceeds               the default is FAIL OPEN
```

## 7. Dynamics

Anthropic's own text names each hook event's blocking behavior directly,
already partially quoted in dimension 5. "PreToolUse, Yes, Blocks the tool
call" (Anthropic, "Hooks reference," verified 2026-08-23), meaning the
runtime path is, the hook process runs synchronously, its exit code and
any JSON on stdout are read, and only an explicit exit 2 is guaranteed to
stop the action regardless of what JSON accompanied it.

## 8. Implementation variants

Cursor documents a directly comparable, independently confirmed mechanism
with the identical default. "by default, hook failures, crash, timeout,
invalid JSON, allow the action through, fail-open. this applies broadly to
command-based hooks unless explicitly configured otherwise" (Cursor,
"Hooks," Cursor documentation, https://cursor.com/docs/agent/hooks,
verified 2026-08-23), matching Anthropic's own default from dimension 4
independently. Cursor's own permission shape matches Anthropic's three-way
decision too. "beforeShellExecution, beforeMCPExecution, preToolUse, and
beforeReadFile" each return a response with "permission, allow, deny, or
ask" (same source). Cursor's own variant adds a named, explicit reversal of
the default this entry did not find documented on Anthropic's side. "set
failClosed. true on the hook definition to block the action on failure
instead... recommended for security-critical beforeMCPExecution hooks" and
"this applies to beforeReadFile operations" too (same source).

## 9. Known production uses

Claude Code and Cursor are each real, currently shipping products using
this exact mechanism, confirmed directly against each vendor's own live
documentation under dimensions 1 and 8.

## 10. Consequences

The benefit is stated directly, already quoted in dimension 1 and 2, a
rule enforced by code fires every time, not only when the model remembers
to apply it. the cost is the fail-open default itself, named independently
by both vendors under dimensions 4 and 8, a crashed, timed-out, or
malformed hook is not a gate, it is a rule that silently stopped applying.

## 11. Failure modes and misuse

The sharpest, most directly sourced failure mode is treating a hook that
has never been observed to fail-closed as a hard security boundary. both
vendors state the same default plainly, per dimensions 4 and 8, so a
security-critical rule built as an ordinary hook, with no opt-in reversal
of the default, degrades to no rule at all the moment its own process
crashes or hangs. Cursor's own text names the direct fix for its own
platform, `failClosed`, restricted specifically to security-critical
operations, per dimension 8. this entry did not find a symmetrically named
opt-in on Anthropic's own fetched pages, and reports that as an honest gap
rather than assuming Claude Code offers the identical named setting.

## 12. Trade-off matrix

| Dimension | Hook-based guard rail | Instruction to the model only |
|---|---|---|
| Fires on every matching event | Yes, deterministically, dimension 2 | No, depends on the model choosing to follow it |
| Default on crash or timeout | Fail open, action proceeds, dimension 4 and 8 | Not applicable |
| Can be made to fail closed | Yes on Cursor, named opt-in, dimension 8. not confirmed on Anthropic's side | Not applicable |
| Suited to a judgment call | No, per dimension 3 | Yes |
| Blocking guarantee | Only a specific exit code, dimension 5 | None |

## 13. Related and incompatible patterns

This catalogue's own Filesystem-Based Agent State entry is the direct,
sourced bridge, already quoted under that entry's own dimension 4 and 11.
"Claude treats them as context, not enforced configuration. to block an
action regardless of what Claude decides, use a PreToolUse hook instead"
(Anthropic, "Give Claude persistent memory," Claude Code documentation,
verified 2026-08-23), naming this exact pattern as the enforcement
mechanism a saved memory note is explicitly NOT.

## 14. Refactoring path in and out

This entry explicitly checked the fetched sources for a documented,
staged migration from an instruction-only rule to a hook-enforced one, or
an explicit off switch for a single hook, and did not find a formal,
staged process described on either vendor's page. removing a hook is, on
both platforms, removing or disabling its entry in the settings file that
registers it, per the configuration examples already quoted in dimensions
5 and 8, rather than a named migration procedure.

## 15. Testing and verification

This entry explicitly checked both fetched sources for a documented test
methodology specific to a hook's own correctness and did not find one
beyond running the hook manually against a crafted input. Anthropic's own
worked example, already partially quoted in dimension 5, shows the
verification shape directly, a hook script that checks a condition and
either prints the `permissionDecision` JSON or exits 0 with no decision,
which a test would exercise against both a triggering and a non-triggering
input.

## 16. Observability signals

This entry explicitly checked both fetched sources for a named metric or
dashboard specific to hook execution and did not find one. the closest
directly sourced signal is the non-blocking error notice Anthropic's own
text names. "the action proceeds, and the hook name hook error notice
carries the validation message" (Anthropic, "Hooks reference," verified
2026-08-23), a per-invocation error surface rather than an aggregate
metric.

## 17. Security and privacy implications

The fail-open default named independently by both vendors, per dimensions
4 and 8, is the central security implication of this pattern. a hook
written to enforce a security-critical rule is not a hard boundary unless
it is explicitly configured to fail closed, where that option exists, and
Cursor's own text states which of its own hook types this applies to
directly, `beforeMCPExecution` and `beforeReadFile`, per dimension 8.

## 18. References

1. Anthropic, "Automate actions with hooks," Claude Code documentation,
   https://code.claude.com/docs/en/hooks-guide, verified 2026-08-23.
2. Anthropic, "Hooks reference," Claude Code documentation,
   https://code.claude.com/docs/en/hooks, verified 2026-08-23.
3. Cursor, "Hooks," Cursor documentation,
   https://cursor.com/docs/agent/hooks, verified 2026-08-23.

## Code

TypeScript, Python, and Go implementations of a minimal PreToolUse gate
following the mechanism from dimensions 5 through 7, defaulting to fail
open on an unhandled error and returning an explicit allow, deny, or ask
decision otherwise.

```typescript
type Decision = "allow" | "deny" | "ask";

interface HookResult {
  permissionDecision: Decision;
  permissionDecisionReason?: string;
}

function runGuard(command: string, check: (cmd: string) => HookResult | null): HookResult {
  try {
    const result = check(command);
    if (result === null) {
      return { permissionDecision: "allow" };
    }
    return result;
  } catch {
    return { permissionDecision: "allow", permissionDecisionReason: "guard errored, fail open" };
  }
}
```

```python
from typing import Callable, Optional, TypedDict


class HookResult(TypedDict, total=False):
    permission_decision: str
    permission_decision_reason: str


def run_guard(command: str, check: Callable[[str], Optional[HookResult]]) -> HookResult:
    try:
        result = check(command)
        if result is None:
            return {"permission_decision": "allow"}
        return result
    except Exception:
        return {
            "permission_decision": "allow",
            "permission_decision_reason": "guard errored, fail open",
        }
```

```go
package guard

type HookResult struct {
	PermissionDecision       string
	PermissionDecisionReason string
}

func RunGuard(command string, check func(string) *HookResult) (result HookResult) {
	defer func() {
		if r := recover(); r != nil {
			result = HookResult{
				PermissionDecision:       "allow",
				PermissionDecisionReason: "guard errored, fail open",
			}
		}
	}()
	if r := check(command); r != nil {
		return *r
	}
	return HookResult{PermissionDecision: "allow"}
}
```
