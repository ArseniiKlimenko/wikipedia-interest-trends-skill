# Wikipedia interest analysis

Period 2023-09-01..2026-08-31 (36 months). Growth = last 12 months (2025-09..2026-08) vs previous 12 (2024-09..2025-08).
Traffic: agent=user (humans; known bots excluded), access=all-access; redirects mode=auto.

## Articles used
- Астрономія · uk: "Астрономія" (Q333) [5% of views, rel. growth -47%]; "Чумацький Шлях" (Q321) [19% of views, rel. growth -18%]; "Галактика" (Q318) [6% of views, rel. growth -40%]; "Земля" (Q2) [27% of views, rel. growth -30%]; "Сонце" (Q525) [20% of views, rel. growth -38%]; "Місяць (супутник)" (Q405) [16% of views, rel. growth -40%]; "Зоря" (Q523) [8% of views, rel. growth -38%]

## Results

| Series | Views/mo | Per 1M wiki views | Views chg | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Next 12m forecast [80%] | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| Астрономія (uk) | 12,256 | 216.7 | -50% | -33% [-44%, -21%] | -25% | -32% | 0/12 | 0% | -28% [-40%, -14%] | HIGH (declining) |

Whole-wiki human views, same comparison: uk -25%.
Reading guide: Relative growth = change in the topic's share of all views of that wiki (main interest signal; already net of the whole-wiki change above, so never subtract that change again). Views chg = raw reader numbers. Per 1M wiki views = intensity of interest, comparable across languages. Confidence = trust in the direction of relative growth.

## Confidence notes
- Астрономія (uk): HIGH, declining. Supports: solid volume (~403 views/day); 95% interval excludes zero (-44% to -21%); raw views move the same way (-50%); 12 of the last 12 months moved the same way year-over-year; spikes are only 0% of views.

## Seasonality, forecast and regime changes (monthly share of wiki views)
- Астрономія (uk): seasonality strong (0.81): peaks Feb +39%, Jan +16%; low Jul -39%, Jun -30%; forecast next 12 months vs last 12: -28% [80%: -40%, -14%] (model: seasonal naive + average yearly change, chosen by backtest; smoothing model vs 'same as last year': skill -0.33).
Forecasts extrapolate the recent pattern; they cannot foresee news or product launches.

## Year over year (each 12-month block vs the block before it)
- Астрономія (uk): 2024-09..2025-08 compared with 2023-09..2024-08: relative -28%, views -41%
- Астрономія (uk): 2025-09..2026-08 compared with 2024-09..2025-08: relative -33%, views -50%
The last line is the same comparison as the headline relative growth.

## Where readers are (approx. share of each wiki's views, 2026-08)
- uk.wikipedia: UA 65%, US 11%, PL 4%, GB 3%, DE 3%, BR 1%
Country data is approximate and omits countries Wikimedia withholds for privacy/safety.

## Warnings
- The period spans 2025-04-15..2025-07-15, which includes Wikimedia's bot-detection update (May-June 2025): earlier 'human' views were probably partly automated, so the drop is at least partly a measurement artifact. Relative growth reduces this effect; series flagged with a level shift there deserve extra caution.

## Files (in /Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-6/eval-2-astronomy-uk-trust/with_skill/run-1/outputs)
- summary: summary.md
- analysis: analysis.json
- monthly data: data.csv
- trend chart: trend.png
- growth chart: growth.png
- daily diagnostic chart: daily.png
- narrative draft (edit, then run report): narrative.md

Next: edit narrative.md (write it in the user's language), then run: wt.py report "/Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-6/eval-2-astronomy-uk-trust/with_skill/run-1/outputs"
