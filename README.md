# Battery Storage Backtest

Forecasting German day-ahead electricity prices, and measuring what the forecast is
actually worth to a battery.

**Status:** stage 3 of 6 complete, 19 October 2026; stage 4 next. LEAR, the field's statistical
benchmark, refitted every day, forecasts the held-back years at **rMAE 0.485** against the field's
benchmark, 0.405 against a week-old lookup. Around it, a range of 99 percentiles (QRA, averaged over
four windows) scores **pinball 4.655** on the same years, ahead of the simpler band (4.983,
p < 0.0001). **The yardstick changed at the close of stage 2** — see the note under the stage table.
Stage 4, where the forecast becomes a capture rate, is the one the rest exists for.

---

## The question

A battery earns money by charging when electricity is cheap and discharging when it is
expensive. To do that it has to commit a schedule *before noon on the previous day*,
when tomorrow's prices are still unknown.

So there are two problems: forecast the prices, then decide what to do about them.

This project builds both, and answers one question that gets asked less often than it
should:

> **How much of the achievable revenue does a forecast actually capture — and at what
> point does a better forecast stop being worth anything?**

## Approach

```
ENTSO-E data → features → price forecast → dispatch optimiser → settlement → capture rate
  (published before gate closure)      (decision)          (actual prices)
```

Results are reported three ways, so the numbers mean something:

| Run | Forecast used | Tells you |
|-----|--------------|-----------|
| Ceiling | actual prices | what perfect foresight would have earned |
| Model | model output | what this project earned |
| Floor | naive rule | what no modelling effort earns |

**Capture rate = model revenue ÷ ceiling.**

## Where this is going

Six stages. Each one ends on a number, and no stage starts before the previous number exists —
so a claim can always be traced back to the run that produced it.

| Stage | Delivers | Headline number | Status |
|---|---|---|---|
| 0 | Reproducible data pull, split locked | negative hours, daily spread | **done** 17 Sep 2026 |
| 1 | First model against a naive benchmark | rMAE 0.532 *(last week)* | **done** 30 Sep 2026 |
| 2 | Recalibration, LEAR, holidays | **rMAE 0.485** *(0.405 last week)* | **done** 14 Oct 2026 |
| 3 | Quantile forecasts: QRA on LEAR, conformal beside it | **pinball 4.655** *(QRA, four windows averaged)* | **done** 19 Oct 2026 |
| 4 | Price-dependent bids and a MILP schedule, revenue | **capture rate** | |
| 5 | Drift monitoring, scheduled run | reproducibility | |

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
build). **Still open:** the cap on loops per day, read word for word.

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
had to sell at a loss first. That is what ending each day empty removed. **Stated limits:**
one year, one fixed schedule, no significance test on the gap yet; the limit-price bids are next.

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

### Parked on purpose

Recorded so the reasoning survives, and so nobody re-opens them without new evidence.

| Parked | Until | Why |
|---|---|---|
| **CatBoost, Random Forest** | stage 4 | Both are reported to trade well despite worse error scores — Random Forest for steadier margins, CatBoost in a week-ahead battery-arbitrage comparison. **Capture rate may not rank models the way rMAE does**, and ranking more algorithms on the wrong metric is wasted effort. Stage 4 settles whether the two agree |
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
the fixed schedule. A test of whether LEAR's lead over the naive rule is more than chance remains.
**Stage 2 closed on 14 October**, about a week ahead of that estimate, after running longer than
first planned: the 24-hour grid, MLflow and the significance test went in front of recalibration.
The later stages keep their estimates and move forward with it. Stage 4 is the least certain,
because the optimiser does not exist yet, and since 15 October it also bids with limit prices
rather than only committing one schedule.

| Stage | Estimate | Ends around |
|---|---|---|
| 2 | done | 14 October 2026 |
| 3 | done | 19 October 2026 |
| 4 | ~2 weeks | week of 2 November 2026 |
| 5 | ~1 week | week of 9 November 2026 |

## Setup

| | |
|---|---|
| Market | Day-ahead auction, DE-LU bidding zone |
| Target | Hourly clearing price, €/MWh |
| Decision point | 12:00 on day D−1, before gate closure |
| Horizon | 12–36 hours |
| Train / validate / test | Oct 2018 – 2022 / 2023 / 2024–2025 |
| Battery | 1 MW, 2 MWh, 90 % efficiency per direction |

The history starts in October 2018 because the DE-LU bidding zone did not exist before
that date — Germany, Austria and Luxembourg shared a single zone and a single price.

## What the market actually did

Seven years of DE-LU day-ahead prices, 63,577 hours. Regenerate every figure below with
`just explore`.

![DE-LU day-ahead price, Oct 2018 to Dec 2025](reports/figures/README_price_history.png)

The average went up and came back. The variation went up and stayed — the shaded band never
returns to its 2019 width. **A battery is paid for the band, not the line.**

Two numbers put a figure on the band.

![Negative-price hours and average daily spread, per year](reports/figures/README_negative_hours_and_spread.png)

| Year | Hours below zero | Share | Deepest | Mean daily spread | Days not worth cycling² |
|---|---|---|---|---|---|
| 2018¹ | 27 | 1.2 % | −19 | 40.6 | 2 |
| 2019 | 211 | 2.4 % | −90 | 30.1 | **26** |
| 2020 | 298 | 3.4 % | −84 | 32.5 | 12 |
| 2021 | 139 | 1.6 % | −69 | 80.3 | 2 |
| 2022 | 69 | 0.8 % | −19 | **187.0** | 1 |
| 2023 | 301 | 3.4 % | **−500** | 97.9 | **0** |
| 2024 | 457 | 5.2 % | −135 | 111.2 | **0** |
| 2025 | **576** | **6.6 %** | −250 | 124.1 | 1 |

¹ October to December only.
² Days where the best hour did not beat the cheapest hour by enough to cover round-trip
losses and wear — so the right answer was to stay idle, even knowing the prices in advance.

**Negative hours have risen more than twentyfold** — from 27 in the zone's first quarter to
576 in 2025, when one hour in fifteen cleared below zero. One hour in 2023 reached the
−500 €/MWh floor, the lowest the auction permits.

**The daily spread has roughly quadrupled**, from about 30 €/MWh to about 124. Since a
battery is paid for the spread and nothing else, that is the headline: the opportunity this
project measures is several times larger than it was in 2019.

**The two columns are not the same story twice.** 2025 has more negative hours than 2022
(576 against 69) but a smaller spread (124 against 187). So what produced the spread changed:
in 2022 the expensive hours were extremely expensive; in 2025 the cheap hours are extremely
cheap. **The second kind is worth more**, and the reason is the round-trip loss changing sign.

To deliver 1 MWh, a battery must buy 1 ÷ 0.81 = 1.235 MWh — so the charging price is always
multiplied by 1.235. Against a positive price that works against you; against a negative price
it works for you. Three days with an identical headline spread of 100 €/MWh:

| Charge at | Discharge at | Earned per MWh delivered |
|---|---|---|
| 100 | 200 | 68.5 |
| 0 | 100 | 92.0 |
| −50 | 50 | **103.7** |

Same spread, and half as much again from the third day as the first. A negative hour is worth
more than its face value; an expensive hour has to overcome the loss rather than profit by it.

2021–22 interrupts both columns, and that interruption sits in the middle of the training
period. What caused it is not visible in this data — these files hold prices, load and
weather forecasts, and no fuel or carbon prices at all. The interruption is treated here as
something the model has to survive, not something this repository can explain.

**The last column narrows the question this project has to answer.** In 2019 there were 26
days when a battery with perfect foresight should have stayed idle. Across 2023–2025 there
was one. So *whether* to trade is no longer a real decision — it is always yes. What is left
is **which hours, and how many cycles**, and that is a harder question than the one it
replaced.

### Why the price is what it is

The strongest single driver is **residual load** — demand minus wind and solar, built only
from forecasts published before gate closure. It is what has to be covered by something other
than the weather.

Fitting a straight line through each year separately gives two numbers. The slope says how
many €/MWh one GW of residual load is worth. The correlation says how tightly the two move
together.

| Year | Slope (€/MWh per GW) | Correlation | Hours |
|---|---|---|---|
| 2018¹ | 1.28 | 0.910 | 1,367 |
| 2019 | **1.12** | 0.848 | 8,760 |
| 2020 | 1.16 | 0.828 | 8,784 |
| 2021 | 3.53 | **0.583** | 8,760 |
| 2022 | **7.10** | 0.623 | 8,712 |
| 2023 | 3.09 | 0.883 | 8,759 |
| 2024 | 2.99 | 0.775 | 8,783 |
| 2025 | 3.12 | 0.871 | 8,759 |
| **Pooled** | — | **0.440** | 62,684 |

¹ October to December only.

**The pooled correlation is the weakest number in the table, and that is the finding.** Each
year on its own holds together far better than all of them together. So this is several
relationships stacked, not one relationship scattered — and a model fitted across the whole
record is averaging markets that behaved differently.

![Residual load against price, one fitted line per year](reports/figures/README_residual_load_vs_price.png)

**The slope roughly tripled and stayed tripled** — about 1.1 before 2021, about 3.1 since 2023.
The eight lines sort into three groups, not eight variations on one market: flat and tight
(2018–20), steep and badly fitting (2021–22), steep and tight again (2023–25).

**What that costs is a transfer problem, not an input problem.** It is not that a wrong
weather forecast now costs more — bids were placed against the *published* forecast, so a
forecast that turns out wrong is settled in the balancing markets, not in this auction. The
cost lands on a model that learned the wrong relationship:

| Fitted on | Asked about an ordinary 40 GW day | |
|---|---|---|
| 2019–20 | says **39 €/MWh** | |
| 2024–25 | answer is **114 €/MWh** | **74 €/MWh of error, before any noise** |

**2021 and 2022 are the two years that fit badly** (0.58 and 0.62), and 2022 is also the
steepest by a distance. In those years something other than residual load was doing much of
the work, and **this dataset cannot say what** — it holds no fuel or carbon prices. Whether to
add them is an open scope question, held until the model shows whether it needs them.

Both awkward years sit inside the training period. The test years fit well and share a slope.
That is the shape of the problem stage 2 has to deal with, and the first model is deliberately
built with no correction for it — so that whatever stage 2 builds has something to beat.

### What negative prices are not

Negative prices are usually explained as wind and solar making more than the country needed.
Mostly they are not:

| Of 2,053 hours that cleared below zero | |
|---|---|
| Wind and solar alone exceeded demand | 424 (**21 %**) |
| Median residual load during those hours | **+5.1 GW** |

Four fifths of the time the system still needed several GW from something else, and the price
went below zero anyway. Something kept generating that would have lost more by stopping
(*must-run generation*).

Naming the cause is beyond this dataset. Counting the hours is not, and the count is enough to
rule out the simple explanation.

## Ground rules

- **Every feature must have been knowable at the decision point.** Published TSO forecasts
  qualify; actual generation does not, however freely available it is today.
- **The test period is evaluated once**, at the end of a stage. Repeated evaluation with
  adjustment in between makes the final number optimistic.
- **Every model faces a benchmark** — the naive rule first, then LEAR from the
  [epftoolbox](https://github.com/jeslago/epftoolbox), with Diebold-Mariano to test whether
  a difference is real.

## Data

| Source | Used for |
|--------|----------|
| [ENTSO-E Transparency Platform](https://transparency.entsoe.eu) | Prices, load forecast, wind and solar generation forecast, actual generation |
| [SMARD.de](https://www.smard.de) | Cross-check, and a fallback while API access is pending |

ENTSO-E API access requires a free account plus a token request. No raw data is committed
to this repository — the pull is reproducible from `src/data.py`.

[docs/data-quality.md](docs/data-quality.md) records what the history actually contains:
coverage per series, the gaps and what was decided about them, and seven hours the client
library silently dropped before anyone counted.

## Running it

**Prerequisite: Python 3.11.** Nothing else. The exact version is pinned in
`.python-version`; anything 3.11.x will do.

### Get it running — three commands, no extra tooling

```bash
git clone <this repo> && cd battery-storage-backtest

python3 -m venv .venv                              # a project-local environment
.venv/bin/pip install -r requirements.txt          # once, not per terminal session
.venv/bin/python -m pytest tests/ -q               # 210 tests, offline, no token
```

That's the whole setup. `pip install` writes into `.venv/` on disk, so it persists — you
never repeat it unless `requirements.txt` changes, and you never need to "activate"
anything, because every command below names the interpreter explicitly.

Expect `210 passed`, in a little over a minute.

### See it work, without a token

```bash
.venv/bin/python -m scripts.explore     # headline numbers and the three figures
```

Needs the cached data — see the next section. Everything above this line runs on a fresh
clone with no account anywhere.

### With an ENTSO-E account

The platform is free; registration takes a day or two because the API token is granted by
hand. Then:

```bash
cp .env.example .env                                 # paste your token into it
.venv/bin/python -m scripts.verify_forecast_series   # ~20 s — are the forecasts forecasts?
.venv/bin/python -m scripts.pull                     # ~20 min, ~34 MB
.venv/bin/python -m scripts.explore                  # now has data to describe
```

### Shorter commands, optional

Those `.venv/bin/python -m ...` invocations are what the [`justfile`](justfile) wraps. If you
install [`just`](https://just.systems), each becomes one word:

```bash
brew install just                  # macOS
pip install rust-just              # any platform, ships the same binary
# or: curl -sSf https://just.systems/install.sh | bash -s -- --to ~/.local/bin

just                               # the menu
just setup · test · pull · verify · explore · train · quantiles · significance · final-score · clean
```

**Nothing requires it.** The justfile is the single source of truth for what each command is,
so it doubles as documentation — read it and you have the raw commands, which is why they are
not duplicated here to drift out of step. `just` also searches parent directories, so its
recipes work from anywhere in the project, and the same commands appear in VS Code under
*Tasks: Run Task*.

### Why the pull is safe to re-run

It fetches the whole history every time and **never overwrites what is already cached.** Run
it twice and every series reports `unchanged` — that is the reproducibility check made
observable, and it is why a revision on ENTSO-E's side cannot rewrite the data a published
result rested on. Displaced copies are kept under `data/raw/archive/`, and every pull appends
a line to `data/raw/manifest.csv`.

Dependencies are pinned exactly in `requirements.txt`, hand-curated rather than frozen, so a
clean clone resolves to the same versions that produced every number above.

## Structure

[docs/architecture.md](docs/architecture.md) is the map — what each file is for, how they
connect, and where to start reading. In short:

```
BUILT
  src/config.py              split dates, EIC codes, battery parameters — single source of truth
  src/sources/entsoe.py      the data-item catalog: what is fetched, and what may reach a model
  src/data.py                caching and normalisation; the loaders everything else calls
  src/features.py            the gate — where the availability rule is enforced, not declared
  src/models.py              the benchmarks, the line, the tree, LEAR, and QRA and conformal ranges
  src/evaluate.py            rMAE, pinball and coverage, Diebold-Mariano, all on shared hours
  src/backtest.py            the battery's plan (a MILP), the day-by-day walk, settlement at real prices
  scripts/pull.py            just pull        — fetch every series in the catalog
  scripts/explore.py         just explore     — headline numbers and the README figures
  scripts/train.py           just train       — score the validation year, as often as you like
  scripts/quantiles.py       just quantiles   — QRA and conformal ranges around LEAR, scored on 2023
  scripts/final_score.py     just final-score — read the held-back years, once per stage (`ranges`: stage 3)
  scripts/significance.py    just significance — every p-value the README states, from MLflow
  scripts/backtest.py        just backtest    — the battery on 2023 (`ceiling`: perfect foresight; `fixed`: LEAR and naive)
  reports/scores.csv         every scored run, appended, stamped with its commit
  reports/quantile_scores.csv the same for ranges: pinball, coverage, crossing, window
```

Everything above `features.py` is transport: getting data from ENTSO-E onto disk without
damaging it. Everything below it is a decision. The two scripts at the bottom are split for the
same reason: `train.py` has no code path to the held-back years, and a test enforces it, so
the one reading a stage is allowed stays something you have to mean to do. That file is where the question changes from
*"did we fetch this correctly?"* to *"were we allowed to know this?"* — which is why it carries
two independent guards and a test that rebuilds a delivery day from a world truncated at the
auction deadline.

## Scope

**In:** day-ahead prices, Germany, hourly resolution, one battery, one revenue stream.

**Out:** intraday trading, balancing reserve, multiple countries, quarter-hourly modelling.
Each is interesting; each is a separate project.

**Also out, and worth naming because the distance is the point.** None of the following is
built here, and a backtest is not a system without them:

| What production adds | Why it matters |
|---|---|
| A hard deadline | the forecast exists before 12:00, every day. In practice an internal cut-off an hour earlier, leaving room to run the optimiser, submit and recover — which is an operational margin, not the information boundary the backtest is judged against. Usually ready is unusable |
| Fallbacks | when a source is late, something still has to be bid. On 9 September the ENTSO-E API was unreachable for over an hour, and only a second source kept work moving |
| Alerts, not dashboards | a message when coverage or error crosses a threshold, rather than a chart nobody is watching at 11:45 |
| Backfill and versioning | when history is revised, yesterday's decisions stay explainable |
| A named person awake at 11:45 | the part no amount of modelling replaces |

## Honest framing

Day-ahead price forecasting is not a novel research problem. Every direct marketer and
storage optimiser runs a better version of this, with more data and full-time teams. The
purpose here is a well-built, honestly evaluated implementation — not a new result.

The revenue figures are gross trading margin from day-ahead arbitrage: one revenue stream,
before grid fees, taxes and capital costs. They are not an investment case.

And one thing worth keeping in view while building, because it decides what the final number
means. **Accuracy only pays where it changes a decision.** If two forecasts produce the same
battery schedule, the more accurate one earned nothing. So the interesting result at the end
is not the error metric — it is the point where better forecasts stop converting into money.

Stage 1 has already shown the first half of that. The tree beat the straight-line model on
the validation year and lost to it on years nothing had been tuned against, which means a
difference in error that looked real was not. Whether either difference moves a euro is
stage 4's question.

## References

Listed with the claim each one supports, so a reader can check the reasoning rather than
take it on trust. Where this repository states a number, the number comes from a command in
[Running it](#running-it) — these are for the choices around it.

**Method**

| Source | What it supports here |
|---|---|
| Lago, Marcjasz, De Schutter & Weron (2021), *Forecasting day-ahead electricity prices: a review of state-of-the-art algorithms, best practices and an open-access benchmark*, Applied Energy 293 — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0306261921004529) · [preprint (PDF)](https://www.dcsc.tudelft.nl/~bdeschutter/pub/rep/21_011.pdf) · doi:10.1016/j.apenergy.2021.116983 | Why LEAR is the benchmark to beat rather than an arbitrary choice, and why the field's default calibration window is a rolling two years rather than all available history |
| [epftoolbox](https://github.com/jeslago/epftoolbox) | The reference implementation of LEAR and DNN that accompanies the paper above |
| Diebold & Mariano (1995), *Comparing Predictive Accuracy* — [paper](https://www.semanticscholar.org/paper/Comparing-Predictive-Accuracy-Diebold-Mariano/1b2e489a0ea4a937b64df59f42509fb043765cbb) | Why a lower average error is not by itself evidence that one forecast beats another: errors run in streaks and move together, so the spread has to be estimated robustly |
| Diebold (2015), *Comparing Predictive Accuracy, Twenty Years Later* — [NBER w18391 (PDF)](https://www.nber.org/system/files/working_papers/w18391/w18391.pdf) | The author's own account of where the test is misapplied — worth reading before using it, not after |
| [Testing for equal predictive accuracy with strong dependence](https://arxiv.org/pdf/2409.12662) | That the test loses power as errors become more dependent, so "not significant" must be read as *cannot tell*, never as *the same* |

**Data**

| Source | What it supports here |
|---|---|
| [ENTSO-E Transparency Platform](https://transparency.entsoe.eu) | Every series in the pull. Terms of use are theirs, which is why no raw data is committed |
| [SMARD.de](https://www.smard.de) | The independent cross-check that confirmed prices to the cent, and the fallback that kept work moving through an API outage |
| [Energy-Charts](https://api.energy-charts.info) | The validated alternative for the 37 load-forecast days ENTSO-E is missing — evaluated in [docs/data-quality.md](docs/data-quality.md) and deliberately not yet adopted |

## Licence

Code is MIT licensed — see [LICENSE](LICENSE). This covers the code only; data retrieved
from ENTSO-E remains subject to their own terms of use.
