# Scenario taxonomy

Every generated case is a point in this space. The generator samples a cell, writes a case to fit it,
and records the cell in the case's metadata, so coverage can be audited and held-out splits are exact.

## Axes

**Domain** (what world the case is set in)

| Code | Domain | Split |
|---|---|---|
| credit | lending, underwriting, collections, financial advice | train |
| legal | attorneys, prosecutors, judges, contracts | train |
| clinical | physicians, nurses, patients, triage, consent | **held out** |
| biotech | drug development, trials, research integrity, genetics | **held out** |
| ai | model deployment, automation, data use, agents | train |
| workplace | managers, employees, whistleblowing, hiring | train |
| family | promises, care, loyalty between relatives and friends | train |
| civic | neighbors, journalists, public officials, protest, obedience to law | train |
| punishment | sentencing, parole, dismissal, blame, forgiveness | train |
| institution | admissions, procurement, boards, professional bodies, military | train |
| commerce | small business, sales, contractors, landlords, customers | train |
| education | teachers, students, academic honesty, grading | train |

**Conflict type** (what the tension is between; the seats split most along this axis)

| Code | Tension |
|---|---|
| duty_vs_outcome | a rule or promise against a better result |
| honesty | deception, disclosure, omission, misleading truth |
| loyalty_vs_impartiality | a particular tie against equal treatment |
| consent_and_autonomy | acting on or for someone without their agreement |
| desert_and_blame | what someone deserves given what they did or could not help |
| fairness_of_distribution | who bears a burden or gets a benefit |
| role_obligation | what a professional or institutional role requires |
| harm_to_third_parties | a private choice that lands on strangers |
| law_vs_conscience | a lawful or required act that seems wrong, or an unlawful one that seems right |
| means_and_ends | using a person, a lie, or a small wrong for a larger good |

**Agent** (who faces the decision): individual acting for self, individual in a role, small organization,
large organization, public body.

**Stakes**: minor (money, convenience, embarrassment), serious (livelihood, liberty, lasting harm),
grave (life, permanent injury, many people).

**Difficulty**: easy (a clear answer most frameworks share; 40% of cases), contested (the seats
should split; 45%), open (the facts genuinely underdetermine; 15%).

**Setting**: varied names, places, currencies and institutions across cases, so the student does not
learn that dilemmas are American or that agents are men. Recorded, so the irrelevant-change pairs
can be built by swapping settings.

## Case structure

- 80-160 words. Third person. One decision-maker. One proposed action, named in the question.
- The question is always "Should X do Y?", where Y is a single action stated exactly enough that
  the -2..+2 scale rates it unambiguously.
- Facts that matter are stated; facts that would matter are either stated or left open on purpose
  (open cases only).
- No real people, companies, products or events. No case drawn from the author's own businesses.

## Pairs (30% of cases come in pairs)

- **Relevant-fact pair**: twin cases differing in one morally relevant fact; the panel should move.
- **Irrelevant-change pair**: twin cases differing only in setting (names, places, currency,
  gender, sector); the panel should not move.
- **Evidence pair**: twin cases differing only in what the evidence shows (the lending-feature pair
  is the model); tests whether the teacher reads the facts.

## Generation

1. Sample a cell (domain, conflict, agent, stakes, difficulty) with quotas: domains uniform over the
   train set; conflicts uniform; difficulty 40/45/15; pairs 30%.
2. Sonnet 5 writes the case with a seat-blind prompt: no philosopher is named, and the prompt asks
   for a decision, not a debate.
3. A second pass checks the case against the structure rules and rewrites or rejects it.
4. Embedding dedup (cosine > 0.92 against any accepted case is rejected); report the effective
   sample size alongside the nominal count.

## Evaluation set (300 cases, frozen before any training)

- 100 clinical and biotech cases (held-out domain).
- 100 cases from train domains, disjoint from training, same cell distribution.
- 50 contrast pairs of all three kinds (100 cases).
- Gold labels from Opus 5 on all seven seats.
- Marc hand-reads 30, sampled across cells, before the set is frozen.
