---
name: Hardware-in-the-Loop Testing
slug: hardware-in-the-loop-testing
family: 28-embedded-hardware
category: Structural
aliases: [HIL, HIL Simulation, Plant-in-the-Loop Testing]
first_described: "Wikipedia and National Instruments hardware-in-the-loop documentation"
maturity: canonical
related: [interrupt-service-routine, watchdog-timer]
incompatible_with: []
verified: 2026-08-21
---

# Hardware-in-the-Loop Testing

## 1. Name, aliases, and lineage

The canonical name is Hardware-in-the-Loop Testing, the pattern where
real controller hardware, running its real firmware, is connected to
a virtual model of the physical system it would otherwise control,
rather than to the real physical system itself. Wikipedia's own
reference defines the mechanism directly, "hardware-in-the-loop
simulation, also known by various acronyms such as HiL, HITL, and
HWIL, is a technique that is used in the development and testing of
complex real-time embedded systems."

The alias **HIL** is the standard abbreviation used throughout
embedded systems and automotive engineering literature. **HIL
Simulation** names the pattern by its mechanism, the physical system
is simulated rather than real. **Plant-in-the-Loop Testing** names the
pattern by the term control-systems engineering uses for the physical
system being controlled, "the plant."

## 2. Problem and context

An embedded controller's firmware needs to be validated against the
real physical system it will eventually control, such as an engine, a
braking system, or an aircraft actuator, but testing directly against
that real physical system during development is often expensive,
slow, or genuinely dangerous, since a firmware bug under test could
damage costly equipment or injure someone. Hardware-in-the-Loop
Testing solves this by keeping the real controller hardware and real
firmware in the test loop, exactly as it would run in production, but
replacing the real physical system with a real-time software model
that responds to the controller's outputs the way the real system
would. Wikipedia's own reference states the resulting benefit
directly, HIL is preferred over testing on the real physical system
because it avoids "testing at or beyond the range of certain ECU
parameters" that would create hazardous conditions for test
engineers, and because a real plant, such as a jet engine, is
genuinely "more expensive than a high fidelity, real-time simulator."

## 3. Forces

The pattern balances the following competing pressures.

- **Testing the real controller hardware and firmware.** Favored.
  Unlike a pure software simulation of the controller itself, HIL
  keeps the actual controller hardware and its actual compiled
  firmware in the loop, so timing, I/O behavior, and hardware-specific
  bugs are genuinely exercised, not merely modeled.
- **Safety and cost avoidance.** Favored. Wikipedia's own reference
  names this directly, HIL avoids "testing at or beyond the range of
  certain ECU parameters" that would be hazardous, so a firmware bug
  under test cannot damage real physical hardware or endanger anyone,
  per NI's own documented framing of avoiding "damaging expensive or
  dangerous equipment."
- **Availability before physical hardware exists.** Favored. Wikipedia's
  own reference states this directly, HIL lets engineers complete
  roughly "95% of the engine controller testing" before physical
  prototypes become available, allowing real controller validation
  work to start earlier in a
  development schedule.
- **Fidelity of the simulated plant.** Sacrificed. The physical system
  being controlled is, by definition, a model rather than the real
  thing, so any inaccuracy in that model's real-time behavior is a
  real gap between what HIL testing validates and what the genuine
  physical system will actually do.
- **Real-time computational cost.** Sacrificed. NI's own documentation
  names this directly, HIL requires "real-time compute to read, write
  and control the I/O and communication buses deterministically," a
  real, specialized hardware and software cost beyond a simple offline
  simulation.

## 4. Applicability and non-applicability

Reach for Hardware-in-the-Loop Testing when the following hold.

- The real controller's firmware genuinely needs validation against
  realistic physical-system dynamics before the real physical system
  is genuinely available, safe, or affordable to test against
  directly.
- A firmware bug under test could genuinely damage expensive equipment
  or endanger a person if tested directly against the real physical
  system, per NI's own documented risk-avoidance framing.
- The plant's real-time behavior can genuinely be modeled with
  sufficient fidelity in a real-time simulation to make the test
  worth running.

Do NOT reach for Hardware-in-the-Loop Testing in these cases, and the
reason matters more than the rule.

- **The real physical system's behavior genuinely cannot be modeled
  with sufficient fidelity**, per the fidelity-of-the-simulated-plant
  force in dimension 3, a HIL test against a genuinely inaccurate
  model can give false confidence, testing directly against the real
  physical system, where safety and cost allow it, is more trustworthy
  than a poorly-modeled HIL test.
- **The controller's real-time compute and I/O requirements genuinely
  exceed what a HIL test system can deterministically simulate**, per
  NI's own documented deterministic-compute requirement, a controller
  whose real timing demands outpace the available real-time simulation
  hardware needs a different validation strategy, or a more capable
  real-time test platform, before HIL testing can genuinely apply.
- **The system under test genuinely has no real physical plant
  to simulate**, such as a purely data-processing embedded system with
  no real physical actuator or sensor loop, HIL's entire premise, a
  simulated physical system responding to the controller, does not
  apply.

## 5. Structure

Hardware-in-the-Loop Testing has three structural parts.

- **The controller under test**, the real embedded hardware running
  its real, unmodified firmware, exactly as it would run in
  production.
- **The plant simulation**, the real-time software model of the
  physical system, Wikipedia's own reference describing it directly
  as "a mathematical representation of all related dynamic systems,"
  representing the real complexity of "the process-actuator system"
  the controller would otherwise be connected to.
- **The I/O interface**, the real electrical and communication
  connections, analog and digital signals and protocols such as CAN
  or Ethernet, joining the controller's real inputs and outputs to the
  plant simulation, per NI's own documented deterministic real-time
  compute requirement.

## 6. ASCII structure diagram

```
  +------------------+      real I/O       +--------------------+
  |  controller under  |  <-------------->  |  plant simulation     |
  |  test, real hardware  |     signals        |  real-time software     |
  |  real firmware        |                    |  models the physical    |
  +------------------+                     |  system's response      |
                                            +--------------------+
```

## 7. Dynamics

The trace below shows one complete control-and-respond cycle.

```
The controller under test produces an output

the real controller, running its real firmware, computes an output
signal based on its current inputs, exactly as it would in production
   |-- that output is sent over the real I/O interface to the plant
       simulation

The plant simulation responds in real time

the real-time test system computes the mathematical representation of
the plant's dynamics, per Wikipedia's own documented description of
the plant simulation from dimension 5
   |-- it computes what the real physical system would genuinely do
       in response to that output
   |-- it sends the resulting simulated sensor values back to the
       controller over the same real I/O interface, within the real
       controller's own actual timing expectations

The cycle repeats continuously

the controller reads the simulated sensor values as if they came from
the real physical system, and produces its next output based on them,
so the entire closed control loop runs exactly as it would in
production, with only the physical system itself replaced by its
real-time model
```

## 8. Implementation variants

**Signal-level HIL.** The real controller's electrical inputs and
outputs, analog and digital signals, are connected directly to the
real-time simulation hardware, the closest possible match to how the
controller would be wired in the real physical system.

**Bus-level HIL.** The controller communicates with the plant
simulation over a real communication protocol, such as CAN or
Ethernet, rather than
individual discrete signals, suited to a controller whose real
interface to the physical system is itself bus-based.

**Full-vehicle or full-system HIL.** Multiple real controllers, each
with their own real firmware, are connected simultaneously to one
shared, larger plant simulation, testing the genuine interaction
between several real controllers against one consistent, real-time
model of the complete physical system.

## 9. Known production uses

**Wikipedia's own reference, defining the HIL mechanism and its
safety, cost, and early-availability benefits.** The reference states
this directly. "Hardware-in-the-loop simulation, also known by
various acronyms such as HiL, HITL, and HWIL, is a technique that is
used in the development and testing of complex real-time embedded
systems." The plant is "represented through a mathematical
representation of all related dynamic systems." HIL avoids "testing
at or beyond the range of certain ECU parameters" that would be
hazardous, proves economical when "the plant is more expensive than a
high fidelity, real-time simulator," and allows roughly "95% of the
engine controller testing" to complete before physical prototypes
become available. Wikipedia,
"Hardware-in-the-loop simulation,"
https://en.wikipedia.org/wiki/Hardware-in-the-loop_simulation,
verified 2026-08-21.

**National Instruments' own documentation, on the real-time
determinism requirement and the risk this pattern exists to avoid.**
NI states this directly. HIL systems require "real-time compute to
read, write and control the I/O and communication buses
deterministically." The methodology exists specifically to avoid
"damaging expensive or dangerous equipment" that direct physical
testing would risk. National Instruments, "What Is Hardware-in-the-
Loop (HIL)?,"
https://www.ni.com/en/solutions/transportation/hardware-in-the-loop/what-is-hardware-in-the-loop-.html,
verified 2026-08-21.

## 10. Consequences

Positive.

- The real controller hardware and its real, unmodified firmware are
  genuinely exercised, catching hardware-specific and timing-related
  bugs a pure software simulation of the controller would miss.
- Expensive or dangerous physical equipment is never put at risk
  during firmware validation, per NI's own documented risk-avoidance
  framing.
- Testing can genuinely begin before the real physical system exists
  or is available, per Wikipedia's own documented early-availability
  benefit, shortening the real development schedule.

Negative.

- The plant simulation's real fidelity is never perfect, a real gap
  between what HIL testing validates and what the genuine physical
  system will actually do under every real condition.
- The real-time compute and deterministic I/O requirement, per NI's
  own documented need, is a genuine hardware and software cost beyond
  a simple offline simulation.
- A HIL test system itself, its wiring, its real-time platform, its
  plant model, becomes another piece of infrastructure that must be
  built, maintained, and kept accurate as the real physical system's
  design evolves.

## 11. Failure modes and misuse

**Trusting a HIL test result as equivalent to real physical-system
validation when the plant simulation's real fidelity is genuinely
insufficient.** Symptom. A controller passes every HIL test and is
deployed, only to fail against the real physical system in a way the
simulation never reproduced, because the simulation's real-time model
diverged from the genuine physical system's actual behavior in some
condition the test never exercised. Cause. Treating a HIL pass as a
complete substitute for real physical-system validation, rather than
as one layer of testing that a genuinely inaccurate plant model can
give false confidence in. Fix. Validate the plant simulation's own
fidelity against real physical-system data wherever genuinely
possible, and treat HIL testing as one layer in a broader validation
strategy that still includes real physical-system testing for the
cases HIL cannot cover with sufficient fidelity.

**Running the plant simulation with real-time compute that cannot
genuinely keep up with the controller's actual timing expectations.**
Symptom. The controller behaves incorrectly during a HIL test in a way
that does not reproduce on the real physical system, or does not
reproduce consistently, because the simulation's real timing genuinely
drifted from what the controller expects, per NI's own documented
deterministic-compute requirement. Cause. Under-provisioning the
real-time test system's compute or I/O determinism relative to the
controller's genuine, real timing demands. Fix. Confirm the real-time
test system's own deterministic I/O and compute capability genuinely
meets or exceeds the controller's real timing requirements before
trusting any HIL test result, and treat a timing mismatch as a defect
in the test setup, never in the controller under test.

**Letting the plant simulation's model drift out of sync with the
real physical system's own design as that design evolves, without a
process to keep them aligned.** Symptom. HIL test results that were
once accurate become silently misleading over time, as the real
physical system's actual design changes in ways the simulation was
never updated to reflect. Cause. No real process ties updates to the
physical system's design to a corresponding update of the plant
simulation, so the two silently diverge. Fix. Treat the plant
simulation as a real, versioned artifact tied to the physical system's
own design, updated deliberately whenever that design changes, rather
than a one-time model built once and left untouched.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Hardware-in-the-Loop Testing | Software-in-the-Loop | Direct testing on the real physical system |
|---|---|---|---|
| Testing the real controller hardware and firmware | Strong, real hardware and real firmware, per Wikipedia's own documented mechanism | Weak, the controller itself is also simulated, not real | Strongest, everything is genuinely real |
| Safety and cost avoidance | Strong, per NI's own documented risk-avoidance framing | Strongest, no physical hardware at all is involved | Weakest, a bug can genuinely damage real, possibly expensive or dangerous equipment |
| Availability before physical hardware exists | Strong, per Wikipedia's own documented early-availability benefit | Strongest, no hardware of any kind is required | None, the real physical system must already exist |
| Fidelity to real physical-system behavior | Moderate, limited by the real plant simulation's own accuracy | Weakest, both controller and plant are modeled | Strongest, nothing is simulated at all |

Reading of the table. Hardware-in-the-Loop Testing wins specifically
when the real controller hardware and firmware genuinely need
validation, and testing against the real physical system directly is
genuinely too risky, costly, or unavailable. A purely software-based
simulation fits earlier-stage, hardware-independent algorithm
validation better, and direct testing on the real physical system,
where safety and cost genuinely allow it, remains the highest-fidelity
option of all.

## 13. Related and incompatible patterns

- **Interrupt Service Routine.** A HIL test system's own real-time I/O
  handling frequently depends on interrupt-driven timing to meet its
  deterministic compute requirement, per NI's own documented need, so
  a poorly-designed interrupt path in the test system itself can
  become a real source of the timing-mismatch failure mode described
  in dimension 11.
- **Watchdog Timer.** A controller under HIL test still runs its real
  watchdog logic exactly as in production, so a HIL test that
  genuinely stalls the plant simulation can, correctly, trigger the
  controller's real watchdog reset, exercising that recovery path as
  part of the same test.

## 14. Refactoring path in and out

Introducing the pattern into a development process that does not have
it. Ordered steps, most relevant to a team currently validating
controller firmware only against the real physical system directly.

1. Confirm the real physical system's behavior can genuinely be
   modeled with sufficient fidelity for a real-time simulation to be
   worth running.
2. Build and validate the plant simulation itself against real
   physical-system data wherever genuinely available, before trusting
   it as a stand-in.
3. Confirm the real-time test system's deterministic compute and I/O
   capability genuinely meets the controller's real timing
   requirements, per NI's own documented need.
4. Connect the real, unmodified controller hardware and firmware to
   the validated plant simulation, and confirm known-good and
   known-bad test cases produce the expected results before relying on
   it for new validation work.

Removing the pattern when it stops earning its place, most relevant
when the real physical system has genuinely become safe, cheap, and
available enough that direct testing no longer carries the risk HIL
exists to avoid.

1. Confirm, concretely, that direct testing against the real physical
   system is genuinely safe, affordable, and available, rather than
   assuming it is.
2. Move validation work to the real physical system directly, treating
   the HIL test system as a superseded, earlier-stage validation layer
   rather than deleting it outright.
3. Confirm the same known-good and known-bad test cases the HIL system
   validated still produce the expected results against the real
   physical system before fully retiring the HIL layer.

## 15. Testing and verification

Easier because of the pattern.

- A known-bad or fault-injection test case, such as a simulated sensor
  failure or an out-of-range physical condition, can be run
  repeatedly and safely against the plant simulation, per NI's own
  documented risk-avoidance framing, without any risk to real,
  physical equipment.
- A test can be run earlier in a development schedule, per Wikipedia's
  own documented early-availability benefit, before the real physical
  system is genuinely available to test against at all.

Harder because of the pattern.

- Confirming the plant simulation's own real fidelity to the genuine
  physical system needs real physical-system data to validate against,
  which may itself be limited or hard to obtain, especially early in a
  program.
- Verifying the real-time test system's own deterministic timing
  genuinely meets the controller's real requirements needs
  measurement on the actual HIL hardware, not an assumption that it
  does.

Techniques that apply.

- **Plant-fidelity validation tests.** Compare the plant simulation's
  real-time behavior against real physical-system data wherever
  genuinely available, and quantify the gap.
- **Fault-injection tests.** Drive the plant simulation through
  simulated failure conditions that would be unsafe or costly to
  reproduce on real physical equipment, and assert the controller
  responds correctly.
- **Real-time determinism verification.** Measure the HIL test
  system's own real, deterministic I/O and compute timing against the
  controller's actual requirements, confirming the mismatch failure
  mode in dimension 11 cannot occur.
- **Known-good, known-bad regression tests.** Maintain a set of test
  cases with known-correct expected results, and re-run them whenever
  the plant simulation or the controller's firmware changes, catching
  a silent drift between the two.

## 16. Observability signals

What to record.

- The real-time test system's own measured timing jitter or latency
  relative to the controller's actual timing requirements, since a
  rising figure directly points at the timing-mismatch failure mode
  from dimension 11.
- Whether a HIL test result genuinely matched a subsequent real
  physical-system test result, where such a comparison is genuinely
  possible, since a mismatch directly signals the plant simulation's
  fidelity has a real, uncaught gap.

A healthy state. The real-time test system's timing stays comfortably
within the controller's real requirements, and HIL test results, where
comparable, genuinely match subsequent real physical-system results.

A failing state. The real-time test system's timing drifts toward or
past the controller's real requirements, or a HIL test result is later
contradicted by a real physical-system test, either directly pointing
at a real, uncaught gap in the test system's own fidelity or
determinism.

## 17. Security and privacy implications

**A HIL test system connected to the same network or infrastructure
as a production deployment pipeline can become a genuine attack path,
since an attacker who compromises the test system could inject
malicious firmware or falsified test results into a downstream
deployment decision.** Because a HIL test system's entire purpose is
to validate firmware before it is trusted for deployment, an attacker
with the ability to manipulate the plant simulation's responses, or to
substitute a falsified controller image into the test loop, can cause
a genuinely faulty or malicious firmware image to appear validated,
undermining every downstream decision that trusts the HIL test result.
Isolating the HIL test infrastructure from any network or system an
external attacker could plausibly reach, and verifying the integrity
of both the controller firmware image and the plant simulation model
before and after each test run, are real, necessary parts of a
security-conscious HIL testing process, not only a test-quality
concern.

## 18. References

1. Wikipedia. "Hardware-in-the-loop simulation".
   https://en.wikipedia.org/wiki/Hardware-in-the-loop_simulation
   Verified 2026-08-21. Source of the HIL definition, plant-simulation
   description, and safety, cost, and early-availability quotes used
   in dimensions 1, 2, 3, 5, 7, 9, and 10.
2. National Instruments. "What Is Hardware-in-the-Loop (HIL)?".
   https://www.ni.com/en/solutions/transportation/hardware-in-the-loop/what-is-hardware-in-the-loop-.html
   Verified 2026-08-21. Source of the real-time deterministic-compute
   requirement and risk-avoidance quotes used in dimensions 3, 4, 5,
   9, 10, and 11.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. C models the controller-firmware side of the real I/O loop
directly, the language most embedded controller firmware under HIL
test is actually written in. Python shows the same conceptual shape
using a minimal, host-testable plant simulation, the pattern's
fault-injection-testable variant from dimension 15, expressed
portably. Swift shows the same conceptual shape using a minimal
model, analogous to how a native test rig's own plant-simulation
loop might be structured. Java, Go, and Rust are omitted, since the
pattern's real home is C and the two languages chosen already cover
its production and its testable-simulation shapes.

### C

```c
#include <stdio.h>

typedef struct {
    double temperature_c;
} plant_state_t;

static double controller_output(double temperature_c) {
    if (temperature_c > 80.0) {
        return 0.0;
    }
    return 1.0;
}

static plant_state_t plant_step(plant_state_t state, double heater_on) {
    plant_state_t next = state;
    if (heater_on > 0.5) {
        next.temperature_c += 2.0;
    } else {
        next.temperature_c -= 1.0;
    }
    return next;
}

static void print_step(int step, double temperature_c, double heater_on) {
    printf("step %d temperature %.1f heater %.1f", step, temperature_c, heater_on);
    putchar(10);
}

int main(void) {
    plant_state_t plant = { .temperature_c = 20.0 };

    for (int step = 0; step < 5; step++) {
        double heater_on = controller_output(plant.temperature_c);
        print_step(step, plant.temperature_c, heater_on);
        plant = plant_step(plant, heater_on);
    }

    return 0;
}
```

### Python

```python
from dataclasses import dataclass


@dataclass
class PlantState:
    temperature_c: float


def controller_output(temperature_c: float) -> float:
    if temperature_c > 80.0:
        return 0.0
    return 1.0


def plant_step(state: PlantState, heater_on: float) -> PlantState:
    delta = 2.0 if heater_on > 0.5 else -1.0
    return PlantState(temperature_c=state.temperature_c + delta)


if __name__ == "__main__":
    plant = PlantState(temperature_c=20.0)

    for step in range(5):
        heater_on = controller_output(plant.temperature_c)
        print("step", step, "temperature", round(plant.temperature_c, 1), "heater", heater_on)
        plant = plant_step(plant, heater_on)
```

### Swift

```swift
struct PlantState {
    var temperatureC: Double
}

func controllerOutput(temperatureC: Double) -> Double {
    temperatureC > 80.0 ? 0.0 : 1.0
}

func plantStep(_ state: PlantState, heaterOn: Double) -> PlantState {
    let delta = heaterOn > 0.5 ? 2.0 : -1.0
    return PlantState(temperatureC: state.temperatureC + delta)
}

var plant = PlantState(temperatureC: 20.0)

for step in 0..<5 {
    let heaterOn = controllerOutput(temperatureC: plant.temperatureC)
    print("step", step, "temperature", plant.temperatureC, "heater", heaterOn)
    plant = plantStep(plant, heaterOn: heaterOn)
}
```
