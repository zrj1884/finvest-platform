"""Redis client and Stream-based message bus."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

# Global Redis client (initialized on app startup)
redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get the global Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return redis_client


async def close_redis() -> None:
    """Close the global Redis client."""
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None


# --- Stream-based Message Bus (替代 Kafka) ---

class StreamBus:
    """Lightweight message bus built on Redis Streams.

    Usage:
        bus = StreamBus()

        # Produce
        await bus.publish("market:quotes", {"symbol": "AAPL", "price": 150.0})

        # Consume (in a background task)
        async for message in bus.subscribe("market:quotes", group="quote-processor"):
            process(message)
    """

    def __init__(self, redis: aioredis.Redis | None = None):
        self._redis = redis

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is not None:
            return self._redis
        return await get_redis()

    async def publish(self, stream: str, data: dict[str, Any], maxlen: int = 10000) -> str:
        """Publish a message to a stream.

        Args:
            stream: Stream name (e.g. "market:quotes", "news:articles")
            data: Message payload (will be JSON-serialized)
            maxlen: Max stream length (approximate trimming)

        Returns:
            Message ID
        """
        r = await self._get_redis()
        msg_id = await r.xadd(stream, {"data": json.dumps(data, default=str)}, maxlen=maxlen, approximate=True)
        return msg_id

    async def subscribe(
        self,
        stream: str,
        group: str,
        consumer: str = "worker-1",
        batch_size: int = 10,
        block_ms: int = 5000,
    ):
        """Subscribe to a stream using consumer groups.

        Creates the group if it doesn't exist. Yields messages one by one.

        Args:
            stream: Stream name
            group: Consumer group name
            consumer: Consumer name within the group
            batch_size: Number of messages to fetch per read
            block_ms: Block timeout in milliseconds (0 = forever)
        """
        r = await self._get_redis()

        # Create consumer group (ignore if exists)
        try:
            await r.xgroup_create(stream, group, id="0", mkstream=True)
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        while True:
            try:
                messages = await r.xreadgroup(
                    groupname=group,
                    consumername=consumer,
                    streams={stream: ">"},
                    count=batch_size,
                    block=block_ms,
                )

                if not messages:
                    continue

                for _stream_name, entries in messages:
                    for msg_id, fields in entries:
                        try:
                            payload = json.loads(fields.get("data", "{}"))
                            yield {"id": msg_id, "stream": stream, "data": payload}
                            # Acknowledge after successful processing
                            await r.xack(stream, group, msg_id)
                        except Exception:
                            logger.exception("Error processing message %s from %s", msg_id, stream)

            except aioredis.ConnectionError:
                logger.warning("Redis connection lost, reconnecting...")
                await _reconnect_delay()
            except Exception:
                logger.exception("Unexpected error in stream consumer")
                await _reconnect_delay()

    async def stream_info(self, stream: str) -> dict[str, Any]:
        """Get stream metadata (length, groups, etc.)."""
        r = await self._get_redis()
        try:
            info = await r.xinfo_stream(stream)
            return dict(info)
        except aioredis.ResponseError:
            return {}

    async def stream_length(self, stream: str) -> int:
        """Get the number of messages in a stream."""
        r = await self._get_redis()
        return await r.xlen(stream)


async def _reconnect_delay() -> None:
    """Wait before reconnecting."""
    await asyncio.sleep(2)


# Pre-defined stream names
class Streams:
    """Stream name constants."""
    QUOTES = "market:quotes"          # 实时行情
    QUOTES_DAILY = "market:daily"     # 日线数据
    NEWS = "news:articles"            # 新闻资讯
    SENTIMENT = "news:sentiment"      # 情感分析结果
    ORDERS = "trade:orders"           # 交易订单事件
    ALERTS = "system:alerts"          # 系统告警
