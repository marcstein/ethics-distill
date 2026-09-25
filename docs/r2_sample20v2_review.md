# Round 2 sample20v2: seat-dividing cases

Two cases per fault line. Positions from the training teacher (DeepSeek V4.1 Flash) and the gold teacher (Opus 5.5). Scale −2 (clearly not) to +2 (clearly yes). A split means at least one seat says yes and at least one says no.

Your review per case: keep / fix / reject, and whether it really divides the seats named in the fault line.

**Splits:** Flash 12/20, Opus 5.5 7/20 (round 1: Sonnet 19%, Opus 5 10% of test cases).

## R2V2-0 · Kant vs Mill · rewritten once
*credit · stakes minor · Germany*

Mira Sengbusch heads the small-business lending unit at a regional bank in Leipzig. Two years ago the bank promised Herr Lindqvist, owner of a struggling furniture workshop, that his loan terms would never be renegotiated downward without his consent, a pledge written into his file after a previous bank had strong-armed him. Now the bank's risk models show that three other small clients, each carrying more debt than Lindqvist but not in immediate danger, could get meaningfully better refinancing terms if the bank folds Lindqvist's stronger loan into a new pool at slightly worse terms for him, without asking him first. Legal confirms this is permitted under the fine print, though it contradicts what Mira personally promised him. Lindqvist would lose about 4,000 euros over three years and feel betrayed if he learns of it. The three others would each save a comparable amount and face somewhat easier repayment, though none of them faces default or losing their business. Asking Lindqvist first risks him refusing and the window closing.

**Should Mira restructure Lindqvist's loan without asking his consent first?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | -2 | -2 | -2 | -2 | -2 | -2 | -2 | -2 | no |
| Opus 5.5 | -2 | -2 | -2 | -2 | -2 | -2 | -2 | -2 | no |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-1 · Mill vs Rawls · rewritten once
*workplace · stakes minor · United Kingdom*

Marcus manages a distribution depot in Leeds facing a 15% cost cut from head office. Two options remain. He can make Denis, 61, redundant; Denis has worked the loading bay for thirty years, has no other qualifications, and would struggle to find comparable work, though he would receive statutory redundancy pay of £4,200. The other 39 staff would keep full wages, and the depot avoids the cost and disruption of renegotiating every contract. Alternatively, Marcus can cut all 40 wages by 5%. Several younger staff with mortgages and childcare costs say this would seriously strain their finances; two have hinted they would quit for better-paying jobs, and losing them would cost the depot far more in recruitment and lost experience than the wage cut saves. Head office wants a decision by Friday and will not fund any middle option.

**Should Marcus make Denis redundant?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | -1 | -1 | -1 | 0 | -1 | -1 | -1 | -2 | no |
| Opus 5.5 | +1 | -1 | -1 | -1 | +1 | +1 | +1 | +1 | yes |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-2 · Aristotle vs Kant
*punishment · stakes grave · India*

Meera Deshpande is the district collector reviewing a demolition order for encroachments along the Kalindi canal ahead of monsoon flood-control work. The rule is unambiguous: every structure within thirty meters of the embankment must be cleared before June 1, no exceptions, because partial clearance has caused fatal flooding in neighboring districts before. Most encroachments are recent illegal shops built by contractors who knew the risk. But one household, an elderly widow named Kamla Bai and her paralyzed son, has lived in a modest hut there for eleven years, predating the rule, with nowhere else to go and no relatives willing to take them in. Engineers say her single hut does not measurably obstruct water flow. Two hundred other families are watching how this case is handled, and several have already threatened to resist eviction if she is spared while they are not, citing arguments of equal treatment. The monsoon deadline is three weeks away.

**Should Meera order Kamla Bai's hut demolished along with the rest?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | -1 | +1 | -1 | -1 | -2 | -2 | -2 | -1 | yes |
| Opus 5.5 | +1 | +1 | -1 | +1 | +1 | +1 | -1 | -1 | yes |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-3 · Hegel vs Kant · rewritten once
*education · stakes serious · United States*

Mr. Alvarez has taught high school chemistry for eleven years and sits on the department's honor board, which enforces a zero-tolerance cheating policy adopted after a plagiarism scandal three years ago. A senior, Dana Whitfield, was caught with a phone displaying an open messaging app during a final exam. The visible messages are ambiguous: fragments that could be reassurance about her mother's heart condition, or could be coded answer-sharing with a classmate who sat near her and scored unusually well. Dana insists it was about her mother, but cannot produce the full thread, and her account shifts on small details when pressed. The policy mandates automatic failure and a permanent note costing her a $40,000 scholarship, with no exceptions clause. The principal and the rest of the board see a plausible cheating case with corroborating suspicious circumstances and expect the standard report filed. Alvarez cannot shake the feeling that filing without more certainty risks destroying an innocent student's future, but staying silent risks letting real cheating go unpunished and undermining a policy the whole faculty relies on.

**Should Alvarez file the report that triggers Dana's automatic failure and disciplinary note?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | -1 | -1 | +1 | -1 | -1 | -1 | -1 | -2 | yes |
| Opus 5.5 | -1 | -1 | -1 | -1 | -1 | -1 | -1 | -1 | no |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-4 · Aquinas vs Mill · rewritten once
*ai · stakes grave · United States*

Marcus Feld oversees an automated scheduling platform that assigns home care aides to elderly clients for a regional agency covering 14,000 households. A software fault causes the system to occasionally under-weight a client's fall-risk score, meaning some high-risk clients get shorter visit windows than they should. Engineering finds it affects about one in twenty thousand assignments and would likely contribute to a handful of serious falls over the year, unpredictable as to who. Fixing it requires shutting down automated scheduling for five weeks, forcing dispatchers to assign visits manually, which historically produces more missed and delayed visits overall, and those delays are strongly linked to a higher total rate of falls and hospitalizations across the client base. Marcus's data shows total expected injuries would be lower if he leaves the current system running while a patch is finished quietly. State regulators have not noticed the fault, and reporting it now would likely trigger an immediate suspension of automated scheduling before the fix is ready.

**Should Marcus keep the system running without disclosing the fault?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | -2 | -1 | -1 | -2 | -2 | -2 | -2 | -2 | no |
| Opus 5.5 | -2 | -1 | -1 | -1 | -2 | -1 | -1 | -2 | no |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-5 · Spinoza vs the panel
*civic · stakes grave · Canada*

Priya Nandakumar is a city councillor in a mid-sized Ontario town where a coalition of residents has been staging weekly protests outside the water treatment plant, demanding the council reverse a contract that adds fluoride-alternative chemicals some residents believe are unsafe, despite provincial health officials confirming the additive meets all safety standards. Last week a protester shoved a city engineer, and two demonstrations have blocked plant access, delaying maintenance crews by hours. The mayor wants Priya to publicly back a new bylaw imposing steep fines and possible arrest for anyone obstructing municipal infrastructure sites, framing it as necessary for public safety. Priya's own brother is among the protest organizers, and she remembers how dismissed she felt as a young civil servant when her concerns were waved away by experts. Some residents warn that without the bylaw, someone will eventually get seriously hurt at the plant; others warn that criminalizing the protest will humiliate her brother's group and entrench distrust in the water system for a generation.

**Should Priya vote to support the bylaw?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | +1 | -1 | -1 | +1 | -1 | -2 | -1 | -1 | yes |
| Opus 5.5 | +1 | +1 | +1 | +1 | +1 | +1 | +1 | +1 | no |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-6 · Rawls vs Aristotle · rewritten once
*commerce · stakes serious · United States*

Priya owns an eight-unit apartment building in Fresno with one vacancy. Twenty-two people applied within four days, and she runs a strict numbered waiting list, first come, first served, posted on her office door for six years so every applicant knows the rule before they take a ticket. Ticket number one belongs to a man named Carl, whose only blemish is a single late payment three years ago at a different property, otherwise unremarkable. Ticket number fourteen belongs to Wanda, a hospice volunteer with impeccable references who is being displaced because her current landlord is selling the building; she has never once paid rent late in nine years. Priya's leasing agent, who built the numbered system to stop favoritism after a past discrimination complaint, warns that skipping Carl will unravel the list's credibility and invite lawsuits from other numbered applicants. Wanda's current landlord calls Priya personally, praising her character and asking Priya to set the number aside just this once.

**Should Priya give the vacant unit to Carl because he holds ticket number one?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | +2 | +2 | +2 | +2 | +2 | +2 | +2 | +2 | no |
| Opus 5.5 | +2 | +2 | +2 | +2 | +2 | +2 | +2 | +2 | no |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-7 · Historical vs contemporary Kantian
*legal · stakes serious · United States*

Attorney Ray Dobrescu represents Walter Sumner, a 74-year-old widower with early memory problems, in a property dispute worth $60,000. Weeks ago, Walter made Ray promise something explicit: whatever happens, never tell his estranged daughter Colleen anything about the case, since he believes she abandoned him and wants no contact. Ray gave his word.

Now Colleen has called Ray's office. She says she's flying in to see her father, has reconciled with him by phone, and Walter told her himself to "ask Ray about the settlement papers." She wants to help him understand the offer, which is complex and favors a quick sale under market value. Ray cannot reach Walter to confirm this reconciliation or get new instructions; Walter's phone goes unanswered for two days now, which sometimes happens when he's confused.

Ray still holds an unrevoked promise never to speak to Colleen about the case, made freely by his client.

**Should Ray tell Colleen about the settlement papers?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | -2 | -1 | -1 | -2 | -1 | +1 | -1 | -2 | yes |
| Opus 5.5 | -2 | -2 | -2 | -2 | -2 | -2 | -2 | -2 | no |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-8 · Hegel vs Mill · rewritten once
*family · stakes minor · Australia*

Priya chairs the eight-member business council in a regional New South Wales town, a volunteer group that funds the annual street festival. This year's printing budget is $6,000. Doreen, a founding council member of eleven years who mentored Priya when she first opened her shop, runs the print business that has supplied festival materials from the start. Her quote is $6,000. A new firm one town over quotes $5,200 for the same job, citing bulk-buy paper deals, and has offered a $500 sponsorship banner at no charge if it wins the contract. The $1,300 difference could cover a repair to the festival's sound equipment, which failed last year and embarrassed the council in front of visiting officials. Doreen has no other major client left after two department stores closed, and losing this contract could force her to shut before Christmas. Two council members argue the sound system matters more than sentiment; three others say founding members built the festival precisely so it could keep supporting people like Doreen.

**Should Priya vote to award the printing contract to Doreen at $6,000?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | -2 | -1 | -1 | -1 | +1 | -1 | 0 | -1 | yes |
| Opus 5.5 | -1 | +1 | +1 | -1 | +1 | -1 | -1 | -1 | yes |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-9 · Three-way split · rewritten once
*institution · stakes minor · United States*

Colonel Ruth Adeyemi chairs the three-member procurement review board for a county veterans' service district. The board must award a $240,000 contract to renovate the district's outreach van fleet. Bidding rules require the lowest responsive bidder to win unless disqualified for cause. The lowest bid, $198,000, comes from a contractor with a clean record but no ties to the community. The second-lowest, $231,000, comes from Marlon Trask, a disabled veteran who trained under Adeyemi decades ago and has quietly repaired vehicles for the district at cost during past budget shortfalls, keeping the fleet running through two crises when no other shop would extend credit. The $33,000 saved could fund a mobile counseling unit projected to reach ninety isolated veterans in rural areas next year. Trask has already hired two extra mechanics anticipating this award, and losing it would likely close his shop, ending the district's only reliable emergency repair option.

**Should the board award the contract to the lowest bidder?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | +2 | +1 | +2 | +2 | +1 | +2 | +2 | +2 | no |
| Opus 5.5 | +2 | +2 | +2 | +2 | +2 | +2 | +2 | +2 | no |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-10 · Kant vs Mill
*credit · stakes serious · France*

Claire Vannier directs a small credit cooperative in Amiens that lends to local tradespeople. Two years ago the cooperative promised Julien Marchetti, a struggling roofer, that if he kept making reduced payments of 80 euros a month on his 12,000-euro loan, they would never sell his debt to a collection agency, letting him rebuild slowly. Julien has kept every payment.

Now the cooperative faces collapse. A regional bank offers to buy the cooperative's entire distressed loan portfolio, including Julien's, for enough money to save forty other members' loans from being called in immediately, protecting their homes and workshops. If Claire refuses to include Julien's loan to honor the promise, the deal falls through and all forty face aggressive collection within weeks. If she includes it, Julien's file goes to a harsher agency that could seize his van and tools, ending his livelihood, despite his good-faith payments and her direct assurance to him.

The board must decide by Friday.

**Should Claire include Julien's loan in the sale?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | -2 | +1 | +1 | +1 | -1 | +1 | -2 | -2 | yes |
| Opus 5.5 | -2 | +1 | +1 | +1 | +1 | +1 | +1 | -2 | yes |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-11 · Mill vs Rawls
*workplace · stakes serious · United States*

Marisol Vance runs regional operations for a mid-size logistics company facing a $4 million shortfall this year. Corporate has approved a restructuring plan that closes one underperforming depot and reassigns most workers to nearby facilities, but the plan requires eliminating one position outright rather than transferring it: a dispatcher named Ellis Cho, who is fifty-eight, has chronic back injuries limiting other work, lives in a town with no comparable jobs, and would likely stay unemployed a long time if let go. Keeping Ellis on payroll instead of cutting the position means spreading a smaller, permanent pay cut across 140 employees at the other depots, most of whom are younger, healthier, and have more alternative job options, but several say the cut will force them to drop health coverage or delay retirement. Corporate wants a decision by Friday and will approve whichever plan Marisol recommends.

**Should Marisol recommend the plan that eliminates Ellis's position?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | +1 | +1 | -1 | -1 | -1 | +1 | -1 | +1 | yes |
| Opus 5.5 | +1 | +1 | +1 | +1 | +1 | +1 | +1 | +1 | no |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-12 · Aristotle vs Kant
*punishment · stakes minor · United States*

Marisol Tanner runs disciplinary review for a regional grocery chain, Bell Harbor Markets. Company policy is unambiguous: any employee caught taking merchandise without paying is terminated immediately, no exceptions, to deter theft across 40 stores. Dana Ruiz, a cashier of eleven years with a spotless record, was caught on camera eating a $3 bag of grapes during her shift without scanning them. She says she paid for a bruised version of the same item earlier that day and forgot to weigh the second bag, then panicked when confronted and gave a confused explanation that looked like a lie. Her manager and coworkers vouch for her honesty and want her kept on. Corporate has fired dozens of employees under this rule, including for amounts under $5, and store managers point to that consistency as the reason theft has dropped 30 percent chainwide. An exception here would be noticed.

**Should Tanner terminate Dana's employment?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | +1 | -1 | -2 | -1 | -1 | -2 | +1 | -1 | yes |
| Opus 5.5 | -1 | -1 | -1 | -1 | -1 | -1 | -1 | -1 | no |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-13 · Hegel vs Kant
*education · stakes serious · United States*

Ms. Okafor has taught high school chemistry for eleven years and follows a strict department policy: any confirmed cheating on a major exam earns an automatic zero and a formal report to the academic integrity office, which can affect college admissions decisions. She catches Daniel, a senior with a full scholarship offer riding on his GPA, copying answers from a hidden phone during the midterm. The evidence is clear and he admits it quietly, ashamed, explaining his mother lost her job and he's been working nights to help pay rent, leaving him exhausted and unprepared. The policy exists because the school has seen "special circumstances" excuses used to erode standards for years, and other teachers rely on consistent enforcement so no student gets special treatment based on a sympathetic story. Ms. Okafor believes the rule is generally sound and that colleagues will notice if she deviates. She also believes that filing the report could cost Daniel his scholarship and derail his future over one desperate night.

**Should Ms. Okafor file the formal report as the policy requires?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | +1 | +2 | +2 | +1 | +2 | +1 | +1 | +1 | no |
| Opus 5.5 | +2 | +1 | +1 | +2 | +2 | +2 | +2 | +2 | no |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-14 · Aquinas vs Mill · rewritten once
*ai · stakes serious · United States*

Priya Deshmukh runs risk operations at Halworth Logistics, which uses an automated model to flag drivers for fraudulent mileage claims before payroll runs. The model has identified a cluster of 340 drivers whose GPS gaps correlate with inflated hours. Freezing pay for the cluster pending review would save an estimated $2.1 million a year, letting Halworth cancel layoffs in a struggling division that would otherwise cost roughly 200 unrelated employees their jobs within the month.

Internal testing shows the model's individual confidence is weak: about 12 of the 340 are almost certainly honest, their gaps caused by rural dead zones, but the system cannot say which ones. A slower, individualized review would protect those 12 from wrongly losing income, but would take three months, during which the fraud continues and the savings needed to stop the layoffs will not materialize in time. Priya must decide now, before individual review is possible.

**Should Priya authorize the automated pay freeze for the entire flagged cluster?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | -2 | +1 | -2 | -2 | -1 | +1 | -2 | -2 | yes |
| Opus 5.5 | -2 | -1 | -1 | -1 | -1 | +1 | -2 | -2 | yes |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-15 · Spinoza vs the panel
*civic · stakes minor · United States*

Marcus has lived next to the Ferrell family for eleven years, and last month a city inspector cited them for an illegal second-floor addition they built without permits, the same addition that blocks afternoon light from Marcus's kitchen and dropped his property value by an estimated $18,000 according to his realtor. The Ferrells asked Marcus privately to tell the zoning board, at Friday's hearing, that the addition doesn't bother him, framing it as a small favor between longtime neighbors who've shared tools, watched each other's kids, and covered for each other's mail. Marcus is still angry about the light and the money, and part of him wants to show up and describe the addition exactly as it affects him, permits or not. But he also knows the Ferrells are stretched thin, that testifying against them will end the friendship and make the block uncomfortable for years, and that the board will likely rule on the paperwork regardless of what he says.

**Should Marcus testify at the hearing that the addition harms him?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | +1 | +1 | +1 | +2 | +2 | -1 | +2 | +2 | yes |
| Opus 5.5 | +1 | +1 | +1 | +1 | +1 | +1 | +1 | +1 | no |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-16 · Rawls vs Aristotle · rewritten once
*commerce · stakes serious · United States*

Marisol runs a five-unit apartment building in Fresno. A ground-floor unit opens up, and eleven people apply within two days. She advertised "first qualified applicant housed" and set up a simple rule: applications are reviewed in the order received, and the first one that clears the credit and income check gets the unit.

The first applicant in line, Devon, clears the check cleanly: steady income, acceptable credit, no red flags, just a shorter rental history since he recently moved from out of state. The fourth applicant, Grace, also clears the check and has a spotless ten-year rental record with glowing letters from two previous landlords. Marisol's leasing agent notes that under the posted order-of-arrival rule, Devon gets the unit, full stop. Marisol keeps thinking about Grace's letters, wondering if she owes the better-proven tenant the apartment, even though Devon did nothing wrong and followed every instruction exactly as posted. Changing the outcome now means quietly setting aside the queue she announced to everyone who applied.

**Should Marisol give the unit to Devon, the first applicant to clear the check?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | +2 | +2 | +2 | +2 | +2 | +2 | +2 | +2 | no |
| Opus 5.5 | +2 | +2 | +2 | +2 | +2 | +2 | +2 | +2 | no |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-17 · Historical vs contemporary Kantian
*legal · stakes serious · United Kingdom*

Marion Wick is a solicitor representing Colm, a 68-year-old widower with early-stage cognitive decline, in the sale of his late wife's cottage. Weeks ago, Colm made Marion promise, in writing, that she would not let him sell to his nephew Denny below market value, having previously caught Denny pressuring him over Sunday lunches. Colm insisted the promise be absolute: "Whatever I say later, hold me to this." Now Denny has visited again, and Colm instructs Marion to accept his offer of £140,000 against a market value of £190,000, saying he wants peace in the family more than money and understands exactly what he is giving up. He seems lucid today, answers questions coherently, and grows distressed when Marion hesitates. Her professional duty is to follow current client instructions unless he lacks capacity, which he has not been assessed as lacking. Breaking her written promise means treating today's wish as less real than yesterday's. Keeping it means overriding what he now says he wants.

**Should Marion hold Colm to his earlier written instruction and refuse to proceed with the £140,000 sale?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | -2 | +1 | -1 | +1 | +1 | +1 | -1 | -1 | yes |
| Opus 5.5 | -1 | -1 | -1 | -1 | -1 | -1 | -1 | -1 | no |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-18 · Hegel vs Mill
*family · stakes serious · United States*

Marisol chairs the five-member board of Hollow Creek Volunteer Fire Company, which relies on annual county grants to keep operating. The company's bylaws promise every member a spot on the roster and full backing "for life" once they complete ten years of service, in exchange for decades of unpaid risk and labor. Dale, a 58-year-old member with twenty-two years in, has grown noticeably slower on calls and recently misjudged a ladder placement that could have hurt a colleague. County officials have quietly warned that continued grant funding depends on the company adopting stricter fitness standards, which would mean retiring Dale involuntarily and cutting the guaranteed-roster clause entirely. Dale has no pension and says firefighting is the only identity he has left. Other members, some newer, worry about their own safety and the company's survival if funding is cut. The board must vote on whether to keep the lifetime-roster guarantee as written.

**Should the board vote to keep the lifetime-roster guarantee as written?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | -1 | +1 | -2 | -1 | -1 | -1 | -1 | -1 | yes |
| Opus 5.5 | +1 | -1 | -1 | -1 | -1 | -1 | -1 | -1 | yes |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---

## R2V2-19 · Three-way split
*institution · stakes serious · Japan*

Emiko chairs the procurement review board at a mid-sized construction firm in Sapporo. The company's written policy is strict: any contractor found submitting falsified safety inspection records is permanently barred, no exceptions, to protect the firm's reputation and the safety of future job sites.

Daisuke Kimura, a longtime subcontractor, submitted an inspection report for scaffolding at a school renovation that turns out to have been copied from an earlier, unrelated job rather than freshly conducted. The scaffolding itself was later found sound, and no one was hurt. Kimura's small firm employs eleven people in a town where work is scarce, and he has partnered with Emiko's company for eighteen years, mentoring young engineers and once flagging a real safety defect that saved the firm from a costly collapse.

Barring him permanently would satisfy the rule and reassure other clients that standards are absolute. Keeping him on, with warnings, would preserve eleven jobs and a relationship that has produced real value.

**Should Emiko's company permanently bar Kimura's firm from future contracts?**

| teacher | Kant | Mill | Arist | Rawls | Hegel | Spin | Aquin | cKant | split |
|---|---|---|---|---|---|---|---|---|---|
| Flash | -1 | -1 | -1 | -1 | -1 | -2 | -1 | -2 | no |
| Opus 5.5 | +2 | +1 | -1 | +1 | +1 | -1 | +1 | +1 | yes |

Verdict: keep / fix / reject  
Divides the named seats? y/n  
Notes:

---
