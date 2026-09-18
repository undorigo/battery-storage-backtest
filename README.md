# Battery Storage Backtest

Forecasting German day-ahead electricity prices, and measuring what the forecast is
actually worth to a battery.

**Status:** in progress, started 8 September 2026. No results yet.

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
  (known at 11:00 on D-1)              (decision)          (actual prices)
```

Results are reported three ways, so the numbers mean something:

| Run | Forecast used | Tells you |
|-----|--------------|-----------|
| Ceiling | actual prices | what perfect foresight would have earned |
| Model | model output | what this project earned |
| Floor | naive rule | what no modelling effort earns |

**Capture rate = model revenue ÷ ceiling.**

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

Two numbers matter to a battery, and both moved in the same direction.

![Negative-price hours and average daily spread, per year](reports/figures/README_negative_hours_and_spread.png)

| Year | Hours below zero | Share | Deepest | Mean daily spread |
|---|---|---|---|---|
| 2018¹ | 27 | 1.2 % | −19 | 40.6 |
| 2019 | 211 | 2.4 % | −90 | 30.1 |
| 2020 | 298 | 3.4 % | −84 | 32.5 |
| 2021 | 139 | 1.6 % | −69 | 80.3 |
| 2022 | 69 | 0.8 % | −19 | **187.0** |
| 2023 | 301 | 3.4 % | **−500** | 97.9 |
| 2024 | 457 | 5.2 % | −135 | 111.2 |
| 2025 | **576** | **6.6 %** | −250 | 124.1 |

¹ October to December only.

**Negative hours have risen more than twentyfold** — from 27 in the zone's first quarter to
576 in 2025, when one hour in fifteen cleared below zero. One hour in 2023 reached the
−500 €/MWh floor, the lowest the auction permits.

**The daily spread has roughly quadrupled**, from about 30 €/MWh to about 124. Since a
battery is paid for the spread and nothing else, that is the headline: the opportunity this
project measures is several times larger than it was in 2019.

Both trends break in 2021–22. Gas set the price during the energy crisis, so surplus power
was rare and negative hours collapsed while the spread reached 187 €/MWh. That single
interruption sits in the middle of the training period and matters more than its two years
suggest.

### Why the price is what it is

![Residual load against price, coloured by year](reports/figures/README_residual_load_vs_price.png)

Residual load — demand minus wind and solar, built only from forecasts published before gate
closure — is the mechanism behind all of it. Where it turns negative, so does the price.

But the relationship is **not one relationship**:

| | Correlation with price |
|---|---|
| Pooled across all 62,684 hours | **0.44** |
| Within a single year | 0.58 – **0.91** |

The pooled figure is the weaker one, and that is the point. The same residual load cleared
near 40 €/MWh in 2019 and above 300 in 2022, so a model fitted across the whole record is
fitting several relationships at once.

The weakest years are 2021 (0.58) and 2022 (0.62). In those years something other than
residual load was doing most of the work, and **this dataset cannot say what** — it holds no
fuel or carbon prices. Whether to add them is an open scope question, held until the model
shows whether it needs them.

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

Commands live in the [`justfile`](justfile). Run `just` with no argument for the menu.

```bash
brew install just          # or: curl -sSf https://just.systems/install.sh | bash -s -- --to ~/.local/bin

git clone <this repo> && cd battery-storage-backtest
just setup                 # create the venv, install pinned dependencies
just test                  # 40 contract tests — offline, no token needed

cp .env.example .env       # then paste your ENTSO-E token into it
just verify                # confirm the forecast series really are forecasts
just pull                  # download the full history, ~34 MB, about 20 minutes
just explore               # the headline numbers above, and the figures
```

`just pull` fetches the whole history every time and never overwrites what is already
cached. Run it twice and every series reports `unchanged` — that is the reproducibility
check, and it is why a revision on ENTSO-E's side cannot rewrite the data a published
result rested on. Displaced copies are kept under `data/raw/archive/`, and every pull
appends a line to `data/raw/manifest.csv`.

`just` searches parent directories, so any of these work from anywhere in the project. The
same commands are available in VS Code under *Tasks: Run Task*.

Python 3.11.14, pinned in `.python-version`. Dependencies are pinned exactly in
`requirements.txt` — a clean clone resolves to the same versions.

## Structure

[docs/architecture.md](docs/architecture.md) is the map — what each file is for, how they
connect, and where to start reading. In short:

```
BUILT
  src/config.py            split dates, EIC codes, battery parameters — single source of truth
  src/sources/entsoe.py    the data-item catalog: what is fetched, and what may reach a model
  src/data.py              caching and normalisation; the loaders everything else calls
  scripts/                 entry points — one per command in the justfile

PLANNED
  src/features.py          feature construction; enforces the availability rule
  src/models.py            training, benchmarks, quantile models
  src/backtest.py          dispatch optimiser and settlement
  src/evaluate.py          rMAE, Diebold-Mariano, pinball loss, capture rate
```

## Scope

**In:** day-ahead prices, Germany, hourly resolution, one battery, one revenue stream.

**Out:** intraday trading, balancing reserve, multiple countries, quarter-hourly modelling.
Each is interesting; each is a separate project.

## Honest framing

Day-ahead price forecasting is not a novel research problem. Every direct marketer and
storage optimiser runs a better version of this, with more data and full-time teams. The
purpose here is a well-built, honestly evaluated implementation — not a new result.

The revenue figures are gross trading margin from day-ahead arbitrage: one revenue stream,
before grid fees, taxes and capital costs. They are not an investment case.

## Licence

Code is MIT licensed — see [LICENSE](LICENSE). This covers the code only; data retrieved
from ENTSO-E remains subject to their own terms of use.
