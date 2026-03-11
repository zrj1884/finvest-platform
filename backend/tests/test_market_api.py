"""Tests for market data query API endpoints."""

from typing import Any
from unittest.mock import patch

import pytest
from httpx import AsyncClient


class TestStockDailyAPI:
    @pytest.mark.asyncio
    async def test_get_stock_daily_empty(self, client: AsyncClient) -> None:
        """Test stock daily endpoint returns empty list when no data."""
        with patch("app.api.v1.market._get_cache", return_value=None), \
             patch("app.api.v1.market._set_cache", return_value=None):
            resp = await client.get("/api/v1/market/stocks/000001/daily?market=a_share&limit=10")

        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_get_stock_daily_cached(self, client: AsyncClient) -> None:
        """Test stock daily endpoint returns cached data."""
        cached_data: list[dict[str, Any]] = [
            {"time": "2025-01-02T00:00:00+08:00", "symbol": "000001", "close": 10.5}
        ]
        with patch("app.api.v1.market._get_cache", return_value=cached_data):
            resp = await client.get("/api/v1/market/stocks/000001/daily")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "000001"


class TestStockKlineAPI:
    @pytest.mark.asyncio
    async def test_get_kline_daily_empty(self, client: AsyncClient) -> None:
        with patch("app.api.v1.market._get_cache", return_value=None), \
             patch("app.api.v1.market._set_cache", return_value=None):
            resp = await client.get("/api/v1/market/stocks/000001/kline?period=daily&limit=10")

        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_get_kline_cached(self, client: AsyncClient) -> None:
        cached: list[list[Any]] = [
            ["2025-01-02T00:00:00", 10.0, 10.5, 9.8, 10.8, 100000]
        ]
        with patch("app.api.v1.market._get_cache", return_value=cached):
            resp = await client.get("/api/v1/market/stocks/000001/kline")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert len(data[0]) == 6


class TestFundNavAPI:
    @pytest.mark.asyncio
    async def test_get_fund_nav_empty(self, client: AsyncClient) -> None:
        with patch("app.api.v1.market._get_cache", return_value=None), \
             patch("app.api.v1.market._set_cache", return_value=None):
            resp = await client.get("/api/v1/market/funds/110011/nav?limit=10")

        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_get_fund_nav_cached(self, client: AsyncClient) -> None:
        cached = [{"time": "2025-01-02T00:00:00", "symbol": "110011", "nav": 1.5}]
        with patch("app.api.v1.market._get_cache", return_value=cached):
            resp = await client.get("/api/v1/market/funds/110011/nav")

        assert resp.status_code == 200
        assert resp.json()[0]["nav"] == 1.5


class TestBondDailyAPI:
    @pytest.mark.asyncio
    async def test_get_bond_daily_empty(self, client: AsyncClient) -> None:
        with patch("app.api.v1.market._get_cache", return_value=None), \
             patch("app.api.v1.market._set_cache", return_value=None):
            resp = await client.get("/api/v1/market/bonds/113050/daily?limit=10")

        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestNewsAPI:
    @pytest.mark.asyncio
    async def test_get_news_empty(self, client: AsyncClient) -> None:
        with patch("app.api.v1.market._get_cache", return_value=None), \
             patch("app.api.v1.market._set_cache", return_value=None):
            resp = await client.get("/api/v1/market/news?limit=10")

        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_get_news_cached(self, client: AsyncClient) -> None:
        cached = [
            {"time": "2025-01-02T00:00:00", "source": "sina_finance", "title": "Test News"}
        ]
        with patch("app.api.v1.market._get_cache", return_value=cached):
            resp = await client.get("/api/v1/market/news")

        assert resp.status_code == 200
        assert resp.json()[0]["source"] == "sina_finance"

    @pytest.mark.asyncio
    async def test_get_news_filter_source(self, client: AsyncClient) -> None:
        with patch("app.api.v1.market._get_cache", return_value=None), \
             patch("app.api.v1.market._set_cache", return_value=None):
            resp = await client.get("/api/v1/market/news?source=xueqiu&limit=5")

        assert resp.status_code == 200


class TestCacheHelpers:
    @pytest.mark.asyncio
    async def test_get_cache_returns_none_on_error(self) -> None:
        from app.api.v1.market import _get_cache
        with patch("app.api.v1.market.get_redis", side_effect=Exception("connection error")):
            result = await _get_cache("test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_cache_handles_error(self) -> None:
        from app.api.v1.market import _set_cache
        with patch("app.api.v1.market.get_redis", side_effect=Exception("connection error")):
            await _set_cache("test_key", {"data": 1}, 60)
