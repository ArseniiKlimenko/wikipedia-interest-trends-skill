"""wikitrends: research topic interest across Wikipedia language editions.

Commands (see `python -m wikitrends --help`):
  resolve  - find Wikidata items and article titles for a topic in several languages
  related  - list articles linked from a seed article, ranked by recent views
  analyze  - fetch pageviews, compute growth + confidence, write charts and a summary
  report   - render a one-page PDF from an analysis directory and narrative.md
  check    - verify the environment and API access
  cache    - show or clear the local data cache
"""

__version__ = "1.0.0"
