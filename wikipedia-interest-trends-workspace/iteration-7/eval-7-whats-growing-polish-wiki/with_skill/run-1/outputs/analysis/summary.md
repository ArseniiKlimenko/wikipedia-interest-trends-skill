# Wikipedia interest analysis

Period 2024-09-01..2026-08-31 (24 months). Growth = last 12 months (2025-09..2026-08) vs previous 12 (2024-09..2025-08).
Traffic: agent=user (humans; known bots excluded), access=all-access; redirects mode=auto.

## Articles used
- Maroko · pl: "Maroko" (Q1028)
- Malta · pl: "Malta" (Q233)
- Poznań · pl: "Poznań" (Q268)
- Order Odrodzenia Polski · pl: "Order Odrodzenia Polski" (Q579688)

## Results

| Series | Views/mo | Per 1M wiki views | Views chg | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Next 12m forecast [80%] | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| Maroko | 30,936 | 164.5 | +14% | +26% [+12%, +44%] | +43% | +21% | 10/12 | 13% | +61% [+27%, +108%] | HIGH (growing) |
| Malta | 64,141 | 341.0 | +3% | +13% [+5%, +23%] | +13% | +9% | 11/12 | 15% | -1% [-8%, +7%] | HIGH (growing) |
| Poznań | 27,330 | 145.3 | -1% | +8% [+3%, +16%] | +7% | +9% | 11/12 | 0% | -14% [-28%, +5%] | MEDIUM (growing) |
| Order Odrodzenia Polski | 41,586 | 221.1 | -2% | +8% [+1%, +16%] | +8% | +8% | 8/12 | 4% | -32% [-52%, -3%] | MEDIUM (growing) |

Whole-wiki human views, same comparison: pl -9%.
Reading guide: Relative growth = change in the topic's share of all views of that wiki (main interest signal; already net of the whole-wiki change above, so never subtract that change again). Views chg = raw reader numbers. Per 1M wiki views = intensity of interest, comparable across languages. Confidence = trust in the direction of relative growth.

## Confidence notes
- Maroko: HIGH, growing. Supports: solid volume (~1017 views/day); 95% interval excludes zero (+12% to +44%); raw views move the same way (+14%); 10 of the last 12 months moved the same way year-over-year; spikes are only 13% of views. Largest spikes: 2026-07-09 (x26.9), 2026-07-04 (x13.5), 2026-07-31 (x10.7).
- Malta: HIGH, growing. Supports: solid volume (~2109 views/day); 95% interval excludes zero (+5% to +23%); raw views move the same way (+3%); 11 of the last 12 months moved the same way year-over-year; spikes are only 15% of views. Largest spikes: 2025-11-17 (x53.8), 2025-03-24 (x40.9), 2025-11-18 (x8.5).
- Poznań: MEDIUM, growing. Supports: solid volume (~899 views/day); 95% interval excludes zero (+3% to +16%); 11 of the last 12 months moved the same way year-over-year; spikes are only 0% of views. Concerns: raw views move the other way (-1%): the change is relative to a shrinking wiki. Largest spikes: 2026-03-15 (x2.0).
- Order Odrodzenia Polski: MEDIUM, growing. Supports: solid volume (~1367 views/day); 95% interval excludes zero (+1% to +16%); 8 of the last 12 months moved the same way year-over-year; spikes are only 4% of views. Concerns: raw views move the other way (-2%): the change is relative to a shrinking wiki. Largest spikes: 2026-04-27 (x7.2), 2025-03-22 (x4.4), 2026-04-29 (x4.2).

## Seasonality, forecast and regime changes (monthly share of wiki views)
- Maroko: seasonality moderate (0.43): peaks Jan +16%, Mar +10%; low May -19%, Apr -8%; forecast next 12 months vs last 12: +61% [80%: +27%, +108%] (model: ETS(A,Ad,A) on log, chosen by backtest).
- Malta: seasonality strong (0.87): peaks Mar +22%, Jan +14%; low Jun -12%, Dec -10%; forecast next 12 months vs last 12: -1% [80%: -8%, +7%] (model: ETS(A,Ad,A) on log, chosen by backtest).
- Poznań: seasonality strong (0.71): peaks Sep +13%, Aug +11%; low Jan -10%, Feb -7%; forecast next 12 months vs last 12: -14% [80%: -28%, +5%] (model: ETS(A,Ad,A) on log, chosen by backtest).
- Order Odrodzenia Polski: seasonality weak (0.34): peaks Feb +7%, Aug +7%; low Jul -13%, May -3%; forecast next 12 months vs last 12: -32% [80%: -52%, -3%] (model: ETS(A,Ad,A) on log, chosen by backtest).
Forecasts extrapolate the recent pattern; they cannot foresee news or product launches.

## Partial pooling (empirical Bayes; steadies small, noisy wikis)
- pl.wikipedia: common trend +12%, between-series spread tau=0.04 (k=4).
  - Maroko: raw +26% -> pooled +15% [+8%, +22%] (weight on own data 0.23)
  - Malta: raw +13% -> pooled +12% [+7%, +18%] (weight on own data 0.46)
  - Poznań: raw +8% -> pooled +9% [+5%, +15%] (weight on own data 0.57)
  - Order Odrodzenia Polski: raw +8% -> pooled +10% [+4%, +15%] (weight on own data 0.48)
Pooled values shrink noisy estimates toward the group's common trend; with tau=0 the data are consistent with one shared trend. Quote raw growth as the measurement, pooled as the robust estimate.

## Comparisons (difference in relative growth, percentage points)
- pl.wikipedia: Maroko vs Malta: +12 pp [-1, +30] -> difference not statistically clear
- pl.wikipedia: Maroko vs Poznań: +17 pp [-0, +37] -> difference not statistically clear
- pl.wikipedia: Maroko vs Order Odrodzenia Polski: +18 pp [+1, +38] -> clear difference

## Opportunity ranking (weights size=1, growth=1, intensity=0.5; 1 = best)
1. Malta - score 0.87 (size 1.00, growth 0.67, intensity 1.00; confidence high)
2. Maroko - score 0.60 (size 0.33, growth 1.00, intensity 0.33; confidence high)
3. Order Odrodzenia Polski - score 0.53 (size 0.67, growth 0.33, intensity 0.67; confidence medium)
4. Poznań - score 0.00 (size 0.00, growth 0.00, intensity 0.00; confidence medium)
Scores rank series within each group only (percentile ranks); change weights with --weights. The growth component uses the partially pooled growth (see above).

## Where readers are (approx. share of each wiki's views, 2026-08)
- pl.wikipedia: PL 87%, US 4%, DE 2%, GB 1%
Country data is approximate and omits countries Wikimedia withholds for privacy/safety.

## Suggestions (consider before concluding)
- Check demand outside Wikipedia before recommending: wt.py signals "/Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-7/eval-7-whats-growing-polish-wiki/with_skill/run-1/outputs/analysis" --keyword pl="<local phrase>" (Google Trends for the same topic per country + App Store competition); then re-run report.

## Warnings
- The period spans 2025-04-15..2025-07-15, which includes Wikimedia's bot-detection update (May-June 2025): earlier 'human' views were probably partly automated, so the drop is at least partly a measurement artifact. Relative growth reduces this effect; series flagged with a level shift there deserve extra caution.

## Files (in /Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-7/eval-7-whats-growing-polish-wiki/with_skill/run-1/outputs/analysis)
- summary: summary.md
- analysis: analysis.json
- monthly data: data.csv
- trend chart: trend.png
- growth chart: growth.png
- daily diagnostic chart: daily.png
- narrative draft (edit, then run report): narrative.md

Next: edit narrative.md (write it in the user's language), then run: wt.py report "/Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-7/eval-7-whats-growing-polish-wiki/with_skill/run-1/outputs/analysis"
