# Methodology: what every number means

Read this when you need to explain a metric, justify a confidence grade, or answer "how was
this calculated?". Everything below is implemented in `scripts/wikitrends/` and is deterministic
(fixed bootstrap seed): the same inputs always give the same numbers.

## Contents
1. Data source and cleaning
2. Growth metrics
3. Confidence grade
4. Comparisons and ranking
5. Context: geography, known data breaks
6. Claim check
7. How to phrase results for a founder
8. Seasonality, forecast, regime changes, partial pooling

## 1. Data source and cleaning
- **Source**: Wikimedia Analytics API, `per-article` (daily views of each article) and `aggregate`
  (daily views of the whole language edition). Data exists from July 2015. License CC0.
- **Agent `user`** (default): human traffic. Self-identified crawlers (`spider`) and heuristically
  detected bots (`automated`) are excluded; undetected bots remain possible.
- **Periods** are whole calendar months ending with the last complete month. The tool also loads
  history before the period (48 months in total, from July 2015 at the earliest) for the models,
  year-over-year blocks, the bot-update step and the seasonal check of level shifts; growth itself
  uses only the requested period.
- **Missing days** are zeros (the API omits zero-view days).
- **Redirects** (`--redirects auto`, the default): when an article shows a sudden level change or
  appears mid-period, views of its redirect titles are added (a renamed article keeps its old
  views under the old title). `all` always adds them (max 20 per article); `none` never does.
- **Spike dampening**: a day is a spike if it is more than 5 robust SDs above the 29-day rolling
  median *and* at least 2x that median. It is replaced by the median. Growth uses the dampened
  series; raw totals are kept for audience size. `Spikes` = share of all views that were spike
  excess. Sustained changes are not removed (they move the rolling median).

## 2. Growth metrics
| Metric | Definition |
|---|---|
| Views/mo | Average monthly raw views in the recent 12 months (audience size) |
| Per 1M wiki views | Topic views / all views of that wiki x 1,000,000 (intensity; comparable across languages) |
| Views chg | Spike-dampened views, recent 12 months vs previous 12 (the summary adds the with-spikes values when they differ by 5+ pp) |
| **Relative growth** | Change in the topic's *share* of all wiki views, recent 12 vs previous 12. Main signal. |
| 95% CI | Union of (a) a paired circular block bootstrap: 2,000 resamples of 28-day blocks where day *i* of the recent year is drawn together with day *i* of the previous year (same season), numerator and denominator together; and (b) a t-interval on the 12 monthly log-ratios (same calendar month, recent vs previous) whose standard error is inflated by sqrt((1+r)/(1-r)) for their lag-1 autocorrelation r (clipped to 0..0.7) |
| Last 6m YoY | Share in the last 6 months vs the same 6 months a year earlier (momentum) |
| Trend/yr | Theil-Sen slope of log monthly share over the whole period, as %/year |
| Months up | How many of the last 12 months beat the same month a year earlier (share) |
| Year over year | Each 12-month block vs the previous one, over the period plus its history |

With fewer than 24 months, growth compares the last half with the first half; seasonality is not
controlled, so confidence is capped at LOW.

**Calibration of the interval** (synthetic series without any real change, 200 runs each, 24
months; the share of runs whose interval excluded 0, nominal 5%): Poisson noise 2.5%; daily AR(1)
rho=0.9 7%; monthly level shocks 4%; seasonality + AR(1) 8%; very persistent drift (daily rho=0.99)
19.5%. The earlier unpaired bootstrap gave 6.5%, 16%, 11%, 0% (but 48 pp wide) and 55%. Power: a
steady +20%/year trend under daily AR(1) rho=0.9 noise is detected in 66% of runs, and in 100% with
Poisson noise at 30 views/day. Slow drifts lasting many months are real changes in attention but not
necessarily trends; the year-over-year blocks and the confidence notes help tell them apart.

**Why relative growth?** Wikipedia's total human traffic moves for reasons unrelated to any topic
(AI answers in search, bot reclassification, a shift of readers between language editions, such as
Ukrainian readers moving from ru to uk after 2022). Dividing by the whole-wiki total isolates
interest in the topic. The summary always shows the whole-wiki change too, so you can explain
"raw views fell 20% but the topic gained share".

## 3. Confidence grade (trust in the direction of relative growth)
Direction: **up** if the 95% CI is above 0, **down** if below 0, **no clear change** otherwise.

For up/down, each failed check counts once (and the period being shorter than 24 months forces LOW):
1. low volume (< 20 views/day in the recent year)
2. raw views move the other way
3. fewer than 8 of the last 12 months agree year-over-year
4. spikes >= 25% of views
5. the direction flips when spike days are kept
6. the whole-period monthly trend points the other way
7. one article in the basket drives the result (removing it flips the sign)
8. across the May-June 2025 bot-detection update the series' share moved by 25%+ in the same
   direction as the measured change (see §5)

Grade: 0 failures = **HIGH**, 1-2 = **MEDIUM**, 3+ = **LOW**. Severe problems force **LOW**: very
low volume (< 5/day), a non-seasonal level shift (x3 jump in 8-week medians that does not repeat a
year earlier or later), or an article that appears mid-period.

For "no clear change": **MEDIUM** if the interval is narrow (width <= 25 pp) so any change is small,
otherwise **LOW**.

Level shifts at a known data break carry an explanation, and the summary reports the trend after
the shift so you can see what happened since.

## 4. Comparisons and ranking
- **Groups**: languages within each topic when several languages are requested; otherwise topics
  within the one language.
- **Comparison**: the leader (highest relative growth) against each other series. Difference in
  percentage points with a 95% interval: the union of the paired bootstrap (all series of one
  analysis use the same resampled days, so shocks they share, like holidays or the wiki total,
  cancel; resamples undefined for either series are dropped as pairs) and a t-interval on the
  monthly log-ratio differences with the same autocorrelation inflation. "Clear" if the interval is
  above zero.
- **Ranking**: within each group, percentile ranks (0 = worst, 1 = best) of size (Views/mo),
  growth (relative growth) and intensity (per 1M), combined as a weighted mean
  (`--weights`, default size=1, growth=1, intensity=0.5). It is a transparent heuristic for
  ordering candidates, not a forecast. Always show confidence next to rank.

## 5. Context
- **Where readers are**: Wikimedia's `top-by-country` data for the last month of the period. Only
  approximate, rounded buckets are published, and some countries are withheld for reader
  privacy/safety (Turkey and Vietnam, for example, do not appear). If a wiki's home country is
  missing, the shares describe diaspora and other traffic only.
- **Known data break**: in May-June 2025 Wikimedia updated bot detection and reclassified part of
  the traffic counted as human. The tool measures the step instead of assuming it: views in
  Jul-Aug 2025 vs Mar-Apr 2025, divided by the same ratio a year earlier (seasonal adjustment), for
  each wiki total (shown in the warning) and for each series' share of its wiki. Relative growth
  already removes a step that a topic shares with its wiki; a series is flagged only when its own
  share moved by 25% or more across the update (check 8 above). Articles that bots targeted are the
  typical case.

## 6. Claim check
`report` splits narrative.md into sentences (and ';' parts) and finds which series each one names
(series name, `xx.wikipedia`, `(xx)`, the language name in English or Ukrainian). Then:
- **Errors** (exit code 1): a percentage that matches no computed value *of the named series*
  (tolerance about 1 pp; 80/95% next to interval words and 100 next to "index" are allowed); a
  flipped sign; an unsigned number whose direction word ("grew", "зростання") contradicts the value;
  a growth/positive word for a series whose interval crosses or is below zero (negations such as
  "no clear growth" are recognised), or a decline word for a growing one; a confidence level that
  differs from the grade.
- **Warnings**: a country name used for a language edition without reader/geo context; plain
  numbers (>= 100) or multipliers ("2.5x") that are not in the analysis or signals (outside facts);
  a sentence comparing relative growth with the whole-wiki change; Russian letters/words in a
  Ukrainian text or CJK characters; the draft left unedited.
It cannot judge reasoning or facts that carry no number; read the text once more yourself.

## 7. Phrasing for a founder
- "Interest is growing": only with a CI above zero, and always with the confidence grade.
- "Interest is stable": CI crosses zero and is narrow.
- "We can't tell": CI crosses zero and is wide, or the grade is LOW.
- Translate relative growth: "the topic's share of everything people read on Polish Wikipedia
  rose 15% (95% range +9% to +21%)".
- Name the proxy: "measured through the articles X and Y".
- End with the decision: what to validate next and with which signal.

## 8. Seasonality, forecast, regime changes, partial pooling
All four work on the **monthly share** (dampened topic views / all wiki views) over the period plus
its history (up to 48 months), in logs, so effects are multiplicative. Seasonality and the forecast
need at least 36 months: with 24, noise alone produced "moderate" seasonality in 84-88% of
synthetic series and no backtest could run.

**Seasonality** (`models.seasonal_decompose`): iterated 2x12 centred moving-average trend plus
per-calendar-month median of the detrended values (robust to one odd year). `strength` =
1 - var(remainder) / var(seasonal + remainder), from 0 (none) to 1 (pure seasonality); >= 0.64
is reported as strong, >= 0.36 as moderate, but only if the pattern repeats from year to year:
the detrended series is cut into 12-month profiles, the statistic is their mean pairwise
correlation, and the null distribution rotates each year's profile by a random number of months
(999 draws). With p >= 0.05 the summary says "no reliable seasonality". On synthetic series
without seasonality this reports seasonality in 2-6% of runs (36 and 48 months); a +-20% seasonal
swing is found in 80% (36 months) and 99% (48 months). Peak/low months are shown as % versus an
average month.

**Forecast** (`models.forecast`): three candidates are backtested with 6-month forecasts from up
to three origins (rolling origin), and the one with the lowest mean absolute error is used:
1. ETS(A,Ad,A): Holt-Winters with a damped trend, parameters by grid search on one-step errors;
2. seasonal naive: next year repeats the last year;
3. seasonal naive + drift: plus the average year-over-year change.
The 80% range comes from 2,000 simulated paths (bootstrapped one-step errors for ETS; for the
naive methods one yearly shock per path plus smaller monthly noise). "Next 12 months vs last 12"
compares summed shares. `skill` = 1 - MAE(ETS)/MAE(seasonal naive): > 0 means the smoothing model
beats "same as last year". Every origin trains on at least 24 months, so series with fewer than 36
months get no forecast. Synthetic check (AR(1) noise + seasonality, 200 runs): the 80% range for
"next 12 vs last 12" covered the truth in 89% of runs at 36 and 48 months (slightly conservative).
When the range lies entirely on the other side of zero from a measured direction, the summary
notes the conflict and the draft does not present the forecast as the expected outcome.

**Regime changes** (`models.changepoints`): PELT with a piecewise-linear cost on the seasonally
adjusted log share, minimum segment 6 months, penalty 6·log(n)·σ², where σ comes from second
differences and is inflated by the residual lag-1 autocorrelation. Calibration on synthetic data:
about 3% false breaks on trend-only series with AR(1) noise; ~97% detection of a 40% level step,
~85% of a trend reversal. Breaks with both a level jump and a trend change under 15% are dropped.
Breaks inside May-July 2025 are labelled as coinciding with the bot-detection update.

**Partial pooling** (`models.partial_pool`): a random-effects model on log(1 + relative growth).
Each series' standard error comes from its 95% bootstrap interval, the between-series variance τ²
from the DerSimonian-Laird estimator, and each estimate is shrunk toward the group mean with
weight τ²/(τ² + se²). Small, noisy wikis move most; precise ones barely move. τ = 0 means the
data are consistent with one shared trend. The ranking uses pooled growth whenever a group has 3+
series.
