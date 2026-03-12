import api from './index'

// --- Types ---

export interface Account {
  id: string
  user_id: string
  name: string
  market: string
  broker: string | null
  account_no: string | null
  balance: number
  is_simulated: boolean
  created_at: string
}

export interface Position {
  id: string
  account_id: string
  symbol: string
  name: string | null
  quantity: number
  available_quantity: number
  avg_cost: number
  current_price: number
  market_value: number
  unrealized_pnl: number
  realized_pnl: number
  updated_at: string
}

export interface OrderRecord {
  id: string
  account_id: string
  symbol: string
  name: string | null
  side: string
  order_type: string
  status: string
  quantity: number
  filled_quantity: number
  price: number | null
  filled_price: number | null
  commission: number
  submitted_at: string | null
  filled_at: string | null
  cancelled_at: string | null
  remark: string | null
  created_at: string
}

export interface OrderCreateRequest {
  account_id: string
  symbol: string
  side: 'buy' | 'sell'
  order_type: 'market' | 'limit'
  quantity: number
  price?: number
  remark?: string
}

export interface AccountCreateRequest {
  name: string
  market: string
  is_simulated?: boolean
  balance?: number
}

// --- Account APIs ---

export async function createAccount(data: AccountCreateRequest): Promise<Account> {
  const resp = await api.post<Account>('/v1/accounts', data)
  return resp.data
}

export async function listAccounts(): Promise<Account[]> {
  const resp = await api.get<Account[]>('/v1/accounts')
  return resp.data
}

export async function getAccount(id: string): Promise<Account> {
  const resp = await api.get<Account>(`/v1/accounts/${id}`)
  return resp.data
}

export async function listPositions(accountId: string): Promise<Position[]> {
  const resp = await api.get<Position[]>(`/v1/accounts/${accountId}/positions`)
  return resp.data
}

export async function resetAccount(id: string): Promise<Account> {
  const resp = await api.post<Account>(`/v1/accounts/${id}/reset`)
  return resp.data
}

// --- Order APIs ---

export async function placeOrder(data: OrderCreateRequest): Promise<OrderRecord> {
  const resp = await api.post<OrderRecord>('/v1/trading/orders', data)
  return resp.data
}

export interface OrderListResponse {
  items: OrderRecord[]
  total: number
}

export async function listOrders(
  accountId: string,
  status?: string,
  symbol?: string,
  limit = 20,
  offset = 0,
): Promise<OrderListResponse> {
  const resp = await api.get<OrderListResponse>('/v1/trading/orders', {
    params: { account_id: accountId, status, symbol, limit, offset },
  })
  return resp.data
}

export async function getOrder(id: string): Promise<OrderRecord> {
  const resp = await api.get<OrderRecord>(`/v1/trading/orders/${id}`)
  return resp.data
}

export async function cancelOrder(id: string): Promise<OrderRecord> {
  const resp = await api.delete<OrderRecord>(`/v1/trading/orders/${id}`)
  return resp.data
}
