"""wikitrends: research topic interest across Wikipedia language editions.

Commands (see `python -m wikitrends --help`):
  resolve  - find Wikidata items and article titles for a topic in several languages
  related  - list articles linked from a seed article, ranked by recent views
  expand   - suggest an article basket from the Wikidata graph + link graph
  discover - find growing topics (monthly top-1000 lists, or sub-topics of a seed item)
  signals  - second demand signals for an analysis: Google Trends and the App Store
  analyze  - fetch pageviews, compute growth + confidence, write charts and a summary
  report   - render a one-page PDF from an analysis directory and narrative.md
  check    - verify the environment and API access
  cache    - show or clear the local data cache
"""

__version__ = "1.2.0"
