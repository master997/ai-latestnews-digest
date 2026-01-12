"""RSS feed scraper module."""

import feedparser
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import html
import re


@dataclass
class Article:
    """Represents a single article from an RSS feed."""
    title: str
    link: str
    source: str
    published: Optional[datetime]
    description: str
    summary: str = ""
    relevance_score: float = 0.0

    def __hash__(self):
        return hash(self.link)

    def __eq__(self, other):
        if isinstance(other, Article):
            return self.link == other.link
        return False


def clean_html(raw_html: str) -> str:
    """Remove HTML tags and decode entities from text."""
    clean = re.sub(r'<[^>]+>', '', raw_html)
    clean = html.unescape(clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def parse_date(entry: dict) -> Optional[datetime]:
    """Parse publication date from feed entry."""
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6])
        except (TypeError, ValueError):
            pass
    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6])
        except (TypeError, ValueError):
            pass
    return None


def fetch_feed(url: str, source_name: str, max_entries: int = 50) -> list[Article]:
    """
    Fetch and parse articles from an RSS feed.

    Args:
        url: RSS feed URL
        source_name: Name of the source for attribution
        max_entries: Maximum number of entries to fetch

    Returns:
        List of Article objects
    """
    articles = []

    try:
        feed = feedparser.parse(url)

        if feed.bozo and not feed.entries:
            print(f"  Warning: Could not parse feed from {source_name}: {feed.bozo_exception}")
            return articles

        for entry in feed.entries[:max_entries]:
            title = clean_html(entry.get('title', 'No Title'))
            link = entry.get('link', '')

            description = ''
            if 'summary' in entry:
                description = clean_html(entry.summary)
            elif 'description' in entry:
                description = clean_html(entry.description)
            elif 'content' in entry and entry.content:
                description = clean_html(entry.content[0].get('value', ''))

            # Truncate description if too long
            if len(description) > 1000:
                description = description[:1000] + "..."

            published = parse_date(entry)

            article = Article(
                title=title,
                link=link,
                source=source_name,
                published=published,
                description=description
            )
            articles.append(article)

    except Exception as e:
        print(f"  Error fetching {source_name}: {e}")

    return articles


def fetch_all_feeds(feeds_config: list[dict]) -> list[Article]:
    """
    Fetch articles from all configured RSS feeds.

    Args:
        feeds_config: List of feed configurations from config file

    Returns:
        Deduplicated list of Article objects
    """
    all_articles = []
    seen_links = set()

    for feed in feeds_config:
        if not feed.get('enabled', True):
            continue

        name = feed.get('name', 'Unknown')
        url = feed.get('url', '')

        if not url:
            continue

        print(f"  Fetching: {name}")
        articles = fetch_feed(url, name)

        for article in articles:
            if article.link not in seen_links:
                seen_links.add(article.link)
                all_articles.append(article)

    # Sort by publication date (newest first)
    all_articles.sort(
        key=lambda x: x.published or datetime.min,
        reverse=True
    )

    return all_articles
