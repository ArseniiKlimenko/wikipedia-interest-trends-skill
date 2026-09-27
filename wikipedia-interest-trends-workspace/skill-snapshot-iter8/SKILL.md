---
name: wikipedia-interest-trends
description: >-
  Measure how interest in topics changes across Wikipedia language editions (Wikimedia pageview
  data) and turn it into decisions: growth with 95% intervals and a confidence grade, seasonality,
  a 12-month forecast, regime changes, comparison and ranking of languages or topics, automatic
  topic baskets from Wikidata, discovery of growing topics, a second signal from Google Trends and
  the App Store, charts and a shareable one-page PDF. Use it whenever someone asks which topic,
  course, content area or language/market to invest in next, what is growing, whether interest in a
  subject is rising and how far that can be trusted, when interest peaks, how interest compares
  between languages or countries, or mentions Wikipedia pageviews, Google Trends or app-store
  demand, even if they only want a demand signal for a B2C product, content or localization decision.
compatibility: Needs Python 3.9+ and internet access to wikimedia.org, *.wikipedia.org, wikidata.org, query.wikidata.org, itunes.apple.com, trends.google.com (only with signals --trends) and PyPI (the first run installs pinned numpy, matplotlib and reportlab into a private virtual environment).
license: MIT
metadata:
  version: "1.2.0"
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
Wikimedia asks API clients for a contact: if the user gave you an email or project URL for this,
`export WIKITRENDS_CONTACT=<it>` before the first command; otherwise the tool warns once and uses a
generic User-Agent. Outputs go to `--out` (default `./wikitrends-output/<slug>`, never inside this folder).

## Workflow

### 1. Frame the question (no long interview)
Pull out four things, and pick defaults instead of asking when the request is clear enough:
- **Topics**: what the user wants to measure (a course, subject, product area).
- **Languages**: Wikipedia codes (`pl` Polish, `cs` Czech, `uk` Ukrainian, `de`, `es`, `pt`, `tr`,
  `vi`...). A language is not a country (see Pitfalls).
- **Period**: default `--months 24` (last 12 months vs the previous 12). The tool also loads up to
  48 months of history on its own for seasonality, the forecast and year-over-year blocks, so a
  "how far can we trust this" question does not need a longer period. Honour explicit periods;
  periods under 24 months cap confidence at LOW (seasonality is not controlled).
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
- **Name the intent you measure.** For "learning X", exam and course articles (IELTS, TOEFL) carry
  learning intent, while the article on the language itself measures general interest. Pick one
  deliberately, or run both as separate `--topic`s, and say which one the answer is based on.
- **Broad subject → basket.** When the user means a field, course or skill (astronomy, cooking,
  personal finance), the single definition article is a poor proxy: few people read "Astronomy"
  itself, while "Sun", "Planet" and "Galaxy" draw most of the readers. Let the tool build it:
  ```bash
  python3 <skill>/scripts/wt.py expand Q333 --langs uk,pl
  ```
  It combines the Wikidata graph (sub-classes, parts, what the field studies) with articles linked
  both ways, keeps only neighbours that Wikidata confirms are on-topic, ranks them by recent views,
  and prints a ready `--topic "Label=Q333|Q...|Q..."` with items that have articles in every
  language. Pages with more than 3x the seed's views are left out as general-interest pages, and
  items that would be 20%+ of the basket are flagged. Drop any item that does not match the user's
  meaning. A narrow concept (a diet, an
  exam, a product type) is fine with one article. More guidance:
  [references/choosing-articles.md](references/choosing-articles.md).
- **No article in a language** is a finding in its own right (a content gap). `resolve` shows what
  a search in that wiki finds. Use a local article only if it really covers the topic
  (`pl:Title`), and call it a proxy in the report.

### 2b. When the question is "what is growing?" (no fixed topic yet)
```bash
python3 <skill>/scripts/wt.py discover uk --seed Q333   # which parts of a subject grow
python3 <skill>/scripts/wt.py discover pl               # what grows in the whole wiki
```
Each candidate gets the full growth measurement (relative growth, 95% interval, spikes,
confidence). "Growing" also needs a Benjamini-Hochberg q <= 0.10, because with ~60 candidates a
few look "up" by chance; rows that are up but fail it are listed as hypotheses. With `--seed` the
candidates are the sub-topics from `expand`. Without it they come from the monthly top-1000 lists,
with people, films, TV, sport, lists and events excluded, so the result shows broad attention
shifts (countries, historical subjects, technologies) rather than celebrities. The **Pattern**
column separates *sustained* growth from *bursts* (most of the year's views in two months), and
"Shared peaks" lists bursts in the same month, which often have one cause (e.g. a World Cup
lifting several countries at once). Present only sustained rows as content opportunities; name the
shared event for bursts. Treat LOW rows as hypotheses. Then run `analyze` on the promising QIDs.

### 3. Run the analysis
```bash
python3 <skill>/scripts/wt.py analyze \
  --topic "Intermittent fasting=Q1666254" \
  --langs pl,cs --months 24 --report-lang uk --out <output-dir>
```
- `--topic "Label=Q1|Q2|pl:Title"` can be repeated. Items are QIDs or `lang:Title`
  (disambiguation pages are refused).
- `--report-lang uk` when the user writes Ukrainian (labels in charts, draft and PDF; `en`
  otherwise). Always write the narrative in the user's language.
- `--weights size=1,growth=2,intensity=0.5` changes the ranking criteria.
- It prints `summary.md`: **rules for your reply**, articles used, a results table, confidence
  notes, models, comparisons, ranking, reader geography, **suggestions**, warnings and file names.
  Read all of it before concluding. If
  Suggestions propose a broader basket or a longer period, do that re-run first: it is cheap because
  the data is cached.

### 4. Interpret: what the numbers mean
- **Relative growth** is the main interest signal: the change in the topic's share of *all*
  views of that language edition. It removes Wikipedia-wide traffic changes. It is already *net*
  of the whole-wiki change, so never subtract the wiki trend from it again or compare the two: a
  topic at -48% in a wiki that fell 25% lost share *on top of* that decline. **Views change** is the
  reader count after dampening short spikes (the summary gives the with-spikes values when they
  differ).
- **95% interval** crossing zero means "no clear change". Never call that growth, a rise or a
  positive trend, even when it is the best estimate in the group: "+7% [-20%, +43%]" is "no clear
  change, highest point estimate". If you still recommend that series, say it is for its upside
  and must be verified first. The interval compares the same calendar days and months of both
  years and allows for persistent noise, so it is wider than a naive one; that is intended.
- **Confidence** (HIGH / MEDIUM / LOW) grades how far to trust the *direction*. Quote the listed
  concerns: low volume, spikes, one article dominating, level shifts, a known data break.
- **Comparisons** say whether one series grows faster than another with statistical clarity.
- **Ranking** orders series within each topic (or within one language) by weighted percentile
  ranks of size, growth and intensity. It is relative to the set you asked about, nothing more.
- **Per 1M wiki views** compares how intensely a topic is read across languages of very
  different size. Absolute views show audience size.
- **May-June 2025 bot-detection update**: the warning gives the *measured* step of each wiki's
  human views across it, and Confidence notes flag the series whose own step differs from their
  wiki's by 25%+. Mention the update only for flagged series or a flagged level shift, using those
  numbers; never estimate its size yourself.
- **Seasonality** (strength 0-1, peak and low months) is reported only when the month pattern
  repeats across the years of history (p < 0.05); otherwise the summary says there is none. It
  tells when to launch or run campaigns: a school subject that drops 40% in July needs a September
  launch.
- **Forecast** of the next 12 months vs the last 12, with an 80% range, only for series with 36+
  months of history. The model is picked by a rolling-origin backtest (smoothing model, "same as
  last year", or "same as last year plus the yearly change"). Present it as a range and a
  scenario, never as a promise; if the summary notes that it points against the measured change,
  do not use it as the expected outcome.
- **Regime changes** are dated breaks in level or trend (e.g. "2026-03: trend -41%/yr → -19%/yr"),
  useful to say *when* something changed.
- **Partial pooling**: with 3+ languages (or topics) the tool shrinks noisy estimates of small wikis
  toward the group's common trend, and the ranking uses the pooled value. Quote raw growth as the
  measurement and pooled growth as the robust estimate when they differ.

Detailed definitions and confidence rules: [references/methodology.md](references/methodology.md).

### 4b. Check with a second signal (recommended before recommending anything)
```bash
python3 <skill>/scripts/wt.py signals <output-dir> --trends --keyword pl="nauka angielskiego"
```
For each language it checks the countries where most of its readers are (or its home country):
the **App Store** for a keyword (competition, ratings, recent entrants; Apple's official search
API) and, with `--trends`, **Google Trends** for the same Wikidata topic (via its Freebase ID, so it
is language-independent), last 12 months vs previous 12, and whether it **agrees** with Wikipedia.
`report` then adds a "Second signals" line to the PDF. Reading it:
- Agreement strengthens the conclusion. **DISAGREE** (typically Trends up, Wikipedia down) usually
  means readers moved from Wikipedia to search or AI answers. Report both, not just one.
- `--trends` uses Google's unofficial web endpoints (few cached requests; automated use may
  conflict with Google's terms), so mention the source in the report. If it fails, or the user
  prefers the official route, use a CSV export from trends.google.com: `--trends-csv lang=file.csv`.
- A basket is represented in Trends by the topic of its first item; the output says so.
- App Store figures describe supply and traction, not search volume. **0 relevant apps** means the
  keyword did not match store listings (often English-only), not that there is no market: try
  another `--keyword` and never conclude "avoid this market" from it. Details:
  [references/discovery-and-signals.md](references/discovery-and-signals.md).

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

Rules that keep the report trustworthy and readable:
- **Every reason points to the data.** Each "why" should cite a number or note from summary.md
  (size, growth, intensity, confidence, geography). Outside knowledge (competition, market size,
  demographics, "growing startup scene") cannot be backed by this data, and a reader will assume it
  came from the analysis. Leave it out, or mark it plainly as an assumption outside the data.
- **Explain relative growth once in plain words** ("the topic's share of everything read on Czech
  Wikipedia"), and give the whole-wiki change for context (the draft includes that line).
- **Keep it short:** answer at most 3 sentences, at most 5 evidence bullets of about 25 words each.
  Longer text still fits on one page, but `report` warns that it had to shrink the page.

The first section becomes the highlighted answer box; the other sections sit beside the chart.
Then render the PDF:
```bash
python3 <skill>/scripts/wt.py report <output-dir>
```
It prints the PDF path, confirms that it is one page, and runs a **claim check** against the
analysis: every percentage must match a value *of the series the sentence names* with the same
sign; words like "grows/positive/зростає" must fit the series' direction; stated confidence levels
must match. Problems make `report` exit with code 1: fix narrative.md and run `report` again until
it passes. It also warns about country names used for language editions, numbers that are not in
the data (outside facts), comparisons with the whole-wiki change, and Russian words in Ukrainian
text; fix those unless you are sure the text is right.

### 6. Reply to the user
Lead with the answer, then give the key numbers with their intervals and confidence, the main
caveats and assumptions (articles used, period, what "relative" means), a recommendation, and the
paths to `report.pdf` and the charts (`trend.png`, `growth.png`). Keep it short; the PDF holds
the detail.

## Follow-up questions
When the user refines an earlier request ("add Portuguese", "growth matters more"):
1. Re-use the **same `--topic` values** (same QIDs, grouped the same way) so the numbers stay
   comparable. Change the measurement only if the user asks, and then say why.
2. Re-run `analyze` with the new options (a new `--out` folder is fine). The earlier run is found
   automatically (same `--out` folder, or the last run from this working directory in the last
   12 hours); pass `--previous <earlier folder>` if it was elsewhere. The summary then starts with
   **Changes vs previous analysis**: languages or weights changed, and each series' rank before
   and after. It flags **MEASUREMENT CHANGED** if the topics differ.
3. Rebuild every claim from the **new** summary.md. Do not copy sentences from your earlier
   answer: it may contain a mistake that the new run corrects. Open the reply with what changed.

Data is cached locally (finished months never change), so follow-ups are fast:
- another language: add it to `--langs`; a longer history: `--months 36`;
- different criteria: new `--weights`; another article in the basket: extend `--topic`;
- a different presentation only: edit narrative.md and re-run `report` (no re-analysis needed).

## Pitfalls to mention when relevant
- **Language is not country.** Series are named `<code>.wikipedia`. Name audiences by language
  ("Spanish-language readers", not "Spain"; "Vietnamese-language Wikipedia", not "Vietnam"). Check the "Where readers are" section: es.wikipedia serves Spain
  and Latin America, and many readers use English Wikipedia instead of their own. Some home
  countries (for example Turkey or Vietnam) are *withheld* from Wikimedia's country data. That does
  **not** mean the audience is diaspora: most readers are still there, and the listed shares only
  split the remaining traffic.
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
- `python3 <skill>/scripts/wt.py selftest`: offline tests (use it if results look suspicious).
- `python3 <skill>/scripts/wt.py related uk:Астрономія`: raw list of articles linked both ways with
  recent views (`expand` already uses it and filters it).
- Add `--json` to `resolve` for machine-readable output; `analyze` also writes `analysis.json`
  and `data.csv` (monthly values) for further work.
