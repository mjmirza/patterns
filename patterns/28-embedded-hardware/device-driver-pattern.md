---
name: Device Driver Pattern
slug: device-driver-pattern
family: 28-embedded-hardware
category: Structural
aliases: [Device Model, Subsystem API, Config-Data Split]
first_described: "Zephyr Project documentation, device driver model"
maturity: canonical
related: [hardware-abstraction-layer, interrupt-service-routine]
incompatible_with: []
verified: 2026-08-21
---

# Device Driver Pattern

## 1. Name, aliases, and lineage

The canonical name is Device Driver Pattern, the pattern where a
generic, device-independent function-pointer API is defined once per
peripheral type, and each concrete hardware driver fills that API in
with its own implementation, so application code programs against the
generic interface rather than any one driver directly. This is a
distinct concern from the already-published Hardware Abstraction
Layer entry, which covers a portability layer over an entire chip's
peripheral set. this pattern covers the specific mechanism, a
subsystem API struct, per-instance config and data structures, and a
boot-time initialization sequence, that a single driver instance
itself is built from. Zephyr's own documentation states the mechanism
directly, "most drivers will be implementing a device-independent
subsystem API. Applications can simply program to that generic API,
and application code is not specific to any particular driver
implementation."

The alias **Device Model** names the pattern by Zephyr's own framing
of the whole mechanism, the device object, its config and data
structures, and its boot-time initialization together. **Subsystem
API** names the pattern by its defining artifact, the function-pointer
struct every driver of a given type fills in. **Config-Data Split**
names the pattern by its defining per-instance structure, described in
dimension 5.

## 2. Problem and context

An embedded system supports several different concrete peripherals of
the same general type, such as more than one UART or I2C controller
on a chip, or the same peripheral type across several different chip
families a codebase must support, and application code needs a single,
consistent way to talk to any of them without being rewritten for
each concrete device. The Device Driver Pattern solves this by
defining one generic, function-pointer API per peripheral type, and
having every concrete driver implementation fill that same struct in
with its own functions, so application code calls through the generic
struct and never touches a driver's own internals directly. Zephyr's
own documentation shows the mechanism directly, a generic API struct
shape, "`typedef int (*subsystem_do_this_t)(const struct device *dev,
int foo, int bar);`" paired with a struct of such function pointers,
"`__subsystem struct subsystem_driver_api { subsystem_do_this_t
do_this; subsystem_do_that_t do_that; };`"

## 3. Forces

The pattern balances the following competing pressures.

- **Application independence from a specific driver.** Favored.
  Zephyr's own documentation states this directly, application code
  "is not specific to any particular driver implementation," so
  swapping which concrete driver backs a peripheral never requires
  changing the application code that calls it.
- **Support for multiple instances of the same peripheral type.**
  Favored. Zephyr's own documentation states this directly, "each
  instance of the driver will have a different config struct and data
  struct," so a chip with several UARTs, for example, is served by one
  driver implementation reused per instance, rather than duplicated
  code per instance.
- **A clean split between build-time and runtime state.** Favored.
  Zephyr's own documentation names the two structures directly, the
  config struct "is for read-only configuration data set at build
  time," while the data struct "is kept in RAM, and is used by the
  driver for per-instance runtime housekeeping."
- **Boot-time ordering complexity.** Sacrificed. Zephyr's own
  documentation names this directly, drivers are "processed at boot
  time and the corresponding initialization functions are called
  sequentially according to their specified level and priority,"
  across three distinct levels, a real, genuine ordering concern a
  driver author must reason about correctly.
- **A layer of indirection on every call.** Sacrificed. Every call
  through the generic API struct is a function-pointer call rather
  than a direct call, a real, though usually small, runtime cost
  compared to calling a concrete driver's function directly.

## 4. Applicability and non-applicability

Reach for the Device Driver Pattern when the following hold.

- The system genuinely has more than one peripheral of the same type,
  or genuinely needs to support more than one concrete chip family for
  the same peripheral type, so a generic, swappable interface has
  genuine value.
- Application code genuinely benefits from being written once against
  a stable, generic API, rather than being tied to one specific
  driver's own internal functions.
- The real boot-time ordering between this driver and any other
  kernel service or driver it genuinely depends on can be expressed
  through the initialization-level mechanism, per Zephyr's own
  documented three levels.

Do NOT reach for the Device Driver Pattern in these cases, and the
reason matters more than the rule.

- **The system genuinely has exactly one, permanently fixed peripheral
  of that type, with no real prospect of ever swapping it or
  supporting a second instance**, the generic API struct's indirection
  and the per-instance config-data split add real, unneeded complexity
  for a peripheral that will never genuinely vary.
- **The real call overhead of a function-pointer indirection is
  genuinely unacceptable**, such as an extremely tight, cycle-counted
  inner loop, a direct call to a concrete, known driver function fits
  that real constraint better than the generic API's indirection.
- **The peripheral's real boot-time dependencies genuinely cannot be
  expressed through Zephyr's own documented three-level, priority-
  ordered initialization scheme**, a genuinely more complex, dynamic
  dependency ordering needs a different initialization strategy than
  this pattern's static, level-and-priority mechanism provides.

## 5. Structure

The Device Driver Pattern has four structural parts.

- **The subsystem API struct**, per Zephyr's own documented shape, a
  struct of function pointers, one per operation the peripheral type
  supports, that every concrete driver of that type fills in.
- **The config struct**, Zephyr's own documentation describing it
  directly as "read-only configuration data set at build time," such
  as a base memory-mapped I/O address or an IRQ line number.
- **The data struct**, Zephyr's own documentation describing it
  directly as kept "in RAM" for "per-instance runtime housekeeping,"
  such as reference counts, semaphores, or scratch buffers.
- **The boot-time initialization**, Zephyr's own documented mechanism,
  where a driver's init function is called automatically, ordered by
  a declared level and priority, before the application itself starts
  running.

## 6. ASCII structure diagram

```
  application code
        |
        v
  subsystem API struct (function pointers, one per operation)
        |
        v
  concrete driver instance
  +-------------------+
  |  config struct       |  build-time, read-only
  |  data struct          |  runtime, RAM
  |  init function          |  called at boot, ordered by level/priority
  +-------------------+
```

## 7. Dynamics

The trace below shows one complete boot-and-call cycle.

```
The system boots

per Zephyr's own documented mechanism, every driver declared through
the device model is processed at boot time
   |-- each driver's init function is called, in order, according to
       its declared initialization level and priority
   |-- the init function usually sets up the data struct's initial
       runtime state, reading whatever the config struct's build-time
       settings specify

Application code calls a peripheral operation

the application calls through the generic subsystem API struct, per
Zephyr's own documented function-pointer shape, never through the
concrete driver's own function names directly
   |-- the function-pointer call dispatches to the specific driver
       instance's real implementation
   |-- that implementation reads its own config struct for build-time
       settings and its own data struct for current runtime state,
       and performs the real operation against the real hardware
```

## 8. Implementation variants

**Single-instance driver, no config-data split genuinely needed.** A
minimal form for a peripheral that genuinely only ever has one
instance, where the config and data structs may be combined or
simplified, at the cost of losing the clean reusability the full split
provides if a second instance is ever genuinely needed later.

**Multi-instance driver, the canonical Zephyr form.** Described
directly above, one driver implementation, reused across several
concrete instances, each with its own config and data struct, per
Zephyr's own documented per-instance separation.

**Layered driver, built on a lower-level subsystem API.** A driver for
a higher-level peripheral is itself implemented by calling through
another, lower-level subsystem API, such as a sensor driver built on
top of an I2C bus driver's own generic API, composing this pattern
recursively.

## 9. Known production uses

**Zephyr's own documentation, defining the subsystem API struct and
the application-independence benefit it provides.** Zephyr states the
mechanism and the benefit directly. "Most drivers will be implementing
a device-independent subsystem API. Applications can simply program to
that generic API, and application code is not specific to any
particular driver implementation." The API shape itself is a struct of
function pointers, "`typedef int (*subsystem_do_this_t)(const struct
device *dev, int foo, int bar); ... __subsystem struct
subsystem_driver_api { subsystem_do_this_t do_this;
subsystem_do_that_t do_that; };`" Zephyr Project, "Device Driver
Model,"
https://docs.zephyrproject.org/latest/kernel/drivers/index.html,
verified 2026-08-21.

**Zephyr's own documentation, on the per-instance config-data split
and the boot-time initialization ordering this pattern depends on.**
Zephyr states this directly. "Each instance of the driver will have a
different config struct and data struct." The config struct "is for
read-only configuration data set at build time." The data struct "is
kept in RAM, and is used by the driver for per-instance runtime
housekeeping." Drivers "are processed at boot time and the
corresponding initialization functions are called sequentially
according to their specified level and priority." Zephyr Project,
"Device Driver Model,"
https://docs.zephyrproject.org/latest/kernel/drivers/index.html,
verified 2026-08-21.

## 10. Consequences

Positive.

- Application code stays genuinely independent of any specific driver
  implementation, per Zephyr's own documented benefit, so swapping the
  concrete hardware never requires rewriting the application.
- One driver implementation genuinely serves multiple instances of the
  same peripheral type, per Zephyr's own documented per-instance
  config-data split, avoiding duplicated driver code.
- Boot-time initialization ordering is expressed declaratively, per
  Zephyr's own documented level-and-priority mechanism, rather than
  through hand-written, error-prone startup sequencing code.

Negative.

- Every call through the generic API struct carries a real, though
  usually small, function-pointer indirection cost compared to
  calling a concrete driver's function directly.
- The boot-time initialization-level and priority mechanism is a real,
  genuine source of ordering bugs when a driver's true dependencies
  are not expressed correctly through it.
- The config-data split and the generic API struct add real structural
  overhead for a peripheral that will genuinely only ever have one,
  fixed instance.

## 11. Failure modes and misuse

**Declaring a driver's initialization level or priority incorrectly,
so it runs before a kernel service or another driver it genuinely
depends on has itself finished initializing.** Symptom. The driver's
own init function crashes, or silently produces incorrect state,
because it reads from or calls into a dependency that has not
genuinely finished its own boot-time setup yet. Cause. Choosing an
initialization level or priority without genuinely confirming the
real dependency's own declared level and priority, so the two end up
ordered incorrectly relative to each other. Fix. Confirm every real
dependency's own declared initialization level and priority before
choosing a driver's own, and order this driver strictly after every
genuine dependency, per Zephyr's own documented level-and-priority
mechanism.

**Storing build-time-only information in the data struct, or runtime,
mutable state in the config struct, breaking the clean split Zephyr's
own documentation defines.** Symptom. A value that should never change
at runtime is accidentally mutated, corrupting behavior across every
call that reads it afterward, or a value that genuinely needs to
change at runtime cannot be updated because it was placed in the
read-only config struct. Cause. Not respecting the real distinction
Zephyr's own documentation draws directly, the config struct is "for
read-only configuration data set at build time," while the data
struct is the place for genuine "per-instance runtime housekeeping."
Fix. Place every value that genuinely never changes after build time
in the config struct, and every value that genuinely changes at
runtime in the data struct, with no exceptions, and treat any
violation as a structural bug in the driver, not a stylistic
preference.

**Calling a concrete driver's own internal function directly from
application code, rather than through the generic subsystem API
struct, silently reintroducing the exact driver-specific coupling
this pattern exists to avoid.** Symptom. Application code that was
genuinely independent of the specific driver implementation, per
Zephyr's own documented benefit, becomes silently coupled to it,
breaking the moment a different concrete driver is swapped in, in a
way that is not obvious from reading the application code alone.
Cause. Reaching for a driver's own internal function directly, perhaps
for a real or perceived performance reason, without recognizing that
doing so defeats the entire purpose of the generic API struct. Fix.
Call through the generic subsystem API struct exclusively from
application code, and if a genuine, measured performance need exists
that the generic API cannot meet, address it by extending the generic
API itself, not by bypassing it from application code.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Device Driver Pattern (generic API struct) | Direct concrete-driver calls | Hardware Abstraction Layer alone |
|---|---|---|---|
| Application independence from a specific driver | Strong, per Zephyr's own documented benefit | None, application code is directly coupled to one driver | Strong, but scoped to whole-chip portability, not per-peripheral instances |
| Support for multiple instances of the same peripheral type | Strong, per Zephyr's own documented config-data split | Weak, usually requires duplicated code per instance | Not directly addressed, HAL is chip-level, not instance-level |
| Boot-time ordering expressiveness | Strong, a declared level-and-priority mechanism, per Zephyr's own documentation | None, ordering must be hand-coded | Varies by implementation, not a defined property of HAL itself |
| Call overhead | Moderate, one function-pointer indirection | Lowest, a direct call | Varies, depends on the specific HAL implementation |

Reading of the table. The Device Driver Pattern wins specifically when
a peripheral type genuinely has, or could genuinely have, multiple
instances or multiple concrete implementations, and application
independence from the specific driver is genuinely valuable. A
peripheral genuinely fixed to exactly one instance forever fits direct
calls better, and a whole-chip portability concern, rather than a
per-instance one, is what the separate Hardware Abstraction Layer
entry addresses.

## 13. Related and incompatible patterns

- **Hardware Abstraction Layer.** The broader, chip-level portability
  concern this pattern's per-instance, per-peripheral-type mechanism
  sits inside, a HAL frequently exposes several device drivers, each
  built using this pattern, behind its own, still more general
  interface.
- **Interrupt Service Routine.** A device driver's own implementation
  frequently registers and handles an interrupt as part of its real
  operation, such as a UART driver's receive-complete interrupt, so
  the interrupt-safety constraints that entry describes apply directly
  inside a driver's own code.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to application code currently calling a specific
concrete driver's own functions directly.

1. Confirm the peripheral type genuinely has, or could genuinely have,
   more than one instance or more than one concrete implementation,
   justifying the generic API struct's real indirection cost.
2. Define the generic subsystem API struct, per Zephyr's own
   documented function-pointer shape, covering every operation the
   application genuinely needs.
3. Split the concrete driver's own state into a config struct for
   genuinely build-time, read-only settings and a data struct for
   genuinely runtime, mutable state, per Zephyr's own documented
   distinction.
4. Rewrite application code to call exclusively through the generic
   API struct, confirming no remaining call site reaches into the
   concrete driver's own internal functions directly.

Removing the pattern when it stops earning its place, most relevant
when a peripheral type has genuinely settled to exactly one, permanent
instance with no real prospect of ever varying.

1. Confirm, concretely, that the peripheral type genuinely will never
   have a second instance or a second concrete implementation, rather
   than assuming it will not.
2. Move application code to call the single, concrete driver's
   functions directly, removing the generic API struct's indirection.
3. Confirm no other part of the system still depends on the generic
   API struct's existence before removing it entirely.

## 15. Testing and verification

Easier because of the pattern.

- A test can substitute a mock implementation of the generic API
  struct in place of the real hardware driver, exercising application
  code without needing real hardware present at all, since the
  application only ever depends on the generic struct's shape.
- A test can assert the config struct's real values are genuinely
  never mutated at runtime, a simple, deterministic check that
  directly verifies the build-time-versus-runtime split described in
  dimension 11.

Harder because of the pattern.

- Verifying a driver's real boot-time initialization ordering is
  genuinely correct relative to its real dependencies needs a test
  that can drive the real, full boot sequence, not only the driver's
  own init function in isolation.
- Confirming the generic API struct's real function-pointer dispatch
  behaves correctly under real hardware timing needs a test on the
  actual target hardware, not a host-based mock alone.

Techniques that apply.

- **Mock-driver substitution tests.** Substitute a mock implementation
  of the generic API struct, and exercise application code against it
  with no real hardware present.
- **Config-immutability tests.** Assert the config struct's real
  values are genuinely never mutated after the driver's own
  initialization completes.
- **Boot-order verification tests.** Drive the real, full boot
  sequence and assert every driver's real dependencies are genuinely
  satisfied before it runs, per its declared level and priority.
- **Real-hardware dispatch verification.** Confirm the generic API
  struct's real function-pointer calls behave correctly on the actual
  target hardware, under real timing.

## 16. Observability signals

What to record.

- Whether every driver's real, declared initialization level and
  priority genuinely completed in the expected order, since an
  out-of-order completion directly points at the boot-ordering
  failure mode from dimension 11.
- Whether any application code path genuinely calls a concrete
  driver's own function directly, bypassing the generic API struct,
  since any such call directly points at the coupling failure mode
  from dimension 11.

A healthy state. Every driver's real boot-time initialization
completes in the expected, declared order, and every application code
path calls exclusively through the generic API struct, with no direct
concrete-driver coupling anywhere.

A failing state. A driver's real initialization completes out of its
expected order, pointing directly at a boot-ordering bug, or an
application code path is found calling a concrete driver's own
function directly, pointing directly at reintroduced, undesired
coupling.

## 17. Security and privacy implications

**A driver's data struct, kept in RAM for genuine runtime
housekeeping per Zephyr's own documented design, can retain sensitive
information across a device's lifetime if it is never genuinely
cleared, and a driver's config struct, if it can be modified at
runtime through a bug that violates its intended read-only nature, can
let an attacker redirect a peripheral's real hardware addressing to an
unintended, potentially sensitive memory region.** Because the config
struct is meant to hold "read-only configuration data set at build
time," per Zephyr's own documentation, any code path that genuinely
allows it to be modified at runtime, whether through a bug or a
deliberately exposed API, undermines a real assumption other code in
the system may depend on, such as a fixed, trusted base memory-mapped
I/O address. Similarly, sensitive data left in a driver's data struct
after the driver is genuinely done with it, such as a cryptographic
key buffer used during a driver operation, can be read by a
subsequent, unrelated user of the same memory if it is not explicitly
cleared. Treating the config struct as genuinely immutable after
initialization, and explicitly clearing any sensitive content from a
driver's data struct once it is genuinely no longer needed, are real,
necessary parts of a security-conscious device driver implementation.

## 18. References

1. Zephyr Project. "Device Driver Model".
   https://docs.zephyrproject.org/latest/kernel/drivers/index.html
   Verified 2026-08-21. Source of the subsystem API struct shape, the
   application-independence benefit, the per-instance config-data
   split, and the boot-time initialization-ordering quotes used in
   dimensions 1, 2, 3, 5, 7, 9, and 10.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. C models the function-pointer subsystem API and the config-data
split directly, the language real embedded device drivers such as
Zephyr's are actually written in. Python shows the same conceptual
shape using a minimal, host-testable simulation, the pattern's
mock-driver-substitution-testable variant from dimension 15, expressed
portably. Swift shows the same conceptual shape using a minimal
model, analogous to how a native application's own protocol-based
driver abstraction might be structured. Java, Go, and Rust are
omitted, since the pattern's real home is C and the two languages
chosen already cover its production and its testable-simulation
shapes.

### C

```c
#include <stdio.h>

typedef struct {
    unsigned long base_address;
} driver_config_t;

typedef struct {
    int open_count;
} driver_data_t;

typedef struct device {
    const driver_config_t *config;
    driver_data_t *data;
    int (*write_byte)(const struct device *dev, int value);
} device_t;

static int concrete_write_byte(const device_t *dev, int value) {
    dev->data->open_count++;
    printf("write %d to base 0x%lx, call count %d",
           value, dev->config->base_address, dev->data->open_count);
    putchar(10);
    return 0;
}

int main(void) {
    driver_config_t config = { .base_address = 0x40000000 };
    driver_data_t data = { .open_count = 0 };
    device_t uart0 = {
        .config = &config,
        .data = &data,
        .write_byte = concrete_write_byte,
    };

    uart0.write_byte(&uart0, 65);
    uart0.write_byte(&uart0, 66);

    return 0;
}
```

### Python

```python
from dataclasses import dataclass
from typing import Callable


@dataclass
class DriverConfig:
    base_address: int


@dataclass
class DriverData:
    open_count: int = 0


class Device:
    def __init__(self, config: DriverConfig, data: DriverData, write_byte: Callable[["Device", int], int]):
        self.config = config
        self.data = data
        self._write_byte = write_byte

    def write_byte(self, value: int) -> int:
        return self._write_byte(self, value)


def concrete_write_byte(dev: Device, value: int) -> int:
    dev.data.open_count += 1
    print("write", value, "to base", hex(dev.config.base_address), "call count", dev.data.open_count)
    return 0


if __name__ == "__main__":
    uart0 = Device(
        config=DriverConfig(base_address=0x40000000),
        data=DriverData(),
        write_byte=concrete_write_byte,
    )

    uart0.write_byte(65)
    uart0.write_byte(66)
```

### Swift

```swift
struct DriverConfig {
    let baseAddress: UInt
}

final class DriverData {
    var openCount = 0
}

protocol WritableDevice {
    var config: DriverConfig { get }
    var data: DriverData { get }
    func writeByte(_ value: Int) -> Int
}

final class UARTDevice: WritableDevice {
    let config: DriverConfig
    let data: DriverData

    init(config: DriverConfig, data: DriverData) {
        self.config = config
        self.data = data
    }

    func writeByte(_ value: Int) -> Int {
        data.openCount += 1
        print("write", value, "to base", config.baseAddress, "call count", data.openCount)
        return 0
    }
}

let uart0 = UARTDevice(config: DriverConfig(baseAddress: 0x40000000), data: DriverData())

_ = uart0.writeByte(65)
_ = uart0.writeByte(66)
```
