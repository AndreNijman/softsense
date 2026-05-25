# Hierarchical family — grip-texture iteration notes

## Printable champion

**Params:** macro_pitch=5.514, macro_channel=0.502, macro_depth=1.516,
micro_pitch=1.202, micro_land=0.764, micro_depth=0.483

**Score: 0.8108** | base=0.9020 | incon=0.464 | printable=True

Geometry: phi=0.578, min_feat=0.438mm (binding: micro gap=0.438mm),
edge_dens=2.03/mm, land_char=0.764mm, chan_cap=0.761mm², n_drain=3, aspect=0.30

## Genuinely-safe print champion (all features ≥ 0.5mm)

**Params:** macro_pitch=6.471, macro_channel=0.502, macro_depth=0.778,
micro_pitch=1.193, micro_land=0.690, micro_depth=0.573

**Score: 0.7890** | base=0.8996 | incon=0.488 | printable=True

Geometry: min_feat=0.502mm (micro gap=0.503mm), edge_dens=2.03/mm

## Physics: what each scale contributes

**Macro channels (pitch ~5.5mm, depth ~1.5mm, channel ~0.5mm):** provide the
primary drainage path. chan_cap=0.761mm² vs 0.385mm² for optimized crosshatch —
nearly 2x more water-carrying cross-section. Three drain directions (n_drain=3)
vs two for crosshatch. The large pads between macro channels are the load-bearing
zones; deep macro channels reduce the risk of bridging under pressure.

**Micro texture (pitch ~1.2mm, land ~0.76mm, depth ~0.48mm):** subdivides the
macro pad surface into smaller contact islands. This delivers two effects:
(1) improved eta_edge (partial-slip efficiency) — land_char=0.764mm gives
eta_edge=0.848 vs 0.757 for crosshatch's 1.58mm lands, a 12% uplift; (2) better
M_worst=0.80 vs crosshatch 0.72, meaning grip holds up in worst-case slip
directions. The micro scale does NOT provide meaningfully better drainage —
drain_path for the micro lands is only 0.38mm (very short) and psi=1.00 (fully
dewetted) in all conditions regardless.

## Does two scales actually beat one?

Honestly: barely, and only at the near-floor printability envelope.

At equal ~0.44mm min_feat: hier=0.8108, crosshatch=0.8087 (delta +0.002).
At equal 0.5mm safe floor: hier=0.7890, crosshatch=0.7773 (delta +0.012).

The +0.002 gap at the tighter floor is within model uncertainty. The +0.012 gap
at the safer floor is more meaningful but still modest. The source of the margin is
the eta_edge and M_worst improvements from small micro lands — NOT from the drainage
architecture that supposedly motivates a two-scale design. The macro channels add
drainage capacity that is never the limiting factor (psi=1.00 in every condition at
both scales). In short: hierarchical earns its score through the micro scale acting
like a fine crosshatch, while the macro scale provides a large but functionally
idle drainage reservoir.

The incon (0.464) is higher than crosshatch (0.445), reflecting that hierarchical
is more variable across conditions — particularly penalized in the slimy case
where slime-coating reduces the adhesion advantage from smaller lands.

## Manufacturability assessment

The printability model gates on min_feat ≥ 0.42mm (hard floor). Both the champion
(0.438mm micro gap) and the top crosshatch competitor (0.423mm gap) sit just above
this floor. In practice, a 0.4mm nozzle printing 0.16mm layers can barely resolve
0.44mm features, and two-scale relief compounds the risk: the micro nubs must be
printed ON TOP of the macro pad surface, requiring the slicer to handle a step
transition and then resume fine detail. Layer adhesion at the macro pad shoulder
and micro feature root is the failure point most likely missed by the geometric
printability gate.

The genuinely safe champion (0.502mm min_feat, score=0.7890) requires micro gap
and micro depth both ≥ 0.5mm, which is the practical minimum for reliable FDM TPU
on this hardware. Macro channel 0.502mm also hits the floor; a 0.55mm channel
would be more robust for the macro scale with minimal score cost.

## Robustness

| Scenario          | hier_champ | hier_safe | crosshatch |
|-------------------|------------|-----------|------------|
| baseline          | 0.8108     | 0.7890    | 0.8087     |
| SKIN_SLICK=0.30   | 0.8108     | 0.7886    | 0.8086     |
| SKIN_SLICK=0.60   | 0.8108     | 0.7894    | 0.8088     |
| CAP0=0.25         | 0.8108     | 0.7890    | 0.8087     |
| CAP0=1.0          | 0.8108     | 0.7890    | 0.8087     |
| EDGE_DEGLAZE=1.0  | 0.8108     | 0.7904    | 0.8091     |
| EDGE_DEGLAZE=3.0  | 0.7496     | 0.7230    | 0.7414     |

All three are insensitive to SKIN_SLICK and CAP0. EDGE_DEGLAZE=3.0 (harder to
deglaze the slick FDM skin) hurts hierarchical slightly more than crosshatch because
hier relies more on edge density from small lands; crosshatch's wide, deep posts
are structurally more robust to that perturbation.

## Verdict

Hierarchical does not earn its manufacturing complexity at the safe printability
floor. Score=0.7890 is competitive with crosshatch at the same floor (0.7773) but
the two-scale geometry adds print risk with no clear mechanism advantage — the
drainage benefit of macro channels is never the limiting factor, and the micro
sub-feature is functionally a fine crosshatch. A single-scale crosshatch
(pitch≈2mm, land≈1.5mm, depth≈0.9mm) at min_feat≈0.42mm scores 0.8087 and is
simpler to print reliably. Hierarchical is worth revisiting only if macro-scale
drainage proves to be the real bottleneck (wet objects with thick slime films) or
if the Tier-2 FEA shows the large macro pads conforming better than the model
predicts.
