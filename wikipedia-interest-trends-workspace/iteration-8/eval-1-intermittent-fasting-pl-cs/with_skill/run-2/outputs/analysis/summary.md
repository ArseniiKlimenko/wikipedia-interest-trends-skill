# Wikipedia interest analysis

Period 2024-09-01..2026-08-31 (24 months). Growth = last 12 months (2025-09..2026-08) vs previous 12 (2024-09..2025-08).
Traffic: agent=user (humans; known bots excluded), access=all-access; redirects mode=auto.

## Rules for your reply (`report` checks the narrative against them)
- A 95% interval that crosses 0 means "no clear change": never call it growth, a rise or a positive trend.
- Each row is a language edition of Wikipedia, not a country: write "Vietnamese-language readers", not "Vietnam" (country data are in "Where readers are").
- Relative growth is already net of the whole-wiki change: do not subtract it again or compare the two.
- Quote only numbers from this summary and signals.md (same sign); add no outside market facts without a source.

## Articles used
- intermittent fasting · cs: "Přerušovaný půst" (Q1666254)
- intermittent fasting · pl: NO ARTICLE

## Results

| Series | Views/mo | Per 1M wiki views | Views chg (spikes damped) | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Next 12m forecast [80%] | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| cs.wikipedia (Czech) | 183 | 3.1 | -42% | -34% [-53%, -5%] | -43% | -41% | 1/12 | 17% | -43% [-62%, -6%] | MEDIUM (declining) |
| pl.wikipedia (Polish) | - | - | - | no article | - | - | - | - | - | N/A |

Whole-wiki human views, same comparison: cs -13%, pl -9%.
Reading guide: Relative growth = change in the topic's share of all views of that wiki (main interest signal; already net of the whole-wiki change above, so never subtract that change again). Views chg = change in reader numbers after dampening short spikes (values with spike days kept are in Confidence notes when they differ by 5+ pp). Per 1M wiki views = intensity of interest, comparable across languages. Confidence = trust in the direction of relative growth.

## Confidence notes
- cs.wikipedia (Czech): MEDIUM, declining. Supports: 95% interval excludes zero (-53% to -5%); raw views move the same way (-42%); 11 of the last 12 months moved the same way year-over-year; spikes are only 17% of views. Concerns: low volume (~6 views/day). Largest spikes: 2025-04-14 (x36.3), 2025-08-15 (x27.3), 2024-10-17 (x7.9). With spike days kept: relative -47%, views -54% (headline figures dampen spikes).
- pl.wikipedia (Polish): N/A, unclear. Concerns: no article in pl.wikipedia.

## Seasonality, forecast and regime changes (monthly share of wiki views, with up to 48 months of history)
- cs.wikipedia (Czech): seasonality moderate (0.49; repeats across 4 years, p=0.018): peaks Apr +31%, Feb +26%; low Oct -35%, Nov -34%; forecast next 12 months vs last 12: -43% [80%: -62%, -6%] (model: seasonal naive + average yearly change, chosen by a rolling-origin backtest (3 origins, 48 months of history; MAE ets 0.469, snaive 0.571, snaive_drift 0.265)).
Forecasts extrapolate the recent pattern; they cannot foresee news or product launches.

## Year over year (each 12-month block vs the block before it; uses history before the period)
- cs.wikipedia (Czech): 2023-09..2024-08 compared with 2022-09..2023-08: relative -54%, views -55%
- cs.wikipedia (Czech): 2024-09..2025-08 compared with 2023-09..2024-08: relative -36%, views -39%
- cs.wikipedia (Czech): 2025-09..2026-08 compared with 2024-09..2025-08: relative -34%, views -42%
The last line is the same comparison as the headline relative growth.

## Where readers are (approx. share of each wiki's views, 2026-08)
- cs.wikipedia: CZ 80%, US 5%, SK 5%
- pl.wikipedia: PL 87%, US 4%, DE 2%, GB 1%
Country data is approximate and omits countries Wikimedia withholds for privacy/safety.

## Suggestions (consider before concluding)
- cs.wikipedia (Czech) is measured by one article ("Přerušovaný půst", ~6 views/day). If the user means a broad subject (a course, field or skill), add 3-5 core subtopics: run `wt.py related cs:Přerušovaný půst`, pick relevant QIDs, and re-run analyze with them in the same --topic.
- Check demand outside Wikipedia before recommending: wt.py signals "/Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-8/eval-1-intermittent-fasting-pl-cs/with_skill/run-2/outputs/analysis" --trends --keyword cs="<local phrase>" --keyword pl="<local phrase>" (Google Trends for the same topic per country via its unofficial endpoint + App Store competition); then re-run report.

## Warnings
- 'intermittent fasting' has no article in pl.wikipedia: interest cannot be measured there (also a sign of a content gap). Search in pl.wikipedia for "intermittent fasting" suggests: Stres oksydacyjny, Głodówka lecznicza, Paleolityczny styl życia, Skróty i skrótowce używane w medycynie. If one of them really covers the topic, add it as pl:<Title> and state that it is a proxy.
- The period includes Wikimedia's bot-detection update (May-June 2025), which reclassified part of the earlier 'human' views as automated. Measured step of whole-wiki human views across it (Jul-Aug vs Mar-Apr 2025, seasonally adjusted with 2024 where available): cs +3%, pl -5%. Relative growth nets out a step that a topic shares with its wiki. No series moved differently from its wiki by 25% or more, so the update is unlikely to drive these results; do not cite it as an explanation.

## Files (in /Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-8/eval-1-intermittent-fasting-pl-cs/with_skill/run-2/outputs/analysis)
- summary: summary.md
- analysis: analysis.json
- monthly data: data.csv
- trend chart: trend.png
- growth chart: growth.png
- daily diagnostic chart: daily.png
- narrative draft (edit, then run report): narrative.md

Next: edit narrative.md (write it in the user's language), then run: wt.py report "/Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-8/eval-1-intermittent-fasting-pl-cs/with_skill/run-2/outputs/analysis"
