export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export interface RegisterRequest {
  full_name: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface ApiError {
  detail: string;
}