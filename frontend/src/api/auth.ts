import api from './index'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  nickname?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserInfo {
  id: string
  email: string
  nickname: string
  is_active: boolean
  oauth_provider: string | null
  created_at: string
}

export async function login(data: LoginRequest): Promise<AuthResponse> {
  const resp = await api.post<AuthResponse>('/v1/auth/login', data)
  return resp.data
}

export async function register(data: RegisterRequest): Promise<UserInfo> {
  const resp = await api.post<UserInfo>('/v1/auth/register', data)
  return resp.data
}

export async function getMe(): Promise<UserInfo> {
  const resp = await api.get<UserInfo>('/v1/users/me')
  return resp.data
}
