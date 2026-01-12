"""Main CLI entry point for AI News Digest."""

import argparse
import sys
from pathlib import Path

import yaml

from .scraper import fetch_all_feeds
from .llm import LLMProcessor
from .digest import generate_digest, print_digest_summary


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI News Digest - Aggregate and summarize AI/ML news from RSS feeds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      Run with default config.yaml
  %(prog)s -c custom.yaml       Use custom config file
  %(prog)s --no-summary         Skip LLM summarization
  %(prog)s --max-articles 10    Limit to 10 articles
  %(prog)s --list-feeds         List configured feeds
        """
    )

    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output directory for digest (overrides config)"
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        help="Maximum number of articles to process (overrides config)"
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Skip LLM summarization and relevance ranking"
    )
    parser.add_argument(
        "--list-feeds",
        action="store_true",
        help="List configured RSS feeds and exit"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # List feeds mode
    if args.list_feeds:
        print("\nConfigured RSS Feeds:")
        print("-" * 40)
        for feed in config.get("feeds", []):
            status = "enabled" if feed.get("enabled", True) else "disabled"
            print(f"  [{status}] {feed.get('name', 'Unknown')}")
            print(f"           {feed.get('url', 'No URL')}")
        return

    # Get settings
    digest_config = config.get("digest", {})
    output_dir = args.output or digest_config.get("output_dir", "./digests")
    max_articles = args.max_articles or digest_config.get("max_articles", 20)
    relevance_threshold = digest_config.get("relevance_threshold", 0.3)
    topic = config.get("topic", "AI and machine learning")

    print("\n" + "=" * 60)
    print("AI NEWS DIGEST")
    print("=" * 60)

    # Fetch RSS feeds
    print("\n[1/3] Fetching RSS feeds...")
    feeds_config = config.get("feeds", [])
    articles = fetch_all_feeds(feeds_config)
    print(f"  Found {len(articles)} articles from {len([f for f in feeds_config if f.get('enabled', True)])} feeds")

    if not articles:
        print("No articles found. Check your feed configuration.")
        return

    # Limit articles
    articles = articles[:max_articles]

    # Process with LLM
    if not args.no_summary:
        print(f"\n[2/3] Processing articles with LLM...")
        try:
            llm_config = config.get("llm", {})
            processor = LLMProcessor(llm_config)

            for i, article in enumerate(articles, 1):
                if not args.quiet:
                    print(f"  Processing {i}/{len(articles)}: {article.title[:50]}...")

                summary, relevance = processor.process_article(
                    article.title,
                    article.description,
                    topic
                )
                article.summary = summary
                article.relevance_score = relevance

        except ValueError as e:
            print(f"\nError: {e}")
            print("Skipping LLM processing. Articles will not have summaries or relevance scores.")
    else:
        print("\n[2/3] Skipping LLM processing (--no-summary flag)")
        # Set default relevance based on keyword matching
        for article in articles:
            text = (article.title + " " + article.description).lower()
            keywords = ["ai", "artificial intelligence", "machine learning", "ml", "llm", "neural", "gpt", "claude"]
            matches = sum(1 for kw in keywords if kw in text)
            article.relevance_score = min(1.0, matches * 0.2)

    # Filter by relevance threshold
    if not args.no_summary:
        filtered = [a for a in articles if a.relevance_score >= relevance_threshold]
        print(f"  {len(filtered)} articles meet relevance threshold ({relevance_threshold})")
        articles = filtered if filtered else articles[:5]

    # Generate digest
    print(f"\n[3/3] Generating markdown digest...")
    filepath = generate_digest(articles, topic, output_dir)
    print(f"  Saved to: {filepath}")

    # Print summary to console
    if not args.quiet:
        print_digest_summary(articles, topic)

    print(f"\nDone! Digest saved to: {filepath}")


if __name__ == "__main__":
    main()
