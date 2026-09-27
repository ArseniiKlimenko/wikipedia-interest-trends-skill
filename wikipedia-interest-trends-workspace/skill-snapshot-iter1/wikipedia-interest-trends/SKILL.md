---
name: wikipedia-interest-trends
description: >-
  Measure how interest in topics changes across Wikipedia language editions (Wikimedia pageview
  data) and turn it into decisions: growth with 95% intervals and a confidence grade, comparison
  between languages or topics, an opportunity ranking, charts and a shareable one-page PDF. Use it
  whenever someone asks which topic, course, content area or language/market to invest in next,
  whether interest in a subject is growing and how far that can be trusted, how interest compares
  between languages or countries, or mentions Wikipedia pageviews, popularity or traffic trends,
  even if they only want a demand signal for a B2C product, content or localization decision.
compatibility: Needs Python 3.9+ and internet access to wikimedia.org, wikidata.org and PyPI (the first run installs numpy, matplotlib and reportlab into a private virtual environment).
license: MIT
metadata:
  version: "1.0.0"
---

# Wikipedia interest trends

Founders use this to decide what to build next: which topic to add, which language to launch.
Bundled code does all data work: resolving articles across languages, downloading and caching
pageviews, statistics, confidence checks, charts and the PDF. Your job is to pick sensible
articles, run the commands, interpret the output honestly and write the conclusion in the user's
language. Do not write your own download or statistics code. The tool's numbers are the source
of truth, and the report checks your text against them.

All commands use the launcher. `<skill>` is the absolute path of the folder holding this file:

```bash
python3 <skill>/scripts/wt.py <command> [options]
```

The first call creates a private environment (about 20-60 s). If you see "waiting ... (normal)",
Wikimedia is rate-limiting; just wait. Run commands one after another, not in parallel.

## Workflow

### 1. Frame the question (no long interview)
Pull out four things, and pick defaults instead of asking when the request is clear enough:
- **Topics**: what the user wants to measure (a course, subject, product area).
- **Languages**: Wikipedia codes (`pl` Polish, `cs` Czech, `uk` Ukrainian, `de`, `es`, `pt`, `tr`,
  `vi`...). A language is not a country (see Pitfalls).
- **Period**: default `--months 24` (last 12 months vs the previous 12). Use `--months 36` when the
  user asks how far to trust a trend: it adds a year-over-year history. Honour explicit periods.
- **What "promising" means**: audience size, growth or intensity. This sets `--weights`.

State your assumptions in the answer rather than asking, unless the topic is truly ambiguous.

### 2. Map topics to Wikipedia articles
```bash
python3 <skill>/scripts/wt.py resolve "intermittent fasting" "astronomy" --langs pl,cs,uk
```
- Query in English for the best Wikidata match; the output shows the QID (e.g. `Q1666254`) and the
  article title in every requested language.
- Choose the item whose description matches the user's meaning. Skip disambiguation pages,
  journals, films and people with the same name.
- A broad topic is better measured by a **basket** of 2-6 core articles (e.g. astronomy + planet +
  galaxy + star). A narrow topic is fine with one article. For how to choose articles and proxies,
  see [references/choosing-articles.md](references/choosing-articles.md).
- **No article in a language** is a finding in its own right (a content gap). `resolve` shows what
  a search in that wiki finds. Use a local article only if it really covers the topic
  (`pl:Title`), and call it a proxy in the report.
- To discover subtopics ("what inside astronomy is popular?"):
  `python3 <skill>/scripts/wt.py related uk:Астрономія --limit 20` lists neighbouring articles
  with recent views and QIDs, ready to feed into `analyze`.

### 3. Run the analysis
```bash
python3 <skill>/scripts/wt.py analyze \
  --topic "Intermittent fasting=Q1666254" \
  --langs pl,cs --months 24 --report-lang uk --out <output-dir>
```
- `--topic "Label=Q1|Q2|pl:Title"` can be repeated. Items are QIDs or `lang:Title`.
- `--report-lang uk` for Ukrainian labels in the charts and PDF (`en` otherwise). Always write the
  narrative in the user's language.
- `--weights size=1,growth=2,intensity=0.5` changes the ranking criteria.
- It prints `summary.md`: articles used, a results table, confidence notes, comparisons, ranking,
  reader geography, warnings and file names. Read all of it before concluding.

### 4. Interpret: what the numbers mean
- **Relative growth** is the main interest signal: the change in the topic's share of *all*
  views of that language edition. It removes Wikipedia-wide traffic changes (many wikis lost
  10-25% of human views in 2025). **Views change** is the raw reader count.
- **95% interval** crossing zero means "no clear change". Never call that growth.
- **Confidence** (HIGH / MEDIUM / LOW) grades how far to trust the *direction*. Quote the listed
  concerns: low volume, spikes, one article dominating, level shifts, a known data break.
- **Comparisons** say whether one series grows faster than another with statistical clarity.
- **Ranking** orders series within each topic (or within one language) by weighted percentile
  ranks of size, growth and intensity. It is relative to the set you asked about, nothing more.
- **Per 1M wiki views** compares how intensely a topic is read across languages of very
  different size. Absolute views show audience size.
- Warnings about a **level shift** or the **May-June 2025 bot-detection update** mean that part of a
  decline may be a measurement artifact. Say so plainly.

Detailed definitions and confidence rules: [references/methodology.md](references/methodology.md).

### 5. Write the report
`analyze` writes a data-based draft at `<output-dir>/narrative.md`. Rewrite it in the user's
language with the Write tool, keeping this shape:

```markdown
# <Title in the user's language>

## <Answer>
Two or three sentences: the direct answer, the key number with its interval, and the confidence.

## <Evidence>
- One bullet per key series or fact, with numbers copied from summary.md.

## <Recommendation>
- What to do given the user's goal, and why (tie it to size / growth / confidence).

## <Caveats / Next steps>
- The main limitation and how to reduce it (longer period, broader basket, second data source).
```

The first section becomes the highlighted answer box; the other sections sit beside the chart.
Then render the PDF:
```bash
python3 <skill>/scripts/wt.py report <output-dir>
```
It prints the PDF path, confirms that it is one page, and runs a **claim check**: every
percentage in your narrative must match a computed metric. If it lists problems, fix the numbers
in narrative.md and run `report` again.

### 6. Reply to the user
Lead with the answer, then give the key numbers with their intervals and confidence, the main
caveats and assumptions (articles used, period, what "relative" means), a recommendation, and the
paths to `report.pdf` and the charts (`trend.png`, `growth.png`). Keep it short; the PDF holds
the detail.

## Follow-up questions
Data is cached locally (finished months never change), so re-running with new options is fast:
- another language: add it to `--langs`; a longer history: `--months 36`;
- different criteria: new `--weights`; another article in the basket: extend `--topic`;
- a different presentation only: edit narrative.md and re-run `report` (no re-analysis needed).

Keep the same QIDs across follow-ups so numbers stay comparable, and use a new `--out` folder
when the user may still want the earlier version.

## Pitfalls to mention when relevant
- **Language is not country.** Check the "Where readers are" section: es.wikipedia serves Spain
  and Latin America; some countries (for example Turkey or Vietnam) are withheld from Wikimedia's
  country data. Many readers use English Wikipedia instead of their own.
- **Curiosity is not purchase intent.** Recommend validating with a second signal.
- **Low volume** (under about 20 views a day) is noisy, so prefer broader baskets or longer periods.
- **Seasonality**: school topics drop in summer and diets peak in January, which is why growth
  compares whole years.
- **News spikes** are dampened automatically; the summary lists the largest ones with dates, which
  can explain an event.
- Do not compare absolute views of *different baskets* across languages. Compare growth and
  intensity instead.

## Other commands
- `python3 <skill>/scripts/wt.py check`: environment, cache and API connectivity.
- `python3 <skill>/scripts/wt.py cache info|clear`: local cache.
- Add `--json` to `resolve` for machine-readable output; `analyze` also writes `analysis.json`
  and `data.csv` (monthly values) for further work.
