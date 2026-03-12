import api from './index'

export interface StockDaily {
  time: string
  symbol: string
  name: string | null
  market: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number | null
  turnover: number | null
  change_pct: number | null
  amplitude: number | null
}

export interface FundNav {
  time: string
  symbol: string
  name: string | null
  nav: number
  accumulated_nav: number | null
  daily_return: number | null
}

export interface BondDaily {
  time: string
  symbol: string
  name: string | null
  bond_type: string | null
  close: number
  volume: number
  amount: number | null
  ytm: number | null
  change_pct: number | null
}

export interface NewsArticle {
  time: string
  source: string
  url: string
  title: string
  content: string | null
  symbols: string | null
  sentiment_score: number | null
}

// K-line data: [time, open, close, low, high, volume]
export type KlineData = [string, number, number, number, number, number]

export async function getStockDaily(
  symbol: string,
  market = 'a_share',
  limit = 100,
  startDate?: string,
  endDate?: string,
): Promise<StockDaily[]> {
  const params: Record<string, string | number> = { market, limit }
  if (startDate) params.start_date = startDate
  if (endDate) params.end_date = endDate
  const { data } = await api.get<StockDaily[]>(`/v1/market/stocks/${symbol}/daily`, { params })
  return data
}

export async function getStockKline(
  symbol: string,
  market = 'a_share',
  period = 'daily',
  limit = 200,
): Promise<KlineData[]> {
  const { data } = await api.get<KlineData[]>(`/v1/market/stocks/${symbol}/kline`, {
    params: { market, period, limit },
  })
  return data
}

export async function getFundNav(symbol: string, limit = 100): Promise<FundNav[]> {
  const { data } = await api.get<FundNav[]>(`/v1/market/funds/${symbol}/nav`, {
    params: { limit },
  })
  return data
}

export async function getBondDaily(symbol: string, limit = 100): Promise<BondDaily[]> {
  const { data } = await api.get<BondDaily[]>(`/v1/market/bonds/${symbol}/daily`, {
    params: { limit },
  })
  return data
}

export async function getNews(
  limit = 50,
  source?: string,
  symbol?: string,
  keyword?: string,
): Promise<NewsArticle[]> {
  const params: Record<string, string | number> = { limit }
  if (source) params.source = source
  if (symbol) params.symbol = symbol
  if (keyword) params.keyword = keyword
  const { data } = await api.get<NewsArticle[]>('/v1/market/news', { params })
  return data
}
