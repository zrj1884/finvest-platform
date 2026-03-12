import api from './index'

export interface AssetOverview {
  total_value: number
  total_balance: number
  total_market_value: number
  total_unrealized_pnl: number
  total_realized_pnl: number
  total_pnl: number
  total_pnl_pct: number
  account_count: number
}

export interface MarketAllocation {
  market: string
  market_value: number
  balance: number
  total_value: number
  percentage: number
  account_count: number
}

export interface HoldingItem {
  symbol: string
  name: string | null
  market: string
  account_name: string
  account_id: string
  quantity: number
  avg_cost: number
  current_price: number
  market_value: number
  unrealized_pnl: number
  unrealized_pnl_pct: number
  realized_pnl: number
}

export interface CashFlowItem {
  id: string
  account_name: string
  symbol: string
  side: string
  quantity: number
  price: number
  commission: number
  amount: number
  filled_at: string
}

export async function getOverview(): Promise<AssetOverview> {
  const resp = await api.get<AssetOverview>('/v1/portfolio/overview')
  return resp.data
}

export async function getAllocation(): Promise<MarketAllocation[]> {
  const resp = await api.get<MarketAllocation[]>('/v1/portfolio/allocation')
  return resp.data
}

export async function getHoldings(): Promise<HoldingItem[]> {
  const resp = await api.get<HoldingItem[]>('/v1/portfolio/holdings')
  return resp.data
}

export interface PerformancePoint {
  date: string
  total_value: number
}

export async function getPerformance(days?: number): Promise<PerformancePoint[]> {
  const resp = await api.get<PerformancePoint[]>('/v1/portfolio/performance', {
    params: { days },
  })
  return resp.data
}

export async function getCashFlows(limit?: number): Promise<CashFlowItem[]> {
  const resp = await api.get<CashFlowItem[]>('/v1/portfolio/cash-flows', {
    params: { limit },
  })
  return resp.data
}
