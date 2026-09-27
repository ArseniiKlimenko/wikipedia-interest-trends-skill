# Wikipedia interest analysis

Period 2024-09-01..2026-08-31 (24 months). Growth = last 12 months (2025-09..2026-08) vs previous 12 (2024-09..2025-08).
Traffic: agent=user (humans; known bots excluded), access=all-access; redirects mode=auto.

## Rules for your reply (`report` checks the narrative against them)
- A 95% interval that crosses 0 means "no clear change": never call it growth, a rise or a positive trend.
- Each row is a language edition of Wikipedia, not a country: write "Vietnamese-language readers", not "Vietnam" (country data are in "Where readers are").
- Relative growth is already net of the whole-wiki change: do not subtract it again or compare the two.
- Quote only numbers from this summary and signals.md (same sign); add no outside market facts without a source.

## Articles used
- Астрономія · uk: "Астрономія" (Q333) [5% of views, rel. growth -49%]; "Чумацький Шлях" (Q321) [19% of views, rel. growth -18%]; "Галактика" (Q318) [6% of views, rel. growth -40%]; "Земля" (Q2) [27% of views, rel. growth -30%]; "Сонце" (Q525) [20% of views, rel. growth -38%]; "Місяць (супутник)" (Q405) [16% of views, rel. growth -40%]; "Зоря" (Q523) [8% of views, rel. growth -38%]

## Results

| Series | Views/mo | Per 1M wiki views | Views chg (spikes damped) | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Next 12m forecast [80%] | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| Астрономія · uk.wikipedia | 12,256 | 216.7 | -50% | -33% [-44%, -20%] | -25% | -37% | 0/12 | 0% | -22% [-38%, +7%] | HIGH (declining) |

Whole-wiki human views, same comparison: uk -25%.
Reading guide: Relative growth = change in the topic's share of all views of that wiki (main interest signal; already net of the whole-wiki change above, so never subtract that change again). Views chg = change in reader numbers after dampening short spikes (values with spike days kept are in Confidence notes when they differ by 5+ pp). Per 1M wiki views = intensity of interest, comparable across languages. Confidence = trust in the direction of relative growth.

## Confidence notes
- Астрономія · uk.wikipedia: HIGH, declining. Supports: solid volume (~403 views/day); 95% interval excludes zero (-44% to -20%); raw views move the same way (-50%); 12 of the last 12 months moved the same way year-over-year; spikes are only 0% of views.

## Seasonality, forecast and regime changes (monthly share of wiki views, with up to 48 months of history)
- Астрономія · uk.wikipedia: seasonality strong (0.85; repeats across 4 years, p=0.004): peaks Feb +36%, Mar +16%; low Jul -39%, Jun -30%; forecast next 12 months vs last 12: -22% [80%: -38%, +7%] (model: seasonal naive + average yearly change, chosen by a rolling-origin backtest (3 origins, 48 months of history; MAE ets 0.202, snaive 0.337, snaive_drift 0.186)); regime change 2024-02: level -14%, trend +8%/yr -> -27%/yr.
Forecasts extrapolate the recent pattern; they cannot foresee news or product launches.

## Year over year (each 12-month block vs the block before it; uses history before the period)
- Астрономія · uk.wikipedia: 2023-09..2024-08 compared with 2022-09..2023-08: relative -1%, views -7%
- Астрономія · uk.wikipedia: 2024-09..2025-08 compared with 2023-09..2024-08: relative -28%, views -41%
- Астрономія · uk.wikipedia: 2025-09..2026-08 compared with 2024-09..2025-08: relative -33%, views -50%
The last line is the same comparison as the headline relative growth.

## Where readers are (approx. share of each wiki's views, 2026-08)
- uk.wikipedia: UA 65%, US 11%, PL 4%, GB 3%, DE 3%, BR 1%
Country data is approximate and omits countries Wikimedia withholds for privacy/safety.

## Suggestions (consider before concluding)
- Check demand outside Wikipedia before recommending: wt.py signals "/Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-8/eval-2-astronomy-uk-trust/with_skill/run-2/outputs/analysis" --trends --keyword uk="<local phrase>" (Google Trends for the same topic per country via its unofficial endpoint + App Store competition); then re-run report.

## Warnings
- The period includes Wikimedia's bot-detection update (May-June 2025), which reclassified part of the earlier 'human' views as automated. Measured step of whole-wiki human views across it (Jul-Aug vs Mar-Apr 2025, seasonally adjusted with 2024 where available): uk +29%. Relative growth nets out a step that a topic shares with its wiki. No series moved differently from its wiki by 25% or more, so the update is unlikely to drive these results; do not cite it as an explanation.

## Files (in /Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-8/eval-2-astronomy-uk-trust/with_skill/run-2/outputs/analysis)
- summary: summary.md
- analysis: analysis.json
- monthly data: data.csv
- trend chart: trend.png
- growth chart: growth.png
- daily diagnostic chart: daily.png
- narrative draft (edit, then run report): narrative.md

Next: edit narrative.md (write it in the user's language), then run: wt.py report "/Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-8/eval-2-astronomy-uk-trust/with_skill/run-2/outputs/analysis"
