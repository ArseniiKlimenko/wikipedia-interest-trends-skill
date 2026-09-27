# Wikipedia interest analysis

Period 2023-09-01..2026-08-31 (36 months). Growth = last 12 months (2025-09..2026-08) vs previous 12 (2024-09..2025-08).
Traffic: agent=user (humans; known bots excluded), access=all-access; redirects mode=auto.

## Articles used
- Екзопланета · uk: "Екзопланета" (Q44559)
- Чорна діра · uk: "Чорна діра" (Q589)
- Дослідження космосу · uk: "Дослідження космосу" (Q180046) [+2 redirects]

## Results

| Series | Views/mo | Per 1M wiki views | Views chg | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Next 12m forecast [80%] | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| Екзопланета | 543 | 9.6 | -45% | -28% [-40%, -12%] | -31% | -14% | 1/12 | 1% | -27% [-39%, -11%] | MEDIUM (declining) |
| Чорна діра | 1,810 | 32.0 | -31% | -9% [-23%, +6%] | -13% | -11% | 4/12 | 0% | -9% [-26%, +7%] | LOW (no clear change) |
| Дослідження космосу | 246 | 4.4 | -80% | -73% [-82%, -60%] | -57% | -55% | 1/12 | 0% | -52% [-78%, -10%] | LOW (declining) |

Whole-wiki human views, same comparison: uk -25%.
Reading guide: Relative growth = change in the topic's share of all views of that wiki (main interest signal; already net of the whole-wiki change above, so never subtract that change again). Views chg = raw reader numbers. Per 1M wiki views = intensity of interest, comparable across languages. Confidence = trust in the direction of relative growth.

## Confidence notes
- Екзопланета: MEDIUM, declining. Supports: 95% interval excludes zero (-40% to -12%); raw views move the same way (-45%); 11 of the last 12 months moved the same way year-over-year; spikes are only 1% of views. Concerns: low volume (~18 views/day). Largest spikes: 2025-04-17 (x4.6), 2026-01-08 (x4.9), 2024-05-22 (x2.1).
- Чорна діра: LOW, no clear change. Supports: solid volume (~60 views/day). Concerns: 95% interval is wide (-23% to +6%). Largest spikes: 2023-10-19 (x2.4), 2023-10-18 (x2.2), 2025-11-06 (x2.7).
- Дослідження космосу: LOW, declining. Supports: 95% interval excludes zero (-82% to -60%); raw views move the same way (-80%); 11 of the last 12 months moved the same way year-over-year; spikes are only 0% of views. Concerns: low volume (~8 views/day); sudden persistent level change around 2024-09-02 (x5.1): check for a rename, merge, bot traffic or a real event; trend after it: -71%/yr. Largest spikes: 2026-05-15 (x6.8), 2025-10-17 (x2.9).

## Seasonality, forecast and regime changes (monthly share of wiki views)
- Екзопланета: seasonality strong (0.86): peaks Feb +74%, Apr +43%; low Jul -32%, Oct -25%; forecast next 12 months vs last 12: -27% [80%: -39%, -11%] (model: ETS(A,Ad,A) on log, chosen by backtest; smoothing model vs 'same as last year': skill +0.54).
- Чорна діра: seasonality strong (0.74): peaks Apr +40%, Mar +24%; low Jul -29%, Jun -26%; forecast next 12 months vs last 12: -9% [80%: -26%, +7%] (model: seasonal naive + average yearly change, chosen by backtest; smoothing model vs 'same as last year': skill -0.93).
- Дослідження космосу: seasonality strong (0.80): peaks Apr +121%, Dec +104%; low Jul -76%, Aug -74%; forecast next 12 months vs last 12: -52% [80%: -78%, -10%] (model: seasonal naive + average yearly change, chosen by backtest; smoothing model vs 'same as last year': skill +0.33); regime change 2025-09: level -61%, trend -40%/yr -> +62%/yr.
Forecasts extrapolate the recent pattern; they cannot foresee news or product launches.

## Partial pooling (empirical Bayes; steadies small, noisy wikis)
- uk.wikipedia: common trend -42%, between-series spread tau=0.44 (k=3).
  - Екзопланета: raw -28% -> pooled -28% [-41%, -13%] (weight on own data 0.95)
  - Чорна діра: raw -9% -> pooled -10% [-23%, +5%] (weight on own data 0.97)
  - Дослідження космосу: raw -73% -> pooled -69% [-79%, -56%] (weight on own data 0.83)
Pooled values shrink noisy estimates toward the group's common trend; with tau=0 the data are consistent with one shared trend. Quote raw growth as the measurement, pooled as the robust estimate.

## Year over year (each 12-month block vs the block before it)
- Екзопланета: 2024-09..2025-08 compared with 2023-09..2024-08: relative -6%, views -24%
- Екзопланета: 2025-09..2026-08 compared with 2024-09..2025-08: relative -28%, views -45%
- Чорна діра: 2024-09..2025-08 compared with 2023-09..2024-08: relative -10%, views -27%
- Чорна діра: 2025-09..2026-08 compared with 2024-09..2025-08: relative -9%, views -31%
- Дослідження космосу: 2024-09..2025-08 compared with 2023-09..2024-08: relative -27%, views -41%
- Дослідження космосу: 2025-09..2026-08 compared with 2024-09..2025-08: relative -73%, views -80%
The last line is the same comparison as the headline relative growth.

## Comparisons (difference in relative growth, percentage points)
- uk.wikipedia: Чорна діра vs Екзопланета: +19 pp [+4, +33] -> clear difference
- uk.wikipedia: Чорна діра vs Дослідження космосу: +64 pp [+54, +74] -> clear difference

## Opportunity ranking (weights size=1, growth=1, intensity=0.5; 1 = best)
1. Чорна діра - score 1.00 (size 1.00, growth 1.00, intensity 1.00; confidence low)
2. Екзопланета - score 0.50 (size 0.50, growth 0.50, intensity 0.50; confidence medium)
3. Дослідження космосу - score 0.00 (size 0.00, growth 0.00, intensity 0.00; confidence low)
Scores rank series within each group only (percentile ranks); change weights with --weights. The growth component uses the partially pooled growth (see above).

## Where readers are (approx. share of each wiki's views, 2026-08)
- uk.wikipedia: UA 65%, US 11%, PL 4%, GB 3%, DE 3%, BR 1%
Country data is approximate and omits countries Wikimedia withholds for privacy/safety.

## Suggestions (consider before concluding)
- Екзопланета is measured by one article ("Екзопланета", ~18 views/day). If the user means a broad subject (a course, field or skill), add 3-5 core subtopics: run `wt.py related uk:Екзопланета`, pick relevant QIDs, and re-run analyze with them in the same --topic.
- Дослідження космосу is measured by one article ("Дослідження космосу", ~8 views/day). If the user means a broad subject (a course, field or skill), add 3-5 core subtopics: run `wt.py related uk:Дослідження космосу`, pick relevant QIDs, and re-run analyze with them in the same --topic.

## Warnings
- The period spans 2025-04-15..2025-07-15, which includes Wikimedia's bot-detection update (May-June 2025): earlier 'human' views were probably partly automated, so the drop is at least partly a measurement artifact. Relative growth reduces this effect; series flagged with a level shift there deserve extra caution.

## Files (in /Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-6/eval-5-growing-subtopics-astronomy/with_skill/run-1/outputs/contemporary-topics)
- summary: summary.md
- analysis: analysis.json
- monthly data: data.csv
- trend chart: trend.png
- growth chart: growth.png
- daily diagnostic chart: daily.png
- narrative draft (edit, then run report): narrative.md

Next: edit narrative.md (write it in the user's language), then run: wt.py report "/Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-6/eval-5-growing-subtopics-astronomy/with_skill/run-1/outputs/contemporary-topics"
