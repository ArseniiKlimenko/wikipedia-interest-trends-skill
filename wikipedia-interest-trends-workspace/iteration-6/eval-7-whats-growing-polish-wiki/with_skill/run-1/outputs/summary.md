# Wikipedia interest analysis

Period 2024-09-01..2026-08-31 (24 months). Growth = last 12 months (2025-09..2026-08) vs previous 12 (2024-09..2025-08).
Traffic: agent=user (humans; known bots excluded), access=all-access; redirects mode=auto.

## Articles used
- Maroko · pl: "Maroko" (Q1028)
- Malta · pl: "Malta" (Q233)
- Paragwaj · pl: "Paragwaj" (Q733)
- Senegal · pl: "Senegal" (Q1041)
- Wybrzeże Kości Słoniowej · pl: "Wybrzeże Kości Słoniowej" (Q1008)
- Bractwo Kapłańskie Świętego Piusa X · pl: "Bractwo Kapłańskie Świętego Piusa X" (Q868160)

## Results

| Series | Views/mo | Per 1M wiki views | Views chg | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Next 12m forecast [80%] | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| Maroko | 30,936 | 164.5 | +14% | +26% [+12%, +44%] | +43% | +21% | 10/12 | 13% | +61% [+27%, +108%] | HIGH (growing) |
| Malta | 64,141 | 341.0 | +3% | +13% [+5%, +23%] | +13% | +9% | 11/12 | 15% | -1% [-8%, +7%] | HIGH (growing) |
| Paragwaj | 12,932 | 68.7 | +53% | +68% [+30%, +129%] | +96% | +34% | 10/12 | 34% | +39% [+11%, +98%] | MEDIUM (growing) |
| Senegal | 11,551 | 61.4 | +18% | +30% [+11%, +55%] | +37% | +23% | 9/12 | 32% | +3% [-12%, +29%] | MEDIUM (growing) |
| Wybrzeże Kości Słoniowej | 14,034 | 74.6 | +34% | +47% [+10%, +115%] | +85% | +12% | 10/12 | 38% | +19% [-8%, +86%] | MEDIUM (growing) |
| Bractwo Kapłańskie Świętego Piusa X | 15,899 | 84.5 | +95% | +114% [+45%, +238%] | +154% | +72% | 12/12 | 26% | +119% [+30%, +401%] | MEDIUM (growing) |

Whole-wiki human views, same comparison: pl -9%.
Reading guide: Relative growth = change in the topic's share of all views of that wiki (main interest signal; already net of the whole-wiki change above, so never subtract that change again). Views chg = raw reader numbers. Per 1M wiki views = intensity of interest, comparable across languages. Confidence = trust in the direction of relative growth.

## Confidence notes
- Maroko: HIGH, growing. Supports: solid volume (~1017 views/day); 95% interval excludes zero (+12% to +44%); raw views move the same way (+14%); 10 of the last 12 months moved the same way year-over-year; spikes are only 13% of views. Largest spikes: 2026-07-09 (x26.9), 2026-07-04 (x13.5), 2026-07-31 (x10.7).
- Malta: HIGH, growing. Supports: solid volume (~2109 views/day); 95% interval excludes zero (+5% to +23%); raw views move the same way (+3%); 11 of the last 12 months moved the same way year-over-year; spikes are only 15% of views. Largest spikes: 2025-11-17 (x53.8), 2025-03-24 (x40.9), 2025-11-18 (x8.5).
- Paragwaj: MEDIUM, growing. Supports: solid volume (~425 views/day); 95% interval excludes zero (+30% to +129%); raw views move the same way (+53%); 10 of the last 12 months moved the same way year-over-year. Concerns: 34% of views came from short spikes. Largest spikes: 2026-07-04 (x27.1), 2026-06-29 (x25.0), 2026-06-30 (x23.1).
- Senegal: MEDIUM, growing. Supports: solid volume (~380 views/day); 95% interval excludes zero (+11% to +55%); raw views move the same way (+18%); 9 of the last 12 months moved the same way year-over-year. Concerns: 32% of views came from short spikes. Largest spikes: 2026-06-16 (x94.5), 2026-07-01 (x62.9), 2026-06-17 (x8.4).
- Wybrzeże Kości Słoniowej: MEDIUM, growing. Supports: solid volume (~461 views/day); 95% interval excludes zero (+10% to +115%); raw views move the same way (+34%); 10 of the last 12 months moved the same way year-over-year. Concerns: 38% of views came from short spikes. Largest spikes: 2026-06-20 (x43.5), 2026-06-30 (x40.7), 2026-06-21 (x7.2).
- Bractwo Kapłańskie Świętego Piusa X: MEDIUM, growing. Supports: solid volume (~523 views/day); 95% interval excludes zero (+45% to +238%); raw views move the same way (+95%); 12 of the last 12 months moved the same way year-over-year. Concerns: 26% of views came from short spikes. Largest spikes: 2026-07-02 (x13.9), 2026-07-03 (x8.5), 2026-07-01 (x7.9).

## Seasonality, forecast and regime changes (monthly share of wiki views)
- Maroko: seasonality moderate (0.43): peaks Jan +16%, Mar +10%; low May -19%, Apr -8%; forecast next 12 months vs last 12: +61% [80%: +27%, +108%] (model: ETS(A,Ad,A) on log, chosen by backtest).
- Malta: seasonality strong (0.87): peaks Mar +22%, Jan +14%; low Jun -12%, Dec -10%; forecast next 12 months vs last 12: -1% [80%: -8%, +7%] (model: ETS(A,Ad,A) on log, chosen by backtest).
- Paragwaj: seasonality moderate (0.53): peaks Jun +35%, Jan +27%; low Aug -39%, Apr -14%; forecast next 12 months vs last 12: +39% [80%: +11%, +98%] (model: ETS(A,Ad,A) on log, chosen by backtest).
- Senegal: seasonality moderate (0.58): peaks Nov +25%, Jun +22%; low Aug -24%, Apr -14%; forecast next 12 months vs last 12: +3% [80%: -12%, +29%] (model: ETS(A,Ad,A) on log, chosen by backtest).
- Wybrzeże Kości Słoniowej: seasonality moderate (0.51): peaks Jun +80%, Dec +20%; low Feb -20%, May -20%; forecast next 12 months vs last 12: +19% [80%: -8%, +86%] (model: ETS(A,Ad,A) on log, chosen by backtest); regime change 2025-06: level -33%, trend +45%/yr -> +93%/yr (coincides with the Wikimedia bot-detection update (May-June 2025)).
- Bractwo Kapłańskie Świętego Piusa X: seasonality moderate (0.47): peaks Jul +58%, May +47%; low Mar -25%, Jan -21%; forecast next 12 months vs last 12: +119% [80%: +30%, +401%] (model: ETS(A,Ad,A) on log, chosen by backtest).
Forecasts extrapolate the recent pattern; they cannot foresee news or product launches.

## Partial pooling (empirical Bayes; steadies small, noisy wikis)
- pl.wikipedia: common trend +35%, between-series spread tau=0.13 (k=6).
  - Maroko: raw +26% -> pooled +27% [+14%, +43%] (weight on own data 0.81)
  - Malta: raw +13% -> pooled +15% [+7%, +23%] (weight on own data 0.92)
  - Paragwaj: raw +68% -> pooled +50% [+24%, +81%] (weight on own data 0.46)
  - Senegal: raw +30% -> pooled +31% [+14%, +51%] (weight on own data 0.71)
  - Wybrzeże Kości Słoniowej: raw +47% -> pooled +40% [+14%, +72%] (weight on own data 0.38)
  - Bractwo Kapłańskie Świętego Piusa X: raw +114% -> pooled +53% [+23%, +91%] (weight on own data 0.27)
Pooled values shrink noisy estimates toward the group's common trend; with tau=0 the data are consistent with one shared trend. Quote raw growth as the measurement, pooled as the robust estimate.

## Comparisons (difference in relative growth, percentage points)
- pl.wikipedia: Bractwo Kapłańskie Świętego Piusa X vs Paragwaj: +46 pp [-15, +135] -> difference not statistically clear
- pl.wikipedia: Bractwo Kapłańskie Świętego Piusa X vs Wybrzeże Kości Słoniowej: +66 pp [+2, +165] -> clear difference
- pl.wikipedia: Bractwo Kapłańskie Świętego Piusa X vs Senegal: +84 pp [+16, +199] -> clear difference
- pl.wikipedia: Bractwo Kapłańskie Świętego Piusa X vs Maroko: +88 pp [+23, +202] -> clear difference
- pl.wikipedia: Bractwo Kapłańskie Świętego Piusa X vs Malta: +100 pp [+30, +228] -> clear difference

## Opportunity ranking (weights size=1, growth=2, intensity=0.5; 1 = best)
1. Bractwo Kapłańskie Świętego Piusa X - score 0.83 (size 0.60, growth 1.00, intensity 0.60; confidence medium)
2. Paragwaj - score 0.54 (size 0.20, growth 0.80, intensity 0.20; confidence medium)
3. Wybrzeże Kości Słoniowej - score 0.51 (size 0.40, growth 0.60, intensity 0.40; confidence medium)
4. Maroko - score 0.46 (size 0.80, growth 0.20, intensity 0.80; confidence high)
5. Malta - score 0.43 (size 1.00, growth 0.00, intensity 1.00; confidence high)
6. Senegal - score 0.23 (size 0.00, growth 0.40, intensity 0.00; confidence medium)
Scores rank series within each group only (percentile ranks); change weights with --weights. The growth component uses the partially pooled growth (see above).

## Where readers are (approx. share of each wiki's views, 2026-08)
- pl.wikipedia: PL 87%, US 4%, DE 2%, GB 1%
Country data is approximate and omits countries Wikimedia withholds for privacy/safety.

## Warnings
- The period spans 2025-04-15..2025-07-15, which includes Wikimedia's bot-detection update (May-June 2025): earlier 'human' views were probably partly automated, so the drop is at least partly a measurement artifact. Relative growth reduces this effect; series flagged with a level shift there deserve extra caution.

## Files (in /Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-6/eval-7-whats-growing-polish-wiki/with_skill/run-1/outputs)
- summary: summary.md
- analysis: analysis.json
- monthly data: data.csv
- trend chart: trend.png
- growth chart: growth.png
- daily diagnostic chart: daily.png
- narrative draft (edit, then run report): narrative.md

Next: edit narrative.md (write it in the user's language), then run: wt.py report "/Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-6/eval-7-whats-growing-polish-wiki/with_skill/run-1/outputs"
