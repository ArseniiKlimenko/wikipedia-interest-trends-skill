# Growing topics in pl.wikipedia

Candidates: articles in the monthly top-1000 of pl.wikipedia over the last 3 months (people, films, TV, sport, lists excluded). Period 2024-09..2026-08; relative growth = last 12 months vs previous 12 (share of all wiki views), 95% interval, spike-dampened.
Measured 60 candidates (0 skipped below 90 views/month): 16 growing, 2 declining, 42 without a clear change.

Relative growth is already net of the whole-wiki traffic change; do not adjust it again.

## Growing (95% interval above zero; sustained first, then by confidence and growth)

| # | Article | QID | Views/mo | Relative growth [95% CI] | Spikes | Pattern | Confidence |
|---|---|---|---|---|---|---|---|
| 1 | Maroko | Q1028 | 30,936 | +26% [+12%, +44%] | 13% | sustained | HIGH |
| 2 | Malta | Q233 | 64,141 | +13% [+5%, +23%] | 15% | sustained | HIGH |
| 3 | Poznań | Q268 | 27,330 | +8% [+3%, +16%] | 0% | sustained | MEDIUM |
| 4 | Order Odrodzenia Polski | Q579688 | 41,586 | +8% [+1%, +16%] | 4% | sustained | MEDIUM |
| 5 | Bractwo Kapłańskie Świętego Piusa X | Q868160 | 15,899 | +114% [+45%, +238%] | 26% | burst, peak 2026-07 (57% of the year in 2 months) | MEDIUM |
| 6 | Paragwaj | Q733 | 12,932 | +68% [+30%, +129%] | 34% | burst, peak 2026-06 (57% of the year in 2 months) | MEDIUM |
| 7 | Wybrzeże Kości Słoniowej | Q1008 | 14,034 | +47% [+10%, +115%] | 38% | burst, peak 2026-06 (68% of the year in 2 months) | MEDIUM |
| 8 | Senegal | Q1041 | 11,551 | +30% [+11%, +55%] | 32% | burst, peak 2026-06 (56% of the year in 2 months) | MEDIUM |
| 9 | Falklandy | Q9648 | 11,997 | +25% [+3%, +59%] | 34% | burst, peak 2026-07 (61% of the year in 2 months) | MEDIUM |
| 10 | Księga wieczysta | Q672598 | 30,300 | +2456% [+762%, +5081%] | 4% | burst, peak 2026-04 (58% of the year in 2 months) | LOW |
| 11 | Curaçao | Q25279 | 74,538 | +332% [+89%, +780%] | 67% | burst, peak 2026-06 (85% of the year in 2 months) | LOW |
| 12 | Ranking FIFA | Q180825 | 13,286 | +309% [+51%, +797%] | 32% | burst, peak 2026-06 (55% of the year in 2 months) | LOW |
| 13 | Odyseja | Q35160 | 13,112 | +276% [+24%, +677%] | 16% | burst, peak 2026-07 (70% of the year in 2 months) | LOW |
| 14 | Ceuta | Q5823 | 20,460 | +146% [+8%, +351%] | 57% | burst, peak 2026-08 (86% of the year in 2 months) | LOW |
| 15 | Republika Zielonego Przylądka | Q1011 | 65,254 | +62% [+19%, +139%] | 37% | burst, peak 2026-06 (66% of the year in 2 months) | LOW |

## Shared peaks (bursts in the same month; check for a common cause)
- 2026-06: Paragwaj, Wybrzeże Kości Słoniowej, Senegal, Curaçao, Ranking FIFA, Republika Zielonego Przylądka.
- 2026-07: Bractwo Kapłańskie Świętego Piusa X, Falklandy, Odyseja.
Bursts that peak in the same month may share one cause (a tournament, an election, a film release, news). If they do, name it and treat the group as one short-lived event, not as separate growth areas. Only 'sustained' rows are candidates for lasting content.

## Declining fastest

- Niemcy (Q183): -13% [-18%, -8%], high confidence
- Polska (Q36): -6% [-10%, -2%], medium confidence

Next: turn promising QIDs into topics (group related ones) and run `wt.py analyze` for the full analysis, seasonality, forecast and report. LOW confidence rows are hypotheses, not findings.
Files: /Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends/wikitrends-output/discover_pl_top/discover.json, discover.md
