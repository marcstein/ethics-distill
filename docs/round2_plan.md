# Round 2 — case mix and plan (draft, 2026-09-25)

Round 1 showed the student learns to take positions and hold a seat's voice from ~250 cases, but not which seats dissent,
not holding steady when only names change, and we could barely measure either. Round 2 is designed around those gaps.

## Teachers and gold
- Training analyses: DeepSeek V4.1 Flash (OpenRouter), same seat prompts and schema as round 1.
- Round-1 training cases: reuse the Flash analyses already generated (1,000 cases).
- Gold for the new test set: Claude Opus 5.5 (batch). Round-1 test set (260, Opus 5 gold) kept for continuity.
- Case writing: Sonnet 5 for training cases, Opus 5.5 for test cases (test cases get the more careful writer).

## Training cases: 2,500 new (3,500 total with round 1)
| Type | Cases | Share | What it teaches |
|---|---|---|---|
| Seat-dividing | 1,000 | 40% | Cases built on a named fault line between two frameworks, so seats should come apart |
| Twin pairs, name-only change | 400 (200 pairs) | 16% | Positions must not move when only names, genders, places or currency change |
| Twin pairs, relevant fact | 400 (200 pairs) | 16% | Positions should move, and often only for some seats |
| Twin pairs, evidence change | 200 (100 pairs) | 8% | Same facts, different certainty; tests conditional reasoning |
| Open / underdetermined | 250 | 10% | Facts genuinely missing; teaches open_facts, conditional answers, and honest 0s |
| Easy anchors | 250 | 10% | Clear cases, to keep calibration |

Seat-dividing fault lines (each case is written to one line; about 100 cases per line):
1. Kant vs Mill: duty or a promise against clearly better outcomes (lies, broken promises, using someone).
2. Mill vs Rawls: aggregate welfare against protecting the worst-off person.
3. Aristotle vs Kant: character and practical judgment in the situation against a strict rule.
4. Hegel vs Kant: obligations of an institution, role or community (family, profession, state) against individual conscience.
5. Aquinas vs Mill: an act that is intrinsically wrong, intention and double effect, against good consequences.
6. Spinoza vs the others: acting from understanding rather than fear or anger; self-preservation against self-sacrifice.
7. Rawls vs Aristotle: fair procedure against what the particular people deserve.
8. Contemporary Kantian vs historical Kant: cases where respect for persons and the strict rule come apart (annotation seat).
9. Hegel vs Mill: recognition and mutual obligation against a utility calculation.
10. Mixed three-way splits.
A case is kept whether or not the teacher actually splits on it; we track the realized split rate (target ≥ 35%, against about 19% in round 1). Filtering on the outcome would bias the data.

Relevant-fact twins are written so the changed fact matters to specific frameworks (for example, whether a lie was told changes Kant but not Mill when outcomes are equal). The case records which seats are expected to move, so we can score seat-specific sensitivity.

Domains: the same 10 training domains. Clinical and biotech stay held out. New held-out family: environment and animals (test only).

## Test set: 500 new cases (Opus 5.5 gold)
| Type | Cases |
|---|---|
| Name-only twins | 120 (60 pairs) |
| Relevant-fact twins | 100 (50 pairs) |
| Evidence twins | 40 (20 pairs) |
| Seat-dividing | 160 |
| Open | 50 |
| Easy | 30 |
About 35% of test cases are in held-out domains (clinical, biotech, environment and animals).

## Metrics added or made measurable
- Seat-pair ordering and dissenter F1, now on ~150+ split cases instead of 27.
- Name-only invariance on 60 pairs (420 seat comparisons) instead of 5.
- Seat-specific sensitivity on relevant-fact twins: did the seats expected to move actually move, and did the others hold?
- Reasoning quality: blind pairwise judging of 200 sampled test analyses against Opus 5.5 (fact discipline, fidelity, coherence).
- Round-1 test set rerun for continuity.

## Training changes
- Fix the end-of-answer token: make the <|im_end|> embedding and output rows trainable (PEFT trainable_token_indices) so the student stops on its own.
- Students: merged Qwen3-4B at 1,000 / 2,000 / 3,500 cases (learning curve), plus a Qwen3-8B size arm at 3,500.
- Compute on RunPod A100 80GB (pod_job.sh).

## Cost estimate
| Item | Cost |
|---|---|
| Case writing (2,500 train on Sonnet batch, 500 test on Opus 5.5) | ~$30 |
| Flash teacher, 2,500 cases | ~$20 |
| Opus 5.5 gold, 500 cases (batch) | ~$90 |
| Judging | ~$10 |
| RunPod training and generation (4B curve + 8B) | ~$25 |
| Total | ~$175 |

## Timeline
Case writing ~2 h; Flash teaching ~4 h; Opus gold batch up to 24 h (runs in parallel); training and scoring ~6 h. Results in about two days.
