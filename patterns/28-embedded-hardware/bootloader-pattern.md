---
name: Bootloader Pattern
slug: bootloader-pattern
family: 28-embedded-hardware
category: Structural
aliases: [Firmware Update Bootloader, A/B Image Swap, Secure Boot Chain]
first_described: "MCUboot documentation, design and image trailer"
maturity: canonical
related: [hardware-abstraction-layer, watchdog-timer]
incompatible_with: []
verified: 2026-08-21
---

# Bootloader Pattern

## 1. Name, aliases, and lineage

The canonical name is Bootloader Pattern, the structure where a small,
trusted piece of firmware runs before the main application, verifies
and selects which firmware image to run, and can fail safely back to
a known-working image if a newly-installed one turns out to be bad.
MCUboot's own documentation describes the mechanism directly, that its
bootloader "comprises the bootutil library" for most bootloader
functions, with "the final step of actually jumping to the main
image" happening in a small, port-specific boot application.

The alias **Firmware Update Bootloader** names the pattern by its
primary purpose, enabling firmware to update itself in the field.
**A/B Image Swap** names one common implementation shape, two firmware
slots that trade places during an update. **Secure Boot Chain** names
the pattern by its trust property, each stage verifying the next
before handing off control.

## 2. Problem and context

An embedded device shipped to the field needs a way to receive new
firmware after it has left the factory, and that update must never
leave the device permanently unable to boot, even if the new firmware
is genuinely broken or the update itself is interrupted, such as by a
power loss partway through writing the new image. A Bootloader Pattern
solves this by keeping the update logic in a small, separate piece of
code that runs first, verifies the firmware image before handing off
control, and can revert to the previous working image if the new one
fails. MCUboot's own documentation states the resulting benefit
directly, that "test swaps are supported to provide a rollback
mechanism to prevent devices from becoming 'bricked' by bad firmware."

## 3. Forces

The pattern balances the following competing pressures.

- **Recovery from a bad update.** Favored. MCUboot's own documentation
  names this directly, if a new image fails to confirm itself as
  operational, "reversion occurs automatically," so a device with a
  genuinely broken update is never left permanently unbootable.
- **Resilience against interruption.** Favored. MCUboot's own
  documentation states this directly, "the swap status region allows
  the bootloader to recover in case it restarts in the middle of an
  image swap operation," so a power loss partway through an update
  does not leave the device in a corrupted, half-swapped state.
- **Trust in what runs.** Favored. MCUboot's own documentation names
  the mechanism directly, images "must be signed," and the bootloader
  verifies a signature against an embedded public key before allowing
  an image to run.
- **Flash storage cost.** Sacrificed. A/B image swapping needs enough
  flash for two full firmware slots plus a scratch area, per MCUboot's
  own documented swap mechanism, roughly double the storage a single-
  image system would need.
- **Boot-time complexity and latency.** Sacrificed. Every boot now
  passes through the bootloader's own verification and swap-recovery
  logic before the main application starts, adding real code size and
  a small, but real, boot-time cost compared to a device with no
  bootloader at all.

## 4. Applicability and non-applicability

Reach for a Bootloader Pattern when the following hold.

- The device genuinely needs to receive firmware updates after it
  ships, whether over a wired connection, a wireless link, or physical
  media, and cannot rely on returning the device to the factory for
  every update.
- The device genuinely needs to survive a bad update without becoming
  permanently unbootable, such as a remotely-deployed device nobody
  can physically reach to recover by hand.
- The device genuinely needs to trust the firmware it runs, such as a
  device where an attacker installing unauthorized firmware would be a
  real, serious risk.

Do NOT reach for a Bootloader Pattern in these cases, and the reason
matters more than the rule.

- **The device genuinely never receives a firmware update after it
  ships**, a device programmed once at the factory and never updated
  again does not need the swap, rollback, or verification machinery
  a bootloader provides, since there is never a new image to verify or
  revert.
- **The device genuinely cannot spare the flash storage for two
  firmware slots plus scratch space**, per the flash-storage-cost
  force in dimension 3, a device with genuinely too little flash for
  the doubled storage cost needs a different update strategy, such as
  a single-slot update with an external recovery mechanism instead.
- **The device genuinely has no real threat model for unauthorized
  firmware**, such as an isolated, physically-secured device with no
  remote update path at all, the signature-verification machinery
  adds real complexity for a trust property the device does not
  actually need.

## 5. Structure

A Bootloader Pattern has four structural parts.

- **The bootloader itself**, the small, trusted code that runs first,
  MCUboot's own documentation describing its two pieces directly, "the
  bootutil library" handling most bootloader functions, and a small,
  port-specific boot application handling "the final step of actually
  jumping to the main image."
- **The firmware slots**, the primary slot the device boots from and,
  in an A/B swap implementation, a secondary slot holding a candidate
  update, plus a scratch area MCUboot's own documentation describes as
  temporary storage used during the swap.
- **The image trailer**, metadata stored at the end of each slot,
  MCUboot's own documentation describing it directly as storing "swap
  status, encryption keys, and confirmation flags" that let the
  bootloader "determine appropriate boot actions."
- **The public key**, embedded in the bootloader itself, MCUboot's own
  documentation describing its role directly, verifying an image's
  signature by checking it "against every embedded key" and accepting
  "the first match."

## 6. ASCII structure diagram

```
  power on
      |
      v
  bootloader runs first
      |
      +-- verify signature against embedded public key
      |
      +-- check image trailer for pending swap / confirm status
      |
      +-- swap or revert if needed, per the trailer's recorded state
      |
      v
  jump to the verified, selected main image
```

## 7. Dynamics

The trace below shows one complete firmware update cycle.

```
A new image arrives in the secondary slot

the device writes the new candidate image into the secondary firmware
slot while the current, working image keeps running from the primary
slot
   |-- the device marks the secondary slot as pending a test swap

The device reboots

the bootloader runs first, per MCUboot's own documented sequence
   |-- it finds the secondary slot marked for a test swap
   |-- it performs the swap, sector by sector, through the scratch
       area, per MCUboot's own documented copy-erase-move-restore
       sequence, so a power loss at any point can be recovered from
       the swap status region on the next boot
   |-- once swapped, it jumps to the new image, now running from the
       primary slot

The new image confirms itself, or it does not

if the new image runs correctly, it marks itself confirmed in its own
image trailer
   |-- on every future boot, the bootloader sees the confirmed image
       and simply boots it directly, no further swap needed
   |-- if the new image never confirms itself, per MCUboot's own
       documented rollback mechanism, the bootloader reverts to the
       previous, known-working image on the next reset, so a genuinely
       bad update never leaves the device permanently unbootable
```

## 8. Implementation variants

**Test-swap with explicit confirm, the canonical MCUboot form.**
Described directly above, a new image is swapped in as a test, and
must explicitly confirm itself as working before the bootloader
commits to it, per MCUboot's own documented rollback mechanism.

**Direct-XIP, no swap.** Rather than physically swapping image
contents between two slots, the bootloader instead verifies and jumps
directly to whichever slot holds a valid, newer image, avoiding the
swap-copy cost entirely at the expense of needing both slots to be
independently executable in place.

**Signature-only verification, no swap or rollback.** A simpler
bootloader variant that verifies an image's signature before booting
it, per MCUboot's own documented public-key mechanism, but has no
A/B swap or automatic rollback machinery, trading recovery from a bad
update for a smaller, simpler bootloader.

## 9. Known production uses

**MCUboot's own documentation, defining the swap mechanism and its
fail-safe, power-cut-resistant property.** MCUboot states this
directly. During a swap, the bootloader copies "a secondary slot
sector to scratch," erases the secondary slot, moves the primary
slot's sector to secondary, then places "the scratch contents into
the primary slot." "The swap status region allows the bootloader to
recover in case it restarts in the middle of an image swap
operation." MCUboot Project, "Design,"
https://docs.mcuboot.com/design.html, verified 2026-08-21.

**MCUboot's own documentation, on the rollback mechanism and image
trailer that make a bad update recoverable.** MCUboot states this
directly. "Test swaps are supported to provide a rollback mechanism to
prevent devices from becoming 'bricked' by bad firmware." An image
that fails to confirm itself as operational is automatically reverted.
The image trailer stores "swap status, encryption keys, and
confirmation flags," letting the bootloader "determine appropriate
boot actions." MCUboot Project, "Design,"
https://docs.mcuboot.com/design.html, verified 2026-08-21.

**MCUboot's own documentation, on the signature-verification mechanism
this pattern's trust property depends on.** MCUboot states this
directly. "In order to upgrade to an image (or even boot it, if
`MCUBOOT_VALIDATE_PRIMARY_SLOT` is enabled), the images must be
signed." The bootloader's own key-matching logic "hashes the image's
KEYHASH TLV against every embedded key and accepts the first match."
MCUboot Project, "Readme (Zephyr),"
https://docs.mcuboot.com/readme-zephyr.html, verified 2026-08-21.

## 10. Consequences

Positive.

- A genuinely bad update never leaves the device permanently
  unbootable, per MCUboot's own documented rollback mechanism, since
  an unconfirmed image is automatically reverted.
- A power loss during an update is genuinely recoverable, per MCUboot's
  own documented swap status region, since the bootloader can resume
  or recover an interrupted swap from where it left off.
- Only firmware signed by a trusted key can run, per MCUboot's own
  documented signature-verification mechanism, giving the device a
  real, verifiable trust boundary at boot.

Negative.

- The device needs roughly double the flash storage a single-image
  system would, per the swap mechanism's two-slot-plus-scratch
  requirement.
- Every boot now passes through the bootloader's own verification and
  swap-recovery logic before the main application starts, a real,
  though usually small, boot-time cost.
- The bootloader itself is a genuinely security-sensitive piece of
  code, since a bug in its signature verification or swap-recovery
  logic can undermine the very trust and recovery guarantees the
  pattern exists to provide.

## 11. Failure modes and misuse

**Shipping a device with no automatic rollback, so a genuinely bad
firmware update leaves the device permanently unbootable.** Symptom.
A device that received a firmware update stops responding entirely,
with no way to recover it without physical access and specialized
tools, even though the underlying hardware is otherwise healthy.
Cause. Choosing the signature-only variant from dimension 8, which
verifies but does not swap or automatically revert, for a device that
genuinely needed the rollback protection, or implementing the confirm
step incorrectly so a bad image is mistakenly treated as confirmed.
Fix. Use the full test-swap-with-confirm variant, per MCUboot's own
documented rollback mechanism, for any device that must survive a bad
update in the field, and verify the confirm step genuinely only fires
when the new image has proven itself operational.

**An update process that writes a new image without properly signing
it, or with a signature that does not match any key embedded in the
bootloader.** Symptom. A legitimate firmware update is rejected by the
bootloader and the device continues running its old firmware, and the
failure can look identical to an actual attack being blocked, making
it hard to tell a genuine deployment mistake from a real security
event. Cause. A build or release process that fails to sign the image
with the correct private key, or that embeds the wrong public key
into the bootloader in the first place, so MCUboot's own documented
key-matching logic never finds a match. Fix. Verify the signing key
pair used in the release process genuinely matches the public key
embedded in the deployed bootloader, and test a real signed update
against a real device before wide deployment.

**A swap operation interrupted by a power loss at a point the swap
status region cannot actually recover from, due to a bug or an
unhandled edge case in the recovery logic itself.** Symptom. A device
that lost power during a firmware update is left in a corrupted,
neither-old-nor-new state, defeating the exact power-cut-resistance
the pattern exists to provide. Cause. A bug in the bootloader's own
swap-recovery logic, or an edge case, such as a second power loss
during the recovery attempt itself, that the recovery logic was not
genuinely tested against. Fix. Test the swap-recovery logic against a
real, repeated power-cut simulation, not only a single interruption at
one point in the sequence, since the recovery logic itself is exactly
the code a genuine field failure will exercise.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Bootloader Pattern (test-swap) | Signature-only, no swap | No bootloader at all |
|---|---|---|---|
| Recovery from a bad update | Strong, per MCUboot's own documented rollback mechanism | None, a bad signed image still boots and stays booted | None, there is no update mechanism to recover from |
| Resilience against interruption | Strong, per MCUboot's own documented swap status region | Moderate, no swap means less to interrupt, but also no recovery machinery | Not applicable, no update happens at all |
| Trust in what runs | Strong, per MCUboot's own documented signature verification | Strong, the same signature verification without the swap | None, whatever was factory-programmed runs with no check at all |
| Flash storage cost | High, two slots plus scratch | Lower, no scratch or secondary swap slot strictly needed | Lowest, a single firmware image only |

Reading of the table. The full test-swap-with-confirm variant wins
specifically when a device genuinely needs to survive both a bad
update and an interrupted one in the field. A device that only needs
to verify what it runs, without full swap-based rollback, fits the
signature-only variant better, and a device that genuinely never
updates in the field does not need a bootloader's machinery at all.

## 13. Related and incompatible patterns

- **Hardware Abstraction Layer.** A bootloader's own flash-write and
  flash-read operations are frequently accessed through a hardware
  abstraction layer, keeping the flash driver portable across the
  different microcontrollers a bootloader may need to support.
- **Watchdog Timer.** A watchdog is frequently used alongside a
  bootloader's confirm step, so a new image that hangs rather than
  crashing outright is still caught, the watchdog reset triggering the
  same rollback path a crash would.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a device currently shipping a single firmware
image with no field-update capability.

1. Confirm the device genuinely needs field firmware updates, and
   genuinely needs to survive a bad one, rather than assuming it does.
2. Partition flash storage for the primary slot, the secondary slot,
   and a scratch area, per MCUboot's own documented layout, confirming
   the device genuinely has enough flash for the doubled storage cost.
3. Integrate the bootloader itself, wiring its signature verification
   to a real, deployed public key, and its swap-recovery logic to the
   device's real flash driver.
4. Test the full update-swap-confirm cycle, and the rollback path for
   a genuinely bad image, against real hardware before any field
   deployment.

Removing the pattern when it stops earning its place, most relevant
when a device's real deployment model has genuinely changed to no
longer need field updates.

1. Confirm, concretely, that the device genuinely no longer needs
   field firmware updates, rather than assuming it does not.
2. Move to a single, unswapped firmware image, recovering the flash
   storage the secondary slot and scratch area previously consumed.
3. Confirm no remaining code path still expects the bootloader's swap
   or rollback machinery to be present.

## 15. Testing and verification

Easier because of the pattern.

- A test can drive a simulated update cycle and assert an image that
  never confirms itself is genuinely reverted on the next reset,
  directly verifying MCUboot's own documented rollback mechanism.
- A test can assert an image signed with the wrong key is genuinely
  rejected by the bootloader's key-matching logic, a simple,
  deterministic check of the signature-verification mechanism.

Harder because of the pattern.

- Verifying the swap-recovery logic genuinely survives a power loss
  needs a test that can interrupt real flash writes at a real,
  specific point in the sequence, not merely a simulated interruption
  in a host-based test.
- Confirming the full update cycle behaves correctly under real flash
  timing and real power characteristics needs a test on the actual
  target hardware, not a host simulation.

Techniques that apply.

- **Rollback verification tests.** Drive a simulated update where the
  new image never confirms itself, and assert the bootloader reverts
  to the previous image on the next reset.
- **Signature-rejection tests.** Assert an image signed with an
  unrecognized key is genuinely rejected, never booted.
- **Power-cut interruption tests.** Interrupt a real flash write during
  a swap at several distinct points in the sequence, and assert the
  bootloader recovers correctly from each one on the next boot.
- **Real-hardware update-cycle verification.** Confirm the full
  update-swap-confirm cycle on real target hardware, under real flash
  timing, before any field deployment.

## 16. Observability signals

What to record.

- Whether a firmware update genuinely completed with a confirmed
  image, or was reverted, since a rising revert rate directly signals
  a problem with the update content or the deployment process itself.
- The image trailer's recorded swap and confirmation state on boot,
  since an unexpected or inconsistent state directly points at a
  possible bug in the swap-recovery logic itself.

A healthy state. Firmware updates consistently reach a confirmed
state, and the image trailer's recorded state on every boot matches
what the update process expects.

A failing state. A rising rate of reverted updates, pointing at a
problem with the update content or the deployment process, or an
image trailer recorded in an unexpected or inconsistent state,
pointing directly at a possible bug in the swap-recovery logic itself.

## 17. Security and privacy implications

**A bootloader whose public key can itself be overwritten, or whose
signature check can be bypassed, defeats the entire trust chain the
pattern exists to provide, allowing an attacker to install
unauthorized firmware.** Because MCUboot's own documented trust model
depends entirely on the public key embedded in the bootloader and the
correctness of its signature-matching logic, any path that lets an
attacker overwrite that key, downgrade to an older bootloader with a
known signature-check flaw, or otherwise bypass the check, undermines
every other guarantee the pattern provides, including the recovery and
rollback protections, since an attacker who can install unsigned
firmware can also install firmware that disables those protections.
Protecting the bootloader region itself from modification, such as
through a hardware-enforced read-only or write-protected region, and
preventing a downgrade to a bootloader version with a known
vulnerability, are both real, necessary parts of a security-conscious
bootloader deployment, not optional hardening.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. C models the image-trailer and swap-decision shape directly,
the language real bootloaders such as MCUboot are actually written
in. Python shows the same conceptual shape using a minimal, host-
testable simulation, the pattern's rollback-verification-testable
variant from dimension 15, expressed portably. Swift shows the same
conceptual shape using a minimal model, analogous to how a native
application's own update-and-confirm state machine might be
structured. Java, Go, and Rust are omitted, since the pattern's real
home is C and the two languages chosen already cover its production
and its testable-simulation shapes.

### C

```c
#include <stdio.h>

typedef enum {
    SLOT_PENDING,
    SLOT_CONFIRMED,
    SLOT_REVERTED
} slot_state_t;

static slot_state_t primary_state = SLOT_CONFIRMED;

static int try_new_image(int signature_valid) {
    if (!signature_valid) {
        return -1;
    }
    primary_state = SLOT_PENDING;
    return 0;
}

static void confirm_image(void) {
    if (primary_state == SLOT_PENDING) {
        primary_state = SLOT_CONFIRMED;
    }
}

static void reboot_check(void) {
    if (primary_state == SLOT_PENDING) {
        primary_state = SLOT_REVERTED;
    }
}

static void print_state(const char *label) {
    printf("%s state %d", label, (int)primary_state);
    putchar(10);
}

int main(void) {
    print_state("initial");

    try_new_image(1);
    print_state("after unsigned test image");
    reboot_check();
    print_state("after reboot with no confirm");

    try_new_image(1);
    confirm_image();
    print_state("after confirmed image");

    return 0;
}
```

### Python

```python
from enum import Enum, auto


class SlotState(Enum):
    CONFIRMED = auto()
    PENDING = auto()
    REVERTED = auto()


class Bootloader:
    def __init__(self):
        self.state = SlotState.CONFIRMED

    def try_new_image(self, signature_valid: bool) -> bool:
        if not signature_valid:
            return False
        self.state = SlotState.PENDING
        return True

    def confirm_image(self) -> None:
        if self.state == SlotState.PENDING:
            self.state = SlotState.CONFIRMED

    def reboot_check(self) -> None:
        if self.state == SlotState.PENDING:
            self.state = SlotState.REVERTED


if __name__ == "__main__":
    loader = Bootloader()
    print("initial state:", loader.state)

    loader.try_new_image(signature_valid=True)
    print("after unsigned test image:", loader.state)
    loader.reboot_check()
    print("after reboot with no confirm:", loader.state)

    loader.try_new_image(signature_valid=True)
    loader.confirm_image()
    print("after confirmed image:", loader.state)
```

### Swift

```swift
enum SlotState {
    case confirmed
    case pending
    case reverted
}

final class Bootloader {
    private(set) var state: SlotState = .confirmed

    func tryNewImage(signatureValid: Bool) -> Bool {
        guard signatureValid else {
            return false
        }
        state = .pending
        return true
    }

    func confirmImage() {
        if state == .pending {
            state = .confirmed
        }
    }

    func rebootCheck() {
        if state == .pending {
            state = .reverted
        }
    }
}

extension SlotState: Equatable {}

let loader = Bootloader()
print("initial state:", loader.state)

_ = loader.tryNewImage(signatureValid: true)
print("after unsigned test image:", loader.state)
loader.rebootCheck()
print("after reboot with no confirm:", loader.state)

_ = loader.tryNewImage(signatureValid: true)
loader.confirmImage()
print("after confirmed image:", loader.state)
```

## 18. References

1. MCUboot Project. "Design".
   https://docs.mcuboot.com/design.html
   Verified 2026-08-21. Source of the bootloader structure, swap
   mechanism, power-cut resilience, and rollback quotes used in
   dimensions 1, 2, 3, 5, 7, 9, and 10.
2. MCUboot Project. "Readme (Zephyr)".
   https://docs.mcuboot.com/readme-zephyr.html
   Verified 2026-08-21. Source of the image-signing and public-key
   verification quotes used in dimensions 3, 5, 9, and 10.
