# Scale-up: 1.5× and 2.0× variants (underwater-archaeology sizing)

The shipped 1× gripper is small (jaw opens to ~118 mm at the fingertips, per-finger
force 0.14–0.73 N) — too small and too weak to recover typical underwater-archaeology
finds. This rebuild scales the **entire** gripper **self-similarly** to two larger
sizes, **1.5×** and **2.0×**, and re-runs every sim/FEA/stat at the new sizes.

Both variants are generated from the same parametric source by one env var:

```bash
GRIPPER_SCALE=1.5  python scripts/export_parts.py     # -> variants/scale_1.5x/parts
GRIPPER_SCALE=2.0  python scripts/export_parts.py     # -> variants/scale_2.0x/parts
```

`SCALE=1.0` reproduces the canonical 1× model byte-for-byte (the scaling code is
proven neutral at 1×), so the original design is preserved as the reference.

---

## 1. What "self-similar" means here (and what does NOT scale)

Every **linear design dimension** is multiplied by the scale factor `k` — the linkage
(crank/follower/coupler), the gears (pitch radii, tooth heights, face widths), the
**finger walls** (the key fix — see §3), the enclosure, the input shaft, the flange,
and the snap-clips. Because lengths, radii and thicknesses all scale together, the
**wall/blade ratio, gear module ratio, and every angle are preserved** — true
mechanical similitude. (Verified: finger rotation is identical −20.07° at 1.0/1.5/2.0×,
and the kinematic opening scales exactly ×k.)

Deliberately **held constant** (these are not functions of part size), each documented
inline in `gripper.py`:

| Held | Why |
|---|---|
| Print/tolerance clearances (`PRINT_CLEAR` 0.3, mesh/bore running gaps, snap-pin counterbore clears) | Set by the 0.4 mm FDM nozzle, not the part. The *nominal* scales, the additive gap is held → running fits stay ~0.3 mm at every scale. |
| Fastener sizes (M4 bolts, M3 taps) | An M4 is M4 at any scale; only the bolt-pattern **positions** scale. (See §6 — at 2× consider M5/M6 for the higher loads.) |
| Flood / drain / vent hole **radii** | Sized by absolute bubble/surface-tension + FDM-floor physics; positions scale. |
| Edge-break chamfers / fillets (`DFM_EDGE`, `CHAM_*`, `R_VERT`, finger fillets) | Manufacturing finishes; held (also keeps fillet ops robust). |

The grip **micro-texture** (crosshatch posts) **does** scale (channels 0.54→0.81→1.08 mm)
— this is grip-safe because the wet-grip campaign found grip is *grip-neutral above a
~0.3 mm channel* (drainage saturates), and every scaled channel stays above that. Scaling
it (vs holding absolute) keeps the post **count** constant, which is what makes the bigger
finger printable in reasonable time.

---

## 2. Size & kinematics (verified from the CAD)

| Quantity | 1.0× (ref) | **1.5×** | **2.0×** |
|---|---|---|---|
| Finger blade length | 90 mm | **135 mm** | **180 mm** |
| Jaw opening at tip (open) | 124 mm | **186 mm** | **248 mm** |
| Jaw opening at base (open) | 62 mm | 93 mm | 124 mm |
| Jaw gap (closed) | 9.9 mm | 14.8 mm | 19.7 mm |
| Assembly footprint (bbox) | 100.8 × 31 × 162 | 150.8 × 46.5 × 243 | 200.8 × 62 × 324 mm |
| Solid material volume | 56.5 cm³ | 197.4 cm³ | 473.4 cm³ |
| ≈ printed mass (100 % dense, ~1.15 g/cm³) | ~65 g | **~0.23 kg** | **~0.54 kg** |
| Longest single part | 100.8 mm | 151 mm | 201 mm |
| Print plates (256 mm P1S bed) | 3 | **3** | **4** (rigid splits to 2) |

All parts fit the 256 mm Bambu P1S bed at both scales (`make_print_plates` raises if a
part exceeds the bed — clean pass at 1.5× and 2.0×).

---

## 3. Why the bigger finger now actually grips (the headline)

The shipped finger is a Fin-Ray blade with **fixed-thickness walls**. The old
`fea/SCALABILITY.md` study scaled the **blade only** and found the finger went floppy
above ~1.1× (universal grasp score 0.645 at 1× → 0.441 at 1.5× → 0.368 at 2× — the walls
stayed thin relative to the bigger blade, so it bent instead of squeezing).

Self-similar scaling fixes exactly this: the **walls scale with the blade**, so the
wall/blade stiffness ratio is constant and the bigger finger is as stiff (relative to its
size) as the validated 1× finger.

**FEA confirms it (3-object screen battery, local — MSI down).** On the matched-material
basis (E = 40 MPa, the same modulus the old blade-only study used) the self-similar finger
holds a **flat** universal score and reaches the 12 N stress-probe at every scale:

| Universal grasp score | 1.0× | 1.5× | 2.0× |
|---|---|---|---|
| **Self-similar (walls scale)** — E40 basis | 0.632 | **0.598** | **0.619** |
| Old **blade-only** (walls fixed) — E40 basis | 0.645 | 0.441 | 0.368 |
| Small-circle grip reached | 12.0 N | 12.3 N | 13.5 N |
| (blade-only could only reach) | 12 N | ~3.6 N | ~2.7 N |

On the current Bambu TPU 95A HF material (E = 9.8 MPa, ~4× softer) the 12 N probe isn't
reached within the stroke at any size, but the score still does **not** fall — it edges up
0.484 → 0.543 → 0.591, because the bigger finger develops more absolute grip at the same
proportional closure. Either way the up-scaling **floppy/under-grip failure is fixed**.

*Honest scope:* this fixes the under-grip failure mode, **not** conformance — round-object
wrap is modest at every scale (it's a force-reach + safety result, not a wrap result). The
von-Mises safety margin stays >1.5× but does dip toward 2× (9.1× → 5.3× → 4.8× on flat
boxes — still safe). Full numbers + caveats in `fea/SCALABILITY.md §7`.

---

## 4. Drivetrain, motor, underwater, grip (re-run at both scales)

**Gear ceiling & force envelope** (`motor/DRIVETRAIN.md`, `motor/SELECTION.md`) — confirmed to
3 sig figs on the self-similar radial-crown FEA:

| | 1.0× | 1.5× | 2.0× |
|---|---|---|---|
| `T_safe` (gear bind, radial 2D) ∝ **k³** | 0.0131 | 0.0442 | 0.105 N·m |
| per-finger force band ∝ **k²** | 0.14–0.28 | 0.31–0.64 | 0.55–1.13 N |
| servo over-torque vs `T_safe` (smallest, STS3215) | 224× | 67× | **28×** |

The selected servos still clear the gear ceiling by **28–725×** at every scale, so the gripper
stays **gear-limited** and the firmware current-limit remains the gear protection. Force grows
~k² but is still capped below the 12 N finger probe — a *functional absolute* grip still needs the
proposed gear module re-size (scale-invariant finding). (Two non-self-similar tooling scripts —
`gear_fea_3d.py`, `torque_chain.py` — were caught and excluded from the scaling headline; flagged
for an MSI self-similar re-run.)

**Underwater crush** (`fea/UNDERWATER_FEA.md`) — **scale-invariant**, as similitude predicts:
the von-Mises field and material-yield depth are unchanged (peak vM 12.58 MPa @100 m, yield
~177 m at all scales); only **displacement scales ∝ k**. A coordinate-scaled control gives *exact*
invariance (vM 12.58074 MPa identical to 5 dp); the re-meshed runs show a tiny +2.5%/+6.5%
discretization residual from the held absolute-size finish features. Flooded stays vM ≈ 0.

**Wet grip** (`grip/GRIP_TEXTURE.md`) — nuanced (the swarm corrected an over-simple premise):
the **cited-physics core is scale-invariant** (−0.5% over 1→2×; drainage stays in the saturated
plateau, channels 0.81/1.08 mm ≫ 0.3 mm), but the **full surrogate score softens −11.6%/−22.2%**
at 1.5×/2× because bigger posts mean fewer skin-breaking **edges per area** at the fixed 0.16 mm
print resolution. This is a real (if low-confidence) effect, not an artifact; ranking and
printability are preserved. A finer-relative texture could be reintroduced at 2× to recover edge
density (out of scope for a pure self-similar scale-up).

---

## 5. What to print

Pick a scale and print everything in its variant tree:

```
variants/scale_1.5x/parts/    # 10 STL + STEP, MANIFEST.md
variants/scale_1.5x/plates/   # plate_{petg,rigid,tpu}_1.stl  (3 plates)
variants/scale_2.0x/parts/
variants/scale_2.0x/plates/   # plate_{petg,rigid_1,rigid_2,tpu}_1.stl  (4 plates)
```

Materials and orientations are unchanged from 1× (PA12-GF rigid, PETG snap-pins, TPU
fingers); see each variant's `parts/MANIFEST.md`. Assembly is identical to the 1× (the
input shaft still installs from below, pinion-first).

---

## 6. Honest framing & downstream changes

- **Force is bigger but still gear-limited.** Self-similar scaling raises the deliverable
  grip force ~k² (≈ 2.25× at 1.5×, 4× at 2×) and the gear ceiling ~k³, but the gripper is
  still **gear/motor-current-limited**, not a high-force industrial jaw. The repo posture
  stays rank/size, not certified absolute newtons.
- **Mounting interface changed.** The flange bolt-pattern and the D-coupler scale (the
  coupler must transmit ~k² torque), so the 7 separate mounting **adapters**
  (`motor/cad/adapters/`) must be re-scaled to re-mate. Consider stepping the flange bolts
  up to **M5/M6** at 2× given the higher loads (currently kept at M4).
- **Compute caveat:** these re-runs were done **locally** (the MSI FEA node was
  unreachable); FEA used screen/coarse modes for the comparative rankings. A
  high-fidelity MSI re-run is the follow-up for publication-grade fields.
