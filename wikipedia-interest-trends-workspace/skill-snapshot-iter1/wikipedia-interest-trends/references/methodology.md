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

## 1. Data source and cleaning
- **Source**: Wikimedia Analytics API, `per-article` (daily views of each article) and `aggregate`
  (daily views of the whole language edition). Data exists from July 2015. License CC0.
- **Agent `user`** (default): human traffic. Self-identified crawlers (`spider`) and heuristically
  detected bots (`automated`) are excluded; undetected bots remain possible.
- **Periods** are whole calendar months ending with the last complete month.
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
| Views chg | Dampened views, recent 12 months vs previous 12 |
| **Relative growth** | Change in the topic's *share* of all wiki views, recent 12 vs previous 12. Main signal. |
| 95% CI | Moving-block bootstrap: 2,000 resamples of 28-day blocks within each period, numerator and denominator together |
| Last 6m YoY | Share in the last 6 months vs the same 6 months a year earlier (momentum) |
| Trend/yr | Theil-Sen slope of log monthly share over the whole period, as %/year |
| Months up | How many of the last 12 months beat the same month a year earlier (share) |
| Year over year | For periods of 36+ months: each 12-month block vs the previous one |

With fewer than 24 months, growth compares the last half with the first half (flagged: seasonality
can bias it).

**Why relative growth?** Wikipedia's total human traffic moves for reasons unrelated to any topic
(AI answers in search, bot reclassification, a shift of readers between language editions, such as
Ukrainian readers moving from ru to uk after 2022). Dividing by the whole-wiki total isolates
interest in the topic. The summary always shows the whole-wiki change too, so you can explain
"raw views fell 20% but the topic gained share".

## 3. Confidence grade (trust in the direction of relative growth)
Direction: **up** if the 95% CI is above 0, **down** if below 0, **no clear change** otherwise.

For up/down, each failed check counts once:
1. low volume (< 20 views/day in the recent year)
2. raw views move the other way
3. fewer than 8 of the last 12 months agree year-over-year
4. spikes >= 25% of views
5. the direction flips when spike days are kept
6. the whole-period monthly trend points the other way
7. one article in the basket drives the result (removing it flips the sign)

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
  percentage points with a 95% interval from the bootstrap samples; "clear" if the interval is
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
- **Known data break**: in May-June 2025 Wikimedia updated bot detection. Much traffic that had been
  counted as human turned out to be automated, and reported human views dropped from then on
  (many wikis show a step down). Year-over-year comparisons that span mid-2025 partly reflect
  this. Relative growth reduces the effect when bots were spread evenly, but not for articles that
  bots targeted.

## 6. Claim check
`report` extracts every percentage (and "pp" figure) from narrative.md and compares it with all
computed metrics (tolerance about 1 pp). Unmatched numbers are listed. They are usually typos,
rounding or numbers invented from memory. Fix them rather than ignoring the warning.

## 7. Phrasing for a founder
- "Interest is growing": only with a CI above zero, and always with the confidence grade.
- "Interest is stable": CI crosses zero and is narrow.
- "We can't tell": CI crosses zero and is wide, or the grade is LOW.
- Translate relative growth: "the topic's share of everything people read on Polish Wikipedia
  rose 15% (95% range +9% to +21%)".
- Name the proxy: "measured through the articles X and Y".
- End with the decision: what to validate next and with which signal.
