# Wikipedia interest analysis

Period 2024-09-01..2026-08-31 (24 months). Growth = last 12 months (2025-09..2026-08) vs previous 12 (2024-09..2025-08).
Traffic: agent=user (humans; known bots excluded), access=all-access; redirects mode=auto.

## Articles used
- English · pl: "Język angielski" (Q1860)
- English · tr: "İngilizce" (Q1860)
- English · es: "Idioma inglés" (Q1860)
- English · vi: "Tiếng Anh" (Q1860)
- English · de: "Englische Sprache" (Q1860)

## Results

| Series | Views/mo | Per 1M wiki views | Views chg | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| pl (польська) | 8,087 | 43.0 | -19% | -11% [-15%, -6%] | -3% | -10% | 2/12 | 1% | HIGH (declining) |
| tr (турецька) | 7,080 | 65.1 | -17% | -1% [-10%, +10%] | +15% | -5% | 8/12 | 0% | MEDIUM (no clear change) |
| es (іспанська) | 25,962 | 47.7 | -29% | -10% [-16%, -3%] | -5% | -10% | 2/12 | 0% | HIGH (declining) |
| vi (вʼєтнамська) | 12,478 | 253.8 | -23% | +2% [-8%, +15%] | -1% | -5% | 6/12 | 0% | MEDIUM (no clear change) |
| de (німецька) | 23,477 | 33.3 | -8% | -0% [-5%, +4%] | -4% | +0% | 4/12 | 0% | MEDIUM (no clear change) |

Whole-wiki human views, same comparison: pl -9%, tr -16%, es -21%, vi -24%, de -7%.
Reading guide: Relative growth = change in the topic's share of all views of that wiki (main interest signal; removes Wikipedia-wide traffic trends). Views chg = raw reader numbers. Per 1M wiki views = intensity of interest, comparable across languages. Confidence = trust in the direction of relative growth.

## Confidence notes
- pl (польська): HIGH, declining. Supports: solid volume (~266 views/day); 95% interval excludes zero (-15% to -6%); raw views move the same way (-19%); 10 of the last 12 months moved the same way year-over-year; spikes are only 1% of views. Largest spikes: 2025-10-14 (x2.9), 2025-10-30 (x2.5), 2025-08-19 (x2.6).
- tr (турецька): MEDIUM, no clear change. Supports: solid volume (~233 views/day); 95% interval is narrow (-10% to +10%), so any change is small. Largest spikes: 2026-04-16 (x3.5), 2026-04-09 (x2.3).
- es (іспанська): HIGH, declining. Supports: solid volume (~854 views/day); 95% interval excludes zero (-16% to -3%); raw views move the same way (-29%); 10 of the last 12 months moved the same way year-over-year; spikes are only 0% of views. Largest spikes: 2025-05-08 (x2.6).
- vi (вʼєтнамська): MEDIUM, no clear change. Supports: solid volume (~410 views/day); 95% interval is narrow (-8% to +15%), so any change is small.
- de (німецька): MEDIUM, no clear change. Supports: solid volume (~772 views/day); 95% interval is narrow (-5% to +4%), so any change is small. Largest spikes: 2025-01-06 (x2.3).

## Comparisons (difference in relative growth, percentage points)
- topic: English: vi (вʼєтнамська) vs de (німецька): +2 pp [-9, +17] -> difference not statistically clear
- topic: English: vi (вʼєтнамська) vs tr (турецька): +3 pp [-6, +13] -> difference not statistically clear
- topic: English: vi (вʼєтнамська) vs es (іспанська): +12 pp [+1, +26] -> clear difference
- topic: English: vi (вʼєтнамська) vs pl (польська): +12 pp [+2, +26] -> clear difference

## Opportunity ranking (weights size=1, growth=1, intensity=0.5; 1 = best)
1. vi (вʼєтнамська) - score 0.80 (size 0.50, growth 1.00, intensity 1.00; confidence medium)
2. es (іспанська) - score 0.60 (size 1.00, growth 0.25, intensity 0.50; confidence high)
3. de (німецька) - score 0.60 (size 0.75, growth 0.75, intensity 0.00; confidence medium)
4. tr (турецька) - score 0.35 (size 0.00, growth 0.50, intensity 0.75; confidence medium)
5. pl (польська) - score 0.15 (size 0.25, growth 0.00, intensity 0.25; confidence high)
Scores rank series within each group only (percentile ranks); change weights with --weights.

## Where readers are (approx. share of each wiki's views, 2026-08)
- pl.wikipedia: PL 87%, US 4%, DE 2%, GB 1%
- tr.wikipedia: US 31%, DE 15%, NL 5%, GB 4%, BR 4%, FR 3% | NOTE: TR is withheld from Wikimedia's country data for reader safety. This does NOT mean readers are abroad: most readers are probably in TR; the shares above only split the remaining, non-withheld traffic.
- es.wikipedia: ES 32%, MX 17%, AR 13%, CL 6%, CO 6%, US 6%
- vi.wikipedia: US 47%, SG 5%, JP 5%, BR 4%, GB 3%, IN 3% | NOTE: VN is withheld from Wikimedia's country data for reader safety. This does NOT mean readers are abroad: most readers are probably in VN; the shares above only split the remaining, non-withheld traffic.
- de.wikipedia: DE 75%, AT 8%, CH 5%, US 4%
Country data is approximate and omits countries Wikimedia withholds for privacy/safety.

## Warnings
- The period spans 2025-04-15..2025-07-15, which includes Wikimedia's bot-detection update (May-June 2025): earlier 'human' views were probably partly automated, so the drop is at least partly a measurement artifact. Relative growth reduces this effect; series flagged with a level shift there deserve extra caution.

## Files (in /Users/aklim/Library/Application Support/Claude/scratch-workspaces/7263d695-1594-4b85-9a91-4b8981276957/c8849df8-2684-489e-ad25-c2cb19bfaf45/scratch-2026-09-26-3e841e/wikipedia-interest-trends-workspace/iteration-3/eval-3-english-learning-audiences/with_skill/run-1/outputs)
- summary: summary.md
- analysis: analysis.json
- monthly data: data.csv
- trend chart: trend.png
- growth chart: growth.png
- daily diagnostic chart: daily.png
- narrative draft (edit, then run report): narrative.md

Next: edit narrative.md (write it in the user's language), then run: wt.py report "/Users/aklim/Library/Application Support/Claude/scratch-workspaces/7263d695-1594-4b85-9a91-4b8981276957/c8849df8-2684-489e-ad25-c2cb19bfaf45/scratch-2026-09-26-3e841e/wikipedia-interest-trends-workspace/iteration-3/eval-3-english-learning-audiences/with_skill/run-1/outputs"
