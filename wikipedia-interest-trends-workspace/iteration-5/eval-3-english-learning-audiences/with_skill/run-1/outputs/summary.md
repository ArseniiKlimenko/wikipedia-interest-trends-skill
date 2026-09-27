# Wikipedia interest analysis

Period 2024-09-01..2026-08-31 (24 months). Growth = last 12 months (2025-09..2026-08) vs previous 12 (2024-09..2025-08).
Traffic: agent=user (humans; known bots excluded), access=all-access; redirects mode=auto.

## Articles used
- English Learning Exams · pl: "TOEFL" (Q487425) [30% of views, rel. growth -47%]; "IELTS" (Q490396) [70% of views, rel. growth -15%]
- English Learning Exams · tr: "TOEFL" (Q487425) [38% of views, rel. growth -12%]; "IELTS" (Q490396) [62% of views, rel. growth +23%]
- English Learning Exams · es: "TOEFL" (Q487425) [60% of views, rel. growth -49%]; "IELTS" (Q490396) [40% of views, rel. growth -36%]
- English Learning Exams · vi: "TOEFL" (Q487425) [15% of views, rel. growth -45%]; "IELTS" (Q490396) [85% of views, rel. growth -19%]
- English Learning Exams · de: "TOEFL" (Q487425) [66% of views, rel. growth -40%]; "International English Language Testing System" (Q490396) [34% of views, rel. growth -37%]

## Results

| Series | Views/mo | Per 1M wiki views | Views chg | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| pl (польська) | 412 | 2.2 | -33% | -27% [-36%, -15%] | -25% | -29% | 1/12 | 0% | MEDIUM (declining) |
| tr (турецька) | 1,745 | 16.0 | -11% | +7% [-20%, +43%] | -43% | -3% | 6/12 | 1% | LOW (no clear change) |
| es (іспанська) | 1,128 | 2.1 | -56% | -44% [-54%, -34%] | -39% | -46% | 0/12 | 0% | HIGH (declining) |
| vi (вʼєтнамська) | 1,767 | 35.9 | -43% | -24% [-36%, -13%] | -30% | -19% | 2/12 | 1% | HIGH (declining) |
| de (німецька) | 896 | 1.3 | -43% | -39% [-46%, -32%] | -39% | -37% | 0/12 | 0% | HIGH (declining) |

Whole-wiki human views, same comparison: pl -9%, tr -16%, es -21%, vi -24%, de -7%.
Reading guide: Relative growth = change in the topic's share of all views of that wiki (main interest signal; already net of the whole-wiki change above, so never subtract that change again). Views chg = raw reader numbers. Per 1M wiki views = intensity of interest, comparable across languages. Confidence = trust in the direction of relative growth.

## Confidence notes
- pl (польська): MEDIUM, declining. Supports: 95% interval excludes zero (-36% to -15%); raw views move the same way (-33%); 11 of the last 12 months moved the same way year-over-year; spikes are only 0% of views. Concerns: low volume (~14 views/day). Largest spikes: 2024-12-04 (x2.3), 2025-03-10 (x2.1).
- tr (турецька): LOW, no clear change. Supports: solid volume (~57 views/day). Concerns: 95% interval is wide (-20% to +43%). Largest spikes: 2025-02-08 (x2.6), 2026-05-17 (x3.1), 2025-02-09 (x2.1).
- es (іспанська): HIGH, declining. Supports: solid volume (~37 views/day); 95% interval excludes zero (-54% to -34%); raw views move the same way (-56%); 12 of the last 12 months moved the same way year-over-year; spikes are only 0% of views.
- vi (вʼєтнамська): HIGH, declining. Supports: solid volume (~58 views/day); 95% interval excludes zero (-36% to -13%); raw views move the same way (-43%); 10 of the last 12 months moved the same way year-over-year; spikes are only 1% of views. Largest spikes: 2025-05-12 (x2.3), 2026-06-02 (x2.9), 2026-07-09 (x2.4).
- de (німецька): HIGH, declining. Supports: solid volume (~29 views/day); 95% interval excludes zero (-46% to -32%); raw views move the same way (-43%); 12 of the last 12 months moved the same way year-over-year; spikes are only 0% of views. Largest spikes: 2025-06-02 (x3.1).

## Comparisons (difference in relative growth, percentage points)
- topic: English Learning Exams: tr (турецька) vs vi (вʼєтнамська): +31 pp [+10, +62] -> clear difference
- topic: English Learning Exams: tr (турецька) vs pl (польська): +33 pp [+6, +69] -> clear difference
- topic: English Learning Exams: tr (турецька) vs de (німецька): +46 pp [+18, +82] -> clear difference
- topic: English Learning Exams: tr (турецька) vs es (іспанська): +51 pp [+24, +87] -> clear difference

## Opportunity ranking (weights size=1, growth=1, intensity=0.5; 1 = best)
1. vi (вʼєтнамська) - score 0.90 (size 1.00, growth 0.75, intensity 1.00; confidence high)
2. tr (турецька) - score 0.85 (size 0.75, growth 1.00, intensity 0.75; confidence low)
3. pl (польська) - score 0.30 (size 0.00, growth 0.50, intensity 0.50; confidence medium)
4. es (іспанська) - score 0.25 (size 0.50, growth 0.00, intensity 0.25; confidence high)
5. de (німецька) - score 0.20 (size 0.25, growth 0.25, intensity 0.00; confidence high)
Scores rank series within each group only (percentile ranks); change weights with --weights.

## Where readers are (approx. share of each wiki's views, 2026-08)
- pl.wikipedia: PL 87%, US 4%, DE 2%, GB 1%
- tr.wikipedia: TR is withheld from Wikimedia's country data for reader safety, so the country split is not usable here. Most readers are presumably in TR; do not describe this audience as diaspora.
- es.wikipedia: ES 32%, MX 17%, AR 13%, CL 6%, CO 6%, US 6%
- vi.wikipedia: VN is withheld from Wikimedia's country data for reader safety, so the country split is not usable here. Most readers are presumably in VN; do not describe this audience as diaspora.
- de.wikipedia: DE 75%, AT 8%, CH 5%, US 4%
Country data is approximate and omits countries Wikimedia withholds for privacy/safety.

## Suggestions (consider before concluding)
- tr (турецька): the result flips without "IELTS"; report it as driven by that article or split the basket into separate topics.
- tr (турецька) has LOW confidence; a 36-month run (--months 36) shows whether the direction persists.

## Warnings
- The period spans 2025-04-15..2025-07-15, which includes Wikimedia's bot-detection update (May-June 2025): earlier 'human' views were probably partly automated, so the drop is at least partly a measurement artifact. Relative growth reduces this effect; series flagged with a level shift there deserve extra caution.

## Files (in /Users/aklim/Library/Application Support/Claude/scratch-workspaces/7263d695-1594-4b85-9a91-4b8981276957/c8849df8-2684-489e-ad25-c2cb19bfaf45/scratch-2026-09-26-3e841e/wikipedia-interest-trends-workspace/iteration-5/eval-3-english-learning-audiences/with_skill/run-1/outputs)
- summary: summary.md
- analysis: analysis.json
- monthly data: data.csv
- trend chart: trend.png
- growth chart: growth.png
- daily diagnostic chart: daily.png
- narrative draft (edit, then run report): narrative.md

Next: edit narrative.md (write it in the user's language), then run: wt.py report "/Users/aklim/Library/Application Support/Claude/scratch-workspaces/7263d695-1594-4b85-9a91-4b8981276957/c8849df8-2684-489e-ad25-c2cb19bfaf45/scratch-2026-09-26-3e841e/wikipedia-interest-trends-workspace/iteration-5/eval-3-english-learning-audiences/with_skill/run-1/outputs"
