# Wikipedia interest analysis

Period 2024-09-01..2026-08-31 (24 months). Growth = last 12 months (2025-09..2026-08) vs previous 12 (2024-09..2025-08).
Traffic: agent=user (humans; known bots excluded), access=all-access; redirects mode=auto.

## Articles used
- Intermittent fasting · pl: NO ARTICLE
- Intermittent fasting · cs: "Přerušovaný půst" (Q1666254)
- Fasting (proxy for Poland) · pl: "Post" (Q44602) [+1 redirects]
- Fasting (proxy for Poland) · cs: "Půst" (Q44602)

## Results

| Series | Views/mo | Per 1M wiki views | Views chg | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| Intermittent fasting (pl) | - | - | - | no article | - | - | - | - | N/A |
| Intermittent fasting (cs) | 183 | 3.1 | -42% | -34% [-51%, -8%] | -43% | -41% | 1/12 | 17% | MEDIUM (declining) |
| Fasting (proxy for Poland) (pl) | 1,511 | 8.0 | -14% | -6% [-32%, +32%] | -11% | -7% | 5/12 | 22% | LOW (no clear change) |
| Fasting (proxy for Poland) (cs) | 602 | 10.1 | -41% | -32% [-55%, +8%] | -43% | -28% | 3/12 | 30% | LOW (no clear change) |

Whole-wiki human views, same comparison: pl -9%, cs -13%.
Reading guide: Relative growth = change in the topic's share of all views of that wiki (main interest signal; removes Wikipedia-wide traffic trends). Views chg = raw reader numbers. Per 1M wiki views = intensity of interest, comparable across languages. Confidence = trust in the direction of relative growth.

## Confidence notes
- Intermittent fasting (pl): N/A, unclear. Concerns: no article in pl.wikipedia.
- Intermittent fasting (cs): MEDIUM, declining. Supports: 95% interval excludes zero (-51% to -8%); raw views move the same way (-42%); 11 of the last 12 months moved the same way year-over-year; spikes are only 17% of views. Concerns: low volume (~6 views/day). Largest spikes: 2025-04-14 (x36.3), 2025-08-15 (x27.3), 2024-10-17 (x7.9).
- Fasting (proxy for Poland) (pl): LOW, no clear change. Supports: solid volume (~50 views/day). Concerns: sudden persistent level change around 2025-05-04 (x0.32): coincides with Wikimedia's bot-detection update (May-June 2025): earlier 'human' views were probably partly automated, so the drop is at least partly a measurement artifact; trend after it: +33%/yr; 95% interval is wide (-32% to +32%). Largest spikes: 2025-04-18 (x28.7), 2025-03-05 (x10.6), 2026-04-03 (x22.5).
- Fasting (proxy for Poland) (cs): LOW, no clear change. Concerns: low volume (~20 views/day); 95% interval is wide (-55% to +8%). Largest spikes: 2025-04-18 (x41.9), 2026-04-03 (x39.1), 2025-03-05 (x12.1).

## Comparisons (difference in relative growth, percentage points)
- topic: Fasting (proxy for Poland): Fasting (proxy for Poland) (pl) vs Fasting (proxy for Poland) (cs): +26 pp [+14, +35] -> clear difference

## Opportunity ranking (weights size=1, growth=1, intensity=0.5; 1 = best)
1. Fasting (proxy for Poland) (pl) - score 0.80 (size 1.00, growth 1.00, intensity 0.00; confidence low)
2. Fasting (proxy for Poland) (cs) - score 0.20 (size 0.00, growth 0.00, intensity 1.00; confidence low)
Scores rank series within each group only (percentile ranks); change weights with --weights.

## Where readers are (approx. share of each wiki's views, 2026-08)
- pl.wikipedia: PL 87%, US 4%, DE 2%, GB 1%
- cs.wikipedia: CZ 80%, US 5%, SK 5%
Country data is approximate and omits countries Wikimedia withholds for privacy/safety.

## Suggestions (consider before concluding)
- Intermittent fasting (cs) is measured by one article ("Přerušovaný půst", ~6 views/day). If the user means a broad subject (a course, field or skill), add 3-5 core subtopics: run `wt.py related cs:Přerušovaný půst`, pick relevant QIDs, and re-run analyze with them in the same --topic.
- Fasting (proxy for Poland) (pl) is measured by one article ("Post", ~50 views/day). If the user means a broad subject (a course, field or skill), add 3-5 core subtopics: run `wt.py related pl:Post`, pick relevant QIDs, and re-run analyze with them in the same --topic.
- Fasting (proxy for Poland) (pl) has LOW confidence; a 36-month run (--months 36) shows whether the direction persists.
- Fasting (proxy for Poland) (cs) is measured by one article ("Půst", ~20 views/day). If the user means a broad subject (a course, field or skill), add 3-5 core subtopics: run `wt.py related cs:Půst`, pick relevant QIDs, and re-run analyze with them in the same --topic.
- Fasting (proxy for Poland) (cs) has LOW confidence; a 36-month run (--months 36) shows whether the direction persists.

## Warnings
- 'Intermittent fasting' has no article in pl.wikipedia: interest cannot be measured there (also a sign of a content gap). Search in pl.wikipedia for "intermittent fasting" suggests: Stres oksydacyjny, Głodówka lecznicza, Paleolityczny styl życia, Skróty i skrótowce używane w medycynie. If one of them really covers the topic, add it as pl:<Title> and state that it is a proxy.
- The period spans 2025-04-15..2025-07-15, which includes Wikimedia's bot-detection update (May-June 2025): earlier 'human' views were probably partly automated, so the drop is at least partly a measurement artifact. Relative growth reduces this effect; series flagged with a level shift there deserve extra caution.

## Files (in /Users/aklim/Library/Application Support/Claude/scratch-workspaces/7263d695-1594-4b85-9a91-4b8981276957/c8849df8-2684-489e-ad25-c2cb19bfaf45/scratch-2026-09-26-3e841e/wikipedia-interest-trends-workspace/iteration-2/eval-1-intermittent-fasting-pl-cs/with_skill/run-1/outputs)
- summary: summary.md
- analysis: analysis.json
- monthly data: data.csv
- trend chart: trend.png
- growth chart: growth.png
- daily diagnostic chart: daily.png
- narrative draft (edit, then run report): narrative.md

Next: edit narrative.md (write it in the user's language), then run: wt.py report "/Users/aklim/Library/Application Support/Claude/scratch-workspaces/7263d695-1594-4b85-9a91-4b8981276957/c8849df8-2684-489e-ad25-c2cb19bfaf45/scratch-2026-09-26-3e841e/wikipedia-interest-trends-workspace/iteration-2/eval-1-intermittent-fasting-pl-cs/with_skill/run-1/outputs"
