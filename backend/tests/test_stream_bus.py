"""Tests for Redis Stream message bus."""

import pytest
import redis.asyncio as aioredis

from app.core.redis import StreamBus


@pytest.fixture
async def redis_client():
    """Create a test Redis client."""
    client = aioredis.from_url("redis://localhost:6379/1", decode_responses=True)
    yield client
    # Cleanup test streams
    keys = [k async for k in client.scan_iter("test:*")]
    if keys:
        await client.delete(*keys)
    await client.aclose()


@pytest.fixture
def bus(redis_client):
    return StreamBus(redis=redis_client)


async def test_publish(bus, redis_client):
    msg_id = await bus.publish("test:stream", {"symbol": "AAPL", "price": 150.0})
    assert msg_id is not None
    length = await redis_client.xlen("test:stream")
    assert length == 1


async def test_publish_multiple(bus, redis_client):
    for i in range(5):
        await bus.publish("test:multi", {"index": i})
    length = await redis_client.xlen("test:multi")
    assert length == 5


async def test_stream_length(bus):
    for i in range(3):
        await bus.publish("test:len", {"i": i})
    length = await bus.stream_length("test:len")
    assert length == 3


async def test_subscribe_reads_messages(bus, redis_client):
    # Publish messages first
    await bus.publish("test:sub", {"msg": "hello"})
    await bus.publish("test:sub", {"msg": "world"})

    # Subscribe and read
    messages = []
    async for msg in bus.subscribe("test:sub", group="test-group", batch_size=10, block_ms=500):
        messages.append(msg["data"])
        if len(messages) >= 2:
            break

    assert len(messages) == 2
    assert messages[0]["msg"] == "hello"
    assert messages[1]["msg"] == "world"
