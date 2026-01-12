# AI News Digest

A Python CLI tool that scrapes RSS feeds from AI/ML news sources, uses an LLM to summarize articles and rank them by relevance, and outputs a daily markdown digest.

## Features

- Scrapes multiple RSS feeds (The Verge AI, MIT Tech Review, Hacker News, etc.)
- LLM-powered article summarization (2-3 sentences per article)
- Relevance ranking based on configurable topics
- Outputs formatted markdown digest files
- Configurable via YAML file

## Installation

```bash
# Clone or download the project
cd ai-digest

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

## Configuration

Edit `config.yaml` to customize:

### RSS Feeds

```yaml
feeds:
  - name: "The Verge AI"
    url: "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"
    enabled: true

  - name: "Custom Feed"
    url: "https://example.com/feed.xml"
    enabled: true
```

### LLM Settings

```yaml
llm:
  provider: "openai"  # or "anthropic"
  model: "gpt-4o-mini"
  api_key_env: "OPENAI_API_KEY"
```

### Digest Settings

```yaml
digest:
  max_articles: 20
  output_dir: "./digests"
  relevance_threshold: 0.3

topic: "AI and machine learning"
```

## Usage

Set your API key:

```bash
export OPENAI_API_KEY="your-api-key"
# or for Anthropic
export ANTHROPIC_API_KEY="your-api-key"
```

Run the digest:

```bash
# Using the CLI
python -m ai_digest

# Or if installed as a package
ai-digest
```

### CLI Options

```
-c, --config       Path to config file (default: config.yaml)
-o, --output       Output directory for digest
--max-articles     Maximum articles to process
--no-summary       Skip LLM summarization
--list-feeds       List configured feeds
--quiet            Suppress progress output
-v, --verbose      Enable verbose output
```

### Examples

```bash
# Run with default settings
python -m ai_digest

# Use custom config
python -m ai_digest -c my-config.yaml

# Limit to 10 articles
python -m ai_digest --max-articles 10

# Skip LLM processing (keyword-based ranking only)
python -m ai_digest --no-summary

# List configured feeds
python -m ai_digest --list-feeds
```

## Output

The tool generates markdown files in the `digests/` directory:

```
digests/
  digest_2024-01-15.md
  digest_2024-01-16.md
  ...
```

Each digest includes:
- Articles grouped by relevance tier (Highly Relevant, Related, Other)
- Source attribution and publication dates
- LLM-generated summaries
- Relevance scores

## Adding Custom Feeds

Edit `config.yaml` to add or remove RSS feeds:

```yaml
feeds:
  - name: "My Custom Source"
    url: "https://example.com/rss.xml"
    enabled: true
```

Set `enabled: false` to temporarily disable a feed without removing it.

## Requirements

- Python 3.10+
- OpenAI or Anthropic API key
