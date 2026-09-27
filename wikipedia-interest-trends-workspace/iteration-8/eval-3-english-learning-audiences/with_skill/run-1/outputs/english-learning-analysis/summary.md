# Wikipedia interest analysis

Period 2024-09-01..2026-08-31 (24 months). Growth = last 12 months (2025-09..2026-08) vs previous 12 (2024-09..2025-08).
Traffic: agent=user (humans; known bots excluded), access=all-access; redirects mode=auto.

## Rules for your reply (`report` checks the narrative against them)
- A 95% interval that crosses 0 means "no clear change": never call it growth, a rise or a positive trend.
- Each row is a language edition of Wikipedia, not a country: write "Vietnamese-language readers", not "Vietnam" (country data are in "Where readers are").
- Relative growth is already net of the whole-wiki change: do not subtract it again or compare the two.
- Quote only numbers from this summary and signals.md (same sign); add no outside market facts without a source.

## Articles used
- English language learning · pl: "IELTS" (Q490396) [70% of views, rel. growth -15%]; "TOEFL" (Q487425) [30% of views, rel. growth -47%]
- English language learning · tr: "IELTS" (Q490396) [62% of views, rel. growth +23%]; "TOEFL" (Q487425) [38% of views, rel. growth -12%]
- English language learning · es: "IELTS" (Q490396) [40% of views, rel. growth -36%]; "TOEFL" (Q487425) [60% of views, rel. growth -49%]
- English language learning · vi: "IELTS" (Q490396) [85% of views, rel. growth -19%]; "TOEFL" (Q487425) [15% of views, rel. growth -45%]
- English language learning · de: "International English Language Testing System" (Q490396) [34% of views, rel. growth -37%]; "TOEFL" (Q487425) [66% of views, rel. growth -40%]

## Results

| Series | Views/mo | Per 1M wiki views | Views chg (spikes damped) | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Next 12m forecast [80%] | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| pl.wikipedia (польська) | 412 | 2.2 | -33% | -27% [-36%, -17%] | -25% | -29% | 1/12 | 0% | -22% [-40%, +7%] | MEDIUM (declining) |
| tr.wikipedia (турецька) | 1,745 | 16.0 | -11% | +7% [-62%, +198%] | -43% | -3% | 6/12 | 1% | -49% [-67%, -14%] | LOW (no clear change) |
| es.wikipedia (іспанська) | 1,128 | 2.1 | -56% | -44% [-54%, -33%] | -39% | -46% | 0/12 | 0% | -26% [-48%, +11%] | HIGH (declining) |
| vi.wikipedia (вʼєтнамська) | 1,767 | 35.9 | -43% | -24% [-35%, -13%] | -30% | -19% | 2/12 | 1% | -23% [-40%, +6%] | HIGH (declining) |
| de.wikipedia (німецька) | 896 | 1.3 | -43% | -39% [-45%, -33%] | -39% | -37% | 0/12 | 0% | -8% [-31%, +24%] | MEDIUM (declining) |

Whole-wiki human views, same comparison: pl -9%, tr -16%, es -21%, vi -24%, de -7%.
Reading guide: Relative growth = change in the topic's share of all views of that wiki (main interest signal; already net of the whole-wiki change above, so never subtract that change again). Views chg = change in reader numbers after dampening short spikes (values with spike days kept are in Confidence notes when they differ by 5+ pp). Per 1M wiki views = intensity of interest, comparable across languages. Confidence = trust in the direction of relative growth.

## Confidence notes
- pl.wikipedia (польська): MEDIUM, declining. Supports: 95% interval excludes zero (-36% to -17%); raw views move the same way (-33%); 11 of the last 12 months moved the same way year-over-year; spikes are only 0% of views. Concerns: low volume (~14 views/day). Largest spikes: 2024-12-04 (x2.3), 2025-03-10 (x2.1).
- tr.wikipedia (турецька): LOW, no clear change. Supports: solid volume (~57 views/day). Concerns: 95% interval is wide (-62% to +198%). Largest spikes: 2025-02-08 (x2.6), 2026-05-17 (x3.1), 2025-02-09 (x2.1).
- es.wikipedia (іспанська): HIGH, declining. Supports: solid volume (~37 views/day); 95% interval excludes zero (-54% to -33%); raw views move the same way (-56%); 12 of the last 12 months moved the same way year-over-year; spikes are only 0% of views.
- vi.wikipedia (вʼєтнамська): HIGH, declining. Supports: solid volume (~58 views/day); 95% interval excludes zero (-35% to -13%); raw views move the same way (-43%); 10 of the last 12 months moved the same way year-over-year; spikes are only 1% of views. Concerns: around the May-June 2025 bot-detection update this series moved +32% relative to its wiki, against the measured direction. Largest spikes: 2025-05-12 (x2.3), 2026-06-02 (x2.9), 2026-07-09 (x2.4).
- de.wikipedia (німецька): MEDIUM, declining. Supports: solid volume (~29 views/day); 95% interval excludes zero (-45% to -33%); raw views move the same way (-43%); 12 of the last 12 months moved the same way year-over-year; spikes are only 0% of views. Concerns: around the May-June 2025 bot-detection update this series moved -31% relative to its wiki (seasonally adjusted); part of the decline may be a measurement artifact. Largest spikes: 2025-06-02 (x3.1).

## Seasonality, forecast and regime changes (monthly share of wiki views, with up to 48 months of history)
- pl.wikipedia (польська): seasonality moderate (0.39; repeats across 4 years, p=0.037): peaks Sep +18%, Jan +13%; low May -21%, Aug -14%; forecast next 12 months vs last 12: -22% [80%: -40%, +7%] (model: seasonal naive + average yearly change, chosen by a rolling-origin backtest (3 origins, 48 months of history; MAE ets 0.232, snaive 0.347, snaive_drift 0.184)).
- tr.wikipedia (турецька): seasonality weak (0.34; repeats across 4 years, p=0.029): peaks Jul +39%, Aug +35%; low May -31%, Apr -29%; forecast next 12 months vs last 12: -49% [80%: -67%, -14%] (model: ETS(A,Ad,A) on log, chosen by a rolling-origin backtest (3 origins, 48 months of history; MAE ets 0.335, snaive 0.487, snaive_drift 0.584)); regime change 2025-06: level +129%, trend -9%/yr -> -60%/yr (coincides with the Wikimedia bot-detection update (May-June 2025)).
- es.wikipedia (іспанська): no reliable seasonality (the month pattern does not repeat across 4 years, p=0.12; do not describe peaks); forecast next 12 months vs last 12: -26% [80%: -48%, +11%] (model: ETS(A,Ad,A) on log, chosen by a rolling-origin backtest (3 origins, 48 months of history; MAE ets 0.232, snaive 0.510, snaive_drift 0.269)); regime change 2024-11: level +17%, trend -22%/yr -> -46%/yr.
- vi.wikipedia (вʼєтнамська): seasonality moderate (0.63; repeats across 4 years, p=0.004): peaks Jul +41%, Jun +30%; low Jan -19%, May -13%; forecast next 12 months vs last 12: -23% [80%: -40%, +6%] (model: seasonal naive + average yearly change, chosen by a rolling-origin backtest (3 origins, 48 months of history; MAE ets 0.195, snaive 0.282, snaive_drift 0.182)).
- de.wikipedia (німецька): no reliable seasonality (the month pattern does not repeat across 4 years, p=0.05; do not describe peaks); forecast next 12 months vs last 12: -8% [80%: -31%, +24%] (model: ETS(A,Ad,A) on log, chosen by a rolling-origin backtest (3 origins, 48 months of history; MAE ets 0.232, snaive 0.409, snaive_drift 0.336)); regime change 2025-04: level -13%, trend -3%/yr -> -37%/yr (coincides with the Wikimedia bot-detection update (May-June 2025)).
Forecasts extrapolate the recent pattern; they cannot foresee news or product launches.

## Partial pooling (empirical Bayes; steadies small, noisy wikis)
- topic: English language learning: common trend -33%, between-series spread tau=0.11 (k=5).
  - pl.wikipedia (польська): raw -27% -> pooled -29% [-36%, -20%] (weight on own data 0.75)
  - tr.wikipedia (турецька): raw +7% -> pooled -32% [-45%, -15%] (weight on own data 0.04)
  - es.wikipedia (іспанська): raw -44% -> pooled -40% [-48%, -31%] (weight on own data 0.60)
  - vi.wikipedia (вʼєтнамська): raw -24% -> pooled -27% [-36%, -18%] (weight on own data 0.70)
  - de.wikipedia (німецька): raw -39% -> pooled -38% [-43%, -32%] (weight on own data 0.83)
Pooled values shrink noisy estimates toward the group's common trend; with tau=0 the data are consistent with one shared trend. Quote raw growth as the measurement, pooled as the robust estimate.

## Year over year (each 12-month block vs the block before it; uses history before the period)
- pl.wikipedia (польська): 2023-09..2024-08 compared with 2022-09..2023-08: relative -19%, views -22%
- pl.wikipedia (польська): 2024-09..2025-08 compared with 2023-09..2024-08: relative -20%, views -24%
- pl.wikipedia (польська): 2025-09..2026-08 compared with 2024-09..2025-08: relative -27%, views -33%
- tr.wikipedia (турецька): 2023-09..2024-08 compared with 2022-09..2023-08: relative -20%, views -22%
- tr.wikipedia (турецька): 2024-09..2025-08 compared with 2023-09..2024-08: relative +22%, views +7%
- tr.wikipedia (турецька): 2025-09..2026-08 compared with 2024-09..2025-08: relative +7%, views -11%
- es.wikipedia (іспанська): 2023-09..2024-08 compared with 2022-09..2023-08: relative -27%, views -30%
- es.wikipedia (іспанська): 2024-09..2025-08 compared with 2023-09..2024-08: relative -14%, views -30%
- es.wikipedia (іспанська): 2025-09..2026-08 compared with 2024-09..2025-08: relative -44%, views -56%
- vi.wikipedia (вʼєтнамська): 2023-09..2024-08 compared with 2022-09..2023-08: relative -21%, views -14%
- vi.wikipedia (вʼєтнамська): 2024-09..2025-08 compared with 2023-09..2024-08: relative -23%, views -31%
- vi.wikipedia (вʼєтнамська): 2025-09..2026-08 compared with 2024-09..2025-08: relative -24%, views -43%
- de.wikipedia (німецька): 2023-09..2024-08 compared with 2022-09..2023-08: relative -7%, views -7%
- de.wikipedia (німецька): 2024-09..2025-08 compared with 2023-09..2024-08: relative -5%, views -11%
- de.wikipedia (німецька): 2025-09..2026-08 compared with 2024-09..2025-08: relative -39%, views -43%
The last line is the same comparison as the headline relative growth.

## Comparisons (difference in relative growth, percentage points)
- topic: English language learning: tr.wikipedia (турецька) vs vi.wikipedia (вʼєтнамська): +31 pp [-30, +177] -> difference not statistically clear
- topic: English language learning: tr.wikipedia (турецька) vs pl.wikipedia (польська): +33 pp [-38, +247] -> difference not statistically clear
- topic: English language learning: tr.wikipedia (турецька) vs de.wikipedia (німецька): +46 pp [-23, +239] -> difference not statistically clear
- topic: English language learning: tr.wikipedia (турецька) vs es.wikipedia (іспанська): +51 pp [-19, +259] -> difference not statistically clear

## Opportunity ranking (weights size=1, growth=1, intensity=0.5; 1 = best)
1. vi.wikipedia (вʼєтнамська) - score 1.00 (size 1.00, growth 1.00, intensity 1.00; confidence high)
2. tr.wikipedia (турецька) - score 0.65 (size 0.75, growth 0.50, intensity 0.75; confidence low)
3. pl.wikipedia (польська) - score 0.40 (size 0.00, growth 0.75, intensity 0.50; confidence medium)
4. es.wikipedia (іспанська) - score 0.25 (size 0.50, growth 0.00, intensity 0.25; confidence high)
5. de.wikipedia (німецька) - score 0.20 (size 0.25, growth 0.25, intensity 0.00; confidence medium)
Scores rank series within each group only (percentile ranks); change weights with --weights. The growth component uses the partially pooled growth (see above).

## Where readers are (approx. share of each wiki's views, 2026-08)
- pl.wikipedia: PL 87%, US 4%, DE 2%, GB 1%
- tr.wikipedia: TR is withheld from Wikimedia's country data for reader safety, so the country split is not usable here. Most readers are presumably in TR; do not describe this audience as diaspora.
- es.wikipedia: ES 32%, MX 17%, AR 13%, CL 6%, CO 6%, US 6%
- vi.wikipedia: VN is withheld from Wikimedia's country data for reader safety, so the country split is not usable here. Most readers are presumably in VN; do not describe this audience as diaspora.
- de.wikipedia: DE 75%, AT 8%, CH 5%, US 4%
Country data is approximate and omits countries Wikimedia withholds for privacy/safety.

## Suggestions (consider before concluding)
- tr.wikipedia (турецька): the result flips without "IELTS"; report it as driven by that article or split the basket into separate topics.
- tr.wikipedia (турецька) has LOW confidence; a 36-month run (--months 36) shows whether the direction persists.
- Check demand outside Wikipedia before recommending: wt.py signals "/Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-8/eval-3-english-learning-audiences/with_skill/run-1/outputs/english-learning-analysis" --trends --keyword pl="<local phrase>" --keyword tr="<local phrase>" --keyword es="<local phrase>" (Google Trends for the same topic per country via its unofficial endpoint + App Store competition); then re-run report.

## Warnings
- The period includes Wikimedia's bot-detection update (May-June 2025), which reclassified part of the earlier 'human' views as automated. Measured step of whole-wiki human views across it (Jul-Aug vs Mar-Apr 2025, seasonally adjusted with 2024 where available): pl -5%, tr +9%, es +4%, vi -21%, de -2%. Relative growth nets out a step that a topic shares with its wiki. Series whose own step differs by 25% or more: tr.wikipedia (турецька); vi.wikipedia (вʼєтнамська); de.wikipedia (німецька) (see Confidence notes).

## Files (in /Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-8/eval-3-english-learning-audiences/with_skill/run-1/outputs/english-learning-analysis)
- summary: summary.md
- analysis: analysis.json
- monthly data: data.csv
- trend chart: trend.png
- growth chart: growth.png
- daily diagnostic chart: daily.png
- narrative draft (edit, then run report): narrative.md

Next: edit narrative.md (write it in the user's language), then run: wt.py report "/Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-8/eval-3-english-learning-audiences/with_skill/run-1/outputs/english-learning-analysis"
