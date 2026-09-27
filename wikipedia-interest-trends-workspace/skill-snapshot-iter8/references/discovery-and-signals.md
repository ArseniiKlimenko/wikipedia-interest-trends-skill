# Discovery and second signals: details

Read this when you use `discover` or `signals`, or when a user asks how these numbers are made.

## discover
- **Whole-wiki mode** (`discover pl`): candidates are the articles in Wikimedia's monthly top-1000
  lists over the last 3 months (`--top-months`), minus the main page and special/namespace pages.
  By default, anything whose Wikidata instance-of chain (3 hops) reaches a person, fictional
  character, film, TV series/season/episode, album/song, band, sports season/event/club, list,
  disambiguation page, year, election, video game, event or future event, TV programme, ranking
  list or rating system is dropped (`--include-all` keeps them). What remains is still news-sensitive (countries during tournaments, eclipses).
- **Subject mode** (`discover uk --seed Q333`): candidates are the verified sub-topics from `expand`.
  This is the mode for product questions ("which parts of astronomy should the course cover?").
- Every candidate is measured like `analyze` does it (24 months, dampened spikes, relative growth
  with a 95% interval, confidence grade). Rows under `--min-views` (default 90/month) are skipped.
  The growing list is sorted by confidence first, then growth, so large clean trends rank above
  tiny pages with extreme percentages.
- **Multiple testing.** Measuring ~60 candidates means a few will look "up" by chance (with the
  earlier unpaired interval about 3-5 per run under no change). Each candidate's p-value is the
  larger of the bootstrap and monthly t-test p-values; Benjamini-Hochberg q-values are computed
  over the analysed candidates, and "growing" requires q <= 0.10. Up-but-not-significant rows are
  listed separately as hypotheses.
- **Bursts** (35%+ of the year's views in two months) are listed with their peak month even when
  they are not significant, and bursts that peak in the same month are grouped ("Shared peaks"),
  because one event (a tournament, a pilgrimage season, news) often lifts several pages at once.
- First run: about one API call per candidate (60 candidates ≈ 20-40 s); cached afterwards.

## signals
Run it on an analysis folder: `signals <dir> [--keyword lang=phrase] [--geo lang=CC,CC]`.

**Country.** For each language, the countries with 15%+ of its readers in the analysis' country
data (at most 3; e.g. es→ES, MX), otherwise its main home country (pl→PL, uk→UA, pt→BR, ...).
Override with `--geo es=ES,MX,AR`.

**Google Trends.**
- Topic = the Wikidata item's Freebase ID (P646), which Google Trends treats as a topic in every
  language. Without one, the local article title (or `--keyword`) is used as a plain search term,
  which is less comparable. A basket of several items uses the topic of its **first** item; the
  output says which topic stands for the basket.
- Weekly index (0-100, relative to the peak in the window), last 12 months vs previous 12, 95%
  interval by block bootstrap (4-week blocks). Only the direction and the change are meaningful.
- **Agreement** with the Wikipedia direction for that language: `agree`, `both flat`, `partly` (one
  side shows no clear change), `DISAGREE`. A frequent pattern since 2024-25: Trends up, Wikipedia
  down, meaning people still search for the subject but read answers elsewhere. For a product,
  Google interest is usually the better demand proxy; Wikipedia remains the better *comparable*
  cross-language measurement.
- **Opt-in (`--trends`).** Access uses Google Trends' public web endpoints: unofficial,
  undocumented and rate-limited, and Google's terms of service do not permit automated querying
  without permission. The skill therefore queries them only when asked, sends a few requests per
  run with pauses, caches results for 7 days, and sends no contact details to Google. For regular
  or commercial use, prefer the official Google Trends API (alpha access, announced 2025) or the
  CSV route: on trends.google.com choose the topic and country, set the same period, download
  "Interest over time" as CSV, and pass `--trends-csv lang=path` (same metric). On failure the
  command reports it and continues.

**App Store** (Apple iTunes Search API, official, no key, about 20 calls/minute).
- Search results for the keyword in the country store. An app counts as relevant when a word of
  the keyword (or of the English topic name) starts a word in its name, or in its description for
  apps outside generic genres (social networking, music, photo & video, entertainment, games,
  shopping, finance, travel, news...). Words shorter than 5 letters must match whole words, so
  "post" does not match "InPost".
- Warnings: **0 relevant apps** means the wording did not match store listings (many are in
  English), not that demand is missing; try another `--keyword`. When fewer than half of the
  results are relevant, the numbers are flagged as rough.
- Metrics over the 25 most-rated relevant apps: total ratings (traction of the category), how many
  were updated in the last 12 months (activity), how many were released in the last 24 months and
  their share of ratings (room for newcomers), and the leader's share of ratings (concentration).
- There is no search volume in this API. Read it as competition and category activity: many rated,
  actively updated apps = proven but crowded market; a dominant old leader = hard entry; recent
  entrants gaining ratings = open market. Keyword wording matters, so use the phrase a local user
  would type.
