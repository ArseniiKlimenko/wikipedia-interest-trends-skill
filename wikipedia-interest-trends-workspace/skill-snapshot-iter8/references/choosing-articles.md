# Choosing articles: turning a business topic into a measurable basket

Wikipedia measures interest in *articles*, while users ask about *topics* ("an astronomy course",
"learning English"). The basket of articles is the main modelling assumption, so choose it
deliberately and name it in the report.

## Principles
1. **Start from the user's intent.** "Astronomy course" means the subject, so use core astronomy
   articles. "Learning English" means intent to learn: exam articles (IELTS, TOEFL) carry more
   learning intent than the general "English language" article, which is also read for history
   and linguistics.
2. **Use Wikidata items (QIDs)** so the same concept is measured in every language. `resolve`
   shows each item's title per language.
3. **Compare like with like.** Prefer items that have articles in *all* compared languages. If one
   language lacks an article, the summary says the basket is incomplete. Growth stays usable, but
   absolute sizes are not comparable.
4. **2-6 articles for a broad topic, 1 for a narrow one.** More articles give smoother data and
   less dependence on one page's quirks (renames, bot traffic, main-page features).
5. **Avoid ambiguous or news-driven pages** unless news interest is the question: people, events,
   companies, and words with several meanings (e.g. "Mercury": planet, element, god).
6. **Check the basket after running.** "Articles used" in the summary shows each article's share
   of views and its own relative growth. If one article is 80%+ of the basket, the result is
   essentially that article. If articles disagree strongly, consider splitting them into separate
   topics (e.g. "English exams" vs "English language").
7. **Split intents into separate topics** (`--topic` twice) rather than mixing them in one basket.

## When an article is missing
- The absence itself is a finding: nobody has written about it in that language (a possible
  content gap and a weak signal about local interest).
- `resolve` searches that wiki. A local article can serve as a proxy **only** if it covers the same
  concept. For example, "Głodówka lecznicza" (therapeutic fasting) in Polish is *not* the same as
  intermittent fasting. If you use such a page, call it a proxy and lower your confidence.
- Alternatives: a broader item that exists (e.g. "Fasting"), or report "not measurable in this
  language" and rely on the other languages.

## Building a basket automatically
`wt.py expand <QID> --langs a,b` combines two sources and prints a ready `--topic`:
- **Wikidata graph**: items that are a subclass, part, facet or instance of the seed, or that the
  seed has as a part or studies (P279, P361, P1269, P31, P527, P2578);
- **Link graph**: articles linked both ways with the seed in the first language, kept only if
  Wikidata confirms that they are a kind of the seed or of what it studies (instance-of /
  subclass-of chain, up to 4 hops). This removes cities, universities and people.
Candidates are ranked by views over the last 60 days; the basket takes the seed plus the top
items that have articles in every requested language. Two guards against general-interest pages:
items with more than 3x the seed article's views are left out ("too general", listed separately),
and items that would be 20%+ of the basket's views are flagged for review. Review the basket
anyway: e.g. "Earth" is correctly an astronomical object, but it also draws geography readers, so
a user asking about astronomy *courses* may prefer to drop it. `analyze` then reports whether one
article drives the result (leave-one-out check).

## Discovering subtopics
`wt.py discover <lang> --seed <QID>` measures every sub-topic from `expand` (relative growth,
interval, confidence) and ranks the growing ones: "what inside this subject is gaining readers?".
`wt.py related <lang>:<Title>` is the raw, unfiltered link list.

## Verified examples (QIDs)
| Topic | Items |
|---|---|
| Intermittent fasting | Q1666254 (no Polish article as of 2026) |
| Astronomy (broad) | Q333 astronomy, Q318 galaxy, Q525 Sun, Q634 planet, Q321 Milky Way, Q523 star, Q1 universe |
| English: general interest | Q1860 English language, Q130192 English as a second or foreign language |
| English: learning intent | Q490396 IELTS, Q487425 TOEFL |

Always confirm QIDs with `resolve`. Descriptions tell you whether you have the right concept.
