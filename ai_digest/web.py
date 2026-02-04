"""Web UI for AI News Digest."""

import json
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash

from .cli import load_config, run_pipeline
from .digest import generate_digest, group_articles
from .scraper import Article


def create_app(config_path: str = "config.yaml") -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.secret_key = os.urandom(24)

    config = load_config(config_path)

    @app.route("/")
    def index():
        """Home page: list available digests."""
        output_dir = config.get("digest", {}).get("output_dir", "./digests")
        digests = _list_digests(output_dir)
        feeds = config.get("feeds", [])
        return render_template(
            "index.html",
            digests=digests,
            feeds=feeds,
            topic=config.get("topic", "AI and machine learning"),
        )

    @app.route("/digest/<date>")
    def view_digest(date: str):
        """View a specific digest by date."""
        output_dir = config.get("digest", {}).get("output_dir", "./digests")
        json_path = os.path.join(output_dir, f"digest_{date}.json")

        if not os.path.exists(json_path):
            flash(f"Digest for {date} not found.")
            return redirect(url_for("index"))

        with open(json_path, "r") as f:
            data = json.load(f)

        articles = _articles_from_json(data["articles"])
        groups = group_articles(articles)
        return render_template(
            "digest.html",
            date=date,
            topic=data.get("topic", ""),
            groups=groups,
            total=len(articles),
        )

    @app.route("/generate", methods=["POST"])
    def generate():
        """Trigger new digest generation."""
        skip_llm = "skip_llm" in request.form
        articles = run_pipeline(config, skip_llm=skip_llm, quiet=True)

        if not articles:
            flash("No articles found. Check your feed configuration.")
            return redirect(url_for("index"))

        topic = config.get("topic", "AI and machine learning")
        output_dir = config.get("digest", {}).get("output_dir", "./digests")
        generate_digest(articles, topic, output_dir)

        date_str = datetime.now().strftime("%Y-%m-%d")
        flash(f"Digest generated for {date_str}.")
        return redirect(url_for("view_digest", date=date_str))

    @app.route("/feeds")
    def feeds():
        """View configured RSS feeds."""
        feed_list = config.get("feeds", [])
        return render_template("feeds.html", feeds=feed_list)

    return app


def _list_digests(output_dir: str) -> list[dict]:
    """List available digests from the output directory."""
    digests = []
    path = Path(output_dir)
    if not path.exists():
        return digests

    for json_file in sorted(path.glob("digest_*.json"), reverse=True):
        date = json_file.stem.replace("digest_", "")
        with open(json_file, "r") as f:
            data = json.load(f)
        digests.append({
            "date": date,
            "topic": data.get("topic", ""),
            "article_count": len(data.get("articles", [])),
        })
    return digests


def _articles_from_json(articles_data: list[dict]) -> list[Article]:
    """Reconstruct Article objects from JSON data."""
    articles = []
    for a in articles_data:
        published = None
        if a.get("published"):
            try:
                published = datetime.fromisoformat(a["published"])
            except (ValueError, TypeError):
                pass
        articles.append(Article(
            title=a["title"],
            link=a["link"],
            source=a["source"],
            published=published,
            description=a.get("description", ""),
            summary=a.get("summary", ""),
            relevance_score=a.get("relevance_score", 0.0),
        ))
    return articles
