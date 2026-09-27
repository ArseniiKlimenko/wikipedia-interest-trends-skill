# Wikipedia interest analysis

Period 2023-09-01..2026-08-31 (36 months). Growth = last 12 months (2025-09..2026-08) vs previous 12 (2024-09..2025-08).
Traffic: agent=user (humans; known bots excluded), access=all-access; redirects mode=auto.

## Articles used
- Чумацький Шлях · uk: "Чумацький Шлях" (Q321)
- Космологія · uk: "Космологія" (Q338)
- Астрофізика · uk: "Астрофізика" (Q37547) [+2 redirects]
- Метеорний потік · uk: "Метеорний потік" (Q105000)

## Results

| Series | Views/mo | Per 1M wiki views | Views chg | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Next 12m forecast [80%] | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| Чумацький Шлях | 2,302 | 40.7 | -38% | -18% [-27%, -6%] | -14% | -19% | 0/12 | 0% | -18% [-28%, -4%] | HIGH (declining) |
| Космологія | 181 | 3.2 | -43% | -25% [-36%, -11%] | -5% | -19% | 3/12 | 0% | +47% [+4%, +124%] | MEDIUM (declining) |
| Астрофізика | 183 | 3.2 | -51% | -35% [-59%, +3%] | +0% | -29% | 4/12 | 7% | -24% [-50%, +18%] | LOW (no clear change) |
| Метеорний потік | 200 | 3.5 | -43% | -24% [-53%, +4%] | +10% | -35% | 3/12 | 12% | -31% [-59%, +12%] | LOW (no clear change) |

Whole-wiki human views, same comparison: uk -25%.
Reading guide: Relative growth = change in the topic's share of all views of that wiki (main interest signal; already net of the whole-wiki change above, so never subtract that change again). Views chg = raw reader numbers. Per 1M wiki views = intensity of interest, comparable across languages. Confidence = trust in the direction of relative growth.

## Confidence notes
- Чумацький Шлях: HIGH, declining. Supports: solid volume (~76 views/day); 95% interval excludes zero (-27% to -6%); raw views move the same way (-38%); 12 of the last 12 months moved the same way year-over-year; spikes are only 0% of views. Largest spikes: 2024-09-16 (x2.8), 2025-11-26 (x2.1), 2026-01-05 (x2.5).
- Космологія: MEDIUM, declining. Supports: 95% interval excludes zero (-36% to -11%); raw views move the same way (-43%); 9 of the last 12 months moved the same way year-over-year; spikes are only 0% of views. Concerns: low volume (~6 views/day). Largest spikes: 2025-09-17 (x5.5).
- Астрофізика: LOW, no clear change. Concerns: low volume (~6 views/day); sudden persistent level change around 2024-08-28 (x3.6): check for a rename, merge, bot traffic or a real event; trend after it: -33%/yr; 95% interval is wide (-59% to +3%). Largest spikes: 2024-09-10 (x5.9), 2024-09-11 (x5.2), 2024-09-12 (x4.0).
- Метеорний потік: LOW, no clear change. Concerns: low volume (~7 views/day); 95% interval is wide (-53% to +4%). Largest spikes: 2026-08-12 (x18.6), 2024-08-12 (x11.2), 2026-08-13 (x11.5).

## Seasonality, forecast and regime changes (monthly share of wiki views)
- Чумацький Шлях: seasonality strong (0.82): peaks Apr +28%, Mar +18%; low Jun -25%, Jul -21%; forecast next 12 months vs last 12: -18% [80%: -28%, -4%] (model: seasonal naive + average yearly change, chosen by backtest; smoothing model vs 'same as last year': skill +0.11).
- Космологія: seasonality moderate (0.61): peaks Apr +54%, Sep +45%; low Jul -36%, Aug -27%; forecast next 12 months vs last 12: +47% [80%: +4%, +124%] (model: ETS(A,Ad,A) on log, chosen by backtest; smoothing model vs 'same as last year': skill +0.17).
- Астрофізика: seasonality strong (0.85): peaks Sep +359%, Dec +23%; low Jun -37%, Jul -37%; forecast next 12 months vs last 12: -24% [80%: -50%, +18%] (model: seasonal naive + average yearly change, chosen by backtest; smoothing model vs 'same as last year': skill -0.38).
- Метеорний потік: seasonality moderate (0.59): peaks Aug +125%, Feb +38%; low Jun -41%, Mar -23%; forecast next 12 months vs last 12: -31% [80%: -59%, +12%] (model: seasonal naive + average yearly change, chosen by backtest; smoothing model vs 'same as last year': skill -1.18).
Forecasts extrapolate the recent pattern; they cannot foresee news or product launches.

## Partial pooling (empirical Bayes; steadies small, noisy wikis)
- uk.wikipedia: common trend -21%, between-series spread tau=0.00 (k=4).
  - Чумацький Шлях: raw -18% -> pooled -21% [-28%, -14%] (weight on own data 0.00)
  - Космологія: raw -25% -> pooled -21% [-28%, -14%] (weight on own data 0.00)
  - Астрофізика: raw -35% -> pooled -21% [-28%, -14%] (weight on own data 0.00)
  - Метеорний потік: raw -24% -> pooled -21% [-28%, -14%] (weight on own data 0.00)
Pooled values shrink noisy estimates toward the group's common trend; with tau=0 the data are consistent with one shared trend. Quote raw growth as the measurement, pooled as the robust estimate.

## Year over year (each 12-month block vs the block before it)
- Чумацький Шлях: 2024-09..2025-08 compared with 2023-09..2024-08: relative -20%, views -35%
- Чумацький Шлях: 2025-09..2026-08 compared with 2024-09..2025-08: relative -18%, views -38%
- Космологія: 2024-09..2025-08 compared with 2023-09..2024-08: relative -14%, views -30%
- Космологія: 2025-09..2026-08 compared with 2024-09..2025-08: relative -25%, views -43%
- Астрофізика: 2024-09..2025-08 compared with 2023-09..2024-08: relative -26%, views -41%
- Астрофізика: 2025-09..2026-08 compared with 2024-09..2025-08: relative -35%, views -51%
- Метеорний потік: 2024-09..2025-08 compared with 2023-09..2024-08: relative -33%, views -46%
- Метеорний потік: 2025-09..2026-08 compared with 2024-09..2025-08: relative -24%, views -43%
The last line is the same comparison as the headline relative growth.

## Comparisons (difference in relative growth, percentage points)
- uk.wikipedia: Чумацький Шлях vs Метеорний потік: +6 pp [-23, +37] -> difference not statistically clear
- uk.wikipedia: Чумацький Шлях vs Космологія: +7 pp [-3, +18] -> difference not statistically clear
- uk.wikipedia: Чумацький Шлях vs Астрофізика: +17 pp [-18, +40] -> difference not statistically clear

## Opportunity ranking (weights size=1, growth=1, intensity=0.5; 1 = best)
1. Чумацький Шлях - score 0.80 (size 1.00, growth 0.50, intensity 1.00; confidence high)
2. Метеорний потік - score 0.60 (size 0.67, growth 0.50, intensity 0.67; confidence low)
3. Астрофізика - score 0.40 (size 0.33, growth 0.50, intensity 0.33; confidence low)
4. Космологія - score 0.20 (size 0.00, growth 0.50, intensity 0.00; confidence medium)
Scores rank series within each group only (percentile ranks); change weights with --weights. The growth component uses the partially pooled growth (see above).

## Where readers are (approx. share of each wiki's views, 2026-08)
- uk.wikipedia: UA 65%, US 11%, PL 4%, GB 3%, DE 3%, BR 1%
Country data is approximate and omits countries Wikimedia withholds for privacy/safety.

## Suggestions (consider before concluding)
- Космологія is measured by one article ("Космологія", ~6 views/day). If the user means a broad subject (a course, field or skill), add 3-5 core subtopics: run `wt.py related uk:Космологія`, pick relevant QIDs, and re-run analyze with them in the same --topic.
- Астрофізика is measured by one article ("Астрофізика", ~6 views/day). If the user means a broad subject (a course, field or skill), add 3-5 core subtopics: run `wt.py related uk:Астрофізика`, pick relevant QIDs, and re-run analyze with them in the same --topic.
- Метеорний потік is measured by one article ("Метеорний потік", ~7 views/day). If the user means a broad subject (a course, field or skill), add 3-5 core subtopics: run `wt.py related uk:Метеорний потік`, pick relevant QIDs, and re-run analyze with them in the same --topic.

## Warnings
- The period spans 2025-04-15..2025-07-15, which includes Wikimedia's bot-detection update (May-June 2025): earlier 'human' views were probably partly automated, so the drop is at least partly a measurement artifact. Relative growth reduces this effect; series flagged with a level shift there deserve extra caution.

## Files (in /Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-6/eval-5-growing-subtopics-astronomy/with_skill/run-1/outputs/subtopics-detail)
- summary: summary.md
- analysis: analysis.json
- monthly data: data.csv
- trend chart: trend.png
- growth chart: growth.png
- daily diagnostic chart: daily.png
- narrative draft (edit, then run report): narrative.md

Next: edit narrative.md (write it in the user's language), then run: wt.py report "/Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-6/eval-5-growing-subtopics-astronomy/with_skill/run-1/outputs/subtopics-detail"
