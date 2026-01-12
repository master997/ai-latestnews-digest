"""LLM integration module for summarization and relevance ranking."""

import os
import json
from typing import Optional


def get_openai_client(api_key: str):
    """Get OpenAI client."""
    from openai import OpenAI
    return OpenAI(api_key=api_key)


def get_anthropic_client(api_key: str):
    """Get Anthropic client."""
    from anthropic import Anthropic
    return Anthropic(api_key=api_key)


def summarize_and_rank_openai(
    client,
    model: str,
    title: str,
    description: str,
    topic: str
) -> tuple[str, float]:
    """
    Summarize article and calculate relevance using OpenAI.

    Returns:
        Tuple of (summary, relevance_score)
    """
    prompt = f"""Analyze this article and provide:
1. A concise 2-3 sentence summary
2. A relevance score from 0.0 to 1.0 for the topic "{topic}"

Article Title: {title}
Article Description: {description}

Respond in JSON format:
{{"summary": "your summary here", "relevance": 0.8}}"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
        )

        content = response.choices[0].message.content.strip()
        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        result = json.loads(content)
        summary = result.get("summary", "")
        relevance = float(result.get("relevance", 0.0))
        relevance = max(0.0, min(1.0, relevance))

        return summary, relevance

    except Exception as e:
        print(f"    Error in OpenAI call: {e}")
        return "", 0.0


def summarize_and_rank_anthropic(
    client,
    model: str,
    title: str,
    description: str,
    topic: str
) -> tuple[str, float]:
    """
    Summarize article and calculate relevance using Anthropic.

    Returns:
        Tuple of (summary, relevance_score)
    """
    prompt = f"""Analyze this article and provide:
1. A concise 2-3 sentence summary
2. A relevance score from 0.0 to 1.0 for the topic "{topic}"

Article Title: {title}
Article Description: {description}

Respond in JSON format only, no other text:
{{"summary": "your summary here", "relevance": 0.8}}"""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text.strip()
        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        result = json.loads(content)
        summary = result.get("summary", "")
        relevance = float(result.get("relevance", 0.0))
        relevance = max(0.0, min(1.0, relevance))

        return summary, relevance

    except Exception as e:
        print(f"    Error in Anthropic call: {e}")
        return "", 0.0


class LLMProcessor:
    """Handles LLM-based summarization and relevance ranking."""

    def __init__(self, config: dict):
        """
        Initialize LLM processor with configuration.

        Args:
            config: LLM configuration dictionary
        """
        self.provider = config.get("provider", "openai")
        self.model = config.get("model", "gpt-4o-mini")
        api_key_env = config.get("api_key_env", "OPENAI_API_KEY")

        self.api_key = os.environ.get(api_key_env)
        if not self.api_key:
            raise ValueError(
                f"API key not found. Set the {api_key_env} environment variable."
            )

        self.client = None

    def _get_client(self):
        """Lazily initialize the API client."""
        if self.client is None:
            if self.provider == "openai":
                self.client = get_openai_client(self.api_key)
            elif self.provider == "anthropic":
                self.client = get_anthropic_client(self.api_key)
            else:
                raise ValueError(f"Unknown LLM provider: {self.provider}")
        return self.client

    def process_article(
        self,
        title: str,
        description: str,
        topic: str
    ) -> tuple[str, float]:
        """
        Summarize article and calculate relevance score.

        Args:
            title: Article title
            description: Article description/content
            topic: Topic for relevance scoring

        Returns:
            Tuple of (summary, relevance_score)
        """
        client = self._get_client()

        # Use description or title if description is empty
        text = description if description else title

        if self.provider == "openai":
            return summarize_and_rank_openai(
                client, self.model, title, text, topic
            )
        elif self.provider == "anthropic":
            return summarize_and_rank_anthropic(
                client, self.model, title, text, topic
            )
        else:
            return "", 0.0
