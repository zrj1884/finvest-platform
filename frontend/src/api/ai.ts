import api from './index'

export interface ReportResponse {
  symbol: string
  market: string
  report_type: string
  title: string
  content_md: string
  generated_at: string
  tokens_used: number
  cost_usd: number
}

export interface UsageResponse {
  total_requests: number
  total_prompt_tokens: number
  total_completion_tokens: number
  total_cost_usd: number
}

export async function generateStockReport(
  symbol: string,
  market: string,
): Promise<ReportResponse> {
  const resp = await api.post<ReportResponse>('/v1/ai/report/stock', {
    symbol,
    market,
  })
  return resp.data
}

export async function generateIndustryReport(
  symbols: [string, string][],
  industryName: string = 'Industry Comparison',
): Promise<ReportResponse> {
  const resp = await api.post<ReportResponse>('/v1/ai/report/industry', {
    symbols,
    industry_name: industryName,
  })
  return resp.data
}

export async function getLLMUsage(): Promise<UsageResponse> {
  const resp = await api.get<UsageResponse>('/v1/ai/usage')
  return resp.data
}
