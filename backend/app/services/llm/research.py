"""AI Investment Research Report Generator.

Agent workflow: data collection → analysis → report generation.
Outputs Markdown / HTML reports for individual stocks and industry comparisons.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm.gateway import LLMGateway

logger = logging.getLogger(__name__)

STOCK_REPORT_SYSTEM = """You are a professional financial analyst at a top investment bank.
Write investment research reports in Markdown format.
Be data-driven, objective, and clear. Include:
1. Executive Summary (2-3 sentences)
2. Price & Technical Analysis
3. Fundamental Analysis
4. Market Sentiment
5. Risk Factors
6. Investment Recommendation (Buy/Hold/Sell with target price range)

Use the data provided. Do not fabricate numbers."""

INDUSTRY_REPORT_SYSTEM = """You are a senior industry analyst.
Write an industry comparison report in Markdown format comparing the provided stocks.
Include:
1. Industry Overview
2. Comparative Metrics Table (PE, PB, ROE, market cap)
3. Competitive Analysis
4. Growth Outlook
5. Top Pick Recommendation

Use the data provided. Do not fabricate numbers."""


@dataclass
class ResearchReport:
    """Generated research report."""

    symbol: str
    market: str
    report_type: str  # "stock" or "industry"
    title: str
    content_md: str
    generated_at: datetime
    llm_provider: str
    llm_model: str
    tokens_used: int
    cost_usd: float


class ResearchReportGenerator:
    """Generate AI investment research reports."""

    def __init__(self, gateway: LLMGateway | None = None) -> None:
        self.gateway = gateway or LLMGateway()

    async def generate_stock_report(
        self,
        db: AsyncSession,
        symbol: str,
        market: str,
        provider: str | None = None,
    ) -> ResearchReport:
        """Generate a comprehensive stock analysis report.

        Collects data from DB, feeds to LLM, returns structured report.
        """
        # 1. Collect data
        data = await self._collect_stock_data(db, symbol, market)

        # 2. Build prompt
        prompt = self._build_stock_prompt(symbol, market, data)

        # 3. Generate report via LLM
        resp = await self.gateway.complete(
            prompt=prompt,
            system=STOCK_REPORT_SYSTEM,
            provider=provider,
            temperature=0.4,
            max_tokens=4000,
        )

        title = f"Investment Analysis: {symbol} ({market})"

        return ResearchReport(
            symbol=symbol,
            market=market,
            report_type="stock",
            title=title,
            content_md=resp.content,
            generated_at=datetime.now(timezone.utc),
            llm_provider=resp.provider,
            llm_model=resp.model,
            tokens_used=resp.total_tokens,
            cost_usd=resp.cost_usd,
        )

    async def generate_industry_report(
        self,
        db: AsyncSession,
        symbols: list[tuple[str, str]],
        industry_name: str = "Comparison",
        provider: str | None = None,
    ) -> ResearchReport:
        """Generate an industry comparison report for multiple stocks."""
        # Collect data for all symbols
        all_data: list[dict[str, Any]] = []
        for sym, mkt in symbols:
            data = await self._collect_stock_data(db, sym, mkt)
            data["symbol"] = sym
            data["market"] = mkt
            all_data.append(data)

        prompt = self._build_industry_prompt(industry_name, all_data)

        resp = await self.gateway.complete(
            prompt=prompt,
            system=INDUSTRY_REPORT_SYSTEM,
            provider=provider,
            temperature=0.4,
            max_tokens=4000,
        )

        sym_list = ", ".join(s for s, _ in symbols)
        title = f"Industry Report: {industry_name} ({sym_list})"

        return ResearchReport(
            symbol=sym_list,
            market="mixed",
            report_type="industry",
            title=title,
            content_md=resp.content,
            generated_at=datetime.now(timezone.utc),
            llm_provider=resp.provider,
            llm_model=resp.model,
            tokens_used=resp.total_tokens,
            cost_usd=resp.cost_usd,
        )

    async def _collect_stock_data(
        self,
        db: AsyncSession,
        symbol: str,
        market: str,
    ) -> dict[str, Any]:
        """Collect stock data from DB for report generation."""
        data: dict[str, Any] = {"symbol": symbol, "market": market}

        # Recent price data (last 30 days)
        price_query = text("""
            SELECT time, open, high, low, close, volume, change_pct
            FROM stock_daily
            WHERE symbol = :symbol AND market = :market
            ORDER BY time DESC
            LIMIT 30
        """)
        result = await db.execute(price_query, {"symbol": symbol, "market": market})
        rows = result.fetchall()
        if rows:
            latest = rows[0]
            data["latest_price"] = {
                "date": str(latest[0]),
                "open": float(latest[1]),
                "high": float(latest[2]),
                "low": float(latest[3]),
                "close": float(latest[4]),
                "volume": int(latest[5]),
                "change_pct": float(latest[6]) if latest[6] else None,
            }
            data["price_30d"] = [
                {"date": str(r[0]), "close": float(r[4]), "volume": int(r[5])}
                for r in rows
            ]

        # Latest features (technical + fundamental)
        feature_query = text("""
            SELECT ma5, ma10, ma20, ma60, macd, macd_signal, rsi_14,
                   kdj_k, kdj_d, kdj_j, boll_upper, boll_mid, boll_lower,
                   pe_ttm, pb, ps_ttm, total_mv, roe, revenue_yoy, profit_yoy
            FROM stock_features
            WHERE symbol = :symbol AND market = :market
            ORDER BY time DESC
            LIMIT 1
        """)
        result = await db.execute(feature_query, {"symbol": symbol, "market": market})
        feat_row = result.fetchone()
        if feat_row:
            cols = [
                "ma5", "ma10", "ma20", "ma60", "macd", "macd_signal", "rsi_14",
                "kdj_k", "kdj_d", "kdj_j", "boll_upper", "boll_mid", "boll_lower",
                "pe_ttm", "pb", "ps_ttm", "total_mv", "roe", "revenue_yoy", "profit_yoy",
            ]
            data["features"] = {
                col: float(val) if val is not None else None
                for col, val in zip(cols, feat_row)
            }

        # Recent news sentiment
        news_query = text("""
            SELECT title, sentiment_score, time
            FROM news_articles
            WHERE (symbols LIKE :pattern OR symbols IS NULL)
            ORDER BY time DESC
            LIMIT 10
        """)
        result = await db.execute(news_query, {"pattern": f"%{symbol}%"})
        news_rows = result.fetchall()
        if news_rows:
            data["recent_news"] = [
                {
                    "title": r[0],
                    "sentiment": float(r[1]) if r[1] else None,
                    "date": str(r[2]),
                }
                for r in news_rows
            ]

        return data

    @staticmethod
    def _build_stock_prompt(symbol: str, market: str, data: dict[str, Any]) -> str:
        """Build the stock analysis prompt from collected data."""
        sections: list[str] = [f"## Stock: {symbol} (Market: {market})\n"]

        if "latest_price" in data:
            p = data["latest_price"]
            sections.append(f"### Latest Price Data\n"
                            f"- Date: {p['date']}\n"
                            f"- Close: {p['close']}\n"
                            f"- Change: {p.get('change_pct', 'N/A')}%\n"
                            f"- Volume: {p['volume']:,}\n")

        if "features" in data:
            f = data["features"]
            tech_map = {"ma5": "MA5", "ma20": "MA20", "ma60": "MA60"}
            tech = [f"{label}={f[k]:.2f}" for k, label in tech_map.items() if f.get(k)]
            if f.get("rsi_14"):
                tech.append(f"RSI(14)={f['rsi_14']:.1f}")
            if f.get("macd"):
                tech.append(f"MACD={f['macd']:.4f}")
            if tech:
                sections.append(f"### Technical Indicators\n{', '.join(tech)}\n")

            fund_map = {
                "pe_ttm": ("PE(TTM)", ".2f"),
                "pb": ("PB", ".2f"),
                "roe": ("ROE", ".2f%"),
                "total_mv": ("Market Cap", ".0f亿"),
                "revenue_yoy": ("Revenue YoY", ".2f%"),
            }
            fund = []
            for key, (label, fmt) in fund_map.items():
                if f.get(key):
                    if fmt.endswith("%"):
                        fund.append(f"{label}={f[key]:{fmt[:-1]}}%")
                    elif fmt.endswith("亿"):
                        fund.append(f"{label}={f[key]:{fmt[:-1]}}亿")
                    else:
                        fund.append(f"{label}={f[key]:{fmt}}")
            if fund:
                sections.append(f"### Fundamental Data\n{', '.join(fund)}\n")

        if "recent_news" in data:
            news_lines = []
            for n in data["recent_news"][:5]:
                sent = f" (sentiment: {n['sentiment']:.2f})" if n.get("sentiment") is not None else ""
                news_lines.append(f"- {n['title']}{sent}")
            sections.append("### Recent News\n" + "\n".join(news_lines) + "\n")

        sections.append("\nPlease write a comprehensive investment analysis report based on the above data.")
        return "\n".join(sections)

    @staticmethod
    def _build_industry_prompt(industry_name: str, all_data: list[dict[str, Any]]) -> str:
        """Build industry comparison prompt."""
        sections: list[str] = [f"## Industry: {industry_name}\n"]

        for data in all_data:
            sym = data.get("symbol", "?")
            mkt = data.get("market", "?")
            sections.append(f"### {sym} ({mkt})")

            if "latest_price" in data:
                p = data["latest_price"]
                sections.append(f"Price: {p['close']}, Change: {p.get('change_pct', 'N/A')}%")

            if "features" in data:
                f = data["features"]
                ind_map = {"pe_ttm": "PE", "pb": "PB", "roe": "ROE", "total_mv": "MktCap"}
                metrics = []
                for k, label in ind_map.items():
                    if f.get(k):
                        if k == "total_mv":
                            metrics.append(f"{label}={f[k]:.0f}亿")
                        elif k == "roe":
                            metrics.append(f"{label}={f[k]:.2f}%")
                        else:
                            metrics.append(f"{label}={f[k]:.2f}")
                if metrics:
                    sections.append(", ".join(metrics))
            sections.append("")

        sections.append("\nPlease write an industry comparison report based on the above data.")
        return "\n".join(sections)
