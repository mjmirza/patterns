---
name: Game Loop
slug: game-loop
family: 29-realtime-simulation
category: Real-Time Simulation
aliases: [Main Loop, Core Loop, Fixed Timestep Loop]
first_described: "Glenn Fiedler, Fix Your Timestep!, gafferongames.com, June 10, 2004; formalized as a named pattern by Robert Nystrom in Game Programming Patterns"
maturity: canonical
related: []
incompatible_with: []
verified: 2026-08-23
---

# Game Loop

## 1. Name, aliases, and lineage

A game loop is the top-level control structure of a real-time simulation.
process input, advance the simulation state, render the current state,
repeat, for as long as the program runs. It is also called a main loop or a
core loop, and the specific, more disciplined variant this entry focuses on
is the fixed timestep loop.

The clearest, directly verified lineage runs through two sources this entry
fetched live. Glenn Fiedler's own article, dated June 10, 2004, is the
widely cited origin of the accumulator technique this pattern is built
around (Fiedler, Glenn, "Fix Your Timestep!," Gaffer On Games,
https://gafferongames.com/post/fix_your_timestep/, verified 2026-08-23).
Robert Nystrom's own book names Fiedler's article directly as its own
foundation. "The classic article on game loops is Glenn Fiedler's Fix Your
Timestep. This chapter would not be the same without it" (Nystrom, Robert,
"Game Loop," Game Programming Patterns,
https://gameprogrammingpatterns.com/game-loop.html, verified 2026-08-23).
Nystrom's own book places the chapter in Part II, Sequencing Patterns,
alongside Double Buffer and Update Method (Nystrom, Robert, "Game
Programming Patterns," table of contents,
https://gameprogrammingpatterns.com/contents.html, verified 2026-08-23).

So the lineage is a clean two-step chain. Fiedler's 2004 practitioner
article supplies the technique, Nystrom's book formalizes it as a named,
catalogued pattern. this entry treats both as primary sources rather than
picking one over the other.

## 2. Problem and context

A naive loop that simulates and renders as fast as the hardware allows ties
the simulation's own speed to whatever machine it happens to run on. a
faster machine simulates faster, physics behaves differently frame to frame,
and the same recorded input produces a different outcome on different
hardware. Nystrom states the intent this pattern answers directly.
"Decouple the progression of game time from user input and processor speed"
(Nystrom, "Game Loop," verified 2026-08-23). this problem shows up in any
software that repeatedly advances an internal state and presents it to a
person. games, physics or particle simulations, and any near-real-time
visualization that must behave the same way regardless of how fast the
machine driving it happens to be.

## 3. Forces

Fiedler's own article names the central tension. there are several genuinely
different ways to advance time each frame, and each carries a real
trade-off between simplicity and determinism (Fiedler, "Fix Your Timestep!,"
verified 2026-08-23). A variable timestep, where each frame simply measures
how much real time elapsed and advances the simulation by exactly that
amount, is the simplest possible loop. It is also, per Nystrom's own stated
conclusion, the source of the real problem. "It makes gameplay
non-deterministic and unstable. And this is the real problem, of course.
Physics and networking in particular become much harder with a variable
time step" (Nystrom, "Game Loop," verified 2026-08-23).

The opposing force is the cost of the fix. decoupling the simulation rate
from the render rate through a fixed timestep plus an accumulator is more
complex to implement and reason about than the naive variable loop.
Nystrom's own text names this cost plainly. "It is more complex. The main
downside is there is a bit more going on in the implementation" (Nystrom,
"Game Loop," verified 2026-08-23). The pattern exists because, for anything
whose behaviour must be reproducible, deterministic under recorded input, or
predictable across hardware, that added complexity buys back exactly the
guarantee a variable timestep gives up.

## 4. Applicability and non-applicability

A fixed timestep game loop applies whenever the simulation's own physics or
game logic must be deterministic. reproducible under a recorded input
stream, stable under a physics engine tuned to a specific step size, or
consistent across two machines running the same networked simulation.
Nystrom's own text names determinism as the reason the added complexity of
the accumulator pattern is usually worth it, since a variable step "makes
gameplay non-deterministic and unstable" (Nystrom, "Game Loop," verified
2026-08-23), which directly threatens physics stability, recorded-replay
correctness, and any peer-to-peer networking scheme that assumes identical
simulation results from identical input.

The pattern is a poor fit, or unnecessary complexity, for software with no
such determinism requirement. a simple animation, a UI transition, or a
visualization with no physics engine to destabilize and no networked or
replay-based correctness requirement can run a plain variable timestep loop
without the accumulator's added bookkeeping. this entry did not find a
source stating this non-applicable case explicitly. it is a direct
consequence of Nystrom's own stated rationale for why the pattern exists,
read in the negative, and is reported here as this entry's own reasoned
inference rather than a directly sourced claim.

## 5. Structure

Both primary sources converge on the same four-part shape. measure how much
real time passed since the last iteration, accumulate it, drain the
accumulator in fixed-size steps calling the simulation update once per step,
then render whatever the current state is. Nystrom's own code, quoted
directly, shows the shape.

quote:
double previous = getCurrentTime();
double lag = 0.0;
while (true) {
   double current = getCurrentTime();
   double elapsed = current - previous;
   previous = current;
   lag += elapsed;

   processInput();

   while (lag >= MS_PER_UPDATE)
   {
     update();
     lag -= MS_PER_UPDATE;
   }

   render();
}
end quote

(Nystrom, "Game Loop," "Play Catch Up" section, verified 2026-08-23).

Fiedler's own code names the same accumulator by a different variable name
and integrates a physics state directly.

quote:
while ( accumulator >= dt )
{
    integrate( state, t, dt );
    accumulator -= dt;
    t += dt;
}
end quote

(Fiedler, "Fix Your Timestep!," "Free the physics" section, verified
2026-08-23). Fiedler's own `accumulator` is functionally identical to
Nystrom's `lag`. both hold the leftover real time not yet consumed by a
whole simulation step, and both drain it in a while loop bounded by the
fixed step size.

## 6. ASCII structure diagram

```
  loop start
       |
       v
  measure elapsed real time since last iteration
       |
       v
  accumulator += elapsed
       |
       v
  process input
       |
       v
  +---------------------------+
  | while accumulator >= dt   |
  |   update(dt)              |  <- fixed-size simulation step
  |   accumulator -= dt       |
  +---------------------------+
       |
       v
  render(interpolate(accumulator / dt))
       |
       v
  loop repeats
```

## 7. Dynamics

Each iteration, the accumulator drains in whole fixed-size steps. if a
frame's real elapsed time is larger than one step, the inner while loop runs
the simulation update more than once before rendering, and if it is smaller,
the accumulator simply carries the leftover fraction into the next
iteration. Rendering never runs inside that inner loop, which is the
structural decoupling Nystrom names directly. "yanked rendering out of the
update loop" (Nystrom, "Game Loop," verified 2026-08-23), so the simulation
advances at a constant, predictable rate while the render call happens once
per outer iteration regardless of how many inner update steps just ran.

Because the render call can land at a point between two simulation steps,
the state on screen is, strictly, always slightly behind the true simulation
time by whatever fraction of a step the accumulator has not yet drained.
Fiedler's own fix for the resulting visual stutter is to interpolate the
rendered state between the previous and current simulation states, blended
by the fraction the accumulator represents of one whole step (Fiedler, "Fix
Your Timestep!," verified 2026-08-23).

Nystrom's own text separately discusses who owns the outer loop itself. a
platform's own event loop calling into the game's code, or the game writing
and owning its own loop directly. the platform-owned form gives up timing
control in exchange for never having to write or optimize the loop, while
the self-owned form gives total control at the cost of doing that work
yourself (Nystrom, "Game Loop," verified 2026-08-23).

## 8. Implementation variants

Godot Engine's own current documentation confirms a real, shipping
implementation of the fixed timestep pattern. "The physics engine runs at a
fixed rate (a default of 60 iterations per second)," which "is typically
different from the frame rate which fluctuates based on what is rendered and
available resources," and Godot's own physics callback receives a delta
value that stays constant at that fixed rate (Godot Engine, "Physics
introduction," https://docs.godotengine.org/en/stable/tutorials/physics/physics_introduction.html,
verified 2026-08-23). this is a direct, current, citable production instance
of decoupling simulation rate from render rate.

A commonly repeated claim, that id Software's Quake ran its simulation on a
fixed 60Hz tick, does not hold up against Quake's own published source code.
this entry fetched id Software's own historical WinQuake release directly
rather than relying on the popular claim. `Host_FilterTime`, in `host.c`,
clamps a variable frame time rather than fixing it to a constant step.

quote:
if (host_framerate.value > 0)
    host_frametime = host_framerate.value;
else
{
    if (host_frametime > 0.1)
        host_frametime = 0.1;
    if (host_frametime < 0.001)
        host_frametime = 0.001;
}
end quote

(id Software, `WinQuake/host.c`,
https://github.com/id-Software/Quake/blob/master/WinQuake/host.c, verified
2026-08-23), and physics functions in `sv_phys.c` consume that same variable,
clamped `host_frametime` value directly rather than a fixed step (id
Software, `WinQuake/sv_phys.c`,
https://github.com/id-Software/Quake/blob/master/WinQuake/sv_phys.c, verified
2026-08-23). Quake's real architecture is a variable timestep bounded
between 0.001 and 0.1 seconds, not the fixed accumulator pattern this entry
otherwise describes. this entry reports the correction plainly rather than
repeating the unverified popular claim.

## 9. Known production uses

Godot Engine ships the fixed timestep pattern as a first-class, documented
feature of its physics system, defaulting to 60 fixed iterations per second
and exposing a dedicated physics-process callback distinct from its
variable-rate render callback, per dimension 8's citation. this is a real,
current, widely used open-source game engine, not a toy example.

Quake, per dimension 8's corrected finding, is a real, shipped, historically
significant production use of a RELATED but distinct approach, a variable
timestep clamped to a bounded range rather than a fixed accumulator step.
this entry reports it here specifically to correct the popular but
unverified claim that Quake used a fixed 60Hz tick, rather than to claim it
as an example of the accumulator pattern this entry otherwise describes.

Glenn Fiedler's own article is itself evidence of the pattern's real-world
currency. it is written from hands-on professional game-development
experience and remains, per its citation by Nystrom's own book, the
practitioner community's reference article on the topic, cited directly
rather than through a secondary summary (Fiedler, "Fix Your Timestep!,"
verified 2026-08-23).

## 10. Consequences

The pattern buys determinism at the cost of implementation complexity, per
dimension 3's stated tension. once the simulation runs on a fixed step, the
same recorded input sequence produces the same output sequence regardless of
the machine's actual frame rate, which is exactly what a physics engine
tuned to one step size, a recorded replay system, or a networked simulation
assuming identical results from identical input all require to work
correctly.

The trade is not free. the render call, per dimension 7, always lags the
true simulation time by some fraction of a step, which either shows as
visible micro-stutter or must be hidden by interpolating between the
previous and current simulation states, an extra piece of work Fiedler's own
article treats as a necessary follow-on to the accumulator technique itself
(Fiedler, "Fix Your Timestep!," verified 2026-08-23) rather than an optional
polish step.

A second, more serious consequence appears when the fixed step itself
becomes expensive to compute, described fully as a failure mode in dimension
11. the same mechanism that buys determinism, an inner loop that keeps
consuming fixed steps until the accumulator drains, has no upper bound on
how many steps it will run in a single outer iteration if the machine falls
behind.

## 11. Failure modes and misuse

The canonical, named failure mode is Fiedler's own coinage, the spiral of
death. "It's called the spiral of death because being behind causes your
update to simulate more steps to catch up, which causes you to fall further
behind, which causes you to simulate more steps" (Fiedler, "Fix Your
Timestep!," verified 2026-08-23). this entry explicitly checked whether
Nystrom's own chapter uses the same term and confirmed it does not. the term
is Fiedler's, and Nystrom's chapter discusses the same underlying
falling-behind problem under its own design-decisions comparison without
naming it a spiral of death. the failure condition itself, regardless of
name, is real and mechanical. if a single simulation step takes longer to
compute than the step's own fixed duration represents in real time, the
accumulator can never fully drain, and each outer iteration adds more
pending steps than it removes, so the game locks into ever-increasing
catch-up work rather than recovering.

A second, quieter misuse is applying the full fixed-step accumulator pattern
to software with no genuine determinism requirement, per dimension 4's
reasoned, unsourced boundary. the pattern's own stated cost, per dimension
3, is real implementation complexity, and paying that cost where nothing
downstream actually needs bit-for-bit reproducibility is unnecessary
overhead rather than a correctness improvement.

## 12. Trade-off matrix

| Dimension | Fixed step plus accumulator | Plain variable timestep |
|---|---|---|
| Determinism across hardware | Guaranteed, per dimension 4 | Not guaranteed, per dimension 3's cited downside |
| Physics engine stability | Stable, tuned to one known step size | Can destabilize as frame time varies |
| Implementation complexity | Higher, per Nystrom's own stated downside | Lower, the naive loop |
| Behavior when a step is slow | Bounded risk of the spiral of death, dimension 11 | Simply runs slower, no catch-up debt |
| Rendering smoothness | Needs interpolation to hide the step lag, dimension 7 | Renders exactly the latest computed state |
| Networked or replay determinism | Directly supports it | Undermines it |

## 13. Related and incompatible patterns

Game Loop is closely, directly related to this catalogue's own
Entity-Component-System entry, and the connection is not this entry's own
inference. Nystrom's own book bridges the two through a third chapter,
Update Method, placed in the same Part II, Sequencing Patterns, section as
Game Loop itself. Update Method's own stated intent is to "Simulate a
collection of independent objects by telling each to process one frame of
behavior at a time," and it names both sides of the bridge directly.
"Naturally, Game Loop is another pattern in this book," and, on the
Component side, "If you are already using the Component pattern, this is a
no-brainer. It lets each component update itself independently" (Nystrom,
Robert, "Update Method," https://gameprogrammingpatterns.com/update-method.html,
verified 2026-08-23). the mechanical link is a single sentence. "Once per
frame, the game loop walks the collection and calls update() on each
object" (Nystrom, "Update Method," verified 2026-08-23). so the fixed-step
inner loop this entry describes in dimension 5 is exactly the per-frame walk
that, in an Entity-Component-System, invokes each system over its matching
components.

Game Loop is also related to this catalogue's own Spatial Partitioning
entry as a practical pairing, not a documented one. this entry explicitly
checked Nystrom's own Spatial Partition chapter's "See Also" section for a
cross-reference to Game Loop and confirmed one is not present. the pairing,
rebuilding or querying a spatial partition once per simulation step, is a
real, reasoned engineering practice this entry reports as inferred rather
than sourced.

Game Loop has no directly incompatible pattern named in the sourced
material. its own two structural variants, platform-owned versus
self-owned, and fixed-no-sync versus fixed-with-sync versus variable versus
fixed-update-variable-render, per dimension 7 and the trade-off matrix in
dimension 12, are alternative implementations of the same problem rather
than incompatible patterns.

## 14. Refactoring path in and out

Refactoring a plain variable timestep loop into the fixed accumulator
pattern starts by separating the render call out of whatever loop currently
also advances simulation state, per dimension 7's structural decoupling.
introduce the accumulator variable, move the simulation update behind an
inner while loop bounded by a fixed step size, and move the render call to
run once per outer iteration after that inner loop drains. Nystrom's own
three communication-shape design decisions do not apply here since Game
Loop has no component-communication concern, but the same incremental
spirit applies. add interpolation for rendering, per Fiedler's own
recommendation, only after the accumulator itself is working and stepping
correctly, since interpolation is a smoothing pass on top of an already
correct fixed-step simulation, not a prerequisite for it.

Refactoring out of the fixed accumulator pattern, back toward a plain
variable timestep loop, is driven by discovering that no genuine
determinism requirement exists for the software in question, per dimension
4's reasoned boundary, or by hitting the spiral of death failure mode from
dimension 11 in a context where the correct fix is reducing the fixed
step's own computational cost rather than removing the fixed-step structure
that exposed the problem. Nystrom's own guidance does not treat "abandon
the fixed step" as the fix for a slow simulation. the accumulator's own
purpose is preserved by making the per-step work cheaper, not by removing
the mechanism that made the slowness visible.

## 15. Testing and verification

The strongest real, citable verification technique for this exact pattern
comes from the rollback-networking community rather than from either
primary source directly. GGPO, a real, still-referenced peer-to-peer
networking library for competitive games, states its own precondition
plainly. "Rollback networking is designed to be integrated into a fully
deterministic peer-to-peer engine. With full determinism, the game is
guaranteed to play out the same way on all players computers if we simply
feed them the same inputs" (GGPO, https://ggpo.net/, verified 2026-08-23).
this is a direct, practical test for whether a fixed timestep loop is
genuinely deterministic. record an input stream, replay it twice, on the
same machine or on two different machines, and assert the resulting
simulation states are identical. a fixed-step loop that fails this test is
not actually delivering the guarantee it exists to provide, regardless of
whether it looks correct in isolation.

Verify the spiral of death failure mode directly, per dimension 11, by
forcing a single simulated step to take longer than its own fixed duration
and asserting the loop either recovers (drains the backlog without
compounding it) or degrades in a bounded, observable way rather than
locking up silently.

Verify the render-side interpolation from dimension 7 separately from
simulation correctness. a test asserting the interpolated render state
falls strictly between the previous and current simulation states,
proportional to the accumulator's remaining fraction, catches an
interpolation bug without needing to also exercise the simulation logic
itself.

## 16. Observability signals

The single most direct signal for this pattern is the accumulator's own
value, sampled once per outer iteration. a value that trends upward over
time, rather than oscillating around a small bound, is a leading indicator
of the spiral of death from dimension 11 before it becomes visible as a
frozen or crawling simulation.

The count of inner simulation steps run per outer iteration is the second
signal, and it directly measures the same condition from a different angle.
one or two steps per frame is healthy. a rising, unbounded step count per
frame is the same warning the accumulator trend line gives, confirmed from a
second measurement.

Per-step simulation time, measured directly rather than inferred, names the
root cause when either of the above signals fires. if the fixed step's own
computational cost approaches or exceeds the fixed step duration itself,
the loop is at genuine risk of falling permanently behind regardless of how
much slack the accumulator currently has.

## 17. Security and privacy implications

A game loop by itself has no direct data-handling surface, so the genuine
security angle is availability rather than confidentiality. the spiral of
death from dimension 11 is a real, mechanical resource-exhaustion risk, and
in a networked context where an attacker can influence what the simulation
must compute each step, whether by spawning excess simulated entities or
triggering an expensive code path, an unbounded catch-up loop becomes a
practical denial-of-service vector against the process running the
simulation. a defensive fixed-step implementation caps the number of
catch-up steps run in a single outer iteration, deliberately trading
strict determinism for availability when the machine has fallen too far
behind to recover the normal way, rather than letting the inner loop run
unbounded.

The determinism property this pattern provides, per dimension 15's GGPO
citation, is itself a trust boundary in a peer-to-peer networked context.
GGPO's own stated precondition, that all peers must compute identical
results from identical input, means any peer whose simulation state
diverges, whether from a genuine bug or a deliberately modified client, is
indistinguishable at the network layer from a legitimate desync until a
checksum or state comparison catches it. this entry did not find a source
describing a general solution to that specific trust problem and reports it
as a genuine, unaddressed gap rather than asserting a mitigation.

## 18. References

1. Fiedler, Glenn, "Fix Your Timestep!," Gaffer On Games,
   https://gafferongames.com/post/fix_your_timestep/, dated June 10, 2004,
   verified 2026-08-23.
2. Nystrom, Robert, "Game Loop," Game Programming Patterns,
   https://gameprogrammingpatterns.com/game-loop.html, verified 2026-08-23.
3. Nystrom, Robert, "Game Programming Patterns," table of contents,
   https://gameprogrammingpatterns.com/contents.html, verified 2026-08-23.
4. Godot Engine, "Physics introduction,"
   https://docs.godotengine.org/en/stable/tutorials/physics/physics_introduction.html,
   verified 2026-08-23.
5. id Software, "WinQuake/host.c," Quake source release,
   https://github.com/id-Software/Quake/blob/master/WinQuake/host.c,
   verified 2026-08-23.
6. id Software, "WinQuake/sv_phys.c," Quake source release,
   https://github.com/id-Software/Quake/blob/master/WinQuake/sv_phys.c,
   verified 2026-08-23.
7. Nystrom, Robert, "Update Method," Game Programming Patterns,
   https://gameprogrammingpatterns.com/update-method.html, verified
   2026-08-23.
8. GGPO, https://ggpo.net/, verified 2026-08-23.

## Code

TypeScript, Python, and Go implementations of a fixed timestep game loop
with an accumulator, following Nystrom's and Fiedler's own shape from
dimension 5, plus a bounded catch-up cap to defend against the spiral of
death from dimension 11.

```typescript
type UpdateFn = (dt: number) => void;
type RenderFn = (alpha: number) => void;
type NowFn = () => number;

const MS_PER_UPDATE = 1000 / 60;
const MAX_CATCH_UP_STEPS = 5;

class FixedStepLoop {
  private accumulator = 0;
  private previous: number;
  private running = false;

  constructor(
    private update: UpdateFn,
    private render: RenderFn,
    private now: NowFn = () => performance.now()
  ) {
    this.previous = this.now();
  }

  start(): void {
    this.running = true;
    this.previous = this.now();
    this.tick();
  }

  stop(): void {
    this.running = false;
  }

  private tick = (): void => {
    if (!this.running) return;

    const current = this.now();
    const elapsed = current - this.previous;
    this.previous = current;
    this.accumulator += elapsed;

    let steps = 0;
    while (this.accumulator >= MS_PER_UPDATE && steps < MAX_CATCH_UP_STEPS) {
      this.update(MS_PER_UPDATE);
      this.accumulator -= MS_PER_UPDATE;
      steps += 1;
    }
    if (steps === MAX_CATCH_UP_STEPS) {
      this.accumulator = 0;
    }

    this.render(this.accumulator / MS_PER_UPDATE);
    if (this.running) setTimeout(this.tick, 0);
  };
}
```

```python
import time
from typing import Callable

MS_PER_UPDATE = 1.0 / 60.0
MAX_CATCH_UP_STEPS = 5


class FixedStepLoop:
    def __init__(
        self,
        update: Callable[[float], None],
        render: Callable[[float], None],
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self.update = update
        self.render = render
        self.now = now
        self.accumulator = 0.0
        self.previous = self.now()
        self.running = False

    def start(self) -> None:
        self.running = True
        self.previous = self.now()
        while self.running:
            self._tick()

    def stop(self) -> None:
        self.running = False

    def _tick(self) -> None:
        current = self.now()
        elapsed = current - self.previous
        self.previous = current
        self.accumulator += elapsed

        steps = 0
        while self.accumulator >= MS_PER_UPDATE and steps < MAX_CATCH_UP_STEPS:
            self.update(MS_PER_UPDATE)
            self.accumulator -= MS_PER_UPDATE
            steps += 1
        if steps == MAX_CATCH_UP_STEPS:
            self.accumulator = 0.0

        self.render(self.accumulator / MS_PER_UPDATE)
```

```go
package gameloop

import "time"

const (
	msPerUpdate     = time.Second / 60
	maxCatchUpSteps = 5
)

type UpdateFn func(dt time.Duration)
type RenderFn func(alpha float64)

type FixedStepLoop struct {
	update      UpdateFn
	render      RenderFn
	accumulator time.Duration
	previous    time.Time
	running     bool
}

func New(update UpdateFn, render RenderFn) *FixedStepLoop {
	return &FixedStepLoop{update: update, render: render}
}

func (l *FixedStepLoop) Start() {
	l.running = true
	l.previous = time.Now()
	for l.running {
		l.tick()
	}
}

func (l *FixedStepLoop) Stop() {
	l.running = false
}

func (l *FixedStepLoop) tick() {
	current := time.Now()
	elapsed := current.Sub(l.previous)
	l.previous = current
	l.accumulator += elapsed

	steps := 0
	for l.accumulator >= msPerUpdate && steps < maxCatchUpSteps {
		l.update(msPerUpdate)
		l.accumulator -= msPerUpdate
		steps++
	}
	if steps == maxCatchUpSteps {
		l.accumulator = 0
	}

	alpha := float64(l.accumulator) / float64(msPerUpdate)
	l.render(alpha)
}
```
