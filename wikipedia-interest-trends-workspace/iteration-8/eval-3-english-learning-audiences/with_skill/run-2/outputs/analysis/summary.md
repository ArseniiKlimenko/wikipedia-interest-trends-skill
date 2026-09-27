# Wikipedia interest analysis

Period 2024-09-01..2026-08-31 (24 months). Growth = last 12 months (2025-09..2026-08) vs previous 12 (2024-09..2025-08).
Traffic: agent=user (humans; known bots excluded), access=all-access; redirects mode=auto.

## Rules for your reply (`report` checks the narrative against them)
- A 95% interval that crosses 0 means "no clear change": never call it growth, a rise or a positive trend.
- Each row is a language edition of Wikipedia, not a country: write "Vietnamese-language readers", not "Vietnam" (country data are in "Where readers are").
- Relative growth is already net of the whole-wiki change: do not subtract it again or compare the two.
- Quote only numbers from this summary and signals.md (same sign); add no outside market facts without a source.

## Articles used
- English language · pl: "Język angielski" (Q1860)
- English language · tr: "İngilizce" (Q1860)
- English language · es: "Idioma inglés" (Q1860)
- English language · vi: "Tiếng Anh" (Q1860)
- English language · de: "Englische Sprache" (Q1860)

## Results

| Series | Views/mo | Per 1M wiki views | Views chg (spikes damped) | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Next 12m forecast [80%] | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| pl.wikipedia (польська) | 8,087 | 43.0 | -19% | -11% [-23%, +4%] | -3% | -10% | 2/12 | 1% | -15% [-25%, -5%] | LOW (no clear change) |
| tr.wikipedia (турецька) | 7,080 | 65.1 | -17% | -1% [-26%, +31%] | +15% | -5% | 8/12 | 0% | +0% [-40%, +51%] | LOW (no clear change) |
| es.wikipedia (іспанська) | 25,962 | 47.7 | -29% | -10% [-18%, -2%] | -5% | -10% | 2/12 | 0% | +0% [-50%, +61%] | HIGH (declining) |
| vi.wikipedia (вʼєтнамська) | 12,478 | 253.8 | -23% | +2% [-21%, +31%] | -1% | -5% | 6/12 | 0% | +0% [-19%, +36%] | LOW (no clear change) |
| de.wikipedia (німецька) | 23,477 | 33.3 | -8% | -0% [-4%, +4%] | -4% | +0% | 4/12 | 0% | +0% [-14%, +17%] | MEDIUM (no clear change) |

Whole-wiki human views, same comparison: pl -9%, tr -16%, es -21%, vi -24%, de -7%.
Reading guide: Relative growth = change in the topic's share of all views of that wiki (main interest signal; already net of the whole-wiki change above, so never subtract that change again). Views chg = change in reader numbers after dampening short spikes (values with spike days kept are in Confidence notes when they differ by 5+ pp). Per 1M wiki views = intensity of interest, comparable across languages. Confidence = trust in the direction of relative growth.

## Confidence notes
- pl.wikipedia (польська): LOW, no clear change. Supports: solid volume (~266 views/day). Concerns: 95% interval is wide (-23% to +4%). Largest spikes: 2025-10-14 (x2.9), 2025-10-30 (x2.5), 2025-08-19 (x2.6).
- tr.wikipedia (турецька): LOW, no clear change. Supports: solid volume (~233 views/day). Concerns: 95% interval is wide (-26% to +31%). Largest spikes: 2026-04-16 (x3.5), 2026-04-09 (x2.3).
- es.wikipedia (іспанська): HIGH, declining. Supports: solid volume (~854 views/day); 95% interval excludes zero (-18% to -2%); raw views move the same way (-29%); 10 of the last 12 months moved the same way year-over-year; spikes are only 0% of views. Largest spikes: 2025-05-08 (x2.6).
- vi.wikipedia (вʼєтнамська): LOW, no clear change. Supports: solid volume (~410 views/day). Concerns: 95% interval is wide (-21% to +31%).
- de.wikipedia (німецька): MEDIUM, no clear change. Supports: solid volume (~772 views/day); 95% interval is narrow (-4% to +4%), so any change is small. Largest spikes: 2025-01-06 (x2.3).

## Seasonality, forecast and regime changes (monthly share of wiki views, with up to 48 months of history)
- pl.wikipedia (польська): no reliable seasonality (the month pattern does not repeat across 4 years, p=0.23; do not describe peaks); forecast next 12 months vs last 12: -15% [80%: -25%, -5%] (model: seasonal naive + average yearly change, chosen by a rolling-origin backtest (3 origins, 48 months of history; MAE ets 0.201, snaive 0.138, snaive_drift 0.109)).
- tr.wikipedia (турецька): no reliable seasonality (the month pattern does not repeat across 4 years, p=0.89; do not describe peaks); forecast next 12 months vs last 12: +0% [80%: -40%, +51%] (model: seasonal naive (repeat last year), chosen by a rolling-origin backtest (3 origins, 48 months of history; MAE ets 0.202, snaive 0.154, snaive_drift 0.338)); regime change 2023-09: level -31%, trend -39%/yr -> -5%/yr.
- es.wikipedia (іспанська): no reliable seasonality (the month pattern does not repeat across 4 years, p=0.35; do not describe peaks); forecast next 12 months vs last 12: +0% [80%: -50%, +61%] (model: seasonal naive (repeat last year), chosen by a rolling-origin backtest (3 origins, 48 months of history; MAE ets 0.230, snaive 0.100, snaive_drift 0.552)); regime change 2023-09: level -52%, trend -38%/yr -> -15%/yr.
- vi.wikipedia (вʼєтнамська): no reliable seasonality (the month pattern does not repeat across 4 years, p=0.12; do not describe peaks); forecast next 12 months vs last 12: +0% [80%: -19%, +36%] (model: seasonal naive (repeat last year), chosen by a rolling-origin backtest (3 origins, 48 months of history; MAE ets 0.279, snaive 0.185, snaive_drift 0.202)); regime change 2025-06: level +26%, trend -18%/yr -> -14%/yr (coincides with the Wikimedia bot-detection update (May-June 2025)).
- de.wikipedia (німецька): seasonality moderate (0.63; repeats across 4 years, p=0.004): peaks Apr +7%, Jun +5%; low Aug -8%, Oct -7%; forecast next 12 months vs last 12: +0% [80%: -14%, +17%] (model: seasonal naive (repeat last year), chosen by a rolling-origin backtest (3 origins, 48 months of history; MAE ets 0.124, snaive 0.049, snaive_drift 0.162)).
Forecasts extrapolate the recent pattern; they cannot foresee news or product launches.

## Partial pooling (empirical Bayes; steadies small, noisy wikis)
- topic: English language: common trend -4%, between-series spread tau=0.04 (k=5).
  - pl.wikipedia (польська): raw -11% -> pooled -6% [-12%, +1%] (weight on own data 0.18)
  - tr.wikipedia (турецька): raw -1% -> pooled -4% [-11%, +3%] (weight on own data 0.06)
  - es.wikipedia (іспанська): raw -10% -> pooled -7% [-12%, -1%] (weight on own data 0.39)
  - vi.wikipedia (вʼєтнамська): raw +2% -> pooled -4% [-10%, +3%] (weight on own data 0.07)
  - de.wikipedia (німецька): raw -0% -> pooled -1% [-5%, +2%] (weight on own data 0.74)
Pooled values shrink noisy estimates toward the group's common trend; with tau=0 the data are consistent with one shared trend. Quote raw growth as the measurement, pooled as the robust estimate.

## Year over year (each 12-month block vs the block before it; uses history before the period)
- pl.wikipedia (польська): 2023-09..2024-08 compared with 2022-09..2023-08: relative -21%, views -24%
- pl.wikipedia (польська): 2024-09..2025-08 compared with 2023-09..2024-08: relative -14%, views -19%
- pl.wikipedia (польська): 2025-09..2026-08 compared with 2024-09..2025-08: relative -11%, views -19%
- tr.wikipedia (турецька): 2023-09..2024-08 compared with 2022-09..2023-08: relative -49%, views -49%
- tr.wikipedia (турецька): 2024-09..2025-08 compared with 2023-09..2024-08: relative -8%, views -18%
- tr.wikipedia (турецька): 2025-09..2026-08 compared with 2024-09..2025-08: relative -1%, views -17%
- es.wikipedia (іспанська): 2023-09..2024-08 compared with 2022-09..2023-08: relative -66%, views -67%
- es.wikipedia (іспанська): 2024-09..2025-08 compared with 2023-09..2024-08: relative -15%, views -30%
- es.wikipedia (іспанська): 2025-09..2026-08 compared with 2024-09..2025-08: relative -10%, views -29%
- vi.wikipedia (вʼєтнамська): 2023-09..2024-08 compared with 2022-09..2023-08: relative -17%, views -10%
- vi.wikipedia (вʼєтнамська): 2024-09..2025-08 compared with 2023-09..2024-08: relative -15%, views -24%
- vi.wikipedia (вʼєтнамська): 2025-09..2026-08 compared with 2024-09..2025-08: relative +2%, views -23%
- de.wikipedia (німецька): 2023-09..2024-08 compared with 2022-09..2023-08: relative -19%, views -19%
- de.wikipedia (німецька): 2024-09..2025-08 compared with 2023-09..2024-08: relative -12%, views -17%
- de.wikipedia (німецька): 2025-09..2026-08 compared with 2024-09..2025-08: relative -0%, views -8%
The last line is the same comparison as the headline relative growth.

## Comparisons (difference in relative growth, percentage points)
- topic: English language: vi.wikipedia (вʼєтнамська) vs de.wikipedia (німецька): +2 pp [-21, +32] -> difference not statistically clear
- topic: English language: vi.wikipedia (вʼєтнамська) vs tr.wikipedia (турецька): +3 pp [-24, +39] -> difference not statistically clear
- topic: English language: vi.wikipedia (вʼєтнамська) vs es.wikipedia (іспанська): +12 pp [-17, +52] -> difference not statistically clear
- topic: English language: vi.wikipedia (вʼєтнамська) vs pl.wikipedia (польська): +12 pp [-21, +63] -> difference not statistically clear

## Opportunity ranking (weights size=1, growth=1, intensity=0.5; 1 = best)
1. vi.wikipedia (вʼєтнамська) - score 0.70 (size 0.50, growth 0.75, intensity 1.00; confidence low)
2. de.wikipedia (німецька) - score 0.70 (size 0.75, growth 1.00, intensity 0.00; confidence medium)
3. es.wikipedia (іспанська) - score 0.50 (size 1.00, growth 0.00, intensity 0.50; confidence high)
4. tr.wikipedia (турецька) - score 0.35 (size 0.00, growth 0.50, intensity 0.75; confidence low)
5. pl.wikipedia (польська) - score 0.25 (size 0.25, growth 0.25, intensity 0.25; confidence low)
Scores rank series within each group only (percentile ranks); change weights with --weights. The growth component uses the partially pooled growth (see above).

## Where readers are (approx. share of each wiki's views, 2026-08)
- pl.wikipedia: PL 87%, US 4%, DE 2%, GB 1%
- tr.wikipedia: TR is withheld from Wikimedia's country data for reader safety, so the country split is not usable here. Most readers are presumably in TR; do not describe this audience as diaspora.
- es.wikipedia: ES 32%, MX 17%, AR 13%, CL 6%, CO 6%, US 6%
- vi.wikipedia: VN is withheld from Wikimedia's country data for reader safety, so the country split is not usable here. Most readers are presumably in VN; do not describe this audience as diaspora.
- de.wikipedia: DE 75%, AT 8%, CH 5%, US 4%
Country data is approximate and omits countries Wikimedia withholds for privacy/safety.

## Suggestions (consider before concluding)
- pl.wikipedia (польська) has LOW confidence; a 36-month run (--months 36) shows whether the direction persists.
- tr.wikipedia (турецька) has LOW confidence; a 36-month run (--months 36) shows whether the direction persists.
- vi.wikipedia (вʼєтнамська) has LOW confidence; a 36-month run (--months 36) shows whether the direction persists.
- Check demand outside Wikipedia before recommending: wt.py signals "/Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-8/eval-3-english-learning-audiences/with_skill/run-2/outputs/analysis" --trends --keyword pl="<local phrase>" --keyword tr="<local phrase>" --keyword es="<local phrase>" (Google Trends for the same topic per country via its unofficial endpoint + App Store competition); then re-run report.

## Warnings
- The period includes Wikimedia's bot-detection update (May-June 2025), which reclassified part of the earlier 'human' views as automated. Measured step of whole-wiki human views across it (Jul-Aug vs Mar-Apr 2025, seasonally adjusted with 2024 where available): pl -5%, tr +9%, es +4%, vi -21%, de -2%. Relative growth nets out a step that a topic shares with its wiki. Series whose own step differs by 25% or more: vi.wikipedia (вʼєтнамська) (see Confidence notes).

## Files (in /Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-8/eval-3-english-learning-audiences/with_skill/run-2/outputs/analysis)
- summary: summary.md
- analysis: analysis.json
- monthly data: data.csv
- trend chart: trend.png
- growth chart: growth.png
- daily diagnostic chart: daily.png
- narrative draft (edit, then run report): narrative.md

Next: edit narrative.md (write it in the user's language), then run: wt.py report "/Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-8/eval-3-english-learning-audiences/with_skill/run-2/outputs/analysis"
