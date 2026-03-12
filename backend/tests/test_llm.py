"""Tests for LLM gateway, sentiment analysis, and research reports."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm.gateway import LLMGateway, LLMResponse, UsageTracker, ProviderConfig
from app.services.llm.sentiment import SentimentAnalyzer
from app.services.llm.research import ResearchReportGenerator


# ===== Gateway =====

class TestUsageTracker:
    def test_record(self) -> None:
        tracker = UsageTracker()
        resp = LLMResponse(
            content="test", model="m", provider="deepseek",
            prompt_tokens=100, completion_tokens=50, total_tokens=150,
            cost_usd=0.001,
        )
        tracker.record(resp)
        assert tracker.total_requests == 1
        assert tracker.total_prompt_tokens == 100
        assert tracker.total_cost_usd == 0.001

    def test_multiple_records(self) -> None:
        tracker = UsageTracker()
        for _ in range(3):
            resp = LLMResponse(
                content="x", model="m", provider="deepseek",
                prompt_tokens=10, completion_tokens=5, total_tokens=15,
                cost_usd=0.0001,
            )
            tracker.record(resp)
        assert tracker.total_requests == 3
        assert tracker.total_prompt_tokens == 30
        summary = tracker.summary()
        assert summary["total_requests"] == 3
        assert "deepseek" in summary["by_provider"]

    def test_multi_provider(self) -> None:
        tracker = UsageTracker()
        tracker.record(LLMResponse(content="a", model="m", provider="deepseek",
                                   prompt_tokens=10, completion_tokens=5, total_tokens=15, cost_usd=0.001))
        tracker.record(LLMResponse(content="b", model="m", provider="qwen",
                                   prompt_tokens=20, completion_tokens=10, total_tokens=30, cost_usd=0.002))
        summary = tracker.summary()
        assert len(summary["by_provider"]) == 2


class TestLLMGateway:
    def test_init_default(self) -> None:
        with patch("app.services.llm.gateway.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "deepseek"
            mock_settings.DEEPSEEK_API_KEY = "sk-test"
            mock_settings.DEEPSEEK_BASE_URL = "https://api.deepseek.com"
            mock_settings.DEEPSEEK_MODEL = "deepseek-chat"
            mock_settings.QWEN_API_KEY = ""
            mock_settings.QWEN_BASE_URL = ""
            mock_settings.QWEN_MODEL = ""
            mock_settings.OPENAI_API_KEY = ""
            mock_settings.OPENAI_BASE_URL = ""
            mock_settings.OPENAI_MODEL = ""
            gw = LLMGateway()
            assert gw.provider == "deepseek"

    def test_get_config_invalid(self) -> None:
        gw = LLMGateway(provider="deepseek")
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            gw._get_config("nonexistent")

    @pytest.mark.asyncio
    async def test_chat_no_api_key(self) -> None:
        gw = LLMGateway(provider="deepseek")
        # Override config to have empty key
        gw._configs["deepseek"] = ProviderConfig(
            api_key="", base_url="https://test", model="test",
        )
        with pytest.raises(ValueError, match="API key not configured"):
            await gw.chat([{"role": "user", "content": "test"}])

    @pytest.mark.asyncio
    async def test_chat_success(self) -> None:
        gw = LLMGateway(provider="deepseek")
        gw._configs["deepseek"] = ProviderConfig(
            api_key="sk-test", base_url="https://test.com",
            model="test-model", cost_per_m_input=0.14, cost_per_m_output=0.28,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post = AsyncMock(return_value=mock_response)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = instance

            result = await gw.chat([{"role": "user", "content": "test"}])

        assert result.content == "Hello!"
        assert result.total_tokens == 15
        assert result.cost_usd > 0
        assert gw.usage.total_requests == 1

    @pytest.mark.asyncio
    async def test_complete(self) -> None:
        gw = LLMGateway(provider="deepseek")
        gw._configs["deepseek"] = ProviderConfig(
            api_key="sk-test", base_url="https://test.com", model="test",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Analysis result"}}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post = AsyncMock(return_value=mock_response)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = instance

            result = await gw.complete("Analyze this stock")

        assert result.content == "Analysis result"


# ===== Sentiment =====

class TestSentimentParser:
    def test_parse_valid_json(self) -> None:
        scores = SentimentAnalyzer._parse_scores("[0.5, -0.3, 0.0]", 3)
        assert scores == [0.5, -0.3, 0.0]

    def test_parse_with_code_block(self) -> None:
        content = "```json\n[0.8, -0.2]\n```"
        scores = SentimentAnalyzer._parse_scores(content, 2)
        assert scores == [0.8, -0.2]

    def test_parse_invalid(self) -> None:
        scores = SentimentAnalyzer._parse_scores("invalid response", 3)
        assert scores == [None, None, None]

    def test_parse_out_of_range(self) -> None:
        scores = SentimentAnalyzer._parse_scores("[0.5, 2.0, -0.3]", 3)
        assert scores[0] == 0.5
        assert scores[1] is None  # 2.0 out of range
        assert scores[2] == -0.3

    def test_parse_padding(self) -> None:
        scores = SentimentAnalyzer._parse_scores("[0.5]", 3)
        assert len(scores) == 3
        assert scores[0] == 0.5
        assert scores[1] is None
        assert scores[2] is None

    def test_parse_trimming(self) -> None:
        scores = SentimentAnalyzer._parse_scores("[0.1, 0.2, 0.3, 0.4]", 2)
        assert len(scores) == 2


class TestSentimentAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_batch(self) -> None:
        mock_gw = AsyncMock(spec=LLMGateway)
        mock_gw.complete = AsyncMock(return_value=LLMResponse(
            content="[0.5, -0.3]", model="m", provider="p",
        ))
        analyzer = SentimentAnalyzer(gateway=mock_gw)

        articles = [{"title": "Good news"}, {"title": "Bad news"}]
        scores = await analyzer.analyze_batch(articles)
        assert scores == [0.5, -0.3]

    @pytest.mark.asyncio
    async def test_analyze_batch_error(self) -> None:
        mock_gw = AsyncMock(spec=LLMGateway)
        mock_gw.complete = AsyncMock(side_effect=RuntimeError("API error"))
        analyzer = SentimentAnalyzer(gateway=mock_gw)

        articles = [{"title": "test1"}, {"title": "test2"}]
        scores = await analyzer.analyze_batch(articles)
        assert scores == [None, None]


# ===== Research =====

class TestResearchReportGenerator:
    @pytest.mark.asyncio
    async def test_generate_stock_report(self) -> None:
        mock_gw = AsyncMock(spec=LLMGateway)
        mock_gw.complete = AsyncMock(return_value=LLMResponse(
            content="# Stock Report\nThis is a test report.",
            model="test-model", provider="deepseek",
            prompt_tokens=100, completion_tokens=200, total_tokens=300,
            cost_usd=0.001,
        ))

        # Mock DB
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_result.fetchone.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        generator = ResearchReportGenerator(gateway=mock_gw)
        report = await generator.generate_stock_report(mock_db, "000001", "a_share")

        assert report.report_type == "stock"
        assert report.symbol == "000001"
        assert "Stock Report" in report.content_md
        assert report.tokens_used == 300

    @pytest.mark.asyncio
    async def test_generate_industry_report(self) -> None:
        mock_gw = AsyncMock(spec=LLMGateway)
        mock_gw.complete = AsyncMock(return_value=LLMResponse(
            content="# Industry Comparison\nBanking sector analysis.",
            model="test", provider="deepseek",
            prompt_tokens=200, completion_tokens=400, total_tokens=600,
            cost_usd=0.002,
        ))

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_result.fetchone.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        generator = ResearchReportGenerator(gateway=mock_gw)
        report = await generator.generate_industry_report(
            mock_db, [("000001", "a_share"), ("601318", "a_share")], "Banking",
        )

        assert report.report_type == "industry"
        assert "Industry Comparison" in report.content_md
        assert report.tokens_used == 600

    def test_build_stock_prompt(self) -> None:
        data = {
            "symbol": "000001",
            "market": "a_share",
            "latest_price": {
                "date": "2025-01-01",
                "open": 10.0, "high": 10.5, "low": 9.8,
                "close": 10.2, "volume": 1000000,
                "change_pct": 1.5,
            },
            "features": {
                "ma5": 10.1, "ma20": 10.0, "ma60": 9.8,
                "rsi_14": 55.0, "macd": 0.05,
                "pe_ttm": 8.5, "pb": 0.8, "roe": 12.5,
                "total_mv": 2000, "revenue_yoy": 15.0,
            },
        }
        prompt = ResearchReportGenerator._build_stock_prompt("000001", "a_share", data)
        assert "000001" in prompt
        assert "10.2" in prompt
        assert "RSI(14)=55.0" in prompt
        assert "PE(TTM)=8.50" in prompt
