# Growing topics in pl.wikipedia

Candidates: articles in the monthly top-1000 of pl.wikipedia over the last 3 months (people, films, TV, sport, lists excluded). Period 2024-09..2026-08; relative growth = last 12 months vs previous 12 (share of all wiki views), 95% interval, spike-dampened.
Measured 60 candidates (0 skipped below 90 views/month): 16 growing, 2 declining, 42 without a clear change.

## Growing (95% interval above zero; sorted by confidence, then growth)

| # | Article | QID | Views/mo | Relative growth [95% CI] | Spikes | Confidence |
|---|---|---|---|---|---|---|
| 1 | Maroko | Q1028 | 30,936 | +26% [+12%, +44%] | 13% | HIGH |
| 2 | Malta | Q233 | 64,141 | +13% [+5%, +23%] | 15% | HIGH |
| 3 | Bractwo Kapłańskie Świętego Piusa X | Q868160 | 15,899 | +114% [+45%, +238%] | 26% | MEDIUM |
| 4 | Paragwaj | Q733 | 12,932 | +68% [+30%, +129%] | 34% | MEDIUM |
| 5 | Wybrzeże Kości Słoniowej | Q1008 | 14,034 | +47% [+10%, +115%] | 38% | MEDIUM |
| 6 | Senegal | Q1041 | 11,551 | +30% [+11%, +55%] | 32% | MEDIUM |
| 7 | Falklandy | Q9648 | 11,997 | +25% [+3%, +59%] | 34% | MEDIUM |
| 8 | Poznań | Q268 | 27,330 | +8% [+3%, +16%] | 0% | MEDIUM |
| 9 | Order Odrodzenia Polski | Q579688 | 41,586 | +8% [+1%, +16%] | 4% | MEDIUM |
| 10 | Księga wieczysta | Q672598 | 30,300 | +2456% [+762%, +5081%] | 4% | LOW |
| 11 | Curaçao | Q25279 | 74,538 | +332% [+89%, +780%] | 67% | LOW |
| 12 | Ranking FIFA | Q180825 | 13,286 | +309% [+51%, +797%] | 32% | LOW |
| 13 | Odyseja | Q35160 | 13,112 | +276% [+24%, +677%] | 16% | LOW |
| 14 | Ceuta | Q5823 | 20,460 | +146% [+8%, +351%] | 57% | LOW |
| 15 | Republika Zielonego Przylądka | Q1011 | 65,254 | +62% [+19%, +139%] | 37% | LOW |

## Declining fastest

- Niemcy (Q183): -13% [-18%, -8%], high confidence
- Polska (Q36): -6% [-10%, -2%], medium confidence

Next: turn promising QIDs into topics (group related ones) and run `wt.py analyze` for the full analysis, seasonality, forecast and report. LOW confidence rows are hypotheses, not findings.
Files: /Users/aklim/Documents/wikipedia-interest-trends-skill/wikipedia-interest-trends-workspace/iteration-6/eval-7-whats-growing-polish-wiki/with_skill/run-1/outputs/discover.json, discover.md
