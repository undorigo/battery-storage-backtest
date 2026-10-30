# Decisions and results, stage by stage

The full record behind the README: every decision with the alternatives it rejected, and every
stage's detailed results. It was moved here word for word from the README on 30 October 2026, so the
README could open with the result. Where the text says "this page", it means the README, where it
was written. Every number here regenerates from a command it names, like every number in the README.

New decisions are added here as they are made; the README keeps the short version.

## Where this is going

Six stages. Each one ends on a number, and no stage starts before the previous number exists —
so a claim can always be traced back to the run that produced it.

| Stage | Delivers | Headline number | Status |
|---|---|---|---|
| 0 | Reproducible data pull, split locked | negative hours, daily spread | **done** 17 Sep 2026 |
| 1 | First model against a naive benchmark | rMAE 0.532 *(last week)* | **done** 30 Sep 2026 |
| 2 | Recalibration, LEAR, holidays | **rMAE 0.485** *(0.405 last week)* | **done** 14 Oct 2026 |
| 3 | Quantile forecasts: QRA on LEAR, conformal beside it | **pinball 4.655** *(QRA, four windows averaged)* | **done** 19 Oct 2026 |
| 4 | Price-dependent bids and a MILP schedule, revenue | **capture rate 90.1 %** *(bids on LEAR, strict rule; 94.0 % pair)* | **done** 27 Oct 2026 |
| 5 | Drift monitoring, scheduled run, a web page | reproducibility | next |

**Read this before any number on this page: the yardstick changed on 15 October 2026, at the
close of stage 2.** An rMAE is our error divided by a simple rule's error. Until then the rule was
"same hour last week". The field's rule is "same hour yesterday" from Tuesday to Friday and last
week from Saturday to Monday (Lago et al. 2021, epftoolbox). Yesterday is usually the closer guess,
so the field's rule is harder to beat, and every ratio against it is higher. **From the close of
stage 2 on, every rMAE is divided by the field's rule**, with last week's beside it. **Every number
dated before 15 October — stage 1's 0.532 and every figure in the stage 2 steps below — was divided
by last week's price** and is left as it was. Rankings and p-values do not change: every model shares
the denominator, and the significance test does not use it. The 2023 and held-back runs were
repeated to get both ratios (`9b2ed8d`); the last-week ratios came out identical to the last digit,
and the held-back forecasts were refitted identically, not re-chosen.

Stage 4 is the one the rest exists for. Everything before it makes the capture rate mean
something; without stages 0–3 it would be a number with no provenance.

**Decided 15 October: stage 3 forecasts a range, and stage 4 bids with it.** A battery that
commits one fixed schedule and ignores risk needs only the average forecast, so a range alone would
change nothing it does. The real auction also takes price-dependent bids ("charge at 03:00 only
below 60 €/MWh"), and those need a range to set the limit. So stage 3 turns LEAR's daily forecasts
into quantiles the way the field does (*Quantile Regression Averaging*, Nowotarski & Weron 2015;
compared in Lipiecki, Uniejewski & Weron 2024), with *conformal prediction* — a band read off past
misses — as the simple comparison, scored by pinball loss and coverage on 2023. Stage 4 bids with
those quantiles, as in Nitka & Weron (2023), and keeps the fixed schedule beside the bids, so the
capture rate shows in euros whether the range was worth having.

**Decided 20 October: a buy and its sell are sent as one package, which goes through whole or not at
all** (the exchange's *loop blocks*; Hirsch & Ziel 2026). Each order still carries a limit price,
set from the range before the auction closes. So the battery never ends a day half-traded, and every run — perfect
foresight, naive, fixed schedule, bids — keeps the same one-day convention, each day ending empty.
Rejected: starting each day half full and fixing a one-sided day with an unlimited order the next
day (Nitka & Weron 2023, and most papers), because it uses half the battery and would change the
ceiling; a fixed schedule only, because it postpones the question. **Checked 21 October:** EPEX
still offers loop blocks after the 15-minute switch (*Trading at EPEX SPOT*, February 2026), and one
block can cover several hours, not necessarily adjacent (EUPHEMIA public description, December
2025).

**Checked 22 October, from EPEX's own documents.** Loop blocks have run on the German day-ahead
since 12 December 2018 (EPEX press release, 13 December 2018). *Each block on its own, or the pair?*
EPEX states the pair rule for its own loop blocks, though in its GB frequency auction: "If accepted,
the surplus of the loop family must be non-negative" (*FRA algorithm – Public description*, 2022).
EUPHEMIA's rules for linked blocks give the same if each block of a loop is the other's parent. No
document for the German day-ahead says so. *Several loops a day?* EPEX's block parameters sheet
(13 December 2023) caps loop families per portfolio and market area, but was read only through
search excerpts (3 or 8), so it is recorded as unknown. *A loop filled in part?* Allowed in EPEX's GB
auction; not stated for Germany, so all or nothing here. And the exchange checks money, not price
gaps: a block's *surplus* is how far it beat its limit, times its volume.

**Decided 22 October: one loop per buy-then-sell round, the strict rule leading.** A day is cut
where the battery is empty again, and each piece goes out as its own loop, judged alone: a weak
evening round neither rides on a strong morning one nor sinks it. Rounds that share energy merge
into one loop by the same cut; on 2023 no day of LEAR's needs more than 3. The second round is worth
6,265 € of the ceiling (12 %), almost all of it from the midday solar dip between spring and autumn;
held to one round a day, LEAR earns 40,160 € instead of 45,950 € (scratch, before days ended empty).
A loop fills under the **strict rule** when each block beats its own limit, under the **pair rule**
when the two surpluses together are not negative. Strict leads because the pair rule is not
confirmed for Germany, and it fills only a subset of what the pair rule fills. On illustrative
limits (QRA's 75th percentile to buy, 25th to sell) the two differ by about 14,000 € on 2023, more
than the second round is worth, so both are reported. Rejected: one loop per day (both rounds stand
or fall together); one round only (the papers' rule, 11 points given up, and a second planner to
build). **Still open:** the cap on loops per day, read word for word. It does not bind on these
years: LEAR's plan needs at most 3 loops a day on 2024–25 too.

**Decided 26 October: limits at break-even.** The exchange compares a block's limit with the block's
real prices averaged by volume, so each limit is the range's prices averaged the same way: QRA's
75th percentile to buy, 25th to sell (Nitka & Weron 2023's best band, not tuned here). On 2023 that
average lets through 77.0 % of buy blocks, where one hour at p75 lets through 76.7 %. Then both limits
move by the same amount until the round would earn exactly 0 at them. No round that goes through can
lose money, under either rule, and no safe pair of limits lets more through. Rejected: the band as
published, which promises a loss on 208 of 561 rounds (the range is wider than the gap the battery
trades; on 31 January pair filled such a round and lost 67 €); dropping those rounds (49.8 % strict);
picking the best band on 2023. Both papers bid single hours, so neither has a rule for a block.

**The bids' first capture rate: 40,956 € on 2023, 81.0 % of the ceiling under the strict rule;
46,600 €, 92.2 %, under the pair rule** (`just backtest bids`, a few seconds, reading the stored
LEAR and QRA runs). Strict sends 366 of LEAR's 561 rounds, pair 519; none of them lost money. **What
it shows:** limits can only stop trades LEAR's plan chose, never add one, so the most they can gain
over the fixed schedule (91.0 %) is what its 42 losing rounds lost, 608 €. Under the pair rule,
break-even limits stop exactly those, whatever the percentiles, so the range plays no part. Under
the strict rule, many good rounds miss on one side by a few euros: 10 points below sending the plan
without limits, and the range adds about 1 point over none (LEAR's own forecast moved to break-even,
79.8 %). **So on 2023 stage 3's range is worth almost nothing as a limit on LEAR's hours.** Where a
range could still pay is in choosing the hours, which is the stochastic program rejected on 15
October. **Stated limits:** one year; the backtest fills every loop whose limits were beaten, while
the exchange may also reject such a block (not checked for loops); which rule Germany applies is
still unconfirmed, and it moves the answer by 11 points.

**Decided 21 October: every run plans one delivery day at a time.** At 12:00 on D−1 LEAR forecasts day D only; nobody has a forecast for D+1, because the
grid operators' wind, solar and load forecasts for it come out a day later. On 2023, with LEAR's
stored forecasts (a scratch comparison, nothing refitted): planning one day earned 45,950 €; a copy
of day D standing in for D+1, 42,502 €; real prices from the same weekday a week earlier, 40,627 €;
even LEAR's own forecast for D+1, made a day *later* and so not available, 45,047 €. Seeing
tomorrow is worth only 482 € a year on real prices, because a 2-hour battery fills and empties
within the day anyway; an overnight trade must beat 19 % losses and wear, a gap about the size of
LEAR's error, so a forecast of day two loses more bets than it wins. The field plans the same way on
this market (Hirsch & Ziel 2026, one day, empty at its end); longer horizons pay for storage that
takes many hours to fill (Prat et al., *How long is long enough?*). Rejected: a copy of day D (−3,450
€); a separate 36–60-hour forecast (a second model without the inputs that make the first one
work). **Stated limit:** overnight trades are given up, worth at most 482 € (0.9 %) in 2023.

**Decided 22 October: each day ends empty.** Charge held over midnight is a trade split across two
auctions, bought in today's and sold in tomorrow's, and no loop block can hold it. On 2023 it also
earned less: ending every day empty moved the ceiling from 50,542 € to 50,557 €, LEAR up 42 €, the
naive rule up 215 €, because a battery that fills on an evening paid to take power meets the next
paid morning with no room (24 and 25 December). Hirsch & Ziel plan the same way. Rejected: sending
the evening buy alone as a plain order (planning and settling would have to alternate day by day,
for 3 days a year); planning it but never sending it (the next day would start from charge that
is not there). **Stated limit:** an evening below zero before a morning that pays is given up;
2023 cannot say what that is worth in years with more of them.

**The ceiling: 50,557 € on 2023** (`just backtest ceiling`, a few seconds; built 20 October at
51,024 € on a two-day plan, rerun 21 October on one day and 22 October ending each day empty). It is
what the battery would have earned planned on the prices that actually cleared: one delivery day at
a time, starting and ending empty, wear included, about 541 full cycles. No day loses money, since nothing is bought for
tomorrow. Each hour is either charging or discharging, never both, because otherwise the plan would
collect money at very negative prices for burning energy as losses, which 2023's 27 hours below
about −34 € made worth doing. Every run starts each day empty, as the ceiling does, so the ceiling
is the best plan for every single day: a day above it is a bug, and `just backtest fixed` counts them.

**The first capture rate: LEAR's fixed schedule earned 45,992 € on 2023, 91.0 % of the ceiling; the
field's naive rule 40,193 €, 79.5 %** (22 October, each day ending empty; 21 October, with charge
carried over midnight, 90.9 % and 79.1 %; `just backtest fixed`, about 10 seconds, reading
the stored `just train daily` run, nothing refitted). Each day's forecast is put back onto real
hours (the invented spring 02:00 dropped, the averaged autumn 02:00 on both hours), planned like the
ceiling and paid at real prices. So LEAR's lower error is worth about 5,800 € a year here, and the
room between the simplest rule and perfect knowledge is only about 20 points — a forecast can add at
most that. **Days above the ceiling:** none. While charge was carried over midnight the naive rule
beat it on 4 days (113 €), each a day it started with different charge, repaid by the day before;
on 25 December the ceiling, full from the day before, met a morning that paid buyers up to 13 € and
had to sell at a loss first. That is what ending each day empty removed. **The lead is not
chance** (26 October): LEAR earned more than the naive rule on 261 of 365 days, 15.89 € a day on
average, one-sided p 1.4 × 10⁻¹⁷ by Diebold-Mariano on daily earnings, the test behind every
p-value here (printed by `just backtest fixed`); it leads in every month. **Stated limits:** one
year, one fixed schedule.

**Decided 26 October: money ranks the models, and the average of three is a candidate.** Planned on
each stored 2023 forecast and paid at real prices (`just backtest fixed`): LEAR 91.0 %, the tree
90.7 %, the straight line 91.6 %, though the line's error is clearly worst (rMAE 0.615 against 0.504).
None of these gaps is more than chance (p 0.18 and 0.64 against LEAR): one year of daily earnings
can only see gaps above about 1.5 points, and the line's 0.6 would need about 7 years. Why error and
money disagree, tested directly: shifting LEAR's whole forecast by ±20 € moves its earnings by at
most 0.4 points, and given the true daily level (a hindsight diagnostic) it gains nothing, while
the true shape of each day takes every model to 99.5–99.8 %. The battery is paid for which hours are
cheap and dear; the line's extra error is mostly in the level. The field reports the same split
between error and profit (Spread THieF, arXiv 2609.23223; foundation models for arbitrage, arXiv
2609.00089), without testing its profit gaps. **The average of the three, hour by hour, keeps 47,485 €,
93.9 %** (ahead of LEAR on 207 days, behind on 105, p 1.9 × 10⁻⁹): the three miss the shape partly in
different hours (correlation 0.71–0.78). Equal weights, the field's default, tried once on 2023, so
the held-back years are its test. **Decided for that reading, before it:** LEAR, the average, the tree
and the straight line, each as a fixed schedule; the bids on LEAR, strict and pair; the ceiling.
Rejected: new algorithms in stage 4 (a neural net, CatBoost, Random Forest), because a new member's
gain to the average would likely sit below what the data can detect, at the cost of a new dependency,
tuning and daily walks.

Two warnings from the literature are carried in: the most accurate ranges did not earn the most
(Nitka & Weron 2023), and simple quantile bidding rules can be gamed and ignore that a battery's
hours depend on each other (Hirsch & Ziel 2026).

**Why that way round.** A standalone price forecast is close to a commodity — several vendors
sell them and the accuracy differences between them are thin. The margin sits in the two things
on either side of the forecast: the optimisation that turns it into a schedule under real asset
constraints, and the reliability that makes it dependable at 11:45 every morning. That is why
the firms doing this commercially ask for machine learning and optimisation in the same job
description, and it is why a project that stopped at a good rMAE would have measured the least
valuable part.

### Where stage 1 landed

A gradient-boosted tree forecasts the 17,542 held-back hours of 2024–25 with a mean absolute
error of **17.44 €/MWh** against the naive rule's 32.81 — an rMAE of **0.532**, divided by last
week's price as every number was before 15 October. Reproduce it
with `just final-score`; the run is stamped into `reports/scores.csv` with the commit that
produced it.

The more useful result was not the headline. Scored on the validation year the tree beat the
straight-line model, 0.488 to 0.532. On the held-back years, **with the identical recipe, the
ranking reversed** — 0.627 against 0.575. The tree had been chosen partly because it suited
2023, and only years nobody had looked at revealed it. That is the whole apparatus doing its
job, and it is why stage 2 carries a significance test rather than a leaderboard.

### Where stage 2 landed

LEAR, refitted every day on its last 1,092 days, forecasts the 17,544 held-back hours of 2024–25
with a mean absolute error of **13.28 €/MWh**. The field's benchmark misses by 27.38, giving an rMAE
of **0.485**; last week's price misses by 32.81, giving 0.405. Reproduce both with `just
final-score`, and the p-values with `just significance`.

| rMAE, field's benchmark *(last week's)* | 2023, validation | 2024–25, held back |
|---|---|---|
| Straight line, refitted daily | 0.615 *(0.523)* | 0.648 *(0.541)* |
| Tree, refitted daily | **0.503** *(0.428)* | 0.548 *(0.457)* |
| LEAR, refitted daily | 0.504 *(0.429)* | **0.485** *(0.405)* |
| Tree, fitted once on 2018–2023 | | 0.636 *(0.530)* |
| Straight line, fitted once on 2018–2023 | | 0.675 *(0.563)* |

**The ranking held this time.** Stage 1's validation winner lost on the held-back years; stage 2's
did not, and every held-back gap is significant (LEAR better than the tree, p < 0.0001; the tree
better than the line, p < 0.0001). **The 2023 tie broke in LEAR's favour:** closer in every hour of
the day, most at night and in the evening peak, with the tree still better on the 1,033
negative-price hours (17.3 against 19.5 €/MWh). LEAR's lead grows from 2024 (0.433 against 0.458)
to 2025 (0.377 against 0.457). Why is not known; one guess, not checked, is that by 2025 LEAR's
1,092 days have left most of the crisis behind while the tree still learns from every year.

**Daily refitting is the lever on untouched years too:** the tree goes from 0.530 fitted once to
0.457 refitted daily, the line from 0.563 to 0.541 (both p < 0.0001).

Checked before believed: LEAR is closer than the tree on 55 % of hours, not on nearly all of them.
**It is a LEAR-level result, not a top one.** Against the field's benchmark Lago et al. (2021) report
LEAR at 0.431 and their best ensemble at 0.374 on German prices of 2016–17, other years and so only
roughly comparable; against last week's, 0.405 sits inside arXiv 2311.02610's 0.40–0.43 for LEAR,
whose best models reach 0.34–0.36. Not done: rebuilding held-back days from data cut at gate closure,
as was done for four days of 2023. **All of this is error, not money.** Whether LEAR's lead turns
into revenue is what stage 4 measures.

**Every figure in the steps below is from before 15 October, so divided by last week's price.**

### What stage 2 did, in the order the evidence supported

Before any of it, **every delivery day becomes 24 hours long.** A clock-change day has 23 or 25,
and one model per delivery hour needs the same 24 every day. The rule is the field's own (Lago et
al. 2021, §3.1): Berlin clock time, the missing spring hour filled from its neighbours, the doubled
autumn hour averaged. Built 6 October. The battery is still settled on the hours that really
happened.

**Then the significance test (Diebold-Mariano), before the first comparison.** Moving onto the
grid shifted the tree's validation score from 0.488 to 0.483 without improving any forecast: 4 %
of its training rows changed and it landed differently, in every hour. Refitting monthly against
daily may differ by less than that, so rMAE alone cannot read the first comparison stage 2 makes.
Built 7 October: the field's daily version (epftoolbox), plus a correction for good and bad days
running in streaks, which in 2023 turns a plain p of 0.02 into 0.058. Every hour's forecast is kept
in MLflow, and `just significance` (built 14 October) regenerates every p-value on this page from
those runs. It needs the `just train` runs first, and names any that are missing.

1. **Refit as the year runs.** Measured on validation, refitting monthly instead of once moved
   the tree from 0.488 to 0.440 — a larger gain than any model choice produced. An expanding
   window beat a rolling two-year one, so the lever is *refit more often*, not *forget the
   crisis*. **Re-run on the grid, walking forward** (`just train once|monthly|daily`, built
   7 Oct; all 8,760 hours of 2023 since the autumn midnight fill on 12 Oct): the tree goes
   0.483 → 0.440 → 0.429, the line 0.532 → 0.525 → 0.523. Every step is significant, but the
   tree's monthly → daily (p = 0.028) is fragile. One hour earlier it read 0.437 → 0.430 and
   p = 0.11: a single extra training row moved every November and December forecast of the
   monthly tree. That verdict rests on the tree's wobble, not on a settled difference. With
   holidays in the frame (14 Oct) it reads 0.443 → 0.428 and p = 0.0015: monthly got worse again,
   daily did not get better.
2. **LEAR**, the field's statistical benchmark. **Built and measured 13 October** (`just train
   daily`): 24 Lasso models on a day table (one row per delivery day, whole earlier days as inputs),
   one 1,092-day window refitted every day, as epftoolbox does. **0.429, a tie with the daily
   tree** (MAE 14.44 against 14.45; Diebold-Mariano p = 0.50 either way; with holidays from 14
   October, 0.429 against 0.428, p = 0.53 / 0.47) and clearly ahead of the line (p < 0.001). The tie hides a split: LEAR is better at night (00:00: 8.2 against 11.6 €/MWh)
   and worse through the solar hours (14:00: 19.5 against 17.1). Checked for hindsight before
   being believed: four days rebuilt from data cut off at gate closure give identical forecasts.
   It matches the field's reference code: epftoolbox's own LEAR, given the same windows, gives the
   same forecasts to 1e-10 €/MWh on ten days of 2023 (a one-off check, recorded in the work log on
   13 October). About a third of the 8,760 daily refits stop at epftoolbox's 2,500-step limit
   before settling. scikit-learn warns each time, and the warning is silenced, as epftoolbox
   silences it: letting eight days run 40 times longer moved their forecasts by 0.09 €/MWh on
   average, so the warning flags no real loss of accuracy here. Lago et al.'s average over four
   windows is their benchmark for methods that average, so it is a later variant.
   **Every year instead of 1,092 days, measured 14 October** (`just train daily all`): **0.472,
   worse** (Diebold-Mariano p < 0.001), in every hour and in ten of twelve months, most through the
   solar hours. The tree did better learning from every year; LEAR does not, as one published
   German study also found (arXiv 2311.02610). LEAR keeps its 1,092 days.
3. **One model per delivery hour — dropped 14 October.** LEAR already is one, a line per hour.
   The tree already splits on the hour, so a tree per hour would be tuning, which 13 October ruled
   out. **A stated limit instead:** LEAR's gain over the line is measured, but LEAR differs from it
   in three ways at once (24 models, Lasso on a robust ruler, the day table's inputs), and which of
   them earns the gain is not known.
4. **German public holidays — built and measured 14 October.** The nine nationwide ones, as a
   yes/no column for every model, from the `holidays` package; regional ones left out. Each is
   fixed by law years ahead, so known at gate closure. **No model moved significantly**, in any
   schedule, either way (2023, daily: line 0.523 → 0.523, tree 0.429 → 0.428, LEAR 0.429 → 0.429;
   closest call the monthly tree, 0.440 → 0.443, p = 0.097 for *worse*). Kept by a rule fixed before
   the result: the effect is real and known in advance, so the flag stays unless it hurts. **Why
   so little:** the published load forecast already drops to Sunday's level on holidays, and the
   models had learned that; the flag got almost no weight. LEAR and the line still miss most on
   holidays (21.5 and 29.6 €/MWh against about 14 and 17 on other days), so whatever they get
   wrong there, it is not *knowing* it is a holiday. Every 2023 number above from this date on
   includes the flag; the earlier rows stay in `reports/scores.csv` as a different feature set.

Every step is judged with the significance test, because stage 1 demonstrated that a gap of
0.044 on one year is not evidence of anything.

### Where stage 3 landed

**Closed on 19 October 2026.** LEAR's one forecast per hour becomes 99 percentiles, two ways. *QRA*
fits a line through recent dots — LEAR's forecast against the real price — for each percentile, so
the band can widen when LEAR expects a high price and narrow when it expects a low one. *Conformal*
takes how big LEAR's past misses were and puts a band of that width around today's forecast. Both
learn only from forecasts LEAR really made: LEAR is walked forward first, and its scores come back
exactly as stage 2 reported them (0.504 on 2023, MAE 13.283 on the held-back years).

**The range chosen on 2023 is the field's: the average of four.** Each method is run with windows of
28, 56, 91 and 182 days and the four ranges are averaged percentile by percentile (Lipiecki,
Uniejewski & Weron 2024). Each window is wrong at different moments — a short one forgets a calm
spell too fast, a long one remembers a crisis too long — and averaging lets those errors partly
cancel.

| Pinball *(lower is better)* | 2023, validation | 2024–25, held back |
|---|---|---|
| **QRA, average of four** | **5.195** | **4.655** |
| conformal, average of four | 5.398 | 4.983 |
| QRA, best single window (91 days) | 5.300 | *not read* |
| 80 % band holds (QRA / conformal) | 0.821 / 0.823 | 0.789 / 0.805 |

Pinball loss is the average distance from the price to each line, charged lopsidedly: for p90, a
price above the line costs nine times what one below costs. It grows with the price level, so the
two columns are not comparable with each other; each row is compared within its column.

**The ranking held on the years held back.** QRA beats conformal on 2024–25 (p < 0.0001), as on 2023
(p = 0.0019). On 2023, the average beat the best single window (p = 0.0001), and single windows told
their own story: with 182 days QRA won clearly, at 91 days the two could not be told apart, so most of
QRA's single-window lead was coping with a stale window. Most of the held-back lead sits in
January–March 2024, when prices fell from about 100 €/MWh to 60–75: QRA's 80 % band narrowed to
28–36 € and still held 85 %, while conformal kept the 45 € it had learned on dearer days.
Reproduce with `just quantiles 28 56 91 182`, `just final-score ranges` (read once, about 4.5
hours) and `just significance`; the rows are in `reports/quantile_scores.csv`.

**Stated limits.** The window average was chosen on 2023 among five candidates, which flatters its
2023 score slightly; the held-back years were read once, after the choice. QRA's bands run a little
narrow on the held-back years (80 % held 79 %, 90 % held 88 %); conformal's sit on target. Both still
lag the market: QRA's 80 % band held 71–76 % in April–June 2024, and both fell to about 70–75 % in
November–December 2024, the dearest months. Each hour's 99 lines are fitted separately and often
cross; they are sorted back into order. Where LEAR's forecast lies beyond every forecast in the
window, both methods score two to three times worse, conformal as badly as QRA, so those are hard
hours rather than QRA guessing past its data. **All of this is error, not money.** Whether the range
earns anything is stage 4's question.

**What it costs to run.** The held-back reading replays 913 days and takes about 4.5 hours on a
laptop. A live forecast does one day: about 20–25 seconds for LEAR and the four windows, against
about 8 for a single window (worked out from measured parts, not timed as one run).

### Where stage 4 landed

**Closed on 27 October 2026, with the held-back years read once** (`just final-score battery`, under a
minute, reading the forecasts and range stages 2 and 3 stored; rows in `reports/capture_scores.csv`).
Nothing was refitted, and what would be scored was fixed on 26 October, before looking.

| Share of the ceiling | 2023, validation | 2024–25, held back |
|---|---|---|
| Ceiling: perfect foresight, wear included | 50,557 € | 134,077 € |
| **Bids on LEAR, strict rule** | 81.0 % | **90.1 %** |
| Bids on LEAR, pair rule | 92.2 % | 94.0 % |
| LEAR, fixed schedule | 91.0 % | 93.0 % |
| Average of the three, fixed schedule | 93.9 % | 94.4 % |
| Straight line, fixed schedule | 91.6 % | 92.8 % |
| Tree, fixed schedule | 90.7 % | 92.2 % |
| Naive rule, fixed schedule | 79.5 % | 84.9 % |

**The headline is the strict rule's 90.1 %**: LEAR's plan sent as one loop per round, limits from
QRA's range moved to break-even, a loop filled only if each of its two orders beat its own limit.
Strict leads because it can only understate what the battery would have made; the pair rule, stated
by EPEX only for another auction, sits beside it. Under either rule no round that went through lost
money (803 and 998 of 1,103 rounds).

**What held.** LEAR beat the naive rule on 501 days and trailed on 211, 14.78 € a day (p 1.3 × 10⁻²⁶).
**The average of the three beat LEAR on 372 days and trailed on 224**, 2.67 € a day (p 0.00013): found
on 2023 and confirmed on years nobody had looked at, though smaller than 2023's 4.09 € a day. Limits
did what 2023 showed: under the pair rule they remove the losing rounds and add 1 point; under the
strict rule they cost 2.9 points against sending the plan without them (10 on 2023).

**What one more look could not settle.** Neither the tree nor the line earned more than LEAR (p 0.94
and 0.63). The line, ahead of LEAR on 2023, is behind on 2024–25, and neither gap was ever more than
chance. Stated before the reading: these years can rank the average against LEAR, not the three
single models against each other.

**Every share is higher than on 2023**, and the room between the naive rule and perfect foresight
shrank from 21 points to 15. The ceiling earned 183 € a day against 139 € in 2023. Why is not tested;
one guess is that bigger, more regular swings within the day, with more solar, make the day's shape
easier to find.

**One alarm, explained.** The line and the average each beat the ceiling on one day, by 1.3 and 0.7
cents. The solver stops once it is within 0.01 % of the best plan (its default), and re-solved
exactly the ceiling is at or above both runs. Not a leak; nothing was changed.

**Stated limits.** Which fill rule Germany applies is unconfirmed, and it moves the answer by 3.9
points. The backtest fills every loop whose limits were beaten, while the exchange may also reject
such a block. The bids ride on LEAR, not on the average, because the range was built around LEAR.
Overnight trades are given up by design. One small battery, assumed too small to move the price.
Gross trading margin only, as stated under *Honest framing*.

**Checked 30 October: our euros against published German battery revenues.** Each source's method
was read before its number. Ours: the day-ahead auction alone, hourly, 81 % round trip, wear charged,
before fees; the ceiling about 67,000 € a year for 1 MW / 2 MWh. **The figures most often quoted
cover every market, and the gap is the finding.** For 2024 a 1 MW / 2 MWh battery is put at 180,000 €
across day-ahead, intraday and both reserve markets (Aurora, February 2025), and at about 144,000 €
per MW across intraday and reserve (Enervis index): two to three times our perfect-foresight ceiling,
most of it from reserve. So 90.1 % is a share of the day-ahead slice, not of what a German battery
earned. **A day-ahead share of such a battery is not comparable either:** a battery that also sells
reserve holds part of itself back, so its day-ahead slice understates what day-ahead alone pays.
**Day-ahead alone, one figure:** 89 k€ per MW for 2025 (PortfolioEnergy, method mostly unstated).
It sits above our ceiling, and every known difference points that way (higher efficiency,
quarter-hours from October 2025, perhaps no wear charge), so it is a direction, not a check. **No
published figure plans on a forecast**, so the capture rate has no outside counterpart. **The one
candidate for a like-for-like check** is the ISEA index (RWTH Aachen), which also scores the
day-ahead auction alone with hindsight, on the same zone, data and battery size; its headline
"Cross-Market" covers FCR, aFRR and continuous intraday only. Its 90.25 % round trip, missing wear
charge and cycle cap pull in different directions, so only our ceiling re-run on its settings over
the overlapping months (from late 2024) would make it a check: noted, not built. Nothing already read
was changed.

**What stage 5 starts from.** A chain that runs end to end on stored forecasts, every number on this
page regenerated by a command. Its first decision is what a scheduled run would send each morning:
LEAR's plan with strict bids (the headline, one daily refit, a range built for it), or the average
(more money on both readings, but three daily refits and no range of its own yet). And the first
thing to watch for drift is already known: QRA's bands ran narrow in the dearest months of 2024.

**Decided 27 October: three additions, in this order.** First, **our euros against published revenue
figures for German batteries.** Stage 4's numbers have not yet been compared with anything outside this
project, and everything after builds on them. Second, **a one-page summary at the top of this README**,
for a reader who wants the result before the detail. Third, in stage 5, **a small web page**
(Streamlit). Past results come first: pick a day and see the forecast, its range, the real price, the
battery's plan and what it earned. Tomorrow's forecast follows once the daily run exists. The page
reads a small data file kept in git, because the stored runs are not, and a clean clone must show the
same thing. Rejected: the summary first (it would need rewriting if the check finds something); a page
with tomorrow's forecast only (nothing to show until the daily run is built).

### Parked on purpose

Recorded so the reasoning survives, and so nobody re-opens them without new evidence.

| Parked | Until | Why |
|---|---|---|
| **CatBoost, Random Forest** | **closed 26 Oct 2026** | Parked because capture rate may not rank models the way rMAE does. Stage 4 settled it: it does not (on 2023 the straight line, worst by error, earned as much as LEAR and the tree), but one year cannot tell models apart within about 1.5 points, so two more would land in the same unresolved band. They would matter only as members of the average, and as trees they would likely miss in the same hours as ours. A neural net, the field's partner for LEAR (Lago et al. 2021), is the candidate if the average is ever extended: after stage 5, not before |
| **Experiment tracking (MLflow)** | **unparked 5 Oct 2026**, built 7 Oct 2026 | Parked because no run could be lost: each regenerates in seconds. Reopened by a different question, whether runs can be compared side by side. Stage 2 compares several refitting variants, and the significance test needs every hour's forecast, which the score file does not keep. `reports/scores.csv` stays the record, because it is in git; MLflow is where runs are compared. `just train` now also logs one run per forecast to a local `mlflow.db`, each stating its time convention and keeping the hourly forecasts its score came from (`src/tracking.py`). They live in `reports/mlflow/`, which git ignores: MLflow records this machine's full path inside. View them with `.venv/bin/mlflow ui --backend-store-uri sqlite:///reports/mlflow/mlflow.db --port 5001` and <http://localhost:5001>; on macOS the default port 5000 belongs to AirPlay, which answers 403 |
| **A second data source for the 37 missing load-forecast days** | closed, not parked | Dropping *all* of 2018 moved the score by nothing, so 888 hours of it cannot matter |

### The plan as a page

The same plan, shareable and refreshed whenever a stage closes:
<https://claude.ai/artifact/Mysse8XGB4exGFykeDcmYm>. This README is canonical; the page is the form
that travels. The version that stood until 2 October is archived unchanged as a dated snapshot and is
not maintained — [docs/worklog.md](docs/worklog.md) records both links and which is which.

### Roughly when

Re-estimated on 7 October from what the stages actually took — seven working days for stage 0,
six for stage 1 — at about three and a half working days a week.

**Stage 3 closed on 19 October**, the week the estimate gave, with the window chosen and the
held-back years read once. Stage 4 started 20 October by settling its one open decision (an
unfilled order is handled as a loop block, buy and sell together or not at all) and building the
perfect-foresight ceiling. On 21 October each run was set to plan one day at a time and the
first capture rate came in. On 22 October the exchange's rules were read from EPEX's own documents,
each day was set to end empty (LEAR 91.0 %, the naive rule 79.5 %), and the bids' shape was decided:
one loop per round, the strict fill rule leading. On 26 October the limits were set from the range at
break-even and the bids' first capture rate came in: 81.0 % strict, 92.2 % pair, against 91.0 % for
the fixed schedule. LEAR's lead over the naive rule in euros was then tested day by day and is not
chance (p 1.4 × 10⁻¹⁷). The same day the three stored models were planned side by side: money does
not rank them as error does, and their average keeps 93.9 %. What remains is the years held back,
read once, with what gets scored fixed beforehand.
**Stage 4 closed on 27 October**, the week before the estimate, with that reading: 90.1 % strict as
the headline, and the average's lead held. Before stage 5, about a day: the revenue check and the
one-page summary (decided 27 October). The revenue check was done on 30 October, recorded as a
direction: published figures cover more markets or state too little to reconcile. The summary at the
top followed the same day; the rest of this README is to be rewritten in its plain style. Stage 5
grows by its web page, to about a week and a half.
**Stage 2 closed on 14 October**, about a week ahead of that estimate, after running longer than
first planned: the 24-hour grid, MLflow and the significance test went in front of recalibration.
The later stages keep their estimates and move forward with it. Stage 4 is the least certain,
because the optimiser does not exist yet, and since 15 October it also bids with limit prices
rather than only committing one schedule.

| Stage | Estimate | Ends around |
|---|---|---|
| 2 | done | 14 October 2026 |
| 3 | done | 19 October 2026 |
| 4 | done | 27 October 2026 |
| 4½ | revenue check, summary done 30 Oct; README rewrite ~½ day | week of 2 November 2026 |
| 5 | ~1½ weeks | week of 9 November 2026 |

### Decided 30 October: what the daily run sends

**The average of the three forecasts, as a fixed plan without limits; LEAR's plan if any of the three
fails.** Read from numbers already measured, nothing new computed: on 2024–25 the average kept 94.4 %
of the ceiling, LEAR's plan sent without limits 93.0 %, LEAR's strict bids 90.1 % (94.0 % pair). The
average's lead over LEAR was found on 2023 and confirmed on 2024–25 (p 0.00013). Under the strict rule,
limits cost more than they save on both readings: on 2024–25 they avoided 1,376 € of losses and gave
up 5,197 € of good rounds. The average has no range of its own, so it can only go without limits.
LEAR's QRA range is still computed each day, for the drift checks, not to set bids. Rejected: LEAR
with strict bids (the headline, but about 4 points below the average); LEAR without limits (one model
instead of three, 1.4 points below). **What it changes:** the daily run sends something other than the
headline configuration; the headline stays as read on 27 October, because it is what was fixed before
the reading. **Stated limits:** unlimited orders accept any price, so some rounds lose money (already
inside the 94.4 %); three models are three things that can fail before noon, hence the fallback.
