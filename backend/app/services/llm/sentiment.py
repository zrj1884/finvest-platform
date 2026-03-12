"""News sentiment analysis via LLM API.

Batch-analyses news articles and writes sentiment scores back to the database.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm.gateway import LLMGateway

logger = logging.getLogger(__name__)

SENTIMENT_SYSTEM_PROMPT = """You are a financial sentiment analysis expert.
Analyze the sentiment of financial news articles.
For each article, return a score from -1.0 (very bearish) to 1.0 (very bullish).
0.0 means neutral.

Return ONLY a JSON array of numbers, one per article. Example: [-0.5, 0.8, 0.0]
Do not include any other text."""

BATCH_SIZE = 10  # Articles per LLM call


class SentimentAnalyzer:
    """Analyze news sentiment using LLM API calls."""

    def __init__(self, gateway: LLMGateway | None = None) -> None:
        self.gateway = gateway or LLMGateway()

    async def analyze_batch(
        self,
        articles: list[dict[str, str]],
        provider: str | None = None,
    ) -> list[float | None]:
        """Analyze sentiment for a batch of articles.

        Args:
            articles: List of dicts with 'title' and optionally 'content' keys.
            provider: LLM provider override.

        Returns:
            List of sentiment scores (-1.0 to 1.0), None for failures.
        """
        results: list[float | None] = []

        for i in range(0, len(articles), BATCH_SIZE):
            batch = articles[i : i + BATCH_SIZE]
            scores = await self._analyze_chunk(batch, provider)
            results.extend(scores)

        return results

    async def _analyze_chunk(
        self,
        articles: list[dict[str, str]],
        provider: str | None = None,
    ) -> list[float | None]:
        """Analyze a single chunk of articles."""
        # Build prompt
        article_texts = []
        for idx, art in enumerate(articles, 1):
            title = art.get("title", "")
            content = art.get("content", "")
            snippet = content[:200] if content else ""
            article_texts.append(f"{idx}. {title}\n{snippet}")

        prompt = f"Analyze the sentiment of these {len(articles)} financial news articles:\n\n"
        prompt += "\n\n".join(article_texts)

        try:
            resp = await self.gateway.complete(
                prompt=prompt,
                system=SENTIMENT_SYSTEM_PROMPT,
                provider=provider,
                temperature=0.1,
                max_tokens=500,
            )
            return self._parse_scores(resp.content, len(articles))
        except Exception:
            logger.error("Sentiment analysis failed for batch of %d articles", len(articles), exc_info=True)
            return [None] * len(articles)

    @staticmethod
    def _parse_scores(content: str, expected_count: int) -> list[float | None]:
        """Parse LLM response into a list of float scores."""
        # Try to extract JSON array from response
        content = content.strip()
        # Handle markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if len(lines) > 2 else content

        try:
            scores = json.loads(content)
            if isinstance(scores, list):
                result: list[float | None] = []
                for s in scores:
                    if isinstance(s, (int, float)) and -1.0 <= float(s) <= 1.0:
                        result.append(round(float(s), 2))
                    else:
                        result.append(None)
                # Pad or trim to expected count
                while len(result) < expected_count:
                    result.append(None)
                return result[:expected_count]
        except (json.JSONDecodeError, TypeError):
            pass

        logger.warning("Failed to parse sentiment scores from LLM response: %s", content[:200])
        return [None] * expected_count

    async def analyze_and_store(
        self,
        db: AsyncSession,
        limit: int = 50,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Fetch unscored news, analyze sentiment, update DB.

        Returns:
            Dict with stats: analyzed, updated, errors.
        """
        # Fetch articles without sentiment scores
        query = text("""
            SELECT url, source, time, title, content
            FROM news_articles
            WHERE sentiment_score IS NULL
            ORDER BY time DESC
            LIMIT :limit
        """)
        result = await db.execute(query, {"limit": limit})
        rows = result.fetchall()

        if not rows:
            return {"analyzed": 0, "updated": 0}

        articles = [{"title": row[3], "content": row[4] or ""} for row in rows]
        scores = await self.analyze_batch(articles, provider=provider)

        # Update sentiment scores in DB
        updated = 0
        for row, score in zip(rows, scores):
            if score is not None:
                update_stmt = text("""
                    UPDATE news_articles
                    SET sentiment_score = :score
                    WHERE url = :url AND source = :source AND time = :time
                """)
                await db.execute(update_stmt, {
                    "score": score,
                    "url": row[0],
                    "source": row[1],
                    "time": row[2],
                })
                updated += 1

        logger.info("Sentiment analysis: %d articles analyzed, %d updated", len(articles), updated)
        return {
            "analyzed": len(articles),
            "updated": updated,
            "usage": self.gateway.usage.summary(),
        }
