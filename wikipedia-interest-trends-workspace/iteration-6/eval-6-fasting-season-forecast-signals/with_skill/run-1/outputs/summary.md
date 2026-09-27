# Wikipedia interest analysis

Period 2024-09-01..2026-08-31 (24 months). Growth = last 12 months (2025-09..2026-08) vs previous 12 (2024-09..2025-08).
Traffic: agent=user (humans; known bots excluded), access=all-access; redirects mode=auto.

## Articles used
- intermittent fasting · cs: "Přerušovaný půst" (Q1666254)
- intermittent fasting · de: "Intermittierendes Fasten" (Q1666254)

## Results

| Series | Views/mo | Per 1M wiki views | Views chg | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Next 12m forecast [80%] | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| cs (чеська) | 183 | 3.1 | -42% | -34% [-51%, -8%] | -43% | -41% | 1/12 | 17% | +5% [-44%, +155%] | MEDIUM (declining) |
| de (німецька) | 1,563 | 2.2 | -42% | -38% [-45%, -30%] | -36% | -33% | 1/12 | 2% | +24% [-22%, +117%] | HIGH (declining) |

Whole-wiki human views, same comparison: cs -13%, de -7%.
Reading guide: Relative growth = change in the topic's share of all views of that wiki (main interest signal; already net of the whole-wiki change above, so never subtract that change again). Views chg = raw reader numbers. Per 1M wiki views = intensity of interest, comparable across languages. Confidence = trust in the direction of relative growth.

## Confidence notes
- cs (чеська): MEDIUM, declining. Supports: 95% interval excludes zero (-51% to -8%); raw views move the same way (-42%); 11 of the last 12 months moved the same way year-over-year; spikes are only 17% of views. Concerns: low volume (~6 views/day). Largest spikes: 2025-04-14 (x36.3), 2025-08-15 (x27.3), 2024-10-17 (x7.9).
- de (німецька): HIGH, declining. Supports: solid volume (~51 views/day); 95% interval excludes zero (-45% to -30%); raw views move the same way (-42%); 11 of the last 12 months moved the same way year-over-year; spikes are only 2% of views. Largest spikes: 2025-01-26 (x3.2), 2025-01-25 (x3.0), 2025-01-27 (x2.6).

## Seasonality, forecast and regime changes (monthly share of wiki views)
- cs (чеська): seasonality strong (0.67): peaks Jan +81%, Apr +17%; low Jul -28%, Nov -26%; forecast next 12 months vs last 12: +5% [80%: -44%, +155%] (model: ETS(A,Ad,A) on log, chosen by backtest).
- de (німецька): seasonality moderate (0.61): peaks Jan +20%, Mar +20%; low Dec -20%, Sep -19%; forecast next 12 months vs last 12: +24% [80%: -22%, +117%] (model: ETS(A,Ad,A) on log, chosen by backtest).
Forecasts extrapolate the recent pattern; they cannot foresee news or product launches.

## Comparisons (difference in relative growth, percentage points)
- topic: intermittent fasting: cs (чеська) vs de (німецька): +4 pp [-13, +28] -> difference not statistically clear

## Opportunity ranking (weights size=1, growth=1, intensity=0.5; 1 = best)
1. cs (чеська) - score 0.60 (size 0.00, growth 1.00, intensity 1.00; confidence medium)
2. de (німецька) - score 0.40 (size 1.00, growth 0.00, intensity 0.00; confidence high)
Scores rank series within each group only (percentile ranks); change weights with --weights.

## Where readers are (approx. share of each wiki's views, 2026-08)
- cs.wikipedia: CZ 80%, US 5%, SK 5%
- de.wikipedia: DE 75%, AT 8%, CH 5%, US 4%
Country data is approximate and omits countries Wikimedia withholds for privacy/safety.

## Suggestions (consider before concluding)
- cs (чеська) is measured by one article ("Přerušovaný půst", ~6 views/day). If the user means a broad subject (a course, field or skill), add 3-5 core subtopics: run `wt.py related cs:Přerušovaný půst`, pick relevant QIDs, and re-run analyze with them in the same --topic.

## Warnings
- The period spans 2025-04-15..2025-07-15, which includes Wikimedia's bot-detection update (May-June 2025): earlier 'human' views were probably partly automated, so the drop is at least partly a measurement artifact. Relative growth reduces this effect; series flagged with a level shift there deserve extra caution.

## Files (in /Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-6/eval-6-fasting-season-forecast-signals/with_skill/run-1/outputs)
- summary: summary.md
- analysis: analysis.json
- monthly data: data.csv
- trend chart: trend.png
- growth chart: growth.png
- daily diagnostic chart: daily.png
- narrative draft (edit, then run report): narrative.md

Next: edit narrative.md (write it in the user's language), then run: wt.py report "/Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-6/eval-6-fasting-season-forecast-signals/with_skill/run-1/outputs"
