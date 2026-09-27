# Wikipedia interest analysis

Period 2024-09-01..2026-08-31 (24 months). Growth = last 12 months (2025-09..2026-08) vs previous 12 (2024-09..2025-08).
Traffic: agent=user (humans; known bots excluded), access=all-access; redirects mode=auto.

## Articles used
- intermittent fasting · pl: NO ARTICLE
- intermittent fasting · cs: "Přerušovaný půst" (Q1666254)

## Results

| Series | Views/mo | Per 1M wiki views | Views chg | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| pl (польська) | - | - | - | no article | - | - | - | - | N/A |
| cs (чеська) | 183 | 3.1 | -42% | -34% [-51%, -8%] | -43% | -41% | 1/12 | 17% | MEDIUM (declining) |

Whole-wiki human views, same comparison: pl -9%, cs -13%.
Reading guide: Relative growth = change in the topic's share of all views of that wiki (main interest signal; removes Wikipedia-wide traffic trends). Views chg = raw reader numbers. Per 1M wiki views = intensity of interest, comparable across languages. Confidence = trust in the direction of relative growth.

## Confidence notes
- pl (польська): N/A, unclear. Concerns: no article in pl.wikipedia.
- cs (чеська): MEDIUM, declining. Supports: 95% interval excludes zero (-51% to -8%); raw views move the same way (-42%); 11 of the last 12 months moved the same way year-over-year; spikes are only 17% of views. Concerns: low volume (~6 views/day). Largest spikes: 2025-04-14 (x36.3), 2025-08-15 (x27.3), 2024-10-17 (x7.9).

## Where readers are (approx. share of each wiki's views, 2026-08)
- pl.wikipedia: PL 87%, US 4%, DE 2%, GB 1%
- cs.wikipedia: CZ 80%, US 5%, SK 5%
Country data is approximate and omits countries Wikimedia withholds for privacy/safety.

## Warnings
- 'intermittent fasting' has no article in pl.wikipedia: interest cannot be measured there (also a sign of a content gap). Search in pl.wikipedia for "intermittent fasting" suggests: Stres oksydacyjny, Głodówka lecznicza, Paleolityczny styl życia, Skróty i skrótowce używane w medycynie. If one of them really covers the topic, add it as pl:<Title> and state that it is a proxy.
- The period spans 2025-04-15..2025-07-15, which includes Wikimedia's bot-detection update (May-June 2025): earlier 'human' views were probably partly automated, so the drop is at least partly a measurement artifact. Relative growth reduces this effect; series flagged with a level shift there deserve extra caution.

## Files (in /Users/aklim/Library/Application Support/Claude/scratch-workspaces/7263d695-1594-4b85-9a91-4b8981276957/c8849df8-2684-489e-ad25-c2cb19bfaf45/scratch-2026-09-26-3e841e/wikipedia-interest-trends-workspace/iteration-1/intermittent-fasting-pl-cs/with_skill/outputs)
- summary: summary.md
- analysis: analysis.json
- monthly data: data.csv
- trend chart: trend.png
- growth chart: growth.png
- daily diagnostic chart: daily.png
- narrative draft (edit, then run report): narrative.md

Next: edit narrative.md (write it in the user's language), then run: wt.py report "/Users/aklim/Library/Application Support/Claude/scratch-workspaces/7263d695-1594-4b85-9a91-4b8981276957/c8849df8-2684-489e-ad25-c2cb19bfaf45/scratch-2026-09-26-3e841e/wikipedia-interest-trends-workspace/iteration-1/intermittent-fasting-pl-cs/with_skill/outputs"
