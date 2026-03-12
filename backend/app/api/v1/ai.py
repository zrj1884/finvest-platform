"""AI analysis API endpoints — sentiment analysis and research reports."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.llm.gateway import LLMGateway
from app.services.llm.sentiment import SentimentAnalyzer
from app.services.llm.research import ResearchReportGenerator

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


# --- Schemas ---

class SentimentRequest(BaseModel):
    limit: int = 50
    provider: str | None = None


class SentimentResponse(BaseModel):
    analyzed: int
    updated: int
    usage: dict | None = None  # type: ignore[type-arg]


class ReportRequest(BaseModel):
    symbol: str
    market: str
    provider: str | None = None


class IndustryReportRequest(BaseModel):
    symbols: list[list[str]]  # [[symbol, market], ...]
    industry_name: str = "Industry Comparison"
    provider: str | None = None


class ReportResponse(BaseModel):
    symbol: str
    market: str
    report_type: str
    title: str
    content_md: str
    generated_at: str
    tokens_used: int
    cost_usd: float


class UsageResponse(BaseModel):
    total_requests: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost_usd: float


# Shared gateway instance for usage tracking within a session
_gateway = LLMGateway()


# --- Endpoints ---

@router.post("/sentiment/analyze", response_model=SentimentResponse)
async def analyze_sentiment(
    req: SentimentRequest,
    db: AsyncSession = Depends(get_db),
) -> SentimentResponse:
    """Analyze sentiment for unscored news articles."""
    analyzer = SentimentAnalyzer(gateway=_gateway)
    try:
        result = await analyzer.analyze_and_store(db, limit=req.limit, provider=req.provider)
        return SentimentResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/report/stock", response_model=ReportResponse)
async def generate_stock_report(
    req: ReportRequest,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """Generate an AI investment research report for a stock."""
    generator = ResearchReportGenerator(gateway=_gateway)
    try:
        report = await generator.generate_stock_report(db, req.symbol, req.market, provider=req.provider)
        return ReportResponse(
            symbol=report.symbol,
            market=report.market,
            report_type=report.report_type,
            title=report.title,
            content_md=report.content_md,
            generated_at=report.generated_at.isoformat(),
            tokens_used=report.tokens_used,
            cost_usd=report.cost_usd,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/report/industry", response_model=ReportResponse)
async def generate_industry_report(
    req: IndustryReportRequest,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """Generate an AI industry comparison report."""
    symbols = [(s[0], s[1]) for s in req.symbols if len(s) == 2]
    if not symbols:
        raise HTTPException(status_code=400, detail="At least one [symbol, market] pair required")

    generator = ResearchReportGenerator(gateway=_gateway)
    try:
        report = await generator.generate_industry_report(
            db, symbols, req.industry_name, provider=req.provider,
        )
        return ReportResponse(
            symbol=report.symbol,
            market=report.market,
            report_type=report.report_type,
            title=report.title,
            content_md=report.content_md,
            generated_at=report.generated_at.isoformat(),
            tokens_used=report.tokens_used,
            cost_usd=report.cost_usd,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/usage", response_model=UsageResponse)
async def get_llm_usage() -> UsageResponse:
    """Get cumulative LLM API usage statistics."""
    summary = _gateway.usage.summary()
    return UsageResponse(
        total_requests=summary["total_requests"],
        total_prompt_tokens=summary["total_prompt_tokens"],
        total_completion_tokens=summary["total_completion_tokens"],
        total_cost_usd=summary["total_cost_usd"],
    )
